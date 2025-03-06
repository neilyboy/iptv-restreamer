#!/bin/bash
# HLS Testing and Fixing Script for IPTV Re-Streaming Application
# This script provides tools to test and fix HLS streaming issues

# Set colors for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}  HLS Testing and Fixing Tool v2.0${NC}"
echo -e "${BLUE}  For IPTV Re-Streaming Application${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Function to check if Docker is running
check_docker() {
  echo -e "${YELLOW}Checking if Docker is running...${NC}"
  if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Docker is not running. Please start Docker and try again.${NC}"
    exit 1
  else
    echo -e "${GREEN}Docker is running.${NC}"
  fi
}

# Function to check container status
check_containers() {
  echo -e "${YELLOW}Checking container status...${NC}"
  
  # Check if containers are running
  if [ "$(docker-compose ps -q nginx-rtmp)" ] && [ "$(docker ps -q --no-trunc | grep $(docker-compose ps -q nginx-rtmp))" ]; then
    echo -e "${GREEN}nginx-rtmp container is running.${NC}"
  else
    echo -e "${RED}nginx-rtmp container is not running.${NC}"
  fi
  
  if [ "$(docker-compose ps -q backend)" ] && [ "$(docker ps -q --no-trunc | grep $(docker-compose ps -q backend))" ]; then
    echo -e "${GREEN}backend container is running.${NC}"
  else
    echo -e "${RED}backend container is not running.${NC}"
  fi
}

# Function to check HLS directory permissions
check_hls_permissions() {
  echo -e "${YELLOW}Checking HLS directory permissions...${NC}"
  
  # Check nginx-rtmp container
  echo -e "${BLUE}Checking nginx-rtmp container:${NC}"
  docker-compose exec nginx-rtmp sh -c "ls -la /tmp/hls"
  
  # Check backend container
  echo -e "${BLUE}Checking backend container:${NC}"
  docker-compose exec backend sh -c "ls -la /tmp/hls"
  
  # Test write permissions
  echo -e "${YELLOW}Testing write permissions...${NC}"
  
  # Test nginx-rtmp
  echo -e "${BLUE}Testing nginx-rtmp container:${NC}"
  if docker-compose exec nginx-rtmp sh -c "echo 'test' > /tmp/hls/nginx_test.txt && cat /tmp/hls/nginx_test.txt"; then
    echo -e "${GREEN}nginx-rtmp container can write to HLS directory.${NC}"
  else
    echo -e "${RED}nginx-rtmp container CANNOT write to HLS directory.${NC}"
  fi
  
  # Test backend
  echo -e "${BLUE}Testing backend container:${NC}"
  if docker-compose exec backend sh -c "echo 'test' > /tmp/hls/backend_test.txt && cat /tmp/hls/backend_test.txt"; then
    echo -e "${GREEN}backend container can write to HLS directory.${NC}"
  else
    echo -e "${RED}backend container CANNOT write to HLS directory.${NC}"
  fi
}

# Function to test HLS serving
test_hls_serving() {
  echo -e "${YELLOW}Testing HLS serving via nginx...${NC}"
  
  # Create a test HLS file
  echo -e "${BLUE}Creating test HLS file...${NC}"
  docker-compose exec nginx-rtmp sh -c "echo '#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXT-X-MEDIA-SEQUENCE:0
#EXTINF:4.000000,
test_segment.ts
#EXT-X-ENDLIST' > /tmp/hls/test.m3u8"

  # Create a dummy TS file
  echo -e "${BLUE}Creating test TS segment...${NC}"
  docker-compose exec nginx-rtmp sh -c "dd if=/dev/zero of=/tmp/hls/test_segment.ts bs=1024 count=10"
  
  # Test accessing the file via nginx
  echo -e "${BLUE}Testing access via nginx...${NC}"
  if curl -s http://localhost:8088/hls/test.m3u8 | grep -q "#EXTM3U"; then
    echo -e "${GREEN}HLS files are being served correctly by nginx.${NC}"
  else
    echo -e "${RED}HLS files are NOT being served correctly by nginx.${NC}"
    echo -e "${YELLOW}Response from nginx:${NC}"
    curl -v http://localhost:8088/hls/test.m3u8
  fi
}

# Function to fix HLS directory permissions
fix_hls_permissions() {
  echo -e "${YELLOW}Fixing HLS directory permissions...${NC}"
  
  # Fix in nginx-rtmp container
  echo -e "${BLUE}Fixing in nginx-rtmp container...${NC}"
  docker-compose exec nginx-rtmp sh -c "mkdir -p /tmp/hls && chmod -R 777 /tmp/hls && chown -R nobody:nogroup /tmp/hls"
  
  # Fix in backend container
  echo -e "${BLUE}Fixing in backend container...${NC}"
  docker-compose exec backend sh -c "mkdir -p /tmp/hls && chmod -R 777 /tmp/hls"
  
  # Verify fixes
  check_hls_permissions
}

# Function to test a stream
test_stream() {
  echo -e "${YELLOW}Testing a stream...${NC}"
  
  # Ask for a test stream URL
  read -p "Enter a test stream URL (or press Enter for a test pattern): " stream_url
  
  if [ -z "$stream_url" ]; then
    stream_url="testsrc=size=640x480:rate=30,format=yuv420p"
    echo -e "${BLUE}Using test pattern as source.${NC}"
  fi
  
  # Generate a random stream ID
  stream_id="test_$(date +%s)"
  echo -e "${BLUE}Using stream ID: ${stream_id}${NC}"
  
  # Start the stream
  echo -e "${BLUE}Starting test stream...${NC}"
  if [ "$stream_url" == "testsrc=size=640x480:rate=30,format=yuv420p" ]; then
    # Use ffmpeg with test source
    docker-compose exec -d backend sh -c "ffmpeg -re -f lavfi -i \"${stream_url}\" -c:v libx264 -b:v 800k -f flv rtmp://nginx-rtmp:1935/live/${stream_id}"
  else
    # Use ffmpeg with external source
    docker-compose exec -d backend sh -c "ffmpeg -re -i \"${stream_url}\" -c:v copy -c:a copy -f flv rtmp://nginx-rtmp:1935/live/${stream_id}"
  fi
  
  # Wait for HLS files to be generated
  echo -e "${BLUE}Waiting for HLS files to be generated...${NC}"
  for i in {1..10}; do
    echo -e "${YELLOW}Checking for HLS files (attempt $i/10)...${NC}"
    if docker-compose exec nginx-rtmp sh -c "ls -la /tmp/hls | grep -E '${stream_id}|stream_${stream_id}'"; then
      echo -e "${GREEN}HLS files found!${NC}"
      break
    fi
    
    if [ $i -eq 10 ]; then
      echo -e "${RED}No HLS files generated after 10 attempts.${NC}"
    fi
    
    sleep 3
  done
  
  # Check if the stream is accessible
  echo -e "${BLUE}Testing if stream is accessible...${NC}"
  if curl -s http://localhost:8088/hls/${stream_id}.m3u8 | grep -q "#EXTM3U" || \
     curl -s http://localhost:8088/hls/stream_${stream_id}.m3u8 | grep -q "#EXTM3U"; then
    echo -e "${GREEN}Stream is accessible via HLS!${NC}"
    echo -e "${GREEN}HLS URL: http://localhost:8088/hls/${stream_id}.m3u8${NC}"
    echo -e "${GREEN}Alternative URL: http://localhost:8088/hls/stream_${stream_id}.m3u8${NC}"
  else
    echo -e "${RED}Stream is NOT accessible via HLS.${NC}"
  fi
  
  # Ask if user wants to stop the test stream
  read -p "Do you want to stop the test stream? (y/n): " stop_stream
  if [ "$stop_stream" == "y" ] || [ "$stop_stream" == "Y" ]; then
    echo -e "${BLUE}Stopping test stream...${NC}"
    docker-compose exec backend sh -c "pkill -f \"ffmpeg.*${stream_id}\""
    echo -e "${GREEN}Test stream stopped.${NC}"
  else
    echo -e "${YELLOW}Test stream will continue running in the background.${NC}"
    echo -e "${YELLOW}Stream ID: ${stream_id}${NC}"
  fi
}

# Function to check nginx configuration
check_nginx_config() {
  echo -e "${YELLOW}Checking nginx configuration...${NC}"
  docker-compose exec nginx-rtmp sh -c "nginx -T | grep -A 20 'rtmp\|http'"
}

# Function to restart containers
restart_containers() {
  echo -e "${YELLOW}Restarting containers...${NC}"
  docker-compose restart nginx-rtmp backend
  echo -e "${GREEN}Containers restarted.${NC}"
  
  # Wait for containers to be ready
  echo -e "${BLUE}Waiting for containers to be ready...${NC}"
  sleep 5
  check_containers
}

# Function to rebuild containers
rebuild_containers() {
  echo -e "${YELLOW}Rebuilding containers...${NC}"
  docker-compose up -d --build nginx-rtmp backend
  echo -e "${GREEN}Containers rebuilt.${NC}"
  
  # Wait for containers to be ready
  echo -e "${BLUE}Waiting for containers to be ready...${NC}"
  sleep 5
  check_containers
}

# Function to run all tests
run_all_tests() {
  check_docker
  check_containers
  check_hls_permissions
  test_hls_serving
  check_nginx_config
}

# Main menu
while true; do
  echo ""
  echo -e "${BLUE}=========================================${NC}"
  echo -e "${BLUE}  HLS Testing and Fixing Tool - Menu${NC}"
  echo -e "${BLUE}=========================================${NC}"
  echo ""
  echo -e "${YELLOW}1. Check container status${NC}"
  echo -e "${YELLOW}2. Check HLS directory permissions${NC}"
  echo -e "${YELLOW}3. Fix HLS directory permissions${NC}"
  echo -e "${YELLOW}4. Test HLS serving via nginx${NC}"
  echo -e "${YELLOW}5. Check nginx configuration${NC}"
  echo -e "${YELLOW}6. Test a stream${NC}"
  echo -e "${YELLOW}7. Restart containers${NC}"
  echo -e "${YELLOW}8. Rebuild containers${NC}"
  echo -e "${YELLOW}9. Run all tests${NC}"
  echo -e "${YELLOW}0. Exit${NC}"
  echo ""
  read -p "Enter your choice: " choice
  
  case $choice in
    1) check_containers ;;
    2) check_hls_permissions ;;
    3) fix_hls_permissions ;;
    4) test_hls_serving ;;
    5) check_nginx_config ;;
    6) test_stream ;;
    7) restart_containers ;;
    8) rebuild_containers ;;
    9) run_all_tests ;;
    0) echo -e "${GREEN}Exiting.${NC}"; exit 0 ;;
    *) echo -e "${RED}Invalid choice. Please try again.${NC}" ;;
  esac
  
  echo ""
  read -p "Press Enter to continue..."
done
