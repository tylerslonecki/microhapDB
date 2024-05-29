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

export default {
  components: {
    Sidebar,
    Navbar // Register the Navbar component
  }
}
</script>

<style>
.content {
  margin-left: 250px; /* Same as sidebar width */
  padding: 20px;
}

html, body {
  margin: 0;
  padding: 0;
}
</style>
