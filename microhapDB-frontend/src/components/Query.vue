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
        
        <!-- View Details Button with Selected Count -->
        <div class="flex items-center">
          <!-- View Details Button -->
          <Button 
            label="View Details" 
            icon="pi pi-arrow-right" 
            :disabled="!selectedSequences.length"
            @click="navigateToDetails" 
          />
          
          <!-- Selected Count Display -->
          <div 
            v-if="selectedSequences.length" 
            class="ml-2 text-base text-gray-700 selected-count"
          >
            ( Selected Alleles: {{ selectedSequences.length }} )
          </div>
        </div>
      </div>
      
      <!-- DataTable for Detailed Information -->
      <DataTable 
        :first="first"
        v-model:selection="selectedSequences"
        :value="sequences" 
        :filters="filters"
        :filterDisplay="'row'"
        :loading="loading"
        :paginator="true" 
        paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
        :rowsPerPageOptions="[10, 25, 50]"
        currentPageReportTemplate="Showing {first} to {last} of {totalRecords} accessions"
        :rows="size" 
        :totalRecords="total"
        :lazy="true"
        showGridlines 
        stripedRows
        @page="onPageChange"
        @filter="onFilter"
        tableStyle="min-width: 50rem"
        class="datatable-gridlines mb-3 w-full"
        :emptyMessage="'No data available. Please adjust your filters or select a species.'"
        selectionMode="multiple" 
        dataKey="uniqueKey" 
        paginatorPosition="both"
      > 
        <!-- Paginator Start Slot -->
        <template #paginatorstart>
          <Button 
            type="button" 
            icon="pi pi-refresh" 
            text 
            @click="refreshTable" 
            v-tooltip="{ value: 'Refresh', showDelay: 1000, hideDelay: 300 }" placeholder="Right"
          />
        </template>
        
        <!-- Paginator End Slot -->
        <template #paginatorend>
          <Button 
            type="button" 
            icon="pi pi-download" 
            text 
            @click="downloadSequences" 
            v-tooltip.left="{ value: 'Download as .CSV', showDelay: 1000, hideDelay: 300 }" placeholder="Left"
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
import Panel from 'primevue/panel';
import Tooltip from 'primevue/tooltip'; // Import Tooltip directive
import { mapActions, mapGetters } from 'vuex';

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
    Panel
  },
  directives: {
    tooltip: Tooltip // Register Tooltip directive
  },
  computed: {
    ...mapGetters(['getSelectedSequences', 'getQueryState']),
    
    // Bind component's data to Vuex store state
    species: {
      get() {
        return this.getQueryState.species;
      },
      set(value) {
        this.updateQueryState({ species: value });
      }
    },
    filters: {
      get() {
        return this.getQueryState.filters;
      },
      set(value) {
        this.updateQueryState({ filters: value });
      }
    },
    page() {
      return this.getQueryState.page;
    },
    size() {
      return this.getQueryState.size;
    },
    sequences() {
      return this.getQueryState.sequences;
    },
    total() {
      return this.getQueryState.total;
    },
    associatedTraits() {
      return this.getQueryState.associatedTraits;
    },
    selectedSequences: {
      get() {
        return this.getSelectedSequences;
      },
      set(value) {
        this.updateSelectedSequences(value);
      }
    },
    first() {
      return (this.page - 1) * this.size;
    }
  },
  data() {
    return {
      speciesOptions: [
        { label: 'Sweetpotato', value: 'sweetpotato' },
        { label: 'Blueberry', value: 'blueberry' },
        { label: 'Alfalfa', value: 'alfalfa' },
        { label: 'Cranberry', value: 'cranberry' }
      ],
      loading: false,
      debounceTimer: null
    };
  },
  watch: {
    // Combined watch block for species and filters
    species(newVal, oldVal) {
      if (newVal !== oldVal) {
        // Reset selected sequences when species changes
        this.updateSelectedSequences([]);

        this.updateQueryState({ page: 1 });
        this.fetchSequences();
      }
    },
    filters: {
      handler() {
        // Debounce filter changes
        if (this.debounceTimer) {
          clearTimeout(this.debounceTimer);
        }
        this.debounceTimer = setTimeout(() => {
          // 1. Reset selected sequences
          this.updateSelectedSequences([]);

          // 2. Fetch the sequences
          this.fetchSequences();
        }, 300); // Debounce delay in ms
      },
      deep: true
    }
  },
  methods: {
    ...mapActions(['updateSelectedSequences', 'updateQueryState', 'resetQueryState']),
    
    async fetchSequences() {
      if (!this.species) {
        this.updateQueryState({ sequences: [], total: 0 });
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
        const response = await axiosInstance.post('posts/sequences', {
          page: this.page,
          size: this.size,
          species: this.species,
          globalFilter: this.filters.global.value,
          filters: activeFilters
        });

        // Add uniqueKey to each sequence so PrimeVue can distinguish them.
        const sequencesWithKeys = response.data.items.map((sequence, index) => {
          sequence.uniqueKey = `${sequence.alleleid}-${sequence.allelesequence}-${index}`;
          return sequence;
        });

        // Update sequences and total in Vuex store
        this.updateQueryState({
          sequences: sequencesWithKeys,
          total: response.data.total
        });

      } catch (error) {
        console.error("Error fetching sequences:", error);
        // Optionally, set an error state to display a message to the user
        this.updateQueryState({ sequences: [], total: 0 });
      } finally {
        this.loading = false;
      }
    },
    onPageChange(event) {
      // PrimeVue uses zero-based indexing for pages
      const newPage = event.page + 1;
      this.updateQueryState({ page: newPage, size: event.rows });
      this.fetchSequences();
    },
    onFilter(event) {
      // Reset selected sequences when filters change
      this.updateSelectedSequences([]);

      // Update filters and reset to first page
      this.updateQueryState({ filters: event.filters, page: 1 });
      // Debounce is handled in the watcher, so no direct fetch here
    },
    onSpeciesChange() {
      // Reset selected sequences when species changes
      this.updateSelectedSequences([]);

      // Reset page to 1 and fetch new sequences
      this.updateQueryState({ page: 1 });
      this.fetchSequences();
    },
    onGlobalFilter() {
      // Reset selected sequences when global filter changes
      this.updateSelectedSequences([]);

      // Reset page to 1 and fetch new sequences
      this.updateQueryState({ page: 1 });
      this.fetchSequences();
    },
    refreshTable() {
      // Reset selected sequences
      this.updateSelectedSequences([]);

      // Reset only the global and column-specific filters
      this.updateQueryState({
        filters: {
          global: { value: null, matchMode: 'contains' },
          alleleid: { value: null, matchMode: 'contains' },
          info: { value: null, matchMode: 'contains' },
          associated_trait: { value: null, matchMode: 'contains' },
          allelesequence: { value: null, matchMode: 'contains' }
        },
        page: 1
      });

      // Fetch the sequences with reset filters and page
      this.fetchSequences();
    },
    navigateToDetails() {
      // Store selected sequences in Vuex (already handled via v-model)
      // Navigate to the Details component
      this.$router.push({ name: 'Details' });
    },
    downloadSequences() {
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
    // If Query state exists in Vuex, fetch sequences based on it
    if (this.getQueryState.species) {
      this.fetchSequences();
    }
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

  /* Stack button and count vertically */
  .filter-row .flex.items-center {
    flex-direction: column;
    align-items: flex-start; /* or center */
  }

  /* Adjust margin for small screens */
  .filter-row .flex.items-center .ml-4 {
    margin-left: 0;
    margin-top: 0.5rem; /* Adds space above the count */
  }
}

/* Centering the label and dropdown */
.centered-label-dropdown {
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-count {
  font-weight: 600;
  display: flex;
  align-items: center;
  /* Optional: Adjust line-height if necessary */
  line-height: 1.5;
}

/* Hover effect for the count display */
.selected-count:hover {
  color: #4A5568; /* Darker gray on hover */
  transition: color 0.3s ease;
}

/* Prevent tooltip text from wrapping */
::v-deep .p-tooltip {
  white-space: nowrap;
  max-width: none; /* Optional: Remove max-width to prevent wrapping */
}
</style>
