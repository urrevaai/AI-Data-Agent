import axios from 'axios';

// Get the base URL from Vite's environment variables
const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

// This check is crucial. If the Vercel environment variable is missing,
// the Vercel build will fail, telling us exactly what's wrong.
if (!VITE_API_BASE_URL) {
  throw new Error("CRITICAL ERROR: VITE_API_BASE_URL is not defined in the Vercel environment.");
}

const apiClient = axios.create({
  baseURL: VITE_API_BASE_URL,
});

export default apiClient;