<template>
    <div class="details-container">
      <!-- Back Button -->
      <div class="mb-2">
        <Button 
          label="Back to Query" 
          icon="pi pi-arrow-left" 
          class="p-button-text p-button-sm" 
          @click="goBack"
        />
      </div>
  
      <!-- Panel for Selected Alleles -->
      <Panel header="Selected Alleles" class="mb-4">
        <!-- Responsive grid for buttons, reduced gap to gap-1 -->
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-1">
          <button
            v-for="allele in getSelectedSequences"
            :key="allele.alleleid || allele.id"
            class="allele-button"
            @click="openAlleleDetail(allele)"
            :title="allele.alleleid || allele.id"
          >
            <div class="allele-button-header">
              <!-- Remove 'truncate' and let text wrap naturally -->
              <h3 class="font-mono text-xs">
                {{ allele.alleleid || allele.id }}
              </h3>
            </div>
          </button>
        </div>
      </Panel>
  
      <!-- Panel for Combined Accessions -->
      <Panel :header="'Combined Accessions (' + uniqueAccessions.length + ')'">
        <div class="mb-2">
          <InputText v-model="searchQuery" placeholder="Search Accessions..." class="p-inputtext-sm" />
        </div>
        <DataTable 
          :value="filteredAccessions"
          :paginator="true"
          :rows="10"
          class="p-datatable-sm"
          :responsiveLayout="'scroll'"
        >
          <Column field="accession" header="Accession" sortable></Column>
          <Column field="source" header="Source" sortable></Column>
          <Column field="owner" header="Owner" sortable></Column>
        </DataTable>
      </Panel>
  
      <!-- Allele Detail Dialog -->
      <Dialog
        header="Allele Details"
        v-model:visible="showDetailDialog"
        :modal="true"
        :closable="true"
        :style="dialogStyle"
        @hide="selectedAlleleDetail = null"
      >
        <div v-if="selectedAlleleDetail" class="p-3">
          <p><strong>Allele ID:</strong> {{ selectedAlleleDetail.alleleid }}</p>
          <p><strong>Sequence:</strong> {{ selectedAlleleDetail.sequence }}</p>
          <p><strong>INFO:</strong> {{ selectedAlleleDetail.info }}</p>
          <p><strong>Associated Trait:</strong> {{ selectedAlleleDetail.associatedTrait }}</p>
          <p><strong>Total Accessions:</strong> {{ selectedAlleleDetail.totalAccessions }}</p>

          <p>
            <strong>Associated Project:</strong>
            <span v-if="selectedAlleleDetail.associatedProject !== 'None'">
              {{ selectedAlleleDetail.associatedProject }}
            </span>
            <span v-else>None</span>
          </p>
          <p>
            <strong>Owner:</strong>
            <span v-if="selectedAlleleDetail.owner">
              {{ selectedAlleleDetail.owner }}
            </span>
            <span v-else>None</span>
          </p>
        </div>
      </Dialog>
    </div>
  </template>
  
  <script>
  import axiosInstance from "../axiosConfig";
  import { mapGetters } from "vuex";
  import Button from "primevue/button";
  import Panel from "primevue/panel";
  import Dialog from "primevue/dialog";
  import DataTable from 'primevue/datatable';
  import Column from 'primevue/column';
  import InputText from 'primevue/inputtext';
  
  export default {
    name: "Details",
    components: {
      Button,
      Panel,
      Dialog,
      DataTable,
      Column,
      InputText
    },
    data() {
      return {
        detailedInfo: [],
        showDetailDialog: false,
        selectedAlleleDetail: null,
        searchQuery: ''
      };
    },
    computed: {
      ...mapGetters(["getSelectedSequences"]),
      uniqueAccessions() {
        const accessions = this.detailedInfo.map(item => ({
          accession: item.accession,
          source: item.source,
          owner: item.owner
        }));
        return [...new Set(accessions.map(acc => acc.accession))].map(acc => {
          const found = accessions.find(a => a.accession === acc);
          return found ? found : { accession: acc, source: 'Unknown', owner: 'Unknown' };
        }).sort((a, b) => a.accession.localeCompare(b.accession));
      },
      filteredAccessions() {
        if (!this.searchQuery) return this.uniqueAccessions;
        const query = this.searchQuery.toLowerCase();
        return this.uniqueAccessions.filter(acc => acc.accession.toLowerCase().includes(query));
      },
      dialogStyle() {
        return {
          width: window.innerWidth < 600 ? '90vw' : '800px'
        };
      }
    },
    methods: {
      async fetchDetailedInfo() {
        if (!this.getSelectedSequences.length) {
          this.detailedInfo = [];
          return;
        }
        try {
          const alleleIds = this.getSelectedSequences.map(seq => seq.alleleid);
          const response = await axiosInstance.post("posts/alleleAccessions/", {
            alleleid: alleleIds
          });
          const alleleToAccessions = {};
          response.data.forEach(item => {
            alleleToAccessions[item.alleleid] = item.accessions;
          });
  
          const flattenedData = [];
          let projectCounter = 0;
          let ownerCounter = 0;
  
          this.getSelectedSequences.forEach(seq => {
            const accessions = alleleToAccessions[seq.alleleid] || [];
            const owner = `Owner ${ownerCounter + 1}`;
            ownerCounter += 1;
  
            const project = `Proj ${projectCounter % 3}`;
            projectCounter += 1;
  
            accessions.forEach(accession => {
              flattenedData.push({
                uniqueKey: `${seq.alleleid}-${accession}-${flattenedData.length}`,
                alleleid: seq.alleleid,
                accession,
                source: project,
                owner: owner
              });
            });
          });
          this.detailedInfo = flattenedData;
        } catch (error) {
          console.error("Error fetching detailed information:", error);
          this.detailedInfo = [];
          this.$toast &&
            this.$toast.add({
              severity: "error",
              summary: "Error",
              detail: "Failed to fetch detailed information.",
              life: 3000
            });
        }
      },
      openAlleleDetail(allele) {
        const detailsForAllele = this.detailedInfo.filter(item => item.alleleid === allele.alleleid);
        const associatedProject = detailsForAllele.length ? detailsForAllele[0].source : "None";
        const owner = detailsForAllele.length ? detailsForAllele[0].owner : "None";
        const totalAccessions = detailsForAllele.length;
  
        this.selectedAlleleDetail = {
          alleleid: allele.alleleid,
          sequence: allele.sequence,
          info: allele.info,
          associatedTrait: allele.associatedTrait,
          associatedProject,
          owner,
          totalAccessions,
        };
        this.showDetailDialog = true;
      },
      goBack() {
        this.$router.push({ name: "Query" });
      },
      handleResize() {
        this.$forceUpdate();
      }
    },
    mounted() {
      this.fetchDetailedInfo();
      window.addEventListener('resize', this.handleResize);
    },
    beforeUnmount() {
      window.removeEventListener('resize', this.handleResize);
    }
  };
  </script>
  
  <style scoped>
  .details-container {
    padding: 10px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  }
  
  /* Make buttons flexible so the text can wrap */
  .allele-button {
    padding: 0.2rem; 
    border: 1px solid #e5e7eb;
    background-color: white;
    cursor: pointer;
    transition: background-color 0.3s, border-color 0.3s, transform 0.3s;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    text-align: left;
    border-radius: 0.5rem;
  }
  
  /* Hover Effect */
  .allele-button:hover {
    background-color: var(--surface-hover, #f0f4c3);
    border-color: var(--primary-color, #8bc34a);
    transform: scale(1.02);
  }
  
  /* Header Styling: allow wrapping, remove truncation */
  .allele-button-header h3 {
    font-size: 0.9rem;
    white-space: normal;          /* allows multi-line wrapping */
    word-wrap: break-word;        /* older property for wrapping text */
    overflow-wrap: anywhere;      /* modern property to break long words */
    margin-bottom: 0.15rem;
  }
  
  /* Dialog Content Styling */
  .dialog-content p {
    font-size: 0.7rem;
    margin: 0.3rem 0;
  }
  
  /* Reduced gap between items from gap-2 to gap-1 in the template */
  .grid {
    display: grid;
  }
  .grid-cols-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .sm\:grid-cols-3 {
    @media (min-width: 640px) {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }
  }
  .md\:grid-cols-4 {
    @media (min-width: 768px) {
      grid-template-columns: repeat(4, minmax(0, 1fr));
    }
  }
  .lg\:grid-cols-6 {
    @media (min-width: 1024px) {
      grid-template-columns: repeat(6, minmax(0, 1fr));
    }
  }
  .gap-1 {
    gap: 0.25rem;
  }
  
  /* Breakpoint adjustments (optional) */
  @media (max-width: 480px) {
    /* Adjust dialog width for very small screens */
    .p-dialog {
      width: 90vw !important;
      max-width: 90vw !important;
    }
  }
  
  /* Utility Classes */
  .text-xs {
    font-size: 0.75rem;
  }
  .mb-4 {
    margin-bottom: 1rem;
  }
  .mb-2 {
    margin-bottom: 0.5rem;
  }
  </style>
  