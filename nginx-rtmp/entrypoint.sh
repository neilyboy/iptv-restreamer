#!/bin/sh

echo "Starting nginx-rtmp server..."
echo "Ensuring HLS directory exists and has proper permissions..."

# Create HLS directory and set permissions
mkdir -p /tmp/hls
chmod -R 777 /tmp/hls
chown -R nobody:nogroup /tmp/hls

# Create a test file to verify permissions
echo "#EXTM3U\n#EXT-X-VERSION:3" > /tmp/hls/test.m3u8
dd if=/dev/zero of=/tmp/hls/test.ts bs=1024 count=10

echo "HLS directory setup complete. Contents:"
ls -la /tmp/hls

echo "Starting nginx..."
nginx -g "daemon off;"
