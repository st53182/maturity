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
      </header>

      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
      </div>
      <p class="progress-text">{{ $t('maturity.progress', { current: currentPage * 5 + currentBatch.length, total: survey.questions.length }) }}</p>

      <div class="batch">
        <div v-for="q in currentBatch" :key="q.id" class="question-block">
          <p class="question-text">{{ q.text }}</p>
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

const QUESTIONS_PER_PAGE = 5;

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
      submitting: false
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
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}

.question-text {
  font-size: 1rem;
  line-height: 1.5;
  color: #111;
  margin-bottom: 0.75rem;
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
