<!--DetailsAlt.vue-->
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
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-1">
          <button
            v-for="(allele, index) in getSelectedSequences"
            :key="`${allele.alleleid || allele.id}-${index}`"
            class="allele-button"
            @click="openAlleleDetail(allele)"
            :title="allele.alleleid || allele.id"
          >
            <span class="remove-btn" @click.stop="removeAllele(allele, index)">X</span>
            <div class="allele-button-header">
              <h3 class="font-mono text-xs">
                {{ allele.alleleid || allele.id }}
              </h3>
              <span class="accession-count text-xs">
                {{ getAlleleAccessionCount(allele) }}
              </span>
            </div>
          </button>
        </div>
      </Panel>
  
      <!-- Panel for Shared Accessions -->
      <Panel class="mb-4">
        <template #header>
          <div class="header-container">
            <span>Shared Accessions ({{ sharedAccessions.length }})</span>
            <Button 
              icon="pi pi-info-circle" 
              class="p-button-text p-button-sm info-icon" 
              @click="showSharedInfoDialog = true" 
            />
          </div>
        </template>
        <!-- Search field for Shared Accessions -->
        <div class="mb-2">
          <InputText 
            v-model="searchSharedQuery" 
            placeholder="Search Shared Accessions..." 
            class="p-inputtext-sm" 
          />
        </div>
        <DataTable 
          :value="filteredSharedAccessions"
          paginator
          :rows="10"
          class="p-datatable-sm"
          responsiveLayout="scroll"
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        >
          <!-- Optional paginator start slot -->
          <template #paginatorstart>
            <!-- Uncomment if needed
            <Button 
              type="button" 
              icon="pi pi-refresh" 
              text 
              @click="refreshSharedTable" 
              v-tooltip="{ value: 'Refresh', showDelay: 1000, hideDelay: 300 }"
            />-->
          </template>
          <!-- Paginator end slot with download button -->
          <template #paginatorend>
            <Button 
              type="button"
              icon="pi pi-download"
              text
              @click="downloadSharedTable"
              v-tooltip.left="{ value: 'Download as .CSV', showDelay: 1000, hideDelay: 300 }"
            />
          </template>
          <Column field="accession" header="Accession" sortable />
          <Column field="source" header="Project" sortable />
          <Column field="owner" header="Program" sortable />
        </DataTable>
      </Panel>
  
      <!-- Panel for Combined Accessions -->
      <Panel>
        <template #header>
          <div class="header-container">
            <span>Combined Accessions ({{ uniqueAccessions.length }})</span>
            <Button 
              icon="pi pi-info-circle" 
              class="p-button-text p-button-sm info-icon" 
              @click="showCombinedInfoDialog = true" 
            />
          </div>
        </template>
        <div class="mb-2">
          <InputText 
            v-model="searchQuery" 
            placeholder="Search Accessions..." 
            class="p-inputtext-sm" 
          />
        </div>
        <DataTable 
          :value="filteredAccessions"
          paginator
          :rows="10"
          class="p-datatable-sm"
          responsiveLayout="scroll"
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        >
          <!-- Optional paginator start slot -->
          <template #paginatorstart>
            <!-- Uncomment if needed
            <Button 
              type="button" 
              icon="pi pi-refresh" 
              text 
              @click="refreshCombinedTable" 
              v-tooltip="{ value: 'Refresh', showDelay: 1000, hideDelay: 300 }"
            />-->
          </template>
          <!-- Paginator end slot with download button -->
          <template #paginatorend>
            <Button 
              type="button"
              icon="pi pi-download"
              text
              @click="downloadCombinedTable"
              v-tooltip.left="{ value: 'Download as .CSV', showDelay: 1000, hideDelay: 300 }"
            />
          </template>
          <Column field="accession" header="Accession" sortable />
          <Column field="source" header="Project" sortable />
          <Column field="owner" header="Program" sortable />
        </DataTable>
      </Panel>
  
      <!-- Allele Detail Dialog -->
      <Dialog
        header="Allele Details"
        v-model:visible="showDetailDialog"
        modal
        closable
        :style="dialogStyle"
        @hide="clearAlleleDetail"
      >
        <div v-if="selectedAlleleDetail" class="p-3">
          <p><strong>Allele ID:</strong> {{ selectedAlleleDetail.alleleid }}</p>
          <p>
            <strong>Sequence:</strong>
            <span class="sequence-modal-wrap">
              {{ selectedAlleleDetail.sequence || 'No sequence available' }}
            </span>
          </p>
          <p><strong>INFO:</strong> {{ selectedAlleleDetail.info || 'No information available' }}</p>
          <p><strong>Associated Trait:</strong> {{ selectedAlleleDetail.associatedTrait || 'No associated traits' }}</p>
          <p><strong>Total Accessions:</strong> {{ selectedAlleleDetail.totalAccessions }}</p>
          <p>
            <strong>Associated Project:</strong>
            <span>{{ selectedAlleleDetail.associatedProject || 'None' }}</span>
          </p>
          <p>
            <strong>Program:</strong>
            <span>{{ selectedAlleleDetail.owner || 'None' }}</span>
          </p>
        </div>
      </Dialog>
  
      <!-- Shared Accessions Info Dialog -->
      <Dialog
        header="Shared Accessions Info"
        v-model:visible="showSharedInfoDialog"
        modal
        closable
        :style="dialogStyle"
      >
        <p>
          <strong>Shared Accessions</strong> represent the <strong>intersection</strong> of accessions across all selected alleles.
          Only accessions that appear in every allele's dataset are included.
        </p>
      </Dialog>
  
      <!-- Combined Accessions Info Dialog -->
      <Dialog
        header="Combined Accessions Info"
        v-model:visible="showCombinedInfoDialog"
        modal
        closable
        :style="dialogStyle"
      >
        <p>
          <strong>Combined Accessions</strong> represent the <strong>union</strong> of accessions across all selected alleles.
          This list includes every unique accession found in any allele's dataset.
        </p>
      </Dialog>
    </div>
  </template>
  
  <script>
  import axiosInstance from "../axiosConfig";
  import { mapGetters } from "vuex";
  import Button from "primevue/button";
  import Panel from "primevue/panel";
  import Dialog from "primevue/dialog";
  import DataTable from "primevue/datatable";
  import Column from "primevue/column";
  import InputText from "primevue/inputtext";
  
  export default {
    name: "Details",
    components: {
      Button,
      Panel,
      Dialog,
      DataTable,
      Column,
      InputText,
    },
    data() {
      return {
        detailedInfo: [],
        showDetailDialog: false,
        selectedAlleleDetail: null,
        searchQuery: "",
        searchSharedQuery: "",
        windowWidth: window.innerWidth,
        // New dialog controls for the info popups:
        showSharedInfoDialog: false,
        showCombinedInfoDialog: false,
      };
    },
    computed: {
      ...mapGetters(["getSelectedSequences"]),
      uniqueAccessions() {
        const accessionMap = new Map();
        this.detailedInfo.forEach(({ accession, source, owner }) => {
          if (!accessionMap.has(accession)) {
            accessionMap.set(accession, { accession, source, owner });
          }
        });
        return Array.from(accessionMap.values()).sort((a, b) =>
          a.accession.localeCompare(b.accession)
        );
      },
      filteredAccessions() {
        if (!this.searchQuery) return this.uniqueAccessions;
        const query = this.searchQuery.toLowerCase();
        return this.uniqueAccessions.filter(acc =>
          acc.accession.toLowerCase().includes(query)
        );
      },
      sharedAccessions() {
        if (!this.getSelectedSequences.length) return [];
        const alleleCount = this.getSelectedSequences.length;
        const accessionMap = new Map();
  
        this.detailedInfo.forEach(item => {
          const { accession, alleleid } = item;
          if (!accessionMap.has(accession)) {
            accessionMap.set(accession, new Set());
          }
          accessionMap.get(accession).add(alleleid);
        });
  
        const shared = [];
        accessionMap.forEach((alleleSet, accession) => {
          if (alleleSet.size === alleleCount) {
            const detail = this.detailedInfo.find(item => item.accession === accession);
            shared.push({
              accession,
              source: detail ? detail.source : '',
              owner: detail ? detail.owner : ''
            });
          }
        });
        return shared.sort((a, b) => a.accession.localeCompare(b.accession));
      },
      filteredSharedAccessions() {
        if (!this.searchSharedQuery) return this.sharedAccessions;
        const query = this.searchSharedQuery.toLowerCase();
        return this.sharedAccessions.filter(acc =>
          acc.accession.toLowerCase().includes(query)
        );
      },
      dialogStyle() {
        return {
          width: this.windowWidth < 600 ? "90vw" : "800px",
        };
      },
    },
    methods: {
      async fetchDetailedInfo() {
        if (!this.getSelectedSequences.length) {
          this.detailedInfo = [];
          return;
        }
        try {
          const alleleIds = this.getSelectedSequences.map(seq => seq.alleleid);
          console.log("Fetching details for allele IDs:", alleleIds);
          
          const { data } = await axiosInstance.post("posts/alleleAccessions", {
            alleleid: alleleIds,
          });
          
          console.log("API response:", data);
          
          // Transform data - fix the mapping to use 'projects' instead of 'sources'
          this.detailedInfo = data.map(item => ({
            uniqueKey: `${item.alleleid}-${item.accession}`,
            alleleid: item.alleleid,
            accession: item.accession,
            source: item.projects && item.projects.length ? item.projects.join(", ") : "",
            owner: item.programs && item.programs.length ? item.programs.join(", ") : ""
          }));
          
          console.log("Transformed detailedInfo:", this.detailedInfo);
        } catch (error) {
          console.error("Error fetching detailed information:", error);
          this.detailedInfo = [];
          if (this.$toast) {
            this.$toast.add({
              severity: "error",
              summary: "Error",
              detail: "Failed to fetch detailed information.",
              life: 3000,
            });
          }
        }
      },
      openAlleleDetail(allele) {
        const detailsForAllele = this.detailedInfo.filter(
          item => item.alleleid === allele.alleleid
        );
        const associatedProject = detailsForAllele[0]?.source || "None";
        const owner = detailsForAllele[0]?.owner || "None";
        const totalAccessions = detailsForAllele.length;
  
        this.selectedAlleleDetail = {
          alleleid: allele.alleleid,
          sequence: allele.allelesequence,
          info: allele.info,
          associatedTrait: allele.associated_trait,
          associatedProject,
          owner,
          totalAccessions,
        };
        this.showDetailDialog = true;
      },
      clearAlleleDetail() {
        this.selectedAlleleDetail = null;
      },
      goBack() {
        this.$router.push({ name: "Query" });
      },
      handleResize() {
        this.windowWidth = window.innerWidth;
      },
      removeAllele(allele, index) {
        console.log('Removing allele:', allele, 'at index:', index);
        console.log('Selected sequences before removal:', this.getSelectedSequences.length);
        
        // Use the index for more precise removal when available
        if (typeof index !== 'undefined') {
          this.$store.state.selectedSequences.splice(index, 1);
        } else {
          this.$store.commit("REMOVE_SELECTED_SEQUENCE", allele);
        }
        
        console.log('Selected sequences after removal:', this.getSelectedSequences.length);
        this.fetchDetailedInfo();
      },
      downloadCSV(data, filename) {
        const header = ["Accession", "Project", "Program"];
        const csvRows = [header.join(",")];
  
        data.forEach(item => {
          const row = [
            `"${item.accession}"`,
            `"${item.source}"`,
            `"${item.owner}"`
          ];
          csvRows.push(row.join(","));
        });
  
        const csvString = csvRows.join("\n");
        const blob = new Blob([csvString], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", filename);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
      },
      downloadCombinedTable() {
        this.downloadCSV(this.filteredAccessions, "combined_accessions.csv");
      },
      downloadSharedTable() {
        this.downloadCSV(this.filteredSharedAccessions, "shared_accessions.csv");
      },
      // Optional: Define refresh methods if desired.
      refreshCombinedTable() {
        this.fetchDetailedInfo();
      },
      refreshSharedTable() {
        this.fetchDetailedInfo();
      },
      getAlleleAccessionCount(allele) {
        const alleleId = allele.alleleid || allele.id;
        const count = this.detailedInfo.filter(item => item.alleleid === alleleId).length;
        return count !== undefined ? `${count} accession${count !== 1 ? 's' : ''}` : 'Loading...';
      },
      ensureUniqueSequences() {
        const beforeCount = this.getSelectedSequences.length;
        this.$store.dispatch("ensureUniqueSequences");
        const afterCount = this.getSelectedSequences.length;
        
        if (beforeCount !== afterCount) {
          console.log(`Removed ${beforeCount - afterCount} duplicate sequences`);
        }
      },
    },
    mounted() {
      this.ensureUniqueSequences();
      this.fetchDetailedInfo();
      window.addEventListener("resize", this.handleResize);
    },
    beforeUnmount() {
      window.removeEventListener("resize", this.handleResize);
    },
  };
  </script>
  
  <style scoped>
  .details-container {
    padding: 10px;
    font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif;
  }
  .allele-button {
    padding: 0.2rem;
    border: 1px solid #e5e7eb;
    background-color: white;
    cursor: pointer;
    transition: background-color 0.3s, border-color 0.3s, transform 0.3s;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
    text-align: left;
    border-radius: 0.5rem;
    position: relative;
  }
  .accession-count {
    font-size: 0.7rem;
    color: #666;
    display: block;
    margin-top: 0.15rem;
    font-weight: normal;
  }
  .remove-btn {
    position: absolute;
    top: -4px;
    right: -4px;
    background-color: #ccc;
    border-radius: 50%;
    width: 18px;
    height: 18px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 10px;
    cursor: pointer;
    z-index: 10;
  }
  .remove-btn:hover {
    background-color: #aaa;
    transform: scale(1.05);
  }
  .allele-button:hover {
    background-color: var(--surface-hover, #f0f4c3);
    border-color: var(--primary-color, #8bc34a);
    transform: scale(1.02);
  }
  .allele-button-header h3 {
    font-size: 0.9rem;
    white-space: normal;
    overflow-wrap: anywhere;
    margin-bottom: 0.15rem;
  }
  .dialog-content p {
    font-size: 0.7rem;
    margin: 0.3rem 0;
  }
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
  @media (max-width: 480px) {
    .p-dialog {
      width: 90vw !important;
      max-width: 90vw !important;
    }
  }
  .mb-4 {
    margin-bottom: 1rem;
  }
  .mb-2 {
    margin-bottom: 0.5rem;
  }
  /* Header container to position the header text and info icon */
  .header-container {
    display: inline-flex;
    align-items: center;
  }
  
  /* Make the header text bold */
  .header-container span {
    font-weight: bold;
  }
  
  /* Position the info icon directly next to the header text */
  .info-icon {
    margin-left: 0.2rem;
  }

  .sequence-modal-wrap {
  white-space: pre-wrap;
  word-break: break-word;

}

  </style>
  