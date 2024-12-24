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
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[10, 25, 50]"
        currentPageReportTemplate="Showing {first} to {last}  of  {totalRecords} accessions"
        :rows="size" 
        :totalRecords="detailedInfo.length"
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
      names: ['Moira', 'Craig','Dongyan', 'Alex', 'Meng', 'Cris', 'Josue', 'Shawn'],
      sourceGroupSize: 5, // Number of consecutive rows with the same source
      ownerGroupSize: 4  // Number of consecutive rows with the same owner
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
        let ownerCounter = 0;    // Counter for owners

        let currentSource = '';
        let currentOwner = '';

        this.getSelectedSequences.forEach(seq => {
          const accessions = alleleToAccessions[seq.alleleid] || [];
          accessions.forEach((accession) => {
            // Assign "Source" every sourceGroupSize rows
            if (flattenedData.length % this.sourceGroupSize === 0) {
              currentSource = `Project ${projectCounter % 3}`; // Cycles through Project 0, 1, 2
              projectCounter += 1;
            }

            // Assign "Owner" every ownerGroupSize rows
            if (flattenedData.length % this.ownerGroupSize === 0) {
              currentOwner = this.names[ownerCounter % this.names.length]; // Cycles through names
              ownerCounter += 1;
            }

            flattenedData.push({
              uniqueKey: `${seq.alleleid}-${accession}-${flattenedData.length}`, // Unique key for dataKey
              alleleid: seq.alleleid,
              accession: accession,
              source: currentSource,
              owner: currentOwner
            });
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
      // Example: Convert detailedInfo to CSV and trigger download
      if (!this.detailedInfo.length) {
        this.$toast.add({ 
          severity: 'warn', 
          summary: 'Warning', 
          detail: 'No data available to download.', 
          life: 3000 
        });
        return;
      }

      const headers = ['Allele ID', 'Accession', 'Source', 'Owner'];
      const rows = this.detailedInfo.map(item => [
        item.alleleid, 
        item.accession, 
        item.source, 
        item.owner
      ]);
      let csvContent = "data:text/csv;charset=utf-8," 
        + headers.join(",") + "\n" 
        + rows.map(e => e.join(",")).join("\n");

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "accessions.csv");
      document.body.appendChild(link); // Required for FF

      link.click(); // This will download the data file named "accessions.csv"
      document.body.removeChild(link);
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
