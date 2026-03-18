<template>
  <div class="edit-maturity">
    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="edit-form">
      <header class="edit-header">
        <h1>Изменить ответы</h1>
        <p v-if="teamName" class="team-name">{{ teamName }}</p>
        <p class="edit-hint">Измените нужные ответы и нажмите «Сохранить и пересчитать отчёт».</p>
      </header>

      <div class="all-questions">
        <div v-for="q in questions" :key="q.id" class="edit-question-block">
          <p class="edit-question-text">{{ q.id + 1 }}. {{ q.text }}</p>
          <div class="edit-yes-no">
            <button
              type="button"
              :class="['btn-answer', 'btn-yes', { active: answers[q.id] === true }]"
              @click="setAnswer(q.id, true)"
            >
              Да
            </button>
            <button
              type="button"
              :class="['btn-answer', 'btn-no', { active: answers[q.id] === false }]"
              @click="setAnswer(q.id, false)"
            >
              Нет
            </button>
          </div>

          <div class="edit-comment">
            <label class="edit-comment-label">Комментарий (опционально)</label>
            <textarea
              v-model="comments[q.id]"
              class="edit-comment-input"
              :disabled="answers[q.id] === undefined || answers[q.id] === null"
              placeholder="Контекст, примеры, пояснение к ответу…"
              rows="2"
            />
          </div>
        </div>
      </div>

      <div class="edit-actions">
        <button type="button" class="btn-back" @click="$router.push(`/maturity/${token}/results`)">
          ← Назад к отчёту
        </button>
        <button
          type="button"
          class="btn-save"
          :disabled="saving"
          @click="saveAndRecalc"
        >
          {{ saving ? 'Сохранение...' : 'Сохранить и пересчитать отчёт' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'EditMaturity',
  data() {
    return {
      token: '',
      teamName: '',
      questions: [],
      answers: {},
      comments: {},
      loading: true,
      error: null,
      saving: false
    };
  },
  async mounted() {
    this.token = this.$route.params.token;
    await this.load();
  },
  methods: {
    async load() {
      try {
        const [surveyRes, resultsRes] = await Promise.all([
          axios.get(`/api/maturity/${this.token}`),
          axios.get(`/api/maturity/${this.token}/results`)
        ]);
        if (!surveyRes.data.completed) {
          this.error = 'Оценка ещё не пройдена. Сначала пройдите опрос.';
          return;
        }
        this.teamName = surveyRes.data.team_name || resultsRes.data.team_name;
        this.questions = surveyRes.data.questions || [];
        const ansList = resultsRes.data.answers || [];
        const comList = resultsRes.data.comments || [];
        this.answers = {};
        this.comments = {};
        this.questions.forEach(q => {
          this.answers[q.id] = ansList[q.id] === true;
          this.comments[q.id] = (comList[q.id] || '').toString();
        });
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка загрузки';
      } finally {
        this.loading = false;
      }
    },
    setAnswer(id, value) {
      this.answers[id] = value;
    },
    async saveAndRecalc() {
      if (this.saving) return;
      const arr = this.questions.map(q => this.answers[q.id] === true);
      const commentsArr = this.questions.map(q => {
        const s = (this.comments[q.id] || '').toString().trim();
        return s ? s : null;
      });
      this.saving = true;
      try {
        await axios.put(`/api/maturity/${this.token}/answers`, { answers: arr, comments: commentsArr });
        this.$router.push(`/maturity/${this.token}/results`);
      } catch (e) {
        this.error = e.response?.data?.error || 'Ошибка сохранения';
      } finally {
        this.saving = false;
      }
    }
  }
};
</script>

<style scoped>
.edit-maturity {
  max-width: 720px;
  margin: 2rem auto;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
}
.error { color: #c00; }

.edit-header {
  margin-bottom: 1.5rem;
}
.edit-header h1 { font-size: 1.35rem; color: #111; }
.team-name { color: #555; margin: 0.25rem 0; }
.edit-hint { font-size: 0.9rem; color: #6b7280; margin: 0; }

.all-questions {
  max-height: 60vh;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 1rem;
  background: #fafafa;
  margin-bottom: 1.5rem;
}

.edit-question-block {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
  padding: 0.75rem 0;
  border-bottom: 1px solid #eee;
}
.edit-question-block:last-child { border-bottom: none; }

.edit-question-text {
  flex: 1;
  margin: 0;
  font-size: 0.9rem;
  color: #334155;
  line-height: 1.45;
}

.edit-comment {
  width: 100%;
  margin-top: 0.5rem;
}

.edit-comment-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 0.35rem;
}

.edit-comment-input {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  padding: 0.55rem 0.7rem;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-size: 0.875rem;
  line-height: 1.35;
}

.edit-comment-input:disabled {
  background: #f3f4f6;
  color: #6b7280;
}

.edit-yes-no {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.btn-answer {
  padding: 0.35rem 0.75rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  border: 2px solid #e5e7eb;
  background: #fff;
}
.btn-answer.btn-yes.active { background: #d1fae5; border-color: #059669; color: #065f46; }
.btn-answer.btn-no.active { background: #fee2e2; border-color: #dc2626; color: #991b1b; }

.edit-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  align-items: center;
}
.btn-back {
  padding: 0.6rem 1rem;
  background: #f3f4f6;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
}
.btn-back:hover { background: #e5e7eb; }
.btn-save {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
.btn-save:hover:not(:disabled) { background: #1d4ed8; }
.btn-save:disabled { opacity: 0.6; cursor: not-allowed; }
</style>
