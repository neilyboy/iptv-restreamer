#!/usr/bin/env python3
"""
HLS Directory Debugging Tool
This script helps diagnose issues with HLS directory creation and permissions
"""

import os
import subprocess
import sys
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("hls-debug")

def check_hls_directory():
    """Check if the HLS directory exists and has proper permissions"""
    hls_dir = "/tmp/hls"
    logger.info(f"Checking HLS directory: {hls_dir}")
    
    # Check if directory exists
    if not os.path.exists(hls_dir):
        logger.error(f"HLS directory {hls_dir} does not exist!")
        logger.info("Creating directory...")
        try:
            os.makedirs(hls_dir, exist_ok=True)
            os.chmod(hls_dir, 0o777)  # Full permissions
            logger.info(f"Created directory {hls_dir} with full permissions")
        except Exception as e:
            logger.error(f"Failed to create directory: {str(e)}")
            return False
    
    # Check permissions
    try:
        permissions = oct(os.stat(hls_dir).st_mode)[-3:]
        logger.info(f"HLS directory permissions: {permissions}")
        
        # Test write access
        test_file = os.path.join(hls_dir, "test_write.txt")
        with open(test_file, 'w') as f:
            f.write("Test write access")
        
        if os.path.exists(test_file):
            logger.info("Write test successful")
            os.remove(test_file)
        else:
            logger.error("Failed to write test file")
            return False
            
    except Exception as e:
        logger.error(f"Error checking permissions: {str(e)}")
        return False
    
    return True

def list_directories():
    """List all directories in /tmp"""
    logger.info("Listing directories in /tmp:")
    try:
        result = subprocess.run(["ls", "-la", "/tmp"], capture_output=True, text=True)
        logger.info(f"Contents of /tmp:\n{result.stdout}")
        
        # Try to list /tmp/hls if it exists
        if os.path.exists("/tmp/hls"):
            result = subprocess.run(["ls", "-la", "/tmp/hls"], capture_output=True, text=True)
            logger.info(f"Contents of /tmp/hls:\n{result.stdout}")
        else:
            logger.error("/tmp/hls directory does not exist")
    except Exception as e:
        logger.error(f"Error listing directories: {str(e)}")
        return False
    
    return True

def check_nginx_hls():
    """Check if nginx-rtmp container has the HLS directory"""
    logger.info("Checking nginx-rtmp container HLS directory:")
    try:
        # This assumes the script is run inside the backend container
        result = subprocess.run(["ping", "-c", "1", "nginx-rtmp"], capture_output=True, text=True)
        logger.info(f"Ping nginx-rtmp result: {result.returncode}")
        
        # Try to curl the nginx ping endpoint
        result = subprocess.run(["curl", "-s", "http://nginx-rtmp:8000/ping"], capture_output=True, text=True)
        logger.info(f"Curl nginx-rtmp ping result: {result.stdout}")
        
        # Try to curl the HLS directory
        result = subprocess.run(["curl", "-s", "http://nginx-rtmp:8000/hls/"], capture_output=True, text=True)
        logger.info(f"Curl nginx-rtmp HLS directory result: {result.returncode}")
        
    except Exception as e:
        logger.error(f"Error checking nginx-rtmp: {str(e)}")
        return False
    
    return True

def create_test_hls_files():
    """Create test HLS files in the directory"""
    hls_dir = "/tmp/hls"
    logger.info(f"Creating test HLS files in {hls_dir}")
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(hls_dir, exist_ok=True)
        os.chmod(hls_dir, 0o777)  # Full permissions
        
        # Create a test m3u8 file
        m3u8_content = """#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:4.000000,
test_segment_0.ts
#EXTINF:4.000000,
test_segment_1.ts
#EXTINF:4.000000,
test_segment_2.ts
#EXT-X-ENDLIST"""
        
        with open(os.path.join(hls_dir, "test_stream.m3u8"), "w") as f:
            f.write(m3u8_content)
        
        # Create dummy TS files
        for i in range(3):
            with open(os.path.join(hls_dir, f"test_segment_{i}.ts"), "wb") as f:
                f.write(b"This is a test TS file")
        
        logger.info("Test HLS files created successfully")
        
        # List the files
        result = subprocess.run(["ls", "-la", hls_dir], capture_output=True, text=True)
        logger.info(f"Contents of {hls_dir} after creating test files:\n{result.stdout}")
        
        return True
    except Exception as e:
        logger.error(f"Error creating test HLS files: {str(e)}")
        return False

def main():
    logger.info("=== HLS Directory Debug Tool ===")
    
    # Check HLS directory
    check_hls_directory()
    
    # List directories
    list_directories()
    
    # Check nginx-rtmp
    check_nginx_hls()
    
    # Create test HLS files
    create_test_hls_files()
    
    logger.info("=== Debug completed ===")

if __name__ == "__main__":
    main()
