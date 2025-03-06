#!/usr/bin/env python3
"""
Test Stream Generator for IPTV Re-Streaming Application
This script creates a test stream to verify HLS file generation
"""

import os
import sys
import subprocess
import time
import logging
import argparse
import glob
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_stream")

# Constants
HLS_DIR = "/tmp/hls"
TEST_STREAM_ID = "test"
RTMP_SERVER_URL = "rtmp://nginx-rtmp:1935/live"
HLS_SERVER_URL = "http://nginx-rtmp:8000/hls"

def ensure_hls_directory():
    """Ensure the HLS directory exists and has proper permissions."""
    try:
        if not os.path.exists(HLS_DIR):
            logger.info(f"Creating HLS directory: {HLS_DIR}")
            os.makedirs(HLS_DIR, exist_ok=True)
            
        # Set permissions to ensure all containers can write to the directory
        os.chmod(HLS_DIR, 0o777)
        
        # Create a test file to verify write access
        test_file_path = os.path.join(HLS_DIR, "test.m3u8")
        with open(test_file_path, "w") as f:
            f.write("#EXTM3U\n#EXT-X-VERSION:3")
        
        test_ts_path = os.path.join(HLS_DIR, "test.ts")
        with open(test_ts_path, "wb") as f:
            f.write(b"Test TS file" * 1024)  # Create a dummy TS file
            
        logger.info(f"HLS directory setup complete: {HLS_DIR}")
        logger.info(f"Test files created: {test_file_path}, {test_ts_path}")
        
        # List all files in the directory for debugging
        files = os.listdir(HLS_DIR)
        logger.info(f"Files in HLS directory: {files}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up HLS directory: {str(e)}")
        return False

def cleanup_test_files():
    """Clean up test files."""
    try:
        # Use glob to find all matching files
        file_patterns = [
            f"{HLS_DIR}/stream_{TEST_STREAM_ID}.m3u8",
            f"{HLS_DIR}/{TEST_STREAM_ID}.m3u8",
            f"{HLS_DIR}/stream_{TEST_STREAM_ID}_*.ts",
            f"{HLS_DIR}/{TEST_STREAM_ID}_*.ts"
        ]
        
        for pattern in file_patterns:
            for file_path in glob.glob(pattern):
                logger.info(f"Removing test file: {file_path}")
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning up test files: {str(e)}")

def log_process_output(process):
    """Log the output of the process in real-time."""
    def read_output(stream, log_func):
        for line in iter(stream.readline, ''):
            if line:
                log_func(f"FFmpeg: {line.strip()}")
    
    # Create threads for stdout and stderr
    stdout_thread = threading.Thread(
        target=read_output,
        args=(process.stdout, logger.info),
        daemon=True
    )
    stderr_thread = threading.Thread(
        target=read_output,
        args=(process.stderr, logger.warning),
        daemon=True
    )
    
    # Start the threads
    stdout_thread.start()
    stderr_thread.start()

def start_test_stream(source_url):
    """
    Start a test stream from the given source URL.
    Returns the process if successful, None otherwise.
    """
    try:
        # Ensure HLS directory exists and is writable
        if not ensure_hls_directory():
            return None
            
        # Clean up any existing test files
        cleanup_test_files()
        
        # Define output paths
        rtmp_output = f"{RTMP_SERVER_URL}/{TEST_STREAM_ID}"
        hls_output_path = f"{HLS_DIR}/stream_{TEST_STREAM_ID}.m3u8"
        
        # Command to stream to RTMP server and generate HLS files directly
        # Try a simpler command first
        ffmpeg_cmd = [
            "ffmpeg",
            "-y",  # Overwrite output files without asking
            "-i", source_url,
            "-c:v", "copy",
            "-c:a", "copy",
            "-f", "hls",
            "-hls_time", "3",
            "-hls_list_size", "60",
            "-hls_segment_filename", f"{HLS_DIR}/stream_{TEST_STREAM_ID}_%03d.ts",
            hls_output_path
        ]
        
        logger.info(f"Executing command: {' '.join(ffmpeg_cmd)}")
        
        # Start the ffmpeg process with pipes for output
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered
            universal_newlines=True
        )
        
        # Start logging the output
        log_process_output(process)
        
        # Wait a moment to see if the process crashes immediately
        time.sleep(2)
        
        if process.poll() is not None:
            # Process has already terminated
            logger.error(f"Test stream failed to start, process exited with code {process.returncode}")
            return None
            
        logger.info("Test stream started successfully")
        return process
        
    except Exception as e:
        logger.error(f"Error starting test stream: {str(e)}")
        return None

def monitor_hls_files(process, duration=60):
    """Monitor HLS file generation for the test stream."""
    try:
        start_time = time.time()
        check_interval = 5  # Check every 5 seconds
        
        while time.time() - start_time < duration:
            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"FFmpeg process terminated unexpectedly with code {process.returncode}")
                return False
                
            # Check for HLS files
            file_patterns = [
                f"{HLS_DIR}/stream_{TEST_STREAM_ID}.m3u8",
                f"{HLS_DIR}/{TEST_STREAM_ID}.m3u8",
                f"{HLS_DIR}/stream_{TEST_STREAM_ID}_*.ts",
                f"{HLS_DIR}/{TEST_STREAM_ID}_*.ts"
            ]
            
            found_files = []
            for pattern in file_patterns:
                matching_files = glob.glob(pattern)
                if matching_files:
                    found_files.extend(matching_files)
            
            if found_files:
                logger.info(f"Found HLS files: {found_files}")
                
                # Check if m3u8 file exists and has content
                m3u8_files = [f for f in found_files if f.endswith('.m3u8')]
                if m3u8_files:
                    try:
                        with open(m3u8_files[0], 'r') as f:
                            content = f.read()
                            if content and '#EXTM3U' in content:
                                logger.info(f"Valid M3U8 content found: {content[:100]}...")
                                logger.info("HLS streaming is working correctly!")
                                return True
                    except Exception as e:
                        logger.error(f"Error reading M3U8 file: {str(e)}")
                
                # If we have TS files but no valid M3U8, still consider it partially working
                ts_files = [f for f in found_files if f.endswith('.ts')]
                if ts_files:
                    logger.info(f"Found {len(ts_files)} TS segment files")
                    logger.info("TS segments are being generated, but M3U8 playlist may have issues")
            
            # List all files in the directory for debugging
            try:
                all_files = os.listdir(HLS_DIR)
                logger.info(f"All files in HLS directory: {all_files}")
            except Exception as e:
                logger.error(f"Error listing HLS directory: {str(e)}")
                
            # Wait before next check
            time.sleep(check_interval)
            
        logger.warning(f"No valid HLS files found after {duration} seconds")
        return False
        
    except Exception as e:
        logger.error(f"Error monitoring HLS files: {str(e)}")
        return False
    finally:
        # Always terminate the process when done
        if process and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()

def check_nginx_rtmp():
    """Check if nginx-rtmp is properly configured for HLS."""
    try:
        import requests
        
        # Try to access the HLS directory via nginx
        response = requests.get(f"{HLS_SERVER_URL}", timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully accessed {HLS_SERVER_URL}")
            logger.info(f"Response: {response.text[:200]}...")
            return True
        else:
            logger.error(f"Failed to access {HLS_SERVER_URL}, status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error accessing {HLS_SERVER_URL}: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test HLS streaming for IPTV Re-Streaming Application")
    parser.add_argument("--source", "-s", required=True, help="Source URL for the test stream")
    parser.add_argument("--duration", "-d", type=int, default=60, help="Duration to run the test stream (seconds)")
    parser.add_argument("--rtmp-only", action="store_true", help="Test RTMP streaming only, without HLS")
    
    args = parser.parse_args()
    
    logger.info("Starting HLS streaming test")
    
    # Check nginx-rtmp configuration
    logger.info("Checking nginx-rtmp configuration...")
    if not check_nginx_rtmp():
        logger.warning("Nginx-RTMP may not be properly configured for HLS streaming")
    
    # Start the test stream
    logger.info(f"Starting test stream from {args.source}")
    process = start_test_stream(args.source)
    
    if process:
        # Monitor HLS file generation
        logger.info(f"Monitoring HLS file generation for {args.duration} seconds")
        success = monitor_hls_files(process, args.duration)
        
        if success:
            logger.info("Test completed successfully. HLS streaming is working!")
        else:
            logger.error("Test failed. HLS streaming is not working properly.")
    else:
        logger.error("Failed to start test stream")

if __name__ == "__main__":
    main()
