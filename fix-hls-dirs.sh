#!/bin/bash
# Script to fix HLS directory issues in the IPTV restreamer

echo "==== IPTV Restreamer HLS Directory Fix Script ===="
echo "This script will check and fix HLS directory issues"

# Check if docker and docker-compose are installed
if ! command -v docker &> /dev/null; then
    echo "Error: docker is not installed or not in PATH"
    exit 1
fi

# Stop containers first
echo "Stopping containers..."
docker-compose down

# Create the HLS directory in the host if it doesn't exist
echo "Creating HLS directory in host..."
mkdir -p ./hls-data
chmod -R 777 ./hls-data

# Update docker-compose.yml to use bind mount instead of volume
echo "Updating docker-compose.yml to use bind mount..."
cat > docker-compose.yml << 'EOL'
version: '3'

services:
  # Frontend web interface
  frontend:
    build:
      context: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    networks:
      - iptv-network
    restart: unless-stopped
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api

  # Backend API and process manager
  backend:
    build:
      context: ./backend
    ports:
      - "8000:8080"  # Map host port 8000 to container port 8080
    volumes:
      - ./backend:/app
      - /var/run/docker.sock:/var/run/docker.sock
      - ./hls-data:/tmp/hls  # Bind mount to host directory
    depends_on:
      - db
      - nginx-rtmp
    networks:
      - iptv-network
    restart: unless-stopped
    environment:
      - DATABASE_URL=postgresql://iptv:iptv_password@db:5432/iptv_streams
      - RTMP_SERVER_URL=rtmp://nginx-rtmp:1935/live
      - HLS_SERVER_URL=http://nginx-rtmp:8000/hls

  # Media server (Nginx with RTMP module)
  nginx-rtmp:
    build:
      context: ./nginx-rtmp
    ports:
      - "8088:8000"  # Map HLS port to 8088 to avoid conflict with backend
      - "1935:1935"  # RTMP port
    volumes:
      - ./hls-data:/tmp/hls  # Bind mount to host directory
    networks:
      - iptv-network
    restart: unless-stopped
    # Add healthcheck to ensure the container is running properly
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s

  # Database for storing stream configurations
  db:
    image: postgres:13-alpine
    environment:
      POSTGRES_USER: iptv
      POSTGRES_PASSWORD: iptv_password
      POSTGRES_DB: iptv_streams
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - iptv-network
    restart: unless-stopped

networks:
  iptv-network:
    driver: bridge

volumes:
  postgres_data:
EOL

# Update nginx-rtmp Dockerfile
echo "Updating nginx-rtmp Dockerfile..."
cat > nginx-rtmp/Dockerfile << 'EOL'
FROM tiangolo/nginx-rtmp

# Copy custom configuration
COPY config/nginx.conf /etc/nginx/nginx.conf

# Create a simple mime.types file directly
RUN echo "types { \
    text/html html htm shtml; \
    text/css css; \
    text/xml xml; \
    image/gif gif; \
    image/jpeg jpeg jpg; \
    application/javascript js; \
    application/json json; \
    video/mp2t ts; \
    application/vnd.apple.mpegurl m3u8; \
    video/mp4 mp4; \
    video/mpeg mpeg mpg; \
    video/x-flv flv; \
}" > /etc/nginx/mime.types

# Expose ports
EXPOSE 1935
EXPOSE 8000

# Create a startup script to ensure the directory exists at runtime
RUN echo '#!/bin/sh\n\
mkdir -p /tmp/hls\n\
chmod -R 777 /tmp/hls\n\
echo "HLS directory created and permissions set"\n\
echo "Contents of /tmp:"\n\
ls -la /tmp\n\
echo "Contents of /tmp/hls:"\n\
ls -la /tmp/hls\n\
nginx -g "daemon off;"\n\
' > /start.sh && chmod +x /start.sh

# Start Nginx using the startup script
CMD ["/start.sh"]
EOL

# Update nginx.conf
echo "Updating nginx.conf..."
cat > nginx-rtmp/config/nginx.conf << 'EOL'
worker_processes auto;
rtmp_auto_push on;
events {
    worker_connections 1024;
}

rtmp {
    server {
        listen 1935;
        chunk_size 4096;

        application live {
            live on;
            record off;
            
            # HLS
            hls on;
            hls_path /tmp/hls;
            hls_fragment 3;
            hls_playlist_length 60;
            
            # Disable variants for now to simplify debugging
            # hls_variant _low bandwidth=500000;
            # hls_variant _mid bandwidth=1000000;
            # hls_variant _hi bandwidth=2000000;
        }
    }
}

http {
    include mime.types;
    default_type application/octet-stream;
    sendfile on;
    keepalive_timeout 65;
    server_tokens off;

    # Gzip Settings
    gzip on;
    gzip_disable "msie6";
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_buffers 16 8k;
    gzip_http_version 1.1;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;

    # HLS Streaming Server
    server {
        listen 8000;
        
        # CORS setup
        add_header 'Access-Control-Allow-Origin' '*' always;
        add_header 'Access-Control-Allow-Methods' 'GET, OPTIONS' always;
        add_header 'Access-Control-Allow-Headers' 'Origin, X-Requested-With, Content-Type, Accept' always;
        
        # HLS
        location /hls {
            types {
                application/vnd.apple.mpegurl m3u8;
                video/mp2t ts;
            }
            alias /tmp/hls;
            add_header Cache-Control no-cache;
            add_header Access-Control-Allow-Origin *;
            
            # Debug
            autoindex on;
        }
        
        # Status page
        location /stat {
            rtmp_stat all;
            rtmp_stat_stylesheet stat.xsl;
        }
        
        location /stat.xsl {
            root /usr/local/nginx/html;
        }
        
        # Ping endpoint for health checks
        location /ping {
            return 200 "pong\n";
        }
    }
}
EOL

# Update stream_manager.py to include debug output
echo "Updating stream_manager.py..."
sed -i 's/logger.info(f"Started stream {stream.name} (ID: {stream_id}) with PID {process.pid}")/logger.info(f"Started stream {stream.name} (ID: {stream_id}) with PID {process.pid}")\n            # Debug HLS directory\n            subprocess.run(["ls", "-la", "\/tmp\/hls"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)\n            logger.info("HLS directory checked")/' backend/stream_manager.py

# Rebuild and restart containers
echo "Rebuilding and restarting containers..."
docker-compose build --no-cache
docker-compose up -d

# Wait for containers to start
echo "Waiting for containers to start..."
sleep 10

# Check if containers are running
echo "Checking container status..."
docker-compose ps

# Check nginx-rtmp logs
echo "Checking nginx-rtmp logs..."
docker-compose logs nginx-rtmp

# Check if HLS directory exists in nginx-rtmp container
echo "Checking HLS directory in nginx-rtmp container..."
docker-compose exec nginx-rtmp ls -la /tmp
docker-compose exec nginx-rtmp ls -la /tmp/hls

echo "==== Fix completed ===="
echo "Try starting a stream and check if HLS files are generated in the ./hls-data directory"
