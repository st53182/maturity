<template>
  <div class="usability-report-page">
    <button type="button" class="ur-back" @click="$router.push('/qa')">← К списку практикумов (/qa)</button>
    <header class="ur-header">
      <h1>📋 Отчёт по юзабилити-тестированию</h1>
      <p class="ur-intro">Заполните шаблон отчёта. Подсказки — под полями. По каждому разделу можно запросить помощь нейросети.</p>
      <div class="ur-actions">
        <button type="button" class="ur-btn primary" :disabled="exporting" @click="exportPdf">
          {{ exporting ? 'Формируем PDF…' : '📄 Скачать PDF' }}
        </button>
      </div>
    </header>

    <div ref="pdfContent" class="ur-report-block">
      <!-- SECTION 1 -->
      <section class="ur-section">
        <h2>Раздел 1 — Метаданные отчёта</h2>
        <p class="ur-hint">Уникальный идентификатор, название проекта и продукта, версия, среда и дата теста.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'metadata'" @click="askAi('metadata', getSection1Context())">
          {{ aiLoading === 'metadata' ? '…' : '🤖 Помощь нейросети' }}
        </button>
        <div v-if="aiSuggestion.section === 'metadata'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field"><label>Report ID</label><input v-model="form.reportId" type="text" placeholder="Например: UTR-2024-001"></div>
          <div class="ur-field"><label>Название проекта</label><input v-model="form.projectName" type="text" placeholder="Проект"></div>
          <div class="ur-field"><label>Продукт / система</label><input v-model="form.productSystem" type="text" placeholder="Веб-приложение, мобильное приложение"></div>
          <div class="ur-field"><label>Функция / модуль</label><input v-model="form.featureModule" type="text" placeholder="Какой модуль тестировали"></div>
          <div class="ur-field"><label>Версия / сборка</label><input v-model="form.productVersion" type="text" placeholder="1.2.0"></div>
          <div class="ur-field"><label>Среда</label><select v-model="form.environment"><option value="">—</option><option value="Web">Web</option><option value="iOS">iOS</option><option value="Android">Android</option><option value="Desktop">Desktop</option></select></div>
          <div class="ur-field"><label>Браузер / устройство</label><input v-model="form.browserDevice" type="text" placeholder="Chrome 120, iPhone 14"></div>
          <div class="ur-field"><label>Место теста</label><select v-model="form.testLocation"><option value="">—</option><option value="Lab">Лаборатория</option><option value="Remote">Удалённо</option><option value="Unmoderated">Немодерируемый</option><option value="Moderated">Модерируемый</option></select></div>
          <div class="ur-field"><label>Дата теста</label><input v-model="form.dateOfTest" type="text" placeholder="ДД.ММ.ГГГГ"></div>
          <div class="ur-field"><label>QA / UX-исследователь</label><input v-model="form.qaResearcher" type="text" placeholder="ФИО или роль"></div>
          <div class="ur-field"><label>Стейкхолдеры</label><input v-model="form.stakeholders" type="text" placeholder="Кто заинтересован в результатах"></div>
        </div>
      </section>

      <!-- SECTION 2 -->
      <section class="ur-section">
        <h2>Раздел 2 — Цели тестирования</h2>
        <p class="ur-hint">Главная и второстепенные цели; критерии успеха.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'objectives'" @click="askAi('objectives', getSection2Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'objectives'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field full"><label>Primary Objective</label><textarea v-model="form.primaryObjective" rows="2" placeholder="Какой аспект юзабилити оцениваем"></textarea></div>
          <div class="ur-field full"><label>Второстепенные цели</label><textarea v-model="form.secondaryObjectives" rows="3" placeholder="По одному на строку или списком"></textarea></div>
          <div class="ur-field full"><label>Критерии успеха</label><textarea v-model="form.successCriteria" rows="2" placeholder="Что считается успешным взаимодействием"></textarea></div>
        </div>
      </section>

      <!-- SECTION 3 -->
      <section class="ur-section">
        <h2>Раздел 3 — Участники теста</h2>
        <p class="ur-hint">Количество участников, профиль, таблица (ID, роль, опыт, заметки).</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'participants'" @click="askAi('participants', getSection3Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'participants'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field"><label>Количество участников</label><input v-model="form.numParticipants" type="text" placeholder="5"></div>
          <div class="ur-field full"><label>Профиль участников</label><textarea v-model="form.participantProfile" rows="2" placeholder="Целевая аудитория, опыт"></textarea></div>
          <div class="ur-table-wrap">
            <table class="ur-table">
              <thead><tr><th>Participant ID</th><th>Роль / персона</th><th>Уровень опыта</th><th>Заметки</th></tr></thead>
              <tbody>
                <tr v-for="(row, i) in form.participantsTable" :key="i">
                  <td><input v-model="row.id" type="text" placeholder="P1"></td>
                  <td><input v-model="row.role" type="text"></td>
                  <td><input v-model="row.experience" type="text"></td>
                  <td><input v-model="row.notes" type="text"></td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <!-- SECTION 4 -->
      <section class="ur-section">
        <h2>Раздел 4 — Сценарий тестирования</h2>
        <p class="ur-hint">ID и название сценария, описание цели, предусловия, шаги задачи, ожидаемый результат.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'scenarios'" @click="askAi('scenarios', getSection4Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'scenarios'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field"><label>Scenario ID</label><input v-model="form.scenarioId" type="text" placeholder="S1"></div>
          <div class="ur-field"><label>Название сценария</label><input v-model="form.scenarioName" type="text"></div>
          <div class="ur-field full"><label>Описание</label><textarea v-model="form.scenarioDescription" rows="2" placeholder="Цель пользователя или реальная задача"></textarea></div>
          <div class="ur-field full"><label>Предусловия</label><textarea v-model="form.preconditions" rows="2" placeholder="Состояние до начала теста"></textarea></div>
          <div class="ur-field full"><label>Шаги задачи для пользователя</label><textarea v-model="form.taskSteps" rows="4" placeholder="1. ...&#10;2. ...&#10;3. ..."></textarea></div>
          <div class="ur-field full"><label>Ожидаемый результат</label><textarea v-model="form.expectedOutcome" rows="2" placeholder="Как выглядит успешное выполнение"></textarea></div>
        </div>
      </section>

      <!-- SECTION 5 -->
      <section class="ur-section">
        <h2>Раздел 5 — Результаты выполнения задач</h2>
        <p class="ur-hint">Таблица по участникам: выполнено да/нет, время, ошибки, помощь, заметки; среднее время, % успеха, наблюдения.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'performance'" @click="askAi('performance', getSection5Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'performance'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-table-wrap">
            <table class="ur-table">
              <thead><tr><th>Participant ID</th><th>Выполнено (Да/Нет)</th><th>Время (сек)</th><th>Ошибки</th><th>Помощь</th><th>Заметки</th></tr></thead>
              <tbody>
                <tr v-for="(row, i) in form.performanceTable" :key="i">
                  <td><input v-model="row.participantId" type="text" placeholder="P1"></td>
                  <td><input v-model="row.completed" type="text" placeholder="Да/Нет"></td>
                  <td><input v-model="row.time" type="text" placeholder="сек"></td>
                  <td><input v-model="row.errors" type="text"></td>
                  <td><input v-model="row.assistance" type="text"></td>
                  <td><input v-model="row.notes" type="text"></td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="ur-field"><label>Среднее время выполнения</label><input v-model="form.avgCompletionTime" type="text" placeholder="сек"></div>
          <div class="ur-field"><label>Успешность задачи (%)</label><input v-model="form.taskSuccessRate" type="text" placeholder="80"></div>
          <div class="ur-field full"><label>Наблюдаемое поведение</label><textarea v-model="form.observedBehavior" rows="3"></textarea></div>
        </div>
      </section>

      <!-- SECTION 6 -->
      <section class="ur-section">
        <h2>Раздел 6 — Юзабилити-проблемы</h2>
        <p class="ur-hint">Issue ID, название, описание, сценарий, шаги воспроизведения, влияние, частота, severity 1–5, рекомендация.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'issues'" @click="askAi('issues', getSection6Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'issues'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field"><label>Issue ID</label><input v-model="form.issueId" type="text" placeholder="U1"></div>
          <div class="ur-field full"><label>Название проблемы</label><input v-model="form.issueTitle" type="text"></div>
          <div class="ur-field full"><label>Описание</label><textarea v-model="form.issueDescription" rows="2"></textarea></div>
          <div class="ur-field full"><label>Затронутый сценарий / задача</label><input v-model="form.issueScenario" type="text"></div>
          <div class="ur-field full"><label>Шаги воспроизведения</label><textarea v-model="form.issueSteps" rows="3" placeholder="1. ...&#10;2. ..."></textarea></div>
          <div class="ur-field"><label>Наблюдаемое поведение</label><input v-model="form.issueObserved" type="text"></div>
          <div class="ur-field"><label>Ожидаемое поведение</label><input v-model="form.issueExpected" type="text"></div>
          <div class="ur-field"><label>Влияние на UX</label><select v-model="form.issueImpact"><option value="">—</option><option value="Low">Low</option><option value="Medium">Medium</option><option value="High">High</option><option value="Critical">Critical</option></select></div>
          <div class="ur-field"><label>Частота (сколько участников)</label><input v-model="form.issueFrequency" type="text"></div>
          <div class="ur-field"><label>Severity (1–5)</label><input v-model="form.issueSeverity" type="text" placeholder="1–5"></div>
          <div class="ur-field full"><label>Скриншот / доказательство</label><input v-model="form.issueScreenshot" type="text" placeholder="Ссылка или описание"></div>
          <div class="ur-field full"><label>Рекомендация</label><textarea v-model="form.issueRecommendation" rows="2"></textarea></div>
        </div>
      </section>

      <!-- SECTION 7 -->
      <section class="ur-section">
        <h2>Раздел 7 — Обратная связь пользователей</h2>
        <p class="ur-hint">Ключевые цитаты, боли, положительные наблюдения.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'feedback'" @click="askAi('feedback', getSection7Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'feedback'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field full"><label>Ключевые цитаты участников</label><textarea v-model="form.keyQuotes" rows="3" placeholder="По одной на строку"></textarea></div>
          <div class="ur-field full"><label>Выявленные боли</label><textarea v-model="form.painPoints" rows="3" placeholder="По одному на строку"></textarea></div>
          <div class="ur-field full"><label>Положительные наблюдения</label><textarea v-model="form.positiveObservations" rows="3" placeholder="По одному на строку"></textarea></div>
        </div>
      </section>

      <!-- SECTION 8 -->
      <section class="ur-section">
        <h2>Раздел 8 — Метрики юзабилити</h2>
        <p class="ur-hint">Task Success Rate %, среднее время, Error rate, удовлетворённость 1–5, SUS (если использовался).</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'metrics'" @click="askAi('metrics', getSection8Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'metrics'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields ur-metrics-grid">
          <div class="ur-field"><label>Task Success Rate (%)</label><input v-model="form.metricsTaskSuccessRate" type="text"></div>
          <div class="ur-field"><label>Среднее время задачи</label><input v-model="form.metricsAvgTime" type="text" placeholder="сек"></div>
          <div class="ur-field"><label>Error Rate</label><input v-model="form.metricsErrorRate" type="text"></div>
          <div class="ur-field"><label>Удовлетворённость (1–5)</label><input v-model="form.metricsSatisfaction" type="text"></div>
          <div class="ur-field"><label>SUS Score (если использовался)</label><input v-model="form.metricsSus" type="text"></div>
        </div>
      </section>

      <!-- SECTION 9 -->
      <section class="ur-section">
        <h2>Раздел 9 — Итог</h2>
        <p class="ur-hint">Основные риски, общая оценка UX, рекомендации команде (1–2–3).</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'summary'" @click="askAi('summary', getSection9Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'summary'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field full"><label>Основные риски юзабилити</label><textarea v-model="form.majorRisks" rows="3" placeholder="По одному на строку"></textarea></div>
          <div class="ur-field full"><label>Общая оценка UX</label><textarea v-model="form.overallAssessment" rows="3"></textarea></div>
          <div class="ur-field full"><label>Рекомендации для команды</label><textarea v-model="form.recommendations" rows="4" placeholder="1. ...&#10;2. ...&#10;3. ..."></textarea></div>
        </div>
      </section>

      <!-- SECTION 10 -->
      <section class="ur-section">
        <h2>Раздел 10 — Вложения</h2>
        <p class="ur-hint">Скриншоты, записи сессий, тепловые карты, дополнительные заметки.</p>
        <button type="button" class="ur-ai-btn" :disabled="aiLoading === 'attachments'" @click="askAi('attachments', getSection10Context())">🤖 Помощь нейросети</button>
        <div v-if="aiSuggestion.section === 'attachments'" class="ur-ai-suggestion">{{ aiSuggestion.text }}</div>
        <div class="ur-fields">
          <div class="ur-field full"><label>Скриншоты / записи / тепловые карты / заметки</label><textarea v-model="form.attachmentsNotes" rows="4" placeholder="Перечислите или опишите вложения"></textarea></div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

const STORAGE_KEY = 'usability_report_draft';

function defaultForm() {
  return {
    reportId: '',
    projectName: '',
    productSystem: '',
    featureModule: '',
    productVersion: '',
    environment: '',
    browserDevice: '',
    testLocation: '',
    dateOfTest: '',
    qaResearcher: '',
    stakeholders: '',
    primaryObjective: '',
    secondaryObjectives: '',
    successCriteria: '',
    numParticipants: '',
    participantProfile: '',
    participantsTable: [
      { id: 'P1', role: '', experience: '', notes: '' },
      { id: 'P2', role: '', experience: '', notes: '' },
      { id: 'P3', role: '', experience: '', notes: '' },
      { id: 'P4', role: '', experience: '', notes: '' },
      { id: 'P5', role: '', experience: '', notes: '' },
    ],
    scenarioId: '',
    scenarioName: '',
    scenarioDescription: '',
    preconditions: '',
    taskSteps: '',
    expectedOutcome: '',
    performanceTable: [
      { participantId: 'P1', completed: '', time: '', errors: '', assistance: '', notes: '' },
      { participantId: 'P2', completed: '', time: '', errors: '', assistance: '', notes: '' },
      { participantId: 'P3', completed: '', time: '', errors: '', assistance: '', notes: '' },
      { participantId: 'P4', completed: '', time: '', errors: '', assistance: '', notes: '' },
      { participantId: 'P5', completed: '', time: '', errors: '', assistance: '', notes: '' },
    ],
    avgCompletionTime: '',
    taskSuccessRate: '',
    observedBehavior: '',
    issueId: '',
    issueTitle: '',
    issueDescription: '',
    issueScenario: '',
    issueSteps: '',
    issueObserved: '',
    issueExpected: '',
    issueImpact: '',
    issueFrequency: '',
    issueSeverity: '',
    issueScreenshot: '',
    issueRecommendation: '',
    keyQuotes: '',
    painPoints: '',
    positiveObservations: '',
    metricsTaskSuccessRate: '',
    metricsAvgTime: '',
    metricsErrorRate: '',
    metricsSatisfaction: '',
    metricsSus: '',
    majorRisks: '',
    overallAssessment: '',
    recommendations: '',
    attachmentsNotes: '',
  };
}

function safeStr(v) {
  return (v != null && typeof v === 'string') ? v : '';
}

export default {
  name: 'UsabilityReport',
  data() {
    return {
      form: this.loadDraft(),
      exporting: false,
      aiLoading: '',
      aiSuggestion: { section: '', text: '' },
    };
  },
  watch: {
    form: { deep: true, handler() { this.saveDraft(); } },
  },
  methods: {
    loadDraft() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        if (raw) {
          const parsed = JSON.parse(raw);
          const base = defaultForm();
          Object.keys(base).forEach((k) => {
            if (parsed[k] !== undefined) {
              if (Array.isArray(base[k]) && Array.isArray(parsed[k])) base[k] = parsed[k].map((row, i) => ({ ...(base[k][i] || {}), ...row }));
              else base[k] = parsed[k];
            }
          });
          return base;
        }
      } catch (e) { /* ignore */ }
      return defaultForm();
    },
    saveDraft() {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(this.form));
      } catch (e) { /* ignore */ }
    },
    getSection1Context() {
      const f = this.form;
      return [f.reportId, f.projectName, f.productSystem, f.featureModule, f.dateOfTest, f.qaResearcher].filter(Boolean).join('; ');
    },
    getSection2Context() {
      return [this.form.primaryObjective, this.form.secondaryObjectives, this.form.successCriteria].filter(Boolean).join('\n');
    },
    getSection3Context() {
      const f = this.form;
      const rows = f.participantsTable.map((r) => [r.id, r.role, r.experience].filter(Boolean).join(', ')).filter(Boolean);
      return [f.numParticipants, f.participantProfile, ...rows].filter(Boolean).join('\n');
    },
    getSection4Context() {
      const f = this.form;
      return [f.scenarioId, f.scenarioName, f.scenarioDescription, f.taskSteps, f.expectedOutcome].filter(Boolean).join('\n');
    },
    getSection5Context() {
      const f = this.form;
      const rows = this.form.performanceTable.map((r) => [r.participantId, r.completed, r.time].filter(Boolean).join(', ')).filter(Boolean);
      return [f.avgCompletionTime, f.taskSuccessRate, f.observedBehavior, ...rows].join('\n');
    },
    getSection6Context() {
      const f = this.form;
      return [f.issueId, f.issueTitle, f.issueDescription, f.issueSteps, f.issueImpact, f.issueRecommendation].filter(Boolean).join('\n');
    },
    getSection7Context() {
      return [this.form.keyQuotes, this.form.painPoints, this.form.positiveObservations].filter(Boolean).join('\n');
    },
    getSection8Context() {
      const f = this.form;
      return [f.metricsTaskSuccessRate, f.metricsAvgTime, f.metricsErrorRate, f.metricsSatisfaction, f.metricsSus].filter(Boolean).join(', ');
    },
    getSection9Context() {
      return [this.form.majorRisks, this.form.overallAssessment, this.form.recommendations].filter(Boolean).join('\n');
    },
    getSection10Context() {
      return safeStr(this.form.attachmentsNotes);
    },
    async askAi(section, context) {
      this.aiLoading = section;
      this.aiSuggestion = { section: '', text: '' };
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post('/api/usability-report/help', { section, context }, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
        this.aiSuggestion = { section, text: data.suggestion || '' };
      } catch (e) {
        this.aiSuggestion = { section, text: e.response?.data?.error || 'Не удалось получить подсказку.' };
      } finally {
        this.aiLoading = '';
      }
    },
    async exportPdf() {
      if (this.exporting) return;
      const el = this.$refs.pdfContent;
      if (!el) return;
      this.exporting = true;
      try {
        el.classList.add('ur-pdf-export');
        const canvas = await html2canvas(el, { scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' });
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
        const name = (safeStr(this.form.reportId) || 'usability-report').replace(/[^\w\s-]/g, '').slice(0, 30);
        pdf.save(`usability-report-${name}.pdf`);
      } catch (e) {
        console.error(e);
        alert('Ошибка при формировании PDF. Попробуйте ещё раз.');
      } finally {
        el.classList.remove('ur-pdf-export');
        this.exporting = false;
      }
    },
  },
};
</script>

<style scoped>
.usability-report-page {
  max-width: 820px;
  margin: 0 auto;
  padding: 24px 16px;
  font-family: 'Segoe UI', system-ui, sans-serif;
  color: #1a1a2e;
}

.ur-back {
  margin-bottom: 16px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #475569;
}

.ur-back:hover { background: #e2e8f0; }

.ur-header {
  margin-bottom: 28px;
}

.ur-header h1 {
  font-size: 1.65rem;
  color: #1a1a2e;
  margin: 0 0 10px;
  font-weight: 700;
}

.ur-intro {
  color: #475569;
  line-height: 1.55;
  margin: 0 0 16px;
}

.ur-actions { margin-bottom: 20px; }

.ur-btn {
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.95rem;
}

.ur-btn.primary {
  background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
}

.ur-btn.primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%);
  box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
}

.ur-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.ur-report-block {
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
  padding: 28px 24px;
}

.ur-section {
  margin-bottom: 32px;
  padding-bottom: 28px;
  border-bottom: 1px solid #e2e8f0;
}

.ur-section:last-child { border-bottom: none; margin-bottom: 0; padding-bottom: 0; }

.ur-section h2 {
  font-size: 1.15rem;
  color: #312e81;
  margin: 0 0 8px;
  font-weight: 700;
}

.ur-hint {
  font-size: 0.875rem;
  color: #64748b;
  margin: 0 0 10px;
  line-height: 1.45;
}

.ur-ai-btn {
  margin-bottom: 12px;
  padding: 6px 14px;
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  color: #0369a1;
  font-size: 0.875rem;
  cursor: pointer;
}

.ur-ai-btn:hover:not(:disabled) { background: #e0f2fe; }

.ur-ai-btn:disabled { opacity: 0.7; cursor: not-allowed; }

.ur-ai-suggestion {
  margin-bottom: 14px;
  padding: 12px 14px;
  background: #ecfdf5;
  border-left: 4px solid #10b981;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #065f46;
  line-height: 1.5;
  white-space: pre-line;
}

.ur-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px 20px;
}

.ur-field.full { grid-column: 1 / -1; }

.ur-metrics-grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }

.ur-field label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 4px;
}

.ur-field input,
.ur-field select,
.ur-field textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-size: 0.9rem;
  font-family: inherit;
  box-sizing: border-box;
}

.ur-field textarea { resize: vertical; min-height: 60px; }

.ur-field input:focus,
.ur-field select:focus,
.ur-field textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.ur-table-wrap {
  grid-column: 1 / -1;
  overflow-x: auto;
  margin-top: 8px;
}

.ur-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.ur-table th,
.ur-table td {
  border: 1px solid #e2e8f0;
  padding: 6px 8px;
  text-align: left;
}

.ur-table th {
  background: #f8fafc;
  font-weight: 600;
  color: #475569;
}

.ur-table input {
  width: 100%;
  padding: 4px 6px;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  font-size: 0.85rem;
}

.ur-pdf-export .ur-ai-btn,
.ur-pdf-export .ur-ai-suggestion { display: none !important; }

@media (max-width: 640px) {
  .ur-fields { grid-template-columns: 1fr; }
  .ur-metrics-grid { grid-template-columns: 1fr; }
}
</style>
