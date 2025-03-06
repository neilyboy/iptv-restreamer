# HLS Streaming in IPTV Re-Streaming Application

This document explains how HLS (HTTP Live Streaming) works in our IPTV Re-Streaming application, common issues, and troubleshooting steps.

## Architecture Overview

Our application uses a dual approach for HLS streaming:

1. **Nginx-RTMP's built-in HLS generation (Primary Method)**:
   - Streams are sent to Nginx-RTMP via RTMP protocol using FFmpeg
   - Nginx-RTMP automatically converts RTMP to HLS format
   - HLS files are stored in `/tmp/hls` directory
   - Files are named `[stream_id].m3u8` and `[stream_id]_[sequence].ts`

2. ~~**Direct FFmpeg HLS generation (Backup Method)**~~:
   - We previously used FFmpeg to directly generate HLS files
   - This approach has been removed in favor of the more reliable Nginx-RTMP approach

## Configuration Points

### Docker Volume

- HLS files are stored in a shared Docker volume mounted at `/tmp/hls`
- This volume is shared between the `nginx-rtmp` and `backend` services
- File permissions are set to `777` to ensure all containers can write to it

### Nginx-RTMP Configuration

Key settings in `nginx-rtmp/config/nginx.conf`:

```nginx
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
            
            # Make sure files are created with correct permissions
            hls_cleanup on;
            
            # Explicitly set the file naming format
            hls_fragment_naming sequential;
            
            # Add HLS fragment naming options
            hls_fragment_slicing aligned;
            
            # Ensure nginx user has write permissions
            exec_static mkdir -p /tmp/hls;
            exec_static chmod -R 777 /tmp/hls;
        }
    }
}
```

### Stream Manager Configuration

The `stream_manager.py` file has been updated to use a simpler approach:

1. FFmpeg now only outputs to RTMP, letting Nginx-RTMP handle the HLS conversion
2. The stream manager monitors for HLS files to verify successful streaming
3. Both the stream manager and Nginx-RTMP ensure the HLS directory has proper permissions

## Common Issues and Solutions

### 1. No HLS Files Generated

**Symptoms**: 
- Stream appears to be running (FFmpeg process is active)
- No `.m3u8` or `.ts` files in the `/tmp/hls` directory

**Possible Causes and Solutions**:

a) **Permission Issues**:
   - Ensure `/tmp/hls` has 777 permissions: `chmod -R 777 /tmp/hls`
   - Verify ownership: `chown -R nobody:nogroup /tmp/hls`

b) **Nginx-RTMP Configuration**:
   - Verify HLS is enabled in nginx.conf: `hls on;`
   - Check HLS path is correct: `hls_path /tmp/hls;`

c) **Stream Source Issues**:
   - Verify the source stream is valid and accessible
   - Try a known working stream for testing

### 2. HLS Files Exist But Not Accessible via HTTP

**Symptoms**:
- `.m3u8` and `.ts` files exist in `/tmp/hls`
- Cannot access streams via `http://localhost:8088/hls/[stream_id].m3u8`

**Possible Causes and Solutions**:

a) **Nginx HTTP Configuration**:
   - Verify HTTP server is configured correctly
   - Check CORS settings
   - Ensure the location block for `/hls` is properly set up

b) **Network/Port Issues**:
   - Verify port 8088 is mapped correctly in docker-compose.yml
   - Check if firewall is blocking access

### 3. Inconsistent File Naming

**Symptoms**:
- Files are named differently than expected
- Some files use `stream_[id]` format while others use just `[id]`

**Solution**:
- We now rely on Nginx-RTMP's consistent naming scheme
- Files should be named `[stream_id].m3u8` and `[stream_id]_[sequence].ts`

## Debugging Tools

### 1. Debug HLS Script

We've created a comprehensive debugging tool: `debug_hls.py`

Run it with:
```bash
docker-compose exec backend python debug_hls.py --all
```

Or for specific tests:
```bash
docker-compose exec backend python debug_hls.py --dir --files --nginx --stream
```

### 2. Direct FFmpeg Test

For testing different FFmpeg commands:
```bash
docker-compose exec backend python direct_ffmpeg_test.py --source [stream_url]
```

### 3. Stream Manager Test

To test the stream manager functionality:
```bash
docker-compose exec backend python test_stream_manager.py --stream-id [id] --wait-time 60
```

## Monitoring

To monitor active streams and their HLS status:

1. Check stream status via API:
   ```
   GET /api/streams/{stream_id}/status
   ```

2. View Nginx-RTMP status page:
   ```
   http://localhost:8088/stat
   ```

3. List HLS files directly:
   ```bash
   docker-compose exec nginx-rtmp ls -la /tmp/hls
   ```

## Recent Changes

1. Simplified FFmpeg command to only output to RTMP
2. Improved monitoring of HLS file generation
3. Enhanced error handling and logging
4. Added comprehensive debugging tools
5. Ensured consistent file permissions and directory structure

## Further Assistance

If you continue to experience issues after trying these troubleshooting steps, please:

1. Run the debug tools and collect their output
2. Check the logs from both the backend and nginx-rtmp services
3. Verify your stream source is accessible and valid
