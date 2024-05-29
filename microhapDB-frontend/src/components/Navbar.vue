<template>
    <div class="navbar">
      <img src="@/assets/BI_logo.png" alt="Logo" class="navbar-logo" />
      <!-- Add additional navbar content here -->
    </div>
  </template>
  
  <script>
  export default {
    name: 'Navbar',
  }
  </script>
  
  <style>
  .navbar {
    display: flex;
    align-items: center;
    background-color: #ffffff00; /* Dark green, similar to the sidebar */
    padding: 10px 20px; /* Adjust based on your preference */
    color: #ff0000;
    border-bottom: solid #536160;
  }
  
  .navbar-logo {
    height: 50px; /* Adjust based on your logo's size */
    width: auto;
  }
  </style>
  