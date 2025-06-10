<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1>Welcome to HaploSearch</h1>
      <p>A comprehensive microhaplotype database for genetic research</p>
      
      <div v-if="isAuthenticated" class="auth-welcome">
        <h3>Welcome, {{ username }}!</h3>
        <p>You're now logged in and can access all features available to you.</p>
      </div>
      
      <div class="features-section">
        <div class="feature-card">
          <i class="pi pi-search feature-icon"></i>
          <h3>Search</h3>
          <p>Query the database for microhaplotypes with advanced filtering</p>
        </div>
        
        <div class="feature-card">
          <i class="pi pi-chart-bar feature-icon"></i>
          <h3>Visualize</h3>
          <p>Generate interactive visualizations for genetic data analysis</p>
        </div>
        
        <div class="feature-card">
          <i class="pi pi-cloud-upload feature-icon"></i>
          <h3>Upload</h3>
          <p>Contribute to the database by uploading your microhaplotype data</p>
        </div>
      </div>
    </div>
    
    <div class="auth-section" v-if="!isAuthenticated">
      <p>Sign in with your ORCID ID to access all features</p>
      <button @click="login" class="login-button">
        <i class="pi pi-sign-in"></i>
        Login with ORCID
      </button>
    </div>
  </div>
</template>

<script>
import { mapState, mapActions } from 'vuex';
import axios from 'axios';

export default {
  name: 'HomePage',
  computed: {
    ...mapState('auth', ['isAuthenticated', 'user']),
    username() {
      return this.user?.username || 'User';
    }
  },
  async created() {
    // Check for token in URL (from ORCID callback)
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const error = urlParams.get('error');
    
    if (error) {
      console.error('Authentication error from URL:', error);
      let errorMessage = `Login failed: ${error}`;
      
      // Provide user-friendly error messages
      if (error === 'duplicate_request') {
        errorMessage = 'Login request already processed. If you are not logged in, please try logging in again.';
      }
      
      if (this.$toast) {
        this.$toast.add({
          severity: 'error',
          summary: 'Authentication Error',
          detail: errorMessage,
          life: 5000
        });
      }
      
      // Clean up the URL
      const cleanUrl = window.location.pathname;
      window.history.replaceState({}, document.title, cleanUrl);
      return;
    }
    
    if (token) {
      console.log('Token found in URL, processing...');
      
      try {
        // Use the auth store action to handle the token
        const success = await this.handleTokenFromUrl(token);
        
        if (success) {
          console.log('Authentication successful');
          
          // Show success message
          if (this.$toast) {
            this.$toast.add({
              severity: 'success',
              summary: 'Logged In',
              detail: `Welcome back, ${this.username}!`,
              life: 3000
            });
          }
        } else {
          console.error('Token validation failed');
          
          if (this.$toast) {
            this.$toast.add({
              severity: 'error',
              summary: 'Authentication Error',
              detail: 'Failed to validate your login. Please try again.',
              life: 5000
            });
          }
        }
      } catch (error) {
        console.error('Error processing token from URL:', error);
        
        let errorMessage = 'Failed to process login. Please try again.';
        if (error.response?.status === 409) {
          errorMessage = 'Login request already processed. If you are not logged in, please try logging in again.';
        }
        
        if (this.$toast) {
          this.$toast.add({
            severity: 'error',
            summary: 'Authentication Error',
            detail: errorMessage,
            life: 5000
          });
        }
      } finally {
        // Clean up the URL by removing the token parameter
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
      }
    } else {
      // No token in URL, just check existing auth status
      try {
        await this.checkAuthStatus();
      } catch (error) {
        console.error('Error checking existing auth status:', error);
        // Don't show error message for this, as user might not be logged in
      }
    }
  },
  methods: {
    ...mapActions('auth', ['checkAuthStatus', 'handleTokenFromUrl']),
    
    login() {
      // Direct the user to the backend's login endpoint
      window.location.href = `${axios.defaults.baseURL}/auth/login`;
    }
  }
}
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  text-align: center;
}

.welcome-section {
  margin-bottom: 3rem;
}

.welcome-section h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  color: var(--primary-color);
}

.welcome-section p {
  font-size: 1.2rem;
  color: var(--text-color-secondary);
  margin-bottom: 2rem;
}

.auth-welcome {
  background-color: #e8f5e8;
  border: 1px solid #4caf50;
  border-radius: 8px;
  padding: 1.5rem;
  margin: 2rem 0;
}

.auth-welcome h3 {
  color: #2e7d32;
  margin-bottom: 0.5rem;
}

.auth-welcome p {
  color: #388e3c;
  margin: 0;
}

.features-section {
  display: flex;
  justify-content: space-between;
  gap: 2rem;
  margin-top: 3rem;
  flex-wrap: wrap;
}

.feature-card {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 1.5rem;
  flex: 1;
  min-width: 250px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
}

.feature-icon {
  font-size: 2rem;
  color: var(--primary-color);
  margin-bottom: 1rem;
}

.feature-card h3 {
  font-size: 1.3rem;
  margin-bottom: 0.5rem;
  color: var(--text-color);
}

.feature-card p {
  color: var(--text-color-secondary);
}

.auth-section {
  margin-top: 3rem;
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.login-button {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  transition: background-color 0.3s ease;
}

.login-button:hover {
  background-color: var(--primary-color-dark);
}

.login-button:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}

@media (max-width: 768px) {
  .features-section {
    flex-direction: column;
  }
  
  .feature-card {
    min-width: auto;
  }
}
</style>
