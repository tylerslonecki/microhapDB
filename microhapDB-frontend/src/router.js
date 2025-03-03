// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from './components/Home.vue';
import UploadComponent from './components/FileUpload.vue';
import JobStatus from './components/JobStatus.vue';
import Report from './components/Report.vue';
import Login from './components/Login.vue';
import SystemAdministration from './components/SystemAdministration.vue';
import Query from './components/Query.vue';
import Details from '@/components/Details.vue';
import DetailsAlt from '@/components/DetailsAlt.vue';
import Visualizations from '@/components/Visualizations.vue';
// import Alignment from './components/Alignment.vue';

import store from './store';

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/query', name: 'Query', component: Query },
  { 
    path: '/system-administration', 
    name: 'SystemAdministration', 
    component: SystemAdministration,
    // meta: { requiresAuth: true, requiresAdmin: true }
  },
  { 
    path: '/upload', 
    name: 'Upload', 
    component: UploadComponent, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/job-status', 
    name: 'JobStatus', 
    component: JobStatus, 
    meta: { requiresAuth: true, requiresAdmin: true } 
  },
  { 
    path: '/report', 
    name: 'Report', 
    component: Report
  },
  { path: '/login', name: 'Login', component: Login },
  { 
    path: '/details', 
    name: 'Details', 
    component: Details
  },
  { 
    path: '/detailsalt', 
    name: 'DetailsAlt', 
    component: DetailsAlt
  },
  { 
    path: '/visualizations', 
    name: 'Visualizations', 
    component: Visualizations
  }

  // { path: '/alignment', name: 'Alignment', component: Alignment }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

// Single router guard using Vuex store:
router.beforeEach(async (to, from, next) => {
  console.log("Router guard triggered");

  // Check if route requires authentication
  if (to.matched.some(record => record.meta.requiresAuth)) {
    // Dispatch action to update auth status from the API
    await store.dispatch('checkAuthStatus');

    const isAuthenticated = store.getters.isAuthenticated;
    const isAdmin = store.getters.isAdmin;

    console.log("Is Authenticated:", isAuthenticated);
    console.log("Is Admin:", isAdmin);

    if (!isAuthenticated) {
      console.log("Not authenticated, redirecting to Login");
      next({ name: 'Login' });
    } else if (to.matched.some(record => record.meta.requiresAdmin) && !isAdmin) {
      console.log("Not admin, redirecting to Home");
      next({ name: 'Home' });
    } else {
      console.log("Authenticated and authorized, proceeding to route");
      next();
    }
  } else {
    // No auth required, proceed
    next();
  }
});

export default router;
