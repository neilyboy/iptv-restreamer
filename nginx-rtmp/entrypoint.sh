#!/bin/sh

echo "Starting nginx-rtmp server..."
echo "Ensuring HLS directory exists and has proper permissions..."

# Clean up any existing HLS files
rm -rf /tmp/hls/*

# Create HLS directory and set permissions
mkdir -p /tmp/hls
chmod -R 777 /tmp/hls
chown -R nobody:nogroup /tmp/hls

# Create test files to verify permissions and HLS functionality
cat > /tmp/hls/test.m3u8 << EOF
#EXTM3U
#EXT-X-VERSION:3
#EXT-X-TARGETDURATION:4
#EXTINF:4.0,
test.ts
#EXT-X-ENDLIST
EOF

dd if=/dev/zero of=/tmp/hls/test.ts bs=1024 count=10

echo "HLS directory setup complete. Contents:"
ls -la /tmp/hls

# Enable nginx debug logging
export NGINX_ENTRYPOINT_QUIET_LOGS=""

echo "Starting nginx..."
nginx -g "daemon off;" -e /dev/stdout
