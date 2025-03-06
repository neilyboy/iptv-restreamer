# HLS Streaming Troubleshooting Guide

This guide provides information on how to troubleshoot and fix HLS streaming issues in the IPTV Re-Streaming application.

## HLS Streaming Architecture

The application uses a dual approach for HLS streaming:

1. **Nginx-RTMP's built-in HLS generation**:
   - Streams are sent to Nginx-RTMP via RTMP protocol
   - Nginx-RTMP automatically converts RTMP to HLS format
   - HLS files are stored in `/tmp/hls` directory

2. **Direct FFmpeg HLS generation** (as backup):
   - FFmpeg directly generates HLS files alongside RTMP output
   - Ensures consistent file naming and generation

## Key Configuration Points

- HLS files are stored in a shared Docker volume mounted at `/tmp/hls`
- File naming convention: `stream_[stream_id].m3u8` and `stream_[stream_id]_[sequence].ts`
- HLS files are served via HTTP on port 8088
- Frontend VideoPlayer component uses HLS.js library to play streams

## Common Issues and Solutions

### 1. Permission Issues

Ensure `/tmp/hls` has 777 permissions:

```bash
docker-compose exec nginx-rtmp chmod -R 777 /tmp/hls
docker-compose exec backend chmod -R 777 /tmp/hls
```

### 2. Path Mismatches

Ensure these configurations use consistent paths:
- nginx.conf: `hls_path /tmp/hls;`
- docker-compose.yml: `- hls_data:/tmp/hls`
- FFmpeg commands: output to `/tmp/hls`

### 3. File Generation Issues

If HLS files aren't being generated:

- Check FFmpeg logs for errors
- Verify source stream is accessible
- Ensure FFmpeg has proper permissions
- Check if nginx-rtmp is configured correctly

### 4. Debugging Tools

#### Debug HLS Script

Use the `debug_hls.py` tool to diagnose issues:

```bash
docker-compose exec backend python debug_hls.py --check-directory --list-files
```

#### Test Stream Generator

Use the `test_stream.py` tool to test HLS generation with a known working stream:

```bash
docker-compose exec backend python test_stream.py --source "https://example.com/test_stream.m3u8" --duration 60
```

## Monitoring HLS Files

To check if HLS files are being generated:

```bash
docker-compose exec nginx-rtmp ls -la /tmp/hls
```

## Viewing HLS Streams

HLS streams can be accessed at:
- Internal URL: `http://nginx-rtmp:8000/hls/stream_[stream_id].m3u8`
- External URL: `http://localhost:8088/hls/stream_[stream_id].m3u8`

## Recent Improvements

The stream manager has been updated with:
- More robust FFmpeg parameters for better compatibility
- Improved HLS file detection using glob patterns
- Background monitoring of HLS file generation
- Better error handling and logging
- Automatic cleanup of stale HLS files

## Still Having Issues?

If you're still experiencing problems:

1. Check the logs:
   ```bash
   docker-compose logs -f backend
   docker-compose logs -f nginx-rtmp
   ```

2. Verify network connectivity between containers:
   ```bash
   docker-compose exec backend ping nginx-rtmp
   ```

3. Test a direct FFmpeg command:
   ```bash
   docker-compose exec backend ffmpeg -i [source_url] -c:v copy -c:a copy -f hls -hls_time 3 -hls_list_size 60 -hls_flags delete_segments+append_list /tmp/hls/test.m3u8
   ```
