<template>
  <div class="edit-maturity" :class="{ 'edit-maturity--new': variant === 'new' }">
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
              :class="['btn-answer', 'btn-no', { active: answers[q.id] === 'no' }]"
              @click="setAnswer(q.id, 'no')"
            >
              {{ $t('maturity.no') }}
            </button>
            <button
              type="button"
              :class="['btn-answer', 'btn-rather-no', { active: answers[q.id] === 'rather_no' }]"
              @click="setAnswer(q.id, 'rather_no')"
            >
              {{ $t('maturity.ratherNo') }}
            </button>
            <button
              type="button"
              :class="['btn-answer', 'btn-dont-know', { active: answers[q.id] === 'dont_know' }]"
              @click="setAnswer(q.id, 'dont_know')"
            >
              {{ $t('maturity.dontKnow') }}
            </button>
            <button
              type="button"
              :class="['btn-answer', 'btn-rather-yes', { active: answers[q.id] === 'rather_yes' }]"
              @click="setAnswer(q.id, 'rather_yes')"
            >
              {{ $t('maturity.ratherYes') }}
            </button>
            <button
              type="button"
              :class="['btn-answer', 'btn-yes', { active: answers[q.id] === 'yes' }]"
              @click="setAnswer(q.id, 'yes')"
            >
              {{ $t('maturity.yes') }}
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
        <button type="button" class="btn-back" @click="$router.push(`${maturityBase}/results`)">
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
  props: {
    variant: { type: String, default: 'legacy' },
  },
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
  computed: {
    maturityBase() {
      return this.variant === 'new' ? `/new/maturity/${this.token}` : `/maturity/${this.token}`;
    }
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
        const allowed = new Set(['no', 'rather_no', 'dont_know', 'rather_yes', 'yes']);
        this.questions.forEach(q => {
          const raw = ansList[q.id];
          if (raw === true) this.answers[q.id] = 'yes';
          else if (raw === false) this.answers[q.id] = 'no';
          else if (allowed.has(raw)) this.answers[q.id] = raw;
          else this.answers[q.id] = 'no';
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
      const allowed = new Set(['no', 'rather_no', 'dont_know', 'rather_yes', 'yes']);
      const arr = this.questions.map(q => {
        const a = this.answers[q.id];
        return allowed.has(a) ? a : 'no';
      });
      const commentsArr = this.questions.map(q => {
        const s = (this.comments[q.id] || '').toString().trim();
        return s ? s : null;
      });
      this.saving = true;
      try {
        await axios.put(`/api/maturity/${this.token}/answers`, { answers: arr, comments: commentsArr });
        this.$router.push(`${this.maturityBase}/results`);
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
  flex-direction: column;
  align-items: stretch;
  gap: 0.65rem;
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
  flex-wrap: wrap;
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
.btn-answer.btn-rather-no.active { background: #ffedd5; border-color: #ea580c; color: #9a3412; }
.btn-answer.btn-rather-yes.active { background: #ecfccb; border-color: #65a30d; color: #3f6212; }
.btn-answer.btn-dont-know.active { background: #e2e8f0; border-color: #64748b; color: #334155; }

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

/* —— New UI —— */
.edit-maturity.edit-maturity--new {
  max-width: 820px;
  padding: 20px 16px 40px;
  background: linear-gradient(180deg, rgba(247, 249, 255, 0.95) 0%, rgba(255, 255, 255, 0.5) 45%);
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.06);
  box-shadow: 0 20px 60px rgba(10, 20, 45, 0.08);
}

.edit-maturity--new .edit-question-block {
  border-radius: 14px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 10px 32px rgba(10, 20, 45, 0.05);
}

.edit-maturity--new .btn-save {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
  border-radius: 12px;
  box-shadow: 0 10px 28px rgba(32, 90, 255, 0.22);
}

.edit-maturity--new .btn-save:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.edit-maturity--new .btn-back {
  border-radius: 12px;
}

.edit-maturity--new .all-questions {
  border-radius: 16px;
  border: 1px solid rgba(10, 20, 45, 0.09);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.92), rgba(247, 250, 255, 0.9));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.45);
}

.edit-maturity--new .edit-question-block {
  margin-bottom: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.86);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.edit-maturity--new .edit-question-block:hover {
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.22);
  box-shadow: 0 16px 36px rgba(10, 20, 45, 0.1);
}

.edit-maturity--new .btn-answer {
  border-radius: 11px;
  border-color: rgba(10, 20, 45, 0.16);
  transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
}

.edit-maturity--new .btn-answer:hover {
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.42);
  box-shadow: 0 8px 20px rgba(32, 90, 255, 0.12);
}

.edit-maturity--new .btn-answer.btn-yes.active {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.95), rgba(16, 185, 129, 0.84));
  border-color: rgba(34, 197, 94, 0.58);
  color: #fff;
}

.edit-maturity--new .btn-answer.btn-no.active {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(244, 63, 94, 0.86));
  border-color: rgba(239, 68, 68, 0.58);
  color: #fff;
}

.edit-maturity--new .btn-answer.btn-dont-know.active {
  background: linear-gradient(135deg, rgba(100, 116, 139, 0.95), rgba(71, 85, 105, 0.86));
  border-color: rgba(100, 116, 139, 0.58);
  color: #fff;
}

.edit-maturity--new .btn-answer.btn-rather-no.active {
  background: linear-gradient(135deg, rgba(234, 88, 12, 0.95), rgba(249, 115, 22, 0.86));
  border-color: rgba(234, 88, 12, 0.58);
  color: #fff;
}

.edit-maturity--new .btn-answer.btn-rather-yes.active {
  background: linear-gradient(135deg, rgba(101, 163, 13, 0.95), rgba(132, 204, 22, 0.86));
  border-color: rgba(101, 163, 13, 0.58);
  color: #fff;
}

.edit-maturity--new .edit-comment-input {
  border-color: rgba(10, 20, 45, 0.14);
  background: rgba(248, 250, 255, 0.94);
}

.edit-maturity--new .edit-comment-input:focus {
  outline: none;
  border-color: rgba(32, 90, 255, 0.58);
  box-shadow: 0 0 0 5px rgba(32, 90, 255, 0.12);
}

.edit-maturity--new .btn-save,
.edit-maturity--new .btn-back {
  position: relative;
  overflow: hidden;
}

.edit-maturity--new .btn-save::after,
.edit-maturity--new .btn-back::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 24%, rgba(255, 255, 255, 0.32), transparent 76%);
  transform: translateX(-125%);
  transition: transform 0.6s ease;
}

.edit-maturity--new .btn-save:hover::after,
.edit-maturity--new .btn-back:hover::after {
  transform: translateX(125%);
}
</style>
