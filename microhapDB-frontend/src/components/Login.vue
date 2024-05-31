<template>
    <div>
      <button @click="login" class="styled-button">Login with ORCID</button>
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
  
  <style>
  .styled-button {
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s ease;
    background-color: #00796b; /* Aesthetic green color */
    color: white;
  }
  
  .styled-button:hover {
    background-color: #00796b8e; /* A darker shade for hover state */
  }
  
  .styled-button:active {
    transform: scale(0.97); /* Scales button down when clicked */
  }
  </style>