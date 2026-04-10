import axios from "axios";

/**
 * API client for the FastAPI backend.
 *
 * In development, Vite proxies /api to localhost:8000.
 * In production, set VITE_API_BASE_URL to the Render backend URL.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// Response interceptor — log errors, pass through data
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error(
      `[API] ${error.config?.method?.toUpperCase()} ${error.config?.url}:`,
      error.response?.status,
      error.response?.data || error.message
    );
    return Promise.reject(error);
  }
);

export default api;
