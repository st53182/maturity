<template>
  <div class="maturity-admin-dash">
    <header class="dash-head">
      <h1>Оценка зрелости по ссылке — сводка</h1>
      <p class="dash-sub">Завершённых опросов (с валидными ответами): {{ aggregates.completed_sessions ?? '—' }}</p>
    </header>

    <div v-if="error" class="dash-error">{{ error }}</div>
    <div v-if="loading" class="dash-loading">Загрузка…</div>

    <template v-else>
      <section class="dash-section">
        <div class="dash-filters">
          <label for="group-filter">Группа команд:</label>
          <select id="group-filter" v-model="selectedGroup" class="dash-select" @change="refresh">
            <option value="">Все группы</option>
            <option v-for="g in groups" :key="g" :value="g">{{ g }}</option>
          </select>
          <button type="button" class="dash-btn" :disabled="!selectedGroup || loadingGroupPlan" @click="generateGroupPlan">
            {{ loadingGroupPlan ? 'Генерация…' : 'Сгенерировать план для группы' }}
          </button>
        </div>
        <div v-if="groupPlanHtml" class="insights-html group-plan-html" v-html="groupPlanHtml"></div>
      </section>

      <section class="dash-section">
        <h2>Сводка по группам команд</h2>
        <div class="group-cards">
          <article v-for="g in groupSummaries" :key="g.group_name" class="group-card">
            <h3>{{ g.group_name }}</h3>
            <p>Сессий: <strong>{{ g.sessions }}</strong></p>
            <p>Да: {{ g.yes }} · Нет: {{ g.no }} · Не знаю: {{ g.dont_know }}</p>
          </article>
        </div>
      </section>

      <section class="dash-section">
        <h2>Распределение ответов (все вопросы)</h2>
        <div v-if="totalsChartData" class="chart-box">
          <Bar :data="totalsChartData" :options="totalsChartOptions" />
        </div>
      </section>

      <section class="dash-section">
        <div class="insights-head">
          <h2>ИИ: типичные слабые места</h2>
          <button type="button" class="dash-btn" :disabled="loadingInsights" @click="loadInsights">
            {{ loadingInsights ? '…' : 'Обновить текст' }}
          </button>
        </div>
        <div v-if="insightsHtml" class="insights-html" v-html="insightsHtml"></div>
        <p v-else class="muted">Нажмите «Обновить текст» (нужен OPENAI_API_KEY на сервере).</p>
      </section>

      <section class="dash-section">
        <h2>Сессии</h2>
        <div class="table-wrap">
          <table class="dash-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Команда</th>
                <th>Группа</th>
                <th>Токен (хвост)</th>
                <th>Отчёт</th>
                <th>Создана</th>
                <th>Завершена</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in sessions" :key="s.id">
                <td>{{ s.id }}</td>
                <td>{{ s.team_name || '—' }}</td>
                <td>
                  <div class="group-edit-cell">
                    <input
                      v-model="groupDrafts[s.id]"
                      type="text"
                      class="group-input"
                      placeholder="Без группы"
                    />
                    <button type="button" class="dash-btn" @click="saveSessionGroup(s.id)">Сохранить</button>
                  </div>
                </td>
                <td class="mono">…{{ s.token_suffix }}</td>
                <td>
                  <router-link
                    v-if="s.completed && s.token"
                    class="report-link"
                    :to="`/new/maturity/${s.token}/results`"
                  >
                    Открыть
                  </router-link>
                  <span v-else class="muted">—</span>
                </td>
                <td>{{ formatDt(s.created_at) }}</td>
                <td>{{ s.completed ? formatDt(s.completed_at) : '—' }}</td>
                <td>
                  <button
                    type="button"
                    class="dash-btn dash-btn-danger"
                    :disabled="deletingId === s.id"
                    @click="removeSession(s)"
                  >
                    {{ deletingId === s.id ? '…' : 'Удалить' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="dash-section">
        <h2>Доли ответов по всем вопросам</h2>
        <p class="muted small">
          Для каждого вопроса — доли «да» / «нет» / «не знаю» среди завершённых сессий. Блок ниже прокручивается.
        </p>
        <div class="q-grid-scroll">
          <div class="q-grid">
            <div v-for="q in aggregateQuestions" :key="q.index" class="q-card">
              <div class="q-meta">
                <span class="q-idx">#{{ q.index + 1 }}</span>
                <span class="q-theme">{{ q.theme }}</span>
              </div>
              <p class="q-text">{{ q.short_text }}</p>
              <div v-if="miniChartData(q)" class="mini-chart">
                <Bar :data="miniChartData(q)" :options="miniChartOptions" />
              </div>
            </div>
        </div>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import axios from 'axios';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar } from 'vue-chartjs';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

function authHeaders() {
  const t = localStorage.getItem('token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}

export default {
  name: 'MaturityLinkAdminDashboard',
  components: { Bar },
  data() {
    return {
      loading: true,
      error: null,
      sessions: [],
      aggregates: {},
      groups: [],
      selectedGroup: '',
      groupDrafts: {},
      deletingId: null,
      insightsHtml: '',
      loadingInsights: false,
      groupPlanHtml: '',
      loadingGroupPlan: false
    };
  },
  computed: {
    aggregateQuestions() {
      const qs = this.aggregates.questions;
      if (!Array.isArray(qs)) return [];
      return qs;
    },
    groupSummaries() {
      const rows = this.aggregates.group_summaries;
      return Array.isArray(rows) ? rows : [];
    },
    totalsChartData() {
      const qs = this.aggregates.questions;
      if (!Array.isArray(qs) || !qs.length) return null;
      let y = 0;
      let n = 0;
      let d = 0;
      for (const q of qs) {
        const c = q.counts || {};
        y += c.yes || 0;
        n += c.no || 0;
        d += c.dont_know || 0;
      }
      return {
        labels: ['Все ответы'],
        datasets: [
          { label: 'Да', data: [y], backgroundColor: '#10b981' },
          { label: 'Нет', data: [n], backgroundColor: '#ef4444' },
          { label: 'Не знаю', data: [d], backgroundColor: '#94a3b8' }
        ]
      };
    },
    totalsChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'bottom' },
          title: { display: false }
        },
        scales: {
          x: { stacked: true },
          y: { stacked: true, beginAtZero: true }
        }
      };
    },
    miniChartOptions() {
      return {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
          legend: { display: false },
          title: { display: false }
        },
        scales: {
          x: { stacked: true, max: 100, ticks: { callback: (v) => `${v}%` } },
          y: { stacked: true, display: false }
        }
      };
    }
  },
  mounted() {
    this.refresh();
  },
  methods: {
    miniChartData(q) {
      return {
        labels: [''],
        datasets: [
          { label: 'Да', data: [q.yes_pct], backgroundColor: '#10b981' },
          { label: 'Нет', data: [q.no_pct], backgroundColor: '#ef4444' },
          { label: 'Не знаю', data: [q.dont_know_pct], backgroundColor: '#94a3b8' }
        ]
      };
    },
    formatDt(iso) {
      if (!iso) return '—';
      try {
        return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' });
      } catch {
        return iso;
      }
    },
    async refresh() {
      this.loading = true;
      this.error = null;
      try {
        const params = this.selectedGroup ? { group_name: this.selectedGroup } : undefined;
        const [ov, ag] = await Promise.all([
          axios.get('/api/maturity-admin/overview', { headers: authHeaders(), params }),
          axios.get('/api/maturity-admin/aggregates', { headers: authHeaders(), params })
        ]);
        this.sessions = ov.data.sessions || [];
        this.groups = ov.data.groups || [];
        this.aggregates = ag.data || {};
        this.groupDrafts = Object.fromEntries(this.sessions.map((s) => [s.id, s.group_name || '']));
      } catch (e) {
        const st = e.response?.status;
        if (st === 403) {
          this.error =
            'Нет доступа: аккаунт не в списке администраторов. На сервере задайте MATURITY_LINK_ADMIN_EMAILS и добавьте email входа (через запятую), затем перезапустите приложение.';
        } else {
          this.error = e.response?.data?.error || e.message || 'Ошибка загрузки';
        }
      } finally {
        this.loading = false;
      }
    },
    async loadInsights() {
      this.loadingInsights = true;
      this.insightsHtml = '';
      try {
        const params = this.selectedGroup ? { group_name: this.selectedGroup } : undefined;
        const res = await axios.get('/api/maturity-admin/insights', { headers: authHeaders(), params });
        this.insightsHtml = res.data.content || '';
      } catch (e) {
        this.insightsHtml = `<p class="err">${e.response?.data?.error || 'Ошибка'}</p>`;
      } finally {
        this.loadingInsights = false;
      }
    },
    async removeSession(s) {
      if (!window.confirm(`Удалить сессию ${s.id} (${s.team_name || 'без имени'})?`)) return;
      this.deletingId = s.id;
      try {
        await axios.delete(`/api/maturity-admin/session/${s.id}`, { headers: authHeaders() });
        this.sessions = this.sessions.filter((x) => x.id !== s.id);
        await this.refreshAggregatesOnly();
      } catch (e) {
        alert(e.response?.data?.error || 'Не удалось удалить');
      } finally {
        this.deletingId = null;
      }
    },
    async refreshAggregatesOnly() {
      try {
        const params = this.selectedGroup ? { group_name: this.selectedGroup } : undefined;
        const ag = await axios.get('/api/maturity-admin/aggregates', { headers: authHeaders(), params });
        this.aggregates = ag.data || {};
      } catch {
        /* ignore */
      }
    },
    async saveSessionGroup(sessionId) {
      try {
        await axios.put(
          `/api/maturity-admin/session/${sessionId}/group`,
          { group_name: this.groupDrafts[sessionId] || null },
          { headers: authHeaders() }
        );
        await this.refresh();
      } catch (e) {
        alert(e.response?.data?.error || 'Не удалось сохранить группу');
      }
    },
    async generateGroupPlan() {
      if (!this.selectedGroup) return;
      this.loadingGroupPlan = true;
      this.groupPlanHtml = '';
      try {
        const res = await axios.post(
          '/api/maturity-admin/group-plan',
          { group_name: this.selectedGroup },
          { headers: authHeaders() }
        );
        this.groupPlanHtml = res.data.content || '';
      } catch (e) {
        this.groupPlanHtml = `<p class="err">${e.response?.data?.error || 'Ошибка'}</p>`;
      } finally {
        this.loadingGroupPlan = false;
      }
    }
  }
};
</script>

<style scoped>
.maturity-admin-dash {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.dash-head h1 {
  font-size: 1.5rem;
  margin: 0 0 0.35rem 0;
  color: #0f172a;
}

.dash-sub {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

.dash-error {
  margin-top: 1rem;
  padding: 12px;
  background: #fef2f2;
  color: #991b1b;
  border-radius: 10px;
}

.dash-loading {
  margin-top: 2rem;
  text-align: center;
  color: #64748b;
}

.dash-section {
  margin-top: 2rem;
}

.dash-section h2 {
  font-size: 1.1rem;
  margin: 0 0 0.75rem 0;
  color: #1e293b;
}

.dash-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.dash-select {
  min-width: 200px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 8px 10px;
}

.group-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.group-card {
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px;
  background: #fff;
}

.group-card h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
}

.group-card p {
  margin: 4px 0;
  font-size: 0.85rem;
  color: #334155;
}

.chart-box {
  height: 280px;
  max-width: 520px;
}

.insights-head {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.insights-html {
  margin-top: 12px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  font-size: 0.95rem;
  line-height: 1.5;
}

.muted {
  color: #64748b;
}

.muted.small {
  font-size: 0.85rem;
}

.table-wrap {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
}

.dash-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.dash-table th,
.dash-table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

.dash-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}

.group-edit-cell {
  display: flex;
  gap: 6px;
  align-items: center;
}

.group-input {
  min-width: 130px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 6px 8px;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 0.8rem;
}

.q-grid-scroll {
  max-height: min(70vh, 1400px);
  overflow-y: auto;
  padding-right: 6px;
  -webkit-overflow-scrolling: touch;
}

.q-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.q-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 12px;
  background: #fff;
}

.q-meta {
  display: flex;
  gap: 8px;
  align-items: baseline;
  margin-bottom: 6px;
}

.q-idx {
  font-weight: 700;
  color: #0f172a;
}

.q-theme {
  font-size: 0.75rem;
  color: #64748b;
}

.q-text {
  font-size: 0.8rem;
  color: #334155;
  margin: 0 0 8px 0;
  line-height: 1.35;
}

.mini-chart {
  height: 72px;
}

.report-link {
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
  font-size: 0.85rem;
}

.report-link:hover {
  text-decoration: underline;
}

.group-plan-html {
  margin-top: 12px;
}
</style>
