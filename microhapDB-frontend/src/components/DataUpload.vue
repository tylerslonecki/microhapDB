<template>
  <div class="data-upload-container">
    <!-- Global Confirmation Dialog -->
    <ConfirmDialog />

    <!-- Duplicate Warning Modal for MADC Upload (duplicates found) -->
    <Dialog v-model:visible="showDuplicateModal" :modal="true" :closable="false" :style="{ width: '600px' }">
      <div class="modal-header">
        <span class="warning-icon">
          <i class="pi pi-exclamation-triangle" style="font-size: 2em; margin-right: 8px;"></i>Warning
        </span>
        <span class="warning-text">Duplicate AlleleIDs Found</span>
      </div>
      <p class="warning-details" v-if="previewResponse">
        {{ previewResponse.duplicate_count }} out of {{ previewResponse.total_count }} alleleIDs in this file already exist in this database.
      </p>
      <p v-if="duplicateList.length">
        Sample of duplicates:<br>
        <span v-for="(allele, index) in duplicateList.slice(0, 5)" :key="index">
          {{ allele }}<span v-if="index !== Math.min(duplicateList.length, 5) - 1">, </span>
        </span>
      </p>
      <div class="download-container">
        <Button label="Download Duplicates CSV" icon="pi pi-download" @click="downloadDuplicates" />
      </div>
      <div>
        <p class="warning-message">
          Upload cannot proceed with duplicate alleleIDs. Please remove the duplicates from your file and try again.
        </p>
      </div>
      <div class="dialog-footer">
        <Button label="Close" icon="pi pi-times" class="p-button-primary" @click="cancelUpload" />
      </div>
    </Dialog>

    <!-- No Duplicates Found Modal for MADC Upload -->
    <Dialog v-model:visible="showNoDuplicateModal" :modal="true" :closable="false" :style="{ width: '400px' }">
      <div class="modal-header">
        <span class="success-icon">✓</span>
        <span class="success-text">No Duplicate AlleleIDs Found</span>
      </div>
      <p class="success-details" v-if="previewResponse">
        0 out of {{ previewResponse.total_count }} alleleIDs in this file already exist in this database.
      </p>
      <div class="dialog-footer">
        <Button label="Cancel" icon="pi pi-times" class="p-button-danger" @click="cancelNoDuplicate" />
        <Button label="Submit Upload" icon="pi pi-check" @click="commitMadcData" autoFocus />
      </div>
    </Dialog>

    <TabView class="custom-tabview">
      <!-- MADC Upload Tab -->
      <TabPanel header="MADC Upload" class="custom-tabpanel">
        <Panel header="MADC Upload">
          <div class="upload-section">
            <div class="two-column-layout">
              <!-- Left Column: Form Elements -->
              <div class="form-column">
                <!-- Species Database Dropdown -->
                <div class="dropdown-container">
                  <label for="pipelineSelectMadc" class="pipeline-label">Please select a Species Database</label>
                  <Dropdown 
                    id="pipelineSelectMadc"
                    v-model="selectedPipelineMadc" 
                    :options="pipelineOptions" 
                    optionLabel="label" 
                    optionValue="value" 
                    placeholder="Please select one"
                    class="w-full"
                  />
                </div>

                <!-- Program Dropdown with Add New Option -->
                <div class="dropdown-container" v-if="selectedPipelineMadc">
                  <label for="programSelectMadc" class="program-label">Program Name</label>
                  <div class="dropdown-with-loading">
                    <Dropdown
                      id="programSelectMadc"
                      v-model="selectedProgramMadc"
                      :options="programOptionsMadc"
                      optionLabel="name"
                      optionValue="value"
                      placeholder="Select a program"
                      class="w-full"
                      :loading="loadingStates.programsMadc"
                      :disabled="loadingStates.programsMadc"
                    />
                    <small v-if="loadingStates.programsMadc" class="loading-text">
                      <i class="pi pi-spin pi-spinner"></i> Loading programs...
                    </small>
                  </div>
                  <!-- Input field for new program name -->
                  <div v-if="selectedProgramMadc === 'new'" class="new-program-input">
                    <label for="newProgramNameMadc" class="new-input-label">Enter new program name:</label>
                    <input
                      id="newProgramNameMadc"
                      v-model="newProgramNameMadc"
                      type="text"
                      placeholder="Enter program name"
                      class="p-inputtext p-component w-full"
                      @input="validateProgramName"
                    />
                    <small v-if="programNameError" class="error-text">{{ programNameError }}</small>
                  </div>
                </div>

                <!-- Project Dropdown with Add New Option -->
                <div class="dropdown-container" v-if="selectedPipelineMadc && (selectedProgramMadc && selectedProgramMadc !== 'new') || (selectedProgramMadc === 'new' && newProgramNameMadc.trim())">
                  <label for="projectSelectMadc" class="project-label">Project Name</label>
                  <div class="dropdown-with-loading">
                    <Dropdown
                      id="projectSelectMadc"
                      v-model="selectedProjectMadc"
                      :options="projectOptionsMadc"
                      optionLabel="name"
                      optionValue="value"
                      placeholder="Select a project"
                      class="w-full"
                      :loading="loadingStates.projectsMadc"
                      :disabled="loadingStates.projectsMadc"
                    />
                    <small v-if="loadingStates.projectsMadc" class="loading-text">
                      <i class="pi pi-spin pi-spinner"></i> Loading projects...
                    </small>
                  </div>
                  <!-- Input field for new project name -->
                  <div v-if="selectedProjectMadc === 'new'" class="new-project-input">
                    <label for="newProjectNameMadc" class="new-input-label">Enter new project name:</label>
                    <input
                      id="newProjectNameMadc"
                      v-model="newProjectNameMadc"
                      type="text"
                      placeholder="Enter project name"
                      class="p-inputtext p-component w-full"
                      @input="validateProjectName"
                    />
                    <small v-if="projectNameError" class="error-text">{{ projectNameError }}</small>
                  </div>
                </div>
                <div v-else-if="selectedPipelineMadc && !selectedProgramMadc">
                  <p>Please select a program first</p>
                </div>
                <div v-else-if="selectedPipelineMadc && selectedProgramMadc === 'new' && !newProgramNameMadc.trim()">
                  <p>Please enter a program name first</p>
                </div>
              </div>

              <!-- Version Column Template (replace this in all three tabs) -->
              <div class="version-column">
                <div class="version-info-container" v-if="selectedPipelineMadc && databaseVersions[selectedPipelineMadc] && !loadingStates.versionMadc">
                  <div class="version-info-text">
                    <i class="pi pi-database"></i>
                    <span>Current {{ capitalizeFirst(selectedPipelineMadc) }} Database</span>
                    <span class="version-number">v{{ databaseVersions[selectedPipelineMadc].version }}</span>
                  </div>
                </div>
                <div class="version-info-container" v-else-if="selectedPipelineMadc && loadingStates.versionMadc">
                  <div class="version-info-text loading">
                    <i class="pi pi-spin pi-spinner"></i>
                    <span>Loading database version...</span>
                  </div>
                </div>
                <div class="version-info-container error" v-else-if="selectedPipelineMadc && databaseVersions[selectedPipelineMadc] === null">
                  <div class="version-info-text error">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span>Unable to load database version</span>
                    <small>Please check your connection</small>
                  </div>
                </div>
              </div>
            </div>
          </div>

            <!-- File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectMadc"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <!-- Button now triggers the preview check before committing -->
              <Button 
                label="Preview Upload" 
                icon="pi pi-upload" 
                @click="checkAndSubmitMadcData" 
                class="upload-button"
              />
              <p v-if="uploadMessageMadc" class="upload-message">
                <i class="pi pi-exclamation-circle" style="font-size: 2em; margin-right: 8px;"></i>
                {{ uploadMessageMadc }}
              </p>
            </div>
        

          <!-- Job Status Table for MADC Uploads -->
          <div class="job-status-section">
            <DataTable 
              :value="jobsMadc" 
              :responsiveLayout="'scroll'" 
              class="custom-datatable"
              showGridlines 
              stripedRows
            >
              <template #header>
                <span class="table-header">MADC Upload Job Status</span>
              </template>
              <Column field="file_name" header="File">
                <template #body="slotProps">
                  <span>{{ slotProps.data.file_name }}</span>
                </template>
              </Column>
              <Column field="status" header="Status">
                <template #body="slotProps">
                  <span>{{ slotProps.data.status }}</span>
                </template>
              </Column>
            </DataTable>
          </div>
        </Panel>
      </TabPanel>

      <!-- PAV Upload Tab -->
      <TabPanel header="Presence-Absence Upload" class="custom-tabpanel">
        <Panel header="Presence-Absence Upload">
          <div class="upload-section">
            <div class="two-column-layout">
              <!-- Left Column: Form Elements -->
              <div class="form-column">
                <div class="dropdown-container">
                  <label for="pipelineSelectPav" class="pipeline-label">Please select a Species Database</label>
                  <Dropdown 
                    id="pipelineSelectPav"
                    v-model="selectedPipelinePav" 
                    :options="pipelineOptions" 
                    optionLabel="label" 
                    optionValue="value" 
                    placeholder="Please select one"
                    class="w-full"
                  />
                </div>

                <!-- Program Dropdown for PAV -->
                <div class="dropdown-container" v-if="selectedPipelinePav">
                  <label for="programSelectPav" class="program-label">Program Name</label>
                  <div class="dropdown-with-loading">
                    <Dropdown
                      id="programSelectPav"
                      v-model="selectedProgramPav"
                      :options="programOptionsPav"
                      optionLabel="name"
                      optionValue="value"
                      placeholder="Select a program"
                      class="w-full"
                      :loading="loadingStates.programsPav"
                      :disabled="loadingStates.programsPav"
                    />
                    <small v-if="loadingStates.programsPav" class="loading-text">
                      <i class="pi pi-spin pi-spinner"></i> Loading programs...
                    </small>
                  </div>
                </div>

                <!-- Version Column for PAV -->
                <div class="version-column">
                  <div class="version-info-container" v-if="selectedPipelinePav && databaseVersions[selectedPipelinePav] && !loadingStates.versionPav">
                    <div class="version-info-text">
                      <i class="pi pi-database"></i>
                      <span>Current {{ capitalizeFirst(selectedPipelinePav) }} Database</span>
                      <span class="version-number">v{{ databaseVersions[selectedPipelinePav].version }}</span>
                    </div>
                  </div>
                  <div class="version-info-container" v-else-if="selectedPipelinePav && loadingStates.versionPav">
                    <div class="version-info-text loading">
                      <i class="pi pi-spin pi-spinner"></i>
                      <span>Loading database version...</span>
                    </div>
                  </div>
                  <div class="version-info-container error" v-else-if="selectedPipelinePav && databaseVersions[selectedPipelinePav] === null">
                    <div class="version-info-text error">
                      <i class="pi pi-exclamation-triangle"></i>
                      <span>Unable to load database version</span>
                      <small>Please check your connection</small>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectPav"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <Button 
                label="Submit Presence-Absence Job" 
                icon="pi pi-upload" 
                @click="confirmSubmitPavData" 
                class="upload-button"
              />
              <p v-if="uploadMessagePav" class="upload-message">
                <i class="pi pi-exclamation-circle" style="font-size: 2em; margin-right: 8px;"></i>
                {{ uploadMessagePav }}
              </p>
            </div>
          </div>
          <div class="job-status-section">
            <DataTable 
              :value="jobsPav" 
              :responsiveLayout="'scroll'" 
              class="custom-datatable"
              showGridlines 
              stripedRows
            >
              <template #header>
                <span class="table-header">Presence-Absence Upload Job Status</span>
              </template>
              <Column field="file_name" header="File">
                <template #body="slotProps">
                  <span>{{ slotProps.data.file_name }}</span>
                </template>
              </Column>
              <Column field="status" header="Status">
                <template #body="slotProps">
                  <span>{{ slotProps.data.status }}</span>
                </template>
              </Column>
            </DataTable>
          </div>
        </Panel>
      </TabPanel>

      <!-- Supplemental Upload Tab -->
      <TabPanel header="Supplemental Upload" class="custom-tabpanel">
        <Panel header="Supplemental Upload">
          <div class="upload-section">
            <div class="two-column-layout">
              <!-- Left Column: Form Elements -->
              <div class="form-column">
                <div class="dropdown-container">
                  <label for="pipelineSelectSupplemental" class="pipeline-label">Please select a Species Database</label>
                  <Dropdown 
                    id="pipelineSelectSupplemental"
                    v-model="selectedPipelineSupplemental" 
                    :options="pipelineOptions" 
                    optionLabel="label" 
                    optionValue="value" 
                    placeholder="Please select one"
                    class="w-full"
                  />
                </div>
              </div>

              <!-- Version Column for Supplemental -->
              <div class="version-column">
                <div class="version-info-container" v-if="selectedPipelineSupplemental && databaseVersions[selectedPipelineSupplemental] && !loadingStates.versionSupplemental">
                  <div class="version-info-text">
                    <i class="pi pi-database"></i>
                    <span>Current {{ capitalizeFirst(selectedPipelineSupplemental) }} Database</span>
                    <span class="version-number">v{{ databaseVersions[selectedPipelineSupplemental].version }}</span>
                  </div>
                </div>
                <div class="version-info-container" v-else-if="selectedPipelineSupplemental && loadingStates.versionSupplemental">
                  <div class="version-info-text loading">
                    <i class="pi pi-spin pi-spinner"></i>
                    <span>Loading database version...</span>
                  </div>
                </div>
                <div class="version-info-container error" v-else-if="selectedPipelineSupplemental && databaseVersions[selectedPipelineSupplemental] === null">
                  <div class="version-info-text error">
                    <i class="pi pi-exclamation-triangle"></i>
                    <span>Unable to load database version</span>
                    <small>Please check your connection</small>
                  </div>
                </div>
              </div>
            </div>

            <!-- File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectSupplemental"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <Button 
                label="Submit Supplemental Job" 
                icon="pi pi-upload" 
                @click="confirmSubmitSupplementalData" 
                class="upload-button"
              />
              <p v-if="uploadMessageSupplemental" class="upload-message">
                <i class="pi pi-exclamation-circle" style="font-size: 2em; margin-right: 8px;"></i>
                {{ uploadMessageSupplemental }}
              </p>
            </div>
          </div>
          <div class="job-status-section">
            <DataTable 
              :value="jobsSupplemental" 
              :responsiveLayout="'scroll'" 
              class="custom-datatable"
              showGridlines 
              stripedRows
            >
              <template #header>
                <span class="table-header">Supplemental Upload Job Status</span>
              </template>
              <Column field="file_name" header="File">
                <template #body="slotProps">
                  <span>{{ slotProps.data.file_name }}</span>
                </template>
              </Column>
              <Column field="status" header="Status">
                <template #body="slotProps">
                  <span>{{ slotProps.data.status }}</span>
                </template>
              </Column>
            </DataTable>
          </div>
        </Panel>
      </TabPanel>
    </TabView>
  </div>
</template>

<script>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import axiosInstance, { axiosLongTimeout } from '../axiosConfig';
import { mapGetters, mapActions } from 'vuex';
import Dropdown from 'primevue/dropdown';
import FileUpload from 'primevue/fileupload';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Panel from 'primevue/panel';
import ConfirmDialog from 'primevue/confirmdialog';
import Dialog from 'primevue/dialog';
import { SUPPORTED_SPECIES } from '../utils/speciesConfig';

export default {
  name: 'DataUpload',
  components: {
    Dropdown,
    FileUpload,
    Button,
    DataTable,
    Column,
    TabView,
    TabPanel,
    Panel,
    ConfirmDialog,
    Dialog,
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin']),
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
  },
  setup() {
    // Shared state
    const pipelineOptions = ref(SUPPORTED_SPECIES);

    // Program and Project options for Dropdowns
    const programOptionsMadc = ref([]);
    const programOptionsPav = ref([]);
    const projectOptionsMadc = ref([]);

    // New name inputs and validation
    const newProgramNameMadc = ref("");
    const newProjectNameMadc = ref("");
    const programNameError = ref("");
    const projectNameError = ref("");

    // MADC Upload state
    const selectedFilesMadc = ref([]);
    const selectedPipelineMadc = ref("");
    const selectedProgramMadc = ref("");
    const selectedProjectMadc = ref("");
    const uploadMessageMadc = ref(null);
    const jobsMadc = ref([]);

    // PAV Upload state
    const selectedFilesPav = ref([]);
    const selectedPipelinePav = ref("");
    const selectedProgramPav = ref("");
    const uploadMessagePav = ref(null);
    const jobsPav = ref([]);

    // Supplemental Upload state
    const selectedFilesSupplemental = ref([]);
    const selectedPipelineSupplemental = ref("");
    const uploadMessageSupplemental = ref(null);
    const jobsSupplemental = ref([]);

    // Duplicate preview state for MADC
    const showDuplicateModal = ref(false);
    const showNoDuplicateModal = ref(false);
    const duplicateList = ref([]);
    const previewResponse = ref(null);
    const loadingPreview = ref(false);

    // State for database versions
    const databaseVersions = ref({});

    // Request cancellation and debouncing state
    const activeRequests = ref(new Map());
    const debounceTimeouts = ref(new Map());
    
    // Loading states for better UX
    const loadingStates = ref({
      programsMadc: false,
      programsPav: false,
      projectsMadc: false,
      versionMadc: false,
      versionPav: false,
      versionSupplemental: false
    });

    // Helper function to cancel active request
    const cancelActiveRequest = (key) => {
      const controller = activeRequests.value.get(key);
      if (controller) {
        controller.abort();
        activeRequests.value.delete(key);
        console.log(`Cancelled request: ${key}`);
      }
    };

    // Helper function to clear debounce timeout
    const clearDebounceTimeout = (key) => {
      const timeout = debounceTimeouts.value.get(key);
      if (timeout) {
        clearTimeout(timeout);
        debounceTimeouts.value.delete(key);
      }
    };

    // Debounced function wrapper
    const debounce = (func, delay, key) => {
      return (...args) => {
        clearDebounceTimeout(key);
        const timeout = setTimeout(() => {
          func.apply(this, args);
          debounceTimeouts.value.delete(key);
        }, delay);
        debounceTimeouts.value.set(key, timeout);
      };
    };

    // Enhanced fetchProgramsBySpecies with cancellation and retry
    const fetchProgramsBySpecies = async (species, target = 'madc') => {
      if (!species) return;
      
      const requestKey = `programs-${species}-${target}`;
      const loadingKey = target === 'madc' ? 'programsMadc' : 'programsPav';
      
      // Set loading state
      loadingStates.value[loadingKey] = true;
      
      // Cancel any existing request for this species/target
      cancelActiveRequest(requestKey);
      
      // Create new AbortController
      const controller = new AbortController();
      activeRequests.value.set(requestKey, controller);
      
      let retries = 2;
      let delay = 1000; // Start with 1 second delay
      
      while (retries >= 0) {
        try {
          console.log(`Fetching programs for ${species} (${target}), ${retries} retries left`);
          
          const response = await axiosLongTimeout.get(`/posts/programs/by_species/${species}`, {
            signal: controller.signal,
            timeout: 20000 // 20 second timeout for this specific request
          });
          
          const fetchedPrograms = response.data.programs || [];
          
          const mappedPrograms = fetchedPrograms.map((prog) => ({
            name: prog.name,
            value: prog.name
          }));
          
          // Only add "Add new program" option for MADC uploads
          if (target === 'madc') {
            mappedPrograms.push({ name: "Add new program", value: "new" });
          }
          
          if (target === 'madc') {
            programOptionsMadc.value = mappedPrograms;
          } else if (target === 'pav') {
            programOptionsPav.value = mappedPrograms;
          }
          
          // Clean up successful request
          activeRequests.value.delete(requestKey);
          loadingStates.value[loadingKey] = false;
          return mappedPrograms;
          
        } catch (error) {
          if (error.name === 'AbortError') {
            console.log(`Request cancelled: ${requestKey}`);
            loadingStates.value[loadingKey] = false;
            return;
          }
          
          console.error(`Error fetching programs for ${species} (attempt ${3 - retries}/3):`, error.message);
          
          if (retries > 0) {
            // Wait before retrying
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2; // Exponential backoff
            retries--;
          } else {
            // Final fallback - provide default options
            let defaultOptions = [];
            
            // Only add "Add new program" option for MADC uploads
            if (target === 'madc') {
              defaultOptions = [{ name: "Add new program", value: "new" }];
            }
            
            if (target === 'madc') {
              programOptionsMadc.value = defaultOptions;
            } else if (target === 'pav') {
              programOptionsPav.value = defaultOptions;
            }
            
            // Clean up failed request
            activeRequests.value.delete(requestKey);
            loadingStates.value[loadingKey] = false;
            return defaultOptions;
          }
        }
      }
    };

    // Enhanced fetchProjectsByProgram with cancellation and retry
    const fetchProjectsByProgram = async (programName) => {
      if (!programName) {
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        return;
      }
      
      const requestKey = `projects-${programName}`;
      
      // Set loading state
      loadingStates.value.projectsMadc = true;
      
      // Cancel any existing request for this program
      cancelActiveRequest(requestKey);
      
      // Create new AbortController
      const controller = new AbortController();
      activeRequests.value.set(requestKey, controller);
      
      let retries = 2;
      let delay = 1000;
      
      while (retries >= 0) {
        try {
          console.log(`Fetching projects for ${programName}, ${retries} retries left`);
          
          const response = await axiosLongTimeout.get(`/posts/projects/by_program_name/${encodeURIComponent(programName)}`, {
            signal: controller.signal,
            timeout: 20000
          });
          
          const fetchedProjects = response.data || [];
          
          const mappedProjects = fetchedProjects.map(project => ({
            name: project.name,
            value: project.name
          }));
          
          // Add "Add new project" option at the end
          mappedProjects.push({ name: "Add new project", value: "new" });
          
          projectOptionsMadc.value = mappedProjects;
          
          // Clean up successful request
          activeRequests.value.delete(requestKey);
          loadingStates.value.projectsMadc = false;
          return mappedProjects;
          
        } catch (error) {
          if (error.name === 'AbortError') {
            console.log(`Request cancelled: ${requestKey}`);
            loadingStates.value.projectsMadc = false;
            return;
          }
          
          console.error(`Error fetching projects for program ${programName} (attempt ${3 - retries}/3):`, error.message);
          
          if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2;
            retries--;
          } else {
            projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
            activeRequests.value.delete(requestKey);
            loadingStates.value.projectsMadc = false;
            return [{ name: "Add new project", value: "new" }];
          }
        }
      }
    };

    // Enhanced fetchDatabaseVersion with cancellation and retry
    const fetchDatabaseVersion = async (species) => {
      if (!species) return;
      
      const requestKey = `version-${species}`;
      
      // Determine which loading state to use based on which pipeline is being fetched
      let loadingKey = 'versionMadc'; // default
      if (selectedPipelinePav.value === species) {
        loadingKey = 'versionPav';
      } else if (selectedPipelineSupplemental.value === species) {
        loadingKey = 'versionSupplemental';
      }
      
      // Set loading state
      loadingStates.value[loadingKey] = true;
      
      // Cancel any existing request for this species
      cancelActiveRequest(requestKey);
      
      // Create new AbortController
      const controller = new AbortController();
      activeRequests.value.set(requestKey, controller);
      
      let retries = 2;
      let delay = 1000;
      
      while (retries >= 0) {
        try {
          console.log(`Fetching database version for ${species}, ${retries} retries left`);
          
          const response = await axiosLongTimeout.get(`/posts/database_version/${species}`, {
            signal: controller.signal,
            timeout: 15000 // 15 second timeout for version info
          });
          
          databaseVersions.value[species] = response.data;
          
          // Clean up successful request
          activeRequests.value.delete(requestKey);
          loadingStates.value[loadingKey] = false;
          return response.data;
          
        } catch (error) {
          if (error.name === 'AbortError') {
            console.log(`Request cancelled: ${requestKey}`);
            loadingStates.value[loadingKey] = false;
            return;
          }
          
          console.error(`Error fetching database version for ${species} (attempt ${3 - retries}/3):`, error.message);
          
          if (retries > 0) {
            await new Promise(resolve => setTimeout(resolve, delay));
            delay *= 2;
            retries--;
          } else {
            databaseVersions.value[species] = null;
            activeRequests.value.delete(requestKey);
            loadingStates.value[loadingKey] = false;
            return null;
          }
        }
      }
    };

    // Create debounced versions of fetch functions
    const debouncedFetchPrograms = debounce(fetchProgramsBySpecies, 300, 'programs');
    const debouncedFetchVersion = debounce(fetchDatabaseVersion, 300, 'version');

    // Validation methods
    const validateProgramName = () => {
      const name = newProgramNameMadc.value.trim();
      if (!name) {
        programNameError.value = "Program name is required";
        return false;
      }
      if (name.length < 2) {
        programNameError.value = "Program name must be at least 2 characters";
        return false;
      }
      programNameError.value = "";
      return true;
    };

    const validateProjectName = () => {
      const name = newProjectNameMadc.value.trim();
      if (!name) {
        projectNameError.value = "Project name is required";
        return false;
      }
      if (name.length < 2) {
        projectNameError.value = "Project name must be at least 2 characters";
        return false;
      }
      projectNameError.value = "";
      return true;
    };

    // File selection handlers
    const handleFileSelectMadc = (event) => {
      selectedFilesMadc.value = event.files;
      console.log('Selected files (MADC):', selectedFilesMadc.value);
    };
    
    const handleFileSelectPav = (event) => {
      selectedFilesPav.value = event.files;
      console.log('Selected files (PAV):', selectedFilesPav.value);
    };
    
    const handleFileSelectSupplemental = (event) => {
      selectedFilesSupplemental.value = event.files;
      console.log('Selected files (Supplemental):', selectedFilesSupplemental.value);
    };

    // Simplified checkAndSubmitMadcData
    const checkAndSubmitMadcData = async () => {
      // Validate required fields
      if (!selectedPipelineMadc.value) {
        uploadMessageMadc.value = "Please select a species database.";
        return;
      }

      // Get the actual program name
      let programName = selectedProgramMadc.value;
      if (selectedProgramMadc.value === 'new') {
        if (!validateProgramName()) {
          uploadMessageMadc.value = "Please enter a valid program name.";
          return;
        }
        programName = newProgramNameMadc.value.trim();
      }

      // Get the actual project name
      let projectName = selectedProjectMadc.value;
      if (selectedProjectMadc.value === 'new') {
        if (!validateProjectName()) {
          uploadMessageMadc.value = "Please enter a valid project name.";
          return;
        }
        projectName = newProjectNameMadc.value.trim();
      }

      if (!programName || !projectName) {
        uploadMessageMadc.value = "Please select or enter both program and project names.";
        return;
      }

      if (!selectedFilesMadc.value || selectedFilesMadc.value.length === 0) {
        uploadMessageMadc.value = "Please select a file to upload.";
        return;
      }

      // Proceed with duplicate check and upload
      await performDuplicateCheck();
    };

    // Perform duplicate check
    const performDuplicateCheck = async () => {
      uploadMessageMadc.value = "Analyzing file for duplicates…";
      loadingPreview.value = true;
      
      const fd = new FormData();
      selectedFilesMadc.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineMadc.value);
      
      try {
        const response = await axiosLongTimeout.post("/posts/upload/preview", fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 30000 // 30 seconds for file processing
        });
        
        console.log("Preview response:", response.data);
        previewResponse.value = response.data;
        loadingPreview.value = false;
        
        if (response.data.duplicate_count > 0) {
          duplicateList.value = response.data.duplicates;
          showDuplicateModal.value = true;
          uploadMessageMadc.value = null;
        } else {
          // If no duplicates are found, show the no-duplicates modal
          showNoDuplicateModal.value = true;
          uploadMessageMadc.value = null;
        }
      } catch (error) {
        loadingPreview.value = false;
        uploadMessageMadc.value = "Error during preview: " + (error.response?.data?.detail || error.message);
      }
    };

    // Commit MADC data after duplicate check
    const commitMadcData = async () => {
      // Get the actual names
      let programName = selectedProgramMadc.value;
      if (selectedProgramMadc.value === 'new') {
        programName = newProgramNameMadc.value.trim();
      }

      let projectName = selectedProjectMadc.value;
      if (selectedProjectMadc.value === 'new') {
        projectName = newProjectNameMadc.value.trim();
      }

      const fd = new FormData();
      selectedFilesMadc.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineMadc.value);
      fd.append("program_name", programName);
      fd.append("project_name", projectName);

      try {
        uploadMessageMadc.value = "Uploading file...";
        await axiosLongTimeout.post("/posts/upload/", fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000 // 60 seconds for actual upload
        });
        uploadMessageMadc.value = "Upload initiated successfully!";
        showNoDuplicateModal.value = false;
        
        // Clear the form
        selectedFilesMadc.value = [];
        selectedProgramMadc.value = "";
        selectedProjectMadc.value = "";
        newProgramNameMadc.value = "";
        newProjectNameMadc.value = "";
        
      } catch (error) {
        console.error("Error uploading file:", error);
        uploadMessageMadc.value = "Error uploading file: " + (error.response?.data?.detail || error.message);
        showNoDuplicateModal.value = false;
      }
    };

    // PAV upload methods
    const confirmSubmitPavData = async () => {
      if (!selectedPipelinePav.value) {
        uploadMessagePav.value = "Please select a species database.";
        return;
      }

      if (!selectedProgramPav.value) {
        uploadMessagePav.value = "Please select a program.";
        return;
      }

      if (!selectedFilesPav.value || selectedFilesPav.value.length === 0) {
        uploadMessagePav.value = "Please select a file to upload.";
        return;
      }

      const fd = new FormData();
      selectedFilesPav.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelinePav.value);
      fd.append("program_name", selectedProgramPav.value);

      try {
        uploadMessagePav.value = "Uploading PAV file...";
        await axiosLongTimeout.post("/posts/pav_upload/", fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        });
        uploadMessagePav.value = "PAV upload initiated successfully!";
        
        // Clear the form
        selectedFilesPav.value = [];
        selectedProgramPav.value = "";
        
      } catch (error) {
        console.error("Error uploading PAV file:", error);
        uploadMessagePav.value = "Error uploading PAV file: " + (error.response?.data?.detail || error.message);
      }
    };

    // Supplemental upload methods
    const confirmSubmitSupplementalData = async () => {
      if (!selectedPipelineSupplemental.value) {
        uploadMessageSupplemental.value = "Please select a species database.";
        return;
      }

      if (!selectedFilesSupplemental.value || selectedFilesSupplemental.value.length === 0) {
        uploadMessageSupplemental.value = "Please select a file to upload.";
        return;
      }

      const fd = new FormData();
      selectedFilesSupplemental.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineSupplemental.value);

      try {
        uploadMessageSupplemental.value = "Uploading supplemental file...";
        await axiosLongTimeout.post("/posts/supplemental_upload/", fd, {
          headers: { 'Content-Type': 'multipart/form-data' },
          timeout: 60000
        });
        uploadMessageSupplemental.value = "Supplemental upload initiated successfully!";
        
        // Clear the form
        selectedFilesSupplemental.value = [];
        
      } catch (error) {
        console.error("Error uploading supplemental file:", error);
        uploadMessageSupplemental.value = "Error uploading supplemental file: " + (error.response?.data?.detail || error.message);
      }
    };

    // Modal handlers
    const cancelUpload = () => {
      showDuplicateModal.value = false;
      uploadMessageMadc.value = null;
      duplicateList.value = [];
      previewResponse.value = null;
    };

    const cancelNoDuplicate = () => {
      showNoDuplicateModal.value = false;
      uploadMessageMadc.value = null;
      previewResponse.value = null;
    };

    const downloadDuplicates = () => {
      if (duplicateList.value.length === 0) {
        alert("No duplicates to download.");
        return;
      }
      
      const csvContent = "data:text/csv;charset=utf-8," + 
        "AlleleID\n" + 
        duplicateList.value.join("\n");
      
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "duplicate_alleles.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    // Database version methods
    const capitalizeFirst = (str) => {
      return str.charAt(0).toUpperCase() + str.slice(1);
    };

    // Job polling methods with improved error handling
    const pollJobStatus = async () => {
      try {
        const requests = [
          axiosInstance.get('/posts/jobStatus', { timeout: 15000 }),
          axiosInstance.get('/posts/pav_jobStatus', { timeout: 15000 }),
          axiosInstance.get('/posts/supplemental_jobStatus', { timeout: 15000 })
        ];
        
        const [madcResponse, pavResponse, supplementalResponse] = await Promise.allSettled(requests);
        
        // Handle each response individually
        if (madcResponse.status === 'fulfilled') {
          jobsMadc.value = madcResponse.value.data;
        } else {
          console.error('Error polling MADC job status:', madcResponse.reason);
        }
        
        if (pavResponse.status === 'fulfilled') {
          jobsPav.value = pavResponse.value.data;
        } else {
          console.error('Error polling PAV job status:', pavResponse.reason);
        }
        
        if (supplementalResponse.status === 'fulfilled') {
          jobsSupplemental.value = supplementalResponse.value.data;
        } else {
          console.error('Error polling Supplemental job status:', supplementalResponse.reason);
        }
        
      } catch (error) {
        console.error('Unexpected error in job status polling:', error);
      }
    };

    // Cleanup function to cancel all active requests
    const cleanup = () => {
      // Cancel all active requests
      for (const [key, controller] of activeRequests.value) {
        controller.abort();
        console.log(`Cleanup: cancelled request ${key}`);
      }
      activeRequests.value.clear();
      
      // Clear all debounce timeouts
      for (const [key, timeout] of debounceTimeouts.value) {
        clearTimeout(timeout);
        console.log(`Cleanup: cleared timeout ${key}`);
      }
      debounceTimeouts.value.clear();
    };

    // Watchers for species changes with debouncing
    watch(selectedPipelineMadc, async (newSpecies, oldSpecies) => {
      if (newSpecies && newSpecies !== oldSpecies) {
        // Reset form completely
        selectedProgramMadc.value = "";
        selectedProjectMadc.value = "";
        newProgramNameMadc.value = "";
        newProjectNameMadc.value = "";
        programNameError.value = "";
        projectNameError.value = "";
        projectOptionsMadc.value = [];
        
        // Use debounced functions to prevent rapid-fire requests
        debouncedFetchPrograms(newSpecies, 'madc');
        debouncedFetchVersion(newSpecies);
      }
    });

    watch(selectedPipelinePav, async (newSpecies, oldSpecies) => {
      if (newSpecies && newSpecies !== oldSpecies) {
        selectedProgramPav.value = "";
        debouncedFetchPrograms(newSpecies, 'pav');
      }
    });

    watch(selectedPipelineSupplemental, async (newSpecies, oldSpecies) => {
      if (newSpecies && newSpecies !== oldSpecies) {
        debouncedFetchVersion(newSpecies);
      }
    });

    // Watch program changes to fetch projects
    watch(selectedProgramMadc, async (newProgram) => {
      if (newProgram && newProgram !== 'new') {
        await fetchProjectsByProgram(newProgram);
      } else if (newProgram === 'new') {
        // When "Add new program" is selected, reset projects to just "Add new project"
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
      } else {
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
      }
      
      // Reset project selection when program changes
      selectedProjectMadc.value = "";
      newProjectNameMadc.value = "";
    });

    // Lifecycle hooks
    onMounted(async () => {
      await pollJobStatus();
      // Set up polling interval
      setInterval(pollJobStatus, 10000); // Increased to 10 seconds to reduce load
    });

    // Cleanup on component unmount
    onUnmounted(() => {
      cleanup();
    });

    return {
      // Reactive references
      pipelineOptions,
      programOptionsMadc,
      programOptionsPav,
      projectOptionsMadc,
      newProgramNameMadc,
      newProjectNameMadc,
      programNameError,
      projectNameError,
      selectedFilesMadc,
      selectedPipelineMadc,
      selectedProgramMadc,
      selectedProjectMadc,
      uploadMessageMadc,
      jobsMadc,
      selectedFilesPav,
      selectedPipelinePav,
      selectedProgramPav,
      uploadMessagePav,
      jobsPav,
      selectedFilesSupplemental,
      selectedPipelineSupplemental,
      uploadMessageSupplemental,
      jobsSupplemental,
      showDuplicateModal,
      showNoDuplicateModal,
      duplicateList,
      previewResponse,
      loadingPreview,
      databaseVersions,
      loadingStates,
      
      // Methods
      validateProgramName,
      validateProjectName,
      handleFileSelectMadc,
      handleFileSelectPav,
      handleFileSelectSupplemental,
      checkAndSubmitMadcData,
      performDuplicateCheck,
      commitMadcData,
      confirmSubmitPavData,
      confirmSubmitSupplementalData,
      cancelUpload,
      cancelNoDuplicate,
      downloadDuplicates,
      capitalizeFirst,
      fetchDatabaseVersion,
      pollJobStatus,
    };
  },
};
</script>

<style scoped>
.data-upload-container {
  max-width: 1200px;
  margin: auto;
  padding: 20px;
}
.upload-section, .job-status-section {
  margin-bottom: 40px;
}
.dropdown-container, .file-upload-container, .table-container {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 20px;
  gap: 10px;
}
.pipeline-label, .program-label, .project-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 5px;
}
.new-program-input, .new-project-input {
  margin-top: 10px;
}
.upload-button {
  margin-top: 10px;
}
.table-header {
  font-size: 1.25rem;
  font-weight: bold;
}
.p-button-success {
  margin-right: 0.5em;
}
.p-tabview .p-tabview-panels {
  margin-top: 20px;
}

.modal-header {
  text-align: center;
  margin-bottom: 1em;
}
.warning-icon {
  color: red;
  font-size: 2em;
  display: block;
}
.warning-text {
  font-size: 1.5em;
  display: block;
  margin-top: 0.2em;
}
.warning-details {
  text-align: center;
  font-size: 1.1em;
  margin-bottom: 1em;
}
.download-container {
  text-align: center;
  margin-bottom: 1em;
}
.dialog-footer {
  display: flex;
  justify-content: space-between;
}
.success-icon {
  color: green;
  font-size: 2em;
  display: block;
}
.success-text {
  color: green;
  font-size: 1.5em;
  display: block;
  margin-top: 0.2em;
}
.success-details {
  text-align: center;
  font-size: 1.1em;
  margin-bottom: 1em;
}

/* New style for larger upload messages */
.upload-message {
  font-size: 1.2em; /* Adjust as needed */
  font-weight: bold;
  margin-top: 10px;
}

/* Control the width of dropdown containers */
.dropdown-container {
  width: 350px; /* Adjust to your preferred width */
  max-width: 100%;
}

/* Make dropdown components match the width of their container */
:deep(.p-dropdown) {
  width: 100% !important; /* Override PrimeVue's w-full class */
}

/* Make AutoComplete components match the width of their container */
:deep(.p-autocomplete) {
  width: 100% !important;
}

/* Make dropdown panel match the width of the dropdown */
:deep(.p-dropdown-panel) {
  width: 350px; /* Keep this value the same as dropdown-container width */
  max-width: 100%;
}

/* AutoComplete panel styling */
:deep(.p-autocomplete-panel) {
  width: 350px;
  max-width: 100%;
}

/* Form help text styling */
.form-help {
  color: #6c757d;
  font-size: 0.875rem;
  margin-top: 0.25rem;
  display: block;
}

/* New input field styling */
.new-program-input,
.new-project-input {
  margin-top: 10px;
  padding: 10px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background-color: #f8f9fa;
}

.new-input-label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  font-size: 0.9rem;
}

.error-text {
  color: #dc3545;
  font-size: 0.8rem;
  margin-top: 4px;
  display: block;
}

/* Input field styling */
.p-inputtext {
  margin-top: 4px;
}

/* Ensure dropdowns show "Add new..." option distinctly */
:deep(.p-dropdown-item:last-child) {
  border-top: 1px solid #e0e0e0;
  background-color: #f8f9fa;
  font-style: italic;
}

/* Enhanced version info container */
.version-info-container {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  border-left: 4px solid #4caf50;
  margin-top: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  min-width: 300px;
}

.version-info-container.error {
  border-left-color: #f44336;
  background-color: #fff5f5;
}

/* Make the database version text much larger and more prominent */
.version-info-text {
  font-size: 1.2rem;
  color: #333;
  display: flex;
  align-items: center;
  flex-direction: column;
  text-align: center;
}

.version-info-text.error {
  color: #f44336;
}

.version-info-text i {
  font-size: 1.5rem;
  color: #4caf50;
  margin-bottom: 8px;
}

.version-info-text.error i {
  color: #f44336;
}

/* Make the version number even larger and highlighted */
.version-number {
  font-size: 2rem;
  font-weight: bold;
  color: #2196F3;
  display: block;
  margin-top: 8px;
}

/* Loading state styling */
.version-info-text.loading {
  color: #757575;
}

.version-info-text.loading i {
  color: #757575;
}

/* New loading and error state styles */
.dropdown-with-loading {
  position: relative;
}

.loading-text {
  color: #757575;
  font-style: italic;
  margin-top: 5px;
  display: block;
}

.loading-text i {
  margin-right: 5px;
  color: #2196F3;
}

/* Loading animation for dropdowns */
.dropdown-loading {
  position: relative;
}

.dropdown-loading::after {
  content: "";
  position: absolute;
  right: 10px;
  top: 50%;
  width: 16px;
  height: 16px;
  margin-top: -8px;
  border: 2px solid rgba(0, 0, 0, 0.1);
  border-top-color: #2196F3;
  border-radius: 50%;
  animation: dropdown-spin 0.8s linear infinite;
}

@keyframes dropdown-spin {
  to { transform: rotate(360deg); }
}

/* Error text styling improvements */
.error-text {
  color: #dc3545;
  font-size: 0.8rem;
  margin-top: 4px;
  display: block;
  font-weight: 500;
}

/* Success feedback for completed operations */
.success-text {
  color: #28a745;
  font-weight: 500;
}

/* Timeout and network error styling */
.network-error {
  background-color: #fff5f5;
  border: 1px solid #f44336;
  border-radius: 4px;
  padding: 10px;
  margin: 10px 0;
  color: #d32f2f;
}

.network-error i {
  margin-right: 8px;
  color: #f44336;
}

/* Retry button styling */
.retry-button {
  background-color: #ff9800;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 10px;
  transition: background-color 0.3s ease;
}

.retry-button:hover {
  background-color: #f57c00;
}

.retry-button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* Better disabled state for dropdowns */
:deep(.p-dropdown.p-disabled) {
  opacity: 0.6;
}

:deep(.p-dropdown.p-disabled .p-dropdown-label) {
  color: #999;
}

/* Loading spinner in dropdowns */
:deep(.p-dropdown-trigger .p-dropdown-trigger-icon.pi-spin) {
  animation: dropdown-spin 1s linear infinite;
}

/* Version info error state small text */
.version-info-text small {
  font-size: 0.9rem;
  margin-top: 4px;
  display: block;
  font-weight: normal;
}

/* Layout improvements for the two-column layout */
.two-column-layout {
  display: flex;
  flex-direction: row;
  gap: 30px;
  margin-bottom: 20px;
}

.form-column {
  flex: 1;
  min-width: 350px;
}

.version-column {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>



