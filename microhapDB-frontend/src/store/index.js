// src/store/index.js
import { createStore } from 'vuex';

export default createStore({
  state: {
    isAuthenticated: false,
    isAdmin: false,
    username: null,
    selectedSequences: [],
    // New state properties for Query component
    query: {
      species: '',
      filters: {
        global: { value: null, matchMode: 'contains' },
        alleleid: { value: null, matchMode: 'contains' },
        info: { value: null, matchMode: 'contains' },
        associated_trait: { value: null, matchMode: 'contains' },
        allelesequence: { value: null, matchMode: 'contains' }
      },
      page: 1,
      size: 25,
      sequences: [],
      total: 0,
      associatedTraits: ['drought resistance', 'anthracnose race1 resistance']
    }
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
    },
    setSelectedSequences(state, sequences) {
      state.selectedSequences = sequences;
    },
    /**
     * Removes a selected allele from the state.
     * It filters out any sequence whose identifier matches the provided allele.
     */
    REMOVE_SELECTED_SEQUENCE(state, allele) {
      state.selectedSequences = state.selectedSequences.filter(seq => {
        // Compare using alleleid if available; fallback to id
        return (seq.alleleid || seq.id) !== (allele.alleleid || allele.id);
      });
    },
    // New mutations for Query state
    setQueryState(state, payload) {
      state.query = { ...state.query, ...payload };
    },
    resetQueryState(state) {
      state.query = {
        species: '',
        filters: {
          global: { value: null, matchMode: 'contains' },
          alleleid: { value: null, matchMode: 'contains' },
          info: { value: null, matchMode: 'contains' },
          associated_trait: { value: null, matchMode: 'contains' },
          allelesequence: { value: null, matchMode: 'contains' }
        },
        page: 1,
        size: 25,
        sequences: [],
        total: 0,
        associatedTraits: ['drought resistance', 'anthracnose race1 resistance']
      };
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
    },
    updateSelectedSequences({ commit }, sequences) {
      commit('setSelectedSequences', sequences);
    },
    // New actions for Query state
    updateQueryState({ commit }, payload) {
      commit('setQueryState', payload);
    },
    resetQueryState({ commit }) {
      commit('resetQueryState');
    }
  },
  getters: {
    isAuthenticated: state => state.isAuthenticated,
    isAdmin: state => state.isAdmin,
    username: state => state.username,
    getSelectedSequences: state => state.selectedSequences,
    // New getters for Query state
    getQueryState: state => state.query
  }
});
