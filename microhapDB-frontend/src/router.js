import { createRouter, createWebHistory } from 'vue-router';
import Home from './components/Home.vue';
import UploadComponent from './components/FileUpload.vue';
import JobStatus from './components/JobStatus.vue';
import Report from './components/Report.vue';
import Login from './components/Login.vue';

function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
}

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: UploadComponent },
  { path: '/job-status', name: 'JobStatus', component: JobStatus, meta: { requiresAuth: true, requiresAdmin: true } },
  { path: '/report', name: 'Report', component: Report },
  { path: '/login', name: 'Login', component: Login }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach(async (to, from, next) => {
  const token = getCookie('access_token');
  const isAuthenticated = !!token;
  let isAdmin = false;

  if (isAuthenticated) {
    try {
      const response = await fetch('https://myfastapiapp.loca.lt/auth/users/me', {
        headers: {
          'Authorization': `Bearer ${token}`
        },
        credentials: 'include'
      });
      const data = await response.json();
      isAdmin = data.is_admin;

      if (to.matched.some(record => record.meta.requiresAuth)) {
        if (!isAuthenticated) {
          next({ name: 'Login' });
        } else if (to.matched.some(record => record.meta.requiresAdmin) && !isAdmin) {
          next({ name: 'Home' });
        } else {
          next();
        }
      } else {
        next();
      }
    } catch (error) {
      console.error('Error verifying admin status:', error);
      next({ name: 'Login' });
    }
  } else {
    if (to.matched.some(record => record.meta.requiresAuth)) {
      next({ name: 'Login' });
    } else {
      next();
    }
  }
});

export default router;
