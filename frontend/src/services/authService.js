import api from './api';

const login = async (username, password) => {
  const formData = new FormData();
  formData.append('username', username);
  formData.append('password', password);
  
  const response = await api.post('/token', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

const register = async (username, email, password) => {
  const response = await api.post('/users/', {
    username,
    email,
    password,
  });
  return response.data;
};

const getCurrentUser = async () => {
  const response = await api.get('/users/me/');
  return response.data;
};

const authService = {
  login,
  register,
  getCurrentUser,
};

export default authService;
