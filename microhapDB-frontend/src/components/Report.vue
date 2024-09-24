<template>
  <div class="report-container">
    <div class="species-filter">
      <select v-model="species" class="species-dropdown" @change="fetchReport">
        <option value="all">All Species</option>
        <option value="sweetpotato">Sweetpotato</option>
        <option value="blueberry">Blueberry</option>
        <option value="alfalfa">Alfalfa</option>
        <option value="cranberry">Cranberry</option>
      </select>
    </div>
    <h2 class="page-title">{{ speciesTitle }}</h2>
    <div v-if="loading" class="loading-message">Loading report...</div>
    <div v-else-if="report">
      <div class="report-section" v-if="species && species !== 'all'">
        <h3>Total Unique Microhaplotypes</h3>
        <p>{{ report.total_unique_sequences }}</p>
      </div>
      <div class="report-section" v-if="species && species !== 'all'">
        <h3>New Microhaplotypes Last Batch</h3>
        <p>{{ report.new_sequences_this_batch }}</p>
      </div>
      <div class="report-section" v-if="species && species !== 'all'">
        <h3></h3>
        <table class="batch-table">
          <thead>
            <tr>
              <th>Version</th>
              <th>Date</th>
              <th>New Microhaplotypes</th>
              <th>Cumulative Microhaplotypes</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="batch in report.batch_history" :key="batch.version">
              <td>{{ 'V' + batch.version.toString().padStart(3, '0') }}</td>
              <td>{{ batch.date }}</td>
              <td>{{ batch.new_sequences }}</td>
              <td>{{ batch.cumulative_sum }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="report-section">
        <h3></h3>
        <div ref="d3ChartContainer" class="chart-grid"></div>
      </div>
    </div>
    <p v-else>No report available.</p>
  </div>
</template>


<script>
import axiosInstance from '../axiosConfig';
import * as d3 from 'd3';

export default {
  name: 'DatabaseReport',
  data() {
    return {
      report: null,
      loading: true,
      species: 'all',
    };
  },
  computed: {
    speciesTitle() {
      if (this.species === 'all') {
        return 'All Species Unique Microhaplotypes';
      } else if (this.species) {
        return `${this.species.charAt(0).toUpperCase() + this.species.slice(1)} Unique Microhaplotypes`;
      } else {
        return 'Sequences';
      }
    },
  },
  methods: {
    async fetchReport() {
      this.loading = true;
      try {
        const response = await axiosInstance.get('/posts/report_data', {
          params: {
            species: this.species || 'all',
          },
        });
        if (response.data.error) {
          console.error('Error fetching report:', response.data.error);
          this.report = null;
        } else {
          this.report = response.data;
          console.log('Report data fetched:', this.report); // Debugging
          this.renderD3Charts(); // Render the D3 charts after data is fetched
        }
      } catch (error) {
        console.error('There was an error fetching the report:', error);
        this.report = null;
      } finally {
        this.loading = false;
      }
    },
    renderD3Charts() {
      const container = d3.select(this.$refs.d3ChartContainer);
      container.selectAll("*").remove(); // Clear previous charts

      if (this.report && this.report.line_chart_data) {
        if (this.species === 'all') {
          // Get and sort species names
          const speciesKeys = Object.keys(this.report.line_chart_data).sort();

          // Loop through all species to render multiple charts
          for (const speciesKey of speciesKeys) {
            const data = this.report.line_chart_data[speciesKey];
            const chartDiv = container.append('div').attr('class', 'chart');
            this.renderD3Chart(chartDiv, data.labels, data.cumulative_sums, speciesKey);
          }
        } else {
          // Render a single larger chart for the selected species
          const data = this.report.line_chart_data;
          const chartDiv = container.append('div').attr('class', 'chart');
          this.renderD3Chart(chartDiv, data.labels, data.cumulative_sums, this.species, 600, 400); // Larger dimensions
        }
      } else {
        console.warn('No line chart data available to render.');
      }
    },
    renderD3Chart(container, labels, cumulativeSums, species, width = 400, height = 300) {
      const margin = { top: 40, right: 30, bottom: 50, left: 50 },
        innerWidth = width - margin.left - margin.right,
        innerHeight = height - margin.top - margin.bottom;

      const svg = container.append('svg')
        .attr('width', width)
        .attr('height', height);

      const chartGroup = svg.append('g')
        .attr('transform', `translate(${margin.left},${margin.top})`);

      const x = d3.scaleLinear()
        .domain([0, labels.length - 1])
        .range([0, innerWidth]);

      const yMax = d3.max(cumulativeSums) * 1.1; // Add 10% padding at the top
      const y = d3.scaleLinear()
        .domain([0, yMax])
        .range([innerHeight, 0]);

      // Define color scale without a predefined domain
      const colorScale = d3.scaleOrdinal(d3.schemeCategory10);

      // // Add vertical gridlines
      // function make_x_gridlines() {
      //   return d3.axisBottom(x).ticks(labels.length);
      // }

      // chartGroup.append('g')
      //   .attr('class', 'grid')
      //   .attr('transform', `translate(0,${innerHeight})`)
      //   .call(make_x_gridlines()
      //     .tickSize(-innerHeight)
      //     .tickFormat('')
      //   );

      // Add horizontal gridlines
      function make_y_gridlines() {
        return d3.axisLeft(y).ticks(5);
      }

      chartGroup.append('g')
        .attr('class', 'grid')
        .call(make_y_gridlines()
          .tickSize(-innerWidth)
          .tickFormat('')
        )
        .selectAll('line')
        .attr('stroke', '#d3d3d3')// Light gray color
        .attr('stroke-width', '1'); 

      // Add X-axis
      chartGroup.append('g')
        .attr('transform', `translate(0,${innerHeight})`)
        .call(d3.axisBottom(x).ticks(labels.length - 1).tickFormat(i => labels[i]));

      // Add Y-axis
      chartGroup.append('g')
        .call(d3.axisLeft(y));

      // Draw the line
      const lineColor = colorScale(species);

      chartGroup.append('path')
        .datum(cumulativeSums)
        .attr('fill', 'none')
        .attr('stroke', lineColor)
        .attr('stroke-width', 2)
        .attr('d', d3.line()
          .x((d, i) => x(i))
          .y(d => y(d))
        );

      // X-axis label
      chartGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('x', innerWidth / 2)
        .attr('y', innerHeight + 40)
        .text('Database Build')
        .style('font-size', '18px');

      // Y-axis label
      chartGroup.append('text')
        .attr('text-anchor', 'middle')
        .attr('transform', `translate(-35,${innerHeight / 2})rotate(-90)`)
        .text('Microhaplotypes Captured')
        .style('font-size', '18px');

      // Chart title using the species name
      svg.append('text')
        .attr('x', width / 2)
        .attr('y', 25) // Position at the top center
        .attr('text-anchor', 'middle')
        .style('font-size', '18px')
        .style('fill', '#00796b')
        .text(`${species.charAt(0).toUpperCase() + species.slice(1)}`);
    },
  },
  mounted() {
    this.fetchReport();
  },
  watch: {
  species() {
    this.fetchReport();
  },
},

};
</script>




<style scoped>
.report-container {
  max-width: 1200px;
  margin: auto;
  padding: 20px;
}

h2 {
  color: #00796b; /* Aesthetic green color */
  text-align: center;
  margin-bottom: 30px;
}

.species-dropdown {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 4px;
  display: block;
  margin: 0 auto 20px auto; /* Center the dropdown */
}

.loading-message {
  text-align: center;
  color: #00796b;
  margin-top: 20px;
}

.report-section {
  margin-bottom: 20px;
}

.batch-table {
  width: 100%;
  border-collapse: collapse;
}

.batch-table th, .batch-table td {
  padding: 12px 15px;
  border: 1px solid #ddd;
  text-align: left;
}

.batch-table th {
  background-color: #00796b;
  color: white;
}

.batch-table tr:nth-child(even) {
  background-color: #f2f2f2;
}

.batch-table tr:hover {
  background-color: #e1f7f5;
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); /* Responsive 3-column layout */
  gap: 20px; /* Space between charts */
  margin-top: 30px; /* Adds more space from the top */
  justify-content: center;
}

.species-chart {
  text-align: center;
  padding: 15px; /* Increased padding for breathing room */
  border: 1px solid #ccc; /* Lighter border color */
  border-radius: 10px; /* Slightly more rounded corners */
  background-color: #ffffff; /* White background for a clean look */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); /* Subtle shadow for an elevated effect */
  height: 300px; /* Slightly taller to ensure the chart fits well */
  display: flex;
  flex-direction: column;
  transition: transform 0.3s ease; /* Smooth animation */
}

.species-chart:hover {
  transform: translateY(-5px); /* Lift the chart on hover */
}

.species-chart h4 {
  margin-bottom: 10px;
  color: #00796b; /* Aesthetic green for the title */
  font-size: 1.2rem; /* Slightly larger font size */
}

.species-chart canvas {
  flex: 1;
  max-height: 80%; /* Ensure canvas fills available space */
}

.line-chart {
  position: relative;
  height: 100%;
}

@media (max-width: 768px) {
  /* Mobile responsiveness: 1-column layout */
  .chart-grid {
    grid-template-columns: 1fr;
    gap: 15px; /* Smaller gap on mobile */
  }

  .chart-container {
  max-width: 400px; /* Limit the width of the chart */
  max-height: 400px; /* Limit the height of the chart */
  margin: 0 auto; /* Center the chart */
  justify-content: center;
}


  .species-chart {
    height: 250px; /* Reduced height for mobile view */
  }
}

.grid line {
  stroke: rgba(211, 211, 211, 0.818);
  stroke-opacity: 0.2;
  shape-rendering: crispEdges;
}

.grid path {
  stroke-width: 0;
}

.chart {
  margin-bottom: 20px;
}

.chart-grid .chart {
  /* Adjust chart sizing */
  width: 100%;
}

@media (max-width: 768px) {
  .chart-grid {
    grid-template-columns: 1fr;
  }
}
</style>
