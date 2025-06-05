import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add a request interceptor to include the auth token in requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const auth = {
  register: (data: { username: string; email: string; password: string; role?: string }) =>
    api.post('/auth/register', data),
  login: (username: string, password: string) =>
    api.post('/auth/login', `username=${username}&password=${password}`, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
};

export const uploads = {
  uploadLog: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post('/uploads/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  getUploadStatus: (uploadId: number) => api.get(`/uploads/${uploadId}/status`),
};

export const logs = {
  search: (params: {
    q?: string;
    log_level?: string;
    start_time?: string;
    end_time?: string;
    source?: string;
    page?: number;
    per_page?: number;
  }) => api.get('/search/', { params }),
  getTimeSeries: (startTime: string, endTime: string, interval = 'hour') =>
    api.get('/analytics/time-series', { 
      params: { 
        start_time: startTime, 
        end_time: endTime, 
        interval 
      } 
    }),
  getDistribution: (field = 'log_level') =>
    api.get('/analytics/distribution', { params: { field } }),
  getTopErrors: (n = 10) =>
    api.get('/analytics/top-errors', { params: { n } }),
};

export default api;
