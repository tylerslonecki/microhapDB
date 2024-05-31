<template>
  <div class="navbar">
    <img src="@/assets/BI_logo.png" alt="Logo" class="navbar-logo" />
    <!-- Add additional navbar content here -->
    <button @click="openLoginModal" class="login-button">Login</button>
    <Modal :isOpen="isLoginModalOpen" @close="closeLoginModal">
      <Login />
    </Modal>
  </div>
</template>

<script>
import Modal from './Modal.vue';
import Login from './Login.vue';

export default {
  name: 'Navbar',
  components: {
    Modal,
    Login
  },
  data() {
    return {
      isLoginModalOpen: false
    };
  },
  methods: {
    openLoginModal() {
      this.isLoginModalOpen = true;
    },
    closeLoginModal() {
      this.isLoginModalOpen = false;
    }
  }
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

.login-button {
  margin-left: auto;
  border: none;
  padding: 10px 20px;
  border-radius: 5px;
  cursor: pointer;
  font-weight: bold;
  transition: background-color 0.3s ease;
  background-color: #00796b; /* Aesthetic green color */
  color: white;
}

.login-button:hover {
  background-color: #005f56; /* A darker shade for hover state */
}

.login-button:active {
  transform: scale(0.97); /* Scales button down when clicked */
}
</style>
