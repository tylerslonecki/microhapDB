<template>
  <div id="app" class="flex flex-col min-h-screen">
    <!-- Menubar -->
    <Menubar class="custom-menubar">
      <!-- Start Slot: Logo and Hamburger Menu -->
      <template #start>
        <div class="flex items-center">
          <!-- Hamburger Menu for All Screens -->
          <Button icon="pi pi-bars" class="mr-2" @click="toggleSidebar" aria-label="Toggle Menu" />
          <img src="@/assets/HaploSearch-logo13.png" alt="Logo" class="menubar-logo" />
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
                <li v-for="(item, index) in sidebarItems" :key="index">
                  <!-- If the item has submenus, render a collapsible section -->
                  <div v-if="item.subItems" class="mb-2">
                    <div
                      @click="toggleSubMenu(index)"
                      class="p-3 flex align-items-center justify-content-between text-600 cursor-pointer"
                    >
                      <span class="font-medium">{{ item.label }}</span>
                      <i :class="{'pi pi-chevron-down': !item.isOpen, 'pi pi-chevron-up': item.isOpen}"></i>
                    </div>
                    <ul v-show="item.isOpen" class="list-none pl-4">
                      <li v-for="(subItem, subIndex) in item.subItems" :key="subIndex">
                        <a
                          @click="navigate(subItem.route)"
                          class="flex align-items-center cursor-pointer p-2 hover:bg-gray-200 rounded"
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
                      class="flex align-items-center cursor-pointer p-3 hover:bg-gray-200 rounded"
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
              <a @click="handleLogout" class="flex align-items-center cursor-pointer p-3 gap-2 hover:bg-gray-200 rounded">
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
      >
        <router-view></router-view>
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

export default {
  components: {
    Dropdown,
    Menubar,
    Button,
    Sidebar,
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
          label: 'Database Report',
          icon: 'pi pi-chart-bar',
          route: '/report',
        },
        {
          label: 'Admin',
          icon: 'pi pi-cog',
          route: '/system-administration',
          // Only visible if the user is an admin
          visible: this.isAdmin,
        },
        {
          label: 'Query',
          icon: 'pi pi-search',
          route: '/query',
        },
      ],
      userMenuOptions: [],
      isSidebarVisible: false, // State for Sidebar visibility
      isMobile: window.innerWidth < 768, // Initial mobile state
    };
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin', 'username']),
    // Additional computed properties can be added here
  },
  async created() {
    await this.checkAuthStatus();
    this.buildMenus();
    // Add event listener to handle window resize
    window.addEventListener('resize', this.handleResize);
  },
  beforeUnmount() {
    // Clean up event listener
    window.removeEventListener('resize', this.handleResize);
  },
  watch: {
    isAuthenticated: 'buildMenus',
    isAdmin: 'buildMenus',
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
    buildMenus() {
      // Update visibility based on admin status
      this.sidebarItems.forEach((item) => {
        if (item.visible !== undefined) {
          item.visible = item.visible && this.isAdmin;
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
    },
    handleLogin() {
      window.location.href = 'https://myfastapiapp.loca.lt/auth/login';
    },
    async handleLogout() {
      await this.logout();
      this.$router.push('/');
    },
    toggleSidebar() {
      this.isSidebarVisible = !this.isSidebarVisible;
    },
    toggleSubMenu(index) {
      this.sidebarItems[index].isOpen = !this.sidebarItems[index].isOpen;
    },
    navigate(route) {
      this.$router.push(route);
      this.isSidebarVisible = false; // Close the sidebar after navigation
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
  height: 40px;
  object-fit: contain;
  border-radius: 8px;
  border: 2px solid #ffffff;
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
    height: 35px;
  }
}

/* Optional: Hide overlay on mobile */
@media (max-width: 768px) {
  .fixed.inset-0.bg-black.opacity-50.z-900 {
    display: none;
  }
}
</style>
