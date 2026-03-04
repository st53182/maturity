<template>
  <div class="maturity-results">
    <div v-if="loading" class="loading">{{ $t('maturity.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="results-content">
      <div ref="pdfContent" class="pdf-block">
        <h1 class="results-title">{{ $t('maturity.resultsTitle') }}</h1>
        <p class="meta">
          <span v-if="teamName" class="team">{{ teamName }}</span>
          <span v-if="completedAt" class="date">{{ formattedDate }}</span>
        </p>
        <div v-if="mainChartData.labels && mainChartData.labels.length" class="radar-wrap">
          <RadarChart :chart-data="mainChartData" :title="$t('maturity.radarTitle')" />
        </div>
        <p class="average-line">
          {{ $t('maturity.overallScore') }}: <strong>{{ averageScore.toFixed(2) }}</strong>
        </p>
      </div>
      <div class="actions">
        <button type="button" class="btn-pdf" :disabled="exporting" @click="exportPdf">
          {{ exporting ? $t('maturity.exporting') : $t('maturity.downloadPdf') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import RadarChart from '@/components/RadarChart.vue';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

export default {
  name: 'MaturityResults',
  components: { RadarChart },
  data() {
    return {
      token: '',
      teamName: '',
      completedAt: null,
      results: {},
      loading: true,
      error: null,
      exporting: false
    };
  },
  computed: {
    mainChartData() {
      if (!this.results || !Object.keys(this.results).length) {
        return { labels: [], datasets: [] };
      }
      const categories = Object.keys(this.results);
      const scores = categories.map(cat => {
        const vals = Object.values(this.results[cat]).map(v => parseFloat(v) || 0);
        return vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
      });
      return {
        labels: categories,
        datasets: [
          {
            label: this.$t('maturity.radarDataset'),
            data: scores,
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2
          }
        ]
      };
    },
    averageScore() {
      if (!this.mainChartData.datasets || !this.mainChartData.datasets[0]) return 0;
      const d = this.mainChartData.datasets[0].data;
      if (!d.length) return 0;
      return d.reduce((a, b) => a + b, 0) / d.length;
    },
    formattedDate() {
      if (!this.completedAt) return '';
      try {
        return new Date(this.completedAt).toLocaleDateString('ru-RU', {
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        });
      } catch {
        return this.completedAt;
      }
    }
  },
  async mounted() {
    this.token = this.$route.params.token;
    await this.loadResults();
  },
  methods: {
    async loadResults() {
      try {
        const res = await axios.get(`/api/maturity/${this.token}/results`);
        this.teamName = res.data.team_name;
        this.completedAt = res.data.completed_at;
        this.results = res.data.results || {};
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки результатов';
      } finally {
        this.loading = false;
      }
    },
    async exportPdf() {
      if (this.exporting) return;
      const el = this.$refs.pdfContent;
      if (!el) return;
      this.exporting = true;
      try {
        const canvas = await html2canvas(el, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff'
        });
        const imgData = canvas.toDataURL('image/jpeg', 0.92);
        const pdf = new jsPDF('p', 'mm', 'a4');
        const w = pdf.internal.pageSize.getWidth();
        const h = pdf.internal.pageSize.getHeight();
        const imgW = w;
        const imgH = (canvas.height * w) / canvas.width;
        let yOff = 0;
        while (yOff < imgH) {
          if (yOff > 0) pdf.addPage();
          pdf.addImage(imgData, 'JPEG', 0, -yOff, imgW, imgH);
          yOff += h;
        }
        const dateStr = this.formattedDate.replace(/\s/g, '-') || 'report';
        const name = (this.teamName || 'maturity').replace(/[^\w\s-]/g, '').slice(0, 30);
        pdf.save(`оценка-зрелости-${name}-${dateStr}.pdf`);
      } catch (e) {
        console.error(e);
        alert(this.$t('maturity.pdfError'));
      } finally {
        this.exporting = false;
      }
    }
  }
};
</script>

<style scoped>
.maturity-results {
  max-width: 800px;
  margin: 2rem auto;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
}

.error { color: #c00; }

.results-title {
  font-size: 1.5rem;
  color: #111;
  margin-bottom: 0.5rem;
}

.pdf-block {
  background: #fff;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.meta {
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.meta .team { font-weight: 600; color: #111; }
.meta .date { margin-left: 1rem; }

.radar-wrap {
  margin: 1.5rem 0;
  min-height: 380px;
}

.average-line {
  margin-top: 1rem;
  font-size: 1.1rem;
}

.actions { margin-top: 1.5rem; }

.btn-pdf {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-pdf:hover:not(:disabled) { background: #1d4ed8; }
.btn-pdf:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
