import React, { useEffect, useRef, useState } from 'react';
import { Box, Typography, Paper, CircularProgress } from '@mui/material';
import Hls from 'hls.js';

function VideoPlayer({ streamId, autoPlay = true }) {
  const videoRef = useRef(null);
  const hlsRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const video = videoRef.current;
    
    if (!video) return;
    
    // Reset states
    setLoading(true);
    setError(null);
    
    // Attempt to load the HLS stream using relative URL
    const loadStream = () => {
      // Use relative URL to match the protocol of the frontend
      const streamUrl = `/hls/${streamId}.m3u8`;
      console.log('Attempting to load HLS stream from:', streamUrl);
      
      // Check if HLS is supported
      if (Hls.isSupported()) {
        if (hlsRef.current) {
          hlsRef.current.destroy();
        }
        
        const hls = new Hls({
          debug: true, // Enable debug for troubleshooting
          enableWorker: true,
          lowLatencyMode: true,
          manifestLoadingTimeOut: 10000, // Increase timeout for manifest loading
          manifestLoadingMaxRetry: 5,    // Increase retries
          levelLoadingTimeOut: 10000,    // Increase timeout for level loading
          fragLoadingTimeOut: 20000,     // Increase timeout for fragment loading
        });
        
        hls.loadSource(streamUrl);
        hls.attachMedia(video);
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          console.log('HLS manifest parsed successfully');
          setLoading(false);
          if (autoPlay) {
            video.play().catch(error => {
              console.error('Error attempting to autoplay:', error);
            });
          }
        });
        
        hls.on(Hls.Events.ERROR, (event, data) => {
          console.warn(`HLS error: ${data.type} - ${data.details}`, data);
          
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                console.error('Network error, trying to recover...');
                hls.startLoad();
                break;
              case Hls.ErrorTypes.MEDIA_ERROR:
                console.error('Media error, trying to recover...');
                hls.recoverMediaError();
                break;
              default:
                console.error('Unrecoverable error:', data);
                setError(`Playback error: ${data.details}`);
                setLoading(false);
                hls.destroy();
                break;
            }
          }
        });
        
        // Additional event listeners for debugging
        hls.on(Hls.Events.MANIFEST_LOADING, () => {
          console.log('Manifest loading...');
        });
        
        hls.on(Hls.Events.LEVEL_LOADED, () => {
          console.log('Level loaded');
          setLoading(false);
        });
        
        hls.on(Hls.Events.FRAG_LOADED, () => {
          console.log('Fragment loaded');
          setLoading(false);
        });
        
        hlsRef.current = hls;
      } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // For Safari and iOS devices
        video.src = streamUrl;
        video.addEventListener('loadedmetadata', () => {
          console.log('Video metadata loaded');
          setLoading(false);
          if (autoPlay) {
            video.play().catch(error => {
              console.error('Error attempting to autoplay:', error);
              setError('Autoplay failed. Please click play.');
            });
          }
        });
        
        video.addEventListener('error', (e) => {
          console.error('Video element error:', e);
          setError(`Playback error: ${video.error ? video.error.message : 'Unknown error'}`);
          setLoading(false);
        });
      } else {
        console.error('HLS is not supported in this browser');
        setError('HLS playback is not supported in this browser');
        setLoading(false);
      }
    };
    
    loadStream();
    
    return () => {
      if (hlsRef.current) {
        hlsRef.current.destroy();
      }
    };
  }, [streamId, autoPlay]);

  return (
    <Paper elevation={3} sx={{ borderRadius: 2, overflow: 'hidden', position: 'relative' }}>
      <Box className="video-container" sx={{ position: 'relative', minHeight: '240px' }}>
        <video
          ref={videoRef}
          controls
          playsInline
          style={{ width: '100%', height: '100%' }}
        />
        
        {loading && (
          <Box 
            sx={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              right: 0, 
              bottom: 0, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              backgroundColor: 'rgba(0,0,0,0.5)'
            }}
          >
            <CircularProgress color="primary" />
            <Typography variant="body2" color="white" sx={{ ml: 2 }}>
              Loading stream...
            </Typography>
          </Box>
        )}
        
        {error && (
          <Box 
            sx={{ 
              position: 'absolute', 
              top: 0, 
              left: 0, 
              right: 0, 
              bottom: 0, 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              backgroundColor: 'rgba(0,0,0,0.7)',
              padding: 2
            }}
          >
            <Typography variant="body1" color="error" align="center">
              {error}
              <br />
              <Typography variant="body2" color="white" sx={{ mt: 1 }}>
                Please check if the stream is running and try refreshing the page.
              </Typography>
            </Typography>
          </Box>
        )}
      </Box>
    </Paper>
  );
}

export default VideoPlayer;
