<template>
  <div class="testing-types-page">
    <button type="button" class="tt-back" @click="$router.push('/qa')">← К списку практикумов (/qa)</button>
    <header class="tt-header">
      <h1>Задание 3: Типы тестирования</h1>
      <p class="tt-intro">
        Для приложения <strong>Growboard</strong> (разделы <strong>Опрос</strong> и <strong>Дашборд</strong>) опишите <strong>по шагам</strong>, как вы видите процесс каждого типа тестирования. Нейросеть оценит ответ по шкале 1–5. При оценке <strong>4 или 5 баллов</strong> засчитывается успех и появится пример краткого отчёта, который можно получить после такого тестирования. После 5 попыток без четвёрки — эталонный вариант.
      </p>
    </header>

    <div v-if="loading" class="tt-loading">Загрузка...</div>
    <div v-else class="tt-grid">
      <article
        v-for="item in types"
        :key="item.key"
        class="tt-card"
        :class="{ done: getState(item.key).score >= 4 }"
      >
        <div class="tt-card-header">
          <h2 class="tt-type-name">{{ item.name }}</h2>
          <span v-if="getState(item.key).score >= 4" class="tt-badge">✓ {{ getState(item.key).score }}/5</span>
        </div>
        <div class="tt-card-body">
          <div class="tt-input-row">
            <textarea
              v-model="stateByKey[item.key].definition"
              class="tt-textarea"
              rows="3"
              :placeholder="placeholderText"
              :disabled="getState(item.key).score >= 4"
            />
            <div class="tt-actions">
              <button
                type="button"
                class="tt-btn"
                :disabled="!stateByKey[item.key].definition.trim() || getState(item.key).loading || getState(item.key).score >= 4"
                @click="evaluate(item.key)"
              >
                {{ getState(item.key).loading ? '…' : 'Отправить' }}
              </button>
              <span class="tt-attempts">Попыток: {{ getState(item.key).attempts }} / 5</span>
            </div>
          </div>
          <div v-if="getState(item.key).lastScore !== null" class="tt-result">
            <span class="tt-score" :class="scoreClass(getState(item.key).lastScore)">
              Оценка: {{ getState(item.key).lastScore }} / 5
            </span>
            <p v-if="getState(item.key).feedback" class="tt-feedback">{{ getState(item.key).feedback }}</p>
          </div>
          <div v-if="getState(item.key).score >= 4" class="tt-example-report">
            <strong>Пример отчёта после такого тестирования:</strong>
            <p v-if="getState(item.key).reportLoading" class="tt-report-loading">Формируем отчёт…</p>
            <p v-else-if="getState(item.key).exampleReport" class="tt-report-text">{{ getState(item.key).exampleReport }}</p>
          </div>
          <div v-if="getState(item.key).attempts >= 5 && getState(item.key).score < 4" class="tt-suggestion-block">
            <button
              v-if="!getState(item.key).suggestion"
              type="button"
              class="tt-btn secondary"
              @click="fetchSuggestion(item.key)"
            >
              Показать вариант нейросети
            </button>
            <div v-else class="tt-suggestion">
              <strong>Вариант нейросети:</strong>
              <p>{{ getState(item.key).suggestion }}</p>
            </div>
          </div>
        </div>
      </article>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const MAX_ATTEMPTS = 5;

function defaultState() {
  return {
    definition: '',
    attempts: 0,
    lastScore: null,
    feedback: '',
    score: null,
    loading: false,
    suggestion: '',
    exampleReport: '',
    reportLoading: false,
  };
}

export default {
  name: 'TestingTypesAssignment',
  data() {
    return {
      types: [],
      stateByKey: {},
      loading: true,
      placeholderText: 'Опишите по шагам, как вы бы проводили этот тип тестирования для Growboard (Опрос, Дашборд). Например: 1) Открыть раздел Опрос. 2) …',
    };
  },
  async mounted() {
    await this.loadList();
  },
  methods: {
    getState(key) {
      if (!this.stateByKey[key]) this.stateByKey[key] = defaultState();
      return this.stateByKey[key];
    },
    scoreClass(score) {
      if (score >= 5) return 'score-5';
      if (score >= 4) return 'score-4';
      if (score >= 3) return 'score-3';
      return 'score-low';
    },
    async loadList() {
      this.loading = true;
      try {
        const lang = this.$i18n?.locale || 'ru';
        const { data } = await axios.get('/api/testing-types/list', { params: { lang } });
        this.types = data.items || [];
        this.types.forEach((item) => {
          if (!this.stateByKey[item.key]) this.stateByKey[item.key] = defaultState();
        });
      } catch (e) {
        console.error(e);
      } finally {
        this.loading = false;
      }
    },
    async evaluate(typeKey) {
      const state = this.getState(typeKey);
      const text = (state.definition || '').trim();
      if (!text || state.attempts >= MAX_ATTEMPTS || state.score >= 4) return;
      state.loading = true;
      state.feedback = '';
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post(
          '/api/testing-types/evaluate',
          { type_key: typeKey, user_definition: text },
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );
        state.attempts += 1;
        state.lastScore = data.score ?? 3;
        state.feedback = data.feedback || '';
        if (state.lastScore >= 4) {
          state.score = state.lastScore;
          this.fetchExampleReport(typeKey);
        }
      } catch (e) {
        state.feedback = e.response?.data?.error || 'Ошибка запроса';
      } finally {
        state.loading = false;
      }
    },
    async fetchSuggestion(typeKey) {
      const state = this.getState(typeKey);
      if (state.suggestion) return;
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.get(`/api/testing-types/suggest/${typeKey}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        state.suggestion = data.suggestion || '';
      } catch (e) {
        state.suggestion = 'Не удалось загрузить вариант.';
      }
    },
    async fetchExampleReport(typeKey) {
      const state = this.getState(typeKey);
      if (state.exampleReport || state.reportLoading) return;
      state.reportLoading = true;
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post(
          '/api/testing-types/example-report',
          { type_key: typeKey, user_steps: state.definition },
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );
        state.exampleReport = data.report || '';
      } catch (e) {
        state.exampleReport = 'Не удалось сформировать пример отчёта.';
      } finally {
        state.reportLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.testing-types-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px 16px;
}

.tt-back {
  margin-bottom: 16px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #475569;
}

.tt-back:hover {
  background: #e2e8f0;
}

.tt-header {
  margin-bottom: 28px;
}

.tt-header h1 {
  font-size: 1.6rem;
  color: #1e293b;
  margin: 0 0 12px;
}

.tt-intro {
  color: #475569;
  line-height: 1.6;
  margin: 0;
}

.tt-loading {
  text-align: center;
  padding: 40px;
  color: #64748b;
}

.tt-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.tt-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

.tt-card.done {
  border-color: #22c55e;
  background: #f0fdf4;
}

.tt-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}

.tt-type-name {
  font-size: 1.1rem;
  font-weight: 700;
  color: #334155;
  margin: 0;
}

.tt-badge {
  background: #22c55e;
  color: #fff;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.85rem;
}

.tt-card-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tt-input-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.tt-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.95rem;
  font-family: inherit;
  resize: vertical;
  box-sizing: border-box;
}

.tt-textarea:disabled {
  background: #f1f5f9;
  color: #64748b;
}

.tt-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

.tt-btn {
  padding: 8px 18px;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.tt-btn:hover:not(:disabled) {
  background: #1d4ed8;
}

.tt-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tt-btn.secondary {
  background: #64748b;
}

.tt-btn.secondary:hover {
  background: #475569;
}

.tt-attempts {
  font-size: 0.9rem;
  color: #64748b;
}

.tt-result {
  padding: 10px 12px;
  background: #f8fafc;
  border-radius: 8px;
  border-left: 4px solid #94a3b8;
}

.tt-score {
  font-weight: 700;
  display: block;
  margin-bottom: 4px;
}

.tt-score.score-5 { color: #16a34a; }
.tt-score.score-4 { color: #2563eb; }
.tt-score.score-3 { color: #ca8a04; }
.tt-score.score-low { color: #dc2626; }

.tt-feedback {
  margin: 0;
  font-size: 0.9rem;
  color: #475569;
  line-height: 1.4;
}

.tt-suggestion-block {
  margin-top: 8px;
}

.tt-suggestion {
  padding: 12px;
  background: #f1f5f9;
  border-radius: 8px;
  border-left: 4px solid #6366f1;
}

.tt-suggestion strong {
  display: block;
  margin-bottom: 6px;
  color: #334155;
}

.tt-suggestion p {
  margin: 0;
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.5;
}

.tt-example-report {
  margin-top: 12px;
  padding: 12px;
  background: #ecfdf5;
  border-radius: 8px;
  border-left: 4px solid #10b981;
}

.tt-example-report strong {
  display: block;
  margin-bottom: 8px;
  color: #065f46;
}

.tt-report-loading {
  margin: 0;
  color: #047857;
  font-size: 0.9rem;
}

.tt-report-text {
  margin: 0;
  font-size: 0.95rem;
  color: #064e3b;
  line-height: 1.5;
  white-space: pre-line;
}
</style>
