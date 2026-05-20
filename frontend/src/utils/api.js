import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000';

/**
 * Fetches data from the API with a retry mechanism for network errors.
 * Useful for GET requests that might fail due to a backend restart.
 */
export const fetchWithRetry = async (url, options = {}, retries = 3, delay = 1000) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await axios({ url, ...options });
    } catch (error) {
      if (i < retries - 1 && (!error.response || error.code === 'ERR_NETWORK')) { // Check for network errors
        console.warn(`Retrying API call to ${url} in ${delay}ms... (Attempt ${i + 1}/${retries})`);
        await new Promise(res => setTimeout(res, delay));
      } else {
        throw error; // Re-throw if not a network error or out of retries
      }
    }
  }
};