<template>
  <div class="home p-p-4">
    <!-- Welcome Panel -->
    <div class="p-grid p-justify-center p-align-center">
      <div class="p-col-12 p-md-8 p-lg-6">
        <Panel class="p-shadow-2">
          <template #header>
            <div class="panel-header">
              <h2>Welcome to HaploSearch!</h2>
              <h4>Empowering Your Genetic Research</h4>
            </div>
          </template>
          <p>
            HaploSearch is designed to streamline your genetic research by allowing you to efficiently query and analyze haplotype data. Whether you're a USDA researcher, collaborator, or student, our intuitive tools and robust features empower you to make informed decisions and drive discoveries.
          </p>
          <Button label="Learn More" icon="pi pi-info-circle" class="p-mt-3" @click="navigateToQuery" />
        </Panel>
      </div>
    </div>

    <!-- Query Feature Panel -->
    <div class="p-grid p-justify-center p-mt-6">
      <div class="p-col-12 p-md-10 p-lg-8">
        <Panel header="Query Feature" class="p-shadow-2">
          <p>
            The Query feature of HaploSearch allows you to perform comprehensive searches across your genetic datasets. With advanced filtering options, you can pinpoint specific haplotypes, analyze genetic variations, and generate detailed reports. Our user-friendly interface ensures that even complex queries are straightforward and accessible.
          </p>

          <!-- Key Capabilities Section -->
          <div class="key-capabilities p-mt-4">
            <h5>Key Capabilities</h5>
            <ul class="p-pl-3">
              <li class="p-mb-2">
                <i class="pi pi-check-circle p-text-success p-mr-2"></i>
                <strong>Advanced Filtering:</strong> Narrow down your search using multiple genetic markers and criteria.
              </li>
              <li class="p-mb-2">
                <i class="pi pi-check-circle p-text-success p-mr-2"></i>
                <strong>Real-Time Visualization:</strong> Visualize your query results with interactive charts and graphs.
              </li>
              <li class="p-mb-2">
                <i class="pi pi-check-circle p-text-success p-mr-2"></i>
                <strong>Exportable Reports:</strong> Generate and export detailed reports for your research needs.
              </li>
            </ul>
          </div>

          <Button label="Start Querying" icon="pi pi-search" class="p-mt-3 p-button-primary" @click="navigateToQuery" />
        </Panel>
      </div>
    </div>
  </div>
</template>

<script>
import Panel from 'primevue/panel';
import Button from 'primevue/button';

export default {
  name: 'Home',
  components: {
    Panel,
    Button
  },
  methods: {
    navigateToQuery() {
      this.$router.push('/query');
    }
  }
}
</script>

<style scoped>
.home {
  background-color: var(--surface-1);
  min-height: 100vh;
  padding: 2rem 0;
}

.panel-header h2 {
  color: var(--primary-color);
  font-size: 1.5rem;
  margin: 0;
}

.panel-header h4 {
  color: var(--text-color-secondary);
  font-size: 1rem;
  margin: 0.5rem 0 0 0;
}

.p-shadow-2 {
  box-shadow: var(--shadow-2);
}

@media (max-width: 768px) {
  .home {
    padding: 1rem 0;
  }

  .panel-header h2 {
    font-size: 1.25rem;
  }

  .panel-header h4 {
    font-size: 0.9rem;
  }
}

/* Optional: Add padding or other styles to the panel content if needed */
.panel-header {
  display: flex;
  flex-direction: column;
}

.panel-header h2,
.panel-header h4 {
  text-align: center;
}

/* Ensure text is visible against the background */
p {
  color: var(--text-color-primary, #000);
}

/* Key Capabilities and Info Sections Styling */
.key-capabilities h5,
.info-section h5 {
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.key-capabilities ul {
  list-style: none;
  padding-left: 0;
}

.key-capabilities li {
  display: flex;
  align-items: center;
  margin-bottom: 0.5rem;
}

.key-capabilities li i {
  margin-right: 0.5rem;
}

/* Optional: Additional styling for subheadings and content */
.info-section {
  /* Add any additional styles for info sections here */
}
</style>
