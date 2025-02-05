<template>
  <div class="sequences-container w-full px-4">
    <Panel header="Query Unique Microhaplotypes" class="mb-4">
      <!-- Filter Row -->
      <div class="filter-row flex items-center justify-between gap-5 mb-3 w-full">
        <!-- Species Dropdown and Keyword Search -->
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
          <div class="flex items-center">
            <IconField>
              <InputIcon>
                <i class="pi pi-search" />
              </InputIcon>
              <InputText 
                v-model="filters.global.value" 
                placeholder="Keyword Search" 
                @input="handleGlobalFilter" 
                class="w-60"
              />
            </IconField>
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
      
      <!-- DataTable without transition wrapper -->
      <!-- A fixed min-height helps prevent layout shifts -->
      <DataTable 
        :first="first"
        v-model:selection="selectedSequences"
        :value="sequences" 
        :filters="filters"
        filterDisplay="row"
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
        
        <!-- Columns -->
        <Column selectionMode="multiple" headerStyle="width: 3rem" exportable="false" />
        
        <Column 
          field="alleleid" 
          header="Allele ID" 
          filter 
          filterPlaceholder="Search Allele ID"
          filterMatchMode="contains"
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

        <Column 
          field="info" 
          header="Info" 
          filter 
          filterPlaceholder="Search Info"
          filterMatchMode="contains"
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

        <Column 
          field="associated_trait" 
          header="Associated Trait" 
          filter 
          filterPlaceholder="Search Associated Trait"
          filterMatchMode="contains"
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

        <Column 
          field="allelesequence" 
          header="Allele Sequence" 
          filter 
          filterPlaceholder="Search Allele Sequence"
          filterMatchMode="contains"
        >
          <template #body="{ data }">
            <span class="small-font">{{ data.allelesequence }}</span>
          </template>
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
    IconField,
    InputIcon,
    Panel
  },
  directives: {
    tooltip: Tooltip
  },
  computed: {
    ...mapGetters(['getSelectedSequences', 'getQueryState']),
    // Two-way binding to Vuex state
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
    }
  },
  methods: {
    ...mapActions(['updateSelectedSequences', 'updateQueryState', 'resetQueryState']),
    
    // Resets the selected sequences
    resetSelection() {
      this.updateSelectedSequences([]);
    },

    // Combines resetting selection and setting the page to 1 before fetching new data
    resetAndFetch() {
      this.resetSelection();
      this.updateQueryState({ page: 1 });
      this.fetchSequences();
    },

    async fetchSequences() {
      if (!this.species) {
        return;
      }
      // Record start time to enforce a minimum loading time.
      const startTime = Date.now();
      this.loading = true;

      // Build active filters (ignoring global)
      const activeFilters = Object.keys(this.filters).reduce((acc, key) => {
        if (this.filters[key].value && key !== 'global') {
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
          globalFilter: this.filters.global.value,
          filters: activeFilters
        });

        // Add a unique key to each sequence for PrimeVue
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
        // Enforce a minimum loading time of 200ms.
        const elapsed = Date.now() - startTime;
        const minLoadingTime = 200;
        if (elapsed < minLoadingTime) {
          await new Promise(resolve => setTimeout(resolve, minLoadingTime - elapsed));
        }
        this.loading = false;
      }
    },

    onPageChange(event) {
      const newPage = event.page + 1;
      this.updateQueryState({ page: newPage, size: event.rows });
      this.fetchSequences();
    },

    onFilter(event) {
      this.resetSelection();
      this.updateQueryState({ filters: event.filters, page: 1 });
      // Debouncing is handled in the watcher.
    },

    handleSpeciesChange() {
      this.resetAndFetch();
    },

    handleGlobalFilter() {
      this.resetAndFetch();
    },

    refreshTable() {
      this.resetSelection();
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
      // The filters watcher will call fetchSequences after debounce.
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

.datatable-gridlines {
  /* Additional styling if required */
}

/* Override the default loading overlay style to use a lighter overlay */
::v-deep .p-datatable-loading-overlay {
  background: rgba(255, 255, 255, 0.4) !important;
  transition: opacity 0.2s ease;
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

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
    align-items: stretch;
  }
  .filter-row > div {
    width: 100%;
  }
  .filter-row .w-60 {
    width: 100%;
  }
  .filter-row .flex.items-center {
    flex-direction: column;
    align-items: flex-start;
  }
  .filter-row .flex.items-center .ml-4 {
    margin-left: 0;
    margin-top: 0.5rem;
  }
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

/* Hide the filter menu icon from the filter row */
::v-deep .p-datatable .p-column-filter .p-column-filter-menu-button {
  display: none;
}

</style>
