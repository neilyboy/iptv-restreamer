import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  Divider,
  CircularProgress,
} from '@mui/material';
import {
  Add as AddIcon,
  PlayCircleOutline as StreamsIcon,
} from '@mui/icons-material';
import streamService from '../services/streamService';
import StreamCard from '../components/StreamCard';

function Dashboard() {
  const [streams, setStreams] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStreams();
  }, []);

  const fetchStreams = async () => {
    try {
      setLoading(true);
      const data = await streamService.getStreams();
      setStreams(data);
      setError(null);
    } catch (error) {
      console.error('Error fetching streams:', error);
      setError('Failed to load streams. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const getStreamStats = () => {
    const total = streams.length;
    const running = streams.filter(stream => stream.status === 'running').length;
    const stopped = streams.filter(stream => stream.status === 'stopped').length;
    const error = streams.filter(stream => stream.status === 'error').length;
    
    return { total, running, stopped, error };
  };

  const stats = getStreamStats();

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => navigate('/streams/add')}
        >
          Add Stream
        </Button>
      </Box>

      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 140,
              bgcolor: 'primary.main',
              color: 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Total Streams
            </Typography>
            <Typography variant="h3">{stats.total}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 140,
              bgcolor: 'success.main',
              color: 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Running
            </Typography>
            <Typography variant="h3">{stats.running}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 140,
              bgcolor: 'grey.500',
              color: 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Stopped
            </Typography>
            <Typography variant="h3">{stats.stopped}</Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper
            sx={{
              p: 2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              height: 140,
              bgcolor: 'error.main',
              color: 'white',
            }}
          >
            <Typography variant="h6" gutterBottom>
              Error
            </Typography>
            <Typography variant="h3">{stats.error}</Typography>
          </Paper>
        </Grid>
      </Grid>

      <Box sx={{ mb: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h5" component="h2">
            Recent Streams
          </Typography>
          <Button
            variant="outlined"
            startIcon={<StreamsIcon />}
            onClick={() => navigate('/streams')}
          >
            View All
          </Button>
        </Box>
        <Divider sx={{ mb: 3 }} />

        {loading ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : error ? (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography color="error">{error}</Typography>
            <Button
              variant="contained"
              onClick={fetchStreams}
              sx={{ mt: 2 }}
            >
              Retry
            </Button>
          </Paper>
        ) : streams.length === 0 ? (
          <Paper sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body1" gutterBottom>
              No streams available. Add your first stream to get started.
            </Typography>
            <Button
              variant="contained"
              color="primary"
              startIcon={<AddIcon />}
              onClick={() => navigate('/streams/add')}
              sx={{ mt: 2 }}
            >
              Add Stream
            </Button>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {streams.slice(0, 4).map((stream) => (
              <Grid item key={stream.id} xs={12} sm={6} md={4} lg={3}>
                <StreamCard stream={stream} onStatusChange={fetchStreams} />
              </Grid>
            ))}
          </Grid>
        )}
      </Box>
    </Box>
  );
}

export default Dashboard;
