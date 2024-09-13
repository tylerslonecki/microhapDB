<template>
    <div class="query-container">
      <h2>Database Query</h2>
      <div class="query-form">
        <label for="queryInput">Enter your SQL query:</label>
        <textarea v-model="query" id="queryInput" rows="5"></textarea>
        <button @click="executeQuery">Execute</button>
      </div>
      <div v-if="results">
        <h3>Results:</h3>
        <pre>{{ formattedResults }}</pre>
      </div>
    </div>
  </template>
  
  <script>
  import axiosInstance from '../axiosConfig'; // Import your axios configuration
  
  export default {
    data() {
      return {
        query: '',
        results: null,
      };
    },
    computed: {
      formattedResults() {
        if (!this.results) return '';
        return JSON.stringify(this.results, null, 2);
      }
    },
    methods: {
      async executeQuery() {
        try {
          const response = await axiosInstance.post('/posts/query', { query: this.query });
          this.results = response.data.result;
        } catch (error) {
          console.error("Error executing query:", error);
          this.results = { error: "Error executing query." };
        }
      }
    }
  }
  </script>
  
  <style scoped>
  .query-container {
    padding: 20px;
    max-width: 800px;
    margin: auto;
  }
  
  .query-form {
    margin-bottom: 20px;
  }
  
  textarea {
    width: 100%;
    padding: 10px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 16px;
  }
  
  button {
    padding: 10px 20px;
    font-size: 16px;
    background-color: #00796b;
    color: white;
    border: none;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }
  
  button:hover {
    background-color: #00796b8e;
  }
  
  pre {
    background: #f4f4f4;
    padding: 10px;
    border-radius: 5px;
    overflow: auto;
  }
  </style>