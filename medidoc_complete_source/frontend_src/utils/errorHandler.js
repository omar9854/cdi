/**
 * Error Handler Utility
 * Handles API errors and formats them for display in React components
 */

/**
 * Extract user-friendly error message from API error response
 * @param {Error} error - The error object from axios or fetch
 * @param {string} defaultMessage - Default message if no specific error found
 * @returns {string} - User-friendly error message
 */
export const getErrorMessage = (error, defaultMessage = 'An error occurred') => {
  // If error is already a string, return it
  if (typeof error === 'string') {
    return error;
  }

  // Check if it's an axios error with response
  if (error?.response?.data) {
    const data = error.response.data;

    // FastAPI validation error format: {detail: [{type, loc, msg, ...}]}
    if (Array.isArray(data.detail)) {
      // Extract messages from validation errors
      const messages = data.detail.map(err => {
        if (typeof err === 'string') return err;
        if (err.msg) return err.msg;
        if (err.message) return err.message;
        return JSON.stringify(err);
      });
      return messages.join(', ');
    }

    // FastAPI simple error format: {detail: "error message"}
    if (typeof data.detail === 'string') {
      return data.detail;
    }

    // Standard error format: {error: "message"}
    if (typeof data.error === 'string') {
      return data.error;
    }

    // Message field
    if (typeof data.message === 'string') {
      return data.message;
    }

    // If data itself is a string
    if (typeof data === 'string') {
      return data;
    }
  }

  // Check error.message
  if (error?.message && typeof error.message === 'string') {
    return error.message;
  }

  // Network errors
  if (error?.request && !error?.response) {
    return 'Network error. Please check your connection.';
  }

  // Default message
  return defaultMessage;
};

/**
 * Safe error display for React components
 * Ensures only strings are rendered in React
 * @param {any} error - The error to display
 * @returns {string} - Safe string to display
 */
export const safeErrorDisplay = (error) => {
  if (!error) return '';
  
  if (typeof error === 'string') return error;
  
  if (error.message && typeof error.message === 'string') {
    return error.message;
  }
  
  // For objects, try to extract meaningful info
  if (typeof error === 'object') {
    try {
      return JSON.stringify(error, null, 2);
    } catch {
      return 'An error occurred';
    }
  }
  
  return String(error);
};

/**
 * Log error to console with context
 * @param {string} context - Where the error occurred
 * @param {Error} error - The error object
 */
export const logError = (context, error) => {
  console.error(`[${context}]`, error);
  
  if (error?.response) {
    console.error('Response data:', error.response.data);
    console.error('Response status:', error.response.status);
  }
};

export default {
  getErrorMessage,
  safeErrorDisplay,
  logError
};
