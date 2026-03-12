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
          class="group-block"
        >
          <div class="radar-wrap">
            <RadarChart :chart-data="chartDataForGroup(group)" :title="group.title" />
          </div>
          <div class="themes-list">
            <button
              v-for="cat in themesInGroup(group)"
              :key="cat.theme"
              type="button"
              class="theme-row"
              @click="openDetail(cat.theme)"
            >
              <span class="theme-name">{{ cat.theme }}</span>
              <span class="theme-score" :class="scoreClass(cat.avg)">{{ formatScore(cat.avg) }}</span>
            </button>
          </div>
        </div>

        <div v-if="recommendationsHtml" class="recommendations-block">
          <h2 class="rec-title">{{ $t('maturity.recommendationsTitle') }}</h2>
          <div v-html="recommendationsHtml" class="rec-html"></div>
        </div>
      </div>

      <div class="actions">
        <button type="button" class="btn-edit" @click="$router.push(`/maturity/${token}/edit`)">
          Изменить ответы
        </button>
        <button type="button" class="btn-show-all" @click="showAllModal = true">
          Показать все
        </button>
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

      <!-- Модальное окно: карточки вопросов и ответов по выбранной теме -->
      <div v-if="selectedTheme" class="detail-overlay" @click.self="selectedTheme = null">
        <div class="detail-modal">
          <div class="detail-header">
            <h3>{{ selectedTheme }}</h3>
            <button type="button" class="detail-close" aria-label="Закрыть" @click="selectedTheme = null">×</button>
          </div>
          <div class="detail-cards">
            <div
              v-for="item in questionsForTheme(selectedTheme)"
              :key="item.id"
              class="detail-card"
            >
              <p class="detail-question">{{ item.text }}</p>
              <div class="detail-answer" :class="item.answer ? 'answer-yes' : 'answer-no'">
                {{ item.answer ? $t('maturity.yes') : $t('maturity.no') }}
              </div>
              <div v-if="item.why_important" class="detail-why">
                <strong>Почему это важно:</strong> {{ item.why_important }}
              </div>
              <div v-if="item.metrics_impact" class="detail-metrics">
                <strong>Метрики влияния:</strong> {{ item.metrics_impact }}
              </div>
              <div v-if="item.negative_for_business" class="detail-negative">
                <strong>Если у команды проблемы в этом:</strong> {{ item.negative_for_business }}
              </div>
              <div v-if="item.business_metrics" class="detail-business-metrics">
                <strong>Бизнес-метрики:</strong> {{ item.business_metrics }}
                <p v-if="businessMetricsDisclaimer" class="detail-disclaimer">{{ businessMetricsDisclaimer }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Модальное окно: все вопросы и ответы -->
      <div v-if="showAllModal" class="detail-overlay" @click.self="showAllModal = false">
        <div class="detail-modal detail-modal-full">
          <div class="detail-header">
            <h3>Все вопросы и ответы</h3>
            <button type="button" class="detail-close" aria-label="Закрыть" @click="showAllModal = false">×</button>
          </div>
          <div class="detail-cards detail-cards-full">
            <p v-if="!allQuestionsWithAnswers.length" class="detail-empty">Нет данных о вопросах и ответах.</p>
            <div
              v-for="item in allQuestionsWithAnswers"
              :key="item.id"
              class="detail-card"
            >
              <p class="detail-question"><span class="detail-q-num">{{ item.id + 1 }}.</span> {{ item.text }}</p>
              <div class="detail-answer" :class="item.answer ? 'answer-yes' : 'answer-no'">
                {{ item.answer ? $t('maturity.yes') : $t('maturity.no') }}
              </div>
              <div v-if="item.why_important" class="detail-why">
                <strong>Почему это важно:</strong> {{ item.why_important }}
              </div>
              <div v-if="item.metrics_impact" class="detail-metrics">
                <strong>Метрики влияния:</strong> {{ item.metrics_impact }}
              </div>
              <div v-if="item.negative_for_business" class="detail-negative">
                <strong>Если у команды проблемы в этом:</strong> {{ item.negative_for_business }}
              </div>
              <div v-if="item.business_metrics" class="detail-business-metrics">
                <strong>Бизнес-метрики:</strong> {{ item.business_metrics }}
                <p v-if="businessMetricsDisclaimer" class="detail-disclaimer">{{ businessMetricsDisclaimer }}</p>
              </div>
            </div>
          </div>
        </div>
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
      answers: [],
      questions: [],
      selectedTheme: null,
      showAllModal: false,
      loading: true,
      error: null,
      exporting: false,
      recommendationsHtml: '',
      loadingRecs: false,
      businessMetricsDisclaimer: '',
      businessMetricsGlossary: []
    };
  },
  computed: {
    questionsByTheme() {
      const map = {};
      if (!this.questions.length || !Array.isArray(this.answers)) return map;
      for (const q of this.questions) {
        if (!map[q.theme]) map[q.theme] = [];
        map[q.theme].push({
          ...q,
          answer: this.answers[q.id] === true
        });
      }
      return map;
    },
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
        this.answers = res.data.answers || [];
        this.questions = res.data.questions || [];
        this.businessMetricsDisclaimer = res.data.business_metrics_disclaimer || '';
        this.businessMetricsGlossary = res.data.business_metrics_glossary || [];
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки результатов';
      } finally {
        this.loading = false;
      }
    },
    themesInGroup(group) {
      if (!group || !group.categories || !this.results) return [];
      return group.categories
        .filter(cat => this.results[cat])
        .map(cat => {
          const vals = Object.values(this.results[cat]).map(v => parseFloat(v) || 0);
          const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0;
          return { theme: cat, avg };
        });
    },
    questionsForTheme(theme) {
      return this.questionsByTheme[theme] || [];
    },
    allQuestionsWithAnswers() {
      const questions = this.questions || [];
      const answers = Array.isArray(this.answers) ? this.answers : [];
      if (!questions.length) return [];
      return questions.map(q => ({
        ...q,
        answer: answers[q.id] === true
      }));
    },
    openDetail(theme) {
      this.selectedTheme = theme;
    },
    formatScore(avg) {
      return avg != null ? avg.toFixed(1) : '—';
    },
    scoreClass(avg) {
      if (avg >= 4) return 'score-high';
      if (avg >= 2) return 'score-mid';
      return 'score-low';
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

.group-block {
  margin: 1.5rem 0;
  overflow: visible;
}

.radar-wrap {
  margin-bottom: 0.75rem;
  height: 620px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.themes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
  min-height: 3rem;
}

.theme-row {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.theme-row:hover {
  background: #e0f2fe;
  border-color: #7dd3fc;
}

.theme-name {
  color: #334155;
}

.theme-score {
  font-weight: 600;
  min-width: 2rem;
  text-align: right;
}

.theme-score.score-high { color: #059669; }
.theme-score.score-mid { color: #d97706; }
.theme-score.score-low { color: #dc2626; }

/* Модальное окно с карточками вопросов/ответов */
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.detail-modal {
  background: #fff;
  border-radius: 12px;
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}
.detail-modal-full {
  max-width: 800px;
  max-height: 95vh;
}
.detail-cards-full {
  min-height: 200px;
}
.detail-empty {
  padding: 2rem;
  color: #6b7280;
  margin: 0;
}
.detail-q-num {
  color: #6b7280;
  margin-right: 0.25rem;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.detail-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #111;
}

.detail-close {
  width: 2rem;
  height: 2rem;
  padding: 0;
  font-size: 1.5rem;
  line-height: 1;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 6px;
}

.detail-close:hover {
  background: #e5e7eb;
  color: #111;
}

.detail-cards {
  overflow-y: auto;
  padding: 1rem 1.25rem;
}

.detail-card {
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.detail-question {
  font-weight: 600;
  color: #111;
  margin: 0 0 0.5rem 0;
  font-size: 0.9375rem;
}

.detail-answer {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.detail-answer.answer-yes {
  background: #d1fae5;
  color: #065f46;
}

.detail-answer.answer-no {
  background: #fee2e2;
  color: #991b1b;
}

.detail-why,
.detail-metrics,
.detail-negative {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #4b5563;
  margin: 0.5rem 0 0 0;
}

.detail-why strong,
.detail-metrics strong,
.detail-negative strong {
  color: #374151;
}

.detail-business-metrics {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: #713f12;
  background: #fefce8;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
}
.detail-disclaimer {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  margin: 0.35rem 0 0 0;
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

.btn-edit, .btn-show-all, .btn-rec, .btn-pdf {
  padding: 0.75rem 1.5rem;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-edit {
  background: #64748b;
}
.btn-edit:hover { background: #475569; }

.btn-show-all {
  background: #0d9488;
}
.btn-show-all:hover { background: #0f766e; }

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
