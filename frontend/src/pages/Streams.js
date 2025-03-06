import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Typography,
  Grid,
  Paper,
  Button,
  TextField,
  InputAdornment,
  CircularProgress,
  Divider,
} from '@mui/material';
import {
  Add as AddIcon,
  Search as SearchIcon,
} from '@mui/icons-material';
import streamService from '../services/streamService';
import StreamCard from '../components/StreamCard';

function Streams() {
  const [streams, setStreams] = useState([]);
  const [filteredStreams, setFilteredStreams] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStreams();
  }, []);

  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredStreams(streams);
    } else {
      const filtered = streams.filter(
        (stream) =>
          stream.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
          stream.url.toLowerCase().includes(searchTerm.toLowerCase()) ||
          stream.stream_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
          stream.status.toLowerCase().includes(searchTerm.toLowerCase())
      );
      setFilteredStreams(filtered);
    }
  }, [searchTerm, streams]);

  const fetchStreams = async () => {
    try {
      setLoading(true);
      const data = await streamService.getStreams();
      setStreams(data);
      setFilteredStreams(data);
      setError(null);
    } catch (error) {
      console.error('Error fetching streams:', error);
      setError('Failed to load streams. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (event) => {
    setSearchTerm(event.target.value);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Streams
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

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Search streams by name, URL, type, or status"
          value={searchTerm}
          onChange={handleSearchChange}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
      </Paper>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="error">{error}</Typography>
          <Button variant="contained" onClick={fetchStreams} sx={{ mt: 2 }}>
            Retry
          </Button>
        </Paper>
      ) : filteredStreams.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          {searchTerm.trim() !== '' ? (
            <Typography variant="body1" gutterBottom>
              No streams match your search criteria.
            </Typography>
          ) : (
            <>
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
            </>
          )}
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {filteredStreams.map((stream) => (
            <Grid item key={stream.id} xs={12} sm={6} md={4} lg={3}>
              <StreamCard stream={stream} onStatusChange={fetchStreams} />
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}

export default Streams;
