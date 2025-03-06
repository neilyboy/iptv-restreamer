import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  Button,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  IconButton,
  Card,
  CardContent,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import streamService from '../services/streamService';
import VideoPlayer from '../components/VideoPlayer';
import StreamLogs from '../components/StreamLogs';

function StreamDetail() {
  const { id } = useParams();
  const [stream, setStream] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusLoading, setStatusLoading] = useState(false);
  const [error, setError] = useState(null);
  const [openDeleteDialog, setOpenDeleteDialog] = useState(false);
  const navigate = useNavigate();

  const fetchStream = useCallback(async () => {
    try {
      setLoading(true);
      const data = await streamService.getStream(id);
      setStream(data);
      setError(null);
    } catch (error) {
      console.error('Error fetching stream:', error);
      setError('Failed to load stream. Please try again later.');
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchLogs = useCallback(async () => {
    try {
      const data = await streamService.getStreamLogs(id);
      setLogs(data);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  }, [id]);

  useEffect(() => {
    fetchStream();
    fetchLogs();

    // Set up polling for status updates
    const intervalId = setInterval(() => {
      fetchStream();
      fetchLogs();
    }, 10000); // Poll every 10 seconds

    return () => clearInterval(intervalId);
  }, [id, fetchStream, fetchLogs]);

  const handleStartStream = async () => {
    try {
      setStatusLoading(true);
      await streamService.startStream(id);
      toast.success(`Started stream: ${stream.name}`);
      fetchStream();
    } catch (error) {
      toast.error('Failed to start stream');
      console.error(error);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleStopStream = async () => {
    try {
      setStatusLoading(true);
      await streamService.stopStream(id);
      toast.success(`Stopped stream: ${stream.name}`);
      fetchStream();
    } catch (error) {
      toast.error('Failed to stop stream');
      console.error(error);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleRestartStream = async () => {
    try {
      setStatusLoading(true);
      await streamService.restartStream(id);
      toast.success(`Restarted stream: ${stream.name}`);
      fetchStream();
    } catch (error) {
      toast.error('Failed to restart stream');
      console.error(error);
    } finally {
      setStatusLoading(false);
    }
  };

  const handleDeleteStream = async () => {
    try {
      setStatusLoading(true);
      await streamService.deleteStream(id);
      toast.success('Stream deleted successfully');
      navigate('/streams');
    } catch (error) {
      toast.error('Failed to delete stream');
      console.error(error);
    } finally {
      setStatusLoading(false);
      setOpenDeleteDialog(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running':
        return 'success';
      case 'stopped':
        return 'default';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/streams')}
            sx={{ mr: 2 }}
          >
            Back
          </Button>
          <Typography variant="h4" component="h1">
            Stream Details
          </Typography>
        </Box>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error" gutterBottom>
            {error}
          </Typography>
          <Button variant="contained" onClick={fetchStream} sx={{ mt: 2 }}>
            Retry
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/streams')}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Stream Details
        </Typography>
      </Box>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
              <Typography variant="h5" component="h2" gutterBottom>
                {stream.name}
              </Typography>
              <Box>
                <IconButton
                  color="primary"
                  onClick={() => navigate(`/streams/${id}/edit`)}
                  title="Edit Stream"
                >
                  <EditIcon />
                </IconButton>
                <IconButton
                  color="error"
                  onClick={() => setOpenDeleteDialog(true)}
                  title="Delete Stream"
                >
                  <DeleteIcon />
                </IconButton>
              </Box>
            </Box>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Stream URL
              </Typography>
              <Typography variant="body1" sx={{ wordBreak: 'break-all' }}>
                {stream.url}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', mb: 2 }}>
              <Box sx={{ mr: 4 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Type
                </Typography>
                <Chip
                  label={stream.stream_type}
                  size="small"
                  color="primary"
                  variant="outlined"
                />
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Status
                </Typography>
                <Chip
                  label={stream.status}
                  size="small"
                  color={getStatusColor(stream.status)}
                />
              </Box>
            </Box>
            <Divider sx={{ my: 2 }} />
            <Box sx={{ display: 'flex', justifyContent: 'flex-start' }}>
              {stream.status === 'running' ? (
                <>
                  <Button
                    variant="outlined"
                    color="error"
                    startIcon={<StopIcon />}
                    onClick={handleStopStream}
                    disabled={statusLoading}
                    sx={{ mr: 2 }}
                  >
                    Stop
                  </Button>
                  <Button
                    variant="outlined"
                    color="warning"
                    startIcon={<RefreshIcon />}
                    onClick={handleRestartStream}
                    disabled={statusLoading}
                  >
                    Restart
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<PlayIcon />}
                  onClick={handleStartStream}
                  disabled={statusLoading}
                >
                  Start
                </Button>
              )}
            </Box>
          </Paper>

          {stream.status === 'running' && (
            <Box sx={{ mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Stream Preview
              </Typography>
              <VideoPlayer streamId={id} />
            </Box>
          )}

          <StreamLogs logs={logs} />
        </Grid>

        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stream Information
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  ID
                </Typography>
                <Typography variant="body1">{stream.id}</Typography>
              </Box>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Created At
                </Typography>
                <Typography variant="body1">
                  {new Date(stream.created_at).toLocaleString()}
                </Typography>
              </Box>
              {stream.updated_at && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Last Updated
                  </Typography>
                  <Typography variant="body1">
                    {new Date(stream.updated_at).toLocaleString()}
                  </Typography>
                </Box>
              )}
              {stream.process_id && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Process ID
                  </Typography>
                  <Typography variant="body1">{stream.process_id}</Typography>
                </Box>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stream URLs
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  HLS URL (m3u8)
                </Typography>
                <Typography variant="body1" color="textSecondary" sx={{ wordBreak: 'break-all' }}>
                  http://{window.location.hostname}:8088/hls/{id}.m3u8
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  RTMP URL
                </Typography>
                <Typography variant="body1" sx={{ wordBreak: 'break-all' }}>
                  rtmp://{window.location.hostname}:1935/live/{id}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={openDeleteDialog}
        onClose={() => setOpenDeleteDialog(false)}
      >
        <DialogTitle>Confirm Deletion</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete the stream "{stream.name}"? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteStream} color="error" autoFocus>
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default StreamDetail;
