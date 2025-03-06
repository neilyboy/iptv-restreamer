import os
import subprocess
import logging
import time
import requests
import glob
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("stream_manager")

class StreamManager:
    def __init__(self, rtmp_server_url: str, hls_server_url: str = "http://192.168.1.113:8088/hls"):
        self.rtmp_server_url = rtmp_server_url
        self.hls_server_url = hls_server_url
        self.active_streams: Dict[str, subprocess.Popen] = {}
        self.hls_dir = "/tmp/hls"
        self.hls_live_dir = "/tmp/hls/live"
        
        # Ensure HLS directory exists with proper permissions
        self._ensure_hls_directory()
        
    def _ensure_hls_directory(self):
        """Ensure the HLS directory exists and has proper permissions."""
        try:
            # Create main HLS directory
            if not os.path.exists(self.hls_dir):
                logger.info(f"Creating HLS directory: {self.hls_dir}")
                os.makedirs(self.hls_dir, exist_ok=True)
            
            # Create live subdirectory
            if not os.path.exists(self.hls_live_dir):
                logger.info(f"Creating HLS live directory: {self.hls_live_dir}")
                os.makedirs(self.hls_live_dir, exist_ok=True)
                
            # Set permissions to ensure all containers can write to the directories
            os.chmod(self.hls_dir, 0o777)
            os.chmod(self.hls_live_dir, 0o777)
            
            # Create a test file to verify write access
            test_file_path = os.path.join(self.hls_dir, "stream_manager_test.txt")
            with open(test_file_path, "w") as f:
                f.write(f"Stream manager test file created at {time.time()}")
            
            logger.info(f"HLS directory setup complete: {self.hls_dir}")
            logger.info(f"Test file created: {test_file_path}")
            
            # List all files in both directories for debugging
            files = os.listdir(self.hls_dir)
            live_files = os.listdir(self.hls_live_dir) if os.path.exists(self.hls_live_dir) else []
            logger.info(f"Files in HLS directory: {files}")
            logger.info(f"Files in HLS live directory: {live_files}")
            
        except Exception as e:
            logger.error(f"Error setting up HLS directory: {str(e)}")
            
    def start_stream(self, db: Session, stream_id: int) -> bool:
        """
        Start a new stream with the given ID from the database.
        Returns True if the stream was started successfully, False otherwise.
        """
        try:
            # Import models here to avoid circular imports
            import models
            
            # Get the stream from the database
            db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
            if not db_stream:
                logger.error(f"Stream {stream_id} not found in database")
                return False
                
            source_url = db_stream.url
            
            # Convert stream_id to string for use as key in active_streams dictionary
            stream_id_str = str(stream_id)
            
            if stream_id_str in self.active_streams:
                logger.info(f"Stream {stream_id} is already active")
                return True
                
            logger.info(f"Starting stream {stream_id} from {source_url}")
            
            # Verify HLS directory exists and is writable
            self._ensure_hls_directory()
            
            # Clean up any existing HLS files for this stream
            self._cleanup_hls_files(stream_id_str)
            
            # Define output paths
            rtmp_output = f"{self.rtmp_server_url}/{stream_id_str}"
            
            # First, check if there's already a stream publishing to this endpoint
            # We'll do this by trying to access the HLS file that would be created by nginx-rtmp
            hls_file_path = f"{self.hls_dir}/{stream_id_str}.m3u8"
            if os.path.exists(hls_file_path):
                logger.warning(f"HLS file for stream {stream_id} already exists, but not in our active streams")
                logger.warning(f"This may indicate another process is already streaming to this endpoint")
                
                # Try to kill any existing ffmpeg processes for this stream
                self._kill_existing_ffmpeg_process(stream_id_str)
                
                # Wait a moment for the process to terminate
                time.sleep(2)
                
                # Clean up any existing HLS files again
                self._cleanup_hls_files(stream_id_str)
            
            # Use a more robust FFmpeg command with optimized settings for HLS streaming
            ffmpeg_cmd = [
                "ffmpeg",
                "-y",  # Overwrite output files without asking
                
                # Input options for better network handling
                "-reconnect", "1",
                "-reconnect_at_eof", "1",
                "-reconnect_streamed", "1",
                "-reconnect_delay_max", "2",
                "-timeout", "5000000",
                "-analyzeduration", "1000000",
                "-probesize", "1000000",
                
                # Input
                "-i", source_url,
                
                # Add verbose logging
                "-loglevel", "debug",
                
                # Video settings - simplified for testing
                "-c:v", "copy",
                "-c:a", "copy",
                
                # Output format settings
                "-f", "flv",
                
                # RTMP output
                rtmp_output
            ]
            
            logger.info(f"Executing command: {' '.join(ffmpeg_cmd)}")
            
            # Start the ffmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                bufsize=1
            )
            
            # Store the process
            self.active_streams[stream_id_str] = process
            
            # Start a thread to continuously read and log FFmpeg output
            def log_output():
                while True:
                    line = process.stderr.readline()
                    if not line and process.poll() is not None:
                        break
                    if line:
                        logger.info(f"FFmpeg output: {line.strip()}")
            
            import threading
            log_thread = threading.Thread(target=log_output, daemon=True)
            log_thread.start()
            
            # Wait a moment to see if the process crashes immediately
            time.sleep(2)
            
            if process.poll() is not None:
                # Process has already terminated
                stdout, stderr = process.communicate()
                logger.error(f"Stream {stream_id} failed to start: {stderr}")
                
                # Check for "Already publishing" error
                if "Already publishing" in stderr:
                    logger.warning(f"Stream {stream_id} is already being published by another process")
                    
                    # Try to kill any existing ffmpeg processes for this stream
                    self._kill_existing_ffmpeg_process(stream_id_str)
                    
                    # Wait a moment and try again with a different stream ID suffix
                    time.sleep(2)
                    
                    # Use a different RTMP endpoint with a timestamp suffix
                    timestamp_suffix = int(time.time()) % 1000
                    rtmp_output = f"{self.rtmp_server_url}/{stream_id_str}_{timestamp_suffix}"
                    
                    # Update the ffmpeg command
                    ffmpeg_cmd = [
                        "ffmpeg",
                        "-y",
                        "-reconnect", "1",
                        "-reconnect_at_eof", "1",
                        "-reconnect_streamed", "1",
                        "-reconnect_delay_max", "2",
                        "-timeout", "5000000",
                        "-analyzeduration", "1000000",
                        "-probesize", "1000000",
                        "-i", source_url,
                        "-loglevel", "debug",
                        "-c:v", "copy",
                        "-c:a", "copy",
                        "-f", "flv",
                        rtmp_output
                    ]
                    
                    logger.info(f"Retrying with command: {' '.join(ffmpeg_cmd)}")
                    
                    # Start the ffmpeg process again
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        bufsize=1
                    )
                    
                    # Update the stored process
                    self.active_streams[stream_id_str] = process
                    
                    # Start a thread to continuously read and log FFmpeg output
                    def log_output():
                        while True:
                            line = process.stderr.readline()
                            if not line and process.poll() is not None:
                                break
                            if line:
                                logger.info(f"FFmpeg output: {line.strip()}")
                    
                    import threading
                    log_thread = threading.Thread(target=log_output, daemon=True)
                    log_thread.start()
                    
                    # Wait again to see if it crashes
                    time.sleep(2)
                    
                    if process.poll() is not None:
                        # Still failed
                        stdout, stderr = process.communicate()
                        logger.error(f"Stream {stream_id} failed to start on retry: {stderr}")
                        
                        # Update database status
                        db_stream.status = "error"
                        db.commit()
                        
                        # Remove from active streams
                        if stream_id_str in self.active_streams:
                            del self.active_streams[stream_id_str]
                            
                        return False
                else:
                    # Update database status
                    db_stream.status = "error"
                    db.commit()
                    
                    # Remove from active streams
                    if stream_id_str in self.active_streams:
                        del self.active_streams[stream_id_str]
                        
                    return False
            
            # Update stream status in database
            db_stream.status = "running"
            db.commit()
            
            # Start a separate thread to monitor HLS file generation
            import threading
            monitor_thread = threading.Thread(
                target=self._monitor_hls_files,
                args=(db, stream_id, stream_id_str),
                daemon=True
            )
            monitor_thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting stream {stream_id}: {str(e)}")
            return False
    
    def _kill_existing_ffmpeg_process(self, stream_id_str):
        """Kill any existing ffmpeg processes for this stream."""
        try:
            logger.info(f"Attempting to kill existing ffmpeg processes for stream {stream_id_str}")
            
            # On Linux, we can use the ps and grep commands
            kill_cmd = f"ps aux | grep 'ffmpeg.*{stream_id_str}' | grep -v grep | awk '{{print $2}}' | xargs -r kill -9"
            subprocess.run(kill_cmd, shell=True)
            
            logger.info(f"Killed any existing ffmpeg processes for stream {stream_id_str}")
        except Exception as e:
            logger.error(f"Error killing existing ffmpeg processes: {str(e)}")
    
    def _monitor_hls_files(self, db: Session, stream_id: int, stream_id_str: str):
        """Monitor HLS file generation for a stream."""
        try:
            # Check every 10 seconds for 5 minutes
            for _ in range(30):
                time.sleep(10)
                
                # Skip if stream is no longer active
                if stream_id_str not in self.active_streams:
                    return
                    
                # Check if HLS files exist
                hls_exists = self.check_hls_files(stream_id_str, attempts=1)
                
                if hls_exists:
                    logger.info(f"HLS files confirmed for stream {stream_id}")
                    return
                    
            # If we get here, no HLS files were found after 5 minutes
            logger.warning(f"No HLS files found for stream {stream_id} after 5 minutes of monitoring")
            
        except Exception as e:
            logger.error(f"Error monitoring HLS files for stream {stream_id}: {str(e)}")
    
    def _cleanup_hls_files(self, stream_id: str):
        """Clean up any existing HLS files for a stream."""
        try:
            # Clean up files in both main and live directories
            patterns = [
                os.path.join(self.hls_dir, f"{stream_id}*.m3u8"),
                os.path.join(self.hls_dir, f"{stream_id}*.ts"),
                os.path.join(self.hls_live_dir, f"{stream_id}*.m3u8"),
                os.path.join(self.hls_live_dir, f"{stream_id}*.ts")
            ]
            
            for pattern in patterns:
                for file in glob.glob(pattern):
                    try:
                        os.remove(file)
                        logger.info(f"Removed HLS file: {file}")
                    except Exception as e:
                        logger.warning(f"Failed to remove file {file}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error cleaning up HLS files: {str(e)}")
            
    def check_hls_files(self, stream_id: str, attempts: int = 1) -> bool:
        """Check if HLS files exist for a stream."""
        for attempt in range(attempts):
            logger.info(f"Checking for HLS files (attempt {attempt + 1}/{attempts})")
            
            # List all files in both directories
            all_files = os.listdir(self.hls_dir)
            live_files = os.listdir(self.hls_live_dir) if os.path.exists(self.hls_live_dir) else []
            
            logger.info(f"All files in HLS directory: {all_files}")
            logger.info(f"All files in HLS live directory: {live_files}")
            
            # Check for files in both directories
            main_m3u8 = os.path.join(self.hls_dir, f"{stream_id}.m3u8")
            live_m3u8 = os.path.join(self.hls_live_dir, f"{stream_id}.m3u8")
            
            if os.path.exists(main_m3u8) or os.path.exists(live_m3u8):
                return True
                
            if attempt < attempts - 1:
                time.sleep(2)
                
        logger.warning(f"No HLS files found for stream {stream_id} after {attempts} attempts")
        return False
    
    def stop_stream(self, db: Session, stream_id: int) -> bool:
        """
        Stop the stream with the given ID.
        Returns True if the stream was stopped successfully, False otherwise.
        """
        try:
            # Import models here to avoid circular imports
            import models
            
            # Get the stream from the database
            db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
            if not db_stream:
                logger.error(f"Stream {stream_id} not found in database")
                return False
            
            # Convert stream_id to string for use as key in active_streams dictionary
            stream_id_str = str(stream_id)
            
            if stream_id_str not in self.active_streams:
                logger.warning(f"Stream {stream_id} is not active")
                # Update database status anyway
                db_stream.status = "stopped"
                db.commit()
                return True
                
            logger.info(f"Stopping stream {stream_id}")
            
            # Get the process
            process = self.active_streams[stream_id_str]
            
            try:
                # First try to terminate gracefully
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning(f"Stream {stream_id} did not terminate gracefully, forcing kill")
                process.kill()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    logger.error(f"Failed to kill stream {stream_id} process")
                    
            # Remove the process from active streams
            del self.active_streams[stream_id_str]
            
            # Clean up HLS files
            logger.info(f"Removing HLS file: {self.hls_dir}/{stream_id_str}.m3u8")
            self._cleanup_hls_files(stream_id_str)
            
            # Update stream status in database
            db_stream.status = "stopped"
            db.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping stream {stream_id}: {str(e)}")
            return False
    
    def get_active_streams(self, db: Optional[Session] = None) -> List[str]:
        """Get a list of active stream IDs."""
        return list(self.active_streams.keys())
    
    def check_stream_status(self, db: Session, stream_id: int) -> Dict:
        """
        Check the status of the stream with the given ID.
        Returns a dictionary with status information.
        """
        try:
            # Import models here to avoid circular imports
            import models
            
            # Get the stream from the database
            db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
            if not db_stream:
                logger.error(f"Stream {stream_id} not found in database")
                return {"status": "not_found", "error": "Stream not found in database"}
            
            # Convert stream_id to string for use as key in active_streams dictionary
            stream_id_str = str(stream_id)
            
            if stream_id_str not in self.active_streams:
                return {"status": "inactive", "error": "Stream is not active"}
                
            process = self.active_streams[stream_id_str]
            
            # Check if the process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                return {
                    "status": "failed",
                    "error": stderr,
                    "exit_code": process.returncode
                }
                
            # Check for HLS files using glob patterns
            file_patterns = [
                os.path.join(self.hls_dir, f"{stream_id_str}.m3u8"),
                os.path.join(self.hls_live_dir, f"{stream_id_str}.m3u8")
            ]
            
            hls_file_path = None
            for pattern in file_patterns:
                if os.path.exists(pattern):
                    hls_file_path = pattern
                    break
            
            # Check for TS segments
            ts_patterns = [
                os.path.join(self.hls_dir, f"{stream_id_str}_*.ts"),
                os.path.join(self.hls_live_dir, f"{stream_id_str}_*.ts")
            ]
            
            ts_files = []
            for pattern in ts_patterns:
                ts_files.extend(glob.glob(pattern))
            
            # Determine HLS URL
            hls_url = None
            if hls_file_path:
                # Extract just the filename from the path
                hls_filename = os.path.basename(hls_file_path)
                hls_url = f"{self.hls_server_url}/{hls_filename}"
            
            return {
                "status": "active" if hls_file_path else "streaming_no_hls",
                "pid": process.pid,
                "hls_url": hls_url,
                "hls_file_exists": bool(hls_file_path),
                "ts_segment_count": len(ts_files),
                "ffmpeg_running": process.poll() is None
            }
        except Exception as e:
            logger.error(f"Error checking status for stream {stream_id}: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def restart_stream(self, db: Session, stream_id: int) -> bool:
        """
        Restart the stream with the given ID.
        Returns True if the stream was restarted successfully, False otherwise.
        """
        try:
            # Import models here to avoid circular imports
            import models
            
            # Get the stream from the database
            db_stream = db.query(models.Stream).filter(models.Stream.id == stream_id).first()
            if not db_stream:
                logger.error(f"Stream {stream_id} not found in database")
                return False
            
            # Convert stream_id to string for use as key in active_streams dictionary
            stream_id_str = str(stream_id)
            
            if stream_id_str not in self.active_streams:
                logger.warning(f"Stream {stream_id} is not active, starting it instead of restarting")
                return self.start_stream(db, stream_id)
                
            # Stop the stream
            stop_success = self.stop_stream(db, stream_id)
            if not stop_success:
                logger.error(f"Failed to stop stream {stream_id} during restart")
                return False
                
            # Wait a moment before starting again
            time.sleep(2)
            
            # Start the stream again
            return self.start_stream(db, stream_id)
        except Exception as e:
            logger.error(f"Error restarting stream {stream_id}: {str(e)}")
            return False

# Create a singleton instance
stream_manager = StreamManager("rtmp://nginx-rtmp:1935/live", "http://192.168.1.113:8088/hls")
