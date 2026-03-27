<template>
  <div class="maturity-admin-dash dash-page">
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
          <button type="button" class="dash-btn" :disabled="!selectedGroup || savingGroupPlan" @click="saveGroupPlan">
            {{ savingGroupPlan ? 'Сохранение…' : 'Сохранить изменения плана' }}
          </button>
          <button type="button" class="dash-btn" :disabled="!selectedGroup || exportingGroupPlan" @click="exportGroupPlanPdf">
            {{ exportingGroupPlan ? 'Экспорт…' : 'Скачать план в PDF' }}
          </button>
          <button type="button" class="dash-btn" @click="showMetricsTree = !showMetricsTree">
            {{ showMetricsTree ? 'Скрыть древо метрик' : 'Показать древо метрик' }}
          </button>
        </div>
        <MetricsTreePanel v-if="showMetricsTree" title="Древо метрик (админ)" class="admin-metrics-tree" />
        <p v-if="groupPlanUpdatedAt" class="muted small">Обновлено: {{ formatDt(groupPlanUpdatedAt) }}</p>
        <div ref="groupPlanExportRoot" class="group-plan-editor" v-if="selectedGroup">
          <h3>План улучшений стрима: {{ selectedGroup }}</h3>
          <label class="plan-label">Диагноз (по данным оценки)</label>
          <textarea v-model="groupPlan.diagnosis" class="plan-input" rows="3" />

          <h4>Инициативы</h4>
          <article v-for="(item, idx) in groupPlan.initiatives" :key="'init-' + idx" class="initiative-card">
            <div class="initiative-head">
              <strong>Инициатива {{ idx + 1 }}</strong>
              <div class="initiative-actions">
                <button type="button" class="dash-btn" @click="toggleInitiativeCollapse(idx)">
                  {{ isInitiativeCollapsed(idx) ? 'Развернуть' : 'Свернуть' }}
                </button>
                <button type="button" class="dash-btn dash-btn-danger" @click="removeInitiative(idx)">Удалить</button>
              </div>
            </div>
            <div v-if="!isInitiativeCollapsed(idx)">
              <label class="plan-label">Название</label>
              <input v-model="item.title" class="plan-input" />
              <label class="plan-label">Цель</label>
              <textarea v-model="item.objective" class="plan-input" rows="2" />
              <label class="plan-label">Владелец / роль</label>
              <input v-model="item.owner" class="plan-input" />
              <label class="plan-label">Метрика успеха</label>
              <input v-model="item.success_metric" class="plan-input" />
              <label class="plan-label">Бизнес-эффект</label>
              <textarea v-model="item.business_impact" class="plan-input" rows="2" />
              <label class="plan-label">Эффект для заказчиков</label>
              <textarea v-model="item.customer_impact" class="plan-input" rows="2" />
            </div>
            <p v-else class="muted small initiative-preview">
              {{ item.title || 'Без названия' }} · {{ item.owner || 'Владелец не указан' }}
            </p>
          </article>
          <button type="button" class="dash-btn" @click="addInitiative">+ Добавить инициативу</button>

          <h4>Roadmap (визуализация по датам)</h4>
          <div class="roadmap-grid">
            <div v-for="(r, idx) in groupPlan.roadmap" :key="'rm-' + idx" class="roadmap-card">
              <div class="initiative-head">
                <strong>{{ r.period || `Этап ${idx + 1}` }}</strong>
                <button type="button" class="dash-btn dash-btn-danger" @click="removeRoadmapItem(idx)">Удалить</button>
              </div>
              <label class="plan-label">Период</label>
              <input v-model="r.period" class="plan-input" placeholder="Недели 1-2" />
              <div class="roadmap-dates">
                <div>
                  <label class="plan-label">Старт</label>
                  <input v-model="r.start_date" type="date" class="plan-input" />
                </div>
                <div>
                  <label class="plan-label">Финиш</label>
                  <input v-model="r.end_date" type="date" class="plan-input" />
                </div>
              </div>
              <label class="plan-label">Инициатива</label>
              <input v-model="r.initiative" class="plan-input" />
              <label class="plan-label">Ключевая веха</label>
              <textarea v-model="r.milestone" class="plan-input" rows="2" />
            </div>
          </div>
          <button type="button" class="dash-btn" @click="addRoadmapItem">+ Добавить этап roadmap</button>

          <h4>Риски и меры снижения</h4>
          <textarea v-model="risksText" class="plan-input" rows="5" placeholder="Каждый риск/мера с новой строки" />
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
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';
import MetricsTreePanel from '@/components/metrics/MetricsTreePanel.vue';
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

function emptyGroupPlan() {
  return {
    diagnosis: '',
    initiatives: [],
    roadmap: [],
    risks: []
  };
}

function normalizeGroupPlan(plan) {
  const src = plan && typeof plan === 'object' ? plan : {};
  return {
    diagnosis: String(src.diagnosis || ''),
    initiatives: Array.isArray(src.initiatives)
      ? src.initiatives.map((i) => ({
        title: String(i?.title || ''),
        objective: String(i?.objective || ''),
        owner: String(i?.owner || ''),
        success_metric: String(i?.success_metric || ''),
        business_impact: String(i?.business_impact || ''),
        customer_impact: String(i?.customer_impact || ''),
        steps: Array.isArray(i?.steps) ? i.steps.map((x) => String(x || '')) : []
      }))
      : [],
    roadmap: Array.isArray(src.roadmap)
      ? src.roadmap.map((r) => ({
        period: String(r?.period || ''),
        start_date: String(r?.start_date || ''),
        end_date: String(r?.end_date || ''),
        initiative: String(r?.initiative || ''),
        milestone: String(r?.milestone || '')
      }))
      : [],
    risks: Array.isArray(src.risks) ? src.risks.map((r) => String(r || '')) : []
  };
}

export default {
  name: 'MaturityLinkAdminDashboard',
  components: { Bar, MetricsTreePanel },
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
      loadingGroupPlan: false,
      savingGroupPlan: false,
      exportingGroupPlan: false,
      showMetricsTree: false,
      groupPlanUpdatedAt: null,
      groupPlan: emptyGroupPlan(),
      risksText: '',
      initiativeCollapsed: {}
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
  watch: {
    selectedGroup() {
      this.groupPlanHtml = '';
      this.groupPlanUpdatedAt = null;
      this.groupPlan = emptyGroupPlan();
      this.risksText = '';
      this.initiativeCollapsed = {};
      if (this.selectedGroup) {
        this.loadGroupPlan();
      }
    }
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
        if (this.selectedGroup) await this.loadGroupPlan();
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
        this.groupPlan = normalizeGroupPlan(res.data.plan);
        this.risksText = (this.groupPlan.risks || []).join('\n');
        this.groupPlanHtml = res.data.content || '';
        this.groupPlanUpdatedAt = res.data.updated_at || null;
        this.initiativeCollapsed = {};
      } catch (e) {
        this.groupPlanHtml = `<p class="err">${e.response?.data?.error || 'Ошибка'}</p>`;
      } finally {
        this.loadingGroupPlan = false;
      }
    },
    async loadGroupPlan() {
      if (!this.selectedGroup) return;
      try {
        const res = await axios.get('/api/maturity-admin/group-plan', {
          headers: authHeaders(),
          params: { group_name: this.selectedGroup }
        });
        this.groupPlan = normalizeGroupPlan(res.data.plan);
        this.risksText = (this.groupPlan.risks || []).join('\n');
        this.groupPlanHtml = res.data.content || '';
        this.groupPlanUpdatedAt = res.data.updated_at || null;
        this.initiativeCollapsed = {};
      } catch {
        this.groupPlan = emptyGroupPlan();
        this.risksText = '';
        this.initiativeCollapsed = {};
      }
    },
    isInitiativeCollapsed(idx) {
      return !!this.initiativeCollapsed[idx];
    },
    toggleInitiativeCollapse(idx) {
      this.initiativeCollapsed = {
        ...this.initiativeCollapsed,
        [idx]: !this.initiativeCollapsed[idx]
      };
    },
    addInitiative() {
      this.groupPlan.initiatives.push({
        title: '',
        objective: '',
        owner: '',
        success_metric: '',
        business_impact: '',
        customer_impact: '',
        steps: []
      });
    },
    removeInitiative(idx) {
      this.groupPlan.initiatives.splice(idx, 1);
      this.initiativeCollapsed = Object.fromEntries(
        Object.entries(this.initiativeCollapsed)
          .filter(([k]) => Number(k) !== idx)
          .map(([k, v]) => [Number(k) > idx ? Number(k) - 1 : Number(k), v])
      );
    },
    addRoadmapItem() {
      this.groupPlan.roadmap.push({
        period: '',
        start_date: '',
        end_date: '',
        initiative: '',
        milestone: ''
      });
    },
    removeRoadmapItem(idx) {
      this.groupPlan.roadmap.splice(idx, 1);
    },
    async saveGroupPlan() {
      if (!this.selectedGroup) return;
      this.savingGroupPlan = true;
      try {
        const plan = normalizeGroupPlan({
          ...this.groupPlan,
          risks: this.risksText.split('\n').map((x) => x.trim()).filter(Boolean)
        });
        const res = await axios.put('/api/maturity-admin/group-plan', {
          group_name: this.selectedGroup,
          plan,
          content: ''
        }, { headers: authHeaders() });
        this.groupPlan = normalizeGroupPlan(res.data.plan);
        this.groupPlanHtml = res.data.content || '';
        this.groupPlanUpdatedAt = res.data.updated_at || null;
        this.risksText = (this.groupPlan.risks || []).join('\n');
      } catch (e) {
        alert(e.response?.data?.error || 'Не удалось сохранить план');
      } finally {
        this.savingGroupPlan = false;
      }
    },
    async exportGroupPlanPdf() {
      if (!this.selectedGroup || this.exportingGroupPlan) return;
      const el = this.$refs.groupPlanExportRoot;
      if (!el) return;
      this.exportingGroupPlan = true;
      try {
        const canvas = await html2canvas(el, { scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' });
        const imgData = canvas.toDataURL('image/png', 0.92);
        const pdf = new jsPDF({ orientation: 'p', unit: 'mm', format: 'a4' });
        const pageW = pdf.internal.pageSize.getWidth();
        const pageH = pdf.internal.pageSize.getHeight();
        const margin = 8;
        const imgW = pageW - margin * 2;
        const imgH = (canvas.height * imgW) / canvas.width;
        let y = margin;
        let left = imgH;
        pdf.addImage(imgData, 'PNG', margin, y, imgW, imgH);
        left -= pageH - margin * 2;
        while (left > 1) {
          y = left - imgH + margin;
          pdf.addPage();
          pdf.addImage(imgData, 'PNG', margin, y, imgW, imgH);
          left -= pageH - margin * 2;
        }
        const safe = this.selectedGroup.replace(/[^\w\s-]/g, '').trim() || 'stream';
        pdf.save(`stream-plan-${safe}.pdf`);
      } finally {
        this.exportingGroupPlan = false;
      }
    }
  }
};
</script>

<style scoped>
.maturity-admin-dash {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.dash-page {
  background: radial-gradient(1200px 420px at 10% -10%, rgba(37, 99, 235, 0.15), transparent 60%),
    radial-gradient(1000px 360px at 95% 0%, rgba(14, 165, 233, 0.12), transparent 60%),
    #f6f9ff;
  border-radius: 20px;
}

.dash-head h1 {
  font-size: 1.7rem;
  margin: 0 0 0.35rem 0;
  color: #0d1733;
  letter-spacing: -0.02em;
}

.dash-sub {
  margin: 0;
  color: #5d6b8a;
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
  padding: 18px;
  border: 1px solid #d8e0f0;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 249, 255, 0.95));
  box-shadow: 0 18px 40px rgba(20, 43, 102, 0.08);
  backdrop-filter: blur(6px);
}

.dash-section h2 {
  font-size: 1.12rem;
  margin: 0 0 0.75rem 0;
  color: #0d1733;
}

.dash-filters {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.dash-select {
  min-width: 200px;
  border: 1px solid #d8e0f0;
  border-radius: 12px;
  padding: 9px 11px;
  background: #f9fbff;
  color: #0d1733;
}

.group-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
}

.group-card {
  border: 1px solid #dbe5f3;
  border-radius: 14px;
  padding: 14px;
  background: linear-gradient(160deg, #ffffff, #f7faff);
  box-shadow: 0 10px 24px rgba(20, 43, 102, 0.08);
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
  max-width: 620px;
  background: #ffffff;
  border: 1px solid #dbe5f3;
  border-radius: 14px;
  padding: 12px;
}

.insights-head {
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}

.insights-html {
  margin-top: 12px;
  padding: 18px;
  background: linear-gradient(165deg, #f8fbff, #ffffff);
  border-radius: 14px;
  border: 1px solid #dbe5f3;
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
  border: 1px solid #dbe5f3;
  border-radius: 14px;
  background: #fff;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.8);
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
  background: #f2f6ff;
  font-weight: 600;
  color: #2b3d63;
}

.group-edit-cell {
  display: flex;
  gap: 6px;
  align-items: center;
}

.group-input {
  min-width: 130px;
  border: 1px solid #d8e0f0;
  border-radius: 10px;
  padding: 7px 9px;
  background: #f9fbff;
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
  border: 1px solid #dbe5f3;
  border-radius: 14px;
  padding: 12px;
  background: linear-gradient(180deg, #ffffff, #f8fbff);
  box-shadow: 0 8px 20px rgba(20, 43, 102, 0.07);
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

.group-plan-editor {
  margin-top: 12px;
  padding: 18px;
  border: 1px solid #d8e0f0;
  border-radius: 16px;
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.98), rgba(243, 248, 255, 0.98));
  box-shadow: 0 18px 36px rgba(20, 43, 102, 0.1);
}

.group-plan-editor h3 {
  margin: 0 0 12px;
  color: #0f172a;
}

.group-plan-editor h4 {
  margin: 16px 0 10px;
  color: #1e293b;
}

.plan-label {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: #475569;
  margin: 8px 0 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.plan-input {
  width: 100%;
  box-sizing: border-box;
  border: 1px solid #d8e0f0;
  border-radius: 12px;
  padding: 9px 10px;
  font-size: 14px;
  font-family: inherit;
  background: #f9fbff;
}

.initiative-card {
  margin: 12px 0;
  padding: 14px;
  border: 1px solid #dbe5f3;
  border-radius: 14px;
  background: linear-gradient(160deg, #ffffff, #f7fbff);
  box-shadow: 0 12px 28px rgba(20, 43, 102, 0.08);
}

.initiative-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.initiative-actions {
  display: flex;
  gap: 8px;
}

.initiative-preview {
  margin-top: 10px;
}

.roadmap-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 12px;
}

.roadmap-card {
  border: 1px solid #bfd3ff;
  border-radius: 16px;
  padding: 12px;
  background: linear-gradient(155deg, #edf4ff 0%, #ffffff 100%);
  box-shadow: 0 12px 28px rgba(59, 130, 246, 0.16);
}

.roadmap-dates {
  display: grid;
  grid-template-columns: 1fr;
  gap: 8px;
}

.dash-btn {
  border: 1px solid rgba(20, 43, 102, 0.18);
  border-radius: 12px;
  background: linear-gradient(145deg, #142b66, #2754c7);
  color: #fff;
  font-weight: 700;
  padding: 0.58rem 0.95rem;
  box-shadow: 0 10px 22px rgba(20, 43, 102, 0.22);
}

.dash-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.dash-btn-danger {
  background: linear-gradient(145deg, #ef4444, #dc2626);
  border-color: rgba(220, 38, 38, 0.35);
}

.admin-metrics-tree {
  margin-top: 12px;
}
</style>
