<template>
  <div id="app" class="flex flex-column" style="height: 100vh;">
    <Menubar :model="menuItems" class="custom-menubar" />
    <div class="layout-container flex flex-row flex-nowrap">
      <aside class="sidebar d-flex flex-column p-2" style="width: 220px;">
        <div class="sidebar-header text-center mb-3">
          <img src="@/assets/logo.png" alt="Logo" class="sidebar-logo" />
          <h3 class="sidebar-title">MicrohapDB</h3>
        </div>
        <PanelMenu :model="sidebarItems" class="mt-2" />
      </aside>
      <main class="content-container p-3 flex-1 overflow-auto">
        <router-view></router-view>
      </main>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';

export default {
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin', 'username'])
  },
  data() {
    return {
      menuItems: [],
      sidebarItems: []
    };
  },
  async created() {
    await this.checkAuthStatus();
    this.buildMenus();
  },
  watch: {
    isAuthenticated: 'buildMenus',
    isAdmin: 'buildMenus'
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
    buildMenus() {
      this.menuItems = [
        {
          label: this.isAuthenticated ? `Hello, ${this.username}` : 'Welcome',
          items: [
            {
              label: this.isAuthenticated ? 'Logout' : 'Login',
              icon: this.isAuthenticated ? 'pi pi-sign-out' : 'pi pi-sign-in',
              command: () => {
                if (this.isAuthenticated) {
                  this.handleLogout();
                } else {
                  this.handleLogin();
                }
              }
            }
          ]
        }
      ];

      this.sidebarItems = [
        {
          label: 'Home',
          icon: 'pi pi-home',
          command: () => this.$router.push('/')
        },
        {
          label: 'Database Report',
          icon: 'pi pi-chart-bar',
          command: () => this.$router.push('/report')
        },
        {
          label: 'Admin',
          icon: 'pi pi-cog',
          visible: this.isAuthenticated && this.isAdmin,
          command: () => this.$router.push('/system-administration')
        },
        {
          label: 'Query',
          icon: 'pi pi-search',
          command: () => this.$router.push('/query')
        }
      ].filter(item => item.visible !== false);
    },
    handleLogin() {
      window.location.href = 'https://myfastapiapp.loca.lt/auth/login';
    },
    async handleLogout() {
      await this.logout();
      this.$router.push('/');
    }
  }
};
</script>

<style scoped>
.layout-container {
  flex: 1;
}

/* Sidebar styling */
.sidebar {
  width: 220px;
  /* background: linear-gradient(135deg, #3a4644, #536160); */
  /* color: #ffffff; */
  /* box-shadow: 2px 0 5px rgba(0,0,0,0.2); */
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sidebar-logo {
  max-width: 80px;
  margin-bottom: 10px;
}

.sidebar-title {
  /* color: #ffffff; */
  font-size: 1.2em;
  font-weight: 600;
}

/* Menubar styling */
.custom-menubar {
  border-radius: 0;
  background: #2c3532;
  border-bottom: 2px solid #3a4644;
  color: #ffffff;
}

/* Content styling */
.content-container {
  /* background: #f5f6f7; */
  padding: 1rem; /* Adjust padding as needed */
  /* Removed flex properties to allow full-width content */
}

/* Improve typography */
body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  /* background: #f5f6f7; */
  /* color: #333; */
}
</style>
