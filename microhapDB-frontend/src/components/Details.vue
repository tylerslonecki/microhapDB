<template>
  <div class="details-container">
    <!-- Panel Component as the Title -->
    <Panel header="Details for Selected Alleles" class="mb-4">
      
      <!-- Buttons Container -->
      <div class="buttons-container flex justify-center items-center gap-2 mb-4">
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
          :disabled="!selectedAccessions.length" 
        />

        <!-- Selected Count Display -->
        <div 
          v-if="selectedAccessions.length" 
          class="text-base text-gray-700 font-bold selected-count"
        >
          ( Selected Accessions: {{ selectedAccessions.length }} )
        </div>
      </div>
      
      <!-- DataTable for Detailed Information -->
      <DataTable 
        :value="detailedInfo"
        v-model:selection="selectedAccessions"
        class="datatable-details mb-3 w-full"  
        :loading="loading"
        :paginator="true" 
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[10, 25, 50]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} accessions"
        :rows="size" 
        :totalRecords="detailedInfo.length"
        showGridlines 
        stripedRows
        tableStyle="min-width: 50rem"
        :emptyMessage="'No data available. Please select alleles to view accessions.'"
        selectionMode="multiple" 
        dataKey="uniqueKey" 
        @page="onPageChange"
        paginatorPosition="both"
      > 
        <!-- Paginator Start Slot -->
        <template #paginatorstart>
          <Button 
            type="button" 
            icon="pi pi-refresh" 
            text 
            @click="refreshTable" 
            v-tooltip="{ value: 'Refresh', showDelay: 1000, hideDelay: 300 }"
            class="p-button-text p-button-icon-only"
            :disabled="loading"
          />
        </template>

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

        <!-- Project Column -->
        <Column 
          field="source"
          header="Project"
          sortable
        />

        <!-- Program Column -->
        <Column 
          field="owner"
          header="Program"
          sortable
        />          

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
      selectedAccessions: [],
      loading: false,
      size: 25,
      names: ['Moira', 'Craig','Dongyan', 'Alex', 'Meng', 'Cris', 'Josue', 'Shawn'],
      sourceGroupSize: 5,
      ownerGroupSize: 4
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
        const alleleIds = this.getSelectedSequences.map(seq => seq.alleleid);
        const response = await axiosInstance.post('posts/alleleAccessions/', {
          alleleid: alleleIds
        });
        const alleleToAccessions = {};
        response.data.forEach(item => {
          alleleToAccessions[item.alleleid] = item.accessions;
        });

        const flattenedData = [];
        let projectCounter = 0;
        let ownerCounter = 0;
        let currentSource = '';
        let currentOwner = '';

        this.getSelectedSequences.forEach(seq => {
          const accessions = alleleToAccessions[seq.alleleid] || [];
          accessions.forEach((accession) => {
            if (flattenedData.length % this.sourceGroupSize === 0) {
              currentSource = `Project ${projectCounter % 3}`;
              projectCounter += 1;
            }
            if (flattenedData.length % this.ownerGroupSize === 0) {
              currentOwner = this.names[ownerCounter % this.names.length];
              ownerCounter += 1;
            }
            flattenedData.push({
              uniqueKey: `${seq.alleleid}-${accession}-${flattenedData.length}`,
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
      this.$router.push({ name: 'Query' });
    },
    downloadAccessions() {
      if (!this.selectedAccessions.length) {
        this.$toast.add({ 
          severity: 'warn', 
          summary: 'Warning', 
          detail: 'No accessions selected for download.', 
          life: 3000 
        });
        return;
      }

      const headers = ['Allele ID', 'Accession', 'Project', 'Program'];
      const csvRows = [headers.join(',')];
      this.selectedAccessions.forEach(item => {
        csvRows.push(`${item.alleleid},${item.accession},${item.source},${item.owner}`);
      });

      let csvContent = "data:text/csv;charset=utf-8," 
        + csvRows.join("\n");

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "accessions.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },
    onPageChange(event) {
      this.size = event.rows;
    },
    refreshTable() {
      this.selectedAccessions = [];
      this.fetchDetailedInfo();
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
  /* Center items (buttons + selection count) horizontally */
}

.datatable-details {
  min-width: 50rem;
}

/* Responsive Design */
@media (max-width: 768px) {
  .buttons-container {
    flex-direction: column;
    align-items: center; /* center on small screens as well */
  }

  .buttons-container > * {
    width: 100%;
    justify-content: center;
  }
}
</style>
