<!-- App.vue -->
<template>
  <div id="app">
    <Navbar/> <!-- Add the Navbar component here -->
    <Sidebar/>
    <div class="content">
      <router-view></router-view>
    </div>
  </div>
</template>

<script>
import Sidebar from './components/Sidebar.vue'; // Adjust the path as necessary
import Navbar from './components/Navbar.vue'; // Import the Navbar component
import { authState } from './authState'; // Import authState for authentication status

export default {
  components: {
    Sidebar,
    Navbar // Register the Navbar component
  },
  created() {
    this.checkAuthStatus(); // Call checkAuthStatus on component creation
  },
  methods: {
    async checkAuthStatus() {
      try {
        const response = await fetch('https://myfastapiapp.loca.lt/auth/status', {
          credentials: 'include'
        });

        if (!response.ok) {
          throw new Error('Failed to fetch authentication status');
        }

        const authStatus = await response.json();
        authState.isAuthenticated = authStatus.is_authenticated;
        authState.isAdmin = authStatus.is_admin;
        authState.username = authStatus.username;  // Update username
      } catch (error) {
        console.error('Error checking authentication status:', error);
        authState.isAuthenticated = false;
        authState.isAdmin = false;
        authState.username = null;
      }
    }
  }
}
</script>

<style>
.content {
  margin-left: 250px; /* Adjust based on your layout */
  padding: 20px;
}

html, body {
  margin: 0;
  padding: 0;
}
</style>
