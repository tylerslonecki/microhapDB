<template>
  <div class="sequences-container">
    <h2 class="page-title">
      {{ species ? (species.charAt(0).toUpperCase() + species.slice(1)) + ' Unique Microhaplotypes' : 'Unique Microhaplotypes' }}
    </h2>
    <div class="filter-row grid align-items-center gap-2 mb-3">
      <div class="flex flex-column gap-1">
        <label for="speciesDropdown" class="font-bold">Species</label>
        <Dropdown 
          id="speciesDropdown" 
          v-model="species" 
          :options="speciesOptions"
          optionLabel="label"
          optionValue="value"
          placeholder="Select Species"
          @change="onSpeciesChange" 
        />
      </div>
      <!-- Add more filters here if needed -->
    </div>

    <div class="flex justify-end mb-3">
      <IconField>
        <InputIcon>
          <i class="pi pi-search" />
        </InputIcon>
        <InputText 
          v-model="filters.global.value" 
          placeholder="Keyword Search" 
          @input="onGlobalFilter" 
        />
      </IconField>
    </div>

    <DataTable 
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
      class="datatable-gridlines mb-3" 
      v-if="sequences.length"
    > 
      <template #paginatorstart>
        <Button type="button" icon="pi pi-refresh" text @click="refreshTable" />
      </template>
      <template #paginatorend>
        <Button type="button" icon="pi pi-download" text />
      </template>

      <Column 
        field="hapid" 
        header="Hap ID" 
        filter 
        filterPlaceholder="Search Hap ID"
        :filterMatchMode="'contains'"
      >
        <template #filter="{ filterModel, filterCallback }">
          <InputText 
            v-model="filterModel.value" 
            type="text" 
            @input="filterCallback()" 
            placeholder="Search Hap ID" 
          />
        </template>
      </Column>

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


      <Column 
        field="allelesequence" 
        header="Allele Sequence" 
        filter 
        filterPlaceholder="Search Allele Sequence"
        :filterMatchMode="'contains'"
      >
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

    <div v-else class="text-center mt-4">
      <p class="text-secondary">No data available</p>
    </div>
  </div>
</template>

<script>
import axiosInstance from '../axiosConfig';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';
import Dropdown from 'primevue/dropdown';
import InputText from 'primevue/inputtext';
import Button from 'primevue/button';
import IconField from 'primevue/iconfield'; // Ensure these components are correctly imported
import InputIcon from 'primevue/inputicon';

export default {
  components: {
    DataTable,
    Column,
    Dropdown,
    InputText,
    Button,
    IconField,
    InputIcon
  },
  data() {
    return {
      sequences: [],
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
        hapid: { value: null, matchMode: 'contains' },
        alleleid: { value: null, matchMode: 'contains' },
        allelesequence: { value: null, matchMode: 'contains' }
      }
    };
  },
  methods: {
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
        const response = await axiosInstance.post('/posts/sequences', {
          page: this.page,
          size: this.size,
          species: this.species,
          globalFilter: this.filters.global.value,
          filters: activeFilters
        });
        this.sequences = response.data.items;
        this.total = response.data.total;
      } catch (error) {
        console.error("Error fetching sequences:", error);
        // Optionally, set an error state to display a message to the user
      } finally {
        this.loading = false;
      }
    },
    onPageChange(event) {
      // PrimeVue uses zero-based indexing for pages
      this.page = event.page + 1; // Convert to 1-based indexing
      this.size = event.rows;
      this.fetchSequences();
    },
    onFilter(event) {
      this.filters = event.filters;
      this.page = 1; // Reset to first page on filter change
      this.fetchSequences();
    },
    onSpeciesChange() {
      this.page = 1; // Reset to first page when species changes
      this.fetchSequences();
    },
    onGlobalFilter() {
      this.page = 1; // Reset to first page on global filter change
      this.fetchSequences();
    },
    refreshTable() {
      this.fetchSequences();
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

.page-title {
  margin-bottom: 20px;
}

/* Adjust styles as needed to match your theme or preferences */
.datatable-gridlines {
  /* Add any specific styling if required */
}
</style>
