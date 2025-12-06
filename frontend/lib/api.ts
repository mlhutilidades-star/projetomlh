import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.set('Authorization', `Bearer ${token}`);
    }
  }
  return config;
});

export const refreshToken = async () => {
  if (typeof window === 'undefined') return;
  const refresh_token = localStorage.getItem('refresh_token');
  if (!refresh_token) return;
  const { data } = await api.post('/auth/refresh', { refresh_token });
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
};

export default api;
