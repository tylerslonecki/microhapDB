<template>
  <div class="sidebar">
    <h2>Menu</h2>
    <ul>
      <li><router-link to="/">Home</router-link></li>
      <li><router-link to="/report">Database Report</router-link></li>
      <li v-if="authState.isAuthenticated">
        <span class="submenu-title">System Administration</span>
        <ul class="submenu">
          <li><router-link to="/upload">Upload</router-link></li>
          <li><router-link to="/job-status">Job Status</router-link></li>
        </ul>
      </li>
    </ul>
  </div>
</template>

<script>
import { authState } from '@/authState'; // Adjust the path if necessary

export default {
  name: 'Sidebar',
  data() {
    return {
      authState
    };
  }
}
</script>

<style>
.sidebar {
  width: 200px; /* Fixed width for the sidebar */
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  background-color: #536160;
  color: #ffffff;
  padding: 20px;
  margin-top: 70px;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  box-shadow: 2px 0 5px rgba(0,0,0,0.2);
}

.sidebar h2 {
  color: #c0d3da;
  margin-bottom: 20px;
  font-size: 18px;
}

.sidebar ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.sidebar ul li {
  margin-bottom: 10px;
}

.sidebar ul li a {
  color: #c0d3da;
  text-decoration: none;
  font-size: 18px;
  display: block;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.sidebar ul li a:hover {
  background-color: #00796b;
  color: #ffffff;
}

.submenu-title {
  color: #c0d3da;
  font-size: 18px;
  display: block;
  padding: 10px;
  border-radius: 4px;
  text-align: center;
  margin-top: 40px; /* Add margin before the System Administration menu */
}

.submenu {
  list-style-type: none;
  padding: 0;
  margin: 0 0 0 20px;
}

.submenu li {
  margin-bottom: 10px;
}

.submenu li a {
  font-size: 16px; /* Slightly smaller font size for submenu items */
}
</style>