<template>
  <div class="sequences-container">
    <div class="species-filter">
      <select v-model="species" class="species-dropdown" @change="resetFilters">
        <option disabled value="">Select Species</option>
        <option value="sweetpotato">Sweetpotato</option>
        <option value="blueberry">Blueberry</option>
        <option value="alfalfa">Alfalfa</option>
        <option value="cranberry">Cranberry</option>
      </select>
    </div>
    <h2 class="page-title">{{ species ? `${species.charAt(0).toUpperCase() + species.slice(1)} Unique Microhaplotypes` : 'Unique Microhaplotypes' }}</h2>
    <div class="filter-form">
      <select v-model="filterField" class="filter-dropdown" @change="clearFilter">
        <option value="">None</option>
        <option value="hapid">Hap ID</option>
        <option value="alleleid">Allele ID</option>
        <option value="allelesequence">Allele Sequence</option>
      </select>
      <input v-model="filter" placeholder="Enter filter value" class="filter-input"/>
      <button @click="searchSequences" class="filter-button">Search</button>
    </div>
    <div v-if="species" class="pagination">
      <button @click="prevPage" :disabled="page === 1" class="pagination-button">Previous</button>
      <span>Page {{ page }} of {{ totalPages }} (Total sequences: {{ total }})</span>
      <button @click="nextPage" :disabled="page * size >= total" class="pagination-button">Next</button>
    </div>
    <table class="sequences-table">
      <thead>
        <tr>
          <th>Hap ID</th>
          <th>Allele ID</th>
          <th>Allele Sequence</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="!sequences.length">
          <td colspan="3">No data available</td>
        </tr>
        <tr v-for="sequence in sequences" :key="sequence.id">
          <td>{{ sequence.hapid }}</td>
          <td>{{ sequence.alleleid }}</td>
          <td>{{ sequence.allelesequence }}</td>
        </tr>
      </tbody>
    </table>
    <div v-if="species" class="pagination">
      <button @click="prevPage" :disabled="page === 1" class="pagination-button">Previous</button>
      <span>Page {{ page }} of {{ totalPages }} (Total sequences: {{ total }})</span>
      <button @click="nextPage" :disabled="page * size >= total" class="pagination-button">Next</button>
    </div>
  </div>
</template>
  
<script>
import axiosInstance from '../axiosConfig'; // Import your axios configuration

export default {
  data() {
    return {
      sequences: [],
      total: 0,
      page: 1,
      size: 25,
      filter: '',
      filterField: '',
      species: '',
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.total / this.size);
    }
  },
  methods: {
    async fetchSequences() {
      if (!this.species) {
        this.sequences = [];
        this.total = 0;
        return;
      }
      try {
        const response = await axiosInstance.post('/posts/sequences', {
          page: this.page,
          size: this.size,
          filter: this.filter,
          filter_field: this.filterField,
          species: this.species
        });
        this.sequences = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        console.error("Error fetching sequences:", error);
      }
    },
    nextPage() {
      if (this.page * this.size < this.total) {
        this.page++;
        this.fetchSequences();
      }
    },
    prevPage() {
      if (this.page > 1) {
        this.page--;
        this.fetchSequences();
      }
    },
    resetFilters() {
      this.filterField = '';
      this.filter = '';
      this.page = 1;
      this.fetchSequences();
    },
    clearFilter() {
      this.filter = '';
      this.page = 1;
    },
    searchSequences() {
      this.page = 1;
      this.fetchSequences();
    }
  },
  mounted() {
    this.fetchSequences();
  }
}
</script>
  
<style scoped>
.sequences-container {
  padding: 10px;
  max-width: calc(100% - 240px); /* Adjust width considering sidebar width */
  margin-left: 10px; /* Align with sidebar */
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.species-filter {
  margin-bottom: 10px;
  margin-left: 10px;
}

.page-title {
  margin-left: 10px; /* Adjust margin to align with dropdown */
  text-align: left;
}

.species-dropdown {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

.filter-form {
  display: flex;
  align-items: center;
  margin-bottom: 20px;
  margin-left: 10px; /* Adjusted for alignment */
}

.filter-input, .filter-dropdown {
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

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 10px 0;
  margin-left: 10px; /* Adjusted for alignment */
}

.pagination-button {
  padding: 10px 10px;
  font-size: 16px;
  background-color: #00796b;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  margin: 0 10px;
  transition: background-color 0.3s ease;
}

.pagination-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.pagination-button:hover:enabled {
  background-color: #005f56;
}

.sequences-table {
  width: calc(100% - 40px); /* Adjust width considering padding */
  margin-left: 10px; /* Adjusted for alignment */
  border-collapse: collapse;
  margin-top: 20px;
}

.sequences-table th, .sequences-table td {
  padding: 12px 15px;
  border: 1px solid #ddd;
  text-align: left;
}

.sequences-table th {
  background-color: #00796b;
  color: white;
}

.sequences-table tr:nth-child(even) {
  background-color: #f2f2f2;
}

.sequences-table tr:hover {
  background-color: #e1f7f5;
}
</style>