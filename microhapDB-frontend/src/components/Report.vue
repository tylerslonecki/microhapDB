<template>
  <div class="database-report w-full px-4">
    <Panel header="Database Version Report" class="mb-4">
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
            <div class="flex justify-content-between align-items-center">
              <h3 class="text-xl font-semibold mb-2">Total Alleles by Version</h3>
              <div>
                <Button 
                  icon="pi pi-cog" 
                  class="p-button-text p-button-rounded" 
                  @click="openSettings('totalAlleles')" 
                  v-tooltip="{ value: 'Chart Settings', position: 'left' }" 
                />
                <Button 
                  icon="pi pi-download" 
                  class="p-button-text p-button-rounded" 
                  @click="downloadChart('totalAlleles')" 
                  v-tooltip="{ value: 'Download Chart', position: 'left' }" 
                />
              </div>
            </div>
          </div>
          <div class="p-card-body">
            <Chart 
              ref="totalAllelesChart"
              type="line" 
              :data="totalAllelesChartData" 
              :options="lineChartOptions" 
              class="h-20rem" 
            />
          </div>
        </div>

        <!-- New Alleles Bar Chart -->
        <div class="p-card mb-4" v-if="hasChart">
          <div class="p-card-header">
            <div class="flex justify-content-between align-items-center">
              <h3 class="text-xl font-semibold mb-2">New Alleles by Version</h3>
              <div>
                <Button 
                  icon="pi pi-cog" 
                  class="p-button-text p-button-rounded" 
                  @click="openSettings('newAlleles')" 
                  v-tooltip="{ value: 'Chart Settings', position: 'left' }" 
                />
                <Button 
                  icon="pi pi-download" 
                  class="p-button-text p-button-rounded" 
                  @click="downloadChart('newAlleles')" 
                  v-tooltip="{ value: 'Download Chart', position: 'left' }" 
                />
              </div>
            </div>
          </div>
          <div class="p-card-body">
            <Chart 
              ref="newAllelesChart"
              type="bar" 
              :data="newAllelesChartData" 
              :options="barChartOptions" 
              class="h-20rem" 
            />
          </div>
        </div>

        <!-- Version Details Table -->
        <div class="p-card">
          <div class="p-card-header">
            <div class="flex justify-content-between align-items-center">
              <h3 class="text-xl font-semibold mb-2">Version Details</h3>
              <div>
                <Button 
                  icon="pi pi-download" 
                  class="p-button-text p-button-rounded" 
                  @click="downloadVersionData" 
                  v-tooltip="{ value: 'Download Version Data', position: 'left' }" 
                />
              </div>
            </div>
          </div>
          <div class="p-card-body">
            <DataTable
              :value="versionData"
              :paginator="true"
              :rows="10"
              :rowsPerPageOptions="[5, 10, 20]"
              stripedRows
              class="p-datatable-sm"
              v-model:expandedRows="expandedRows"
              dataKey="version"
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
              <Column header="Files">
                <template #body="slotProps">
                  <span 
                    v-if="slotProps.data.files && slotProps.data.files.length > 0"
                    class="cursor-pointer text-blue-600 hover:text-blue-800 hover:underline flex items-center"
                    @click="toggleExpansion(slotProps.data)"
                  >
                    <i 
                      class="pi mr-2 transition-transform duration-200"
                      :class="isExpanded(slotProps.data) ? 'pi-chevron-down' : 'pi-chevron-right'"
                    ></i>
                    More details
                  </span>
                  <span v-else class="text-gray-500">No files</span>
                </template>
              </Column>
              <template #expansion="slotProps">
                <div class="p-3">
                  <h5>Uploaded Files for Version {{ slotProps.data.version }}</h5>
                  <div v-if="slotProps.data.files && slotProps.data.files.length > 0">
                    <DataTable :value="slotProps.data.files" class="p-datatable-sm">
                      <Column field="file_name" header="File Name">
                        <template #body="fileProps">
                          <span class="font-medium">{{ fileProps.data.file_name }}</span>
                        </template>
                      </Column>
                      <Column field="upload_type" header="Type">
                        <template #body="fileProps">
                          <span class="p-tag" :class="{
                            'p-tag-success': fileProps.data.upload_type === 'madc',
                            'p-tag-info': fileProps.data.upload_type === 'pav',
                            'p-tag-warning': fileProps.data.upload_type === 'supplemental'
                          }">
                            {{ fileProps.data.upload_type.toUpperCase() }}
                          </span>
                        </template>
                      </Column>
                      <Column field="upload_date" header="Upload Date">
                        <template #body="fileProps">
                          {{ formatDate(fileProps.data.upload_date) }}
                        </template>
                      </Column>
                      <Column field="file_size" header="Size">
                        <template #body="fileProps">
                          {{ formatFileSize(fileProps.data.file_size) }}
                        </template>
                      </Column>
                      <Column field="project_name" header="Project">
                        <template #body="fileProps">
                          {{ fileProps.data.project_name || 'N/A' }}
                        </template>
                      </Column>
                      <Column field="uploaded_by" header="Uploaded By">
                        <template #body="fileProps">
                          {{ fileProps.data.uploaded_by || 'Unknown' }}
                        </template>
                      </Column>
                    </DataTable>
                  </div>
                  <div v-else>
                    <p class="text-gray-500">No files were uploaded for this version.</p>
                  </div>
                </div>
              </template>
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
    </Panel>

    <!-- Chart Settings Dialog -->
    <Dialog 
      v-model:visible="settingsDialogVisible" 
      :header="activeChartType === 'totalAlleles' ? 'Total Alleles Chart Settings' : 'New Alleles Chart Settings'" 
      :style="{width: '80vw', maxWidth: '600px'}"
      :modal="true"
      :closable="true"
      :dismissableMask="true"
    >
      <div class="grid">
        <!-- Colors -->
        <div class="col-12 md:col-6 mb-3" v-if="activeChartType === 'totalAlleles'">
          <label class="block mb-2">Line Color</label>
          <ColorPicker v-model="chartSettings.lineColor" format="hex" appendTo="body" class="w-full" />
        </div>
        <div class="col-12 md:col-6 mb-3" v-if="activeChartType === 'newAlleles'">
          <label class="block mb-2">Bar Color</label>
          <ColorPicker v-model="chartSettings.barColor" format="hex" appendTo="body" class="w-full" />
        </div>
        <div class="col-12 md:col-6 mb-3" v-if="activeChartType === 'newAlleles'">
          <label class="block mb-2">Bar Hover Color</label>
          <ColorPicker v-model="chartSettings.barHoverColor" format="hex" appendTo="body" class="w-full" />
        </div>

        <!-- Font Sizes -->
        <div class="col-12 md:col-6 mb-3">
          <label class="block mb-2">Base Font Size</label>
          <InputNumber v-model="chartSettings.fontSize" :min="8" :max="24" class="w-full" />
        </div>
        <div class="col-12 md:col-6 mb-3">
          <label class="block mb-2">Title Font Size</label>
          <InputNumber v-model="chartSettings.titleSize" :min="12" :max="32" class="w-full" />
        </div>

        <!-- Chart Style -->
        <div class="col-12 md:col-6 mb-3" v-if="activeChartType === 'totalAlleles'">
          <label class="block mb-2">Point Size</label>
          <InputNumber v-model="chartSettings.pointSize" :min="2" :max="10" class="w-full" />
        </div>
        <div class="col-12 md:col-6 mb-3">
          <label class="block mb-2">Border Width</label>
          <InputNumber v-model="chartSettings.borderWidth" :min="1" :max="5" class="w-full" />
        </div>

        <!-- Download Settings -->
        <div class="col-12 mb-3">
          <label class="block mb-2">Download Height (px)</label>
          <Slider v-model="chartSettings.chartHeight" :min="200" :max="2000" :step="100" class="w-full" />
          <small class="block mt-1 text-gray-600">Height: {{ chartSettings.chartHeight }}px</small>
        </div>
        <div class="col-12 mb-3">
          <label class="block mb-2">Download Width (px)</label>
          <Slider v-model="chartSettings.chartWidth" :min="400" :max="4000" :step="100" class="w-full" />
          <small class="block mt-1 text-gray-600">Width: {{ chartSettings.chartWidth }}px</small>
        </div>
      </div>
      <template #footer>
        <Button 
          label="Reset to Defaults" 
          icon="pi pi-refresh" 
          class="p-button-text" 
          @click="resetChartSettings" 
        />
      </template>
    </Dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import { axiosLongTimeout } from '../axiosConfig';
import { SPECIES_LIST } from '../utils/speciesConfig';

// Try importing PrimeVue components
let Dropdown, ProgressSpinner, Chart, DataTable, Column, Panel, Button, Tooltip;
let hasChart = false;
let hasProgressSpinner = false;
// Import Chart.js for direct usage in download function
let ChartJS = null;

try {
  Dropdown = require('primevue/dropdown').default;
  DataTable = require('primevue/datatable').default;
  Column = require('primevue/column').default;
  Panel = require('primevue/panel').default;
  Button = require('primevue/button').default;
  Tooltip = require('primevue/tooltip');
} catch (e) {
  console.error('Error loading base PrimeVue components:', e);
}

try {
  Chart = require('primevue/chart').default;
  // Try to get Chart.js from PrimeVue's Chart component
  try {
    ChartJS = require('chart.js/auto');
  } catch (chartJSError) {
    console.error('Could not load Chart.js directly:', chartJSError);
  }
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
    Column,
    Panel,
    Button,
    ColorPicker: require('primevue/colorpicker').default,
    Slider: require('primevue/slider').default,
    InputNumber: require('primevue/inputnumber').default,
    Dialog: require('primevue/dialog').default,
  },
  directives: {
    tooltip: Tooltip
  },
  setup() {
    // State
    const loading = ref(false);
    const error = ref(null);
    const selectedSpecies = ref('');
    const versionData = ref([]);
    const totalAllelesChart = ref(null);
    const newAllelesChart = ref(null);
    
    // Hardcoded species list
    const speciesList = ref(SPECIES_LIST);

    // Chart settings dialog visibility
    const settingsDialogVisible = ref(false);
    const activeChartType = ref('');
    
    // DataTable expanded rows state
    const expandedRows = ref([]);
    
    // Chart customization state
    const chartSettings = ref({
      lineColor: '#2196F3',
      lineBackgroundColor: 'rgba(33, 150, 243, 0.1)',
      barColor: '#4CAF50',
      barHoverColor: '#66BB6A',
      fontSize: 12,
      titleSize: 16,
      chartHeight: 400,
      chartWidth: 800,
      pointSize: 4,
      borderWidth: 2,
    });

    // Helper for color conversion
    const hexToRgba = (color, alpha = 1) => {
      try {
        // If it's already a valid rgba format, return it
        if (typeof color === 'string' && color.startsWith('rgba(')) {
          return color;
        }
        
        // If it's an object from ColorPicker
        if (typeof color === 'object' && color !== null) {
          if (color.r !== undefined && color.g !== undefined && color.b !== undefined) {
            return `rgba(${color.r}, ${color.g}, ${color.b}, ${alpha})`;
          }
        }
        
        // Handle hex string (with or without #)
        let hex = color;
        if (typeof color === 'string') {
          // Ensure the hex has a # prefix
          if (!color.startsWith('#')) {
            hex = '#' + color;
          }
          
          // Remove # for processing
          hex = hex.replace('#', '');
          
          // Validate hex format
          if (!/^[0-9A-Fa-f]{3,6}$/.test(hex)) {
            console.warn('Invalid hex color format:', color);
            return alpha < 1 ? 'rgba(33, 150, 243, ' + alpha + ')' : '#2196F3';
          }
          
          // Convert 3-digit hex to 6-digit
          if (hex.length === 3) {
            hex = hex.split('').map(char => char + char).join('');
          }
          
          // Parse to RGB values
          const r = parseInt(hex.substring(0, 2), 16);
          const g = parseInt(hex.substring(2, 4), 16);
          const b = parseInt(hex.substring(4, 6), 16);
          
          if (isNaN(r) || isNaN(g) || isNaN(b)) {
            console.warn('Invalid color components:', hex);
            return alpha < 1 ? 'rgba(33, 150, 243, ' + alpha + ')' : '#2196F3';
          }
          
          return alpha < 1 ? `rgba(${r}, ${g}, ${b}, ${alpha})` : `#${hex}`;
        }
        
        // Default fallback color
        console.warn('Using default color for:', color);
        return alpha < 1 ? 'rgba(33, 150, 243, ' + alpha + ')' : '#2196F3';
      } catch (err) {
        console.error('Error processing color:', err);
        return alpha < 1 ? 'rgba(33, 150, 243, ' + alpha + ')' : '#2196F3';
      }
    };
    
    // Updated chart data with reactive settings
    const totalAllelesChartData = computed(() => {
      // Get the color, ensure it's a proper hex or rgba
      const lineColor = hexToRgba(chartSettings.value.lineColor);
      const bgColor = hexToRgba(chartSettings.value.lineColor, 0.1);
      
      console.log('Line color:', lineColor, 'Background color:', bgColor);
      
      return {
        labels: versionData.value.map(v => `v${v.version}`),
        datasets: [
          {
            label: 'Total Alleles',
            data: versionData.value.map(v => v.total_alleles),
            fill: true,
            borderColor: lineColor,
            backgroundColor: bgColor,
            borderWidth: chartSettings.value.borderWidth,
            tension: 0.4,
            pointBackgroundColor: lineColor,
            pointBorderColor: '#fff',
            pointBorderWidth: chartSettings.value.borderWidth,
            pointRadius: chartSettings.value.pointSize,
            pointHoverRadius: chartSettings.value.pointSize + 2
          }
        ]
      };
    });

    const newAllelesChartData = computed(() => {
      // Get the color, ensure it's a proper hex or rgba
      const barColor = hexToRgba(chartSettings.value.barColor);
      const hoverColor = chartSettings.value.barHoverColor ? 
        hexToRgba(chartSettings.value.barHoverColor) : 
        hexToRgba(chartSettings.value.barColor, 0.8);
      
      console.log('Bar color:', barColor, 'Hover color:', hoverColor);
      
      return {
        labels: versionData.value.map(v => `v${v.version}`),
        datasets: [
          {
            label: 'New Alleles Added',
            data: versionData.value.map(v => v.new_alleles),
            backgroundColor: barColor,
            borderColor: barColor,
            borderWidth: chartSettings.value.borderWidth,
            borderRadius: 4,
            hoverBackgroundColor: hoverColor
          }
        ]
      };
    });

    // Base chart options that are common to both charts
    const baseChartOptions = computed(() => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false,  // Hide the legend
        },
        title: {
          display: true,
          font: {
            size: chartSettings.value.titleSize,
            weight: 'bold',
            family: "'Helvetica Neue', 'Arial', sans-serif"
          },
          padding: {
            top: 10,
            bottom: 20
          }
        }
      },
      scales: {
        y: {
          beginAtZero: true,
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          },
          ticks: {
            font: {
              size: chartSettings.value.fontSize,
              family: "'Helvetica Neue', 'Arial', sans-serif"
            }
          },
          title: {
            display: true,
            text: 'Number of Alleles',
            font: {
              size: chartSettings.value.fontSize + 2,
              weight: 'bold',
              family: "'Helvetica Neue', 'Arial', sans-serif"
            },
            padding: {
              top: 10,
              bottom: 10
            }
          }
        },
        x: {
          grid: {
            color: 'rgba(0, 0, 0, 0.1)'
          },
          ticks: {
            font: {
              size: chartSettings.value.fontSize,
              family: "'Helvetica Neue', 'Arial', sans-serif"
            }
          },
          title: {
            display: true,
            text: 'Version',
            font: {
              size: chartSettings.value.fontSize + 2,
              weight: 'bold',
              family: "'Helvetica Neue', 'Arial', sans-serif"
            },
            padding: {
              top: 10,
              bottom: 0
            }
          }
        }
      },
      layout: {
        padding: {
          left: 10,
          right: 10
        }
      }
    }));

    // Line chart specific options
    const lineChartOptions = computed(() => ({
      ...baseChartOptions.value
    }));

    // Bar chart specific options with additional bar settings
    const barChartOptions = computed(() => ({
      ...baseChartOptions.value,
      scales: {
        ...baseChartOptions.value.scales,
        x: {
          ...baseChartOptions.value.scales.x,
          offset: true
        }
      },
      layout: {
        padding: {
          left: 25,
          right: 25
        }
      },
      elements: {
        bar: {
          borderWidth: chartSettings.value.borderWidth
        }
      },
      barPercentage: 0.8,
      categoryPercentage: 0.8
    }));

    // Fetch programs on component mount - REMOVED: Not needed since no programs dropdown in UI
    onMounted(async () => {
      console.log('Report component mounted - programs fetching disabled as not needed for current UI');
      // Programs fetching removed since there's no programs dropdown in the template
      // and selectedProgramId is never set by the user interface
    });

    // Fetch version statistics
    const fetchVersionStats = async () => {
      if (!selectedSpecies.value) return;
      
      loading.value = true;
      error.value = null;
      
      try {
        const url = `/posts/allele-count/${selectedSpecies.value}`;
        const response = await axiosLongTimeout.get(url);
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

    // Helper function to format file sizes
    const formatFileSize = (bytes) => {
      if (!bytes || bytes === 0) return 'Unknown';
      
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };

    // Download chart with custom size
    const downloadChart = async (chartType) => {
      try {
        const chart = chartType === 'totalAlleles' ? totalAllelesChart.value : newAllelesChart.value;
        if (!chart) return;
        
        // If Chart.js isn't available directly, try to extract it from the chart component
        if (!ChartJS && chart && chart.chart) {
          // Try to get the Chart constructor from the chart instance
          const chartInstance = chart.chart;
          if (chartInstance && chartInstance.constructor) {
            console.log('Using Chart constructor from chart instance');
            ChartJS = chartInstance.constructor;
          }
        }
        
        // Fallback - try using a different method to generate an image
        if (!ChartJS) {
          console.log('Using fallback image generation method');
          const canvas = chart.$el.querySelector('canvas');
          if (canvas) {
            // Get image data directly from the canvas
            const image = canvas.toDataURL('image/png');
            const a = document.createElement('a');
            a.href = image;
            a.download = `${chartType === 'totalAlleles' ? 'total-alleles' : 'new-alleles'}-${selectedSpecies.value}-chart.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            return;
          } else {
            throw new Error('Could not access chart canvas');
          }
        }
        
        // Create a temporary canvas with desired dimensions
        const tempCanvas = document.createElement('canvas');
        const ctx = tempCanvas.getContext('2d');
        
        // Set custom dimensions for download
        tempCanvas.width = chartSettings.value.chartWidth;
        tempCanvas.height = chartSettings.value.chartHeight;
        
        // Draw the chart on the temporary canvas
        const chartInstance = new ChartJS(ctx, {
          type: chartType === 'totalAlleles' ? 'line' : 'bar',
          data: chartType === 'totalAlleles' ? totalAllelesChartData.value : newAllelesChartData.value,
          options: {
            ...(chartType === 'totalAlleles' ? lineChartOptions.value : barChartOptions.value),
            animation: false,
            responsive: false,
            maintainAspectRatio: false
          }
        });
        
        // Convert to image and download
        const image = tempCanvas.toDataURL('image/png');
        const a = document.createElement('a');
        a.href = image;
        a.download = `${chartType === 'totalAlleles' ? 'total-alleles' : 'new-alleles'}-${selectedSpecies.value}-chart.png`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        
        // Clean up
        chartInstance.destroy();
      } catch (err) {
        console.error('Error downloading chart:', err);
        
        // Try fallback method - get image directly from chart component
        try {
          const chart = chartType === 'totalAlleles' ? totalAllelesChart.value : newAllelesChart.value;
          if (chart && chart.$el) {
            const canvas = chart.$el.querySelector('canvas');
            if (canvas) {
              console.log('Using direct canvas download fallback');
              const image = canvas.toDataURL('image/png');
              const a = document.createElement('a');
              a.href = image;
              a.download = `${chartType === 'totalAlleles' ? 'total-alleles' : 'new-alleles'}-${selectedSpecies.value}-chart.png`;
              document.body.appendChild(a);
              a.click();
              document.body.removeChild(a);
            }
          }
        } catch (fallbackErr) {
          console.error('Fallback download also failed:', fallbackErr);
        }
      }
    };

    // Open settings dialog for specific chart
    const openSettings = (chartType) => {
      activeChartType.value = chartType;
      settingsDialogVisible.value = true;
    };

    // Reset chart settings
    const resetChartSettings = () => {
      const defaultSettings = {
        lineColor: '#2196F3',
        barColor: '#4CAF50',
        barHoverColor: '#66BB6A',
        fontSize: 12,
        titleSize: 16,
        chartHeight: 400,
        chartWidth: 800,
        pointSize: 4,
        borderWidth: 2,
      };
      
      // Only reset settings for the active chart
      if (activeChartType.value === 'totalAlleles') {
        // Reset line chart settings
        chartSettings.value = {
          ...chartSettings.value,
          lineColor: defaultSettings.lineColor,
          fontSize: defaultSettings.fontSize,
          titleSize: defaultSettings.titleSize,
          pointSize: defaultSettings.pointSize,
          borderWidth: defaultSettings.borderWidth,
          chartHeight: defaultSettings.chartHeight,
          chartWidth: defaultSettings.chartWidth
        };
      } else if (activeChartType.value === 'newAlleles') {
        // Reset bar chart settings
        chartSettings.value = {
          ...chartSettings.value,
          barColor: defaultSettings.barColor,
          barHoverColor: defaultSettings.barHoverColor,
          fontSize: defaultSettings.fontSize,
          titleSize: defaultSettings.titleSize,
          borderWidth: defaultSettings.borderWidth,
          chartHeight: defaultSettings.chartHeight,
          chartWidth: defaultSettings.chartWidth
        };
      }
    };

    // Download version data as CSV
    const downloadVersionData = () => {
      try {
        if (!versionData.value || versionData.value.length === 0) {
          console.error('No version data to download');
          return;
        }
        
        // Create CSV content
        let csvContent = 'Version,Date,Program,Total Alleles,New Alleles,Description\n';
        
        versionData.value.forEach(row => {
          const date = formatDate(row.created_at);
          const description = row.description || 'N/A';
          csvContent += `v${row.version},${date},${row.program_name},${row.total_alleles},${row.new_alleles},"${description}"\n`;
        });
        
        // Create and trigger download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${selectedSpecies.value}-version-data.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error('Error downloading version data:', err);
      }
    };

    // Toggle expansion for a specific row
    const toggleExpansion = (rowData) => {
      const currentlyExpanded = expandedRows.value || {};
      const isCurrentlyExpanded = currentlyExpanded[rowData.version];
      
      if (isCurrentlyExpanded) {
        // Remove from expanded rows
        const remaining = { ...currentlyExpanded };
        delete remaining[rowData.version];
        expandedRows.value = remaining;
      } else {
        // Add to expanded rows
        expandedRows.value = {
          ...currentlyExpanded,
          [rowData.version]: true
        };
      }
    };

    // Check if a row is expanded
    const isExpanded = (rowData) => {
      return !!(expandedRows.value && expandedRows.value[rowData.version]);
    };

    return {
      // State
      loading,
      error,
      selectedSpecies,
      versionData,
      speciesList,
      totalAllelesChart,
      newAllelesChart,
      
      // Feature flags
      hasChart,
      hasProgressSpinner,
      
      // Methods
      fetchVersionStats,
      formatDate,
      formatNumber,
      downloadChart,
      downloadVersionData,
      
      // Chart data
      totalAllelesChartData,
      newAllelesChartData,
      lineChartOptions,
      barChartOptions,
      
      // Chart customization
      chartSettings,
      settingsDialogVisible,
      activeChartType,
      openSettings,
      resetChartSettings,
      
      // DataTable expanded rows state
      expandedRows,
      
      // Helper function to format file sizes
      formatFileSize,
      
      // Toggle expansion for a specific row
      toggleExpansion,
      
      // Check if a row is expanded
      isExpanded,
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

/* Add padding to card headers */
.p-card-header {
  padding: 1rem 1rem 0.5rem 1rem;
}

/* Ensure card titles don't get cut off */
.p-card-header h3 {
  margin-top: 0.5rem;
}
</style>