#!/usr/bin/env python3
"""
Test Script for Stream Manager
This script tests the stream_manager.py functionality
"""

import os
import sys
import time
import logging
import argparse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from stream_manager import stream_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test_stream_manager")

def setup_database():
    """Set up a database connection"""
    try:
        # Get database URL from environment or use default
        database_url = os.environ.get("DATABASE_URL", "postgresql://iptv:iptv_password@db:5432/iptv_streams")
        
        # Create engine and session
        engine = create_engine(database_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        
        return session
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return None

def test_start_stream(db, stream_id, wait_time=60):
    """Test starting a stream"""
    logger.info(f"Testing start_stream for stream ID: {stream_id}")
    
    # Start the stream
    result = stream_manager.start_stream(db, stream_id)
    
    if not result:
        logger.error(f"Failed to start stream {stream_id}")
        return False
    
    logger.info(f"Stream {stream_id} started successfully")
    
    # Wait for specified time to allow HLS files to be generated
    logger.info(f"Waiting {wait_time} seconds for HLS files to be generated...")
    
    # Check status every 10 seconds
    for i in range(wait_time // 10):
        time.sleep(10)
        status = stream_manager.check_stream_status(db, stream_id)
        logger.info(f"Stream status after {(i+1)*10} seconds: {status}")
        
        if status.get("hls_file_exists", False):
            logger.info(f"HLS files found for stream {stream_id}")
            return True
    
    logger.warning(f"No HLS files found for stream {stream_id} after {wait_time} seconds")
    return False

def test_stop_stream(db, stream_id):
    """Test stopping a stream"""
    logger.info(f"Testing stop_stream for stream ID: {stream_id}")
    
    # Stop the stream
    result = stream_manager.stop_stream(db, stream_id)
    
    if not result:
        logger.error(f"Failed to stop stream {stream_id}")
        return False
    
    logger.info(f"Stream {stream_id} stopped successfully")
    return True

def main():
    parser = argparse.ArgumentParser(description="Test Stream Manager functionality")
    parser.add_argument("--stream-id", type=int, required=True, help="Stream ID to test")
    parser.add_argument("--wait-time", type=int, default=60, help="Time to wait for HLS files (seconds)")
    parser.add_argument("--stop", action="store_true", help="Stop the stream after testing")
    
    args = parser.parse_args()
    
    # Set up database
    db = setup_database()
    if not db:
        logger.error("Failed to set up database")
        sys.exit(1)
    
    try:
        # Test starting the stream
        start_success = test_start_stream(db, args.stream_id, args.wait_time)
        
        if start_success:
            logger.info("Stream start test SUCCESSFUL")
        else:
            logger.error("Stream start test FAILED")
        
        # Test stopping the stream if requested
        if args.stop:
            stop_success = test_stop_stream(db, args.stream_id)
            
            if stop_success:
                logger.info("Stream stop test SUCCESSFUL")
            else:
                logger.error("Stream stop test FAILED")
    finally:
        # Close database session
        db.close()

if __name__ == "__main__":
    main()
