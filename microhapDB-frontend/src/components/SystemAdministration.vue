<template>
  <div class="system-admin-container">
    <!-- Global Confirmation Dialog -->
    <ConfirmDialog />

    <!-- Duplicate Warning Modal for MADC Upload (duplicates found) -->
    <Dialog v-model:visible="showDuplicateModal" :modal="true" :closable="false" :style="{ width: '600px' }">
      <div class="modal-header">
        <span class="warning-icon">
          <i class="pi pi-exclamation-circle" style="font-size: 2em; margin-right: 8px;"></i>Warning
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
        <p class="warning-details" v-if="previewResponse">
          By submitting this file you will add {{ previewResponse.duplicate_count  - previewResponse.total_count }} alleleIDs to the database
        </p>
      </div>
      <div class="dialog-footer">
        <Button label="Cancel" icon="pi pi-times" class="p-button-danger" @click="cancelUpload" />
        <Button label="Submit Upload" icon="pi pi-check" @click="commitMadcData" autoFocus />
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

            <!-- Program Dropdown -->
            <div class="dropdown-container">
              <label for="programSelectMadc" class="program-label">Please select or add Program/Owner</label>
              <Dropdown
                id="programSelectMadc"
                v-model="selectedProgramMadc"
                :options="programOptionsMadc"
                optionLabel="name"
                optionValue="value"
                placeholder="Please select one"
                class="w-full"
                @change="handleProgramChangeMadc"
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

            <!-- Source Dropdown with Conditional Rendering -->
            <div class="dropdown-container" v-if="sourceOptionsMadc.length > 0">
              <label for="sourceSelectMadc" class="source-label">Please select or add Source</label>
              <Dropdown
                id="sourceSelectMadc"
                v-model="selectedSourceMadc"
                :options="sourceOptionsMadc"
                optionLabel="name"
                optionValue="value"
                placeholder="Please select one"
                class="w-full"
                @change="handleSourceChangeMadc"
              />
              <!-- New Source Input -->
              <div v-if="selectedSourceMadc === 'new'" class="new-source-input">
                <InputText v-model="newSourceNameMadc" placeholder="Enter new source name" />
                <Button 
                  label="Create Source" 
                  icon="pi pi-plus" 
                  @click="submitNewSourceMadc"
                  class="mt-2"
                />
              </div>
            </div>
            <div v-else>
              <p>Loading sources...</p>
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
            <div class="dropdown-container">
              <label for="programSelectPav" class="program-label">Please select or add Program/Owner</label>
              <Dropdown
                id="programSelectPav"
                v-model="selectedProgramPav"
                :options="programOptionsPav"
                optionLabel="name"
                optionValue="value"
                placeholder="Please select one"
                class="w-full"
                @change="handleProgramChangePav"
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
import { ref, onMounted } from 'vue';
import axiosInstance from '../axiosConfig';
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

export default {
  name: 'SystemAdministration',
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

    // Shared state
    const pipelineOptions = ref([
      { label: 'Alfalfa', value: 'alfalfa' },
      { label: 'Cranberry', value: 'cranberry' },
      { label: 'Blueberry', value: 'blueberry' },
      { label: 'Sweetpotato', value: 'sweetpotato' }
    ]);

    // Program Options
    const programOptionsMadc = ref([]);
    const programOptionsPav = ref([]);

    // Source Options for MADC
    const sourceOptionsMadc = ref([{ name: "Add new source", value: "new" }]);

    // MADC Upload state
    const selectedFilesMadc = ref([]);
    const selectedPipelineMadc = ref("");
    const selectedProgramMadc = ref("");
    const newProgramNameMadc = ref("");
    const uploadMessageMadc = ref(null);
    const jobsMadc = ref([]);
    const selectedSourceMadc = ref("new");
    const newSourceNameMadc = ref("");

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

    // Fetch Programs and Sources
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

    // Improved fetchSources to better handle initial state
    const fetchSources = async () => {
      try {
        const response = await axiosInstance.get("/posts/sources/list");
        const fetchedSources = response.data || [];
        
        // Map sources to dropdown format
        const mappedSources = fetchedSources.map((source) => ({
          name: source.name,
          value: source.name
        }));
        
        // Add the "new source" option
        sourceOptionsMadc.value = [...mappedSources, { name: "Add new source", value: "new" }];
        
        // Set initial selection
        if (fetchedSources.length === 0) {
          selectedSourceMadc.value = 'new';
        } else {
          // Don't set any default, make the user choose explicitly
          selectedSourceMadc.value = '';
        }
        
        return fetchedSources;
      } catch (error) {
        console.error("Error fetching sources:", error);
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

    // Enhanced createSource function
    const createSource = async (sourceName) => {
      try {
        const response = await axiosInstance.post('/posts/sources/create', { name: sourceName });
        const newSource = response.data.name;
        
        // Update the source options locally
        const newSourceObj = { name: newSource, value: newSource };
        sourceOptionsMadc.value = [...sourceOptionsMadc.value.filter(s => s.value !== 'new'), 
                                  newSourceObj, 
                                  { name: "Add new source", value: "new" }];
        
        return { success: true, source: newSource };
      } catch (error) {
        console.error("Error creating source:", error);
        return { success: false, error: error.response?.data?.message || "Failed to create source" };
      }
    };

    // Handle Program/Source change events
    const handleProgramChangeMadc = () => {
      if (selectedProgramMadc.value === 'new') {
        // Additional actions if needed
      }
    };
    const handleProgramChangepav = () => {
      if (selectedProgramMadc.value === 'new') {
        // Additional actions if needed
      }
    };
    const handleSourceChangeMadc = () => {
      if (selectedSourceMadc.value === 'new') {
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

    const submitNewSourceMadc = async () => {
      if (!newSourceNameMadc.value.trim()) {
        uploadMessageMadc.value = "Please enter a valid source name.";
        return;
      }
      
      uploadMessageMadc.value = "Creating source...";
      const result = await createSource(newSourceNameMadc.value.trim());
      
      if (result.success) {
        // Set the selected source to the newly created one
        selectedSourceMadc.value = result.source;
        newSourceNameMadc.value = "";
        uploadMessageMadc.value = "Source created successfully.";
      } else {
        uploadMessageMadc.value = result.error;
      }
    };

    // Improved checkAndSubmitMadcData with better flow control
    const checkAndSubmitMadcData = async () => {
      // First, check if new program/source needs to be created
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
      
      if (selectedSourceMadc.value === 'new' && newSourceNameMadc.value.trim()) {
        // Create the source first
        uploadMessageMadc.value = "Creating source...";
        const sourceResult = await createSource(newSourceNameMadc.value.trim());
        
        if (!sourceResult.success) {
          uploadMessageMadc.value = sourceResult.error;
          return;
        }
        
        // Set the created source
        selectedSourceMadc.value = sourceResult.source;
        newSourceNameMadc.value = "";
        uploadMessageMadc.value = uploadMessageMadc.value 
          ? `${uploadMessageMadc.value} Source created.` 
          : "Source created.";
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
      
      if (!selectedSourceMadc.value) {
        uploadMessageMadc.value = "Please select a source.";
        return false;
      }
      
      if (selectedSourceMadc.value === 'new' && !newSourceNameMadc.value) {
        uploadMessageMadc.value = "Please enter a name for the new source.";
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
      fd.append("source_name", selectedSourceMadc.value);
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
          fetchSources()
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
      sourceOptionsMadc,
      selectedFilesMadc,
      selectedPipelineMadc,
      selectedProgramMadc,
      newProgramNameMadc,
      uploadMessageMadc,
      jobsMadc,
      selectedSourceMadc,
      newSourceNameMadc,
      handleFileSelectMadc,
      checkAndSubmitMadcData,
      commitMadcData,
      cancelNoDuplicate,
      submitNewProgramMadc,
      submitNewProgramPav,
      handleProgramChangeMadc,
      handleProgramChangepav,
      submitNewSourceMadc,
      handleSourceChangeMadc,
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
      previewResponse
    };
  },
};
</script>

<style scoped>
.system-admin-container {
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
  align-items: start;
  margin-bottom: 20px;
  gap: 10px;
}
.pipeline-label, .program-label, .source-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 5px;
}
.new-program-input, .new-source-input {
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
</style>
