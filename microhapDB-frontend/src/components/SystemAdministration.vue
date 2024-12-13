<template>
  <div class="system-admin-container">
    <div class="upload-section">
      <div class="dropdown-container">
        <label for="pipelineSelect" class="pipeline-label">Please select a Species Database</label>
        <Dropdown 
          v-model="selectedPipeline" 
          :options="pipelineOptions" 
          optionLabel="label" 
          optionValue="value" 
          placeholder="Please select one"
          class="w-full"
        />
      </div>

      <div class="dropdown-container">
        <label for="projectSelect" class="project-label">Please select or add a Project</label>
        <Dropdown
          v-model="selectedProject"
          :options="projectOptions"
          optionLabel="name"
          optionValue="value"
          placeholder="Please select one"
          class="w-full"
        />
        <div v-if="selectedProject === 'new'" class="new-project-input">
          <InputText v-model="newProjectName" placeholder="Enter new project name" />
        </div>
      </div>

      <div class="file-upload-container">
        <FileUpload
          mode="basic"
          multiple
          chooseLabel="Choose Files"
          @choose="handleFileChoose"
        ></FileUpload>



        <Button label="Submit Job" icon="pi pi-upload" @click="submitData" class="upload-button"/>
        <p v-if="uploadMessage">{{ uploadMessage }}</p>
      </div>
    </div>

    <div class="job-status-section">
      <h2>Submitted Jobs</h2>
      <Button label="Refresh Jobs" icon="pi pi-refresh" @click="fetchJobs" class="refresh-button"/>

      <div class="table-container">
        <DataTable :value="jobs" :responsiveLayout="'scroll'" class="job-table">
          <Column field="job_id" header="Job ID"></Column>
          <Column field="status" header="Status"></Column>
          <Column header="Submission Time" :body="submissionTimeTemplate"></Column>
          <Column header="Completion Time" :body="completionTimeTemplate"></Column>
          <Column header="Actions" :body="actionsTemplate"></Column>
        </DataTable>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import axiosInstance from '../axiosConfig';
import { mapGetters, mapActions } from 'vuex';

export default {
  computed: {
    ...mapGetters(['isAuthenticated', 'isAdmin']),
  },
  methods: {
    ...mapActions(['checkAuthStatus', 'logout']),
  },
  setup() {
    const selectedFiles = ref([]);
    const selectedPipeline = ref("");
    const selectedProject = ref("");
    const newProjectName = ref("");
    const projects = ref([]);
    const uploadMessage = ref(null);
    const jobs = ref([]);
    let refreshInterval = null;

    const pipelineOptions = ref([
      { label: 'Alfalfa', value: 'alfalfa' },
      { label: 'Cranberry', value: 'cranberry' },
      { label: 'Blueberry', value: 'blueberry' },
      { label: 'Sweetpotato', value: 'sweetpotato' }
    ]);

    // Dynamically build project options including a "new" option
    const projectOptions = ref([]);

    const fetchProjects = async () => {
      try {
        const response = await axiosInstance.get("/posts/projects/list");
        // Map projects from the server to dropdown options
        // Add a "new" option at the end.
        projectOptions.value = response.data.projects.map((proj) => ({
          name: proj.name,
          value: proj.name
        }));
        projectOptions.value.push({ name: "Add new project", value: "new" });
        projects.value = response.data.projects;
      } catch (error) {
        console.error("Error fetching projects:", error);
      }
    };

    const createProject = async (projectName) => {
      try {
        const response = await axiosInstance.post('/posts/projects/create', { name: projectName });
        await fetchProjects();
        selectedProject.value = response.data.project.name;
      } catch (error) {
        console.error("Error creating project:", error);
        uploadMessage.value = "There was an error creating the project.";
        throw error;
      }
    };

    const handleFileSelect = (event) => {
      // event.files is an array of files
      selectedFiles.value = event.files;
      console.log('Selected files:', selectedFiles.value);
    };

    const submitData = async () => {
      if (!selectedPipeline.value) {
        uploadMessage.value = "Please select a species.";
        return;
      }

      if (!selectedProject.value && !newProjectName.value) {
        uploadMessage.value = "Please select or add a project.";
        return;
      }

      const fd = new FormData();
      selectedFiles.value.forEach((file) => {
        fd.append("file", file);
      });

      fd.append("species", selectedPipeline.value);

      if (selectedProject.value === 'new') {
        if (!newProjectName.value) {
          uploadMessage.value = "Please enter a name for the new project.";
          return;
        }
        try {
          await createProject(newProjectName.value);
          fd.append("project_name", newProjectName.value);
        } catch (error) {
          return;
        }
      } else {
        fd.append("project_name", selectedProject.value);
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
        fetchProjects();
      } catch (error) {
        console.error("There was an error processing the file:", error);
        uploadMessage.value = "There was an error processing the file.";
      }
    };

    const fetchJobs = () => {
      axiosInstance.get('/posts/jobStatus')
        .then(response => {
          jobs.value = response.data;
        })
        .catch(error => {
          console.error("There was an error fetching job statuses: ", error);
        });
    };

    const downloadResults = (jobId) => {
      axiosInstance.get(`/posts/download/${jobId}`, { responseType: 'blob' })
        .then(response => {
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', `${jobId}-results.csv`);
          document.body.appendChild(link);
          link.click();
          link.parentNode.removeChild(link);
        })
        .catch(error => {
          console.error("There was an error downloading the results: ", error);
        });
    };

    // Table column templates
    const submissionTimeTemplate = (rowData) => {
      return new Date(rowData.submission_time).toLocaleString();
    };

    const completionTimeTemplate = (rowData) => {
      return rowData.completion_time ? new Date(rowData.completion_time).toLocaleString() : 'N/A';
    };

    const actionsTemplate = (rowData) => {
      if (rowData.status === 'completed') {
        return (
          `<button class="p-button p-component" onclick='(${downloadResults.toString()})("${rowData.job_id}")'>
             <span class="p-button-icon pi pi-download"></span>
             <span class="p-button-label">Download</span>
           </button>`
        );
      } else {
        return '';
      }
    };

    onMounted(() => {
      fetchJobs();
      fetchProjects();
      refreshInterval = setInterval(fetchJobs, 15000);
    });

    onBeforeUnmount(() => {
      if (refreshInterval) {
        clearInterval(refreshInterval);
      }
    });

    return {
      selectedFiles,
      selectedPipeline,
      selectedProject,
      newProjectName,
      projects,
      uploadMessage,
      pipelineOptions,
      projectOptions,
      handleFileSelect,
      submitData,
      jobs,
      fetchJobs,
      downloadResults,
      submissionTimeTemplate,
      completionTimeTemplate,
      actionsTemplate
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

.pipeline-label, .project-label {
  font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  margin-bottom: 5px;
  color: #00796b;
}

.new-project-input {
  margin-top: 10px;
}

.upload-button {
  margin-top: 10px;
}

.job-status-section h2 {
  color: #00796b; 
  text-align: center;
  margin-bottom: 30px;
}

.refresh-button {
  margin-bottom: 20px;
  display: block;
  margin-left: auto;
  margin-right: auto;
}

.table-container {
  width: 100%;
}
</style>
