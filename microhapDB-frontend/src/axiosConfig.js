import axios from 'axios';

// Get the backend URL from environment or use a default
const backendUrl = process.env.VUE_APP_BACKEND_URL || 'http://localhost:8000';

// Set base URL for all requests
axios.defaults.baseURL = backendUrl;

// Remove credentials from all requests since we're using token-based auth
axios.defaults.withCredentials = false;

// Set timeout to prevent hanging requests
axios.defaults.timeout = 15000; // 15 seconds

// Add common headers
axios.defaults.headers.common['Accept'] = 'application/json';
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Create a second axios instance without credentials for fallback
const axiosNoCredentials = axios.create({
  baseURL: backendUrl,
  timeout: 15000,
  withCredentials: false,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Create a longer timeout instance for admin operations
const axiosLongTimeout = axios.create({
  baseURL: backendUrl,
  timeout: 45000, // 45 seconds for admin operations
  withCredentials: false,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Create an extra long timeout instance for file uploads and heavy operations
const axiosExtraLongTimeout = axios.create({
  baseURL: backendUrl,
  timeout: 120000, // 2 minutes for very heavy operations
  withCredentials: false,
  headers: {
    'Accept': 'application/json',
    'Content-Type': 'application/json'
  }
});

// Flag to prevent multiple simultaneous refresh attempts
let isRefreshing = false;
let failedQueue = [];

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  
  failedQueue = [];
};

// Configure axios to handle tokens properly
axios.interceptors.request.use(
  config => {
    // Get token from localStorage
    const token = localStorage.getItem('access_token');
    
    // Add token to headers if it exists
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    console.log(`Making ${config.method.toUpperCase()} request to: ${config.url}`);
    return config;
  },
  error => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Enhanced response interceptor with better refresh token handling
axios.interceptors.response.use(
  response => {
    console.log(`Response from ${response.config.url}: Status ${response.status}`);
    return response;
  },
  async error => {
    const originalRequest = error.config;
    
    console.error('Response error:', {
      status: error.response?.status,
      url: originalRequest?.url,
      detail: error.response?.data?.detail
    });
    
    // Handle token expiration
    if (error.response?.status === 401 && 
        error.response?.data?.detail && 
        (error.response.data.detail.includes('expired') || 
         error.response.data.detail === 'Could not validate credentials') &&
        !originalRequest._retry) {
      
      // Don't try to refresh if we're already trying to refresh
      if (originalRequest.url === '/auth/refresh') {
        console.log('Refresh endpoint failed, clearing auth state');
        localStorage.removeItem('access_token');
        delete axios.defaults.headers.common['Authorization'];
        
        // Redirect to login if not already there
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
          window.location.href = '/login';
        }
        
        return Promise.reject(error);
      }
      
      if (isRefreshing) {
        // If we're already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        }).then(token => {
          originalRequest.headers['Authorization'] = `Bearer ${token}`;
          return axios(originalRequest);
        }).catch(err => {
          return Promise.reject(err);
        });
      }
      
      originalRequest._retry = true;
      isRefreshing = true;
      
      try {
        console.log('Token expired, attempting to refresh...');
        
        const response = await axios.post('/auth/refresh');
        
        if (response.data && response.data.access_token) {
          const newToken = response.data.access_token;
          
          console.log('Token refreshed successfully');
          
          // Store the new token
          localStorage.setItem('access_token', newToken);
          
          // Update the Authorization header for future requests
          axios.defaults.headers.common['Authorization'] = `Bearer ${newToken}`;
          
          // Process the queue of failed requests
          processQueue(null, newToken);
          
          // Retry the original request with the new token
          originalRequest.headers['Authorization'] = `Bearer ${newToken}`;
          
          return axios(originalRequest);
        } else {
          throw new Error('No access token in refresh response');
        }
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        
        // Process the queue with the error
        processQueue(refreshError, null);
        
        // Clear token and redirect to login
        localStorage.removeItem('access_token');
        delete axios.defaults.headers.common['Authorization'];
        
        // Only redirect if not already on login page
        if (window.location.pathname !== '/login' && window.location.pathname !== '/') {
          console.log('Redirecting to login page after failed token refresh');
          window.location.href = '/login';
        }
        
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }
    
    // Handle other types of errors
    if (error.response) {
      // Server responded with error status
      console.error('Server error:', {
        status: error.response.status,
        data: error.response.data,
        url: error.config.url
      });
    } else if (error.request) {
      // Request was made but no response received
      if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
        console.error('Request timeout:', {
          url: error.config.url,
          timeout: error.config.timeout
        });
        
        const timeoutError = new Error('Request timed out. The server is taking longer than expected to respond.');
        timeoutError.code = 'TIMEOUT';
        timeoutError.originalError = error;
        return Promise.reject(timeoutError);
      } else {
        console.error('Network error:', {
          url: error.config.url,
          code: error.code,
          message: error.message
        });
      }
    } else {
      console.error('Request setup error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// Apply the same interceptors to other axios instances
[axiosNoCredentials, axiosLongTimeout, axiosExtraLongTimeout].forEach(instance => {
  instance.interceptors.request.use(
    config => {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      console.log(`Making ${config.method.toUpperCase()} request to: ${config.url}`);
      return config;
    },
    error => Promise.reject(error)
  );
  
  instance.interceptors.response.use(
    response => {
      console.log(`Response from ${response.config.url}: Status ${response.status}`);
      return response;
    },
    error => {
      // Handle timeout errors specifically
      if (error.code === 'ECONNABORTED' && error.message.includes('timeout')) {
        console.error(`${instance.defaults.baseURL} error: ${error.message}`);
        const timeoutError = new Error('Request timed out. The server is taking longer than expected to respond.');
        timeoutError.code = 'TIMEOUT';
        timeoutError.originalError = error;
        return Promise.reject(timeoutError);
      }
      
      // Handle abort errors (don't log these as they are intentional cancellations)
      if (error.name === 'AbortError' || error.message === 'canceled') {
        return Promise.reject(error);
      }
      
      // For other instances, log errors without refresh logic
      console.error(`${instance.defaults.baseURL} error:`, error.response?.data || error.message);
      return Promise.reject(error);
    }
  );
});

// Export the axios instances
export default axios;
export { axiosNoCredentials, axiosLongTimeout, axiosExtraLongTimeout };
