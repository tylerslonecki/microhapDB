<template>
  <div class="database-report">
    <h2 class="text-2xl font-bold mb-4">Database Version Report</h2>

    <!-- Controls -->
    <div class="p-card mb-4">
      <div class="p-card-body">
        <div class="grid">
          <div class="col-12 md:col-6">
            <span class="p-float-label">
              <Dropdown
                v-model="selectedSpecies"
                :options="speciesList"
                optionLabel="name"
                optionValue="value"
                placeholder="Select a Species"
                class="w-full"
                @change="fetchVersionStats"
              />
              <label for="species">Species</label>
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-content-center my-4">
      <div v-if="hasProgressSpinner">
        <ProgressSpinner />
      </div>
      <div v-else class="loading-text">Loading...</div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="error-message mb-4">
      {{ error }}
    </div>

    <!-- Data Visualizations -->
    <template v-else-if="versionData.length > 0">
      <!-- Total Alleles Line Chart -->
      <div class="p-card mb-4" v-if="hasChart">
        <div class="p-card-header">
          <h3 class="text-xl font-semibold mb-2">Total Alleles by Version</h3>
        </div>
        <div class="p-card-body">
          <Chart type="line" :data="totalAllelesChartData" :options="chartOptions" class="h-20rem" />
        </div>
      </div>

      <!-- New Alleles Bar Chart -->
      <div class="p-card mb-4" v-if="hasChart">
        <div class="p-card-header">
          <h3 class="text-xl font-semibold mb-2">New Alleles by Version</h3>
        </div>
        <div class="p-card-body">
          <Chart type="bar" :data="newAllelesChartData" :options="chartOptions" class="h-20rem" />
        </div>
      </div>

      <!-- Version Details Table -->
      <div class="p-card">
        <div class="p-card-header">
          <h3 class="text-xl font-semibold mb-2">Version Details</h3>
        </div>
        <div class="p-card-body">
          <DataTable
            :value="versionData"
            :paginator="true"
            :rows="10"
            :rowsPerPageOptions="[5, 10, 20]"
            stripedRows
            class="p-datatable-sm"
          >
            <Column field="version" header="Version" :sortable="true">
              <template #body="slotProps">
                v{{ slotProps.data.version }}
              </template>
            </Column>
            <Column field="created_at" header="Date" :sortable="true">
              <template #body="slotProps">
                {{ formatDate(slotProps.data.created_at) }}
              </template>
            </Column>
            <Column field="program_name" header="Program" :sortable="true" />
            <Column field="total_alleles" header="Total Alleles" :sortable="true">
              <template #body="slotProps">
                {{ formatNumber(slotProps.data.total_alleles) }}
              </template>
            </Column>
            <Column field="new_alleles" header="New Alleles" :sortable="true">
              <template #body="slotProps">
                {{ formatNumber(slotProps.data.new_alleles) }}
              </template>
            </Column>
            <Column field="description" header="Description">
              <template #body="slotProps">
                {{ slotProps.data.description || 'N/A' }}
              </template>
            </Column>
          </DataTable>
        </div>
      </div>
    </template>

    <!-- Empty State -->
    <div v-else-if="selectedSpecies" class="p-card">
      <div class="p-card-body">
        <p>No data available for the selected species.</p>
      </div>
    </div>

    <!-- Initial State -->
    <div v-else class="p-card">
      <div class="p-card-body">
        <p>Please select a species to view data.</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import axiosInstance from '../axiosConfig';

// Try importing PrimeVue components
let Dropdown, ProgressSpinner, Chart, DataTable, Column;
let hasChart = false;
let hasProgressSpinner = false;

try {
  Dropdown = require('primevue/dropdown').default;
  DataTable = require('primevue/datatable').default;
  Column = require('primevue/column').default;
} catch (e) {
  console.error('Error loading base PrimeVue components:', e);
}

try {
  Chart = require('primevue/chart').default;
  hasChart = true;
} catch (e) {
  console.error('Chart component not available:', e);
  hasChart = false;
}

try {
  ProgressSpinner = require('primevue/progressspinner').default;
  hasProgressSpinner = true;
} catch (e) {
  console.error('ProgressSpinner component not available:', e);
  hasProgressSpinner = false;
}

export default {
  name: 'DatabaseReport',
  components: {
    Dropdown,
    ProgressSpinner,
    Chart,
    DataTable,
    Column
  },
  setup() {
    // State
    const loading = ref(false);
    const error = ref(null);
    const programsError = ref(null);
    const selectedSpecies = ref('');
    const selectedProgramId = ref('');
    const versionData = ref([]);
    const programs = ref([]);
    
    // Hardcoded species list
    const speciesList = ref([
      { name: 'Sweet Potato', value: 'sweetpotato' },
      { name: 'Blueberry', value: 'blueberry' },
      { name: 'Alfalfa', value: 'alfalfa' },
      { name: 'Cranberry', value: 'cranberry' }
    ]);

    // Chart data and options
    const totalAllelesChartData = computed(() => {
      return {
        labels: versionData.value.map(v => `v${v.version}`),
        datasets: [
          {
            label: 'Total Alleles',
            data: versionData.value.map(v => v.total_alleles),
            fill: false,
            borderColor: '#8884d8',
            tension: 0.4
          }
        ]
      };
    });

    const newAllelesChartData = computed(() => {
      return {
        labels: versionData.value.map(v => `v${v.version}`),
        datasets: [
          {
            label: 'New Alleles Added',
            data: versionData.value.map(v => v.new_alleles),
            backgroundColor: '#82ca9d',
          }
        ]
      };
    });

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top'
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    };

    // Fetch programs on component mount
    onMounted(async () => {
      try {
        const response = await axiosInstance.get('/posts/programs/');
        programs.value = response.data;
      } catch (err) {
        console.error('Error fetching programs:', err);
        programsError.value = 'Could not load programs. You can still select a species.';
        programs.value = [];
      }
    });

    // Fetch version statistics
    const fetchVersionStats = async () => {
      if (!selectedSpecies.value) return;
      
      loading.value = true;
      error.value = null;
      
      try {
        const url = `/posts/allele-count/${selectedSpecies.value}${selectedProgramId.value ? `?program_id=${selectedProgramId.value}` : ''}`;
        const response = await axiosInstance.get(url);
        versionData.value = response.data;
      } catch (err) {
        console.error('Error fetching version statistics:', err);
        error.value = 'Failed to load version statistics. Please try again later.';
        versionData.value = [];
      } finally {
        loading.value = false;
      }
    };

    // Helper functions
    const formatDate = (dateString) => {
      if (!dateString) return 'N/A';
      return new Date(dateString).toLocaleDateString();
    };

    const formatNumber = (number) => {
      return number.toLocaleString();
    };

    return {
      // State
      loading,
      error,
      programsError,
      selectedSpecies,
      selectedProgramId,
      versionData,
      programs,
      speciesList,
      
      // Feature flags
      hasChart,
      hasProgressSpinner,
      
      // Methods
      fetchVersionStats,
      formatDate,
      formatNumber,
      
      // Chart data
      totalAllelesChartData,
      newAllelesChartData,
      chartOptions
    };
  }
};
</script>

<style scoped>
.h-20rem {
  height: 20rem;
}

.error-message {
  background-color: #ffebee;
  color: #d32f2f;
  border-left: 4px solid #d32f2f;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
}

.loading-text {
  display: flex;
  justify-content: center;
  font-size: 1.2rem;
  color: #666;
  padding: 2rem 0;
}
</style>