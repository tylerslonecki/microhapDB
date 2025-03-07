<template>
  <div class="comparative-container">
    <Panel header="Comparative Allele Analysis" class="mb-4">
      <!-- Selection Controls -->
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
            optionLabel="label"
            optionValue="value"
            placeholder="-- Select Program --"
            :disabled="!selectedSpecies || programsLoading"
          />
        </div>
        <div class="control-item">
          <label for="visualizationDropdown" class="control-label">Visualization:</label>
          <Dropdown
            id="visualizationDropdown"
            v-model="selectedVisualization"
            :options="visualizationOptions"
            optionLabel="label"
            optionValue="value"
            placeholder="-- Select Visualization --"
          />
        </div>
        <Button
          label="Load Data"
          :disabled="!selectedChromosome || !selectedSpecies || !selectedProgram"
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

      <!-- Filter Controls -->
      <div class="filter-controls mt-3" v-if="comparativeData.length > 0">
        <div class="filter-item">
          <label for="minDifferenceSlider" class="filter-label">Minimum Difference:</label>
          <Slider
            id="minDifferenceSlider"
            v-model="minDifference"
            :min="0"
            :max="maxDifference"
            :step="1"
            class="w-12rem"
          />
          <span class="ml-2">{{ minDifference }}</span>
        </div>
        <div class="filter-item">
          <Button
            label="Export CSV"
            icon="pi pi-download"
            @click="exportCSV"
            class="p-button-outlined"
          />
        </div>
      </div>

      <!-- Chart wrapper -->
      <div class="chart-wrapper">
        <div v-if="loading" class="loading-overlay">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <span>Loading data...</span>
        </div>
        
        <div v-if="!loading" class="chart-container">
          <!-- Single canvas that will be reused for all chart types -->
          <canvas ref="chartCanvas"></canvas>
        </div>
      </div>

      <!-- Data Table -->
      <div class="mt-4" v-if="comparativeData.length > 0 && !loading">
        <h3>Loci with Missing Alleles</h3>
        <DataTable 
          :value="filteredData" 
          :paginator="true" 
          :rows="10"
          :rowsPerPageOptions="[5, 10, 25, 50]"
          stripedRows
          class="p-datatable-sm"
          sortField="difference"
          :sortOrder="-1"
        >
          <Column field="locus" header="Locus" sortable></Column>
          <Column field="total_count" header="Total Alleles" sortable></Column>
          <Column field="program_count" header="Program Alleles" sortable></Column>
          <Column field="difference" header="Difference" sortable></Column>
          <Column field="missing_count" header="Missing Count" sortable></Column>
          <Column header="Actions">
            <template #body="slotProps">
              <Button 
                icon="pi pi-search" 
                class="p-button-rounded p-button-text p-button-sm" 
                @click="showMissingAlleles(slotProps.data)"
                v-tooltip="'View Missing Alleles'"
              />
            </template>
          </Column>
        </DataTable>
      </div>
    </Panel>

    <!-- Missing Alleles Modal -->
    <Dialog 
      v-model:visible="missingAllelesDialogVisible" 
      :header="`Missing Alleles for Locus: ${selectedLocus}`"
      :style="{ width: '50vw' }"
      :modal="true"
    >
      <div class="missing-alleles-container">
        <DataTable 
          :value="selectedMissingAlleles" 
          :paginator="true" 
          :rows="10"
          class="p-datatable-sm"
        >
          <Column field="allele" header="Allele ID"></Column>
        </DataTable>
      </div>
      <template #footer>
        <Button label="Close" icon="pi pi-times" @click="missingAllelesDialogVisible = false" class="p-button-text" />
        <Button label="Export List" icon="pi pi-download" @click="exportMissingAlleles" />
      </template>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, onUnmounted, nextTick } from 'vue';
import { Chart, registerables } from 'chart.js';
import axiosInstance from '../axiosConfig';

// Import PrimeVue components
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';
import Panel from 'primevue/panel';
import Slider from 'primevue/slider';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Tooltip from 'primevue/tooltip';

// Register directives
const vTooltip = Tooltip;

// Register all Chart.js components
Chart.register(...registerables);

// Reactive species options with consistent structure
const speciesOptions = ref([
  { label: 'Alfalfa', value: 'alfalfa' },
  { label: 'Sweetpotato', value: 'sweetpotato' },
  { label: 'Cranberry', value: 'cranberry' }
]);

// Visualization options
const visualizationOptions = ref([
  { label: 'Comparative Bar Chart', value: 'bar' },
  { label: 'Difference Chart', value: 'difference' },
  { label: 'Heat Map', value: 'heatmap' }
]);

// Reactive variables
const selectedSpecies = ref('');
const selectedProgram = ref(null);
const selectedChromosome = ref('');
const selectedVisualization = ref('bar');
const chromosomes = ref([]);
const programs = ref([]);
const comparativeData = ref([]);
const loading = ref(false);
const chromosomesLoading = ref(false);
const programsLoading = ref(false);
const minDifference = ref(0);
const maxDifference = ref(0);
const missingAllelesDialogVisible = ref(false);
const selectedLocus = ref('');
const selectedMissingAlleles = ref([]);
const chartCanvas = ref(null);

// Chart instance (single instance for all chart types)
let chartInstance = null;

// Computed properties
const filteredData = computed(() => {
  return comparativeData.value.filter(item => item.difference >= minDifference.value);
});

// Watch for visualization changes to update charts
watch(selectedVisualization, () => {
  if (comparativeData.value.length > 0) {
    updateCharts();
  }
});

// Watch for minDifference changes to update charts
watch(minDifference, () => {
  if (comparativeData.value.length > 0) {
    updateCharts();
  }
});

// Watch for filteredData to update charts when filter changes
watch(filteredData, () => {
  if (comparativeData.value.length > 0) {
    updateCharts();
  }
}, { deep: true });

// Watch for comparativeData changes to ensure chart gets rendered when data changes
watch(comparativeData, (newData) => {
  if (newData.length > 0) {
    // Use nextTick to ensure DOM is updated before trying to render
    nextTick(() => {
      updateCharts();
    });
  }
}, { deep: true });

async function onSpeciesChange() {
  // Reset selections when species changes
  selectedChromosome.value = '';
  selectedProgram.value = null;
  chromosomes.value = [];
  programs.value = [];
  
  // Reset data and charts
  comparativeData.value = [];
  resetChart();
  
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
    
    // Convert response to consistent format with label/value structure
    programs.value = (response.data.programs || []).map(program => ({
      label: program.name,
      value: program.id
    }));
  } catch (error) {
    console.error("Error fetching programs:", error);
    programs.value = [];
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
    
    if (!response.data || !Array.isArray(response.data.chromosomes)) {
      throw new Error('Invalid chromosome data format');
    }
    
    chromosomes.value = response.data.chromosomes.map(chr => ({ label: chr, value: chr }));
  } catch (error) {
    console.error("Error fetching chromosomes:", error);
    chromosomes.value = [];
    alert("Error loading chromosomes. Please try again later.");
  } finally {
    chromosomesLoading.value = false;
  }
}

async function fetchData() {
  // Check that required selections have been made
  if (!selectedChromosome.value || !selectedSpecies.value || !selectedProgram.value) {
    alert("Please select species, chromosome, and program.");
    return;
  }

  loading.value = true;
  resetChart();
  
  try {
    // Construct the query URL with all parameters
    const query = `?species=${encodeURIComponent(selectedSpecies.value)}&chromosome=${encodeURIComponent(selectedChromosome.value)}&program_id=${encodeURIComponent(selectedProgram.value)}`;
    
    const response = await axiosInstance.get(`/posts/visualizations/comparative${query}`);
    
    // Check if the response contains the expected data structure
    if (!response.data || !Array.isArray(response.data.data)) {
      throw new Error('Invalid response format');
    }
    
    comparativeData.value = response.data.data || [];
    
    // Calculate max difference for slider
    maxDifference.value = Math.max(...comparativeData.value.map(item => item.difference), 0);
    minDifference.value = 0; // Reset to 0
    
    // Use multiple approaches to ensure rendering
    // 1. Use nextTick to wait for DOM updates
    await nextTick();
    
    // 2. Add a small delay to ensure the canvas is fully ready
    setTimeout(() => {
      if (chartCanvas.value) {
        console.log("Rendering chart after timeout");
        updateCharts();
      } else {
        console.error("Chart canvas still not available after timeout");
      }
    }, 50); // Small timeout to ensure DOM is fully updated
    
    // 3. Try immediate rendering as well
    updateCharts();
    
  } catch (error) {
    console.error("Error fetching comparative data:", error);
    comparativeData.value = []; // Reset data on error
    alert(`Error fetching data: ${error.message || 'Unknown error'}. Please try again later.`);
  } finally {
    loading.value = false;
  }
}

function resetChart() {
  if (chartInstance) {
    chartInstance.destroy();
    chartInstance = null;
  }
}

function updateCharts() {
  // Double check that canvas is available
  if (!chartCanvas.value) {
    console.log("Canvas reference not found, will retry...");
    // Try to find the canvas element directly if the ref is not working
    const canvasElement = document.querySelector('.chart-container canvas');
    if (canvasElement) {
      console.log("Found canvas element via DOM query");
    } else {
      console.error("Canvas element not found in DOM");
      // Try again after a short delay
      setTimeout(() => updateCharts(), 100);
      return;
    }
  }
  
  if (filteredData.value.length === 0) {
    console.log("No data to display");
    return;
  }
  
  resetChart();
  
  // Make sure chartCanvas is defined before proceeding
  if (!chartCanvas.value) {
    console.error("Chart canvas is still undefined, cannot render chart");
    return;
  }
  
  // Use a local copy instead of the reactive reference
  const dataToVisualize = [...filteredData.value];
  
  const labels = dataToVisualize.map(item => item.locus);
  const totalCounts = dataToVisualize.map(item => item.total_count);
  const programCounts = dataToVisualize.map(item => item.program_count);
  const differences = dataToVisualize.map(item => item.difference);
  
  console.log(`Drawing ${selectedVisualization.value} chart with ${labels.length} data points`);
  
  try {
    // Update the appropriate chart based on selected visualization
    if (selectedVisualization.value === 'bar') {
      createBarChart(labels, totalCounts, programCounts);
    } else if (selectedVisualization.value === 'difference') {
      createDifferenceChart(labels, differences);
    } else if (selectedVisualization.value === 'heatmap') {
      createHeatmapChart(labels, differences);
    }
    
    // Verify chart was created
    console.log("Chart instance after drawing:", chartInstance ? "Created" : "Failed");
  } catch (error) {
    console.error("Error creating chart:", error);
  }
}

function createBarChart(labels, totalCounts, programCounts) {
  try {
    if (!chartCanvas.value) {
      console.error("Chart canvas is not available");
      return;
    }
    
    const ctx = chartCanvas.value.getContext('2d');
    if (!ctx) {
      console.error("Could not get 2D context from canvas");
      return;
    }
    
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'Total Database',
            data: totalCounts,
            backgroundColor: 'rgba(75, 192, 192, 0.4)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 1
          },
          {
            label: 'Program',
            data: programCounts,
            backgroundColor: 'rgba(153, 102, 255, 0.4)',
            borderColor: 'rgba(153, 102, 255, 1)',
            borderWidth: 1
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Allele Count',
              font: { size: 14, weight: 'bold' }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Locus',
              font: { size: 14, weight: 'bold' }
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Comparative Allele Counts by Locus',
            font: { size: 16, weight: 'bold' }
          },
          tooltip: {
            callbacks: {
              afterLabel: function(context) {
                const dataIndex = context.dataIndex;
                const difference = totalCounts[dataIndex] - programCounts[dataIndex];
                return `Difference: ${difference}`;
              }
            }
          }
        }
      }
    });
    
    console.log("Bar chart successfully created");
  } catch (error) {
    console.error("Error creating bar chart:", error);
  }
}

function createDifferenceChart(labels, differences) {
  try {
    if (!chartCanvas.value) {
      console.error("Chart canvas is not available");
      return;
    }
    
    const ctx = chartCanvas.value.getContext('2d');
    if (!ctx) {
      console.error("Could not get 2D context from canvas");
      return;
    }
    
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Missing Alleles',
          data: differences,
          backgroundColor: differences.map(value => 
            value > 5 ? 'rgba(255, 99, 132, 0.5)' : 
            value > 2 ? 'rgba(255, 159, 64, 0.5)' : 
            'rgba(75, 192, 192, 0.5)'
          ),
          borderColor: differences.map(value => 
            value > 5 ? 'rgb(255, 99, 132)' : 
            value > 2 ? 'rgb(255, 159, 64)' : 
            'rgb(75, 192, 192)'
          ),
          borderWidth: 1
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Difference Count',
              font: { size: 14, weight: 'bold' }
            }
          },
          x: {
            title: {
              display: true,
              text: 'Locus',
              font: { size: 14, weight: 'bold' }
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Missing Alleles by Locus',
            font: { size: 16, weight: 'bold' }
          }
        }
      }
    });
    
    console.log("Difference chart successfully created");
  } catch (error) {
    console.error("Error creating difference chart:", error);
  }
}

function createHeatmapChart(labels, differences) {
  try {
    if (!chartCanvas.value) {
      console.error("Chart canvas is not available");
      return;
    }
    
    const ctx = chartCanvas.value.getContext('2d');
    if (!ctx) {
      console.error("Could not get 2D context from canvas");
      return;
    }
    
    // Create a dataset with y-values of 1 for all points to create a single row heatmap
    const data = labels.map((label, index) => ({
      x: label,
      y: 'Missing Alleles',
      v: differences[index] // The actual value for color intensity
    }));
    
    chartInstance = new Chart(ctx, {
      type: 'scatter',
      data: {
        datasets: [{
          label: 'Heat Map',
          data: data,
          backgroundColor: function(context) {
            const value = context.raw.v;
            const alpha = Math.min(0.8, Math.max(0.1, value / 10)); // Scale alpha based on value
            
            if (value > 5) {
              return `rgba(255, 99, 132, ${alpha})`;
            } else if (value > 2) {
              return `rgba(255, 159, 64, ${alpha})`;
            } else {
              return `rgba(75, 192, 192, ${alpha})`;
            }
          },
          pointRadius: 15,
          pointHoverRadius: 20
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            type: 'category',
            labels: ['Missing Alleles'],
            offset: true
          },
          x: {
            type: 'category',
            labels: labels,
            title: {
              display: true,
              text: 'Locus',
              font: { size: 14, weight: 'bold' }
            }
          }
        },
        plugins: {
          title: {
            display: true,
            text: 'Heat Map of Missing Alleles',
            font: { size: 16, weight: 'bold' }
          },
          tooltip: {
            callbacks: {
              label: function(context) {
                return `Locus: ${context.raw.x}, Missing: ${context.raw.v}`;
              }
            }
          },
          legend: {
            display: false
          }
        }
      }
    });
    
    console.log("Heatmap chart successfully created");
  } catch (error) {
    console.error("Error creating heatmap chart:", error);
  }
}

function showMissingAlleles(data) {
  if (!data || !data.locus) {
    console.error("Invalid data for missing alleles");
    return;
  }
  
  selectedLocus.value = data.locus;
  selectedMissingAlleles.value = Array.isArray(data.missing_alleles) 
    ? data.missing_alleles.map(allele => ({ allele }))
    : [];
    
  missingAllelesDialogVisible.value = true;
}

function exportCSV() {
  if (filteredData.value.length === 0) {
    alert("No data available to export.");
    return;
  }
  
  try {
    const headers = ['Locus', 'Total Count', 'Program Count', 'Difference', 'Missing Count'];
    const rows = filteredData.value.map(item => [
      item.locus,
      item.total_count,
      item.program_count,
      item.difference,
      item.missing_count
    ]);
    
    const csvContent = 
      "data:text/csv;charset=utf-8," + 
      headers.join(",") + "\n" + 
      rows.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `comparative_data_${selectedSpecies.value}_${selectedChromosome.value}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Error exporting CSV:", error);
    alert("Failed to export CSV. Please try again.");
  }
}

function exportMissingAlleles() {
  if (selectedMissingAlleles.value.length === 0) {
    alert("No missing alleles data available to export.");
    return;
  }
  
  try {
    const headers = ['Allele ID'];
    const rows = selectedMissingAlleles.value.map(item => [item.allele]);
    
    const csvContent = 
      "data:text/csv;charset=utf-8," + 
      headers.join(",") + "\n" + 
      rows.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `missing_alleles_${selectedLocus.value}_${new Date().toISOString().split('T')[0]}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  } catch (error) {
    console.error("Error exporting missing alleles CSV:", error);
    alert("Failed to export CSV. Please try again.");
  }
}

onMounted(() => {
  console.log("Component mounted");
  // Try rendering immediately if data is already available
  if (comparativeData.value.length > 0) {
    console.log("Data available on mount, rendering chart");
    
    // Try multiple rendering approaches
    updateCharts(); // Try immediately
    
    nextTick(() => {
      updateCharts(); // Try after DOM update
    });
    
    setTimeout(() => {
      updateCharts(); // Try after a delay
    }, 100);
  }
});

onUnmounted(() => {
  // Clean up chart when component is destroyed
  resetChart();
});
</script>

<style scoped>
.comparative-container {
  max-width: 1000px;
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
  margin-top: 2rem;
}

.chart-container {
  height: 100%;
  width: 100%;
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

.filter-controls {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
  background-color: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-label {
  font-weight: 600;
  margin-right: 0.5rem;
}

.missing-alleles-container {
  max-height: 400px;
  overflow-y: auto;
}

@media (max-width: 768px) {
  .controls {
    flex-direction: column;
    align-items: stretch;
  }
  
  .control-item {
    width: 100%;
  }
  
  .chart-wrapper {
    height: 300px;
  }
}
</style>