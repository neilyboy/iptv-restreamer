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
        
        # Ensure HLS directory exists with proper permissions
        self._ensure_hls_directory()
        
    def _ensure_hls_directory(self):
        """Ensure the HLS directory exists and has proper permissions."""
        try:
            if not os.path.exists(self.hls_dir):
                logger.info(f"Creating HLS directory: {self.hls_dir}")
                os.makedirs(self.hls_dir, exist_ok=True)
                
            # Set permissions to ensure all containers can write to the directory
            os.chmod(self.hls_dir, 0o777)
            
            # Create a test file to verify write access
            test_file_path = os.path.join(self.hls_dir, "stream_manager_test.txt")
            with open(test_file_path, "w") as f:
                f.write(f"Stream manager test file created at {time.time()}")
            
            logger.info(f"HLS directory setup complete: {self.hls_dir}")
            logger.info(f"Test file created: {test_file_path}")
            
            # List all files in the directory for debugging
            files = os.listdir(self.hls_dir)
            logger.info(f"Files in HLS directory: {files}")
            
        except Exception as e:
            logger.error(f"Error setting up HLS directory: {str(e)}")
            # Continue execution even if there's an error, as nginx-rtmp might handle it
    
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
                "-reconnect_delay_max", "5",
                "-timeout", "10000000",  # Longer timeout for network issues
                "-analyzeduration", "2147483647",
                "-probesize", "2147483647",
                
                # Input
                "-i", source_url,
                
                # Video and audio codec settings
                "-c:v", "copy",  # Copy video codec
                "-c:a", "copy",  # Copy audio codec
                
                # Output format and HLS settings
                "-f", "flv",  # Output to RTMP/FLV format
                
                # Error handling
                "-err_detect", "ignore_err",
                
                # RTMP output
                rtmp_output
            ]
            
            logger.info(f"Executing command: {' '.join(ffmpeg_cmd)}")
            
            # Start the ffmpeg process
            process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Store the process
            self.active_streams[stream_id_str] = process
            
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
                        "-reconnect_delay_max", "5",
                        "-timeout", "10000000",
                        "-analyzeduration", "2147483647",
                        "-probesize", "2147483647",
                        "-i", source_url,
                        "-c:v", "copy",
                        "-c:a", "copy",
                        "-f", "flv",
                        "-err_detect", "ignore_err",
                        rtmp_output
                    ]
                    
                    logger.info(f"Retrying with command: {' '.join(ffmpeg_cmd)}")
                    
                    # Start the ffmpeg process again
                    process = subprocess.Popen(
                        ffmpeg_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True
                    )
                    
                    # Update the stored process
                    self.active_streams[stream_id_str] = process
                    
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
                hls_exists = self._verify_hls_files(stream_id_str, max_attempts=1)
                
                if hls_exists:
                    logger.info(f"HLS files confirmed for stream {stream_id}")
                    return
                    
            # If we get here, no HLS files were found after 5 minutes
            logger.warning(f"No HLS files found for stream {stream_id} after 5 minutes of monitoring")
            
        except Exception as e:
            logger.error(f"Error monitoring HLS files for stream {stream_id}: {str(e)}")
    
    def _verify_hls_files(self, stream_id: str, max_attempts: int = 10) -> bool:
        """
        Verify that HLS files are being generated for the given stream ID.
        Returns True if files are found, False otherwise.
        """
        # Check for different possible file patterns
        file_patterns = [
            f"{self.hls_dir}/stream_{stream_id}.m3u8",  # Our direct FFmpeg output
            f"{self.hls_dir}/{stream_id}.m3u8",         # Nginx-RTMP generated
            f"{self.hls_dir}/stream_{stream_id}_*.ts",  # Our TS segments
            f"{self.hls_dir}/{stream_id}_*.ts"          # Nginx-RTMP TS segments
        ]
        
        for attempt in range(max_attempts):
            logger.info(f"Checking for HLS files (attempt {attempt+1}/{max_attempts})")
            
            found_files = []
            for pattern in file_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    found_files.extend(matching_files)
            
            if found_files:
                logger.info(f"Found HLS files: {found_files}")
                return True
                    
            # List all files in the directory for debugging
            try:
                all_files = os.listdir(self.hls_dir)
                logger.info(f"All files in HLS directory: {all_files}")
            except Exception as e:
                logger.error(f"Error listing HLS directory: {str(e)}")
                
            # Wait before next attempt
            time.sleep(2)
        
        logger.warning(f"No HLS files found for stream {stream_id} after {max_attempts} attempts")
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
    
    def _cleanup_hls_files(self, stream_id: str) -> None:
        """Clean up HLS files for the given stream ID."""
        try:
            # Use glob to find all matching files
            file_patterns = [
                f"{self.hls_dir}/stream_{stream_id}.m3u8",
                f"{self.hls_dir}/{stream_id}.m3u8",
                f"{self.hls_dir}/stream_{stream_id}_*.ts",
                f"{self.hls_dir}/{stream_id}_*.ts"
            ]
            
            for pattern in file_patterns:
                for file_path in glob.glob(pattern):
                    logger.info(f"Removing HLS file: {file_path}")
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"Error removing file {file_path}: {str(e)}")
        except Exception as e:
            logger.error(f"Error cleaning up HLS files for stream {stream_id}: {str(e)}")
    
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
                f"{self.hls_dir}/stream_{stream_id_str}.m3u8",
                f"{self.hls_dir}/{stream_id_str}.m3u8"
            ]
            
            hls_file_path = None
            for pattern in file_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    hls_file_path = matching_files[0]
                    break
            
            # Check for TS segments
            ts_patterns = [
                f"{self.hls_dir}/stream_{stream_id_str}_*.ts",
                f"{self.hls_dir}/{stream_id_str}_*.ts"
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
