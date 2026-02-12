import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for scraping
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Process a receipt URL
 * @param {string} url - Receipt URL to process
 * @param {boolean} forceUpdate - Force update if duplicate found
 * @returns {Promise<Object>} Response with success status and data
 */
export const processReceipt = async (url, forceUpdate = false) => {
  try {
    const response = await apiClient.post('/api/receipt/process', {
      url,
      force_update: forceUpdate
    });

    // Check if response indicates duplicate
    if (response.data.is_duplicate && !response.data.success) {
      return {
        success: false,
        is_duplicate: true,
        message: response.data.message,
        data: response.data.data,
        duplicate_info: response.data.duplicate_info
      };
    }

    return {
      success: response.data.success,
      data: response.data,
      message: response.data.message
    };
  } catch (error) {
    // Handle different error types
    if (error.response) {
      // Server responded with error
      const errorMessage = error.response.data?.detail || error.response.data?.message || 'Unknown error';
      return {
        success: false,
        error: errorMessage,
        status: error.response.status,
      };
    } else if (error.request) {
      // No response received
      return {
        success: false,
        error: 'messages.errorNetwork',
        status: 0,
      };
    } else {
      // Request setup error
      return {
        success: false,
        error: error.message || 'messages.errorGeneric',
        status: 0,
      };
    }
  }
};

/**
 * Check API health
 * @returns {Promise<Object>} Health status
 */
export const checkHealth = async () => {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    throw new Error('API health check failed');
  }
};

export default apiClient;
