<template>
  <div class="upload-container">
    <div class="dropdown-container">
      <label for="pipelineSelect" class="pipeline-label">Please select a Species Database</label>
      <select v-model="selectedPipeline" class="dropdown">
        <option disabled value="">Please select one</option>
        <option value="alfalfa">Alfalfa</option>
        <option value="cranberry">Cranberry</option>
        <option value="bluberry">Blueberry</option>
        <option value="sweetpotato">Sweetpotato</option>
      </select>
    </div>
    <div class="file-upload-container">
      <input type="file" @change="handleFileChange" class="file-input" multiple />
      <button @click="submitData" class="upload-button">Submit Job</button>
      <p v-if="uploadMessage">{{ uploadMessage }}</p>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue';
import axiosInstance from '../axiosConfig'; // Import the centralized Axios instance

export default {
  setup() {
    const selectedFiles = ref([]);
    const selectedPipeline = ref("");
    const uploadMessage = ref(null);

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
      fd.append("pipeline", selectedPipeline.value);

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

    return { selectedFiles, selectedPipeline, uploadMessage, handleFileChange, submitData };
  }
};
</script>

<style scoped>
.upload-container {
  text-align: center;
  margin-top: 20px;
}

.dropdown-container, .file-upload-container {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.file-upload-container {
  align-items: center;
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
</style>
