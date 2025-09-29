import axios from 'axios';

// Get the base URL from the environment variables provided by Vite
const VITE_API_BASE_URL = (import.meta as any).env.VITE_API_BASE_URL;

// If the environment variable is missing during the build, stop and show an error.
// This prevents deploying a broken frontend that calls localhost.
if (!VITE_API_BASE_URL) {
  throw new Error("VITE_API_BASE_URL is not defined. Please check your .env.local file and your Vercel environment variable settings.");
}

const api = axios.create({
  baseURL: VITE_API_BASE_URL,
});

export default api;