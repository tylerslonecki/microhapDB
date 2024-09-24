// router.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from './components/Home.vue';
import UploadComponent from './components/FileUpload.vue';
import JobStatus from './components/JobStatus.vue';
import Report from './components/Report.vue';
import Login from './components/Login.vue';
import SystemAdministration from './components/SystemAdministration.vue';
import Query from './components/Query.vue';
// import Alignment from './components/Alignment.vue';

import { authState } from './authState'; // Import the global auth state

async function checkAuthStatus() {
  try {
    const response = await fetch('https://myfastapiapp.loca.lt/auth/status', {
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Failed to fetch authentication status');
    }

    const authStatus = await response.json();

    // Update authState
    authState.isAuthenticated = authStatus.is_authenticated;
    authState.isAdmin = authStatus.is_admin;
    authState.username = authStatus.username;  // Update username

    return authStatus;
  } catch (error) {
    console.error('Error verifying authentication status:', error);
    authState.isAuthenticated = false;
    authState.isAdmin = false;
    authState.username = null;
    return { is_authenticated: false, is_admin: false, username: null };
  }
}

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/query', name: 'Query', component: Query },
  { path: '/system-administration', name: 'SystemAdministration', component: SystemAdministration, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/upload', name: 'Upload', component: UploadComponent, meta: { requiresAuth: true } },
  { path: '/job-status', name: 'JobStatus', component: JobStatus, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/report', name: 'Report', component: Report, meta: { requiresAuth: true } },
  { path: '/login', name: 'Login', component: Login },
  // { path: '/alignment', name: 'Alignment', component: Alignment }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  console.log("Router guard triggered");

  if (to.matched.some(record => record.meta.requiresAuth)) {
    const authStatus = await checkAuthStatus();
    const { is_authenticated, is_admin } = authStatus;

    console.log("Is Authenticated:", is_authenticated);
    console.log("Is Admin:", is_admin);

    if (!is_authenticated) {
      console.log("Not authenticated, redirecting to Login");
      next({ name: 'Login' });
    } else if (to.matched.some(record => record.meta.requiresAdmin) && !is_admin) {
      console.log("Not admin, redirecting to Home");
      next({ name: 'Home' });
    } else {
      console.log("Authenticated and authorized, proceeding to route");
      next();
    }
  } else {
    next();
  }
});

export default router;
