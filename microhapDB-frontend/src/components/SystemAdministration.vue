<template>
  <div class="system-admin-container">
    <TabView class="custom-tabview">
      <!-- Standard Upload Tab -->
      <TabPanel header="MADC Upload" class="custom-tabpanel">
        <Panel header="MADC Upload">
          <!-- Upload Section -->
          <div class="upload-section">
            <!-- Species Database Dropdown -->
            <div class="dropdown-container">
              <label for="pipelineSelect" class="pipeline-label">Please select a Species Database</label>
              <Dropdown 
                id="pipelineSelect"
                v-model="selectedPipeline" 
                :options="pipelineOptions" 
                optionLabel="label" 
                optionValue="value" 
                placeholder="Please select one"
                class="w-full"
              />
            </div>

            <!-- Program Dropdown -->
            <div class="dropdown-container">
              <label for="programSelect" class="program-label">Please select or add Program</label>
              <Dropdown
                id="programSelect"
                v-model="selectedProgram"
                :options="programOptions"
                optionLabel="name"
                optionValue="value"
                placeholder="Please select one"
                class="w-full"
                @change="handleProgramChange"
              />
              <!-- New Program Input -->
              <div v-if="selectedProgram === 'new'" class="new-program-input">
                <InputText v-model="newProgramName" placeholder="Enter new program name" />
                <Button 
                  label="Create Program" 
                  icon="pi pi-plus" 
                  @click="submitNewProgram"
                  class="mt-2"
                />
              </div>
            </div>

            <!-- File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelect"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <Button 
                label="Submit Job" 
                icon="pi pi-upload" 
                @click="submitData" 
                class="upload-button"
              />
              <p v-if="uploadMessage">{{ uploadMessage }}</p>
            </div>
          </div>

          <!-- Job Status Table for Standard Uploads -->
          <div class="job-status-section">
            
            <DataTable 
            :value="jobsStandard" 
            :responsiveLayout="'scroll'" 
            class="custom-datatable"
            showGridlines 
            stripedRows
            >
              <!-- Header Slot for Status Title -->
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

      <!-- EAV Upload Tab -->
      <TabPanel header="PAV Upload" class="custom-tabpanel">
        <Panel header="PAV Upload">
          <!-- Upload Section -->
          <div class="upload-section">
            <!-- Species Database Dropdown for EAV -->
            <div class="dropdown-container">
              <label for="eavPipelineSelect" class="pipeline-label">Please select a Species Database</label>
              <Dropdown 
                id="eavPipelineSelect"
                v-model="selectedPipelineEav" 
                :options="pipelineOptions" 
                optionLabel="label" 
                optionValue="value" 
                placeholder="Please select one"
                class="w-full"
              />
            </div>

            <!-- Program Dropdown for EAV -->
            <div class="dropdown-container">
              <label for="eavProgramSelect" class="program-label">Please select or add Program</label>
              <Dropdown
                id="eavProgramSelect"
                v-model="selectedProgramEav"
                :options="programOptionsEav"
                optionLabel="name"
                optionValue="value"
                placeholder="Please select one"
                class="w-full"
                @change="handleProgramChangeEav"
              />
              <!-- New Program Input for EAV -->
              <div v-if="selectedProgramEav === 'new'" class="new-program-input">
                <InputText v-model="newProgramNameEav" placeholder="Enter new program name" />
                <Button 
                  label="Create Program" 
                  icon="pi pi-plus" 
                  @click="submitNewProgramEav"
                  class="mt-2"
                />
              </div>
            </div>

            <!-- EAV File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectEav"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <Button 
                label="Submit PAV Job" 
                icon="pi pi-upload" 
                @click="submitEavData" 
                class="upload-button"
              />
              <p v-if="uploadMessageEav">{{ uploadMessageEav }}</p>
            </div>
          </div>

          <!-- Job Status Table for EAV Uploads -->
          <div class="job-status-section">
            <DataTable 
              :value="jobsStandard" 
              :responsiveLayout="'scroll'" 
              class="custom-datatable"
              showGridlines 
              stripedRows
              >
              <!-- Header Slot for Status Title -->
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
    </TabView>
  </div>
</template>




<script>
import { ref, onMounted } from 'vue';
import axiosInstance from '../axiosConfig';
import { mapGetters, mapActions } from 'vuex';

// Import PrimeVue components
import Dropdown from 'primevue/dropdown';
import FileUpload from 'primevue/fileupload';
import Button from 'primevue/button';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import InputText from 'primevue/inputtext';
import TabView from 'primevue/tabview';
import TabPanel from 'primevue/tabpanel';
import Panel from 'primevue/panel'; // Import Panel

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
    Panel // Register Panel
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin']),
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
  },
  setup() {
    // -------------------
    // Standard Upload State
    // -------------------
    const selectedFiles = ref([]);
    const selectedPipeline = ref("");
    const selectedProgram = ref("");
    const newProgramName = ref("");
    const uploadMessage = ref(null);
    const jobsStandard = ref([]);

    // Dropdown Options
    const pipelineOptions = ref([
      { label: 'Alfalfa', value: 'alfalfa' },
      { label: 'Cranberry', value: 'cranberry' },
      { label: 'Blueberry', value: 'blueberry' },
      { label: 'Sweetpotato', value: 'sweetpotato' }
    ]);

    const programOptions = ref([]);

    // -------------------
    // EAV Upload State
    // -------------------
    const selectedFilesEav = ref([]);
    const selectedPipelineEav = ref("");
    const selectedProgramEav = ref("");
    const newProgramNameEav = ref("");
    const uploadMessageEav = ref(null);
    const jobsEavList = ref([]);

    const programOptionsEav = ref([]);

    // -------------------
    // Fetch Programs for Standard Upload
    // -------------------
    const fetchPrograms = async () => {
      try {
        const response = await axiosInstance.get("/posts/programs/list");
        const fetchedPrograms = response.data.programs || [];

        // Map existing programs to dropdown options
        programOptions.value = fetchedPrograms.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));

        // Always add the "Add new program" option
        programOptions.value.push({ name: "Add new program", value: "new" });

        // If no existing programs, set selectedProgram to 'new' to show InputText
        if (fetchedPrograms.length === 0) {
          selectedProgram.value = 'new';
        } else {
          // Reset to default placeholder if programs exist
          selectedProgram.value = '';
        }
      } catch (error) {
        console.error("Error fetching programs:", error);
      }
    };

    // -------------------
    // Fetch Programs for EAV Upload
    // -------------------
    const fetchProgramsEav = async () => {
      try {
        const response = await axiosInstance.get("/posts/programs/list");
        const fetchedPrograms = response.data.programs || [];

        // Map existing programs to dropdown options
        programOptionsEav.value = fetchedPrograms.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));

        // Always add the "Add new program" option
        programOptionsEav.value.push({ name: "Add new program", value: "new" });

        // If no existing programs, set selectedProgramEav to 'new' to show InputText
        if (fetchedPrograms.length === 0) {
          selectedProgramEav.value = 'new';
        } else {
          // Reset to default placeholder if programs exist
          selectedProgramEav.value = '';
        }
      } catch (error) {
        console.error("Error fetching programs for EAV:", error);
      }
    };

    // -------------------
    // Handle Program Change for Standard Upload
    // -------------------
    const handleProgramChange = () => {
      if (selectedProgram.value === 'new') {
        // Optionally, focus on the newProgramName input
        // Or perform other actions
      }
    };

    // -------------------
    // Handle Program Change for EAV Upload
    // -------------------
    const handleProgramChangeEav = () => {
      if (selectedProgramEav.value === 'new') {
        // Optionally, focus on the newProgramNameEav input
        // Or perform other actions
      }
    };

    // -------------------
    // Create New Program for Standard Upload
    // -------------------
    const createProgram = async (programName) => {
      try {
        const response = await axiosInstance.post('/posts/programs/create', { name: programName });
        await fetchPrograms();
        selectedProgram.value = response.data.program.name;
        newProgramName.value = ""; // Clear input after creation
        uploadMessage.value = "Program created successfully.";
      } catch (error) {
        console.error("Error creating program:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessage.value = error.response.data.detail;
        } else {
          uploadMessage.value = "There was an error creating the program.";
        }
        throw error;
      }
    };

    // -------------------
    // Create New Program for EAV Upload
    // -------------------
    const createProgramEav = async (programName) => {
      try {
        const response = await axiosInstance.post('/posts/programs/create', { name: programName });
        await fetchProgramsEav();
        selectedProgramEav.value = response.data.program.name;
        newProgramNameEav.value = ""; // Clear input after creation
        uploadMessageEav.value = "Program created successfully.";
      } catch (error) {
        console.error("Error creating EAV program:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessageEav.value = error.response.data.detail;
        } else {
          uploadMessageEav.value = "There was an error creating the program.";
        }
        throw error;
      }
    };

    // -------------------
    // Handle File Selection for Standard Upload
    // -------------------
    const handleFileSelect = (event) => {
      selectedFiles.value = event.files;
      console.log('Selected files (Standard):', selectedFiles.value);
    };

    // -------------------
    // Handle File Selection for EAV Upload
    // -------------------
    const handleFileSelectEav = (event) => {
      selectedFilesEav.value = event.files;
      console.log('Selected files (EAV):', selectedFilesEav.value);
    };

    // -------------------
    // Submit Standard Upload Data
    // -------------------
    const submitData = async () => {
      if (!selectedPipeline.value) {
        uploadMessage.value = "Please select a species.";
        return;
      }

      if (!selectedProgram.value) {
        uploadMessage.value = "Please select a program.";
        return;
      }

      if (selectedProgram.value === 'new' && !newProgramName.value) {
        uploadMessage.value = "Please enter a name for the new program.";
        return;
      }

      const fd = new FormData();
      if (selectedFiles.value.length > 0) {
        // Append all selected files
        selectedFiles.value.forEach((file) => {
          fd.append("file", file);
        });
      } else {
        uploadMessage.value = "No file selected.";
        return;
      }

      fd.append("species", selectedPipeline.value);

      if (selectedProgram.value === 'new') {
        try {
          await createProgram(newProgramName.value);
          fd.append("program_name", newProgramName.value);
        } catch (error) {
          return;
        }
      } else {
        fd.append("program_name", selectedProgram.value);
      }

      try {
        const response = await axiosInstance.post(
          "/posts/upload/",
          fd,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        uploadMessage.value = response.data.message;
        fetchJobsStandard();
        fetchPrograms();
      } catch (error) {
        console.error("There was an error processing the standard upload file:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessage.value = error.response.data.detail;
        } else {
          uploadMessage.value = "There was an error processing the file.";
        }
      }
    };

    // -------------------
    // Submit EAV Upload Data
    // -------------------
    const submitEavData = async () => {
      if (!selectedPipelineEav.value) {
        uploadMessageEav.value = "Please select a species.";
        return;
      }

      if (!selectedProgramEav.value) {
        uploadMessageEav.value = "Please select a program.";
        return;
      }

      if (selectedProgramEav.value === 'new' && !newProgramNameEav.value) {
        uploadMessageEav.value = "Please enter a name for the new program.";
        return;
      }

      const fd = new FormData();
      if (selectedFilesEav.value.length > 0) {
        // Append all selected files
        selectedFilesEav.value.forEach((file) => {
          fd.append("file", file);
        });
      } else {
        uploadMessageEav.value = "No file selected.";
        return;
      }

      fd.append("species", selectedPipelineEav.value);

      if (selectedProgramEav.value === 'new') {
        try {
          await createProgramEav(newProgramNameEav.value);
          fd.append("program_name", newProgramNameEav.value);
        } catch (error) {
          return;
        }
      } else {
        fd.append("program_name", selectedProgramEav.value);
      }

      try {
        const response = await axiosInstance.post(
          "/posts/eav_upload/",
          fd,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        uploadMessageEav.value = response.data.message;
        fetchJobsEav();
        fetchProgramsEav();
      } catch (error) {
        console.error("There was an error processing the EAV upload file:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessageEav.value = error.response.data.detail;
        } else {
          uploadMessageEav.value = "There was an error processing the file.";
        }
      }
    };

    // -------------------
    // Submit New Program for Standard Upload
    // -------------------
    const submitNewProgram = async () => {
      if (!newProgramName.value.trim()) {
        uploadMessage.value = "Please enter a valid program name.";
        return;
      }

      try {
        await createProgram(newProgramName.value.trim());
      } catch (error) {
        // Error message is already set in createProgram
      }
    };

    // -------------------
    // Submit New Program for EAV Upload
    // -------------------
    const submitNewProgramEav = async () => {
      if (!newProgramNameEav.value.trim()) {
        uploadMessageEav.value = "Please enter a valid program name.";
        return;
      }

      try {
        await createProgramEav(newProgramNameEav.value.trim());
      } catch (error) {
        // Error message is already set in createProgramEav
      }
    };

    // -------------------
    // Fetch Jobs for Standard Upload
    // -------------------
    const fetchJobsStandard = async () => {
      try {
        const response = await axiosInstance.get('/posts/jobStatus');
        jobsStandard.value = response.data;
      } catch (error) {
        console.error("There was an error fetching standard job statuses: ", error);
      }
    };

    // -------------------
    // Fetch Jobs for EAV Upload
    // -------------------
    const fetchJobsEav = async () => {
      try {
        const response = await axiosInstance.get('/posts/eav_jobStatus');
        jobsEavList.value = response.data;
      } catch (error) {
        console.error("There was an error fetching EAV job statuses: ", error);
      }
    };


    // -------------------
    // Fetch All Jobs on Mount
    // -------------------
    onMounted(() => {
      fetchJobsStandard();
      fetchJobsEav();
      fetchPrograms();
      fetchProgramsEav();
      // Refresh jobs every 15 seconds
      setInterval(() => {
        fetchJobsStandard();
        fetchJobsEav();
      }, 15000);
    });

    return {
      // Standard Upload
      selectedFiles,
      selectedPipeline,
      selectedProgram,
      newProgramName,
      uploadMessage,
      pipelineOptions,
      programOptions,
      handleFileSelect,
      submitData,
      submitNewProgram,
      jobsStandard,

      // EAV Upload
      selectedFilesEav,
      selectedPipelineEav,
      selectedProgramEav,
      newProgramNameEav,
      uploadMessageEav,
      programOptionsEav,
      handleFileSelectEav,
      submitEavData,
      submitNewProgramEav,
      jobsEavList,

      // Shared Handlers
      handleProgramChange,
      handleProgramChangeEav
    };
  }
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

.pipeline-label, .program-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 5px;
  /* color: #00796b; */
}

.new-program-input {
  margin-top: 10px;
}

.upload-button {
  margin-top: 10px;
}

/* Remove h2 styles since we're not using h2 headers anymore */
/*
.job-status-section h2 {
  color: #00796b; 
  text-align: center;
  margin-bottom: 30px;
}
*/

.table-container {
  width: 100%;
}

.table-header {
  font-size: 1.25rem;
  font-weight: bold;
}

.p-button-success {
  margin-right: 0.5em;
}

/* Optional: Adjust spacing within tabs */
.p-tabview .p-tabview-panels {
  margin-top: 20px;
}
</style>
