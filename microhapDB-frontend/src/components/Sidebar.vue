<template>
  <div class="sidebar">
    <h2>Menu</h2>
    <ul>
      <li><router-link to="/">Home</router-link></li>
      <li><router-link to="/upload">Upload</router-link></li>
      <li><router-link to="/job-status">Job Status</router-link></li>
      <li><router-link to="/report">Database Report</router-link></li>
    </ul>
  </div>
</template>

<script>
import Cookies from 'js-cookie';

export default {
  name: 'Sidebar',
  data() {
    return {
      isAuthenticated: false,
      isAdmin: false
    };
  },
  methods: {
    checkAuth() {
      const token = Cookies.get('access_token');
      if (token) {
        this.isAuthenticated = true;
        // Perform a request to the backend to check if the user is an admin
        fetch('https://myfastapiapp.loca.lt/auth/users/me', {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        })
          .then(response => response.json())
          .then(data => {
            this.isAdmin = data.is_admin;
          })
          .catch(error => {
            console.error('Error fetching user info:', error);
          });
      }
    },
    logout() {
      Cookies.remove('access_token');
      Cookies.remove('is_admin');
      this.isAuthenticated = false;
      this.isAdmin = false;
      this.$router.push('/login');
    }
  },
  created() {
    this.checkAuth();
  }
}
</script>

<style>
.sidebar {
  width: 150px;
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
  font-size: 24px;
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
</style>
