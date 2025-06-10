import axios from 'axios';

const state = {
  isAuthenticated: false,
  user: null,
  role: null,
  isAdmin: false,
  accessibleUserIds: null,
  isLoading: false
};

const mutations = {
  SET_AUTH_STATUS(state, status) {
    state.isAuthenticated = status;
  },
  SET_USER(state, user) {
    state.user = user;
  },
  SET_ROLE(state, role) {
    state.role = role;
    state.isAdmin = role === 'admin';
  },
  SET_ACCESSIBLE_USER_IDS(state, ids) {
    state.accessibleUserIds = ids;
  },
  SET_LOADING(state, loading) {
    state.isLoading = loading;
  },
  CLEAR_AUTH(state) {
    state.isAuthenticated = false;
    state.user = null;
    state.role = null;
    state.isAdmin = false;
    state.accessibleUserIds = null;
    state.isLoading = false;
  }
};

const actions = {
  async checkAuthStatus({ commit }) {
    commit('SET_LOADING', true);
    
    try {
      console.log('Checking auth status...');
      
      // Get token from localStorage
      const token = localStorage.getItem('access_token');
      console.log('Token from localStorage:', token ? `${token.substring(0, 10)}...` : 'none');
      
      // If we have a token, set it in the headers
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      } else {
        // If no token, clear auth state
        commit('CLEAR_AUTH');
        return { is_authenticated: false };
      }
      
      try {
        const response = await axios.get('/auth/status');
        console.log('Auth status response:', response.data);
        
        if (response.data.is_authenticated) {
          commit('SET_AUTH_STATUS', true);
          commit('SET_USER', {
            username: response.data.username,
            isAdmin: response.data.is_admin
          });
          commit('SET_ROLE', response.data.role);
          
          console.log('Authentication successful');
          return response.data;
        } else {
          console.log('Auth failed with message:', response.data.message);
          commit('CLEAR_AUTH');
          localStorage.removeItem('access_token');
          return response.data;
        }
        
      } catch (error) {
        console.error('Error checking auth status:', error);
        
        // If it's a 401 with token expiration, the axios interceptor will handle refresh
        if (error.response && 
            error.response.status === 401 && 
            error.response.data && 
            (error.response.data.detail === 'Token has expired' || 
             error.response.data.detail === 'Signature has expired')) {
          console.log('Token expired, refresh will be handled by axios interceptor');
          // Don't clear auth state immediately, let the interceptor try to refresh
          throw error;
        } else {
          // For other errors, clear auth state
          console.log('Clearing auth state due to error:', error.response?.data?.detail || error.message);
          commit('CLEAR_AUTH');
          localStorage.removeItem('access_token');
          throw error;
        }
      }
    } catch (error) {
      console.error('Error in checkAuthStatus:', error);
      throw error;
    } finally {
      commit('SET_LOADING', false);
    }
  },

  async refreshToken({ commit, dispatch }) {
    try {
      console.log('Attempting to refresh token...');
      
      const response = await axios.post('/auth/refresh');
      
      if (response.data && response.data.access_token) {
        console.log('Token refreshed successfully');
        
        // Store new token
        localStorage.setItem('access_token', response.data.access_token);
        
        // Update axios headers
        axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        
        // Re-check auth status to update user info
        await dispatch('checkAuthStatus');
        
        return response.data.access_token;
      } else {
        throw new Error('No access token in refresh response');
      }
    } catch (error) {
      console.error('Token refresh failed:', error);
      
      // Clear auth state on refresh failure
      commit('CLEAR_AUTH');
      localStorage.removeItem('access_token');
      
      throw error;
    }
  },

  async logout({ commit }) {
    try {
      await axios.post('/auth/logout');
      console.log('Logout request successful');
    } catch (error) {
      console.error('Logout request error:', error);
      // Continue with local cleanup even if server request fails
    } finally {
      // Always clear local state
      localStorage.removeItem('access_token');
      delete axios.defaults.headers.common['Authorization'];
      commit('CLEAR_AUTH');
      console.log('Local auth state cleared');
    }
  },

  async getAccessibleData({ commit }) {
    try {
      const response = await axios.get('/posts/accessible-data');
      commit('SET_ACCESSIBLE_USER_IDS', response.data.accessible_user_ids);
      return response.data;
    } catch (error) {
      console.error('Error getting accessible data:', error);
      
      // Don't throw the error, just return empty data
      commit('SET_ACCESSIBLE_USER_IDS', []);
      return { accessible_user_ids: [] };
    }
  },

  // Action to handle token from URL (e.g., after ORCID callback)
  async handleTokenFromUrl({ dispatch }, token) {
    if (token) {
      console.log('Handling token from URL');
      
      // Store token
      localStorage.setItem('access_token', token);
      
      // Set in axios headers
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      // Check auth status to get user details
      try {
        await dispatch('checkAuthStatus');
        return true;
      } catch (error) {
        console.error('Error validating token from URL:', error);
        return false;
      }
    }
    return false;
  }
};

const getters = {
  isAuthenticated: state => state.isAuthenticated,
  currentUser: state => state.user,
  userRole: state => state.role,
  isAdmin: state => state.isAdmin,
  isLoading: state => state.isLoading,
  accessibleUserIds: state => state.accessibleUserIds,
  hasAccess: (state) => (userId) => {
    if (state.isAdmin || state.accessibleUserIds === null) return true;
    return state.accessibleUserIds.includes(userId);
  },
  canAccessPrivateData: state => state.role === 'admin' || state.role === 'private_user',
  canAccessCollaboratorData: state => ['admin', 'private_user', 'collaborator'].includes(state.role)
};

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
}; 