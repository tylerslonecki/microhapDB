<template>
  <div class="home-container">
    <div class="welcome-section">
      <h1>Welcome to HaploSearch</h1>
      <p>A comprehensive microhaplotype database for population genetics and forensic research</p>
      
      <div v-if="isAuthenticated" class="auth-welcome">
        <div v-if="isAdmin" class="admin-welcome">
          <h3>Welcome, {{ username }}! (Administrator)</h3>
          <p>You have full administrative access to upload data and user accounts. Access the Admin panel to manage user permissions.</p>
        </div>
        <div v-else-if="userRole === 'private_user'" class="private-user-welcome">
          <h3>Welcome, {{ username }}! (Private User)</h3>
          <p>You have access to public & private microhaplotype data and collaborator management. Visit Privacy & Collaborators to manage your data collaborations with other private users.</p>
        </div>
        <div v-else class="public-welcome">
          <h3>Welcome, {{ username }}!</h3>
          <p>You have access to public microhaplotype data and can explore the database for your research needs.</p>
        </div>
      </div>
      
      <div class="features-section">
        <div class="feature-card">
          <i class="pi pi-search feature-icon"></i>
          <h3>Query Microhaplotypes</h3>
          <p><strong>Search and filter</strong> microhaplotype records by species, allele ID, sequence, info field, and associated traits with <strong>paginated results</strong> and <strong>CSV export</strong>. View <strong>detailed allele information</strong>, analyze <strong>shared vs. combined accessions</strong> across selected markers, and export accession data for further analysis.</p>
          <div class="card-action">
            <Button 
              label="Start Querying" 
              icon="pi pi-search" 
              @click="$router.push('/query')"
              class="p-button-sm"
            />
          </div>
        </div>
        
        <div class="feature-card">
          <i class="pi pi-database feature-icon"></i>
          <h3>Database Insights</h3>
          <p>View <strong>database growth over time</strong> with allele count statistics by version, <strong>program contributions</strong>, <strong>file upload history</strong>, and <strong>downloadable reports</strong></p>
          <div class="card-action">
            <Button 
              label="View Reports" 
              icon="pi pi-chart-line" 
              @click="$router.push('/report')"
              class="p-button-sm"
            />
          </div>
        </div>
        
        <div class="feature-card">
          <i class="pi pi-chart-line feature-icon"></i>
          <h3>Missing Alleles Analysis</h3>
          <p><strong>Compare program datasets</strong> against the complete database to identify <strong>missing alleles</strong> by chromosome and locus. <strong>Interactive genome visualization</strong> shows diversity patterns and coverage gaps, with <strong>detailed missing allele lists</strong> and <strong>direct integration to query workflows</strong>.</p>
          <div class="card-action">
            <Button 
              label="Analyze Missing Alleles" 
              icon="pi pi-chart-bar" 
              @click="$router.push('/visualizations-comparative')"
              class="p-button-sm"
            />
          </div>
        </div>
        
        <div v-if="canAccessPrivateData" class="feature-card">
          <i class="pi pi-cloud-upload feature-icon"></i>
          <h3>Data Contribution</h3>
          <p><strong>Contribute microhaplotype datasets</strong> to HaploSearch and <strong>expand the database</strong> with new markers</p>
          <div class="card-action">
            <Button 
              label="Upload Data" 
              icon="pi pi-upload" 
              @click="$router.push('/data-upload')"
              class="p-button-sm"
            />
          </div>
        </div>
        
        <div v-if="userRole === 'private_user'" class="feature-card">
          <i class="pi pi-users feature-icon"></i>
          <h3>Privacy & Collaborators</h3>
          <p><strong>Manage collaborators</strong> to share private datasets, <strong>coordinate research projects</strong>, and <strong>control access</strong> to sensitive genetic data</p>
          <div class="card-action">
            <Button 
              label="Manage Privacy" 
              icon="pi pi-users" 
              @click="$router.push('/user-management')"
              class="p-button-sm"
            />
          </div>
        </div>
        
        <div v-if="isAdmin" class="feature-card">
          <i class="pi pi-cog feature-icon"></i>
          <h3>System Administration</h3>
          <p><strong>Manage user accounts</strong>, oversee data uploads, <strong>monitor system performance</strong>, and maintain <strong>database integrity and security</strong></p>
          <div class="card-action">
            <Button 
              label="Admin Dashboard" 
              icon="pi pi-cog" 
              @click="$router.push('/admin')"
              class="p-button-sm"
            />
          </div>
        </div>
      </div>
    </div>
    
    <div class="auth-section" v-if="!isAuthenticated">
      <div class="login-info">
        <h3>Get Started with HaploSearch</h3>
        <p>Sign in with your ORCID ID to access the full suite of microhaplotype research tools</p>
        
      </div>
      <button @click="login" class="login-button">
        <i class="pi pi-sign-in"></i>
        Login with ORCID
      </button>
    </div>
  </div>
</template>

<script>
import { mapState, mapGetters, mapActions } from 'vuex';
import Button from 'primevue/button';
import axios from 'axios';

export default {
  name: 'HomePage',
  components: {
    Button,
  },
  computed: {
    ...mapState('auth', ['isAuthenticated', 'user']),
    ...mapGetters('auth', ['isAdmin', 'canAccessPrivateData', 'userRole']),
    username() {
      return this.user?.full_name || this.user?.username || 'User';
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

/* Role-specific welcome styling */
.admin-welcome {
  background-color: #fff3e0;
  border: 1px solid #ff9800;
  border-radius: 8px;
  padding: 1.5rem;
}

.admin-welcome h3 {
  color: #e65100;
}

.admin-welcome p {
  color: #f57c00;
}

.private-user-welcome {
  background-color: #e3f2fd;
  border: 1px solid #2196f3;
  border-radius: 8px;
  padding: 1.5rem;
}

.private-user-welcome h3 {
  color: #0d47a1;
}

.private-user-welcome p {
  color: #1565c0;
}

.public-welcome {
  background-color: #e8f5e8;
  border: 1px solid #4caf50;
  border-radius: 8px;
  padding: 1.5rem;
}

.public-welcome h3 {
  color: #2e7d32;
}

.public-welcome p {
  color: #388e3c;
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
  min-width: 280px;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  display: flex;
  flex-direction: column;
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
  line-height: 1.5;
  flex-grow: 1;
  margin-bottom: 1rem;
}

.card-action {
  margin-top: auto;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.card-action .p-button {
  width: 100%;
  justify-content: center;
}

.auth-section {
  margin-top: 3rem;
  padding: 2rem;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.login-info h3 {
  color: var(--text-color);
  margin-bottom: 1rem;
}

.login-info p {
  color: var(--text-color-secondary);
  margin-bottom: 1.5rem;
}

.login-benefits {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
  text-align: left;
}

.benefit-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
}

.benefit-item i {
  color: #4caf50;
  font-size: 1.1rem;
}

.benefit-item span {
  color: var(--text-color);
  font-size: 0.95rem;
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
  
  .login-benefits {
    grid-template-columns: 1fr;
  }
  
  .benefit-item {
    justify-content: center;
    text-align: center;
  }
}
</style>
