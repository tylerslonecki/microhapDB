<template>
    <div class="system-admin-container">
      <div class="upload-section">
        <div class="dropdown-container">
          <label for="pipelineSelect" class="pipeline-label">Please select a Species Database</label>
          <select v-model="selectedPipeline" class="dropdown">
            <option disabled value="">Please select one</option>
            <option value="alfalfa">Alfalfa</option>
            <option value="cranberry">Cranberry</option>
            <option value="blueberry">Blueberry</option>
            <option value="sweetpotato">Sweetpotato</option>
          </select>
        </div>
        <div class="file-upload-container">
          <input type="file" @change="handleFileChange" class="file-input" multiple />
          <button @click="submitData" class="upload-button">Submit Job</button>
          <p v-if="uploadMessage">{{ uploadMessage }}</p>
        </div>
      </div>
      <div class="job-status-section">
        <h2>Submitted Jobs</h2>
        <button @click="fetchJobs" class="refresh-button">Refresh Jobs</button>
        <div class="table-container">
          <table class="job-table">
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Status</th>
                <th>Submission Time</th>
                <th>Completion Time</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="job in jobs" :key="job.job_id">
                <td>{{ job.job_id }}</td>
                <td>{{ job.status }}</td>
                <td>{{ new Date(job.submission_time).toLocaleString() }}</td>
                <td>{{ job.completion_time ? new Date(job.completion_time).toLocaleString() : 'N/A' }}</td>
                <td>
                  <button v-if="job.status === 'completed'" @click="downloadResults(job.job_id)" class="download-button">Download</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, onBeforeUnmount } from 'vue';
  import axiosInstance from '../axiosConfig'; // Import the centralized Axios instance
  
  export default {
    setup() {
      const selectedFiles = ref([]);
      const selectedPipeline = ref("");
      const uploadMessage = ref(null);
      const jobs = ref([]);
      let refreshInterval = null;
  
      const handleFileChange = (event) => {
        selectedFiles.value = Array.from(event.target.files);
        console.log('Selected files:', selectedFiles.value);
      };
  
      const submitData = async () => {
        const fd = new FormData();
        selectedFiles.value.forEach((file) => {
          fd.append("file", file); // Append each file to FormData
        });
  
        // Append the selected pipeline to FormData if needed
        fd.append("species", selectedPipeline.value);
  
        try {
          console.log('Submitting data...');
          const response = await axiosInstance.post(
            "/posts/upload/",
            fd,
            {
              headers: {
                'Content-Type': 'multipart/form-data'
              }
            }
          );
          console.log('Response:', response);
          uploadMessage.value = response.data.message; // Set the message from the backend
        } catch (error) {
          console.error("There was an error processing the file:", error);
          uploadMessage.value = "There was an error processing the file.";
        }
      };
  
      const fetchJobs = () => {
        axiosInstance.get('/posts/jobStatus')
          .then(response => {
            jobs.value = response.data; // Assuming the backend sends an array directly
          })
          .catch(error => {
            console.error("There was an error fetching job statuses: ", error);
          });
      };
  
      const downloadResults = (jobId) => {
        // Send a request to the backend endpoint that serves the results file for a given job ID
        axiosInstance.get(`/posts/download/${jobId}`, { responseType: 'blob' })
          .then(response => {
            // Create a URL for the blob
            const url = window.URL.createObjectURL(new Blob([response.data]));
            // Create a link to download it
            const link = document.createElement('a');
            link.href = url;
            // You can set the filename dynamically based on job ID or any other data
            link.setAttribute('download', `${jobId}-results.csv`);
            document.body.appendChild(link);
            link.click();
            // Clean up and remove the link
            link.parentNode.removeChild(link);
          })
          .catch(error => {
            console.error("There was an error downloading the results: ", error);
          });
      };
  
      onMounted(() => {
        fetchJobs();
        refreshInterval = setInterval(fetchJobs, 15000); // Fetch jobs every 15 seconds
      });
  
      onBeforeUnmount(() => {
        if (refreshInterval) {
          clearInterval(refreshInterval); // Clear the interval when the component is destroyed
        }
      });
  
      return {
        selectedFiles,
        selectedPipeline,
        uploadMessage,
        handleFileChange,
        submitData,
        jobs,
        fetchJobs,
        downloadResults
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
  
  .upload-section .dropdown-container, .upload-section .file-upload-container, .job-status-section .table-container {
    display: flex;
    justify-content: center;
    margin-bottom: 20px;
  }
  
  .pipeline-label, .file-input, .upload-button {
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
    margin: 10px;
  }
  
  .pipeline-label {
    color: #00796b;
  }
  
  .dropdown, .file-input, .upload-button {
    padding: 5px 10px;
    border-radius: 5px;
  }
  
  .dropdown, .file-input {
    border: 1px solid #004d40;
  }
  
  .upload-button {
    border: none;
    cursor: pointer;
    background-color: #00796b;
    color: white;
    transition: background-color 0.3s ease;
  }
  
  .upload-button:hover {
    background-color: #00796b8e;
  }
  
  .upload-button:active {
    transform: scale(0.97);
  }
  
  .job-status-section h2 {
    color: #00796b; /* Aesthetic green color */
    text-align: center;
    margin-bottom: 30px;
  }
  
  .refresh-button, .download-button {
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s ease;
  }
  
  .refresh-button {
    background-color: #00796b; /* Aesthetic green color */
    color: white;
  }
  
  .refresh-button:hover {
    background-color: #00796b8e; /* A darker shade for hover state */
  }
  
  .refresh-button:active, .download-button:active {
    transform: scale(0.97); /* Scales button down when clicked */
  }
  
  .table-container {
    overflow-x: auto; /* Makes table scrollable on small screens */
  }
  
  .job-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 20px;
  }
  
  .job-table th, .job-table td {
    text-align: left;
    padding: 12px;
    border-bottom: 1px solid #ddd;
  }
  
  .job-table th {
    background-color: #00796b;
    color: white;
  }
  
  .job-table tr:nth-child(even) {
    background-color: #f2f2f2;
  }
  
  .download-button {
    background-color: #00796b; /* Bootstrap's success green */
    color: white;
  }
  
  .download-button:hover {
    background-color: #00796b8e; /* A darker shade for hover state */
  }
  </style>
  