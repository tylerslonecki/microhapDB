<template>
  <div class="histogram-container">
    <!-- Dropdown selectors -->
    <div class="controls">
      <div class="control-item">
        <label for="speciesDropdown" class="control-label">Species:</label>
        <Dropdown
          id="speciesDropdown"
          v-model="selectedSpecies"
          :options="speciesOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="-- Select Species --"
          @change="onSpeciesChange"
        />
      </div>
      <div class="control-item">
        <label for="chromosomeDropdown" class="control-label">Chromosome:</label>
        <Dropdown
          id="chromosomeDropdown"
          v-model="selectedChromosome"
          :options="chromosomes"
          optionLabel="label"
          optionValue="value"
          placeholder="-- Select Chromosome --"
          :disabled="!selectedSpecies || chromosomesLoading"
        />
      </div>
      <div class="control-item">
        <label for="programDropdown" class="control-label">Program:</label>
        <Dropdown
          id="programDropdown"
          v-model="selectedProgram"
          :options="programs"
          optionLabel="name"
          optionValue="id"
          placeholder="-- Select Program --"
          :disabled="!selectedSpecies || programsLoading"
        />
      </div>
      <Button
        label="Load Data"
        :disabled="!selectedChromosome || !selectedSpecies"
        @click="fetchData"
      />
    </div>

    <!-- Loading indicators -->
    <div v-if="programsLoading" class="loading-indicator">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <span>Loading programs...</span>
    </div>
    <div v-if="chromosomesLoading" class="loading-indicator">
      <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
      <span>Loading chromosomes...</span>
    </div>

    <!-- Canvas for the histogram -->
    <div class="chart-wrapper">
      <div v-if="loading" class="loading-overlay">
        <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
        <span>Loading data...</span>
      </div>
      <canvas id="histogram"></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { Chart, registerables } from 'chart.js';
import axiosInstance from '../axiosConfig';
import { SUPPORTED_SPECIES } from '../utils/speciesConfig';

// Import PrimeVue components
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';

// Register all Chart.js components
Chart.register(...registerables);

const speciesOptions = SUPPORTED_SPECIES;

// Reactive variables for dropdown selections and histogram data
const selectedSpecies = ref('');
const selectedProgram = ref(null);
const selectedChromosome = ref('');
const chromosomes = ref([]);
const programs = ref([]);
const histogramData = ref([]);
const loading = ref(false);
const chromosomesLoading = ref(false);
const programsLoading = ref(false);

// Chart instance reference
let chartInstance = null;

async function onSpeciesChange() {
  // Reset the chromosome and program selections when species changes
  selectedChromosome.value = '';
  selectedProgram.value = null;
  chromosomes.value = [];
  programs.value = [];
  
  // Reset the histogram data and update chart to show empty state
  histogramData.value = [];
  updateChart();
  
  if (!selectedSpecies.value) return;
  
  // Load programs for this species
  await loadProgramsForSpecies();
  
  // Load chromosomes for this species
  await loadChromosomesForSpecies();
}

async function loadProgramsForSpecies() {
  if (!selectedSpecies.value) return;
  
  programsLoading.value = true;
  try {
    // Call the API endpoint to get programs for the selected species
    const response = await axiosInstance.get(`/posts/programs/by_species/${encodeURIComponent(selectedSpecies.value)}`);
    programs.value = response.data.programs;
  } catch (error) {
    console.error("Error fetching programs:", error);
    alert("Error loading programs. Please try again later.");
  } finally {
    programsLoading.value = false;
  }
}

async function loadChromosomesForSpecies() {
  if (!selectedSpecies.value) return;
  
  chromosomesLoading.value = true;
  try {
    // Call the API endpoint to get chromosomes for the selected species
    const response = await axiosInstance.get(`/posts/visualizations/chromosomes?species=${encodeURIComponent(selectedSpecies.value)}`);
    chromosomes.value = response.data.chromosomes.map(chr => ({ label: chr, value: chr }));
  } catch (error) {
    console.error("Error fetching chromosomes:", error);
    alert("Error loading chromosomes. Please try again later.");
  } finally {
    chromosomesLoading.value = false;
  }
}

async function fetchData() {
  // Check that required selections have been made
  if (!selectedChromosome.value || !selectedSpecies.value) {
    alert("Please select both a chromosome and a species.");
    return;
  }

  loading.value = true;
  try {
    // Construct the query URL with all parameters
    let query = `?species=${encodeURIComponent(selectedSpecies.value)}&chromosome=${encodeURIComponent(selectedChromosome.value)}`;
    
    // Add program parameter if selected
    if (selectedProgram.value) {
      query += `&program_id=${encodeURIComponent(selectedProgram.value)}`;
    }
    
    const response = await axiosInstance.get(`/posts/visualizations/histogram${query}`);

    // Since Axios automatically parses JSON, we access the data directly
    const result = response.data;
    histogramData.value = result.data || [];

    // Update the chart with the new data
    updateChart();
  } catch (error) {
    console.error("Error fetching histogram data:", error);
    alert("Error fetching data. Please try again later.");
  } finally {
    loading.value = false;
  }
}

function updateChart() {
  const labels = histogramData.value.map((item) => item.locus);
  const counts = histogramData.value.map((item) => item.allele_count);

  if (chartInstance) {
    chartInstance.data.labels = labels;
    chartInstance.data.datasets[0].data = counts;
    chartInstance.update();
  } else {
    createChart(labels, counts);
  }
}

function createChart(labels = [], data = []) {
  const ctx = document.getElementById('histogram').getContext('2d');
  chartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Allele Count',
        data: data,
        backgroundColor: 'rgba(75, 192, 192, 0.4)',
        borderColor: 'rgba(75, 192, 192, 1)',
        borderWidth: 1,
        // Adding a slight shadow effect for enhanced visual appeal
        hoverBackgroundColor: 'rgba(75, 192, 192, 0.6)'
      }]
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Allele Count',
            font: {
              size: 16, // Bigger font size for the title
              weight: 'bold' // Bold font weight
            }
          },
          ticks: {
            font: {
              size: 12
            }
          },
          grid: {
            color: 'rgba(0, 0, 0, 0.1)' // Lighter gridlines
          }
        },
        x: {
          title: {
            display: true,
            text: 'Locus',
            font: {
              size: 16,
              weight: 'bold'
            }
          },
          ticks: {
            font: {
              size: 12
            }
          },
          grid: {
            display: false
          }
        }
      },
      plugins: {
        legend: {
          display: false // Hiding legend as the chart has a single dataset
        },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.7)',
          titleFont: {
            size: 14,
            weight: 'bold'
          },
          bodyFont: {
            size: 12
          },
callbacks: {
            title: function(tooltipItems) {
              return `Locus: ${tooltipItems[0].label}`;
            },
            label: function(context) {
              return `Allele Count: ${context.raw}`;
            },
            afterLabel: function() {
              // No parameter needed since we don't use it
              const programInfo = selectedProgram.value 
                ? `Program: ${programs.value.find(p => p.id === selectedProgram.value)?.name || 'Unknown'}`
                : 'All Programs';
              
              return [
                `Species: ${selectedSpecies.value}`,
                `Chromosome: ${selectedChromosome.value}`,
                programInfo
              ];
            }
          }
        }
      }
    }
  });
}

onMounted(() => {
  createChart(); // Creates an empty chart (no labels, no data)
});
</script>

<style scoped>
.histogram-container {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1rem;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.controls {
  margin-bottom: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: flex-end;
  justify-content: space-between;
}

.control-item {
  display: flex;
  flex-direction: column;
  min-width: 180px;
}

.control-label {
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.chart-wrapper {
  position: relative;
  height: 400px;
}

.loading-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin: 0.5rem 0;
  color: #666;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  z-index: 1;
}
</style>