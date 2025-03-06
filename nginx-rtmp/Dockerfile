FROM tiangolo/nginx-rtmp

# Copy nginx configuration
COPY config/nginx.conf /etc/nginx/nginx.conf

# Create HLS directory with proper permissions
RUN mkdir -p /tmp/hls && \
    chown -R nobody:nogroup /tmp/hls && \
    chmod -R 777 /tmp/hls

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Set entrypoint
ENTRYPOINT ["/entrypoint.sh"]
