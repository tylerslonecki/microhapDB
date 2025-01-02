<template>
  <div class="system-admin-container">
    <!-- Add ConfirmDialog here -->
    <ConfirmDialog />

    <TabView class="custom-tabview">
      <!-- MADC Upload Tab -->
      <TabPanel header="MADC Upload" class="custom-tabpanel">
        <Panel header="MADC Upload">
          <!-- Upload Section -->
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
            <!-- Loading Indicator -->
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
              <!-- Modify the @click to use confirmSubmitMadcData -->
              <Button 
                label="Submit Job" 
                icon="pi pi-upload" 
                @click="confirmSubmitMadcData" 
                class="upload-button"
              />
              <p v-if="uploadMessageMadc">{{ uploadMessageMadc }}</p>
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

      <!-- PAV Upload Tab -->
      <TabPanel header="PAV Upload" class="custom-tabpanel">
        <Panel header="PAV Upload">
          <!-- Upload Section -->
          <div class="upload-section">
            <!-- Species Database Dropdown for PAV -->
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
              <!-- New Program Input for PAV -->
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

            <!-- PAV File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectPav"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <!-- Modify the @click to use confirmSubmitPavData -->
              <Button 
                label="Submit PAV Job" 
                icon="pi pi-upload" 
                @click="confirmSubmitPavData" 
                class="upload-button"
              />
              <p v-if="uploadMessagePav">{{ uploadMessagePav }}</p>
            </div>
          </div>

          <!-- Job Status Table for PAV Uploads -->
          <div class="job-status-section">
            <DataTable 
              :value="jobsPav" 
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

      <!-- Supplemental Upload Tab -->
      <TabPanel header="Supplemental Upload" class="custom-tabpanel">
        <Panel header="Supplemental Upload">
          <!-- Upload Section -->
          <div class="upload-section">
            <!-- Species Database Dropdown for Supplemental -->
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

            <!-- Supplemental File Upload Section -->
            <div class="file-upload-container">
              <FileUpload
                mode="basic"
                chooseLabel="Choose Files"
                @select="handleFileSelectSupplemental"
                :customUpload="true"
                :auto="false"
                :multiple="true"
              />
              <!-- Modify the @click to use confirmSubmitSupplementalData -->
              <Button 
                label="Submit Supplemental Job" 
                icon="pi pi-upload" 
                @click="confirmSubmitSupplementalData" 
                class="upload-button"
              />
              <p v-if="uploadMessageSupplemental">{{ uploadMessageSupplemental }}</p>
            </div>
          </div>

          <!-- Job Status Table for Supplemental Uploads -->
          <div class="job-status-section">
            <DataTable 
              :value="jobsSupplemental" 
              :responsiveLayout="'scroll'" 
              class="custom-datatable"
              showGridlines 
              stripedRows
            >
              <!-- Header Slot for Status Title -->
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
import { useConfirm } from 'primevue/useconfirm';
import ConfirmDialog from 'primevue/confirmdialog'; // Import ConfirmDialog

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
    ConfirmDialog // Register ConfirmDialog component
  },
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin']),
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
  },
  setup() {

    const confirm = useConfirm();

    // -------------------
    // Shared Upload State
    // -------------------
    const pipelineOptions = ref([
      { label: 'Alfalfa', value: 'alfalfa' },
      { label: 'Cranberry', value: 'cranberry' },
      { label: 'Blueberry', value: 'blueberry' },
      { label: 'Sweetpotato', value: 'sweetpotato' }
    ]);

    const programOptionsMadc = ref([]);
    const programOptionsPav = ref([]);

    // Initialize sourceOptionsMadc with "Add new source" option
    const sourceOptionsMadc = ref([
      { name: "Add new source", value: "new" }
    ]);

    // -------------------
    // MADC Upload State
    // -------------------
    const selectedFilesMadc = ref([]);
    const selectedPipelineMadc = ref("");
    const selectedProgramMadc = ref("");
    const newProgramNameMadc = ref("");
    const uploadMessageMadc = ref(null);
    const jobsMadc = ref([]);

    const selectedSourceMadc = ref("new"); // Initialize to 'new' if no sources

    const newSourceNameMadc = ref("");

    // -------------------
    // PAV Upload State
    // -------------------
    const selectedFilesPav = ref([]);
    const selectedPipelinePav = ref("");
    const selectedProgramPav = ref("");
    const newProgramNamePav = ref("");
    const uploadMessagePav = ref(null);
    const jobsPav = ref([]);


    // -------------------
    // Supplemental Upload State
    // -------------------
    const selectedFilesSupplemental = ref([]);
    const selectedPipelineSupplemental = ref("");
    const uploadMessageSupplemental = ref(null);
    const jobsSupplemental = ref([]);


    // -------------------
    // Fetch Programs and Sources (Shared)
    // -------------------
    const fetchPrograms = async () => {
      try {
        const response = await axiosInstance.get("/posts/programs/list");
        const fetchedPrograms = response.data.programs || [];

        // Map existing programs to dropdown options for each upload type
        const mappedPrograms = fetchedPrograms.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));

        // Update program options for each upload tab
        programOptionsMadc.value = [...mappedPrograms, { name: "Add new program", value: "new" }];
        programOptionsPav.value = [...mappedPrograms, { name: "Add new program", value: "new" }];

        // If no existing programs, set selectedProgram to 'new' to show InputText
        if (fetchedPrograms.length === 0) {
          selectedProgramMadc.value = 'new';
          selectedProgramPav.value = 'new';
        } else {
          // Reset to default placeholder if programs exist
          selectedProgramMadc.value = '';
          selectedProgramPav.value = '';
        }
      } catch (error) {
        console.error("Error fetching programs:", error);
      }
    };

    const fetchSources = async () => {
      try {
        const response = await axiosInstance.get("/posts/sources/list");
        const fetchedSources = response.data || [];

        // Map existing sources to dropdown options for each upload type
        const mappedSources = fetchedSources.map((source) => ({
          name: source.name,
          value: source.name
        }));

        // Always include "Add new source" option
        sourceOptionsMadc.value = [
          ...mappedSources,
          { name: "Add new source", value: "new" }
        ];

        console.log("Source Options:", sourceOptionsMadc.value); // Debugging Line

        // If no existing sources, set selectedSource to 'new' to show InputText
        if (fetchedSources.length === 0) {
          selectedSourceMadc.value = 'new';
        } else {
          // Reset to default placeholder if sources exist
          selectedSourceMadc.value = null; // Or set to a default source if desired
        }
      } catch (error) {
        console.error("Error fetching sources:", error);
      }
    };

    // -------------------
    // Handle Program Change for MADC Upload
    // -------------------
    const handleProgramChangeMadc = () => {
      if (selectedProgramMadc.value === 'new') {
        // Optionally, focus on the newProgramNameMadc input
        // Or perform other actions
      }
    };

    // -------------------
    // Handle Program Change for PAV Upload
    // -------------------
    const handleProgramChangePav = () => {
      if (selectedProgramPav.value === 'new') {
        // Optionally, focus on the newProgramNamePav input
        // Or perform other actions
      }
    };

    // -------------------
    // Handle Source Change for MADC Upload
    // -------------------
    const handleSourceChangeMadc = () => {
      if (selectedSourceMadc.value === 'new') {
        // Optionally, focus on the newSourceNameMadc input
        // Or perform other actions
      }
    };


    // -------------------
    // Create New Program (Shared)
    // -------------------
    const createProgram = async (programName) => {
      try {
        const response = await axiosInstance.post('/posts/programs/create', { name: programName });
        await fetchPrograms();
        // Set the selected program to the newly created program
        return response.data.program.name;
      } catch (error) {
        console.error("Error creating program:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          return error.response.data.detail;
        } else {
          return "There was an error creating the program.";
        }
      }
    };

    // -------------------
    // Create New Source (Shared)
    // -------------------
    const createSource = async (sourceName) => {
      try {
        const response = await axiosInstance.post('/posts/sources/create', { name: sourceName });
        await fetchSources();
        // Correctly access the 'name' field directly
        return response.data.name;
      } catch (error) {
        console.error("Error creating source:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          return error.response.data.detail;
        } else {
          return "There was an error creating the source.";
        }
      }
    };


    // -------------------
    // Handle File Selection for MADC Upload
    // -------------------
    const handleFileSelectMadc = (event) => {
      selectedFilesMadc.value = event.files;
      console.log('Selected files (MADC):', selectedFilesMadc.value);
    };

    // -------------------
    // Handle File Selection for PAV Upload
    // -------------------
    const handleFileSelectPav = (event) => {
      selectedFilesPav.value = event.files;
      console.log('Selected files (PAV):', selectedFilesPav.value);
    };

    // -------------------
    // Handle File Selection for Supplemental Upload
    // -------------------
    const handleFileSelectSupplemental = (event) => {
      selectedFilesSupplemental.value = event.files;
      console.log('Selected files (Supplemental):', selectedFilesSupplemental.value);
    };

    // -------------------
    // Submit MADC Upload Data
    // -------------------
    const submitMadcData = async () => {
      if (!selectedPipelineMadc.value) {
        uploadMessageMadc.value = "Please select a species.";
        return;
      }

      if (!selectedProgramMadc.value) {
        uploadMessageMadc.value = "Please select a program.";
        return;
      }

      if (selectedProgramMadc.value === 'new' && !newProgramNameMadc.value) {
        uploadMessageMadc.value = "Please enter a name for the new program.";
        return;
      }

      if (!selectedSourceMadc.value) {
        uploadMessageMadc.value = "Please select a source.";
        return;
      }

      if (selectedSourceMadc.value === 'new' && !newSourceNameMadc.value) {
        uploadMessageMadc.value = "Please enter a name for the new source.";
        return;
      }

      const fd = new FormData();
      if (selectedFilesMadc.value.length > 0) {
        // Append all selected files
        selectedFilesMadc.value.forEach((file) => {
          fd.append("file", file);
        });
      } else {
        uploadMessageMadc.value = "No file selected.";
        return;
      }

      fd.append("species", selectedPipelineMadc.value);

      if (selectedProgramMadc.value === 'new') {
        try {
          const newProgram = await createProgram(newProgramNameMadc.value.trim());
          if (typeof newProgram === 'string') {
            if (newProgram === "There was an error creating the program.") {
              uploadMessageMadc.value = newProgram;
              return;
            }
            fd.append("program_name", newProgram);
            selectedProgramMadc.value = newProgram;
            newProgramNameMadc.value = ""; // Clear input after creation
            uploadMessageMadc.value = "Program created successfully.";
          }
        } catch (error) {
          return;
        }
      } else {
        fd.append("program_name", selectedProgramMadc.value);
      }

      if (selectedSourceMadc.value === 'new') {
        try {
          const newSource = await createSource(newSourceNameMadc.value.trim());
          if (typeof newSource === 'string') {
            if (newSource === "There was an error creating the source.") {
              uploadMessageMadc.value = newSource;
              return;
            }
            fd.append("source_name", newSource);
            selectedSourceMadc.value = newSource;
            newSourceNameMadc.value = ""; // Clear input after creation
            uploadMessageMadc.value = uploadMessageMadc.value
              ? `${uploadMessageMadc.value} Source created successfully.`
              : "Source created successfully.";
          }
        } catch (error) {
          return;
        }
      } else {
        fd.append("source_name", selectedSourceMadc.value);
      }

      try {
        const response = await axiosInstance.post(
          "/posts/upload/",
          fd,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        uploadMessageMadc.value = response.data.message;
        fetchJobsMadc();
        // No need to refetch programs or sources here since createProgram and createSource already did it
      } catch (error) {
        console.error("There was an error processing the MADC upload file:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessageMadc.value = error.response.data.detail;
        } else {
          uploadMessageMadc.value = "There was an error processing the file.";
        }
      }
    };

    // -------------------
    // Submit PAV Upload Data
    // -------------------
    const submitPavData = async () => {
      if (!selectedPipelinePav.value) {
        uploadMessagePav.value = "Please select a species.";
        return;
      }

      if (!selectedProgramPav.value) {
        uploadMessagePav.value = "Please select a program.";
        return;
      }

      if (selectedProgramPav.value === 'new' && !newProgramNamePav.value) {
        uploadMessagePav.value = "Please enter a name for the new program.";
        return;
      }

      const fd = new FormData();
      if (selectedFilesPav.value.length > 0) {
        // Append all selected files
        selectedFilesPav.value.forEach((file) => {
          fd.append("file", file);
        });
      } else {
        uploadMessagePav.value = "No file selected.";
        return;
      }

      fd.append("species", selectedPipelinePav.value);

      if (selectedProgramPav.value === 'new') {
        try {
          const newProgram = await createProgram(newProgramNamePav.value.trim());
          if (typeof newProgram === 'string') {
            if (newProgram === "There was an error creating the program.") {
              uploadMessagePav.value = newProgram;
              return;
            }
            fd.append("program_name", newProgram);
            selectedProgramPav.value = newProgram;
            newProgramNamePav.value = ""; // Clear input after creation
            uploadMessagePav.value = "Program created successfully.";
          }
        } catch (error) {
          return;
        }
      } else {
        fd.append("program_name", selectedProgramPav.value);
      }

      try {
        const response = await axiosInstance.post(
          "/posts/pav_upload/",
          fd,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        uploadMessagePav.value = response.data.message;
        fetchJobsPav();
        // No need to refetch programs or sources here since createProgram and createSource already did it
      } catch (error) {
        console.error("There was an error processing the PAV upload file:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessagePav.value = error.response.data.detail;
        } else {
          uploadMessagePav.value = "There was an error processing the file.";
        }
      }
    };

    // -------------------
    // Submit Supplemental Upload Data
    // -------------------
    const submitSupplementalData = async () => {
      if (!selectedPipelineSupplemental.value) {
        uploadMessageSupplemental.value = "Please select a species.";
        return;
      }

      const fd = new FormData();
      if (selectedFilesSupplemental.value.length > 0) {
        // Append all selected files
        selectedFilesSupplemental.value.forEach((file) => {
          fd.append("file", file);
        });
      } else {
        uploadMessageSupplemental.value = "No file selected.";
        return;
      }

      fd.append("species", selectedPipelineSupplemental.value);


      try {
        const response = await axiosInstance.post(
          "/posts/supplemental_upload/",
          fd,
          {
            headers: { 'Content-Type': 'multipart/form-data' }
          }
        );
        uploadMessageSupplemental.value = response.data.message;
        fetchJobsSupplemental();
        // No need to refetch programs or sources here since createProgram and createSource already did it
      } catch (error) {
        console.error("There was an error processing the Supplemental upload file:", error);
        if (error.response && error.response.data && error.response.data.detail) {
          uploadMessageSupplemental.value = error.response.data.detail;
        } else {
          uploadMessageSupplemental.value = "There was an error processing the file.";
        }
      }
    };

    // -------------------
    // Submit New Program for MADC Upload
    // -------------------
    const submitNewProgramMadc = async () => {
      if (!newProgramNameMadc.value.trim()) {
        uploadMessageMadc.value = "Please enter a valid program name.";
        return;
      }

      try {
        const newProgram = await createProgram(newProgramNameMadc.value.trim());
        if (typeof newProgram === 'string') {
          if (newProgram === "There was an error creating the program.") {
            uploadMessageMadc.value = newProgram;
            return;
          }
          selectedProgramMadc.value = newProgram;
          newProgramNameMadc.value = ""; // Clear input after creation
          uploadMessageMadc.value = "Program created successfully.";
        }
      } catch (error) {
        // Error message is already set in createProgram
      }
    };

    // -------------------
    // Submit New Program for PAV Upload
    // -------------------
    const submitNewProgramPav = async () => {
      if (!newProgramNamePav.value.trim()) {
        uploadMessagePav.value = "Please enter a valid program name.";
        return;
      }

      try {
        const newProgram = await createProgram(newProgramNamePav.value.trim());
        if (typeof newProgram === 'string') {
          if (newProgram === "There was an error creating the program.") {
            uploadMessagePav.value = newProgram;
            return;
          }
          selectedProgramPav.value = newProgram;
          newProgramNamePav.value = ""; // Clear input after creation
          uploadMessagePav.value = "Program created successfully.";
        }
      } catch (error) {
        // Error message is already set in createProgram
      }
    };

    // -------------------
    // Submit New Source for MADC Upload
    // -------------------
    const submitNewSourceMadc = async () => {
      if (!newSourceNameMadc.value.trim()) {
        uploadMessageMadc.value = "Please enter a valid source name.";
        return;
      }

      try {
        const newSource = await createSource(newSourceNameMadc.value.trim());
        if (typeof newSource === 'string') {
          if (newSource === "There was an error creating the source.") {
            uploadMessageMadc.value = newSource;
            return;
          }
          selectedSourceMadc.value = newSource;
          newSourceNameMadc.value = ""; // Clear input after creation
          uploadMessageMadc.value = uploadMessageMadc.value
            ? `${uploadMessageMadc.value} Source created successfully.`
            : "Source created successfully.";
        }
      } catch (error) {
        // Error message is already set in createSource
      }
    };

    // -------------------
    // Fetch Jobs for MADC Upload
    // -------------------
    const fetchJobsMadc = async () => {
      try {
        const response = await axiosInstance.get('/posts/jobStatus');
        jobsMadc.value = response.data;
      } catch (error) {
        console.error("There was an error fetching MADC job statuses: ", error);
      }
    };

    // -------------------
    // Fetch Jobs for PAV Upload
    // -------------------
    const fetchJobsPav = async () => {
      try {
        const response = await axiosInstance.get('/posts/pav_jobStatus');
        jobsPav.value = response.data;
      } catch (error) {
        console.error("There was an error fetching PAV job statuses: ", error);
      }
    };

    // -------------------
    // Fetch Jobs for Supplemental Upload
    // -------------------
    const fetchJobsSupplemental = async () => {
      try {
        const response = await axiosInstance.get('/posts/supplemental_jobStatus');
        jobsSupplemental.value = response.data;
      } catch (error) {
        console.error("There was an error fetching Supplemental job statuses: ", error);
      }
    };

    // -------------------
    // Confirmation for MADC Submit
    // -------------------
    const confirmSubmitMadcData = () => {
      confirm.require({
        message: 'Are you sure you want to proceed with the MADC submission?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: submitMadcData, // Call the existing submit method on accept
        reject: () => {
          // Optional: Handle rejection (e.g., show a message or perform an action)
          console.log('MADC submission canceled by the user.');
        }
      });
    };

    // -------------------
    // Confirmation for PAV Submit
    // -------------------
    const confirmSubmitPavData = () => {
      confirm.require({
        message: 'Are you sure you want to proceed with the PAV submission?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: submitPavData, // Call the existing submit method on accept
        reject: () => {
          // Optional: Handle rejection
          console.log('PAV submission canceled by the user.');
        }
      });
    };

    // -------------------
    // Confirmation for Supplemental Submit
    // -------------------
    const confirmSubmitSupplementalData = () => {
      confirm.require({
        message: 'Are you sure you want to proceed with the Supplemental submission?',
        header: 'Confirmation',
        icon: 'pi pi-exclamation-triangle',
        accept: submitSupplementalData, // Call the existing submit method on accept
        reject: () => {
          // Optional: Handle rejection
          console.log('Supplemental submission canceled by the user.');
        }
      });
    };

    // -------------------
    // Fetch All Data on Mount
    // -------------------
    onMounted(() => {
      fetchJobsMadc();
      fetchJobsPav();
      fetchJobsSupplemental();
      fetchPrograms();
      fetchSources();
      // Refresh jobs every 15 seconds
      setInterval(() => {
        fetchJobsMadc();
        fetchJobsPav();
        fetchJobsSupplemental();
      }, 15000);
    });

    return {
      // Shared
      pipelineOptions,

      // Program Options
      programOptionsMadc,
      programOptionsPav,

      // Source Options
      sourceOptionsMadc,

      // MADC Upload
      selectedFilesMadc,
      selectedPipelineMadc,
      selectedProgramMadc,
      newProgramNameMadc,
      uploadMessageMadc,
      jobsMadc,
      selectedSourceMadc,
      newSourceNameMadc,
      handleFileSelectMadc,
      submitMadcData,
      submitNewProgramMadc,
      handleProgramChangeMadc,
      submitNewSourceMadc,
      handleSourceChangeMadc,

      // PAV Upload
      selectedFilesPav,
      selectedPipelinePav,
      selectedProgramPav,
      newProgramNamePav,
      uploadMessagePav,
      jobsPav,
      handleFileSelectPav,
      submitPavData,
      submitNewProgramPav,
      handleProgramChangePav,

      // Supplemental Upload
      selectedFilesSupplemental,
      selectedPipelineSupplemental,
      uploadMessageSupplemental,
      jobsSupplemental,
      handleFileSelectSupplemental,
      submitSupplementalData,

      // Confirmation Methods
      confirmSubmitMadcData,
      confirmSubmitPavData,
      confirmSubmitSupplementalData
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

.pipeline-label, .program-label, .source-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 5px;
  /* color: #00796b; */
}

.new-program-input, .new-source-input {
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
