# IPTV Re-Streaming and Management Web Application

A containerized web application that allows users to input, manage, and monitor multiple IPTV stream URLs. The system enables users to start, stop, edit, and remove streams via a web interface and efficiently serve these streams to multiple devices internally.

## Features

- **Web Interface**: User-friendly dashboard for managing streams
- **Stream Management**: Add, edit, remove, start, stop, and restart streams
- **Stream Monitoring**: Real-time logs and status monitoring
- **Multi-format Support**: Handles various stream formats (m3u8, ts, rtmp, direct URLs)
- **Efficient Re-streaming**: Uses ffmpeg to re-stream content without transcoding
- **Containerized**: Fully dockerized application for easy deployment

## System Components

### 1. Web Interface (Frontend)

- Built with React and Material UI
- Responsive dashboard for stream management
- Real-time stream status monitoring
- Stream preview capability

### 2. Backend API & Process Manager

- Built with Python FastAPI
- RESTful API for CRUD operations
- Manages ffmpeg processes for stream handling
- Monitors stream health and logs

### 3. Media Server

- Nginx with RTMP module
- Ingests streams from ffmpeg
- Converts RTMP to HLS for wider device compatibility
- Serves streams over HTTP

### 4. Database

- PostgreSQL for storing stream configurations and logs

## Getting Started

### Prerequisites

- Docker and Docker Compose

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd iptv-restreamer
   ```

2. Start the application:
   ```bash
   docker-compose up -d
   ```

3. Access the web interface:
   ```
   http://localhost:3000
   ```

4. Access streams:
   ```
   HLS: http://localhost:8088/hls/stream_<stream_id>.m3u8
   RTMP: rtmp://localhost:1935/live/<stream_id>
   ```

## Usage

1. **Register/Login**: Create an account or log in to the application
2. **Add Stream**: Click "Add Stream" and enter the stream details (name, URL, type)
3. **Start Stream**: Click the "Start" button on a stream card
4. **Monitor Stream**: View logs and status on the stream detail page
5. **Access Stream**: Use the provided HLS or RTMP URLs to access the stream

## Architecture

- **Frontend Container**: React application served by Nginx
- **Backend Container**: Python FastAPI application
- **Media Server Container**: Nginx with RTMP module
- **Database Container**: PostgreSQL

## HLS Streaming Details

The application uses HTTP Live Streaming (HLS) to deliver video content to a wide range of devices. Here's how it works:

1. **Stream Ingestion**: The backend uses ffmpeg to pull from the source stream
2. **RTMP Conversion**: The stream is sent to the Nginx-RTMP server via RTMP protocol
3. **HLS Generation**: Nginx-RTMP converts the RTMP stream to HLS format
4. **File Storage**: HLS segments (.ts files) and playlists (.m3u8) are stored in a shared volume at `/tmp/hls`
5. **HTTP Delivery**: The files are served via HTTP on port 8088

### HLS URLs

- **Playlist URL**: `http://[server-ip]:8088/hls/stream_[stream_id].m3u8`
- **Segment Files**: `http://[server-ip]:8088/hls/stream_[stream_id]_[sequence].ts`

## Troubleshooting

### Common Issues

1. **No HLS Files Generated**:
   - Check if the ffmpeg process is running: `docker-compose exec backend ps aux | grep ffmpeg`
   - Verify permissions on the HLS directory: `docker-compose exec nginx-rtmp ls -la /tmp/hls`
   - Check nginx-rtmp logs: `docker-compose logs nginx-rtmp`

2. **Stream Not Playing**:
   - Verify the source stream is accessible
   - Check if HLS files exist: `docker-compose exec nginx-rtmp ls -la /tmp/hls`
   - Check browser console for HLS.js errors
   - Verify the correct URL format: `http://[server-ip]:8088/hls/stream_[stream_id].m3u8`

3. **Permission Issues**:
   - Ensure the shared volume has proper permissions: `docker-compose exec nginx-rtmp chmod -R 777 /tmp/hls`

### Debugging Tool

The application includes a debugging tool to help diagnose HLS streaming issues:

```bash
docker-compose exec backend python debug_hls.py --all
```

Available options:
- `--check-dirs`: Check directory structure and permissions
- `--list-files`: List HLS files
- `--test-stream URL`: Test a specific stream URL
- `--check-nginx`: Check nginx configuration
- `--all`: Run all checks

## Security Considerations

- Change default credentials in production
- Consider using HTTPS for the web interface
- Implement proper authentication for stream access if needed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- ffmpeg for media processing
- Nginx-RTMP for stream distribution
- React and Material UI for the frontend interface
- FastAPI for the backend API
