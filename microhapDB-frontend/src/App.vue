<template>
  <div id="app" class="flex flex-column" style="height: 100vh;">
    <Menubar :model="menuItems" class="custom-menubar" />
    <div class="layout-container flex flex-row flex-nowrap">
      <aside class="sidebar d-flex flex-column py-4 px-3" style="width: 240px;">
        <div class="sidebar-header text-center mb-4">
          <img src="@/assets/BreedingInsightLogo-RGB-1600px.png" alt="Logo" class="sidebar-logo mb-2" />
          <h3 class="sidebar-title mb-0">HaploSearch</h3>
        </div>
        <div class="sidebar-menu-container mt-3">
          <PanelMenu :model="sidebarItems" class="custom-panelmenu" />
        </div>
      </aside>
      <main class="content-container p-4 flex-1 overflow-auto">
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
  width: 240px;
  background: #f8f9fa;
  border-right: 1px solid #dee2e6;
}

.sidebar-header {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.sidebar-logo {
  max-width: 100px;
  margin-bottom: 0.5rem;
}

.sidebar-title {
  font-size: 1.25em;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.sidebar-menu-container {
  flex: 1;
}

/* PanelMenu styling */
.custom-panelmenu .p-panelmenu .p-panelmenu-header .p-panelmenu-header-link {
  padding: 0.75rem 1rem;
  font-size: 14px;
}

.custom-panelmenu .p-panelmenu .p-panelmenu-content .p-panelmenu-root-submenu > .p-panelmenu-item .p-panelmenu-submenu-list > .p-panelmenu-submenu-item {
  padding: 0.5rem 1.5rem;
  font-size: 14px;
}

.custom-panelmenu .p-panelmenu .p-panelmenu-content .p-panelmenu-header .p-panelmenu-icon {
  margin-right: 0.5rem;
}

/* Menubar styling */
.custom-menubar {
  border-radius: 0;
  border-bottom: 2px solid #3a4644;
  color: #ffffff;
}

/* Content styling */
.content-container {
  background: #ffffff;
  padding: 1rem; 
}

/* Improve typography */
body {
  font-family: 'Inter', sans-serif;
  font-size: 14px;
  color: #333;
}
</style>
