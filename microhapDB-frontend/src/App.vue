<template>
  <div id="app" class="flex flex-col min-h-screen">
    <!-- Menubar -->
    <Menubar class="custom-menubar">
      <!-- Start Slot: Logo and Hamburger Menu -->
      <template #start>
        <div class="flex items-center">
          <!-- Hamburger Menu for All Screens -->
          <Button icon="pi pi-bars" class="mr-2" @click="toggleSidebar" aria-label="Toggle Menu" />
          <!-- Make logo clickable to navigate to home page -->
          <div class="logo-container" @click="navigateToHome($event)" @keydown.enter="navigateToHome($event)" @keydown.space="navigateToHome($event)" tabindex="0" role="button" aria-label="Navigate to home page">
            <img src="@/assets/HaploSearch-logo13.png" alt="HaploSearch Logo" class="menubar-logo" />
          </div>
        </div>
      </template>

      <!-- End Slot: User Dropdown -->
      <template #end>
        <Dropdown
          :options="userMenuOptions"
          optionLabel="label"
          :placeholder="isAuthenticated ? `Hello, ${username}` : 'Welcome'"
          class="user-dropdown"
          @change="handleUserAction"
          appendTo="self"
          :showClear="false"
          :filter="false"
        >
          <template #icon>
            <i class="pi pi-user"></i>
          </template>
        </Dropdown>
      </template>
    </Menubar>

    <!-- Main Layout Container -->
    <div class="flex flex-1">
      <!-- Enhanced Sidebar Component (Collapsible on All Screens) -->
      <Sidebar
        v-model:visible="isSidebarVisible"
        position="left"
        :modal="isMobile"
        :dismissable="isMobile"
        :baseZIndex="1000"
        class="sidebar-custom"
      >
        <template #container="{ closeCallback }">
          <div class="flex flex-column h-full">
            <!-- Logo and Close Button -->
            <div class="flex align-items-center justify-content-between px-4 pt-3 flex-shrink-0">
              <span class="inline-flex align-items-center gap-2">
                <!-- Replace the SVG paths with your actual logo SVG paths -->
                <svg width="35" height="40" viewBox="0 0 35 40" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="..." fill="var(--primary-color-color)" />
                  <path d="..." fill="var(--text-color)" />
                </svg>
                <span class="font-semibold text-2xl text-primary">HaploSearch</span>
              </span>
              <span>
                <Button type="button" @click="closeCallback" icon="pi pi-times" rounded outlined class="h-2rem w-2rem"></Button>
              </span>
            </div>

            <!-- Sidebar Menu Items -->
            <div class="overflow-y-auto p-3">
              <ul class="list-none p-0 m-0">
                <!-- Iterate through sidebarItems to dynamically generate menu -->
                <li v-for="(item, index) in sidebarItems.filter(item => item.visible !== false)" :key="index">
                  <!-- If the item has submenus, render a collapsible section -->
                  <div v-if="item.subItems" class="mb-2">
                    <div
                      @click="toggleSubMenu(index, $event)"
                      @keydown.enter="toggleSubMenu(index, $event)"
                      @keydown.space="toggleSubMenu(index, $event)"
                      class="p-3 flex align-items-center justify-content-between text-600 cursor-pointer submenu-toggle"
                      tabindex="0"
                      role="button"
                      :aria-expanded="item.isOpen"
                      :aria-label="`Toggle ${item.label} submenu`"
                    >
                      <span class="font-medium">{{ item.label }}</span>
                      <i :class="{'pi pi-chevron-down': !item.isOpen, 'pi pi-chevron-up': item.isOpen}"></i>
                    </div>
                    <ul v-show="item.isOpen" class="list-none pl-4">
                      <li v-for="(subItem, subIndex) in item.subItems.filter(subItem => subItem.visible !== false)" :key="subIndex">
                        <a
                          @click="navigate(subItem.route)"
                          @keydown.enter="navigate(subItem.route)"
                          @keydown.space="navigate(subItem.route)"
                          class="flex align-items-center cursor-pointer p-2 hover:bg-gray-200 rounded navigation-link"
                          tabindex="0"
                          role="button"
                          :aria-label="`Navigate to ${subItem.label}`"
                        >
                          <i :class="subItem.icon" class="mr-2"></i>
                          <span class="font-medium">{{ subItem.label }}</span>
                        </a>
                      </li>
                    </ul>
                  </div>
                  <!-- If the item has no submenus, render a single link -->
                  <div v-else>
                    <a
                      @click="navigate(item.route)"
                      @keydown.enter="navigate(item.route)"
                      @keydown.space="navigate(item.route)"
                      class="flex align-items-center cursor-pointer p-3 hover:bg-gray-200 rounded navigation-link"
                      tabindex="0"
                      role="button"
                      :aria-label="`Navigate to ${item.label}`"
                    >
                      <i :class="item.icon" class="mr-2"></i>
                      <span class="font-medium">{{ item.label }}</span>
                    </a>
                  </div>
                </li>
              </ul>
            </div>

            <!-- User Section at the Bottom -->
            <div class="mt-auto p-3">
              <hr class="mb-3 border-t border-gray-300" />
              <!-- Updated Logout Section: Replaced Avatar with Signout Icon -->
              <a @click="handleLogout" @keydown.enter="handleLogout" @keydown.space="handleLogout" class="flex align-items-center cursor-pointer p-3 gap-2 hover:bg-gray-200 rounded logout-button" tabindex="0" role="button" aria-label="Logout">
                <i class="pi pi-sign-out text-xl"></i>
                <span class="font-bold">Logout</span>
              </a>
            </div>
          </div>
        </template>
      </Sidebar>

      <!-- Overlay for Desktop when Sidebar is Visible -->
      <div
        v-if="isSidebarVisible && !isMobile"
        class="fixed inset-0 bg-black opacity-50 z-900"
        @click="toggleSidebar"
      ></div>

      <!-- Main Content -->
      <main
        :class="{
          'ml-64': isSidebarVisible && !isMobile,
          'flex-1 p-4 overflow-auto': true
        }"
        class="content-container"
        @click="isSidebarVisible && (isSidebarVisible = false)"
      >
        <router-view v-slot="{ Component, route }">
          <template v-if="route.meta.requiresAuth">
            <AuthGuard 
              :required-role="route.meta.requiredRole"
              :required-roles="route.meta.requiredRoles"
            >
              <component :is="Component" />
            </AuthGuard>
          </template>
          <template v-else>
            <component :is="Component" />
          </template>
        </router-view>
      </main>
    </div>
  </div>
</template>

<script>
import { mapGetters, mapActions } from 'vuex';
import Dropdown from 'primevue/dropdown';
import Menubar from 'primevue/menubar';
import Button from 'primevue/button';
import Sidebar from 'primevue/sidebar';
import axios from 'axios';
import AuthGuard from '@/components/AuthGuard.vue';

export default {
  name: 'App',
  components: {
    Dropdown,
    Menubar,
    Button,
    Sidebar,
    AuthGuard,
  },
  data() {
    return {
      sidebarItems: [
        {
          label: 'Home',
          icon: 'pi pi-home',
          route: '/',
        },
        {
          label: 'Query',
          icon: 'pi pi-search',
          route: '/query',
          requiresAuth: true,
        },
        {
          label: 'Visualizations',
          icon: 'pi pi-chart-bar',
          isOpen: false,
          requiresAuth: true,
          subItems: [
            // {
            //   label: 'Histogram',
            //   icon: 'pi pi-chart-bar',
            //   route: '/visualizations',
            // },
            {
              label: 'Missing Alleles',
              icon: 'pi pi-chart-bar',
              route: '/visualizations-comparative',
            }
          ]
        },
        {
          label: 'Database Report',
          icon: 'pi pi-chart-line',
          route: '/report',
        },
        {
          label: 'User Management',
          icon: 'pi pi-users',
          route: '/user-management',
          // Only visible to private users (non-admin)
          visible: this.userRole === 'private_user',
          requiresAuth: true,
        },
        {
          label: 'Admin',
          icon: 'pi pi-cog',
          isOpen: false,
          // Only visible if the user is an admin (removed private_user access)
          visible: this.isAdmin,
          subItems: [
            {
              label: 'Data Upload',
              icon: 'pi pi-upload',
              route: '/data-upload',
              // Only visible if the user is an admin
              visible: this.isAdmin,
            },
            {
              label: 'Admin Dashboard',
              icon: 'pi pi-th-large',
              route: '/admin',
              // Only visible to admin users
              visible: this.isAdmin,
            }
          ]
        },
      ],
      userMenuOptions: [],
      isSidebarVisible: false, // State for Sidebar visibility
      isMobile: window.innerWidth < 768, // Initial mobile state
    };
  },
  computed: {
    ...mapGetters('auth', ['isAuthenticated', 'isAdmin', 'canAccessPrivateData']),
    username() {
      return this.$store.state.auth.user?.username || '';
    }
  },
  created() {
    // Check auth status when app starts
    this.checkAndUpdateAuthStatus();
    
    // Add event listener to handle window resize
    window.addEventListener('resize', this.handleResize);
    
    // Listen for URL changes to catch token parameters
    window.addEventListener('popstate', this.checkForTokenInUrl);
  },
  mounted() {
    // Double-check for token in URL on mount
    this.checkForTokenInUrl();
  },
  beforeUnmount() {
    // Clean up event listeners
    window.removeEventListener('resize', this.handleResize);
    window.removeEventListener('popstate', this.checkForTokenInUrl);
  },
  watch: {
    isAuthenticated(newVal) {
      console.log('Authentication state changed:', newVal);
      this.buildMenus();
    },
    isAdmin(newVal) {
      console.log('Admin state changed:', newVal);
      this.buildMenus();
    },
  },
  methods: {
    ...mapActions('auth', ['logout', 'checkAuthStatus']),
    
    async checkAndUpdateAuthStatus() {
      try {
        await this.checkAuthStatus();
        console.log('Auth status checked, isAuthenticated:', this.isAuthenticated);
        this.buildMenus();
      } catch (error) {
        console.error('Error checking auth status:', error);
      }
    },
    
    checkForTokenInUrl() {
      const urlParams = new URLSearchParams(window.location.search);
      const token = urlParams.get('token');
      
      if (token) {
        console.log('Token found in URL during navigation');
        localStorage.setItem('access_token', token);
        
        // Clean up the URL
        const cleanUrl = window.location.pathname;
        window.history.replaceState({}, document.title, cleanUrl);
        
        // Update auth status
        this.checkAndUpdateAuthStatus();
      }
    },
    
    buildMenus() {
      // Update visibility based on authentication and admin status
      this.sidebarItems.forEach((item) => {
        // Handle user management for private users
        if (item.label === 'User Management') {
          item.visible = this.userRole === 'private_user';
        }
        
        // Handle admin-only items
        if (item.label === 'Admin') {
          item.visible = this.isAdmin;
          
          // Handle submenu items visibility
          if (item.subItems) {
            item.subItems.forEach(subItem => {
              if (subItem.label === 'System Administration' || subItem.label === 'Admin Dashboard') {
                subItem.visible = this.isAdmin;
              } else if (subItem.label === 'User Management') {
                subItem.visible = this.isAdmin;
              }
            });
          }
        }
        
        // Handle auth-required items
        if (item.requiresAuth) {
          item.visible = this.isAuthenticated;
        }
      });

      // User Menu Options
      if (this.isAuthenticated) {
        this.userMenuOptions = [
          { label: `Hello, ${this.username}`, value: 'none', disabled: true },
          { label: 'Logout', value: 'logout', icon: 'pi pi-sign-out' },
        ];
      } else {
        this.userMenuOptions = [
          { label: 'Welcome', value: 'none', disabled: true },
          { label: 'Login', value: 'login', icon: 'pi pi-sign-in' },
        ];
      }
    },
    handleUserAction(event) {
      const action = event.value;
      if (action === 'login') {
        this.handleLogin();
      } else if (action === 'logout') {
        this.handleLogout();
      }
      // Reset dropdown to prevent it from staying selected
      event.value = null;
    },
    handleLogin() {
      try {
        window.location.href = `${axios.defaults.baseURL}/auth/login`;
      } catch (error) {
        console.error('Login redirect error:', error);
        // Fallback for cases where baseURL might not be set
        window.location.href = '/auth/login';
      }
    },
    async handleLogout() {
      try {
        await this.logout();
        // Show success message if toast is available
        if (this.$toast) {
          this.$toast.add({
            severity: 'success',
            summary: 'Logged Out',
            detail: 'You have been successfully logged out.',
            life: 3000
          });
        }
        this.$router.push('/');
      } catch (error) {
        console.error('Logout error:', error);
        // Show error message if toast is available
        if (this.$toast) {
          this.$toast.add({
            severity: 'error',
            summary: 'Logout Error',
            detail: 'There was an issue logging you out. Please try again.',
            life: 5000
          });
        }
      }
    },
    toggleSidebar() {
      this.isSidebarVisible = !this.isSidebarVisible;
    },
    toggleSubMenu(index, event) {
      // Prevent default behavior for keyboard events
      if (event && event.type === 'keydown') {
        event.preventDefault();
      }
      this.sidebarItems[index].isOpen = !this.sidebarItems[index].isOpen;
    },
    navigate(route) {
      this.$router.push(route);
      this.isSidebarVisible = false; // Close the sidebar after navigation
    },
    navigateToHome(event) {
      // Prevent default behavior for keyboard events
      if (event && event.type === 'keydown') {
        event.preventDefault();
      }
      this.$router.push('/');
    },
    handleResize() {
      const wasMobile = this.isMobile;
      this.isMobile = window.innerWidth < 768;
      // Close sidebar if switching to desktop view
      if (wasMobile && !this.isMobile && this.isSidebarVisible) {
        this.isSidebarVisible = false;
      }
    },
  },
};
</script>

<style scoped>
/* Ensure the app takes full height */
#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* Menubar styling */
.custom-menubar {
  display: flex;
  align-items: center;
  padding: 0.5rem 1rem;
  background-color: var(--primary-color);
  color: #ffffff;
}

/* Logo styling */
.menubar-logo {
  height: 50px;
  object-fit: contain;
  border-radius: 8px;
  border: 2px solid #ffffff;
}

/* Logo container styling for clickable behavior */
.logo-container {
  cursor: pointer;
  border-radius: 8px;
  padding: 4px;
  transition: all 0.2s ease-in-out;
  outline: none;
}

.logo-container:hover {
  background-color: rgba(255, 255, 255, 0.1);
  transform: scale(1.05);
}

.logo-container:focus {
  background-color: rgba(255, 255, 255, 0.1);
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
}

.logo-container:active {
  transform: scale(0.98);
}

/* Navigation link accessibility styles */
.navigation-link:focus,
.submenu-toggle:focus,
.logout-button:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
  background-color: rgba(0, 0, 0, 0.05);
}

/* Improved hover states */
.navigation-link:hover,
.submenu-toggle:hover,
.logout-button:hover {
  background-color: #e5e7eb !important;
  transition: background-color 0.2s ease;
}

/* Active states for better feedback */
.navigation-link:active,
.submenu-toggle:active,
.logout-button:active {
  background-color: #d1d5db !important;
  transform: translateY(1px);
}

/* Ensure icons don't interfere with focus */
.navigation-link i,
.submenu-toggle i,
.logout-button i {
  pointer-events: none;
}

/* User Dropdown Styling */
.user-dropdown {
  margin-left: auto;
  min-width: 150px;
}

.user-dropdown .p-dropdown-label {
  display: flex;
  align-items: center;
}

.user-dropdown .pi-user {
  margin-right: 5px;
  font-size: 1.2em;
}

/* Sidebar Custom Styling */
.sidebar-custom {
  width: 250px;
}

.sidebar-custom .p-sidebar {
  background-color: #f8f9fa;
}

.sidebar-custom .p-sidebar .p-sidebar-content {
  padding: 0;
}

/* PanelMenu styling (if using) */
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

/* Content styling */
.content-container {
  background: #ffffff;
  transition: margin-left 0.3s ease-in-out;
  width: 100%;
}

/* Overlay styling */
.fixed.inset-0.bg-black.opacity-50.z-900 {
  z-index: 900;
}

/* Responsive Adjustments */
@media (max-width: 768px) {
  /* Adjust padding for mobile */
  .content-container {
    padding: 1rem 0.5rem;
  }

  /* Menubar logo smaller on mobile */
  .menubar-logo {
    height: 40px;
  }

  /* User dropdown adjustments for mobile */
  .user-dropdown {
    min-width: 120px;
    font-size: 0.9rem;
  }

  /* Sidebar adjustments for mobile */
  .sidebar-custom {
    width: 280px;
  }

  /* Logo container adjustments for mobile */
  .logo-container {
    padding: 2px;
  }

  .logo-container:hover {
    transform: scale(1.02);
  }
}


/* Optional: Hide overlay on mobile */
@media (max-width: 768px) {
  .fixed.inset-0.bg-black.opacity-50.z-900 {
    display: none;
  }
}

</style>
