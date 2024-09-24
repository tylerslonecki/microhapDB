<!-- Navbar.vue -->
<template>
  <div class="navbar">
    <img src="@/assets/BI_logo.png" alt="Logo" class="navbar-logo" />
    <!-- Add additional navbar content here -->

    <!-- Display username and logout button if authenticated -->
    <div class="navbar-right">
      <span v-if="isAuthenticated" class="username">Hello, {{ username }}</span>
      <button v-if="isAuthenticated" @click="logout" class="login-button">Logout</button>

      <!-- Show login button if not authenticated -->
      <button v-else @click="login" class="login-button">Login</button>
    </div>
  </div>
</template>

<script>
import { authState } from '../authState';  // Adjust the path as necessary

export default {
  name: 'Navbar',
  computed: {
    isAuthenticated() {
      return authState.isAuthenticated;
    },
    username() {
      return authState.username;
    }
  },
  methods: {
    login() {
      window.location.href = 'https://myfastapiapp.loca.lt/auth/login';
    },
    async logout() {
    try {
      const response = await fetch('https://myfastapiapp.loca.lt/auth/logout', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Accept': 'application/json',
        },
      });
      if (!response.ok) {
        throw new Error('Logout failed');
      }
      const data = await response.json();
      console.log(data.message); // Should log "Logged out successfully"

      // Clear your app's authentication state
      authState.isAuthenticated = false;
      authState.isAdmin = false;
      authState.username = null;

      // Redirect to home page
      this.$router.push('/');
    } catch (error) {
      console.error('Error during logout:', error);
    }
  }
  }
}
</script>

<style>
.navbar {
  display: flex;
  align-items: center;
  background-color: #ffffff00;
  padding: 10px 20px;
  color: #ff0000;
  border-bottom: solid #536160;
}

.navbar-logo {
  height: 50px;
  width: auto;
}

/* New styles for the right side of the navbar */
.navbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.username {
  margin-right: 10px;
  font-weight: bold;
  color: #333;
}

.login-button {
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s ease;
  background-color: #00796b;
  color: white;
}

.login-button:hover {
  background-color: #00796b8e;
}

.login-button:active {
  transform: scale(0.97);
}
</style>
