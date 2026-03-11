<template>
  <div class="take-maturity">
    <div v-if="loading" class="loading">{{ $t('maturity.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="survey.completed" class="already-done">
      <p>{{ $t('maturity.alreadyCompleted') }}</p>
      <router-link :to="`/maturity/${token}/results`" class="link-results">{{ $t('maturity.viewResults') }}</router-link>
    </div>
    <div v-else class="maturity-form">
      <header class="maturity-header">
        <h1>{{ $t('maturity.title') }}</h1>
        <p v-if="survey.team_name" class="team-name">{{ survey.team_name }}</p>
        <button v-if="survey.business_metrics_glossary && survey.business_metrics_glossary.length" type="button" class="glossary-toggle" @click="showGlossary = !showGlossary">
          {{ showGlossary ? 'Скрыть глоссарий метрик' : 'Что значат метрики (глоссарий)' }}
        </button>
        <div v-if="showGlossary && survey.business_metrics_glossary" class="glossary-block">
          <div v-for="m in survey.business_metrics_glossary" :key="m.id" class="glossary-item">
            <strong>{{ m.name }}</strong> — {{ m.description }}
          </div>
        </div>
      </header>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <p class="progress-text">{{ $t('maturity.progress', { current: Math.min(currentPage * questionsPerPage + currentBatch.length, survey.questions.length), total: survey.questions.length }) }}</p>

      <div class="batch">
        <div v-for="q in currentBatch" :key="q.id" class="question-block">
          <div class="question-main">
            <div class="question-row" :class="{ 'why-visible': expandedWhy[q.id] }">
              <p class="question-text">{{ q.text }}</p>
              <button
                v-if="q.why_important"
                type="button"
                class="why-trigger"
                :aria-expanded="!!expandedWhy[q.id]"
                @click="toggleWhy(q.id)"
              >
                Почему это важно?
              </button>
              <button
                type="button"
                class="clarify-trigger"
                :disabled="clarifyLoading === q.id"
                @click="askClarify(q)"
              >
                {{ clarifyLoading === q.id ? '...' : 'Попросить разъяснения' }}
              </button>
              <div v-if="q.why_important" class="question-why-hint" :class="{ visible: expandedWhy[q.id] }">
                <span class="why-label">Почему это важно:</span> {{ q.why_important }}
              </div>
            </div>
            <div class="yes-no">
              <button
                type="button"
                :class="['btn-answer', 'btn-yes', { active: answers[q.id] === true }]"
                @click="setAnswer(q.id, true)"
              >
                {{ $t('maturity.yes') }}
              </button>
              <button
                type="button"
                :class="['btn-answer', 'btn-no', { active: answers[q.id] === false }]"
                @click="setAnswer(q.id, false)"
              >
                {{ $t('maturity.no') }}
              </button>
            </div>
          </div>
          <div v-if="clarifyResult && clarifyResult.id === q.id" class="clarify-block">
              <strong>Разъяснение (на примере банковских команд):</strong>
              <p class="clarify-text">{{ clarifyResult.content }}</p>
            </div>
          <div v-if="q.business_metrics" class="info-block info-business-metrics">
            <div class="info-block-title">Бизнес-метрики</div>
            <p class="info-block-text">{{ q.business_metrics }}</p>
            <p class="business-metrics-disclaimer">{{ survey.business_metrics_disclaimer }}</p>
          </div>
          <div v-if="q.metrics_impact || q.negative_for_business" class="question-info">
            <div v-if="q.metrics_impact" class="info-block info-metrics">
              <div class="info-block-title">Метрики влияния</div>
              <p class="info-block-text">{{ q.metrics_impact }}</p>
            </div>
            <div v-if="q.negative_for_business" class="info-block info-negative">
              <div class="info-block-title">Если у команды проблемы в этом</div>
              <p class="info-block-text">{{ q.negative_for_business }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="nav-actions">
        <button v-if="currentPage > 0" type="button" class="btn-nav prev" @click="currentPage--">
          {{ $t('maturity.prev') }}
        </button>
        <button
          v-if="currentPage < totalPages - 1"
          type="button"
          class="btn-nav next"
          :disabled="!isCurrentBatchFilled"
          @click="currentPage++"
        >
          {{ $t('maturity.next') }}
        </button>
        <button
          v-if="currentPage === totalPages - 1"
          type="button"
          class="btn-nav submit"
          :disabled="!allFilled"
          @click="submit"
        >
          {{ $t('maturity.submit') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const QUESTIONS_PER_PAGE = 10;

export default {
  name: 'TakeMaturity',
  data() {
    return {
      token: '',
      survey: { team_name: null, questions: [], completed: false },
      answers: {},
      currentPage: 0,
      loading: true,
      error: null,
      submitting: false,
      questionsPerPage: QUESTIONS_PER_PAGE,
      expandedWhy: {},
      clarifyLoading: null,
      clarifyResult: null,
      showGlossary: false
    };
  },
  computed: {
    totalPages() {
      const n = this.survey.questions?.length || 0;
      return Math.ceil(n / QUESTIONS_PER_PAGE) || 1;
    },
    currentBatch() {
      const q = this.survey.questions || [];
      const start = this.currentPage * QUESTIONS_PER_PAGE;
      return q.slice(start, start + QUESTIONS_PER_PAGE);
    },
    progressPercent() {
      const total = this.survey.questions?.length || 0;
      if (!total) return 0;
      const filled = Object.keys(this.answers).filter(k => this.answers[k] !== undefined && this.answers[k] !== null).length;
      return Math.min(100, (filled / total) * 100);
    },
    isCurrentBatchFilled() {
      return this.currentBatch.every(q => this.answers[q.id] !== undefined && this.answers[q.id] !== null);
    },
    allFilled() {
      const total = this.survey.questions?.length || 0;
      if (!total) return false;
      for (let i = 0; i < total; i++) {
        if (this.answers[i] === undefined || this.answers[i] === null) return false;
      }
      return true;
    }
  },
  async mounted() {
    this.token = this.$route.params.token;
    await this.loadSurvey();
  },
  methods: {
    async loadSurvey() {
      try {
        const res = await axios.get(`/api/maturity/${this.token}`);
        this.survey = res.data;
        this.survey.business_metrics_disclaimer = res.data.business_metrics_disclaimer || '';
        this.survey.business_metrics_glossary = res.data.business_metrics_glossary || [];
        this.survey.questions.forEach(q => {
          if (this.answers[q.id] === undefined) this.answers[q.id] = null;
        });
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки опроса';
      } finally {
        this.loading = false;
      }
    },
    setAnswer(id, value) {
      this.answers[id] = value;
    },
    toggleWhy(id) {
      this.expandedWhy = { ...this.expandedWhy, [id]: !this.expandedWhy[id] };
    },
    async askClarify(q) {
      this.clarifyLoading = q.id;
      this.clarifyResult = null;
      try {
        const res = await axios.post(`/api/maturity/${this.token}/clarify`, {
          question_text: q.text
        });
        this.clarifyResult = { id: q.id, content: res.data.content || '' };
      } catch (e) {
        this.clarifyResult = { id: q.id, content: 'Ошибка: ' + (e.response?.data?.error || 'Сервис недоступен') };
      } finally {
        this.clarifyLoading = null;
      }
    },
    async submit() {
      if (!this.allFilled || this.submitting) return;
      this.submitting = true;
      try {
        const total = this.survey.questions.length;
        const arr = [];
        for (let i = 0; i < total; i++) {
          arr.push(this.answers[i] === true);
        }
        await axios.post(`/api/maturity/${this.token}/submit`, { answers: arr });
        this.$router.push(`/maturity/${this.token}/results`);
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка отправки';
      } finally {
        this.submitting = false;
      }
    }
  }
};
</script>

<style scoped>
.take-maturity {
  max-width: 720px;
  margin: 2rem auto;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading, .error, .already-done {
  text-align: center;
  padding: 2rem;
}

.error { color: #c00; }

.already-done .link-results {
  display: inline-block;
  margin-top: 1rem;
  color: #2563eb;
}

.maturity-header {
  text-align: center;
  margin-bottom: 1.5rem;
}

.maturity-header h1 { font-size: 1.5rem; color: #111; }
.team-name { color: #555; margin-top: 0.5rem; }
.glossary-toggle {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #0369a1;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}
.glossary-block {
  margin-top: 0.75rem;
  padding: 1rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  text-align: left;
  max-height: 200px;
  overflow-y: auto;
}
.glossary-item {
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
  line-height: 1.4;
  color: #475569;
}
.glossary-item strong { color: #334155; }

.progress-bar {
  height: 8px;
  background: #e5e7eb;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #10b981);
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 0.875rem;
  color: #6b7280;
  margin-bottom: 1.5rem;
}

.batch { margin-bottom: 2rem; }

.question-block {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}

@media (min-width: 680px) {
  .question-block {
    grid-template-columns: 1fr minmax(200px, 280px);
  }
}

.question-main {
  min-width: 0;
}

.question-row {
  position: relative;
  margin-bottom: 0.75rem;
}

.question-text {
  font-size: 1rem;
  line-height: 1.5;
  color: #111;
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  padding-right: 0.5rem;
}

/* «Почему это важно» показывается только по клику на кнопку */
.question-why-hint {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #047857;
  background: #ecfdf5;
  border-left: 3px solid #10b981;
  padding: 0.5rem 0.75rem;
  border-radius: 0 6px 6px 0;
  margin-top: 0.5rem;
  max-height: 0;
  opacity: 0;
  overflow: hidden;
  transition: max-height 0.25s ease, opacity 0.2s ease, margin 0.2s ease;
}

.question-why-hint.visible {
  max-height: 12em;
  opacity: 1;
}

.why-trigger {
  font-size: 0.75rem;
  color: #059669;
  background: none;
  border: none;
  padding: 0.25rem 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.why-trigger:hover { color: #047857; }

.why-label {
  font-weight: 600;
  color: #065f46;
}

.clarify-trigger {
  font-size: 0.75rem;
  color: #0369a1;
  background: none;
  border: none;
  padding: 0.25rem 0;
  cursor: pointer;
  text-decoration: underline;
  margin-left: 0.5rem;
}
.clarify-trigger:hover:not(:disabled) { color: #0284c7; }
.clarify-trigger:disabled { opacity: 0.7; cursor: wait; }

.clarify-block {
  margin-top: 0.5rem;
  padding: 0.75rem 1rem;
  background: #f0f9ff;
  border-left: 3px solid #0ea5e9;
  border-radius: 0 8px 8px 0;
  font-size: 0.875rem;
}
.clarify-block strong { color: #0369a1; }
.clarify-text { margin: 0.5rem 0 0 0; line-height: 1.5; color: #0c4a6e; white-space: pre-wrap; }

.question-info {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  min-width: 0;
}

.info-block {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid transparent;
}

.info-block-title {
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.35rem;
}

.info-block-text {
  font-size: 0.8125rem;
  line-height: 1.45;
  margin: 0;
}

.info-metrics {
  background: #eff6ff;
  border-color: #bfdbfe;
  color: #1e40af;
}

.info-metrics .info-block-title { color: #1d4ed8; }
.info-metrics .info-block-text { color: #1e40af; }

.info-negative {
  background: #fef2f2;
  border-color: #fecaca;
  color: #991b1b;
}

.info-negative .info-block-title { color: #b91c1c; }
.info-negative .info-block-text { color: #991b1b; }

.info-business-metrics {
  background: #fefce8;
  border-color: #fde047;
}
.info-business-metrics .info-block-title { color: #854d0e; }
.info-business-metrics .info-block-text { color: #713f12; }
.business-metrics-disclaimer {
  font-size: 0.75rem;
  color: #6b7280;
  margin: 0.5rem 0 0 0;
  font-style: italic;
}

.yes-no {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.btn-answer {
  padding: 0.6rem 1.25rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  border: 2px solid #d1d5db;
  background: #fff;
  transition: all 0.2s;
}

.btn-yes.active { background: #10b981; border-color: #10b981; color: #fff; }
.btn-no.active { background: #ef4444; border-color: #ef4444; color: #fff; }

.btn-answer:hover:not(.active) { border-color: #9ca3af; background: #f3f4f6; }

.nav-actions {
  display: flex;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.btn-nav {
  padding: 0.75rem 1.5rem;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-nav:disabled { opacity: 0.5; cursor: not-allowed; }

.prev { background: #9ca3af; color: #fff; }
.next { background: #3b82f6; color: #fff; }
.submit { background: #10b981; color: #fff; }
</style>
