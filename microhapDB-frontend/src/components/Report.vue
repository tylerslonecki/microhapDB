<template>
  <div class="report-container">
    <div class="species-filter">
      <select v-model="species" class="species-dropdown" @change="fetchReport">
        <option disabled value="">Select Species</option>
        <option value="sweetpotato">Sweetpotato</option>
        <option value="blueberry">Blueberry</option>
        <option value="alfalfa">Alfalfa</option>
        <option value="cranberry">Cranberry</option>
      </select>
    </div>
    <h2 class="page-title">{{ species ? `${species.charAt(0).toUpperCase() + species.slice(1)} Unique Microhaplotypes` : 'Sequences' }}</h2>
    <div v-if="loading" class="loading-message">Loading report...</div>
    <div v-else-if="report">
      <div class="report-section">
        <h3>Total Unique Microhaplotypes</h3>
        <p>{{ report.total_unique_sequences }}</p>
      </div>
      <div class="report-section">
        <h3>New Microhaplotypes last batch</h3>
        <p>{{ report.new_sequences_this_batch }}</p>
      </div>
      <div class="report-section">
        <h3>Batch History</h3>
        <table class="batch-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Date</th>
              <th>New Microhaplotypes</th>
              <th>Cumulative Microhaplotypes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="batch in report.batch_history" :key="batch.batch_id">
              <td>{{ batch.batch_id }}</td>
              <td>{{ batch.date }}</td>
              <td>{{ batch.new_sequences }}</td>
              <td>{{ batch.cumulative_sum }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="report-section">
        <h3></h3>
        <img :src="'data:image/png;base64,' + report.line_chart" alt="Line Chart" />
      </div>
    </div>
    <p v-else>No report available.</p>
  </div>
</template>

<script>
import axiosInstance from '../axiosConfig'; // Import your axios configuration

export default {
  name: 'DatabaseReport',
  data() {
    return {
      report: null,
      loading: true, // Add loading state
      species: '',
    };
  },
  watch: {
    species(newSpecies) {
      if (newSpecies) {
        this.fetchReport();
      }
    }
  },
  methods: {
    async fetchReport() {
      this.loading = true; // Set loading state to true when fetching starts
      try {
        const response = await axiosInstance.get('/posts/report_data');
        this.report = response.data;
      } catch (error) {
        console.error("There was an error fetching the report: ", error);
        this.report = null; // Clear the report in case of an error
      } finally {
        this.loading = false; // Set loading state to false when fetching ends
      }
    }
  },
  mounted() {
    this.fetchReport(); // Fetch the report when the component is mounted
  }
}
</script>

<style scoped>
.report-container {
  max-width: 1200px;
  margin: auto;
  padding: 20px;
}

h2 {
  color: #00796b; /* Aesthetic green color */
  text-align: center;
  margin-bottom: 30px;
}

.species-dropdown {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  display: block;
  margin: 0 auto 20px auto; /* Center the dropdown */
}


.loading-message {
  text-align: center;
  color: #00796b;
  margin-top: 20px;
}

.report-section {
  margin-bottom: 20px;
}

.batch-table {
  width: 100%;
  border-collapse: collapse;
}

.batch-table th, .batch-table td {
  padding: 12px 15px;
  border: 1px solid #ddd;
  text-align: left;
}

.batch-table th {
  background-color: #00796b;
  color: white;
}

.batch-table tr:nth-child(even) {
  background-color: #f2f2f2;
}

.batch-table tr:hover {
  background-color: #e1f7f5;
}
</style>