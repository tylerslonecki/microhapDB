<template>
  <div class="sequences-container w-full px-4">
    <Panel header="Query Unique Microhaplotypes" class="mb-4">
      <!-- Top Filter Row -->
      <div class="filter-row flex items-center justify-between gap-5 mb-3 w-full">
        <!-- Species Dropdown -->
        <div class="flex items-center gap-4">
          <div class="flex items-center gap-2 centered-label-dropdown">
            <label for="speciesDropdown" class="font-bold">Species</label>
            <Dropdown 
              id="speciesDropdown" 
              v-model="species" 
              :options="speciesOptions"
              optionLabel="label"
              optionValue="value"
              placeholder="Select Species"
              @change="handleSpeciesChange" 
              class="w-60"
            />
          </div>
        </div>
        <!-- View Details Button with Selected Count -->
        <div class="flex items-center">
          <Button 
            label="View Details" 
            icon="pi pi-arrow-right" 
            :disabled="!selectedSequences.length"
            @click="navigateToDetails" 
          />
          <div v-if="selectedSequences.length" class="ml-2 text-base text-gray-700 selected-count">
            ( Selected Alleles: {{ selectedSequences.length }} )
          </div>
        </div>
      </div>

      <!-- External Filters Panel (Card) -->
      <Card class="mb-3">
        <div class="flex items-center gap-4 p-4">
          <!-- Filters Label -->
          <div class="font-bold whitespace-nowrap">Filters</div>
          
          <!-- Filter Boxes -->
          <div class="external-filters grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 w-full">
            <InputText 
              v-model="filters.alleleid.value" 
              placeholder="Allele ID" 
              class="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <InputText 
              v-model="filters.info.value" 
              placeholder="Info" 
              class="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <InputText 
              v-model="filters.associated_trait.value" 
              placeholder="Associated Trait" 
              class="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
            <InputText 
              v-model="filters.allelesequence.value" 
              placeholder="Allele Sequence" 
              class="p-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-300"
            />
          </div>
        </div>
      </Card>

      <!-- DataTable with optimized loading -->
      <div class="datatable-wrapper relative">
        <DataTable 
          :first="first"
          v-model:selection="selectedSequences"
          :value="displaySequences" 
          :filters="filters"
          :loading="loading"
          paginator
          paginatorTemplate="FirstPageLink PrevPageLink PageLinks NextPageLink LastPageLink CurrentPageReport RowsPerPageDropdown"
          :rowsPerPageOptions="[10, 25, 50]"
          currentPageReportTemplate="Showing {first} to {last} of {totalRecords} alleles"
          :rows="size" 
          :totalRecords="total"
          lazy
          showGridlines 
          stripedRows
          @page="onPageChange"
          @filter="onFilter"
          tableStyle="min-width: 50rem"
          class="datatable-gridlines mb-3 w-full"
          emptyMessage="No data available. Please adjust your filters or select a species."
          selectionMode="multiple" 
          dataKey="uniqueKey" 
          paginatorPosition="both"
          style="min-height: 300px;"
        > 
          <!-- Paginator Slots -->
          <template #paginatorstart>
            <Button 
              type="button" 
              icon="pi pi-refresh" 
              text 
              @click="refreshTable" 
              v-tooltip="{ value: 'Refresh', showDelay: 1000, hideDelay: 300 }"
            />
          </template>
          <template #paginatorend>
            <Button 
              type="button" 
              icon="pi pi-download" 
              text 
              @click="downloadSequences" 
              v-tooltip.left="{ value: 'Download as .CSV', showDelay: 1000, hideDelay: 300 }"
            />
          </template>
          
          <!-- Columns (without inline filter inputs) -->
          <Column 
            selectionMode="multiple"
            headerCheckbox 
            headerStyle="width: 3rem" 
            exportable="false" 
          />
          <Column field="alleleid" header="Allele ID" />
          <Column field="info" header="Info" />
          <Column field="associated_trait" header="Associated Trait" />
          <Column field="allelesequence" header="Allele Sequence">
            <template #body="{ data }">
              <span class="small-font">{{ data.allelesequence }}</span>
            </template>
          </Column>
        </DataTable>
      </div>
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
import Panel from 'primevue/panel';
import Tooltip from 'primevue/tooltip';
import { mapActions, mapGetters } from 'vuex';

export default {
  name: 'Query',
  components: {
    DataTable,
    Column,
    Dropdown,
    InputText,
    Button,
    Panel
  },
  directives: {
    tooltip: Tooltip
  },
  computed: {
    ...mapGetters(['getSelectedSequences', 'getQueryState']),
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
    displaySequences() {
      // Return placeholder or cached data during loading for smoother transitions
      return this.loadingNewData ? this.cachedData : this.sequences;
    },
    total() {
      return this.getQueryState.total;
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
      loadingNewData: false,
      cachedData: [],
      debounceTimer: null
    };
  },
  watch: {
    species(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.resetSelection();
        this.updateQueryState({ page: 1 });
        this.fetchSequences();
      }
    },
    filters: {
      handler() {
        if (this.debounceTimer) clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
          this.resetSelection();
          this.fetchSequences();
        }, 300);
      },
      deep: true
    },
    sequences(newVal) {
      // Update cached data when sequences are updated
      this.cachedData = newVal;
    }
  },
  methods: {
    ...mapActions(['updateSelectedSequences', 'updateQueryState', 'resetQueryState']),
    resetSelection() {
      this.updateSelectedSequences([]);
    },
    resetAndFetch() {
      this.resetSelection();
      this.updateQueryState({ page: 1 });
      this.fetchSequences();
    },
    async fetchSequences() {
      if (!this.species) {
        return;
      }
      
      // Set loading state, but keep displaying the current data
      this.loading = true;
      this.loadingNewData = true;
      
      const activeFilters = Object.keys(this.filters).reduce((acc, key) => {
        if (this.filters[key].value) {
          acc[key] = { 
            value: this.filters[key].value, 
            matchMode: this.filters[key].matchMode 
          };
        }
        return acc;
      }, {});
      
      try {
        const { data } = await axiosInstance.post('posts/sequences', {
          page: this.page,
          size: this.size,
          species: this.species,
          filters: activeFilters
        });
        
        const sequencesWithKeys = data.items.map((sequence, index) => ({
          ...sequence,
          uniqueKey: `${sequence.alleleid}-${sequence.allelesequence}-${index}`
        }));
        
        this.updateQueryState({
          sequences: sequencesWithKeys,
          total: data.total
        });
      } catch (error) {
        console.error("Error fetching sequences:", error);
        this.updateQueryState({ sequences: [], total: 0 });
      } finally {
        // Turn off loading indicators only after data is updated in the store
        this.$nextTick(() => {
          this.loading = false;
          this.loadingNewData = false;
        });
      }
    },
    onPageChange(event) {
      // Cache current data before changing page
      this.cachedData = [...this.sequences];
      
      const newPage = event.page + 1;
      this.updateQueryState({ page: newPage, size: event.rows });
      this.fetchSequences();
    },
    onFilter(event) {
      // Cache current data before applying filter
      this.cachedData = [...this.sequences];
      
      this.resetSelection();
      this.updateQueryState({ filters: event.filters, page: 1 });
    },
    handleSpeciesChange() {
      // Clear cache when species changes
      this.cachedData = [];
      this.resetAndFetch();
    },
    refreshTable() {
      // Cache current data before refreshing
      this.cachedData = [...this.sequences];
      
      this.resetSelection();
      this.updateQueryState({
        filters: {
          alleleid: { value: null, matchMode: 'contains' },
          info: { value: null, matchMode: 'contains' },
          associated_trait: { value: null, matchMode: 'contains' },
          allelesequence: { value: null, matchMode: 'contains' }
        },
        page: 1
      });
      this.fetchSequences();
    },
    navigateToDetails() {
      this.$router.push({ name: 'DetailsAlt' });
    },
    downloadSequences() {
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
      const csvContent =
        "data:text/csv;charset=utf-8," +
        headers.join(",") +
        "\n" +
        rows.map(e => e.join(",")).join("\n");
      const encodedUri = encodeURI(csvContent);
      const link = document.createElement("a");
      link.setAttribute("href", encodedUri);
      link.setAttribute("download", "sequences.csv");
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  },
  mounted() {
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

.datatable-wrapper {
  /* Container for the datatable */
}

.datatable-gridlines {
  /* No additional styling for better performance */
}

/* Remove the loading overlay transition that was causing the flash */
::v-deep .p-datatable-loading-overlay {
  background: rgba(255, 255, 255, 0.7) !important;
  opacity: 0 !important;
}

/* Add styling for when loading is active */
::v-deep .p-datatable.p-datatable-loading {
  opacity: 1 !important;
}

/* Make sure the table is always visible */
::v-deep .p-datatable-table {
  opacity: 1 !important;
}

.p-datatable .p-column-header,
.p-datatable .p-cell {
  white-space: normal;
}

.p-datatable .p-column-header:nth-child(3),
.p-datatable .p-column-header:nth-child(4) {
  width: 200px;
}

.p-datatable .p-selection-column {
  width: 3rem;
  text-align: center;
}

.small-font {
  font-size: 12px;
}

.external-filters {
  align-items: center;
}

.external-filters > div {
  min-width: 200px;
}

.centered-label-dropdown {
  display: flex;
  align-items: center;
  justify-content: center;
}

.selected-count {
  font-weight: 600;
  display: flex;
  align-items: center;
  line-height: 1.5;
}

.selected-count:hover {
  color: #4A5568;
  transition: color 0.3s ease;
}

::v-deep .p-tooltip {
  white-space: nowrap;
  max-width: none;
}

::v-deep .p-datatable .p-column-filter .p-column-filter-menu-button {
  display: none;
}
</style>