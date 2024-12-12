import { createStore } from 'vuex';

export default createStore({
  state: {
    isAuthenticated: false,
    isAdmin: false,
    username: null
  },
  mutations: {
    setAuthState(state, { isAuthenticated, isAdmin, username }) {
      state.isAuthenticated = isAuthenticated;
      state.isAdmin = isAdmin;
      state.username = username;
    },
    clearAuthState(state) {
      state.isAuthenticated = false;
      state.isAdmin = false;
      state.username = null;
    }
  },
  actions: {
    async checkAuthStatus({ commit }) {
      try {
        const response = await fetch('https://myfastapiapp.loca.lt/auth/status', {
          credentials: 'include' // Ensure cookies are sent
        });
        if (!response.ok) {
          throw new Error('Failed to fetch authentication status');
        }
        const authStatus = await response.json();
        commit('setAuthState', {
          isAuthenticated: authStatus.is_authenticated,
          isAdmin: authStatus.is_admin,
          username: authStatus.username
        });
      } catch (error) {
        console.error('Error checking authentication status:', error);
        commit('clearAuthState');
      }
    },
    async logout({ commit }) {
      try {
        const response = await fetch('https://myfastapiapp.loca.lt/auth/logout', {
          method: 'POST',
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
          },
        });
        if (!response.ok) {
          throw new Error('Logout failed');
        }
        await response.json();
        commit('clearAuthState');
      } catch (error) {
        console.error('Error during logout:', error);
      }
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    isAdmin: state => state.isAdmin,
    username: state => state.username
  }
});
