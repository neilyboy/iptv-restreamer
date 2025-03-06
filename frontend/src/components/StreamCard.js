import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  CardContent,
  CardActions,
  Typography,
  Button,
  Chip,
  Box,
  IconButton,
  Menu,
  MenuItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Refresh as RefreshIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import { toast } from 'react-toastify';
import streamService from '../services/streamService';

function StreamCard({ stream, onStatusChange }) {
  const [loading, setLoading] = useState(false);
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleViewDetails = () => {
    handleMenuClose();
    navigate(`/streams/${stream.id}`);
  };

  const handleEditStream = () => {
    handleMenuClose();
    navigate(`/streams/${stream.id}/edit`);
  };

  const handleDeleteStream = async () => {
    handleMenuClose();
    if (window.confirm(`Are you sure you want to delete the stream "${stream.name}"?`)) {
      try {
        setLoading(true);
        await streamService.deleteStream(stream.id);
        toast.success('Stream deleted successfully');
        if (onStatusChange) onStatusChange();
      } catch (error) {
        toast.error('Failed to delete stream');
        console.error(error);
      } finally {
        setLoading(false);
      }
    }
  };

  const handleStartStream = async () => {
    try {
      setLoading(true);
      await streamService.startStream(stream.id);
      toast.success(`Started stream: ${stream.name}`);
      if (onStatusChange) onStatusChange();
    } catch (error) {
      toast.error('Failed to start stream');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleStopStream = async () => {
    try {
      setLoading(true);
      await streamService.stopStream(stream.id);
      toast.success(`Stopped stream: ${stream.name}`);
      if (onStatusChange) onStatusChange();
    } catch (error) {
      toast.error('Failed to stop stream');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestartStream = async () => {
    try {
      setLoading(true);
      await streamService.restartStream(stream.id);
      toast.success(`Restarted stream: ${stream.name}`);
      if (onStatusChange) onStatusChange();
    } catch (error) {
      toast.error('Failed to restart stream');
      console.error(error);
    } finally {
      setLoading(false);
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

  return (
    <Card className="stream-card" sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <CardContent sx={{ flexGrow: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 'bold' }}>
            {stream.name}
          </Typography>
          <IconButton
            aria-label="more"
            id={`stream-menu-${stream.id}`}
            aria-controls={`stream-menu-${stream.id}`}
            aria-haspopup="true"
            onClick={handleMenuOpen}
          >
            <MoreVertIcon />
          </IconButton>
          <Menu
            id={`stream-menu-${stream.id}`}
            anchorEl={anchorEl}
            keepMounted
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={handleViewDetails}>
              <ListItemIcon>
                <PlayIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>View Details</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleEditStream}>
              <ListItemIcon>
                <EditIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Edit</ListItemText>
            </MenuItem>
            <MenuItem onClick={handleDeleteStream}>
              <ListItemIcon>
                <DeleteIcon fontSize="small" />
              </ListItemIcon>
              <ListItemText>Delete</ListItemText>
            </MenuItem>
          </Menu>
        </Box>
        <Typography color="text.secondary" sx={{ mb: 1 }}>
          {stream.url}
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Type:
          </Typography>
          <Chip
            label={stream.stream_type}
            size="small"
            color="primary"
            variant="outlined"
          />
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Typography variant="body2" color="text.secondary" sx={{ mr: 1 }}>
            Status:
          </Typography>
          <Chip
            label={stream.status}
            size="small"
            color={getStatusColor(stream.status)}
          />
        </Box>
      </CardContent>
      <CardActions>
        {stream.status === 'running' ? (
          <>
            <Button
              size="small"
              startIcon={<StopIcon />}
              color="error"
              onClick={handleStopStream}
              disabled={loading}
            >
              Stop
            </Button>
            <Button
              size="small"
              startIcon={<RefreshIcon />}
              color="warning"
              onClick={handleRestartStream}
              disabled={loading}
            >
              Restart
            </Button>
          </>
        ) : (
          <Button
            size="small"
            startIcon={<PlayIcon />}
            color="success"
            onClick={handleStartStream}
            disabled={loading}
          >
            Start
          </Button>
        )}
        <Button
          size="small"
          onClick={handleViewDetails}
          sx={{ marginLeft: 'auto' }}
        >
          Details
        </Button>
      </CardActions>
    </Card>
  );
}

export default StreamCard;
