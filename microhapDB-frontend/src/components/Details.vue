<!-- src/components/Details.vue -->
<template>
    <div class="details-container">
      <!-- Panel Component as the Title -->
      <Panel header="Details for Selected Alleles" class="mb-4">
        
        <!-- Buttons Container -->
        <div class="buttons-container flex justify-end gap-2 mb-4">
          <Button 
            label="Load More Accessions" 
            icon="pi pi-arrow-left" 
            @click="loadMoreAccessions" 
            class="p-button-secondary"
          />
          <Button 
            label="Download Accessions" 
            icon="pi pi-download" 
            @click="downloadAccessions" 
            class="p-button-success"
          />
        </div>
        
        <!-- DataTable for Detailed Information -->
        <DataTable 
          :value="detailedInfo"
          class="datatable-details mb-3 w-full"  
          :loading="loading"
          :paginator="true" 
          :rows="size" 
          :totalRecords="detailedInfo.length"
          :rowsPerPageOptions="[10, 25, 50]"
          showGridlines 
          stripedRows
          tableStyle="min-width: 50rem"
          :emptyMessage="'No data available. Please select alleles to view accessions.'"
          selectionMode="multiple" 
          dataKey="uniqueKey" 
          @page="onPageChange"
        > 
          <!-- Selection Checkbox Column -->
          <Column 
            selectionMode="multiple" 
            headerStyle="width: 3rem" 
            exportable="false" 
          ></Column>
  
          <!-- Allele ID Column -->
          <Column 
            field="alleleid" 
            header="Allele ID" 
            sortable 
          ></Column>
  
          <!-- Accession Column -->
          <Column 
            field="accession" 
            header="Accession" 
            sortable 
          ></Column>
  
          <!-- Source Column -->
          <Column 
            field="source" 
            header="Source" 
            sortable 
          ></Column>
  
          <!-- Owner Column -->
          <Column 
            field="owner" 
            header="Owner" 
            sortable 
          ></Column>          
  
          <!-- Add other columns as needed -->
        </DataTable>
        
      </Panel>
    </div>
  </template>
  
  <script>
  import axiosInstance from '../axiosConfig';
  import DataTable from 'primevue/datatable';
  import Column from 'primevue/column';
  import Button from 'primevue/button';
  import Panel from 'primevue/panel';
  import { mapGetters } from 'vuex';
  
  export default {
    name: 'Details',
    components: {
      DataTable,
      Column,
      Button,
      Panel
    },
    computed: {
      ...mapGetters(['getSelectedSequences'])
    },
    data() {
      return {
        detailedInfo: [],
        loading: false,
        size: 25, // Number of rows per page
        names: ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank', 'Grace', 'Hannah', 'Ian', 'Julia'] // List of first names for "Owner"
      };
    },
    methods: {
      async fetchDetailedInfo() {
        if (!this.getSelectedSequences.length) {
          this.detailedInfo = [];
          return;
        }
  
        this.loading = true;
  
        try {
          // Extract alleleid from selected sequences
          const alleleIds = this.getSelectedSequences.map(seq => seq.alleleid);
  
          // Make a POST request to the new endpoint
          const response = await axiosInstance.post('posts/alleleAccessions/', {
            alleleid: alleleIds
          });
  
          // Create a mapping from alleleid to accessions
          const alleleToAccessions = {};
          response.data.forEach(item => {
            alleleToAccessions[item.alleleid] = item.accessions;
          });
  
          // Flatten the detailedInfo data: one row per accession with dummy "Source" and "Owner"
          const flattenedData = [];
          let projectCounter = 0; // Counter for "Project X"
  
          this.getSelectedSequences.forEach(seq => {
            const accessions = alleleToAccessions[seq.alleleid] || [];
            accessions.forEach((accession) => {
              flattenedData.push({
                uniqueKey: `${seq.alleleid}-${accession}`, // Unique key for dataKey
                alleleid: seq.alleleid,
                accession: accession,
                source: `Project ${projectCounter}`, // Assign "Project X"
                owner: this.names[projectCounter % this.names.length] // Assign owner cyclically from names list
              });
              projectCounter += 1; // Increment project counter
            });
          });
  
          this.detailedInfo = flattenedData;
  
        } catch (error) {
          console.error("Error fetching detailed information:", error);
          this.detailedInfo = [];
          this.$toast.add({ 
            severity: 'error', 
            summary: 'Error', 
            detail: 'Failed to fetch detailed information.', 
            life: 3000 
          });
        } finally {
          this.loading = false;
        }
      },
      loadMoreAccessions() {
        // Navigate back to the Query component
        this.$router.push({ name: 'Query' });
      },
      downloadAccessions() {
        // Implement download functionality here
        this.$toast.add({ 
          severity: 'info', 
          summary: 'Info', 
          detail: 'Download functionality not implemented yet.', 
          life: 3000 
        });
      },
      onPageChange(event) {
        this.size = event.rows;
        // If implementing server-side pagination, handle it here
        // For client-side pagination, no additional actions are needed
      }
    },
    mounted() {
      this.fetchDetailedInfo();
    }
  };
  </script>
  
  <style scoped>
  .details-container {
    padding: 20px;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  }
  
  .buttons-container {
    /* Align buttons to the right with some spacing */
  }
  
  .datatable-details {
    min-width: 50rem;
  }
  
  /* Responsive Design */
  @media (max-width: 768px) {
    .buttons-container {
      flex-direction: column;
      align-items: stretch;
    }
  
    .buttons-container > * {
      width: 100%;
    }
  }
  </style>
  