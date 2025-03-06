#!/usr/bin/env python3
"""
HLS Debug Tool for IPTV Re-Streaming Application
This script helps diagnose and fix HLS streaming issues
"""

import os
import sys
import argparse
import subprocess
import time
import logging
import requests
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hls_debug")

# Constants
HLS_DIR = "/tmp/hls"
NGINX_HLS_URL = "http://nginx-rtmp:8088/hls"  # Updated port to match container configuration
EXTERNAL_HLS_URL = "http://localhost:8088/hls"

def check_directory_structure():
    """Check if the HLS directory exists and has proper permissions"""
    logger.info("Checking HLS directory structure...")
    
    # Check if directory exists
    if not os.path.exists(HLS_DIR):
        logger.error(f"HLS directory {HLS_DIR} does not exist")
        try:
            os.makedirs(HLS_DIR, exist_ok=True)
            logger.info(f"Created HLS directory {HLS_DIR}")
        except Exception as e:
            logger.error(f"Failed to create HLS directory: {str(e)}")
            return False
    else:
        logger.info(f"HLS directory {HLS_DIR} exists")
    
    # Check permissions
    try:
        # Get directory stats
        stats = os.stat(HLS_DIR)
        permissions = oct(stats.st_mode)[-3:]
        logger.info(f"HLS directory permissions: {permissions}")
        
        # Check if directory is writable
        if os.access(HLS_DIR, os.W_OK):
            logger.info(f"HLS directory {HLS_DIR} is writable")
        else:
            logger.warning(f"HLS directory {HLS_DIR} is not writable")
            try:
                os.chmod(HLS_DIR, 0o777)
                logger.info(f"Set permissions 777 on {HLS_DIR}")
            except Exception as e:
                logger.error(f"Failed to set permissions: {str(e)}")
                return False
        
        # Test write access by creating a file
        test_file = os.path.join(HLS_DIR, "debug_test.txt")
        try:
            with open(test_file, 'w') as f:
                f.write("Debug test file")
            logger.info(f"Successfully wrote test file to {test_file}")
            os.remove(test_file)
            logger.info(f"Removed test file {test_file}")
        except Exception as e:
            logger.error(f"Failed to write test file: {str(e)}")
            return False
            
        return True
    except Exception as e:
        logger.error(f"Error checking directory permissions: {str(e)}")
        return False

def list_hls_files():
    """List all HLS files in the directory"""
    logger.info("Listing HLS files...")
    
    if not os.path.exists(HLS_DIR):
        logger.error(f"HLS directory {HLS_DIR} does not exist")
        return False
    
    try:
        files = os.listdir(HLS_DIR)
        if not files:
            logger.warning("No files found in HLS directory")
        else:
            logger.info(f"Found {len(files)} files in HLS directory:")
            m3u8_files = []
            ts_files = []
            other_files = []
            
            for file in files:
                file_path = os.path.join(HLS_DIR, file)
                file_size = os.path.getsize(file_path)
                file_time = os.path.getmtime(file_path)
                
                if file.endswith('.m3u8'):
                    m3u8_files.append((file, file_size, file_time))
                elif file.endswith('.ts'):
                    ts_files.append((file, file_size, file_time))
                else:
                    other_files.append((file, file_size, file_time))
            
            # Print m3u8 files
            if m3u8_files:
                logger.info("M3U8 Playlist files:")
                for file, size, mtime in m3u8_files:
                    logger.info(f"  - {file} ({size} bytes, modified: {time.ctime(mtime)})")
                    # Try to read the file content
                    try:
                        with open(os.path.join(HLS_DIR, file), 'r') as f:
                            content = f.read()
                        logger.info(f"    Content: {content[:200]}...")
                    except Exception as e:
                        logger.error(f"    Error reading file: {str(e)}")
            
            # Print ts files (just count them by prefix)
            if ts_files:
                prefixes = {}
                for file, size, _ in ts_files:
                    prefix = file.split('_')[0] if '_' in file else file.split('.')[0]
                    if prefix not in prefixes:
                        prefixes[prefix] = []
                    prefixes[prefix].append((file, size))
                
                logger.info("TS Segment files:")
                for prefix, files in prefixes.items():
                    logger.info(f"  - {prefix}: {len(files)} segments, total size: {sum(size for _, size in files)} bytes")
            
            # Print other files
            if other_files:
                logger.info("Other files:")
                for file, size, mtime in other_files:
                    logger.info(f"  - {file} ({size} bytes, modified: {time.ctime(mtime)})")
        
        return True
    except Exception as e:
        logger.error(f"Error listing HLS files: {str(e)}")
        return False

def check_nginx_hls():
    """Check if nginx is serving HLS files"""
    logger.info("Checking if nginx is serving HLS files...")
    
    try:
        # Try to access the HLS directory via nginx
        response = requests.get(NGINX_HLS_URL, timeout=5)
        if response.status_code == 200:
            logger.info(f"Successfully accessed {NGINX_HLS_URL}")
            logger.info(f"Response: {response.text[:200]}...")
            return True
        else:
            logger.error(f"Failed to access {NGINX_HLS_URL}, status code: {response.status_code}")
            return False
    except Exception as e:
        logger.error(f"Error accessing {NGINX_HLS_URL}: {str(e)}")
        return False

def create_test_hls():
    """Create a test HLS file and check if it's accessible"""
    logger.info("Creating test HLS file...")
    
    if not os.path.exists(HLS_DIR):
        logger.error(f"HLS directory {HLS_DIR} does not exist")
        return False
    
    try:
        # Create a test m3u8 file
        test_m3u8 = os.path.join(HLS_DIR, "debug_test.m3u8")
        with open(test_m3u8, 'w') as f:
            f.write("""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:4.000000,
debug_test_segment.ts
#EXT-X-ENDLIST""")
        logger.info(f"Created test m3u8 file: {test_m3u8}")
        
        # Create a dummy TS file
        test_ts = os.path.join(HLS_DIR, "debug_test_segment.ts")
        with open(test_ts, 'wb') as f:
            f.write(b"This is a test TS segment" * 100)  # Make it a reasonable size
        logger.info(f"Created test TS file: {test_ts}")
        
        # Try to access the test file via nginx
        try:
            response = requests.get(f"{NGINX_HLS_URL}/debug_test.m3u8", timeout=5)
            if response.status_code == 200:
                logger.info(f"Successfully accessed test m3u8 via nginx")
                logger.info(f"Response: {response.text}")
                
                # Try to access the test file via external URL
                try:
                    ext_response = requests.get(f"{EXTERNAL_HLS_URL}/debug_test.m3u8", timeout=5)
                    if ext_response.status_code == 200:
                        logger.info(f"Successfully accessed test m3u8 via external URL")
                        logger.info(f"Response: {ext_response.text}")
                    else:
                        logger.error(f"Failed to access test m3u8 via external URL, status code: {ext_response.status_code}")
                except Exception as e:
                    logger.error(f"Error accessing test m3u8 via external URL: {str(e)}")
            else:
                logger.error(f"Failed to access test m3u8 via nginx, status code: {response.status_code}")
        except Exception as e:
            logger.error(f"Error accessing test m3u8 via nginx: {str(e)}")
        
        # Clean up
        try:
            os.remove(test_m3u8)
            os.remove(test_ts)
            logger.info("Removed test files")
        except Exception as e:
            logger.error(f"Error removing test files: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating test HLS file: {str(e)}")
        return False

def check_nginx_config():
    """Check nginx configuration"""
    logger.info("Checking nginx configuration...")
    
    try:
        # Run nginx -T to check configuration
        result = subprocess.run(["curl", "-s", "http://nginx-rtmp:8000/stat"], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Nginx RTMP status:")
            logger.info(result.stdout)
        else:
            logger.error(f"Failed to check nginx status: {result.stderr}")
        
        return True
    except Exception as e:
        logger.error(f"Error checking nginx configuration: {str(e)}")
        return False

def test_stream_generation(stream_id="debug_test", source_url=None, duration=30):
    """Test stream generation with a sample URL"""
    logger.info(f"Testing stream generation with ID: {stream_id}")
    
    if source_url is None:
        # Use a reliable test stream if none provided
        source_url = "https://apollo.production-public.tubi.io/live/ac-koco.m3u8"
        logger.info(f"Using default test stream: {source_url}")
    
    # Clean up any existing test files
    cleanup_test_files(stream_id)
    
    # Define output paths
    rtmp_output = f"rtmp://nginx-rtmp:1935/live/{stream_id}"
    hls_path = f"{HLS_DIR}/{stream_id}.m3u8"
    
    # Test 1: Simple RTMP output (let nginx-rtmp handle HLS conversion)
    logger.info("TEST 1: Simple RTMP output (nginx-rtmp handles HLS)")
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-i", source_url,
        "-c:v", "copy",
        "-c:a", "copy",
        "-f", "flv",
        rtmp_output
    ]
    
    logger.info(f"Executing command: {' '.join(ffmpeg_cmd)}")
    
    try:
        # Start the ffmpeg process
        process = subprocess.Popen(
            ffmpeg_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to see if the process crashes immediately
        time.sleep(2)
        
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            logger.error(f"FFmpeg process failed: {stderr}")
            return False
        
        # Monitor for HLS files
        start_time = time.time()
        hls_files_found = False
        
        while time.time() - start_time < duration:
            # Check if HLS files exist
            if os.path.exists(hls_path):
                logger.info(f"HLS playlist found: {hls_path}")
                
                # Check for TS segments
                ts_files = [f for f in os.listdir(HLS_DIR) if f.startswith(f"{stream_id}_") and f.endswith(".ts")]
                if ts_files:
                    logger.info(f"Found {len(ts_files)} TS segment files")
                    hls_files_found = True
                    break
            
            # List all files in the directory for debugging
            files = os.listdir(HLS_DIR)
            logger.info(f"Current files in HLS directory: {files}")
            
            # Wait before checking again
            time.sleep(5)
        
        # Always terminate the process when done
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except:
                process.kill()
        
        if hls_files_found:
            logger.info("TEST 1 SUCCESSFUL: HLS files were generated by nginx-rtmp")
            
            # Try to access the HLS playlist via HTTP
            try:
                response = requests.get(f"{NGINX_HLS_URL}/{stream_id}.m3u8", timeout=5)
                if response.status_code == 200:
                    logger.info(f"Successfully accessed HLS playlist via HTTP: {response.text[:100]}...")
                else:
                    logger.warning(f"Failed to access HLS playlist via HTTP: {response.status_code}")
            except Exception as e:
                logger.error(f"Error accessing HLS playlist via HTTP: {str(e)}")
            
            return True
        else:
            logger.error("TEST 1 FAILED: No HLS files were generated")
            return False
            
    except Exception as e:
        logger.error(f"Error testing stream generation: {str(e)}")
        return False

def cleanup_test_files(stream_id):
    """Clean up test files for the given stream ID"""
    logger.info(f"Cleaning up test files for stream ID: {stream_id}")
    
    try:
        # Use glob to find all matching files
        import glob
        file_patterns = [
            f"{HLS_DIR}/{stream_id}.m3u8",
            f"{HLS_DIR}/{stream_id}_*.ts"
        ]
        
        for pattern in file_patterns:
            for file_path in glob.glob(pattern):
                logger.info(f"Removing file: {file_path}")
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.error(f"Error removing file {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error cleaning up test files: {str(e)}")

def run_all_tests():
    """Run all tests"""
    logger.info("Running all tests...")
    
    results = {
        "directory_structure": check_directory_structure(),
        "list_hls_files": list_hls_files(),
        "nginx_hls": check_nginx_hls(),
        "create_test_hls": create_test_hls(),
        "nginx_config": check_nginx_config(),
        "test_stream": test_stream_generation()
    }
    
    logger.info("Test results:")
    for test, result in results.items():
        logger.info(f"  - {test}: {'PASS' if result else 'FAIL'}")
    
    return all(results.values())

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="HLS Debug Tool for IPTV Re-Streaming Application")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--dir", action="store_true", help="Check directory structure")
    parser.add_argument("--list", action="store_true", help="List HLS files")
    parser.add_argument("--nginx", action="store_true", help="Check nginx HLS serving")
    parser.add_argument("--test-hls", action="store_true", help="Create and test HLS file")
    parser.add_argument("--config", action="store_true", help="Check nginx configuration")
    parser.add_argument("--stream", action="store_true", help="Test stream generation")
    parser.add_argument("--stream-id", type=str, default="debug_test", help="Stream ID for testing")
    parser.add_argument("--duration", type=int, default=30, help="Duration for stream test in seconds")
    
    args = parser.parse_args()
    
    # If no arguments are provided, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return
    
    # Run tests based on arguments
    if args.all:
        run_all_tests()
    else:
        if args.dir:
            check_directory_structure()
        if args.list:
            list_hls_files()
        if args.nginx:
            check_nginx_hls()
        if args.test_hls:
            create_test_hls()
        if args.config:
            check_nginx_config()
        if args.stream:
            test_stream_generation(args.stream_id, duration=args.duration)

if __name__ == "__main__":
    main()
