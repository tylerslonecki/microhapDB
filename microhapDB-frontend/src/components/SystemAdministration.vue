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
                  <div v-if="selectedPipelineMadc && programOptionsMadc.length <= 1" class="empty-options-message">
                    <small>No existing programs found for this species. You can create a new one.</small>
                  </div>
                </div>

                <!-- Program Dropdown -->
                <div class="dropdown-container" v-if="selectedPipelineMadc">
                  <label for="programSelectMadc" class="program-label">Please select or add Program</label>
                  <Dropdown
                    id="programSelectMadc"
                    v-model="selectedProgramMadc"
                    :options="programOptionsMadc"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="Please select one"
                    class="w-full"
                    @change="handleProgramChangeMadc"
                    :disabled="programOptionsMadc.length <= 1"
                  />
                  <!-- New Program Input -->
                  <div v-if="selectedProgramMadc === 'new'" class="new-program-input">
                    <InputText v-model="newProgramNameMadc" placeholder="Enter new program name" />
                    <Button 
                      label="Create Program" 
                      icon="pi pi-plus" 
                      @click="submitNewProgramMadc"
                      class="mt-2"
                    />
                  </div>
                </div>

                <!-- Project Dropdown with Conditional Rendering - MADC Upload Tab -->
                <div class="dropdown-container" v-if="selectedProgramMadc">
                  <label for="projectSelectMadc" class="project-label">Please select or add Project</label>
                  <Dropdown
                    id="projectSelectMadc"
                    v-model="selectedProjectMadc"
                    :options="projectOptionsMadc"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="Please select one"
                    class="w-full"
                    @change="handleProjectChangeMadc"
                    :disabled="projectOptionsMadc.length <= 1"
                  />
                  <!-- New Project Input -->
                  <div v-if="selectedProjectMadc === 'new'" class="new-project-input">
                    <InputText v-model="newProjectNameMadc" placeholder="Enter new project name" />
                    <Button 
                      label="Create Project" 
                      icon="pi pi-plus" 
                      @click="submitNewProjectMadc"
                      class="mt-2"
                    />
                  </div>
                </div>
                <div v-else-if="selectedPipelineMadc && !selectedProgramMadc">
                  <p>Please select a program first</p>
                </div>
              </div>

              <!-- Version Column Template (replace this in all three tabs) -->
              <div class="version-column">
                <div class="version-info-container" v-if="selectedPipelineMadc && databaseVersions[selectedPipelineMadc]">
                  <div class="version-info-text">
                    <i class="pi pi-database"></i>
                    <span>Current {{ capitalizeFirst(selectedPipelineMadc) }} Database</span>
                    <span class="version-number">v{{ databaseVersions[selectedPipelineMadc].version }}</span>
                  </div>
                </div>
                <div class="version-info-container" v-else-if="selectedPipelineMadc">
                  <div class="version-info-text loading">
                    <i class="pi pi-spin pi-spinner"></i>
                    <span>Loading database version...</span>
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
      <TabPanel header="PAV Upload" class="custom-tabpanel">
        <Panel header="PAV Upload">
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
                  <div v-if="selectedPipelinePav && programOptionsPav.length <= 1" class="empty-options-message">
                    <small>No existing programs found for this species. You can create a new one.</small>
                  </div>
                </div>
                <div class="dropdown-container" v-if="selectedPipelinePav">
                  <label for="programSelectPav" class="program-label">Please select or add Program</label>
                  <Dropdown
                    id="programSelectPav"
                    v-model="selectedProgramPav"
                    :options="programOptionsPav"
                    optionLabel="name"
                    optionValue="value"
                    placeholder="Please select one"
                    class="w-full"
                    @change="handleProgramChangePav"
                    :disabled="programOptionsPav.length <= 1"
                  />
                  <div v-if="selectedProgramPav === 'new'" class="new-program-input">
                    <InputText v-model="newProgramNamePav" placeholder="Enter new program name" />
                    <Button 
                      label="Create Program" 
                      icon="pi pi-plus" 
                      @click="submitNewProgramPav"
                      class="mt-2"
                    />
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
                label="Submit PAV Job" 
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
                <span class="table-header">PAV Upload Job Status</span>
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
import { ref, onMounted, watch } from 'vue';
import axiosInstance, { axiosLongTimeout } from '../axiosConfig';
import { mapGetters, mapActions } from 'vuex';
import Dropdown from 'primevue/dropdown';
import FileUpload from 'primevue/fileupload';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import InputText from 'primevue/inputtext';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Panel from 'primevue/panel';
import ConfirmDialog from 'primevue/confirmdialog';
import Dialog from 'primevue/dialog';
import { useConfirm } from 'primevue/useconfirm';
import { useToast } from 'primevue/usetoast';
import { SUPPORTED_SPECIES } from '../utils/speciesConfig';

export default {
  name: 'DataUpload',
  components: {
    Dropdown,
    FileUpload,
    Button,
    DataTable,
    Column,
    InputText,
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
    const confirm = useConfirm();
    const toast = useToast();

    // Shared state
    const pipelineOptions = ref(SUPPORTED_SPECIES);

    // Program Options
    const programOptionsMadc = ref([]);
    const programOptionsPav = ref([]);

    // Project Options for MADC
    const projectOptionsMadc = ref([{ name: "Add new project", value: "new" }]);

    // MADC Upload state
    const selectedFilesMadc = ref([]);
    const selectedPipelineMadc = ref("");
    const selectedProgramMadc = ref("");
    const newProgramNameMadc = ref("");
    const uploadMessageMadc = ref(null);
    const jobsMadc = ref([]);
    const selectedProjectMadc = ref("");
    const newProjectNameMadc = ref("");

    // PAV Upload state
    const selectedFilesPav = ref([]);
    const selectedPipelinePav = ref("");
    const selectedProgramPav = ref("");
    const newProgramNamePav = ref("");
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

    // Fetch Programs by Species
    const fetchProgramsBySpecies = async (species, target) => {
      if (!species) return;
      
      try {
        uploadMessageMadc.value = "Loading programs...";
        const response = await axiosInstance.get(`/posts/programs/by_species/${species}`);
        const fetchedPrograms = response.data.programs || [];
        const mappedPrograms = fetchedPrograms.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));
        
        // Update the relevant program options list
        if (target === 'madc') {
          programOptionsMadc.value = [...mappedPrograms, { name: "Add new program", value: "new" }];
          
          // If no programs exist for this species, automatically select "Add new program"
          if (mappedPrograms.length === 0) {
            selectedProgramMadc.value = 'new';
          } else {
            // Reset program selection when species changes
            selectedProgramMadc.value = '';
          }
          
          // Reset project selection when species changes
          selectedProjectMadc.value = '';
          projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        } else if (target === 'pav') {
          programOptionsPav.value = [...mappedPrograms, { name: "Add new program", value: "new" }];
          
          // If no programs exist for this species, automatically select "Add new program"
          if (mappedPrograms.length === 0) {
            selectedProgramPav.value = 'new';
          } else {
            // Reset program selection when species changes
            selectedProgramPav.value = '';
          }
        }
        
        uploadMessageMadc.value = null;
      } catch (error) {
        console.error(`Error fetching programs for ${species}:`, error);
        uploadMessageMadc.value = `Error loading programs for ${species}`;
      }
    };

    // Fetch Projects by Program
    const fetchProjectsByProgram = async (programName) => {
      if (!programName || programName === 'new') {
        // If no program selected or "new" is selected, just show the "Add new project" option
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        selectedProjectMadc.value = 'new'; // Automatically select "Add new project"
        return;
      }
      
      try {
        uploadMessageMadc.value = "Loading projects...";
        
        // First we need to get the program ID from the name
        const programResponse = await axiosInstance.get('/posts/programs/list');
        const programs = programResponse.data.programs || [];
        const program = programs.find(p => p.name === programName);
        
        if (!program) {
          console.error(`Program not found: ${programName}`);
          uploadMessageMadc.value = null;
          // If program not found, just show "Add new project" and select it
          projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
          selectedProjectMadc.value = 'new';
          return;
        }
        
        // Now fetch projects for this program
        const response = await axiosInstance.get(`/posts/projects/by_program/${program.id}`);
        const fetchedProjects = response.data || [];
        
        // Map the projects to the correct format
        const mappedProjects = fetchedProjects.map(project => ({
          name: project.name,
          value: project.name
        }));
        
        // Add the "new project" option
        projectOptionsMadc.value = [...mappedProjects, { name: "Add new project", value: "new" }];
        
        // If no projects exist for this program, automatically select "Add new project"
        if (mappedProjects.length === 0) {
          selectedProjectMadc.value = 'new';
        } else {
          // Reset project selection
          selectedProjectMadc.value = '';
        }
        
        uploadMessageMadc.value = null;
      } catch (error) {
        console.error(`Error fetching projects for program ${programName}:`, error);
        uploadMessageMadc.value = `Error loading projects for program ${programName}`;
        
        // In case of error, just show "Add new project" and select it
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        selectedProjectMadc.value = 'new';
      }
    };

    // Fetch Programs and Projects
    const fetchPrograms = async () => {
      try {
        const response = await axiosInstance.get("/posts/programs/list");
        const fetchedPrograms = response.data.programs || [];
        const mappedPrograms = fetchedPrograms.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));
        programOptionsMadc.value = [...mappedPrograms, { name: "Add new program", value: "new" }];
        programOptionsPav.value = [...mappedPrograms, { name: "Add new program", value: "new" }];
        if (fetchedPrograms.length === 0) {
          selectedProgramMadc.value = 'new';
          selectedProgramPav.value = 'new';
        } else {
          selectedProgramMadc.value = '';
          selectedProgramPav.value = '';
        }
      } catch (error) {
        console.error("Error fetching programs:", error);
      }
    };

    // Improved fetchProjects to better handle initial state
    const fetchProjects = async () => {
      try {
        const response = await axiosInstance.get("/posts/projects/list");
        const fetchedProjects = response.data || [];
        
        // Map projects to dropdown format
        const mappedProjects = fetchedProjects.map((project) => ({
          name: project.name,
          value: project.name
        }));
        
        // Add the "new project" option
        projectOptionsMadc.value = [...mappedProjects, { name: "Add new project", value: "new" }];
        
        // Set initial selection
        if (fetchedProjects.length === 0) {
          selectedProjectMadc.value = 'new';
        } else {
          // Don't set any default, make the user choose explicitly
          selectedProjectMadc.value = '';
        }
        
        return fetchedProjects;
      } catch (error) {
        console.error("Error fetching projects:", error);
        throw error;
      }
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

    // Enhanced createProgram function
    const createProgram = async (programName) => {
      try {
        const response = await axiosInstance.post('/posts/programs/create', { name: programName });
        // Directly update the local options array instead of re-fetching
        const newProgram = response.data.program.name;
        
        // Update the program options locally
        const newProgramObj = { name: newProgram, value: newProgram };
        programOptionsMadc.value = [...programOptionsMadc.value.filter(p => p.value !== 'new'), 
                                    newProgramObj, 
                                    { name: "Add new program", value: "new" }];
        
        programOptionsPav.value = [...programOptionsPav.value.filter(p => p.value !== 'new'), 
                                  newProgramObj, 
                                  { name: "Add new program", value: "new" }];
        
        return { success: true, program: newProgram };
      } catch (error) {
        console.error("Error creating program:", error);
        return { success: false, error: error.response?.data?.message || "Failed to create program" };
      }
    };

    // Enhanced createProject function
    const createProject = async (projectName) => {
      try {
        const response = await axiosLongTimeout.post('/posts/projects/create', { name: projectName });
        const newProject = response.data.name;
        
        // Update the project options locally
        const newProjectObj = { name: newProject, value: newProject };
        projectOptionsMadc.value = [...projectOptionsMadc.value.filter(p => p.value !== 'new'), 
                                  newProjectObj, 
                                  { name: "Add new project", value: "new" }];
        
        // Check if there's a warning about duplicate project name
        if (response.data.warning) {
          // Display the warning in a toast message
          toast.add({
            severity: 'warn',
            summary: 'Duplicate Project',
            detail: response.data.warning,
            life: 5000
          });
        }
        
        return { success: true, project: newProject };
      } catch (error) {
        console.error("Error creating project:", error);
        return { success: false, error: error.response?.data?.message || "Failed to create project" };
      }
    };

    // Handle Program/Project change events
    const handleProgramChangeMadc = () => {
      if (selectedProgramMadc.value === 'new') {
        // If "new program" selected, reset projects
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        selectedProjectMadc.value = 'new';
      } else if (selectedProgramMadc.value) {
        // If a program is selected, fetch relevant projects
        fetchProjectsByProgram(selectedProgramMadc.value);
      }
    };
    
    const handleProgramChangePav = () => {
      if (selectedProgramPav.value === 'new') {
        // Additional actions if needed
      }
    };
    
    const handleProjectChangeMadc = () => {
      if (selectedProjectMadc.value === 'new') {
        // Additional actions if needed
      }
    };

    const submitNewProgramMadc = async () => {
      if (!newProgramNameMadc.value.trim()) {
        uploadMessageMadc.value = "Please enter a valid program name.";
        return;
      }
      
      uploadMessageMadc.value = "Creating program...";
      const result = await createProgram(newProgramNameMadc.value.trim());
      
      if (result.success) {
        // Set the selected program to the newly created one
        selectedProgramMadc.value = result.program;
        newProgramNameMadc.value = "";
        uploadMessageMadc.value = "Program created successfully.";
      } else {
        uploadMessageMadc.value = result.error;
      }
    };
    
    // Improved submitNewProgramPav
    const submitNewProgramPav = async () => {
      if (!newProgramNamePav.value.trim()) {
        uploadMessagePav.value = "Please enter a valid program name.";
        return;
      }
      
      uploadMessagePav.value = "Creating program...";
      const result = await createProgram(newProgramNamePav.value.trim());
      
      if (result.success) {
        // Set the selected program to the newly created one
        selectedProgramPav.value = result.program;
        newProgramNamePav.value = "";
        uploadMessagePav.value = "Program created successfully.";
      } else {
        uploadMessagePav.value = result.error;
      }
    };

    const submitNewProjectMadc = async () => {
      if (!newProjectNameMadc.value.trim()) {
        uploadMessageMadc.value = "Please enter a valid project name.";
        return;
      }
      
      uploadMessageMadc.value = "Creating project...";
      const result = await createProject(newProjectNameMadc.value.trim());
      
      if (result.success) {
        // Set the selected project to the newly created one
        selectedProjectMadc.value = result.project;
        newProjectNameMadc.value = "";
        uploadMessageMadc.value = "Project created successfully.";
      } else {
        uploadMessageMadc.value = result.error;
      }
    };

    // Improved checkAndSubmitMadcData with better flow control
    const checkAndSubmitMadcData = async () => {
      // First, check if new program/project needs to be created
      if (selectedProgramMadc.value === 'new' && newProgramNameMadc.value.trim()) {
        // Create the program first
        uploadMessageMadc.value = "Creating program...";
        const programResult = await createProgram(newProgramNameMadc.value.trim());
        
        if (!programResult.success) {
          uploadMessageMadc.value = programResult.error;
          return;
        }
        
        // Set the created program
        selectedProgramMadc.value = programResult.program;
        newProgramNameMadc.value = "";
        uploadMessageMadc.value = "Program created.";
      }
      
      if (selectedProjectMadc.value === 'new' && newProjectNameMadc.value.trim()) {
        // Create the project first
        uploadMessageMadc.value = "Creating project...";
        const projectResult = await createProject(newProjectNameMadc.value.trim());
        
        if (!projectResult.success) {
          uploadMessageMadc.value = projectResult.error;
          return;
        }
        
        // Set the created project
        selectedProjectMadc.value = projectResult.project;
        newProjectNameMadc.value = "";
        uploadMessageMadc.value = uploadMessageMadc.value 
          ? `${uploadMessageMadc.value} Project created.` 
          : "Project created.";
      }
      
      // Now validate all fields
      if (!validateMadcFields()) {
        return;
      }
      
      // Proceed with upload preview
      uploadMessageMadc.value = "Analyzing file for duplicates…";
      loadingPreview.value = true;
      
      const fd = new FormData();
      selectedFilesMadc.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineMadc.value);
      
      try {
        const response = await axiosInstance.post("/posts/upload/preview", fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
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
        uploadMessageMadc.value = "Error during preview: " + (error.response?.data?.message || error.message);
      }
    };

    // Add a helper function to verify all required fields for MADC upload
    const validateMadcFields = () => {
      if (!selectedPipelineMadc.value) {
        uploadMessageMadc.value = "Please select a species.";
        return false;
      }
      
      if (!selectedProgramMadc.value) {
        uploadMessageMadc.value = "Please select a program.";
        return false;
      }
      
      if (selectedProgramMadc.value === 'new' && !newProgramNameMadc.value) {
        uploadMessageMadc.value = "Please enter a name for the new program.";
        return false;
      }
      
      if (!selectedProjectMadc.value) {
        uploadMessageMadc.value = "Please select a project.";
        return false;
      }
      
      if (selectedProjectMadc.value === 'new' && !newProjectNameMadc.value) {
        uploadMessageMadc.value = "Please enter a name for the new project.";
        return false;
      }
      
      if (selectedFilesMadc.value.length === 0) {
        uploadMessageMadc.value = "No file selected.";
        return false;
      }
      
      return true;
    };

    const cancelNoDuplicate = () => {
      showNoDuplicateModal.value = false;
      uploadMessageMadc.value = "Upload canceled.";
    };

    const commitMadcData = async () => {
      // Close both modals
      showDuplicateModal.value = false;
      showNoDuplicateModal.value = false;
      
      uploadMessageMadc.value = "Uploading and processing file…";
      const fd = new FormData();
      selectedFilesMadc.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineMadc.value);
      fd.append("program_name", selectedProgramMadc.value);
      fd.append("project_name", selectedProjectMadc.value);
      fd.append("force", "true");  // Flag to force commit despite duplicates
      try {
        const response = await axiosInstance.post("/posts/upload/", fd, {
          headers: { 'Content-Type': 'multipart/form-data' }
        });
        uploadMessageMadc.value = response.data.message;
      } catch (error) {
        uploadMessageMadc.value = "Error during commit: " + error.message;
      }
    };
    const downloadDuplicates = () => {
      const csvContent = "data:text/csv;charset=utf-8," + duplicateList.value.join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "duplicate_alleleIDs.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    };

    const cancelUpload = () => {
      showDuplicateModal.value = false;
      uploadMessageMadc.value = "Upload canceled.";
    };

    // PAV & Supplemental submission confirmation methods
    const confirmSubmitPavData = () => {
      confirm.require({
        message: 'Are you sure you want to proceed with the PAV submission?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: submitPavData,
        reject: () => {
          console.log('PAV submission canceled.');
        }
      });
    };
    const submitPavData = async () => {
      // Validate required fields
      if (!selectedPipelinePav.value) {
        uploadMessagePav.value = "Please select a species.";
        return;
      }
      if (!selectedProgramPav.value) {
        uploadMessagePav.value = "Please select a program.";
        return;
      }
      if (selectedFilesPav.value.length === 0) {
        uploadMessagePav.value = "No file selected.";
        return;
      }

      uploadMessagePav.value = "Uploading and processing file…";
      const fd = new FormData();
      // Assuming only one file is allowed; use the first file if multiple are selected.
      fd.append("file", selectedFilesPav.value[0]);
      fd.append("species", selectedPipelinePav.value);
      fd.append("program_name", selectedProgramPav.value);

      try {
        const response = await axiosInstance.post("/posts/pav_upload/", fd, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        uploadMessagePav.value = response.data.message;
        // Optionally, refresh the PAV jobs list to show the new job status
        fetchJobsPav();
      } catch (error) {
        uploadMessagePav.value = "Error during commit: " + error.message;
      }
    };
    const confirmSubmitSupplementalData = () => {
      confirm.require({
        message: 'Are you sure you want to proceed with the Supplemental submission?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: submitSupplementalData,
        reject: () => {
          console.log('Supplemental submission canceled.');
        }
      });
    };
    const submitSupplementalData = async () => {
      // Validate that a species database is selected.
      if (!selectedPipelineSupplemental.value) {
        uploadMessageSupplemental.value = "Please select a species database.";
        return;
      }
      // Validate that at least one file is selected.
      if (selectedFilesSupplemental.value.length === 0) {
        uploadMessageSupplemental.value = "No file selected.";
        return;
      }
      // Inform the user that the upload is starting.
      uploadMessageSupplemental.value = "Uploading and processing file…";

      // Create FormData and append files and species.
      const fd = new FormData();
      selectedFilesSupplemental.value.forEach((file) => {
        fd.append("file", file);
      });
      fd.append("species", selectedPipelineSupplemental.value);

      try {
        // Post to the backend endpoint.
        const response = await axiosInstance.post("/posts/supplemental_upload/", fd, {
          headers: { "Content-Type": "multipart/form-data" }
        });
        // Show a success message (adjust as necessary based on your backend response).
        uploadMessageSupplemental.value = response.data.message || 
          "Supplemental upload initiated successfully. Job ID: " + (response.data.job_id || "");
      } catch (error) {
        // Show error message.
        uploadMessageSupplemental.value = "Error during upload: " + error.message;
      }
    };


    // Fetch Job Status functions
    const fetchJobsMadc = async () => {
      try {
        const response = await axiosInstance.get('/posts/jobStatus');
        jobsMadc.value = response.data;
      } catch (error) {
        console.error("Error fetching MADC jobs:", error);
      }
    };
    const fetchJobsPav = async () => {
      try {
        const response = await axiosInstance.get('/posts/pav_jobStatus');
        jobsPav.value = response.data;
      } catch (error) {
        console.error("Error fetching PAV jobs:", error);
      }
    };
    const fetchJobsSupplemental = async () => {
      try {
        const response = await axiosInstance.get('/posts/supplemental_jobStatus');
        jobsSupplemental.value = response.data;
      } catch (error) {
        console.error("Error fetching Supplemental jobs:", error);
      }
    };

    const capitalizeFirst = (str) => {
      if (!str) return '';
      return str.charAt(0).toUpperCase() + str.slice(1);
    };

    // Format date for better readability
    const formatDate = (isoDateString) => {
      try {
        const date = new Date(isoDateString);
        return new Intl.DateTimeFormat('en-US', {
          year: 'numeric',
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        }).format(date);
      } catch (e) {
        return isoDateString; // fallback to original string if parsing fails
      }
    };

    // State for database versions
    const databaseVersions = ref({});

    // Function to fetch database version for a species
    const fetchDatabaseVersion = async (species) => {
      if (!species) return;
      
      try {
        const response = await axiosInstance.get(`/posts/database_version/${species}`);
        if (response.data) {
          databaseVersions.value = {
            ...databaseVersions.value,
            [species]: response.data
          };
        }
      } catch (error) {
        console.error(`Error fetching ${species} database version:`, error);
      }
    };

    // Set up watchers for all three tabs to fetch versions when species is selected
    watch(selectedPipelineMadc, (newValue) => {
      if (newValue) {
        fetchProgramsBySpecies(newValue, 'madc');
        fetchDatabaseVersion(newValue);
      }
    });

    watch(selectedPipelinePav, (newValue) => {
      if (newValue) {
        fetchProgramsBySpecies(newValue, 'pav');
        fetchDatabaseVersion(newValue);
      }
    });

    watch(selectedPipelineSupplemental, (newValue) => {
      if (newValue) {
        fetchDatabaseVersion(newValue);
      }
    });

    // Watch for program selection to update projects
    watch(selectedProgramMadc, (newValue) => {
      if (newValue && newValue !== 'new') {
        fetchProjectsByProgram(newValue);
      } else if (newValue === 'new') {
        // When "Add new program" is selected, reset project options to just "Add new project"
        projectOptionsMadc.value = [{ name: "Add new project", value: "new" }];
        selectedProjectMadc.value = 'new';
      }
    });

    // Improved initialization section
    onMounted(async () => {
      // Set loading states
      uploadMessageMadc.value = "Loading data...";
      uploadMessagePav.value = "Loading data...";
      uploadMessageSupplemental.value = "Loading data...";
      
      // Load essential data first
      try {
        await Promise.all([
          fetchPrograms(),
          fetchProjects()
        ]);
        
        // Clear loading messages
        uploadMessageMadc.value = null;
        uploadMessagePav.value = null;
        uploadMessageSupplemental.value = null;
      } catch (error) {
        console.error("Error during initialization:", error);
        uploadMessageMadc.value = "Error loading data. Please try refreshing the page.";
        uploadMessagePav.value = "Error loading data. Please try refreshing the page.";
        uploadMessageSupplemental.value = "Error loading data. Please try refreshing the page.";
      }
      
      // Fetch job statuses
      fetchJobsMadc();
      fetchJobsPav();
      fetchJobsSupplemental();
      
      // Set up the interval for job status updates
      const statusInterval = setInterval(() => {
        fetchJobsMadc();
        fetchJobsPav();
        fetchJobsSupplemental();
      }, 15000);
      
      // Clean up interval on component unmount
      return () => {
        clearInterval(statusInterval);
      };
    });

    return {
      pipelineOptions,
      programOptionsMadc,
      programOptionsPav,
      projectOptionsMadc,
      selectedFilesMadc,
      selectedPipelineMadc,
      selectedProgramMadc,
      newProgramNameMadc,
      uploadMessageMadc,
      jobsMadc,
      selectedProjectMadc,
      newProjectNameMadc,
      handleFileSelectMadc,
      checkAndSubmitMadcData,
      commitMadcData,
      cancelNoDuplicate,
      submitNewProgramMadc,
      submitNewProgramPav,
      handleProgramChangeMadc,
      handleProgramChangePav,
      submitNewProjectMadc,
      handleProjectChangeMadc,
      selectedFilesPav,
      selectedPipelinePav,
      selectedProgramPav,
      newProgramNamePav,
      uploadMessagePav,
      jobsPav,
      handleFileSelectPav,
      selectedFilesSupplemental,
      selectedPipelineSupplemental,
      uploadMessageSupplemental,
      jobsSupplemental,
      handleFileSelectSupplemental,
      showDuplicateModal,
      showNoDuplicateModal,
      duplicateList,
      downloadDuplicates,
      cancelUpload,
      fetchJobsMadc,
      fetchJobsPav,
      fetchJobsSupplemental,
      loadingPreview,
      confirmSubmitPavData,
      confirmSubmitSupplementalData,
      previewResponse,
      databaseVersions,
      capitalizeFirst,
      formatDate,
      fetchProgramsBySpecies,
      fetchProjectsByProgram,
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

/* Make dropdown panel match the width of the dropdown */
:deep(.p-dropdown-panel) {
  width: 350px; /* Keep this value the same as dropdown-container width */
  max-width: 100%;
}

/* Optional: If you want to control the file upload width too */
.file-upload-container :deep(.p-fileupload) {
  width: 350px;
  max-width: 100%;
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

/* Make the database version text much larger and more prominent */
.version-info-text {
  font-size: 1.2rem;
  color: #333;
  display: flex;
  align-items: center;
  flex-direction: column;
  text-align: center;
}

.version-info-text i {
  font-size: 1.5rem;
  color: #4caf50;
  margin-bottom: 8px;
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


/* Improve dropdown header appearance */
.pipeline-label, .program-label, .project-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
}

/* Add loading animation for dropdowns */
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
</style>
