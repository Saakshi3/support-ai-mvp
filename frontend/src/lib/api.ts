import axios from 'axios';
import toast from 'react-hot-toast';

// Use proxy in development, direct URL as fallback
const API_BASE_URL = process.env.NODE_ENV === 'development' 
  ? '/api'  // Use Vite proxy
  : 'http://localhost:8000'; // Direct API for production

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor to add auth token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      toast.error('Server error occurred');
    } else if (error.response?.status >= 400) {
      const message = error.response?.data?.detail || 'An error occurred';
      toast.error(message);
    }
    return Promise.reject(error);
  }
);

export default api;