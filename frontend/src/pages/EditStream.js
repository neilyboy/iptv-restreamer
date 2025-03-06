import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import {
  Box,
  Typography,
  Paper,
  TextField,
  Button,
  Grid,
  MenuItem,
  FormControl,
  FormHelperText,
  CircularProgress,
} from '@mui/material';
import { ArrowBack as ArrowBackIcon, Save as SaveIcon } from '@mui/icons-material';
import { toast } from 'react-toastify';
import { useFormik } from 'formik';
import * as Yup from 'yup';
import streamService from '../services/streamService';

const streamTypes = [
  { value: 'm3u8', label: 'HLS (m3u8)' },
  { value: 'ts', label: 'MPEG-TS (ts)' },
  { value: 'rtmp', label: 'RTMP' },
  { value: 'direct', label: 'Direct URL' },
];

const validationSchema = Yup.object({
  name: Yup.string().required('Stream name is required'),
  url: Yup.string().required('Stream URL is required').url('Must be a valid URL'),
  stream_type: Yup.string().required('Stream type is required'),
});

function EditStream() {
  const { id } = useParams();
  const [stream, setStream] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchStream();
  }, [id]);

  const fetchStream = async () => {
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
  };

  const formik = useFormik({
    initialValues: {
      name: stream?.name || '',
      url: stream?.url || '',
      stream_type: stream?.stream_type || 'm3u8',
    },
    enableReinitialize: true,
    validationSchema,
    onSubmit: async (values) => {
      try {
        setSaving(true);
        await streamService.updateStream(id, values);
        toast.success('Stream updated successfully');
        navigate(`/streams/${id}`);
      } catch (error) {
        toast.error('Failed to update stream');
        console.error(error);
      } finally {
        setSaving(false);
      }
    },
  });

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
            Edit Stream
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
          onClick={() => navigate(`/streams/${id}`)}
          sx={{ mr: 2 }}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Edit Stream
        </Typography>
      </Box>

      <Paper sx={{ p: 3 }}>
        <form onSubmit={formik.handleSubmit}>
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="name"
                name="name"
                label="Stream Name"
                variant="outlined"
                value={formik.values.name}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.name && Boolean(formik.errors.name)}
                helperText={formik.touched.name && formik.errors.name}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="url"
                name="url"
                label="Stream URL"
                variant="outlined"
                value={formik.values.url}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.url && Boolean(formik.errors.url)}
                helperText={formik.touched.url && formik.errors.url}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                id="stream_type"
                name="stream_type"
                select
                label="Stream Type"
                variant="outlined"
                value={formik.values.stream_type}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                error={formik.touched.stream_type && Boolean(formik.errors.stream_type)}
                helperText={formik.touched.stream_type && formik.errors.stream_type}
              >
                {streamTypes.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </TextField>
              <FormHelperText>
                Select the type of stream you are adding
              </FormHelperText>
            </Grid>
            <Grid item xs={12} sx={{ display: 'flex', justifyContent: 'flex-end', mt: 2 }}>
              <Button
                variant="outlined"
                onClick={() => navigate(`/streams/${id}`)}
                sx={{ mr: 2 }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                startIcon={<SaveIcon />}
                disabled={saving}
              >
                {saving ? <CircularProgress size={24} /> : 'Save Changes'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
}

export default EditStream;
