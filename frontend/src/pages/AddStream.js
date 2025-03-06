import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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

function AddStream() {
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const formik = useFormik({
    initialValues: {
      name: '',
      url: '',
      stream_type: 'm3u8',
    },
    validationSchema,
    onSubmit: async (values) => {
      try {
        setLoading(true);
        await streamService.createStream(values);
        toast.success('Stream created successfully');
        navigate('/streams');
      } catch (error) {
        toast.error('Failed to create stream');
        console.error(error);
      } finally {
        setLoading(false);
      }
    },
  });

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
          Add New Stream
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
                placeholder="Enter a descriptive name for the stream"
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
                placeholder="Enter the URL of the stream source"
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
                onClick={() => navigate('/streams')}
                sx={{ mr: 2 }}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                startIcon={<SaveIcon />}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Save Stream'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>
    </Box>
  );
}

export default AddStream;
