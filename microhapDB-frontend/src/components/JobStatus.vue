<template>
  <div class="job-status-container">
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
</template>

<script>
import axios from '../axiosConfig';

export default {
  name: 'JobStatus',
  data() {
    return {
      jobs: [], // Job data fetched from your backend
      refreshInterval: null,
    };
  },
  mounted() {
    this.fetchJobs();
    this.refreshInterval = setInterval(this.fetchJobs, 15000); // Fetch jobs every 15 seconds
  },
  beforeUnmount() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval); // Clear the interval when the component is destroyed
    }
  },
  methods: {
    fetchJobs() {
      axios.get('/posts/jobStatus')
        .then(response => {
          this.jobs = response.data; // Assuming the backend sends an array directly
        })
        .catch(error => {
          console.error("There was an error fetching job statuses: ", error);
        });
    },
    downloadResults(jobId) {
      // Send a request to the backend endpoint that serves the results file for a given job ID
      axios.get(`/posts/download/${jobId}`, { responseType: 'blob' })
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
    }
  }
}
</script>


<style>
.job-status-container {
  max-width: 1200px;
  margin: auto;
  padding: 20px;
}

h2 {
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


