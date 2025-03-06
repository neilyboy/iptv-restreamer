# HLS Streaming Troubleshooting Guide

This guide provides comprehensive troubleshooting steps for resolving HLS (HTTP Live Streaming) issues in the IPTV Re-Streaming application.

## Common HLS Issues

### 1. Missing HLS Files

**Symptoms:**
- Empty HLS directory
- 404 errors when accessing stream URLs
- VideoPlayer shows loading but never plays

**Solutions:**
- Run the `fix-hls-dirs.sh` script to create and configure the HLS directory properly
- Check permissions on the `/tmp/hls` directory (should be 777)
- Verify that the HLS directory is properly mounted in docker-compose.yml

### 2. Permission Issues

**Symptoms:**
- HLS files are created but not accessible
- Error messages in nginx-rtmp logs about permission denied
- ffmpeg fails to write to the HLS directory

**Solutions:**
- Ensure the HLS directory has 777 permissions: `chmod -R 777 /tmp/hls`
- Check ownership of the directory: `chown -R nobody:nogroup /tmp/hls`
- Verify that the volume mount in docker-compose.yml is correctly configured

### 3. Stream Not Playing in Browser

**Symptoms:**
- HLS files exist but stream doesn't play
- Browser console shows CORS errors
- HLS.js reports manifest loading errors

**Solutions:**
- Check CORS headers in nginx.conf
- Verify that the HLS URL format is correct in the VideoPlayer component
- Ensure the port mapping for nginx-rtmp is correct (8088:8000)
- Test direct access to the m3u8 file via browser

### 4. Inconsistent HLS File Generation

**Symptoms:**
- HLS files are created intermittently
- Some streams work, others don't
- Files are created but not updated

**Solutions:**
- Check both nginx-rtmp and ffmpeg HLS generation settings
- Verify consistent file naming conventions
- Ensure sufficient disk space for HLS files
- Check for conflicting processes writing to the same files

## Diagnostic Tools

### 1. Debug HLS Directories Script

Run the `debug_hls_dirs.py` script in the backend container to:
- Check if the HLS directory exists and has proper permissions
- Test write access to the directory
- List contents of the HLS directory
- Create test HLS files
- Check connectivity to nginx-rtmp

```bash
docker-compose exec backend python debug_hls_dirs.py
```

### 2. Fix HLS Directories Script

The `fix-hls-dirs.sh` script automates the process of:
- Creating the HLS directory with proper permissions
- Updating docker-compose.yml to use bind mounts
- Updating the nginx-rtmp Dockerfile and configuration
- Rebuilding and restarting containers

```bash
chmod +x fix-hls-dirs.sh
./fix-hls-dirs.sh
```

### 3. Manual Checks

Check nginx-rtmp logs:
```bash
docker-compose logs nginx-rtmp
```

Check HLS directory in nginx-rtmp container:
```bash
docker-compose exec nginx-rtmp ls -la /tmp/hls
```

Test HLS file creation manually:
```bash
docker-compose exec nginx-rtmp touch /tmp/hls/test.txt
```

## HLS Directory Structure

The HLS directory should contain:
- `.m3u8` playlist files (e.g., `stream_123.m3u8`)
- `.ts` segment files (e.g., `stream_123_0.ts`, `stream_123_1.ts`, etc.)

Example of a properly functioning HLS directory:
```
-rw-r--r-- 1 nobody nogroup  156 May 10 12:34 stream_123.m3u8
-rw-r--r-- 1 nobody nogroup 1234 May 10 12:34 stream_123_0.ts
-rw-r--r-- 1 nobody nogroup 1234 May 10 12:34 stream_123_1.ts
-rw-r--r-- 1 nobody nogroup 1234 May 10 12:34 stream_123_2.ts
```

## HLS File Naming Convention

The application uses the following naming convention:
- Playlist files: `stream_[stream_id].m3u8`
- Segment files: `stream_[stream_id]_[sequence].ts`

This naming convention is used by both nginx-rtmp's built-in HLS generation and the direct ffmpeg HLS generation.

## Dual HLS Generation Approach

The application uses two methods for HLS generation:

1. **Nginx-RTMP Built-in HLS Generation**:
   - Configured in nginx.conf
   - Automatically converts RTMP streams to HLS
   - Files are stored in `/tmp/hls`

2. **Direct ffmpeg HLS Generation**:
   - Configured in stream_manager.py
   - Generates HLS files alongside RTMP output
   - Provides redundancy if nginx-rtmp HLS generation fails

This dual approach ensures more reliable HLS streaming but requires consistent configuration across both methods.

## Container Architecture

Understanding the container architecture is crucial for troubleshooting:

- **nginx-rtmp container**: Receives RTMP streams and generates HLS files
- **backend container**: Manages streams and can generate HLS files directly
- **frontend container**: Plays HLS streams using HLS.js

The HLS directory (`/tmp/hls`) is shared between the nginx-rtmp and backend containers via a Docker volume or bind mount.

## Network Configuration

- RTMP streams are received on port 1935
- HLS files are served via HTTP on port 8088
- The frontend accesses HLS streams via `http://<hostname>:8088/hls/stream_<id>.m3u8`

## Additional Resources

- [HLS.js Documentation](https://github.com/video-dev/hls.js/blob/master/docs/API.md)
- [Nginx-RTMP Module Documentation](https://github.com/arut/nginx-rtmp-module)
- [ffmpeg HLS Documentation](https://ffmpeg.org/ffmpeg-formats.html#hls-2)
