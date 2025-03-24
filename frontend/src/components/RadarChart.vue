<template>
  <div class="radar-chart">
    <h3>{{ title }}</h3>
    <Radar :data="chartData" :options="chartOptions" />
  </div>
</template>

<script>
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  Title
} from 'chart.js';

import { Radar } from 'vue-chartjs';

ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  Title
);

export default {
  name: 'RadarChart',
  components: {
    Radar
  },
  props: {
    chartData: {
      type: Object,
      required: true
    },
    title: {
      type: String,
      default: ''
    }
  },
  computed: {
    chartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          r: {
            beginAtZero: true,
            suggestedMin: 0,
            suggestedMax: 5,
            ticks: {
              stepSize: 1
            }
          }
        },
        plugins: {
          legend: {
            position: 'top'
          },
          title: {
            display: false // Мы используем <h3>{{ title }}</h3> вместо встроенного title
          }
        }
      };
    }
  }
};
</script>

<style scoped>
.radar-chart {
  width: 100%;
  max-width: 600px;
  height: 400px;
  margin-bottom: 30px;
  background: white;
  border-radius: 10px;
  padding: 15px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
</style>


