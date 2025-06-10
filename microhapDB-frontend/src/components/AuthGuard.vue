<template>
  <div v-if="isLoading" class="loading-container" aria-live="polite">
    <i class="pi pi-spinner pi-spin" aria-hidden="true"></i>
    <span class="sr-only">Loading authentication status...</span>
    <span class="loading-text">Loading...</span>
  </div>
  <div v-else-if="!isAuthenticated" class="auth-message-container">
    <slot name="unauthorized">
      <div class="unauthorized-message" role="alert">
        <i class="pi pi-exclamation-triangle" aria-hidden="true"></i>
        <p>Please log in to access this page.</p>
        <router-link to="/login" class="auth-link">Login</router-link>
      </div>
    </slot>
  </div>
  <div v-else-if="!hasRequiredRole" class="auth-message-container">
    <slot name="forbidden">
      <div class="forbidden-message" role="alert">
        <i class="pi pi-ban" aria-hidden="true"></i>
        <p>You don't have permission to access this page.</p>
        <router-link to="/" class="auth-link">Return to Home</router-link>
      </div>
    </slot>
  </div>
  <div v-else>
    <slot></slot>
  </div>
</template>

<script>
import { mapState, mapGetters } from 'vuex';

export default {
  name: 'AuthGuard',
  props: {
    requiredRole: {
      type: String,
      default: null
    },
    requiredRoles: {
      type: Array,
      default: () => []
    },
    requireAuth: {
      type: Boolean,
      default: true
    }
  },
  data() {
    return {
      isLoading: true
    };
  },
  computed: {
    ...mapState('auth', ['isAuthenticated', 'role']),
    ...mapGetters('auth', ['isAdmin']),
    hasRequiredRole() {
      if (!this.requireAuth) return true;
      if (!this.requiredRole && this.requiredRoles.length === 0) return true;
      
      const roleHierarchy = {
        admin: 3,
        private_user: 2,
        collaborator: 1,
        public: 0
      };
      
      // Check if user has one of the required roles in the array
      if (this.requiredRoles && this.requiredRoles.length > 0) {
        return this.requiredRoles.includes(this.role);
      }
      
      // Fall back to single role check
      return roleHierarchy[this.role] >= roleHierarchy[this.requiredRole];
    }
  },
  async created() {
    try {
      await this.$store.dispatch('auth/checkAuthStatus');
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      this.isLoading = false;
    }
  }
};
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 200px;
}

.loading-text {
  margin-top: 1rem;
  color: var(--text-color-secondary);
  font-size: 1.1rem;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.auth-message-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
  padding: 2rem;
}

.unauthorized-message,
.forbidden-message {
  text-align: center;
  padding: 2rem;
  margin: 2rem;
  border: 1px solid #ddd;
  border-radius: 8px;
  background-color: #f9f9f9;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  max-width: 400px;
}

.unauthorized-message i,
.forbidden-message i {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #f59e0b;
}

.unauthorized-message p,
.forbidden-message p {
  margin: 1rem 0;
  color: var(--text-color);
  font-size: 1.1rem;
}

.auth-link {
  color: var(--primary-color);
  text-decoration: none;
  font-weight: 600;
  padding: 0.5rem 1rem;
  border: 2px solid var(--primary-color);
  border-radius: 4px;
  display: inline-block;
  margin-top: 1rem;
  transition: all 0.3s ease;
}

.auth-link:hover {
  background-color: var(--primary-color);
  color: white;
  text-decoration: none;
}

.auth-link:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
}
</style> 