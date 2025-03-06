#!/bin/sh
# Docker entrypoint script for backend container

echo "Starting backend container..."

# Ensure HLS directory exists and has proper permissions
echo "Ensuring HLS directory exists and has proper permissions..."
mkdir -p /tmp/hls
chmod -R 777 /tmp/hls
echo "HLS directory setup:"
ls -la /tmp/hls

# Create a test file to verify write permissions
echo "Creating test file to verify write permissions..."
echo "Test file" > /tmp/hls/backend_test.txt
if [ -f /tmp/hls/backend_test.txt ]; then
  echo "Successfully created test file"
  cat /tmp/hls/backend_test.txt
  # Keep the file for debugging
else
  echo "ERROR: Failed to create test file in /tmp/hls"
  exit 1
fi

# Wait for nginx-rtmp to be ready
echo "Waiting for nginx-rtmp to be ready..."
for i in $(seq 1 30); do
  if curl -s http://nginx-rtmp:8000/ping > /dev/null; then
    echo "nginx-rtmp is ready!"
    
    # Verify HLS directory is accessible from nginx-rtmp
    echo "Checking if HLS directory is accessible from nginx-rtmp..."
    if curl -s http://nginx-rtmp:8000/hls/ | grep -q "backend_test.txt"; then
      echo "HLS directory is properly shared between containers!"
    else
      echo "WARNING: Test file not visible via nginx-rtmp, but continuing anyway..."
    fi
    
    break
  fi
  echo "Waiting for nginx-rtmp... ($i/30)"
  sleep 1
done

# Start the backend application
echo "Starting backend application..."
exec uvicorn main:app --host 0.0.0.0 --port 8080
