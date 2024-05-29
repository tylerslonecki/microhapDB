import axios from 'axios';

const axiosInstance = axios.create({
  baseURL: 'https://myfastapiapp.loca.lt/', // Base URL for your API
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Ensure cookies are included in requests
});

export default axiosInstance;
