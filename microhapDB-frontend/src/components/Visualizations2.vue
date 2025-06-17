<template>
  <div class="comparative-container">
    <Panel header="Missing Allele Analysis" class="mb-4">
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

      <!-- Chart wrapper -->
      <div class="chart-wrapper">
        <div v-if="loading" class="loading-overlay">
          <i class="pi pi-spin pi-spinner" style="font-size: 2rem"></i>
          <span>Loading data...</span>
        </div>
        
        <!-- Linear Genome specific legend -->
        <div v-if="!loading && loadedChromosomeType === 'all'" class="genome-legend">
          <div class="legend-item">
            <i class="pi pi-info-circle" style="color: #666;"></i>
            <span>Tip: Click on a chromosome bar to view its detailed breakdown</span>
          </div>
        </div>
        
        <!-- Linear Genome specific legend for individual chromosome view -->
        <div v-if="!loading && loadedChromosomeType !== 'all' && loadedChromosomeType !== ''" class="genome-legend">
          <div class="legend-section">
            <h4 class="legend-title">Point Size (Total Alleles)</h4>
            <div class="size-legend">
              <div class="legend-item">
                <div class="legend-circle legend-size-small"></div>
                <span>Low diversity (&lt;5 alleles)</span>
              </div>
              <div class="legend-item">
                <div class="legend-circle legend-size-medium"></div>
                <span>Medium diversity (5-10 alleles)</span>
              </div>
              <div class="legend-item">
                <div class="legend-circle legend-size-large"></div>
                <span>High diversity (&gt;10 alleles)</span>
              </div>
            </div>
          </div>
          <div class="legend-section">
            <h4 class="legend-title">Point Color (% Missing)</h4>
            <div class="color-legend">
              <div class="legend-item">
                <div class="legend-color legend-green"></div>
                <span>Low missing (&lt;20%)</span>
              </div>
              <div class="legend-item">
                <div class="legend-color legend-yellow"></div>
                <span>Medium missing (20-50%)</span>
              </div>
              <div class="legend-item">
                <div class="legend-color legend-red"></div>
                <span>High missing (&gt;50%)</span>
              </div>
            </div>
          </div>
          <div class="legend-item">
            <i class="pi pi-info-circle" style="color: #666;"></i>
            <span><strong>Tip:</strong> Large red bubbles indicate high-diversity loci with many missing alleles</span>
          </div>

        </div>
        
        <div v-if="!loading" class="chart-container">
          <!-- Container for D3 visualizations -->
          <div id="d3-container" ref="d3Container" class="d3-container"></div>
        </div>
      </div>

      <!-- Data Table -->
      <div class="mt-6" v-if="comparativeData.length > 0 && !loading">
        <div class="table-header">
          <h3>Loci with Missing Alleles</h3>
          <Button
            label="Export CSV"
            icon="pi pi-download"
            @click="exportCSV"
            class="p-button-outlined"
          />
        </div>
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
          <Column field="formattedLocus" header="Locus" sortable style="min-width: 200px; max-width: 300px; word-break: break-word;"></Column>
          <Column field="total_count" header="Total Alleles" sortable style="min-width: 100px;"></Column>
          <Column field="program_count" header="Program Alleles" sortable style="min-width: 120px;"></Column>
          <Column field="difference" header="Difference" sortable style="min-width: 100px;"></Column>
          <Column field="missing_count" header="Missing Count" sortable style="min-width: 120px;"></Column>
          <Column header="Actions" style="min-width: 80px; width: 80px;">
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
      :header="`Missing Alleles for Locus: ${selectedMissingAlleles.length > 0 ? selectedMissingAlleles[0].locus : ''}`"
      :style="{ width: '70vw' }"
      :modal="true"
    >
      <div class="missing-alleles-container">
        <DataTable 
          :value="selectedMissingAlleles" 
          :paginator="true" 
          :rows="10"
          :expandedRows="expandedRows"
          class="p-datatable-sm"
          v-model:expandedRows="expandedRows"
          dataKey="alleleId"
          @rowExpand="onRowExpand"
          @rowCollapse="onRowCollapse"
        >
          <Column header="Allele ID" style="min-width: 250px; word-break: break-word;">
            <template #body="slotProps">
              {{ slotProps.data.alleleId }}
            </template>
          </Column>
          <Column header="Actions" style="min-width: 120px;">
            <template #body="slotProps">
              <Button 
                icon="pi pi-plus" 
                label="Add to Query"
                class="p-button-success p-button-sm" 
                @click="addToQueryList(slotProps.data)"
                :disabled="isAlreadyInQueryList(slotProps.data.alleleId)"
              />
            </template>
          </Column>
          <Column :expander="true" header="Accessions" headerStyle="width: 100px; text-align: center;" bodyStyle="text-align: center;" />
          <template #expansion="slotProps">
            <div class="p-3">
              <h5>Accessions for {{ slotProps.data.alleleId }}</h5>
              <div v-if="loadingAccessions[slotProps.data.alleleId]" class="loading-indicator">
                <i class="pi pi-spin pi-spinner"></i>
                <span>Loading accessions...</span>
              </div>
              <div v-else-if="alleleAccessions[slotProps.data.alleleId] && alleleAccessions[slotProps.data.alleleId].length > 0">
                <div class="accession-grid">
                  <div 
                    v-for="accession in alleleAccessions[slotProps.data.alleleId]" 
                    :key="accession.accession"
                    class="accession-item"
                  >
                    <div class="accession-name">{{ accession.accession }}</div>
                    <div class="accession-details">
                      <span v-if="accession.programs.length > 0" class="program-tag">
                        {{ accession.programs.join(', ') }}
                      </span>
                      <span v-if="accession.projects.length > 0" class="project-tag">
                        {{ accession.projects.join(', ') }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
              <div v-else>
                <p>No accessions found for this allele.</p>
              </div>
            </div>
          </template>
        </DataTable>
      </div>
      <template #footer>
        <Button label="Close" icon="pi pi-times" @click="missingAllelesDialogVisible = false" class="p-button-text" />
        <Button label="Export List" icon="pi pi-download" @click="exportMissingAlleles" />
        <Button 
          label="Add All to Query List" 
          icon="pi pi-plus-circle" 
          @click="addAllToQueryList" 
          class="p-button-success"
          :disabled="selectedMissingAlleles.length === 0"
        />
        <Button 
          label="Go to Query" 
          icon="pi pi-arrow-right" 
          @click="navigateToQuery" 
          class="p-button-info"
        />
      </template>
    </Dialog>
    
    <!-- Toast for notifications -->
    <Toast />
  </div>
</template>

<script setup>
/* eslint-disable */
import { ref, onMounted, computed, watch, onUnmounted, nextTick } from 'vue';
import { useStore } from 'vuex';
import { useToast } from 'primevue/usetoast';
import { useRouter } from 'vue-router';
import axiosInstance from '../axiosConfig';

// Import PrimeVue components
import Dropdown from 'primevue/dropdown';
import Button from 'primevue/button';
import Panel from 'primevue/panel';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dialog from 'primevue/dialog';
import Tooltip from 'primevue/tooltip';
import Toast from 'primevue/toast';

// Register directives
const vTooltip = Tooltip;

import * as d3 from 'd3';
import { SUPPORTED_SPECIES } from '../utils/speciesConfig';

// Initialize store and toast
const store = useStore();
const toast = useToast();
const router = useRouter();

// Reactive species options with consistent structure
const speciesOptions = ref(SUPPORTED_SPECIES);

// Reactive variables
const selectedSpecies = ref('');
const selectedProgram = ref(null);
const selectedChromosome = ref('');
const chromosomes = ref([]);
const programs = ref([]);
const comparativeData = ref([]);
const loading = ref(false);
const chromosomesLoading = ref(false);
const programsLoading = ref(false);
const missingAllelesDialogVisible = ref(false);
const selectedLocus = ref('');
const selectedMissingAlleles = ref([]);
const loadedChromosomeType = ref(''); // Track the chromosome type that was actually loaded

// New reactive variables for the enhanced modal functionality
const expandedRows = ref([]);
const alleleAccessions = ref({});
const loadingAccessions = ref({});

// Add more reactive references for the D3 visualization
const d3Container = ref(null);
// eslint-disable-next-line no-unused-vars
let d3Visualization = null;

// Create a computed property for formatted loci that include chromosome name
const formattedLoci = computed(() => {
  return comparativeData.value.map(item => {
    // Create a copy of the item to avoid mutating the original data
    const formattedItem = { ...item };
    // Use the chromosome stored with each item (from the API response)
    const chromosome = item.chromosome || selectedChromosome.value;
    // Add a new property for the formatted locus (with chromosome)
    formattedItem.formattedLocus = `${chromosome}.${item.locus.split('|')[0]}`;
    return formattedItem;
  });
});

// Update filteredData to use the formatted loci
const filteredData = computed(() => {
  return formattedLoci.value;
});

// Watch for comparativeData changes to ensure chart gets rendered when data changes
watch(comparativeData, (newData) => {
  if (newData.length > 0) {
    // Use nextTick to ensure DOM is updated before trying to render
    nextTick(() => {
      updateCharts();
    });
  }
}, { deep: true });

// Watch for row expansions to fetch accessions automatically
watch(expandedRows, (newExpandedRows, oldExpandedRows) => {
  console.log("🔄 expandedRows watcher triggered:", {
    newExpandedRows,
    oldExpandedRows,
    newLength: newExpandedRows?.length || 0,
    oldLength: oldExpandedRows?.length || 0
  });
  
  // Ensure both values are arrays before processing
  const newRows = Array.isArray(newExpandedRows) ? newExpandedRows : [];
  const oldRows = Array.isArray(oldExpandedRows) ? oldExpandedRows : [];
  
  console.log("🔄 Processed rows:", {
    newRowsLength: newRows.length,
    oldRowsLength: oldRows.length,
    newRowsData: newRows,
    oldRowsData: oldRows
  });
  
  // Find newly expanded rows
  const newlyExpanded = newRows.filter(newRow => 
    !oldRows.some(oldRow => oldRow.alleleId === newRow.alleleId)
  );
  
  console.log("🔄 Newly expanded rows:", {
    count: newlyExpanded.length,
    rows: newlyExpanded
  });
  
  // Fetch accessions for newly expanded rows
  newlyExpanded.forEach(row => {
    console.log(`🔄 Fetching accessions for row:`, row, `Using AlleleID: ${row.alleleId}`);
    fetchAccessionsForAllele(row.alleleId);
  });
}, { deep: true });

async function onSpeciesChange() {
  // Reset selections when species changes
  selectedChromosome.value = '';
  selectedProgram.value = null;
  chromosomes.value = [];
  programs.value = [];
  
  // Reset data and charts
  comparativeData.value = [];
  loadedChromosomeType.value = ''; // Reset loaded chromosome type
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
  let retries = 3;
  
  while (retries > 0) {
    try {
      // Call the API endpoint to get programs for the selected species
      const response = await axiosInstance.get(
        `/posts/programs/by_species/${encodeURIComponent(selectedSpecies.value)}`,
        { timeout: 30000 } // Increase timeout to 30 seconds
      );
      
      // Convert response to consistent format with label/value structure
      programs.value = (response.data.programs || []).map(program => ({
        label: program.name,
        value: program.id
      }));
      break; // Success, exit the retry loop
    } catch (error) {
      retries--;
      console.error(`Error fetching programs (${retries} retries left):`, error);
      if (retries === 0) {
        programs.value = [];
        alert("Error loading programs. Please try again later.");
      } else {
        // Wait for 1 second before retrying
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
  }
  
  programsLoading.value = false;
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
    
    // Add "All Chromosomes" option as the first option
    chromosomes.value = [
      { label: 'All Chromosomes', value: 'all' },
      ...response.data.chromosomes.map(chr => ({ label: chr, value: chr }))
    ];
  } catch (error) {
    console.error("Error fetching chromosomes:", error);
    chromosomes.value = [{ label: 'All Chromosomes', value: 'all' }]; // Still add "All" option even on error
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
    let combinedData = [];
    
    if (selectedChromosome.value === 'all') {
      // If "All Chromosomes" is selected, fetch data for each chromosome separately
      // First, get the list of all chromosomes (excluding the "all" option)
      const actualChromosomes = chromosomes.value
        .filter(chr => chr.value !== 'all')
        .map(chr => chr.value);
      
      // Fetch data for each chromosome sequentially
      for (const chromosome of actualChromosomes) {
        const query = `?species=${encodeURIComponent(selectedSpecies.value)}&chromosome=${encodeURIComponent(chromosome)}&program_id=${encodeURIComponent(selectedProgram.value)}`;
        
        const response = await axiosInstance.get(`/posts/visualizations/comparative${query}`);
        
        if (response.data && Array.isArray(response.data.data)) {
          // Add the chromosome to each locus for better identification
          const dataWithChromosome = response.data.data.map(item => ({
            ...item,
            chromosome: chromosome, // Store the chromosome for each locus
          }));
          
          combinedData = [...combinedData, ...dataWithChromosome];
        }
      }
      
      comparativeData.value = combinedData;
      console.log(`Fetched a total of ${combinedData.length} data points across all chromosomes`);
    } else {
      // Regular case: fetch data for a single chromosome
      const query = `?species=${encodeURIComponent(selectedSpecies.value)}&chromosome=${encodeURIComponent(selectedChromosome.value)}&program_id=${encodeURIComponent(selectedProgram.value)}`;
      
      const response = await axiosInstance.get(`/posts/visualizations/comparative${query}`);
      
      // Check if the response contains the expected data structure
      if (!response.data || !Array.isArray(response.data.data)) {
        throw new Error('Invalid response format');
      }
      
      // Add the chromosome to each locus for consistency with the "all" case
      comparativeData.value = response.data.data.map(item => ({
        ...item,
        chromosome: selectedChromosome.value,
      })) || [];
      
      console.log(`Fetched ${comparativeData.value.length} data points for chromosome ${selectedChromosome.value}`);
    }
    
    // Use multiple approaches to ensure rendering
    // 1. Use nextTick to wait for DOM updates
    await nextTick();
    
    // Set the loaded chromosome type after successful data loading
    loadedChromosomeType.value = selectedChromosome.value;
    
    // 2. Add a small delay to ensure the canvas is fully ready
    setTimeout(() => {
      if (d3Container.value) {
        console.log("Rendering chart after timeout");
        updateCharts();
      } else {
        console.error("D3 container still not available after timeout");
      }
    }, 50); // Small timeout to ensure DOM is fully updated
    
    // 3. Try immediate rendering as well
    updateCharts();
    
  } catch (error) {
    console.error("Error fetching comparative data:", error);
    comparativeData.value = []; // Reset data on error
    loadedChromosomeType.value = ''; // Reset loaded chromosome type on error
    alert(`Error fetching data: ${error.message || 'Unknown error'}. Please try again later.`);
  } finally {
    loading.value = false;
  }
}

function resetChart() {
  // Clean up D3 visualizations
  if (d3Container.value) {
    d3Container.value.innerHTML = '';
  }
  
  // Clean up any remaining tooltips
  d3.selectAll('.d3-tooltip').remove();
  
  // Reset cursor
  document.body.style.cursor = '';
}

function updateCharts() {
  if (filteredData.value.length === 0) {
    console.log("No data to display");
    return;
  }
  
  // Check if d3Container is available
  if (!d3Container.value) {
    console.log("D3 container not ready, waiting...");
    // Retry after a short delay
    setTimeout(() => {
      if (d3Container.value) {
        updateCharts();
      } else {
        console.error("D3 container still not available after wait");
      }
    }, 100);
    return;
  }
  
  resetChart();
  
  // Use a local copy instead of the reactive reference
  const dataToVisualize = [...filteredData.value];
  
  console.log(`Using all ${dataToVisualize.length} data points for linear genome view`);
  createLinearGenomeView(dataToVisualize);
}

// Add the D3 linear genome view function
function createLinearGenomeView(data) {
  try {
    // Add null check for d3Container
    if (!d3Container.value) {
      console.error("D3 container not available");
      return;
    }
    
    // Clear previous chart or D3 visualization
    resetChart();
    
    // Also clear any existing D3 visualization
    if (d3Container.value) {
      d3Container.value.innerHTML = '';
    }
    
    // Check if we're in "All Chromosomes" mode
    const isAllChromosomesMode = selectedChromosome.value === 'all';
    
    // Sort the data first by chromosome (if in "all" mode) and then by position
    const sortedData = [...data].sort((a, b) => {
      // First sort by chromosome if in "all" mode
      if (isAllChromosomesMode) {
        if (a.chromosome !== b.chromosome) {
          return a.chromosome.localeCompare(b.chromosome);
        }
      }
      
      // Then sort by position within chromosome
      const aMatch = a.locus.match(/[_.]?(\d+)[_.]?/);
      const bMatch = b.locus.match(/[_.]?(\d+)[_.]?/);
      
      const aPos = aMatch && aMatch[1] ? parseInt(aMatch[1]) : 0;
      const bPos = bMatch && bMatch[1] ? parseInt(bMatch[1]) : 0;
      
      return aPos - bPos;
    });
    
    // Set up D3 visualization
    const width = d3Container.value.clientWidth || 800;
    const height = d3Container.value.clientHeight || 500;
    const margin = { top: 30, right: 50, bottom: 60, left: 60 };
    
    // If we're in all-chromosomes mode, increase the right margin to accommodate the color scale
    if (isAllChromosomesMode) {
      margin.right = 100; // Increase right margin to make room for color scale
    }
    
    // Create SVG
    const svg = d3.select(d3Container.value)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    if (isAllChromosomesMode) {
      // Function to extract position from locus name (reuse from individual chromosome logic)
      const extractPosition = (locusName) => {
        // Try different patterns for position extraction in order of preference
        
        // Try to find numbers after a underscore or dot
        const pattern1 = /[_.](\d+)[_.]?/;
        const match1 = locusName.match(pattern1);
        if (match1 && match1[1]) {
          return parseInt(match1[1]);
        }
        
        // Try to match at the end of the string - like "something123"
        const pattern2 = /(\d+)$/;
        const match2 = locusName.match(pattern2);
        if (match2 && match2[1]) {
          return parseInt(match2[1]);
        }
        
        // Try to find any number sequence
        const pattern3 = /(\d+)/;
        const match3 = locusName.match(pattern3);
        if (match3 && match3[1]) {
          return parseInt(match3[1]);
        }
        
        // If all else fails
        return null;
      };

      // Define segment size (10Mbp)
      const segmentSize = 10000000;
      
      // Group data by chromosome and 10Mbp segments
      const segmentData = {};
      
      sortedData.forEach(item => {
        const chr = item.chromosome;
        const position = extractPosition(item.locus);
        
        // If we can't extract position, assign to segment 0
        const segmentIndex = position !== null ? Math.floor(position / segmentSize) : 0;
        const segmentKey = `${chr}_${segmentIndex}`;
        
        if (!segmentData[segmentKey]) {
          segmentData[segmentKey] = {
            chromosome: chr,
            segmentIndex: segmentIndex,
            startPos: segmentIndex * segmentSize,
            endPos: (segmentIndex + 1) * segmentSize,
            loci: []
          };
        }
        
        segmentData[segmentKey].loci.push(item);
      });

      // Calculate statistics by segment
      const segmentStats = {};
      const segmentKeys = Object.keys(segmentData).sort((a, b) => {
        const [chrA, segA] = a.split('_');
        const [chrB, segB] = b.split('_');
        if (chrA !== chrB) return chrA.localeCompare(chrB);
        return parseInt(segA) - parseInt(segB);
      });
      
      segmentKeys.forEach(segmentKey => {
        const segment = segmentData[segmentKey];
        const totalAlleles = d3.sum(segment.loci, d => d.total_count);
        const missingAlleles = d3.sum(segment.loci, d => d.difference);
        const percentage = totalAlleles > 0 ? (missingAlleles / totalAlleles) * 100 : 0;
        
        segmentStats[segmentKey] = {
          chromosome: segment.chromosome,
          segmentIndex: segment.segmentIndex,
          startPos: segment.startPos,
          endPos: segment.endPos,
          count: segment.loci.length,  // Number of loci with missing alleles
          sum: missingAlleles,   // Total missing alleles
          totalAlleles: totalAlleles, // Total alleles for this segment
          percentage: percentage, // Percentage of missing alleles
          label: `${segment.chromosome} ${Math.round(segment.startPos/1000000)}.0-${Math.round(segment.endPos/1000000)}.0 Mbps`
        };
      });
      
      // Group segments by chromosome for layout with gaps
      const chromosomeGroups = {};
      segmentKeys.forEach(segmentKey => {
        const chromosome = segmentKey.split('_')[0];
        if (!chromosomeGroups[chromosome]) {
          chromosomeGroups[chromosome] = [];
        }
        chromosomeGroups[chromosome].push(segmentKey);
      });
      
      const chromosomes = Object.keys(chromosomeGroups).sort();
      
      // Calculate positions with gaps between chromosomes
      const segmentWidth = 20; // Width of each segment bar
      const gapBetweenSegments = 2; // Small gap between segments within chromosome
      const gapBetweenChromosomes = 40; // Larger gap between chromosomes
      
      let currentX = 0;
      const segmentPositions = {};
      const chromosomePositions = {};
      
      chromosomes.forEach(chromosome => {
        chromosomePositions[chromosome] = currentX;
        
        chromosomeGroups[chromosome].forEach((segmentKey, index) => {
          segmentPositions[segmentKey] = currentX;
          currentX += segmentWidth + gapBetweenSegments;
        });
        
        // Remove the last small gap and add chromosome gap
        currentX = currentX - gapBetweenSegments + gapBetweenChromosomes;
      });
      
      const totalWidth = currentX - gapBetweenChromosomes; // Remove final gap
      
      // Create custom scale for positioning
      const getSegmentX = (segmentKey) => {
        return (segmentPositions[segmentKey] / totalWidth) * innerWidth;
      };
      
      const getSegmentWidth = () => {
        return (segmentWidth / totalWidth) * innerWidth;
      };
      
      // Set up scales for segment bars
      const xScale = d3.scaleBand()
        .domain(segmentKeys)
        .range([0, innerWidth])
        .padding(0.1); // Smaller padding for more segments
        
      // Find the maximum percentage for any segment
      const maxPercentage = d3.max(Object.values(segmentStats), d => d.percentage);
      
      const yScale = d3.scaleLinear()
        .domain([0, Math.min(100, maxPercentage * 1.1)]) // Cap at 100% or add 10% padding
        .range([innerHeight, 0]);
    
      // Generate color scale for segments based on percentage
      const colorScale = d3.scaleLinear()
        .domain([0, maxPercentage * 0.5, maxPercentage])
        .range(['#75C9C8', '#FFA726', '#F06292']); // Light blue, orange, pink
      
      // Add tooltip
      const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'd3-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background-color', 'rgba(255, 255, 255, 0.95)')
        .style('border', '1px solid #ddd')
        .style('border-radius', '4px')
        .style('padding', '6px')
        .style('font-size', '11px')
        .style('pointer-events', 'none')
        .style('z-index', '10000')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.2)');
      
      // Create bars to represent total missing alleles by segment
      svg.selectAll('.segment-bar')
        .data(segmentKeys)
        .enter()
        .append('rect')
        .attr('class', 'segment-bar')
        .attr('x', d => getSegmentX(d))
        .attr('y', d => yScale(segmentStats[d].percentage))
        .attr('width', getSegmentWidth())
        .attr('height', d => innerHeight - yScale(segmentStats[d].percentage))
        .attr('fill', d => colorScale(segmentStats[d].percentage))
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .on('mouseover', function(event, d) {
          const stats = segmentStats[d];
          
          // Highlight this bar
          d3.select(this)
            .attr('stroke', '#333')
            .attr('stroke-width', 2);
          
          // Show tooltip
          tooltip.transition()
            .duration(200)
            .style('opacity', 1);
            
          tooltip.html(`
            <strong>${stats.label}</strong><br/>
            <table style="margin-top:5px;">
              <tr><td>Chromosome:</td><td><b>${stats.chromosome}</b></td></tr>
              <tr><td>Position range:</td><td><b>${(stats.startPos/1000000).toFixed(1)}-${(stats.endPos/1000000).toFixed(1)} Mbp</b></td></tr>
              <tr><td>Missing percentage:</td><td><b>${stats.percentage.toFixed(1)}%</b></td></tr>
              <tr><td>Missing alleles:</td><td><b>${stats.sum}</b></td></tr>
              <tr><td>Total alleles:</td><td><b>${stats.totalAlleles}</b></td></tr>
              <tr><td>Loci affected:</td><td><b>${stats.count}</b></td></tr>
            </table>
            <div style="margin-top:5px; font-style:italic;">Click to view chromosome ${stats.chromosome} in detail</div>
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
          // Remove highlight
          d3.select(this)
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);
            
          // Hide tooltip
          tooltip.transition()
            .duration(500)
            .style('opacity', 0);
        })
        .on('click', (event, d) => {
          // Navigate to the detailed view for this segment
          selectedChromosome.value = d.split('_')[0];
          nextTick(() => {
            fetchData();
          });
        });
      
      // Add value labels on top of bars (only show if percentage is significant)
      // Removed percentage labels to avoid overcrowding with 10Mbp segments
      
      // Add axes
      // Create y-axis only (no complex x-axis needed)
      const yAxis = d3.axisLeft(yScale);
      
      svg.append('g')
        .attr('class', 'y-axis')
        .call(yAxis);
      
      // Add chromosome labels positioned at center of each chromosome group
      chromosomes.forEach(chromosome => {
        const segments = chromosomeGroups[chromosome];
        const firstSegmentX = getSegmentX(segments[0]);
        const lastSegmentX = getSegmentX(segments[segments.length - 1]);
        const centerX = (firstSegmentX + lastSegmentX + getSegmentWidth()) / 2;
        
        svg.append('text')
          .attr('class', 'chromosome-label')
          .attr('x', centerX)
          .attr('y', innerHeight + 15)
          .attr('text-anchor', 'middle')
          .style('font-size', '12px')
          .style('font-weight', 'bold')
          .style('fill', '#333')
          .text(chromosome);
      });
      
      // Add x-axis line
      svg.append('line')
        .attr('class', 'x-axis-line')
        .attr('x1', 0)
        .attr('x2', innerWidth)
        .attr('y1', innerHeight)
        .attr('y2', innerHeight)
        .attr('stroke', '#ddd')
        .attr('stroke-width', 1);
      
      // Add axis labels
      svg.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + 40)
        .style('font-size', '14px')
        .text('Chromosomes (10Mbp segments)');
      
      svg.append('text')
        .attr('class', 'y-axis-label')
        .attr('text-anchor', 'middle')
        .attr('transform', `translate(${-40},${innerHeight / 2}) rotate(-90)`)
        .style('font-size', '14px')
        .text('Missing Allele Percentage');
      
      // Add title
      svg.append('text')
        .attr('class', 'chart-title')
        .attr('text-anchor', 'middle')
        .attr('x', innerWidth / 2)
        .attr('y', -10)
        .style('font-size', '16px')
        .style('font-weight', 'bold')
        .text('Missing Allele Percentage by Segment');
      
      // Add color scale legend to the right side of the chart
      const legendWidth = 20;
      const legendHeight = innerHeight * 0.7;
      const legendX = innerWidth + 25;
      const legendY = innerHeight * 0.15;
      
      // Create color scale gradient for the legend
      const defs = svg.append("defs");
      const gradient = defs.append("linearGradient")
        .attr("id", "color-scale-gradient")
        .attr("x1", "0%")
        .attr("y1", "100%")
        .attr("x2", "0%")
        .attr("y2", "0%");
      
      // Add color stops to match our color scale - use the exact same colorScale that's used for the bars
      gradient.append("stop")
        .attr("offset", "0%")
        .attr("stop-color", colorScale(0));
      
      gradient.append("stop")
        .attr("offset", "50%")
        .attr("stop-color", colorScale(maxPercentage * 0.5));
      
      gradient.append("stop")
        .attr("offset", "100%")
        .attr("stop-color", colorScale(maxPercentage));
      
      // Create the rectangle with gradient fill
      svg.append("rect")
        .attr("x", legendX)
        .attr("y", legendY)
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .style("fill", "url(#color-scale-gradient)")
        .style("stroke", "#ccc")
        .style("stroke-width", 1);
      
      // Add a title for the legend
      svg.append("text")
        .attr("x", legendX + legendWidth / 2)
        .attr("y", legendY - 10)
        .attr("text-anchor", "middle")
        .style("font-size", "12px")
        .style("font-weight", "bold")
        .text("Missing %");
      
      // Add scale ticks and labels
      const legendScale = d3.scaleLinear()
        .domain([0, maxPercentage])
        .range([legendHeight, 0]);
      
      const legendAxis = d3.axisRight(legendScale)
        .ticks(5)
        .tickSize(4);
      
      svg.append("g")
        .attr("class", "legend-axis")
        .attr("transform", `translate(${legendX + legendWidth}, ${legendY})`)
        .call(legendAxis)
        .selectAll("text")
        .style("font-size", "10px");
    } else {
      // Handle individual chromosome view with a scatter plot
      // Get the loci positions
      const lociPositions = [];
      
      // Improved regex for extracting position information from loci
      const extractPosition = (locusName) => {
        // Try different patterns for position extraction in order of preference
        
        // Try to find numbers after a underscore or dot
        const pattern1 = /[_.](\d+)[_.]?/;
        const match1 = locusName.match(pattern1);
        if (match1 && match1[1]) {
          return parseInt(match1[1]);
        }
        
        // Try to match at the end of the string - like "something123"
        const pattern2 = /(\d+)$/;
        const match2 = locusName.match(pattern2);
        if (match2 && match2[1]) {
          return parseInt(match2[1]);
        }
        
        // Try to find any number sequence
        const pattern3 = /(\d+)/;
        const match3 = locusName.match(pattern3);
        if (match3 && match3[1]) {
          return parseInt(match3[1]);
        }
        
        // If all else fails
        return null;
      };
      
      // Process each locus to extract position information
      sortedData.forEach((item, index) => {
        // Extract position using our improved function
        let position = extractPosition(item.locus);
        
        // If we couldn't extract a position, use the index as a fallback
        if (position === null) {
          position = index * 100000;  // Space points when using index-based positions
          console.log(`Could not extract position from ${item.locus}, using index: ${position}`);
        }
        
        lociPositions.push({
          locus: item.formattedLocus,
          originalLocus: item.locus,
          position: position,
          index: index,
          difference: item.difference,
          totalCount: item.total_count,
          programCount: item.program_count,
          missingCount: item.missing_count,
          percentage: ((item.difference / item.total_count) * 100).toFixed(1)
        });
      });
      
      // Check if we've extracted multiple positions
      const uniquePositions = [...new Set(lociPositions.map(d => d.position))];
      console.log(`Extracted ${uniquePositions.length} unique positions from ${lociPositions.length} loci`);
      
      // Analyze position distribution
      const positionGroups = {};
      uniquePositions.forEach(pos => {
        const groupKey = Math.floor(pos / 10000000) * 10000000;
        if (!positionGroups[groupKey]) positionGroups[groupKey] = 0;
        positionGroups[groupKey]++;
      });
      console.log("Position distribution by 10M ranges:", positionGroups);
      
      // If we couldn't extract multiple positions, fall back to using indices
      if (uniquePositions.length < 2 && lociPositions.length > 1) {
        console.log("Falling back to index-based positions");
        lociPositions.forEach((item, index) => {
          item.position = index * 100000;  // Space points when using index-based positions
        });
      }
      
      // Sort by position
      lociPositions.sort((a, b) => a.position - b.position);

      // Create a scale for horizontal placement with appropriate domain
      const xMin = d3.min(lociPositions, d => d.position);
      const xMax = d3.max(lociPositions, d => d.position);
      
      // Debug the position range to understand the data distribution
      console.log(`Position range: min=${xMin}, max=${xMax}, range=${xMax - xMin}`);
      
      // Log points at various parts of the range for debugging
      console.log("First 5 points:");
      lociPositions.slice(0, 5).forEach(d => console.log(`  ${d.locus}: position=${d.position}, diff=${d.difference}`));
      
      console.log("Last 5 points:");
      lociPositions.slice(-5).forEach(d => console.log(`  ${d.locus}: position=${d.position}, diff=${d.difference}`));
      
      // Sample some points in the middle if we have many
      if (lociPositions.length > 20) {
        const midIndex = Math.floor(lociPositions.length / 2);
        console.log("Middle 5 points:");
        lociPositions.slice(midIndex-2, midIndex+3).forEach(d => 
          console.log(`  ${d.locus}: position=${d.position}, diff=${d.difference}`)
        );
      }
      
      const xPadding = Math.max(1, (xMax - xMin) * 0.05); // 5% padding on each side
      
      // The view window size (number of positions visible when fully zoomed out)
      const viewWindowSize = 20000000;
      
      // Store total data range for reference
      console.log(`Data range: ${xMin} to ${xMax}, span: ${xMax - xMin}`);
      
      // Calculate the width needed to show all positions - ensure it's large enough
      const totalScaledWidth = innerWidth * Math.max(1, (xMax - xMin + 2*xPadding) / viewWindowSize);
      console.log(`Total scaled width: ${totalScaledWidth}px for ${xMax - xMin} positions`);
      
      // Create the x scale for the full data range - this is critical for all points to render
      const xScale = d3.scaleLinear()
        .domain([xMin - xPadding, xMax + xPadding])
        .range([0, totalScaledWidth]);
      
      // Test a few positions to verify the scale is working correctly
      console.log(`Scale check: xMin=${xMin} -> ${xScale(xMin)}px, xMax=${xMax} -> ${xScale(xMax)}px`);
      console.log(`Scale check: 20M -> ${xScale(20000000)}px, 40M -> ${xScale(40000000)}px`);

      // Create initial visible scale for the first 20M window
      const visibleXScale = d3.scaleLinear()
        .domain([xMin, Math.min(xMin + viewWindowSize, xMax)])
        .range([0, innerWidth]);
      
      // Create scale for vertical placement
      const yScale = d3.scaleLinear()
        .domain([0, d3.max(lociPositions, d => d.difference) * 1.1])
        .range([innerHeight, 0]);

      // Add a clipPath to limit the visible area
      svg.append("defs")
        .append("clipPath")
        .attr("id", "chart-area")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);

      // Create a group for all the elements - REMOVE CLIPPING
      const plotGroup = svg.append('g')
        .attr('class', 'plot-group');
        // Remove the clip-path attribute to allow points to be visible beyond the view area
      
      // Create a separate group for grid lines
      const gridGroup = svg.append('g')
        .attr('class', 'grid-group');
      
      // Add horizontal grid lines for reference - IN GRID GROUP, NOT PLOT GROUP
      gridGroup.selectAll('.grid-line')
        .data(yScale.ticks(5))
        .enter()
        .append('line')
        .attr('class', 'grid-line')
        .attr('x1', 0)
        .attr('x2', totalScaledWidth)  // Make sure this extends across the full width
        .attr('y1', d => yScale(d))
        .attr('y2', d => yScale(d))
        .attr('stroke', '#eee')
        .attr('stroke-width', 1);
      
      // Add vertical grid lines for better position reference - IN GRID GROUP
      // Create evenly spaced vertical grid lines across the full data range
      const gridSpacing = Math.ceil((xMax - xMin) / 20); // Increase number of grid lines
      const verticalGridPositions = [];
      
      // Generate grid positions across the entire data range
      for (let pos = xMin; pos <= xMax; pos += gridSpacing) {
        verticalGridPositions.push(pos);
      }
      
      // Add the grid lines to span the full width
      gridGroup.selectAll('.vertical-grid-line')
        .data(verticalGridPositions)
        .enter()
        .append('line')
        .attr('class', 'vertical-grid-line')
        .attr('x1', d => xScale(d))
        .attr('x2', d => xScale(d))
        .attr('y1', 0)
        .attr('y2', innerHeight)
        .attr('stroke', '#f5f5f5')
        .attr('stroke-width', 1);

      // Add a line connecting points to help visualize the trend
      const line = d3.line()
        .x(d => xScale(d.position))
        .y(d => yScale(d.difference))
        .curve(d3.curveMonotoneX);
      
      // Only add the line if there are multiple points
      if (lociPositions.length > 1) {
        plotGroup.append('path')
          .datum(lociPositions)
          .attr('class', 'trend-line')
          .attr('fill', 'none')
          .attr('stroke', 'rgba(75, 192, 192, 0.3)')
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('d', line);
      }
      
      // Add a mask to control point visibility
      svg.append("defs")
        .append("clipPath")
        .attr("id", "visible-area")
        .append("rect")
        .attr("width", innerWidth)
        .attr("height", innerHeight);
      
      // Add circles for each locus - make sure ALL points are rendered
      console.log(`Adding ${lociPositions.length} locus points to chart`);
      
      // Calculate percentage missing for each point and create color scale
      lociPositions.forEach(item => {
        item.percentageMissing = (item.difference / item.totalCount) * 100;
      });
      
      // Create color scale for percentage missing (green to red)
      const percentageColorScale = d3.scaleSequential()
        .domain([0, 100])
        .interpolator(d3.interpolateRdYlGn)
        .clamp(true);
      
      // Create size scale for total allele count
      const maxTotalAlleles = d3.max(lociPositions, d => d.totalCount);
      const minTotalAlleles = d3.min(lociPositions, d => d.totalCount);
      const sizeScale = d3.scaleLinear()
        .domain([minTotalAlleles, maxTotalAlleles])
        .range([4, 15]) // Min and max bubble sizes
        .clamp(true);
      
      // Add tooltip
      const tooltip = d3.select('body')
        .append('div')
        .attr('class', 'd3-tooltip')
        .style('opacity', 0)
        .style('position', 'absolute')
        .style('background-color', 'rgba(255, 255, 255, 0.95)')
        .style('border', '1px solid #ddd')
        .style('border-radius', '4px')
        .style('padding', '6px')
        .style('font-size', '11px')
        .style('pointer-events', 'none')
        .style('z-index', '10000')
        .style('box-shadow', '0 2px 8px rgba(0,0,0,0.2)');
      
      const lociPoints = plotGroup.selectAll('.locus-point')
        .data(lociPositions)
        .enter()
        .append('circle')
        .attr('class', 'locus-point')
        .attr('cx', d => xScale(d.position))
        .attr('cy', d => yScale(d.difference))
        .attr('r', d => sizeScale(d.totalCount)) // Size based on total alleles
        .attr('fill', d => percentageColorScale(100 - d.percentageMissing)) // Color based on percentage missing (inverted for green=good, red=bad)
        .attr('stroke', '#fff')
        .attr('stroke-width', 1)
        .attr('data-position', d => d.position) // Add position as data attribute for debugging
        .style('opacity', d => {
          // Set initial opacity based on position
          const initialViewEnd = Math.min(xMin + viewWindowSize, xMax);
          return (d.position >= xMin && d.position <= initialViewEnd) ? 0.8 : 0.3;
        });

      // Verify that all points have been rendered correctly
      console.log(`Rendered ${lociPoints.size()} locus points out of ${lociPositions.length}`);
      
      // Add event handlers with enhanced tooltip
      lociPoints.on('mouseover', function(event, d) {
          // Highlight the point
          d3.select(this)
            .attr('r', d => sizeScale(d.totalCount) + 2)
            .attr('stroke', '#333')
            .attr('stroke-width', 2);
          
          // Show tooltip
          tooltip.transition()
            .duration(200)
            .style('opacity', 1);
          
          // Enhanced tooltip with all metrics
          tooltip.html(`
            <strong>Locus: ${d.locus}</strong><br/>
            <table style="margin-top:5px;">
              <tr><td>Position:</td><td><b>${d.position.toLocaleString()}</b></td></tr>
              <tr><td>Missing alleles:</td><td><b>${d.difference}</b></td></tr>
              <tr><td>Total alleles:</td><td><b>${d.totalCount}</b></td></tr>
              <tr><td>Program alleles:</td><td><b>${d.programCount}</b></td></tr>
              <tr><td>Missing %:</td><td><b>${d.percentageMissing.toFixed(1)}%</b></td></tr>
              <tr><td>Diversity level:</td><td><b>${d.totalCount >= 10 ? 'High' : d.totalCount >= 5 ? 'Medium' : 'Low'}</b></td></tr>
            </table>
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function(d) {
          // Reset highlight
          d3.select(this)
            .attr('r', d => sizeScale(d.totalCount))
            .attr('stroke', '#fff')
            .attr('stroke-width', 1);
          
          // Hide tooltip
          tooltip.transition()
            .duration(500)
            .style('opacity', 0);
        })
        .on('click', function(event, d) {
          // Show missing alleles for this locus when clicked
          const originalItem = sortedData.find(item => 
            item.formattedLocus === d.locus || item.locus === d.originalLocus);
          
          if (originalItem) {
            showMissingAlleles(originalItem);
          }
        });

      // Create x and y axes
      const xAxis = d3.axisBottom(visibleXScale)
        .tickFormat(d3.format(",d"));
      
      const yAxis = d3.axisLeft(yScale);
      
      // Append axes to SVG
      const xAxisGroup = svg.append('g')
        .attr('class', 'x-axis')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(xAxis);
        
      const yAxisGroup = svg.append('g')
        .attr('class', 'y-axis')
        .call(yAxis);
      
      // Add axis labels
      svg.append('text')
        .attr('class', 'x-axis-label')
        .attr('text-anchor', 'middle')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + 40)
        .style('font-size', '14px')
        .text('Position on Chromosome');
      
      svg.append('text')
        .attr('class', 'y-axis-label')
        .attr('text-anchor', 'middle')
        .attr('transform', `translate(${-40},${innerHeight / 2}) rotate(-90)`)
        .style('font-size', '14px')
        .text('Missing Allele Count');
      
      // Add title with data range information and enhanced description
      svg.append('text')
        .attr('class', 'chart-title')
        .attr('text-anchor', 'middle')
        .attr('x', innerWidth / 2)
        .attr('y', -10)
        .style('font-size', '16px')
        .style('font-weight', 'bold')
        .text(`Missing Alleles on Chromosome ${selectedChromosome.value} (${lociPositions.length} loci)`);
      
      // Add visible position range indicator
      const positionRangeText = svg.append('text')
        .attr('class', 'position-range')
        .attr('text-anchor', 'start')
        .attr('x', 10)
        .attr('y', 20)
        .style('font-size', '12px')
        .style('fill', '#666')
        .text(`Viewing positions ${xMin.toLocaleString()} - ${Math.min(xMin + viewWindowSize, xMax).toLocaleString()}`);
      

      
      // Add scrollbar container for single chromosome - use unique variable name
      const singleScrollContainer = d3.select(d3Container.value)
        .append("div")
        .attr("class", "scrollbar-container")
        .style("position", "absolute")
        .style("bottom", "0px") // Move to very bottom edge
        .style("left", `${margin.left}px`)
        .style("width", `${innerWidth}px`)
        .style("height", "16px") // Match CSS height
        .style("overflow-x", "auto")
        .style("overflow-y", "hidden")
        .style("background", "#f0f0f0")
        .style("border", "1px solid #ccc")
        .style("border-radius", "4px")
        .style("z-index", "10")
        .style("scrollbar-width", "auto") // Force scrollbar visibility
        .style("scrollbar-color", "#666 #f0f0f0"); // Force thumb visibility
      
      // Add content to make the scrollbar work - use unique variable name
      const singleScrollContent = singleScrollContainer
        .append("div")
        .style("width", `${totalScaledWidth}px`)
        .style("height", "14px") // Ensure it has enough height
        .style("background", "linear-gradient(to right, #f0f0f0 0%, #f0f0f0 100%)")
        .style("min-width", `${totalScaledWidth}px`);
      
      // Set initial scroll position to 0
      singleScrollContainer.node().scrollLeft = 0;
      
      // Force scrollbar to be visible immediately
      setTimeout(() => {
        const scrollbarEl = singleScrollContainer.node();
        scrollbarEl.style.scrollbarWidth = 'auto';
        scrollbarEl.style.scrollbarColor = '#666 #f0f0f0';
        // Force a tiny scroll to trigger scrollbar appearance
        scrollbarEl.scrollLeft = 1;
        scrollbarEl.scrollLeft = 0;
      }, 100);
      
      // Focus only on scrollbar functionality - no chart interactions
      const scrollbarElement = singleScrollContainer.node();
      
      // Add mouse wheel scrolling to the scrollbar only
      scrollbarElement.addEventListener('wheel', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        const scrollAmount = event.deltaY * 1.5;
        const currentScroll = this.scrollLeft;
        const maxScroll = totalScaledWidth - innerWidth;
        const newScroll = Math.max(0, Math.min(maxScroll, currentScroll + scrollAmount));
        
        this.scrollLeft = newScroll;
      }, { passive: false });
        
      // Add scroll event listener
      singleScrollContainer.on("scroll", function() {
        const scrollLeft = this.scrollLeft;
        
        // Calculate visible domain based on scroll position
        const visibleDomainStart = d3.scaleLinear()
          .domain([0, totalScaledWidth - innerWidth])
          .range([xMin, xMax - viewWindowSize])(scrollLeft);
          
        const visibleDomainEnd = Math.min(visibleDomainStart + viewWindowSize, xMax);
        
        // Update position range text
        positionRangeText.text(`Viewing positions ${Math.round(visibleDomainStart).toLocaleString()} - ${Math.round(visibleDomainEnd).toLocaleString()}`);
        
        console.log(`Scroll - viewing ${visibleDomainStart.toFixed(0)} to ${visibleDomainEnd.toFixed(0)}`);
        
        // Update visible domain and redraw axis
        visibleXScale.domain([visibleDomainStart, visibleDomainEnd]);
        
        // Update x-axis with formatted numbers and evenly spaced ticks
        const visibleTicks = visibleXScale.ticks(8);
        xAxisGroup.call(
          d3.axisBottom(visibleXScale)
            .tickValues(visibleTicks)
            .tickFormat(d3.format(",d"))
        );
        
        // Update plot position - important to get this right!
        plotGroup.attr("transform", `translate(${-scrollLeft}, 0)`);
        
        // Also update the grid group position to keep grid lines aligned
        gridGroup.attr("transform", `translate(${-scrollLeft}, 0)`);
        
        // Count how many points are in view to verify rendering
        let pointsInView = 0;
        let pointsOutOfView = 0;
        
        // Update point visibility based on current view
        plotGroup.selectAll('.locus-point')
          .each(function(d) {
            const inView = d.position >= visibleDomainStart && d.position <= visibleDomainEnd;
            if (inView) pointsInView++; else pointsOutOfView++;
          })
          .style('opacity', d => 
            (d.position >= visibleDomainStart && d.position <= visibleDomainEnd) ? 1 : 0.2
          );
          
        console.log(`Points in view: ${pointsInView}, outside view: ${pointsOutOfView}`);
      });
      
      // Add a reset button to scroll back to the start
      const singleResetButton = d3.select(d3Container.value)
        .append('button')
        .attr('class', 'reset-scroll-button')
        .style('position', 'absolute')
        .style('top', '10px')
        .style('right', '10px')
        .style('padding', '6px 12px')
        .style('background', 'rgba(255,255,255,0.9)')
        .style('border', '1px solid #ddd')
        .style('border-radius', '4px')
        .style('cursor', 'pointer')
        .style('z-index', '5')
        .text('Reset Position')
        .on('click', () => {
          // Scroll back to the start with animation
          singleScrollContainer.node().scrollTo({
            left: 0,
            behavior: 'smooth'
          });
        });
    }
  } catch (error) {
    console.error("Error creating linear genome view:", error);
  }
}

function showMissingAlleles(data) {
  if (!data || !data.locus) {
    console.error("Invalid data for missing alleles");
    return;
  }
  
  selectedLocus.value = data.locus;
  // Store the formatted locus for display
  const formattedLocus = `${selectedChromosome.value}.${data.locus.split('|')[0]}`;
  
  console.log("Raw data analysis:", {
    originalLocus: data.locus,
    selectedChromosome: selectedChromosome.value,
    rawMissingAllelesFirst3: data.missing_alleles?.slice(0, 3),
    missingAllelesTypes: data.missing_alleles?.slice(0, 3).map(a => typeof a),
    missingAllelesFormats: data.missing_alleles?.slice(0, 3).map(a => ({
      value: a,
      containsPipe: String(a).includes('|'),
      containsDot: String(a).includes('.'),
      parts: String(a).split('|')
    }))
  });
  
  // Check if missing_alleles already contains full AlleleIDs or just the unique parts
  const firstMissingAllele = data.missing_alleles?.[0];
  const alreadyFullFormat = firstMissingAllele && String(firstMissingAllele).includes('|');
  
  console.log("AlleleID format detection:", {
    firstMissingAllele,
    alreadyFullFormat,
    shouldConstructFull: !alreadyFullFormat
  });
  
  if (alreadyFullFormat) {
    // Missing alleles are already in full format
    selectedMissingAlleles.value = Array.isArray(data.missing_alleles) 
      ? data.missing_alleles.map(alleleId => ({ 
          alleleId: String(alleleId), // Use the complete format as alleleId
          locus: formattedLocus 
        }))
      : [];
  } else {
    // Missing alleles are just unique identifiers, need to construct full format
    const locusBase = data.locus.split('|')[0]; // Get the locus part before the pipe
    selectedMissingAlleles.value = Array.isArray(data.missing_alleles) 
      ? data.missing_alleles.map(alleleIdPart => ({ 
          alleleId: `${selectedChromosome.value}.${locusBase}|${alleleIdPart}`, // Construct full AlleleID
          locus: formattedLocus 
        }))
      : [];
  }
    
  console.log("Final processed missing alleles:", {
    count: selectedMissingAlleles.value.length,
    first3: selectedMissingAlleles.value.slice(0, 3),
    sampleAlleleIds: selectedMissingAlleles.value.slice(0, 3).map(item => item.alleleId)
  });
    
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
      // Use the formatted locus that already includes the chromosome
      item.formattedLocus,
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
    link.setAttribute("download", `missing_allele_counts_${selectedSpecies.value}_${selectedChromosome.value}_${new Date().toISOString().split('T')[0]}.csv`);
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
    const headers = ['Locus', 'Allele ID'];
    const rows = selectedMissingAlleles.value.map(item => [item.locus, item.allele]);
    
    const csvContent = 
      "data:text/csv;charset=utf-8," + 
      headers.join(",") + "\n" + 
      rows.map(row => row.join(",")).join("\n");
    
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `missing_alleles_${selectedMissingAlleles.value.length > 0 ? selectedMissingAlleles.value[0].locus : 'unknown'}_${new Date().toISOString().split('T')[0]}.csv`);
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

// New methods for enhanced modal functionality
async function fetchAccessionsForAllele(alleleId) {
  if (alleleAccessions.value[alleleId]) {
    console.log(`Accessions already cached for ${alleleId}:`, alleleAccessions.value[alleleId]);
    return; // Already fetched
  }
  
  loadingAccessions.value[alleleId] = true;
  console.log(`🔍 STARTING ACCESSIONS FETCH for: ${alleleId}`);
  
  try {
    console.log(`Fetching accessions for allele: ${alleleId}, species: ${selectedSpecies.value}`);
    
    // Test with a simple case first - let's see what the format should be
    console.log("AlleleID format analysis:", {
      original: alleleId,
      length: alleleId.length,
      containsPipe: alleleId.includes('|'),
      containsDot: alleleId.includes('.'),
      parts: alleleId.split('|'),
      dotParts: alleleId.split('.')
    });
    
    console.log(`📤 Making API call to /posts/alleleAccessions with payload:`, {
      alleleid: [alleleId]
    });
    
    const response = await axiosInstance.post('/posts/alleleAccessions', {
      alleleid: [alleleId]
    });
    
    console.log(`📥 API Response for ${alleleId}:`, {
      status: response.status,
      statusText: response.statusText,
      data: response.data,
      dataLength: response.data?.length || 0
    });
    
    alleleAccessions.value[alleleId] = response.data || [];
    
    if (response.data && response.data.length === 0) {
      console.warn(`⚠️ No accessions found for allele ${alleleId}. This might indicate a species mismatch or missing data.`);
      
      // Let's try to fetch a sample of working AlleleIDs from the Query section to compare
      try {
        console.log("🧪 Testing with a sample query to compare AlleleID formats...");
        const testResponse = await axiosInstance.post('/posts/alleleDetails', {
          species: selectedSpecies.value,
          page: 1,
          size: 5
        });
        
        if (testResponse.data && testResponse.data.items && testResponse.data.items.length > 0) {
          console.log("✅ Sample working AlleleIDs from Query section:", 
            testResponse.data.items.map(item => ({
              alleleid: item.alleleid,
              species: item.species
            }))
          );
          
          // Test with the first working AlleleID to see if our API call works
          const workingAlleleId = testResponse.data.items[0].alleleid;
          console.log(`🧪 Testing API with known working AlleleID: ${workingAlleleId}`);
          
          const testAccessionsResponse = await axiosInstance.post('/posts/alleleAccessions', {
            alleleid: [workingAlleleId]
          });
          
          console.log(`🧪 Test response for working AlleleID ${workingAlleleId}:`, {
            status: testAccessionsResponse.status,
            data: testAccessionsResponse.data,
            dataLength: testAccessionsResponse.data?.length || 0
          });
        }
      } catch (testError) {
        console.error("❌ Error in test query:", testError);
      }
    } else {
      console.log(`✅ Successfully fetched ${response.data?.length || 0} accessions for ${alleleId}`);
    }
  } catch (error) {
    console.error(`❌ Error fetching accessions for allele ${alleleId}:`, error);
    console.error("Error details:", {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data
    });
    alleleAccessions.value[alleleId] = [];
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: `Failed to fetch accessions for allele ${alleleId}. Please try again.`,
      life: 5000
    });
  } finally {
    loadingAccessions.value[alleleId] = false;
    console.log(`🏁 FINISHED ACCESSIONS FETCH for: ${alleleId}`);
  }
}

function toggleAccessions(rowData) {
  const alleleId = rowData.allele;
  const isExpanded = expandedRows.value.find(row => row.allele === alleleId);
  
  if (!isExpanded) {
    // Expanding - fetch accessions if not already fetched
    fetchAccessionsForAllele(alleleId);
  }
}

function addToQueryList(rowData) {
  const alleleId = rowData.alleleId;
  
  if (isAlreadyInQueryList(alleleId)) {
    toast.add({
      severity: 'warn',
      summary: 'Already Added',
      detail: 'This allele is already in your query list.',
      life: 3000
    });
    return;
  }
  
  // Create a sequence object to add to the store
  // We need to also get the sequence data, so let's make an API call
  fetchSequenceAndAddToQueryList(alleleId);
}

async function fetchSequenceAndAddToQueryList(alleleId) {
  try {
    // Use the alleleDetails endpoint to get full sequence information
    const response = await axiosInstance.post('/posts/alleleDetails', {
      species: selectedSpecies.value,
      globalFilter: alleleId,
      page: 1,
      size: 1
    });
    
    if (response.data && response.data.items && response.data.items.length > 0) {
      const sequence = response.data.items[0];
      
      // Update the query state species to match the current visualization species
      // This ensures the Query component shows the correct species
      store.commit('setQueryState', { species: selectedSpecies.value });
      
      store.commit('setSelectedSequences', [...store.state.selectedSequences, sequence]);
      toast.add({
        severity: 'success',
        summary: 'Added to Query List',
        detail: `Added ${alleleId} to query list successfully! Species set to ${selectedSpecies.value}.`,
        life: 3000
      });
    } else {
      toast.add({
        severity: 'warn',
        summary: 'Not Found',
        detail: `Could not find sequence data for ${alleleId}.`,
        life: 3000
      });
    }
  } catch (error) {
    console.error(`Error fetching sequence for ${alleleId}:`, error);
    toast.add({
      severity: 'error',
      summary: 'Error',
      detail: `Failed to add ${alleleId} to query list. Please try again.`,
      life: 5000
    });
  }
}

function isAlreadyInQueryList(alleleId) {
  return store.state.selectedSequences.some(seq => seq.alleleid === alleleId);
}

function addAllToQueryList() {
  if (selectedMissingAlleles.value.length === 0) {
    toast.add({
      severity: 'warn',
      summary: 'No Data',
      detail: 'No alleles to add to query list.',
      life: 3000
    });
    return;
  }
  
  // Filter out alleles that are already in the query list
  const allelesNotInQuery = selectedMissingAlleles.value.filter(item => {
    return !isAlreadyInQueryList(item.alleleId);
  });
  
  if (allelesNotInQuery.length === 0) {
    toast.add({
      severity: 'info',
      summary: 'Already Added',
      detail: 'All alleles are already in your query list.',
      life: 3000
    });
    return;
  }
  
  // Add each allele that's not already in the query list
  allelesNotInQuery.forEach(item => {
    fetchSequenceAndAddToQueryList(item.alleleId);
  });
  
  toast.add({
    severity: 'info',
    summary: 'Adding to Query List',
    detail: `Adding ${allelesNotInQuery.length} allele(s) to query list...`,
    life: 3000
  });
}

function onRowExpand(event) {
  console.log("🔽 Row expanded event:", event.data);
  console.log(`🔽 Fetching accessions for expanded row with AlleleID: ${event.data.alleleId}`);
  fetchAccessionsForAllele(event.data.alleleId);
}

function onRowCollapse(event) {
  console.log("🔼 Row collapsed event:", event.data);
}

function navigateToQuery() {
  // Navigate to the Query component using the router
  router.push({ name: 'Query' });
  
  toast.add({
    severity: 'info',
    summary: 'Navigation',
    detail: 'Navigating to Query page...',
    life: 2000
  });
}
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
  height: 650px; /* Fixed height for linear genome view */
  margin-top: 2rem;
  margin-bottom: 120px; /* Margin for clearance */
  padding-bottom: 60px; /* Padding for scrollbar space */
}

.chart-container {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: visible;
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

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.table-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #333;
}

/* Legend for genome view */
.genome-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 0.5rem;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.legend-section {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-right: 1rem;
}

.legend-title {
  font-size: 14px;
  font-weight: bold;
  margin: 0;
  color: #333;
}

.size-legend,
.color-legend {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.legend-color {
  width: 16px;
  height: 16px;
  border-radius: 50%;
}

.legend-circle {
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 0 0 1px #ddd;
}

.legend-size-small {
  width: 8px;
  height: 8px;
  background-color: rgba(75, 192, 192, 0.8);
}

.legend-size-medium {
  width: 12px;
  height: 12px;
  background-color: rgba(75, 192, 192, 0.8);
}

.legend-size-large {
  width: 18px;
  height: 18px;
  background-color: rgba(75, 192, 192, 0.8);
}

.legend-green {
  background-color: #4CAF50;
}

.legend-yellow {
  background-color: #FFC107;
}

.legend-red {
  background-color: #F44336;
}

.d3-container {
  width: 100%;
  height: 100%;
  position: relative;
  padding-bottom: 80px; /* Padding to accommodate x-axis, instructions, and scrollbar */
  margin-bottom: 15px;
}

/* D3 Specific Styles */
:deep(.x-axis path),
:deep(.y-axis path),
:deep(.x-axis line),
:deep(.y-axis line) {
  stroke: #ddd;
}

:deep(.x-axis text),
:deep(.y-axis text) {
  font-size: 11px;
  fill: #666;
}

:deep(svg) {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Keep interactive element cursors */
:deep(.locus-point) {
  cursor: pointer !important;
}

:deep(.chr-bar) {
  cursor: pointer !important;
}

/* Prevent text selection during drag */
:deep(.d3-container) {
  user-select: none;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
}

/* Bar chart styles */
:deep(.chr-bar),
:deep(.segment-bar) {
  transition: stroke 0.2s, stroke-width 0.2s;
  cursor: pointer;
}

:deep(.chr-bar:hover),
:deep(.segment-bar:hover) {
  opacity: 0.9;
}

:deep(.value-label) {
  pointer-events: none;
  text-shadow: 0px 0px 2px rgba(255, 255, 255, 0.5);
}

:deep(.loci-count) {
  pointer-events: none;
}

:deep(.summary-text) {
  pointer-events: none;
}

/* Line chart styles for individual chromosome view */
:deep(.trend-line) {
  fill: none;
  stroke: rgba(75, 192, 192, 0.4);
  stroke-width: 1.5;
  stroke-dasharray: 4, 4;
  pointer-events: none;
}

:deep(.locus-point) {
  transition: r 0.2s, stroke 0.2s, stroke-width 0.2s;
  cursor: pointer;
}

:deep(.grid-line) {
  pointer-events: none;
  stroke: #eee;
  stroke-width: 1;
}

:deep(.vertical-grid-line) {
  stroke: #f5f5f5;
  stroke-width: 1;
}

/* D3 tooltip styles */
:deep(.d3-tooltip) {
  font-size: 11px;
  color: #333;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  max-width: 300px;
  white-space: nowrap;
  pointer-events: none;
}

:deep(.d3-tooltip table) {
  border-collapse: collapse;
  margin: 0;
}

:deep(.d3-tooltip td) {
  padding: 2px 6px;
  vertical-align: top;
}

:deep(.d3-tooltip td:first-child) {
  color: #666;
  padding-right: 10px;
}

/* Enhanced scrollbar styles */
:deep(.scrollbar-container) {
  scrollbar-width: auto;
  scrollbar-color: #666 #f0f0f0;
  background: #f0f0f0 !important;
  border: 1px solid #ccc !important;
  border-radius: 4px !important;
  box-shadow: inset 0 0 3px rgba(0,0,0,0.1);
  z-index: 10 !important; 
  height: 16px !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  cursor: pointer;
  transition: border-color 0.2s ease;
  overflow-x: auto;
  overflow-y: hidden;
  scrollbar-gutter: stable;
  -webkit-overflow-scrolling: touch;
}

:deep(.scrollbar-container:hover) {
  border-color: #999;
  scrollbar-color: #444 #e8e8e8;
}

:deep(.scrollbar-container::-webkit-scrollbar) {
  height: 14px;
  background: #f0f0f0;
  -webkit-appearance: none;
  appearance: none;
}

:deep(.scrollbar-container::-webkit-scrollbar-track) {
  background: #f0f0f0;
  border-radius: 3px;
  border: none;
  -webkit-appearance: none;
  appearance: none;
}

:deep(.scrollbar-container::-webkit-scrollbar-thumb) {
  background-color: #666 !important;
  border-radius: 3px;
  border: 1px solid #f0f0f0;
  cursor: grab;
  min-width: 40px;
  transition: background-color 0.2s ease;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.3);
  -webkit-appearance: none;
  appearance: none;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

:deep(.scrollbar-container::-webkit-scrollbar-thumb:hover) {
  background-color: #444 !important;
  border-color: #e8e8e8;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.4);
}

:deep(.scrollbar-container::-webkit-scrollbar-thumb:active) {
  background-color: #222 !important;
  cursor: grabbing;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.2);
}

:deep(.scrollbar-container) {
  scrollbar-width: stable;
}

:deep(.scrollbar-container::-webkit-scrollbar) {
  -webkit-appearance: none !important;
  width: auto !important;
  height: 14px !important;
}

:deep(.scrollbar-container::-webkit-scrollbar-thumb) {
  -webkit-appearance: none !important;
}

:deep(.scroll-instructions) {
  pointer-events: none;
  opacity: 1 !important; 
  visibility: visible !important;
}

:deep(.scroll-instructions-single) {
  pointer-events: none;
  opacity: 1 !important; 
  visibility: visible !important;
}

:deep(.reset-scroll-button) {
  background-color: rgba(255, 255, 255, 0.9);
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 6px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

:deep(.reset-scroll-button:hover) {
  background-color: #f0f0f0;
  border-color: #ccc;
}

:deep(.reset-scroll-button:active) {
  background-color: #e8e8e8;
  transform: translateY(1px);
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
    height: 500px;
  }
  
  .missing-alleles-container {
    overflow-x: auto;
  }
  
  .accession-grid {
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  }
}

/* Color scale legend styles */
:deep(.legend-axis path),
:deep(.legend-axis line) {
  stroke: #aaa;
  shape-rendering: crispEdges;
}

:deep(.legend-axis text) {
  font-size: 10px;
  fill: #666;
}

.missing-alleles-container {
  min-height: 300px;
}

.accession-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.3rem;
  margin-top: 0.3rem;
}

.accession-item {
  padding: 0.3rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  background-color: #f9fafb;
}

.accession-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 0.0625rem;
  font-size: 0.875rem;
}

.accession-details {
  display: flex;
  flex-direction: column;
  gap: 0.0625rem;
}

.program-tag, .project-tag {
  font-size: 0.6875rem;
  padding: 0.0625rem 0.375rem;
  border-radius: 10px;
  background-color: #dbeafe;
  color: #1e40af;
  display: inline-block;
  width: fit-content;
  line-height: 1.2;
}

.project-tag {
  background-color: #ecfdf5;
  color: #065f46;
}
</style>