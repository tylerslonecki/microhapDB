<template>
  <div class="p-d-flex p-jc-center p-ai-center p-flex-column" style="height:100vh;">
    <button @click="login" class="styled-button">Login with ORCID</button>
  </div>
</template>

<script>
import { mapActions } from 'vuex';
import axios from 'axios';
import { axiosNoCredentials } from '@/axiosConfig';

export default {
  methods: {
    ...mapActions('auth', ['checkAuthStatus']),

    login() {
      // Direct the user to the backend's login endpoint
      console.log(`Redirecting to login at: ${axios.defaults.baseURL}/auth/login`);
      
      // Store the URL we're redirecting to for debugging
      localStorage.setItem('lastLoginRedirect', `${axios.defaults.baseURL}/auth/login`);
      
      window.location.href = `${axios.defaults.baseURL}/auth/login`;
    },
    
    async handleCallback() {
      const urlParams = new URLSearchParams(window.location.search);
      const error = urlParams.get('error');
      const token = urlParams.get('token');
      
      console.log('URL params:', { error, token });
      console.log('Current localStorage token:', localStorage.getItem('access_token'));
      console.log('Current cookies:', document.cookie);
      
      if (error) {
        console.error('ORCID authentication error:', error);
        if (error === 'duplicate_request') {
          alert('Login request already processed. If you are not logged in, please try again.');
        } else {
          alert(`ORCID authentication error: ${error}`);
        }
        return;
      }

      // If we have a token directly in the URL, use it
      if (token) {
        console.log('Token found in URL, storing it...');
        localStorage.setItem('access_token', token);
        
        // Set the token in axios headers for future requests
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        axiosNoCredentials.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        
        try {
          // Check auth status with the token
          await this.checkAuthStatus();
          console.log('Authentication successful, redirecting to home page...');
          
          // Clean up the URL by removing the token parameter
          const cleanUrl = window.location.pathname;
          window.history.replaceState({}, document.title, cleanUrl);
          
          this.$router.push('/');
          return;
        } catch (error) {
          console.error('Error validating token from URL:', error);
          
          // If it's a CORS error, try without credentials
          if (error.message && error.message.includes('CORS')) {
            console.log('CORS error detected, trying without credentials...');
            try {
              const response = await axiosNoCredentials.get('/auth/status', {
                headers: {
                  'Authorization': `Bearer ${token}`
                }
              });
              console.log('Auth status response (no credentials):', response.data);
              
              // Clean up the URL by removing the token parameter
              const cleanUrl = window.location.pathname;
              window.history.replaceState({}, document.title, cleanUrl);
              
              this.$router.push('/');
              return;
            } catch (fallbackError) {
              console.error('Error checking auth status without credentials:', fallbackError);
            }
          }
          
          // If it's a network error or 401, we'll still proceed with the token
          if (error.code === 'ERR_NETWORK' || (error.response && error.response.status === 401)) {
            console.log('Network error or 401, but proceeding with token from URL');
            // Clean up the URL by removing the token parameter
            const cleanUrl = window.location.pathname;
            window.history.replaceState({}, document.title, cleanUrl);
            
            this.$router.push('/');
            return;
          }
        }
      }

      // Try to get token from cookies
      const getCookie = (name) => {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
      };
      
      const cookieToken = getCookie('access_token') || getCookie('access_token_js');
      if (cookieToken) {
        console.log('Token found in cookies, using it...');
        localStorage.setItem('access_token', cookieToken);
        axios.defaults.headers.common['Authorization'] = `Bearer ${cookieToken}`;
        axiosNoCredentials.defaults.headers.common['Authorization'] = `Bearer ${cookieToken}`;
        
        try {
          await this.checkAuthStatus();
          console.log('Authentication successful from cookie, redirecting to home page...');
          this.$router.push('/');
          return;
        } catch (error) {
          console.error('Error validating token from cookie:', error);
          
          // If it's a CORS error, try without credentials
          if (error.message && error.message.includes('CORS')) {
            console.log('CORS error detected, trying without credentials...');
            try {
              const response = await axiosNoCredentials.get('/auth/status', {
                headers: {
                  'Authorization': `Bearer ${cookieToken}`
                }
              });
              console.log('Auth status response (no credentials):', response.data);
              this.$router.push('/');
              return;
            } catch (fallbackError) {
              console.error('Error checking auth status without credentials:', fallbackError);
            }
          }
          
          // If it's a network error or 401, we'll still proceed with the token
          if (error.code === 'ERR_NETWORK' || (error.response && error.response.status === 401)) {
            console.log('Network error or 401, but proceeding with token from cookie');
            this.$router.push('/');
            return;
          }
        }
      }

      // If we get here, no token was found
      console.log('No token found in URL or cookies');
    }
  },
  created() {
    // If user returned from ORCID with a token or error, handle it
    this.handleCallback();
  }
};
</script>


<style>
.styled-button {
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s ease;
  background-color: #00796b;
  color: white;
}

.styled-button:hover {
  background-color: #00796b8e;
}

.styled-button:active {
  transform: scale(0.97);
}
</style>
