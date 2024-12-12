<template>
  <div class="p-d-flex p-jc-center p-ai-center p-flex-column" style="height:100vh;">
    <button @click="login" class="styled-button">Login with ORCID</button>
  </div>
</template>

<script>
import { mapActions } from 'vuex';

export default {
  methods: {
    ...mapActions(['checkAuthStatus']),

    login() {
      // Direct the user to the backend's login endpoint
      window.location.href = 'https://myfastapiapp.loca.lt/auth/login';
    },
    async handleCallback() {
      const urlParams = new URLSearchParams(window.location.search);
      const code = urlParams.get('code');

      if (code) {
        try {
          // Exchange code for token at callback endpoint
          const response = await fetch(`https://myfastapiapp.loca.lt/auth/callback?code=${code}`, {
            credentials: 'include' // Include cookies
          });

          if (!response.ok) {
            throw new Error('Failed to fetch token');
          }

          // Once the token cookie is set by the backend, check auth status
          await this.checkAuthStatus();

          // Redirect to home page after successful authentication
          this.$router.push('/');
        } catch (error) {
          console.error('Error during ORCID callback:', error);
        }
      }
    }
  },
  created() {
    // If user returned from ORCID with a code, handle it
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
