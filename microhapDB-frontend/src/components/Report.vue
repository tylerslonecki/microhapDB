<template>
    <div class="report-container">
      <h2>Database Report</h2>
      <button @click="fetchReport" class="refresh-button">Refresh Report</button>
      <div v-if="report" v-html="report" class="report-content"></div>
      <p v-else>No report available.</p>
    </div>
  </template>
  
  <script>
  import axios from 'axios';
  
  export default {
    name: 'DatabaseReport',
    data() {
      return {
        report: '',
      };
    },
    mounted() {
      this.fetchReport(); // Fetch the report when the component is mounted
    },
    methods: {
      fetchReport() {
        axios
          .get('https://myfastapiapp.loca.lt/posts/report')
          .then(response => {
            this.report = response.data;
          })
          .catch(error => {
            console.error("There was an error fetching the report: ", error);
            this.report = ''; // Clear the report in case of an error
          });
      }
    }
  }
  </script>
  
  <style>
  .report-container {
    max-width: 1200px;
    margin: auto;
    padding: 20px;
  }
  
  h2 {
    color: #00796b; /* Aesthetic green color */
    text-align: center;
    margin-bottom: 30px;
  }
  
  .refresh-button {
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-weight: bold;
    transition: background-color 0.3s ease;
    background-color: #00796b; /* Aesthetic green color */
    color: white;
  }
  
  .refresh-button:hover {
    background-color: #00796b8e; /* A darker shade for hover state */
  }
  
  .refresh-button:active {
    transform: scale(0.97); /* Scales button down when clicked */
  }
  
  .report-content {
    border: 1px solid #ddd;
    padding: 20px;
    margin-top: 20px;
  }
  </style>
  