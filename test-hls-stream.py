#!/usr/bin/env python3
"""
HLS Stream Testing Tool
This script tests the HLS streaming functionality by creating a test stream
"""

import os
import subprocess
import sys
import logging
import time
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hls-test")

def ensure_hls_directory():
    """Ensure the HLS directory exists and has proper permissions"""
    hls_dir = "/tmp/hls"
    logger.info(f"Checking HLS directory: {hls_dir}")
    
    try:
        # Create directory if it doesn't exist
        if not os.path.exists(hls_dir):
            logger.info(f"HLS directory {hls_dir} does not exist, creating...")
            os.makedirs(hls_dir, exist_ok=True)
        
        # Set permissions
        os.chmod(hls_dir, 0o777)
        logger.info(f"Set permissions 777 on {hls_dir}")
        
        # Check if directory is writable
        test_file = os.path.join(hls_dir, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("Test write access")
        
        if os.path.exists(test_file):
            logger.info(f"Successfully wrote test file to {hls_dir}")
            os.remove(test_file)
        
        # List directory contents
        result = subprocess.run(["ls", "-la", hls_dir], capture_output=True, text=True)
        logger.info(f"Contents of {hls_dir}:\n{result.stdout}")
            
    except Exception as e:
        logger.error(f"Error ensuring HLS directory: {str(e)}")
        logger.error("This may cause HLS streaming to fail")
        return False
    
    return True

def create_test_stream(stream_id=999, test_duration=60):
    """Create a test HLS stream using ffmpeg"""
    logger.info(f"Creating test stream with ID: {stream_id}")
    
    # Ensure HLS directory exists
    if not ensure_hls_directory():
        return False
    
    # Test video source (use a test pattern)
    test_source = "testsrc=size=1280x720:rate=30"
    
    # HLS output paths
    hls_dir = "/tmp/hls"
    hls_segment_path = f"{hls_dir}/stream_{stream_id}_%03d.ts"
    hls_playlist_path = f"{hls_dir}/stream_{stream_id}.m3u8"
    
    logger.info(f"HLS segment path: {hls_segment_path}")
    logger.info(f"HLS playlist path: {hls_playlist_path}")
    
    # ffmpeg command to generate a test pattern and output as HLS
    command = [
        "ffmpeg",
        "-re",
        "-f", "lavfi",
        "-i", test_source,
        "-c:v", "libx264",
        "-b:v", "1000k",
        "-f", "hls",
        "-hls_time", "3",
        "-hls_list_size", "60",
        "-hls_flags", "delete_segments",
        "-hls_segment_filename", hls_segment_path,
        hls_playlist_path
    ]
    
    logger.info(f"Running command: {' '.join(command)}")
    
    try:
        # Start ffmpeg process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        
        logger.info(f"Started test stream with PID {process.pid}")
        
        # Wait a bit for files to be created
        time.sleep(5)
        
        # Check if files were created
        result = subprocess.run(["ls", "-la", "/tmp/hls"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        logger.info(f"HLS directory contents after starting stream:\n{result.stdout}")
        
        # Run for specified duration
        logger.info(f"Test stream will run for {test_duration} seconds")
        
        for i in range(test_duration):
            if i % 10 == 0:
                logger.info(f"Test stream running for {i} seconds...")
            
            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"ffmpeg process exited with code {process.poll()}")
                stderr = process.stderr.read()
                logger.error(f"ffmpeg stderr: {stderr}")
                return False
            
            time.sleep(1)
        
        # Terminate process
        logger.info("Test duration completed, terminating ffmpeg process")
        process.terminate()
        
        try:
            # Wait up to 5 seconds for process to terminate
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            # If it doesn't terminate, kill it forcefully
            logger.info(f"Process {process.pid} did not terminate, killing forcefully")
            process.kill()
            process.wait(timeout=2)
        
        logger.info("Test stream completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating test stream: {str(e)}")
        return False

def check_nginx_hls():
    """Check if nginx-rtmp is serving HLS files"""
    logger.info("Checking if nginx-rtmp is serving HLS files")
    
    try:
        # Try to curl the nginx ping endpoint
        result = subprocess.run(["curl", "-s", "http://nginx-rtmp:8000/ping"], capture_output=True, text=True)
        logger.info(f"Curl nginx-rtmp ping result: {result.stdout}")
        
        # Try to curl the HLS directory
        result = subprocess.run(["curl", "-s", "http://nginx-rtmp:8000/hls/"], capture_output=True, text=True)
        logger.info(f"Curl nginx-rtmp HLS directory result: {result.stdout}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking nginx-rtmp: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test HLS streaming")
    parser.add_argument("--stream-id", type=int, default=999, help="Stream ID to use for test")
    parser.add_argument("--duration", type=int, default=60, help="Duration of test stream in seconds")
    args = parser.parse_args()
    
    logger.info("=== HLS Stream Testing Tool ===")
    
    # Check nginx-rtmp
    check_nginx_hls()
    
    # Create test stream
    create_test_stream(args.stream_id, args.duration)
    
    logger.info("=== Test completed ===")

if __name__ == "__main__":
    main()
