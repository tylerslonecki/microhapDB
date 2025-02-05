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
          />
        </div>
        <Button
          label="Load Data"
          :disabled="!selectedChromosome || !selectedSpecies"
          @click="fetchData"
        />
      </div>
  
      <!-- Canvas for the histogram -->
      <div class="chart-wrapper">
        <canvas id="histogram"></canvas>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, onMounted } from 'vue';
  import { Chart, registerables } from 'chart.js';
  import axiosInstance from '../axiosConfig';
  
  // Import PrimeVue components
  import Dropdown from 'primevue/dropdown';
  import Button from 'primevue/button';
  
  // Register all Chart.js components
  Chart.register(...registerables);

  const speciesOptions = [
    { label: 'alfalfa', value: 'alfalfa' },
    { label: 'sweetpotato', value: 'sweetpotato' },
    { label: 'cranberry', value: 'cranberry' }
  ];
  
  // Arrays for dropdown options
  const chromosomes = [
    { label: 'chr1', value: 'chr1' },
    { label: 'chr2', value: 'chr2' },
    { label: 'chr3', value: 'chr3' },
    { label: 'chr4', value: 'chr4' },
    { label: 'chr5', value: 'chr5' },
    { label: 'chr6', value: 'chr6' },
    { label: 'chr7', value: 'chr7' },
    { label: 'chr8', value: 'chr8' }

  ];
  
  
  // Reactive variables for dropdown selections and histogram data
  const selectedChromosome = ref('');
  const selectedSpecies = ref('');
  const histogramData = ref([]);
  
  // Chart instance reference
  let chartInstance = null;
  
  async function fetchData() {
    // Check that both selections have been made.
    if (!selectedChromosome.value || !selectedSpecies.value) {
      alert("Please select both a chromosome and a species.");
      return;
    }
  
    try {
      // Construct the query URL with the /posts prefix
      const query = `?species=${encodeURIComponent(selectedSpecies.value)}&chromosome=${encodeURIComponent(selectedChromosome.value)}`;
      const response = await axiosInstance.get(`/posts/visualizations/histogram${query}`);
  
      // Since Axios automatically parses JSON, we access the data directly.
      const result = response.data;
      histogramData.value = result.data || [];
  
      // Update the chart with the new data
      updateChart();
    } catch (error) {
      console.error("Error fetching histogram data:", error);
      alert("Error fetching data. Please try again later.");
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
        }]
      },
      options: {
        scales: {
          y: {
            beginAtZero: true,
            title: {
              display: true,
              text: 'Allele Count'
            }
          },
          x: {
            title: {
              display: true,
              text: 'Locus'
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
  }
  
  .control-label {
    margin-bottom: 0.5rem;
    font-weight: 600;
  }
  
  .chart-wrapper {
    position: relative;
    height: 400px;
  }
  </style>
  