#!/bin/bash
# HLS Debugging Script for IPTV Re-Streaming Application

echo "===== HLS Debugging Tool ====="
echo "This script helps diagnose and fix HLS streaming issues"
echo

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Error: docker-compose is not installed"
    exit 1
fi

# Check if the application is running
if ! docker-compose ps | grep -q "nginx-rtmp"; then
    echo "Error: IPTV Re-Streaming application is not running"
    echo "Please start it with: docker-compose up -d"
    exit 1
fi

# Function to check HLS directory
check_hls_directory() {
    echo "===== Checking HLS Directory ====="
    docker-compose exec nginx-rtmp sh -c "ls -la /tmp/hls"
    
    # Check permissions
    docker-compose exec nginx-rtmp sh -c "stat -c '%a %n' /tmp/hls"
    
    # Try to create a test file
    echo "Creating test file in HLS directory..."
    docker-compose exec nginx-rtmp sh -c "echo 'test' > /tmp/hls/test_file.txt && echo 'Success!' || echo 'Failed!'"
    
    # Check if backend can access the directory
    echo "Checking if backend can access HLS directory..."
    docker-compose exec backend sh -c "ls -la /tmp/hls"
}

# Function to check nginx configuration
check_nginx_config() {
    echo "===== Checking Nginx Configuration ====="
    docker-compose exec nginx-rtmp sh -c "cat /etc/nginx/nginx.conf | grep -A 20 'rtmp'"
    docker-compose exec nginx-rtmp sh -c "cat /etc/nginx/nginx.conf | grep -A 20 'location /hls'"
    
    # Test nginx configuration
    echo "Testing nginx configuration..."
    docker-compose exec nginx-rtmp sh -c "nginx -t"
}

# Function to test stream generation
test_stream() {
    echo "===== Testing Stream Generation ====="
    
    # Get stream ID
    read -p "Enter stream ID (default: test): " stream_id
    stream_id=${stream_id:-test}
    
    # Get stream URL
    read -p "Enter stream URL (default: https://apollo.production-public.tubi.io/live/ac-koco.m3u8): " stream_url
    stream_url=${stream_url:-https://apollo.production-public.tubi.io/live/ac-koco.m3u8}
    
    # Get duration
    read -p "Enter test duration in seconds (default: 30): " duration
    duration=${duration:-30}
    
    echo "Running debug_hls.py with stream test..."
    docker-compose exec backend python debug_hls.py --stream --stream-id "$stream_id" --duration "$duration"
}

# Function to run all debug tools
run_all_tests() {
    echo "===== Running All Debug Tests ====="
    docker-compose exec backend python debug_hls.py --all
}

# Function to fix common issues
fix_common_issues() {
    echo "===== Fixing Common Issues ====="
    
    # Fix permissions
    echo "Fixing HLS directory permissions..."
    docker-compose exec nginx-rtmp sh -c "mkdir -p /tmp/hls && chmod -R 777 /tmp/hls && chown -R nobody:nogroup /tmp/hls"
    docker-compose exec backend sh -c "mkdir -p /tmp/hls && chmod -R 777 /tmp/hls"
    
    # Restart services
    echo "Restarting services..."
    docker-compose restart nginx-rtmp
    docker-compose restart backend
    
    echo "Waiting for services to start..."
    sleep 5
    
    # Check if services are running
    docker-compose ps
}

# Function to view logs
view_logs() {
    echo "===== Viewing Logs ====="
    
    # Get number of lines
    read -p "Enter number of lines to show (default: 50): " lines
    lines=${lines:-50}
    
    echo "Nginx-RTMP logs:"
    docker-compose logs --tail="$lines" nginx-rtmp
    
    echo "Backend logs:"
    docker-compose logs --tail="$lines" backend
}

# Main menu
while true; do
    echo
    echo "===== HLS Debugging Menu ====="
    echo "1. Check HLS Directory"
    echo "2. Check Nginx Configuration"
    echo "3. Test Stream Generation"
    echo "4. Run All Debug Tests"
    echo "5. Fix Common Issues"
    echo "6. View Logs"
    echo "0. Exit"
    echo
    
    read -p "Enter your choice: " choice
    
    case $choice in
        1) check_hls_directory ;;
        2) check_nginx_config ;;
        3) test_stream ;;
        4) run_all_tests ;;
        5) fix_common_issues ;;
        6) view_logs ;;
        0) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid choice" ;;
    esac
done
