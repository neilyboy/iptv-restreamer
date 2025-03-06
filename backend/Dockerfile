FROM python:3.9-slim

WORKDIR /app

# Install system dependencies including curl for healthchecks
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create HLS directory with proper permissions
RUN mkdir -p /tmp/hls && \
    chmod -R 777 /tmp/hls

# Create entrypoint script
RUN echo '#!/bin/sh\n\
echo "Starting backend container..."\n\
\n\
# Ensure HLS directory exists and has proper permissions\n\
echo "Ensuring HLS directory exists and has proper permissions..."\n\
mkdir -p /tmp/hls\n\
chmod -R 777 /tmp/hls\n\
\n\
# Create a test file to verify write permissions\n\
echo "Creating test file to verify write permissions..."\n\
echo "Test file from backend" > /tmp/hls/backend_test.txt\n\
\n\
# Wait for nginx-rtmp to be ready\n\
echo "Waiting for nginx-rtmp to be ready..."\n\
for i in $(seq 1 30); do\n\
  if curl -s http://nginx-rtmp:8088/ping > /dev/null; then\n\
    echo "nginx-rtmp is ready!"\n\
    break\n\
  fi\n\
  echo "Waiting for nginx-rtmp... ($i/30)"\n\
  sleep 1\n\
done\n\
\n\
# Start the backend application\n\
echo "Starting backend application..."\n\
exec uvicorn main:app --host 0.0.0.0 --port 8080\n\
' > /app/docker-entrypoint.sh && chmod +x /app/docker-entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Expose port
EXPOSE 8080
