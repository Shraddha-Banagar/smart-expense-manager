/**
 * Central Axios instance. All API calls go through here so that
 * base URL, auth headers, and error handling stay in one place.
 */
import axios from "axios";
import { safeStorage } from "../utils/storage";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8001/api";

const api = axios.create({
  baseURL: API_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Attach the JWT (if present) to every outgoing request.
api.interceptors.request.use((config) => {
  const token = safeStorage.get("access_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Centralized handling of expired/invalid sessions.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      safeStorage.remove("access_token");
      safeStorage.remove("user");
      // Avoid redirect loops if we're already on an auth page.
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;
