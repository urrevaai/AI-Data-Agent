import axios from 'axios';

const baseURL = (import.meta as any)?.env?.VITE_API_BASE || 'http://127.0.0.1:8000';

const api = axios.create({
  baseURL,
});

export default api;


