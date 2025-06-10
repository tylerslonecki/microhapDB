// src/store/index.js
import { createStore } from 'vuex';
import auth from './modules/auth';

export default createStore({
  state: {
    selectedSequences: [],
    // State properties for Query component
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
    setSelectedSequences(state, sequences) {
      state.selectedSequences = sequences;
    },
    /**
     * Removes a selected allele from the state.
     * First tries to find exact object reference match, then falls back to ID comparison.
     * Uses findIndex to remove only the first matching sequence.
     */
    REMOVE_SELECTED_SEQUENCE(state, allele) {
      // First try to find exact object reference match
      let index = state.selectedSequences.findIndex(seq => seq === allele);
      
      // If not found by reference, try by ID
      if (index === -1) {
        const targetId = allele.alleleid || allele.id;
        index = state.selectedSequences.findIndex(seq => {
          return (seq.alleleid || seq.id) === targetId;
        });
      }
      
      if (index !== -1) {
        state.selectedSequences.splice(index, 1);
      }
    },
    /**
     * Ensures selectedSequences contains only unique items based on alleleid
     */
    ENSURE_UNIQUE_SEQUENCES(state) {
      const seen = new Set();
      state.selectedSequences = state.selectedSequences.filter(seq => {
        const id = seq.alleleid || seq.id;
        if (seen.has(id)) {
          return false;
        }
        seen.add(id);
        return true;
      });
    },
    // Mutations for Query state
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
    updateSelectedSequences({ commit }, sequences) {
      commit('setSelectedSequences', sequences);
    },
    ensureUniqueSequences({ commit }) {
      commit('ENSURE_UNIQUE_SEQUENCES');
    },
    // Actions for Query state
    updateQueryState({ commit }, payload) {
      commit('setQueryState', payload);
    },
    resetQueryState({ commit }) {
      commit('resetQueryState');
    }
  },
  getters: {
    getSelectedSequences: state => state.selectedSequences,
    // Getters for Query state
    getQueryState: state => state.query
  },
  modules: {
    auth
  }
});
