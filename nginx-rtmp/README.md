# IPTV Re-Streaming Media Server

This is the media server component for the IPTV Re-Streaming Manager system. It's based on Nginx with the RTMP module to handle stream ingestion and distribution.

## Features

- RTMP ingestion from ffmpeg processes
- HLS conversion for wider device compatibility
- Stream distribution via HTTP (HLS) and RTMP
- Low-latency configuration
- Efficient stream handling

## Technology Stack

- Nginx
- nginx-rtmp-module
- HLS (HTTP Live Streaming)

## Configuration

The Nginx configuration is located in `config/nginx.conf`. Key settings include:

- RTMP server configuration
- HLS settings (segment duration, playlist size)
- HTTP server for HLS distribution

## Docker

The media server is containerized using Docker and can be run as part of the complete IPTV Re-Streaming Manager system using Docker Compose.

## Ports

- `1935`: RTMP ingestion and distribution
- `8000`: HTTP server for HLS distribution

## Accessing Streams

- RTMP: `rtmp://server-ip:1935/live/stream_id`
- HLS: `http://server-ip:8000/hls/stream_id.m3u8`

## License

This project is licensed under the MIT License.
