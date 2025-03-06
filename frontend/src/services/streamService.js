import api from './api';

const getStreams = async () => {
  const response = await api.get('/streams/');
  return response.data;
};

const getStream = async (id) => {
  const response = await api.get(`/streams/${id}`);
  return response.data;
};

const createStream = async (streamData) => {
  const response = await api.post('/streams/', streamData);
  return response.data;
};

const updateStream = async (id, streamData) => {
  const response = await api.put(`/streams/${id}`, streamData);
  return response.data;
};

const deleteStream = async (id) => {
  const response = await api.delete(`/streams/${id}`);
  return response.data;
};

const startStream = async (id) => {
  const response = await api.post(`/streams/${id}/start`);
  return response.data;
};

const stopStream = async (id) => {
  const response = await api.post(`/streams/${id}/stop`);
  return response.data;
};

const restartStream = async (id) => {
  const response = await api.post(`/streams/${id}/restart`);
  return response.data;
};

const getStreamStatus = async (id) => {
  const response = await api.get(`/streams/${id}/status`);
  return response.data;
};

const getStreamLogs = async (id, limit = 100) => {
  const response = await api.get(`/streams/${id}/logs?limit=${limit}`);
  return response.data;
};

const streamService = {
  getStreams,
  getStream,
  createStream,
  updateStream,
  deleteStream,
  startStream,
  stopStream,
  restartStream,
  getStreamStatus,
  getStreamLogs,
};

export default streamService;
