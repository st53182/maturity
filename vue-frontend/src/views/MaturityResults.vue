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
        <p class="average-line">
          {{ $t('maturity.overallScore') }}: <strong>{{ averageScore.toFixed(2) }}</strong>
        </p>

        <div
          v-for="group in radarGroups"
          :key="group.title"
          v-show="chartDataForGroup(group).labels.length"
          class="radar-wrap"
        >
          <RadarChart :chart-data="chartDataForGroup(group)" :title="group.title" />
        </div>

        <div v-if="recommendationsHtml" class="recommendations-block">
          <h2 class="rec-title">{{ $t('maturity.recommendationsTitle') }}</h2>
          <div v-html="recommendationsHtml" class="rec-html"></div>
        </div>
      </div>

      <div class="actions">
        <button
          type="button"
          class="btn-rec"
          :disabled="loadingRecs"
          @click="fetchRecommendations"
        >
          {{ loadingRecs ? $t('maturity.generatingRecs') : $t('maturity.getRecommendations') }}
        </button>
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
      radarGroups: [],
      loading: true,
      error: null,
      exporting: false,
      recommendationsHtml: '',
      loadingRecs: false
    };
  },
  computed: {
    averageScore() {
      if (!this.results || !Object.keys(this.results).length) return 0;
      let total = 0;
      let count = 0;
      for (const cat of Object.values(this.results)) {
        for (const v of Object.values(cat)) {
          total += parseFloat(v) || 0;
          count++;
        }
      }
      return count ? total / count : 0;
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
    chartDataForGroup(group) {
      if (!group || !group.categories || !this.results) {
        return { labels: [], datasets: [] };
      }
      const labels = [];
      const data = [];
      for (const cat of group.categories) {
        const subs = this.results[cat];
        if (!subs) continue;
        const vals = Object.values(subs).map(v => parseFloat(v) || 0);
        const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
        labels.push(cat);
        data.push(avg);
      }
      return {
        labels,
        datasets: [
          {
            label: this.$t('maturity.radarDataset'),
            data,
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
            borderColor: 'rgba(75, 192, 192, 1)',
            borderWidth: 2
          }
        ]
      };
    },
    async loadResults() {
      try {
        const res = await axios.get(`/api/maturity/${this.token}/results`);
        this.teamName = res.data.team_name;
        this.completedAt = res.data.completed_at;
        this.results = res.data.results || {};
        this.radarGroups = res.data.radar_groups || [];
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки результатов';
      } finally {
        this.loading = false;
      }
    },
    async fetchRecommendations() {
      if (this.loadingRecs) return;
      this.loadingRecs = true;
      this.recommendationsHtml = '';
      try {
        const res = await axios.post(`/api/maturity/${this.token}/recommendations`);
        this.recommendationsHtml = res.data.content || '';
      } catch (e) {
        this.recommendationsHtml = '<p class="rec-error">' + (e.response?.data?.error || 'Ошибка загрузки рекомендаций') + '</p>';
      } finally {
        this.loadingRecs = false;
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
  max-width: 900px;
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
  margin-bottom: 1rem;
}

.meta .team { font-weight: 600; color: #111; }
.meta .date { margin-left: 1rem; }

.average-line {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.radar-wrap {
  margin: 1.5rem 0;
  min-height: 320px;
}

.recommendations-block {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}

.rec-title {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #111;
}

.rec-html {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #374151;
}

.rec-html :deep(p) { margin-bottom: 0.75rem; }
.rec-html :deep(ul) { margin: 0.5rem 0 1rem 1.5rem; }
.rec-html :deep(li) { margin-bottom: 0.25rem; }
.rec-error { color: #c00; }

.actions {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.btn-rec, .btn-pdf {
  padding: 0.75rem 1.5rem;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-rec {
  background: #059669;
}

.btn-rec:hover:not(:disabled) { background: #047857; }

.btn-pdf {
  background: #2563eb;
}

.btn-pdf:hover:not(:disabled) { background: #1d4ed8; }

.btn-rec:disabled, .btn-pdf:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
