<!-- Login.vue -->
<template>
  <div>
    <button @click="login" class="styled-button">Login with ORCID</button>
  </div>
</template>

<script>
import { authState } from '../authState'; // Adjust the path as necessary

export default {
  methods: {
    login() {
      window.location.href = 'https://myfastapiapp.loca.lt/auth/login';
    },
    async handleCallback() {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');

      if (code) {
        try {
          const response = await fetch(`https://myfastapiapp.loca.lt/auth/callback?code=${code}`, {
            credentials: 'include'
          });
          if (!response.ok) {
            throw new Error('Failed to fetch token');
          }

          // Fetch the authentication status
          const authStatusResponse = await fetch('https://myfastapiapp.loca.lt/auth/status', {
            credentials: 'include'
          });
          const authStatus = await authStatusResponse.json();

          // Update authState
          authState.isAuthenticated = authStatus.is_authenticated;
          authState.isAdmin = authStatus.is_admin;
          authState.username = authStatus.username;  // Update username

          // Redirect to home page or any other page after successful login
          this.$router.push('/');
        } catch (error) {
          console.error('Error during ORCID callback:', error);
        }
      }
    }
  },
  created() {
    this.handleCallback();
  }
}
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
