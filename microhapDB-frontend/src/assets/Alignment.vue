<!-- <template>
    <div class="alignment-container">
      <h2>Sequence Alignment</h2>
      <div class="filter-form">
        <select v-model="species" class="species-dropdown" @change="resetFilters">
          <option disabled value="">Select Species</option>
          <option v-for="speciesOption in speciesOptions" :key="speciesOption.value" :value="speciesOption.value">
            {{ speciesOption.label }}
          </option>
        </select>
        <select v-model="filterField" class="filter-dropdown" @change="clearFilter">
          <option value="">None</option>
          <option value="hapid">Hap ID</option>
          <option value="alleleid">Allele ID</option>
          <option value="allelesequence">Allele Sequence</option>
        </select>
        <input v-model="filter" placeholder="Enter filter value" class="filter-input"/>
        <button @click="fetchSequences" class="filter-button">Search</button>
      </div>
      <div v-if="sequences.length" class="alignment-viewer">
        <vue-alignment :sequences="sequences" />
      </div>
      <div v-else class="no-data">No data available for alignment.</div>
    </div>
  </template>
  
  <script>
  import axiosInstance from '../axiosConfig'; // Import your axios configuration
  import VueAlignment from 'vue-alignment';
  import { SUPPORTED_SPECIES } from '../utils/speciesConfig';
  
  export default {
    components: {
      VueAlignment
    },
    data() {
      return {
        sequences: [],
        filter: '',
        filterField: '',
        species: '',
        speciesOptions: SUPPORTED_SPECIES,
      };
    },
    methods: {
      async fetchSequences() {
        if (!this.species) {
          this.sequences = [];
          return;
        }
        try {
          const response = await axiosInstance.post('/posts/sequences/alignment', {
            filter: this.filter,
            filter_field: this.filterField,
            species: this.species
          });
          this.sequences = response.data;
        } catch (error) {
          console.error("Error fetching sequences for alignment:", error);
        }
      },
      resetFilters() {
        this.filterField = '';
        this.filter = '';
        this.fetchSequences();
      },
      clearFilter() {
        this.filter = '';
      }
    }
  }
  </script>
  
  <style scoped>
  .alignment-container {
    padding: 10px;
    max-width: calc(100% - 240px); /* Adjust width considering sidebar width */
    margin-left: 10px; /* Align with sidebar */
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  
  .filter-form {
    display: flex;
    align-items: center;
    margin-bottom: 20px;
    margin-left: 10px; /* Adjusted for alignment */
  }
  
  .filter-input, .filter-dropdown, .species-dropdown {
    padding: 10px;
    font-size: 16px;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-right: 10px;
  }
  
  .filter-button {
    padding: 10px 10px;
    font-size: 16px;
    background-color: #00796b;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }
  
  .filter-button:hover {
    background-color: #005f56;
  }
  
  .alignment-viewer {
    margin-top: 20px;
  }
  
  .no-data {
    margin-top: 20px;
    text-align: center;
  }
  </style> -->
<template>
  <div class="alignment-placeholder">
    <p>Alignment component is currently disabled</p>
  </div>
</template>

<script>
export default {
  name: 'Alignment'
}
</script>

<style scoped>
.alignment-placeholder {
  padding: 20px;
  text-align: center;
  color: #666;
}
</style>