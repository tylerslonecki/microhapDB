// src/router/index.js
import { createRouter, createWebHistory } from 'vue-router';
import Home from './components/Home.vue';
import UploadComponent from './components/FileUpload.vue';
import JobStatus from './components/JobStatus.vue';
import Query from './components/Query.vue';
import Details from '@/components/Details.vue';
import DetailsAlt from '@/components/DetailsAlt.vue';
import Visualizations from '@/components/Visualizations.vue';
import Visualizations2 from '@/components/Visualizations2.vue';
import AdminDashboard from './components/AdminDashboard.vue';
import Login from './components/Login.vue';
import Report from './components/Report.vue';
import DataUpload from './components/DataUpload.vue';

const routes = [
  { 
    path: '/', 
    name: 'Home', 
    component: Home 
  },
  { 
    path: '/upload', 
    name: 'Upload', 
    component: UploadComponent, 
    meta: { requiresAuth: true, requiredRole: 'admin' } 
  },
  { 
    path: '/jobStatus', 
    name: 'JobStatus', 
    component: JobStatus, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/query', 
    name: 'Query', 
    component: Query, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/details', 
    name: 'Details', 
    component: Details, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/detailsAlt', 
    name: 'DetailsAlt', 
    component: DetailsAlt, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/visualizations', 
    name: 'Visualizations', 
    component: Visualizations, 
    meta: { requiresAuth: true } 
  },
  { 
    path: '/visualizations-comparative', 
    name: 'Visualizations2', 
    component: Visualizations2,
    meta: { requiresAuth: true }
  },
  {
    path: '/data-upload',
    name: 'DataUpload',
    component: DataUpload,
    meta: { requiresAuth: true, requiredRole: 'admin' }
  },
  {
    path: '/report',
    name: 'Report',
    component: Report
  },
  {
    path: '/user-management',
    name: 'PrivacyCollaborators',
    component: () => import('./components/UserManagement.vue'),
    meta: { requiresAuth: true, requiredRole: 'private_user' }
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, requiredRole: 'admin' }
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresAuth: false }
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// Simple navigation guard to check route access
// We won't try to access the store directly from here to avoid the error
router.beforeEach((to, from, next) => {
  // If the route doesn't require auth, proceed
  if (!to.meta.requiresAuth) {
    next();
    return;
  }

  // For routes requiring auth, we'll let the component handle it using AuthGuard
  next();
});

export default router;
