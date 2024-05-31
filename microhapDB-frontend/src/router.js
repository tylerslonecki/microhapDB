import { createRouter, createWebHistory } from 'vue-router';
import Home from './components/Home.vue';
import UploadComponent from './components/FileUpload.vue';
import JobStatus from './components/JobStatus.vue';
import Report from './components/Report.vue';
import Login from './components/Login.vue';


async function checkAuthStatus() {
  try {
    const response = await fetch('https://myfastapiapp.loca.lt/auth/status', {
      credentials: 'include'
    });

    if (!response.ok) {
      throw new Error('Failed to fetch authentication status');
    }

    return await response.json();
  } catch (error) {
    console.error('Error verifying authentication status:', error);
    return { is_authenticated: false, is_admin: false };
  }
}

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: UploadComponent, meta: { requiresAuth: true } },
  { path: '/job-status', name: 'JobStatus', component: JobStatus, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/report', name: 'Report', component: Report, meta: { requiresAuth: true } },
  { path: '/login', name: 'Login', component: Login }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  console.log("Router guard triggered");  // Initial log to confirm guard is running

  if (to.matched.some(record => record.meta.requiresAuth)) {
    const { is_authenticated, is_admin } = await checkAuthStatus();
    console.log("Is Authenticated:", is_authenticated); // Log authentication status
    console.log("Is Admin:", is_admin); // Log admin status

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
