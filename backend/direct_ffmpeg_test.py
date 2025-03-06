#!/usr/bin/env python3
"""
Direct FFmpeg Test for IPTV Re-Streaming Application
This script tests different FFmpeg commands to find one that works for HLS generation
"""

import os
import subprocess
import time
import logging
import argparse
import glob
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ffmpeg_test")

# Constants
HLS_DIR = "/tmp/hls"

def ensure_hls_directory():
    """Ensure the HLS directory exists and has proper permissions."""
    try:
        if not os.path.exists(HLS_DIR):
            logger.info(f"Creating HLS directory: {HLS_DIR}")
            os.makedirs(HLS_DIR, exist_ok=True)
            
        # Set permissions to ensure all containers can write to the directory
        os.chmod(HLS_DIR, 0o777)
        logger.info(f"Set permissions 777 on {HLS_DIR}")
        
        # List all files in the directory for debugging
        files = os.listdir(HLS_DIR)
        logger.info(f"Files in HLS directory: {files}")
        
        return True
    except Exception as e:
        logger.error(f"Error setting up HLS directory: {str(e)}")
        return False

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

def test_ffmpeg_command(source_url, test_name, command_args, duration=30):
    """Test a specific FFmpeg command."""
    try:
        # Clean up any existing test files
        output_dir = f"{HLS_DIR}/{test_name}"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        os.chmod(output_dir, 0o777)
        
        # Build the FFmpeg command
        ffmpeg_cmd = ["ffmpeg", "-y", "-i", source_url] + command_args
        
        logger.info(f"TEST {test_name}: Executing command: {' '.join(ffmpeg_cmd)}")
        
        # Start the FFmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # Log the output
        log_process_output(process)
        
        # Wait a moment to see if the process crashes immediately
        time.sleep(2)
        
        if process.poll() is not None:
            logger.error(f"TEST {test_name}: FFmpeg process exited with code {process.returncode}")
            return False
        
        # Monitor for the specified duration
        start_time = time.time()
        success = False
        
        while time.time() - start_time < duration:
            # Check if process is still running
            if process.poll() is not None:
                logger.error(f"TEST {test_name}: FFmpeg process terminated with code {process.returncode}")
                break
            
            # Check for output files
            files = glob.glob(f"{output_dir}/*")
            if files:
                logger.info(f"TEST {test_name}: Found output files: {files}")
                success = True
                break
                
            # Wait before checking again
            time.sleep(5)
        
        # Always terminate the process when done
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        
        if success:
            logger.info(f"TEST {test_name}: SUCCESSFUL - Files were generated")
        else:
            logger.error(f"TEST {test_name}: FAILED - No files were generated")
            
        return success
        
    except Exception as e:
        logger.error(f"TEST {test_name}: Error: {str(e)}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Test different FFmpeg commands for HLS generation")
    parser.add_argument("--source", "-s", required=True, help="Source URL for the test stream")
    parser.add_argument("--duration", "-d", type=int, default=30, help="Duration to run each test (seconds)")
    
    args = parser.parse_args()
    
    logger.info("Starting FFmpeg command tests")
    
    # Ensure HLS directory exists and is writable
    if not ensure_hls_directory():
        logger.error("Failed to set up HLS directory")
        return
    
    # Define test cases
    test_cases = [
        {
            "name": "direct_hls",
            "args": [
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "hls", 
                "-hls_time", "3", 
                "-hls_list_size", "60", 
                f"{HLS_DIR}/direct_hls/stream.m3u8"
            ]
        },
        {
            "name": "direct_hls_with_segment_options",
            "args": [
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "hls", 
                "-hls_time", "3", 
                "-hls_list_size", "60", 
                "-hls_segment_filename", f"{HLS_DIR}/direct_hls_with_segment_options/stream_%03d.ts",
                f"{HLS_DIR}/direct_hls_with_segment_options/stream.m3u8"
            ]
        },
        {
            "name": "direct_hls_with_flags",
            "args": [
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "hls", 
                "-hls_time", "3", 
                "-hls_list_size", "60", 
                "-hls_flags", "delete_segments",
                f"{HLS_DIR}/direct_hls_with_flags/stream.m3u8"
            ]
        },
        {
            "name": "rtmp_and_hls",
            "args": [
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "flv", 
                "rtmp://nginx-rtmp:1935/live/test",
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "hls", 
                "-hls_time", "3", 
                "-hls_list_size", "60", 
                f"{HLS_DIR}/rtmp_and_hls/stream.m3u8"
            ]
        },
        {
            "name": "rtmp_only",
            "args": [
                "-c:v", "copy", 
                "-c:a", "copy", 
                "-f", "flv", 
                "rtmp://nginx-rtmp:1935/live/test"
            ]
        },
        {
            "name": "hls_with_transcode",
            "args": [
                "-c:v", "libx264", 
                "-preset", "veryfast", 
                "-c:a", "aac", 
                "-f", "hls", 
                "-hls_time", "3", 
                "-hls_list_size", "60", 
                f"{HLS_DIR}/hls_with_transcode/stream.m3u8"
            ]
        }
    ]
    
    # Run each test case
    results = {}
    for test in test_cases:
        logger.info(f"Running test: {test['name']}")
        success = test_ffmpeg_command(args.source, test["name"], test["args"], args.duration)
        results[test["name"]] = success
    
    # Print summary
    logger.info("=== TEST RESULTS SUMMARY ===")
    for test_name, success in results.items():
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"{test_name}: {status}")
    
    # Provide recommendations
    successful_tests = [name for name, success in results.items() if success]
    if successful_tests:
        logger.info(f"Recommendation: Use the '{successful_tests[0]}' approach for your application")
    else:
        logger.error("All tests failed. Check FFmpeg logs for details.")

if __name__ == "__main__":
    main()
