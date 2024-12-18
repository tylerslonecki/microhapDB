<!-- src/components/Query.vue -->
<template>
  <div class="sequences-container w-full px-4">
    <!-- Panel Component as the Container -->
    <Panel header="Query Unique Microhaplotypes" class="mb-4">
      
      <!-- Filter Row -->
      <div class="filter-row flex items-center justify-between gap-5 mb-3 w-full">
        
        <!-- Filters Group: Species Label, Dropdown, and Keyword Search -->
        <div class="flex items-center gap-4">
          
          <!-- Species Label and Dropdown -->
          <div class="flex items-center gap-2 centered-label-dropdown">
            <label for="speciesDropdown" class="font-bold">Species</label>
            <Dropdown 
              id="speciesDropdown" 
              v-model="species" 
              :options="speciesOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Species"
              @change="onSpeciesChange" 
              class="w-60"
            />
          </div>
          
          <!-- Keyword Search -->
          <div class="flex items-center">
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText 
                v-model="filters.global.value" 
                placeholder="Keyword Search" 
                @input="onGlobalFilter" 
                class="w-60"
              />
            </IconField>
          </div>
        </div>
        
        <!-- View Details Button -->
        <div class="flex items-center">
          <Button 
            label="View Details" 
            icon="pi pi-arrow-right" 
            :disabled="!selectedSequences.length"
            @click="navigateToDetails" 
          />
        </div>
        
      </div>
      
      <!-- DataTable for Detailed Information -->
      <DataTable 
        v-model:selection="selectedSequences"
        :value="sequences" 
        :filters="filters"
        :filterDisplay="'row'"
        :loading="loading"
        :paginator="true" 
        :rows="size" 
        :totalRecords="total"
        :lazy="true"
        :rowsPerPageOptions="[10, 25, 50]"
        showGridlines 
        stripedRows
        @page="onPageChange"
        @filter="onFilter"
        tableStyle="min-width: 50rem"
        class="datatable-gridlines mb-3 w-full"
        :emptyMessage="'No data available. Please adjust your filters or select a species.'"
        selectionMode="multiple" 
        dataKey="uniqueKey" 
      > 
        <template #paginatorstart>
          <Button type="button" icon="pi pi-refresh" text @click="refreshTable" />
        </template>
        <template #paginatorend>
          <Button type="button" icon="pi pi-download" text @click="downloadSequences" />
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
          filter 
          filterPlaceholder="Search Allele ID"
          :filterMatchMode="'contains'"
        >
          <template #filter="{ filterModel, filterCallback }">
            <InputText 
              v-model="filterModel.value" 
              type="text" 
              @input="filterCallback()" 
              placeholder="Search Allele ID" 
            />
          </template>
        </Column>

        <!-- Info Column -->
        <Column 
          field="info" 
          header="Info" 
          filter 
          filterPlaceholder="Search Info"
          :filterMatchMode="'contains'"
        >
          <template #filter="{ filterModel, filterCallback }">
            <InputText 
              v-model="filterModel.value" 
              type="text" 
              @input="filterCallback()" 
              placeholder="Search Info" 
            />
          </template>
        </Column>

        <!-- Associated Trait Column -->
        <Column 
          field="associated_trait" 
          header="Associated Trait" 
          filter 
          filterPlaceholder="Search Associated Trait"
          :filterMatchMode="'contains'"
        >
          <template #filter="{ filterModel, filterCallback }">
            <InputText 
              v-model="filterModel.value" 
              type="text" 
              @input="filterCallback()" 
              placeholder="Search Associated Trait" 
            />
          </template>
        </Column>

        <!-- Allele Sequence Column with Smaller Font -->
        <Column 
          field="allelesequence" 
          header="Allele Sequence" 
          filter 
          filterPlaceholder="Search Allele Sequence"
          :filterMatchMode="'contains'"
        >
          <!-- Custom Body Template for Smaller Font -->
          <template #body="{ data }">
            <span class="small-font">{{ data.allelesequence }}</span>
          </template>

          <!-- Existing Filter Template -->
          <template #filter="{ filterModel, filterCallback }">
            <InputText 
              v-model="filterModel.value" 
              type="text" 
              @input="filterCallback()" 
              placeholder="Search Allele Sequence" 
            />
          </template>
        </Column>
      </DataTable>
    </Panel>
  </div>
</template>

<script>
import axiosInstance from '../axiosConfig';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dropdown from 'primevue/dropdown';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import IconField from 'primevue/iconfield';
import InputIcon from 'primevue/inputicon';
import Panel from 'primevue/panel'; // Import Panel component
import { mapActions } from 'vuex';

export default {
  name: 'Query',
  components: {
    DataTable,
    Column,
    Dropdown,
    InputText,
    Button,
    IconField,
    InputIcon,
    Panel // Register Panel component
  },
  data() {
    return {
      sequences: [],
      selectedSequences: [], // For row selection
      total: 0,
      page: 1, // Initialize to 1 for 1-based indexing
      size: 25,
      species: '',
      loading: false,
      speciesOptions: [
        { label: 'Sweetpotato', value: 'sweetpotato' },
        { label: 'Blueberry', value: 'blueberry' },
        { label: 'Alfalfa', value: 'alfalfa' },
        { label: 'Cranberry', value: 'cranberry' }
      ],
      filters: {
        global: { value: null, matchMode: 'contains' },
        alleleid: { value: null, matchMode: 'contains' },
        info: { value: null, matchMode: 'contains' }, // New filter
        associated_trait: { value: null, matchMode: 'contains' }, // New filter
        allelesequence: { value: null, matchMode: 'contains' }
      },
      associatedTraits: ['drought resistance', 'anthracnose race1 resistance'] // List of associated traits
    };
  },
  methods: {
    ...mapActions(['updateSelectedSequences']),
    async fetchSequences() {
      if (!this.species) {
        this.sequences = [];
        this.total = 0;
        this.loading = false;
        return;
      }

      this.loading = true;

      // Prepare filters for backend
      const activeFilters = {};
      for (const key in this.filters) {
        if (this.filters[key].value && key !== 'global') {
          activeFilters[key] = {
            value: this.filters[key].value,
            matchMode: this.filters[key].matchMode
          };
        }
      }

      try {
        const response = await axiosInstance.post('posts/sequences', { // Updated endpoint path
          page: this.page,
          size: this.size,
          species: this.species,
          globalFilter: this.filters.global.value,
          filters: activeFilters
        });
        this.sequences = response.data.items;
        this.total = response.data.total;

        // Assign dummy data to "Info" and "Associated Traits" columns
        this.assignDummyData();
      } catch (error) {
        console.error("Error fetching sequences:", error);
        // Optionally, set an error state to display a message to the user
        this.sequences = [];
        this.total = 0;
      } finally {
        this.loading = false;
      }
    },
    assignDummyData() {
      // Assign dummy data based on row index
      this.sequences.forEach((sequence, index) => {
        // Assign "likely paralogous" to "Info" every 7th row
        if ((index + 1) % 6 === 0) {
          sequence.info = "likely paralogous";
        } else {
          sequence.info = ""; // Or any default value
        }

        // Assign associated traits every 10th row
        if ((index + 1) % 5 === 0) {
          // Alternate between the two traits
          const traitIndex = Math.floor((index + 1) / 10) % this.associatedTraits.length;
          sequence.associated_trait = this.associatedTraits[traitIndex];
        } else {
          sequence.associated_trait = ""; // Or any default value
        }

        // Ensure each sequence has a uniqueKey for dataKey
        sequence.uniqueKey = `${sequence.alleleid}-${sequence.allelesequence}-${index}`;
      });
    },
    onPageChange(event) {
      // PrimeVue uses zero-based indexing for pages
      this.page = event.page + 1;
      this.size = event.rows;
      this.fetchSequences();
    },
    onFilter(event) {
      this.filters = event.filters;
      this.page = 1; 
      this.fetchSequences();
    },
    onSpeciesChange() {
      this.page = 1; 
      this.fetchSequences();
    },
    onGlobalFilter() {
      this.page = 1;
      this.fetchSequences();
    },
    refreshTable() {
      // Reset only the global and column-specific filters
      this.filters.global.value = null;
      this.filters.alleleid.value = null;
      this.filters.info.value = null; // Reset new filter
      this.filters.associated_trait.value = null; // Reset new filter
      this.filters.allelesequence.value = null;

      this.page = 1;

      this.fetchSequences();
    },
    navigateToDetails() {
      // Store selected sequences in Vuex
      this.updateSelectedSequences(this.selectedSequences);
      
      // Navigate to the Details component
      this.$router.push({ name: 'Details' });
    },
    downloadSequences() {
      // Implement download functionality here
      // Example: Convert sequences to CSV and trigger download
      if (!this.sequences.length) {
        this.$toast.add({ 
          severity: 'warn', 
          summary: 'Warning', 
          detail: 'No data available to download.', 
          life: 3000 
        });
        return;
      }

      const headers = ['Allele ID', 'Info', 'Associated Trait', 'Allele Sequence'];
      const rows = this.sequences.map(seq => [
        seq.alleleid, 
        seq.info, 
        seq.associated_trait, 
        seq.allelesequence
      ]);
      let csvContent = "data:text/csv;charset=utf-8," 
        + headers.join(",") + "\n" 
        + rows.map(e => e.join(",")).join("\n");

      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "sequences.csv");
      document.body.appendChild(link); // Required for FF

      link.click(); // This will download the data file named "sequences.csv"
      document.body.removeChild(link);
    }
  },
  mounted() {
    this.fetchSequences();
  }
};
</script>

<style scoped>
.sequences-container {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

.datatable-gridlines {
  /* Add any specific styling if required */
}

.p-datatable .p-column-header, .p-datatable .p-cell {
  /* Allow text wrapping */
  white-space: normal;
}

.p-datatable .p-column-header:nth-child(3), /* Info column */
.p-datatable .p-column-header:nth-child(4) { /* Associated Trait column */
  width: 200px; /* Adjust width as needed */
}

/* Ensure the selection checkbox column has appropriate width */
.p-datatable .p-selection-column {
  width: 3rem;
  text-align: center;
}

/* Custom class for smaller font in Allele Sequence column */
.small-font {
  font-size: 12px; /* Adjust the size as needed */
  /* You can add more styling if necessary */
}

/* Responsive Design */
@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filter-row > div {
    width: 100%;
  }

  .filter-row .w-60 {
    width: 100%; /* Make inputs full width on small screens */
  }
}

/* Centering the label and dropdown */
.centered-label-dropdown {
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
