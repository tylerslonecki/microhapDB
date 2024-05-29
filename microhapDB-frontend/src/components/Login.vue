<template>
    <div>
      <button @click="login">Login with ORCID</button>
    </div>
  </template>
  
  <script>
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
  