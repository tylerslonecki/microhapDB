<template>
  <div class="sidebar">
    <h2>Menu</h2>
    <ul>
      <li><router-link to="/"><i class="fas fa-home"></i> Home</router-link></li>
      <li><router-link to="/report"><i class="fas fa-chart-bar"></i> Database Report</router-link></li>
      <li v-if="authState.isAuthenticated">
        <span class="submenu-title"><i class="fas fa-cogs"></i> System Administration</span>
        <ul class="submenu">
          <li><router-link to="/upload"><i class="fas fa-upload"></i> Upload</router-link></li>
          <li><router-link to="/job-status"><i class="fas fa-tasks"></i> Job Status</router-link></li>
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
@import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css');

.sidebar {
  width: 220px; /* Fixed width for the sidebar */
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
  transition: all 0.3s ease;
}

.sidebar h2 {
  color: #ecf0f1;
  margin-bottom: 20px;
  font-size: 24px;
  text-align: center;
  border-bottom: 1px solid #34495e;
  padding-bottom: 10px;
}

.sidebar ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.sidebar ul li {
  margin-bottom: 15px;
}

.sidebar ul li a {
  color: #ecf0f1;
  text-decoration: none;
  font-size: 18px;
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  transition: background-color 0.3s ease;
}

.sidebar ul li a i {
  margin-right: 10px;
}

.sidebar ul li a:hover {
  background-color: #34495e;
}

.submenu-title {
  color: #ecf0f1;
  font-size: 20px;
  font-weight: bold;
  display: flex;
  align-items: center;
  padding: 10px;
  border-radius: 4px;
  background-color: #1abc9c;
  text-align: center;
  margin-top: 30px; /* Add margin before the System Administration menu */
}

.submenu-title i {
  margin-right: 10px;
}

.submenu {
  list-style-type: none;
  padding: 0;
  margin: 10px 0 0 20px;
}

.submenu li {
  margin-bottom: 10px;
}

.submenu li a {
  font-size: 16px; /* Slightly smaller font size for submenu items */
}
</style>