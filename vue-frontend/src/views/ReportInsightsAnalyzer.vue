<template>
  <div class="ri-page">
    <div class="ri-page__bg" aria-hidden="true">
      <div class="ri-page__orb ri-page__orb--1" />
      <div class="ri-page__orb ri-page__orb--2" />
    </div>

    <NewToolShell :title="$t('reportInsights.title')" :subtitle="$t('reportInsights.subtitle')">
      <section class="ri-intro">
        <p class="ri-intro__lead">{{ $t('reportInsights.lead') }}</p>
        <ul class="ri-intro__bullets">
          <li>{{ $t('reportInsights.bullet1') }}</li>
          <li>{{ $t('reportInsights.bullet2') }}</li>
          <li>{{ $t('reportInsights.bullet3') }}</li>
        </ul>
      </section>

      <section class="ri-card">
        <h2 class="ri-card__h">{{ $t('reportInsights.uploadTitle') }}</h2>
        <p class="ri-card__hint">{{ $t('reportInsights.uploadHint') }}</p>

        <div class="ri-upload">
          <label class="ri-dropzone" :class="{ 'ri-dropzone--filled': fileName }">
            <input
              ref="fileInput"
              type="file"
              accept=".html,.htm,.pdf,.txt,.csv,.json,.png,.jpg,.jpeg,.webp,.gif,text/html,application/pdf,image/*,text/plain"
              class="ri-dropzone__input"
              @change="onFilePicked"
            />
            <span v-if="!fileName" class="ri-dropzone__placeholder">
              <span class="ri-dropzone__plus">+</span>
              <span>{{ $t('reportInsights.dropzonePlaceholder') }}</span>
            </span>
            <span v-else class="ri-dropzone__filename">{{ fileName }}</span>
          </label>
          <button v-if="fileName" type="button" class="ri-btn ri-btn--ghost" @click="clearFile">
            {{ $t('reportInsights.clearFile') }}
          </button>
        </div>

        <div class="ri-or">{{ $t('reportInsights.or') }}</div>

        <label class="ri-field__label" for="ri-text">{{ $t('reportInsights.pasteLabel') }}</label>
        <textarea
          id="ri-text"
          v-model="pastedText"
          class="ri-textarea"
          rows="6"
          :placeholder="$t('reportInsights.pastePlaceholder')"
        />

        <label class="ri-field__label" for="ri-notes">{{ $t('reportInsights.notesLabel') }}</label>
        <textarea
          id="ri-notes"
          v-model="notes"
          class="ri-textarea ri-textarea--short"
          rows="2"
          :placeholder="$t('reportInsights.notesPlaceholder')"
        />

        <div class="ri-actions">
          <button type="button" class="ri-btn ri-btn--primary" :disabled="!canAnalyze || loading" @click="analyze">
            <span v-if="!loading">{{ $t('reportInsights.analyzeCta') }}</span>
            <span v-else>{{ $t('reportInsights.analyzing') }}</span>
          </button>
          <button type="button" class="ri-btn ri-btn--ghost" :disabled="loading" @click="loadSampleText">
            {{ $t('reportInsights.loadSample') }}
          </button>
        </div>

        <p v-if="error" class="ri-error">{{ error }}</p>
      </section>

      <section v-if="result" class="ri-results">
        <header class="ri-results__header" :class="`ri-results__header--${result.health}`">
          <div class="ri-results__health-dot" />
          <div>
            <div class="ri-results__health-label">{{ healthLabel }}</div>
            <h2 class="ri-results__title">{{ $t('reportInsights.results.summaryTitle') }}</h2>
          </div>
        </header>
        <p class="ri-results__summary">{{ result.summary || $t('reportInsights.results.noSummary') }}</p>

        <div v-if="result.kpis && result.kpis.length" class="ri-kpis">
          <div v-for="(k, idx) in result.kpis" :key="`kpi-${idx}`" class="ri-kpi">
            <div class="ri-kpi__label">{{ k.label }}</div>
            <div class="ri-kpi__value">{{ k.value }}</div>
            <div v-if="k.comment" class="ri-kpi__comment">{{ k.comment }}</div>
          </div>
        </div>

        <h3 class="ri-results__h3">{{ $t('reportInsights.results.insightsTitle') }}</h3>
        <div v-if="result.insights && result.insights.length" class="ri-insights">
          <article
            v-for="(ins, idx) in result.insights"
            :key="`ins-${idx}`"
            class="ri-insight"
            :class="`ri-insight--${(ins.severity || 'info').toLowerCase()}`"
          >
            <header class="ri-insight__head">
              <span class="ri-insight__severity">{{ severityLabel(ins.severity) }}</span>
              <span class="ri-insight__category">{{ categoryLabel(ins.category) }}</span>
            </header>
            <h4 class="ri-insight__title">{{ ins.title }}</h4>
            <p v-if="ins.evidence" class="ri-insight__evidence">
              <strong>{{ $t('reportInsights.results.evidence') }}:</strong> {{ ins.evidence }}
            </p>
            <p v-if="ins.why_it_matters" class="ri-insight__why">
              <strong>{{ $t('reportInsights.results.why') }}:</strong> {{ ins.why_it_matters }}
            </p>
            <p v-if="ins.suggested_action" class="ri-insight__action">
              <strong>{{ $t('reportInsights.results.action') }}:</strong> {{ ins.suggested_action }}
            </p>
          </article>
        </div>
        <p v-else class="ri-empty">{{ $t('reportInsights.results.noInsights') }}</p>

        <div v-if="result.questions_to_ask && result.questions_to_ask.length" class="ri-questions">
          <h3 class="ri-results__h3">{{ $t('reportInsights.results.questionsTitle') }}</h3>
          <ul>
            <li v-for="(q, idx) in result.questions_to_ask" :key="`q-${idx}`">{{ q }}</li>
          </ul>
        </div>
      </section>
    </NewToolShell>
  </div>
</template>

<script>
import axios from 'axios';
import NewToolShell from '@/views/NewToolShell.vue';

export default {
  name: 'ReportInsightsAnalyzer',
  components: { NewToolShell },
  data() {
    return {
      pastedText: '',
      notes: '',
      file: null,
      fileName: '',
      loading: false,
      error: '',
      result: null,
    };
  },
  computed: {
    locale() {
      const loc = this.$i18n.locale;
      const s = typeof loc === 'string' ? loc : loc?.value || 'ru';
      return String(s).toLowerCase().startsWith('en') ? 'en' : 'ru';
    },
    canAnalyze() {
      return !!(this.file || (this.pastedText && this.pastedText.trim().length > 20));
    },
    healthLabel() {
      const h = this.result?.health || 'yellow';
      return this.$t(`reportInsights.results.health.${h}`);
    },
  },
  methods: {
    onFilePicked(e) {
      const f = e.target.files?.[0];
      if (!f) return;
      if (f.size > 6 * 1024 * 1024) {
        this.error = this.$t('reportInsights.errors.fileTooLarge');
        e.target.value = '';
        return;
      }
      this.file = f;
      this.fileName = f.name;
      this.error = '';
    },
    clearFile() {
      this.file = null;
      this.fileName = '';
      if (this.$refs.fileInput) this.$refs.fileInput.value = '';
    },
    loadSampleText() {
      this.pastedText = this.locale === 'en' ? this.sampleEn() : this.sampleRu();
    },
    severityLabel(sev) {
      const key = (sev || 'info').toLowerCase();
      return this.$t(`reportInsights.results.severity.${key}`, key);
    },
    categoryLabel(cat) {
      const key = (cat || 'other').toLowerCase();
      return this.$t(`reportInsights.results.category.${key}`, key);
    },
    async analyze() {
      if (!this.canAnalyze || this.loading) return;
      this.loading = true;
      this.error = '';
      this.result = null;
      const token = localStorage.getItem('token');
      const headers = token ? { Authorization: `Bearer ${token}` } : {};
      try {
        let resp;
        if (this.file) {
          const fd = new FormData();
          fd.append('file', this.file);
          fd.append('locale', this.locale);
          if (this.notes) fd.append('notes', this.notes);
          resp = await axios.post('/api/report-insights/analyze', fd, { headers });
        } else {
          resp = await axios.post(
            '/api/report-insights/analyze',
            { text: this.pastedText, notes: this.notes, locale: this.locale },
            { headers },
          );
        }
        this.result = resp.data;
      } catch (e) {
        const srv = e?.response?.data?.error;
        this.error = srv || this.$t('reportInsights.errors.generic');
      } finally {
        this.loading = false;
      }
    },
    sampleRu() {
      return (
        'Ежеквартальный отчёт по доставке (Q3):\n' +
        'Выручка: 12.4M руб. (план 12.0M, факт прошлого квартала 11.9M).\n' +
        'Маржа: 18% (Q2: 22%, Q1: 21%).\n' +
        'Lead time: среднее 14 дней, медиана 9 дней, P90 42 дня.\n' +
        'Открытые инциденты P1: 3 (Q2: 1).\n' +
        'NPS: 38 (Q2: 41, Q1: 39).\n' +
        'Просроченная дебиторка: 1.1M руб. по 2 клиентам.\n' +
        'Затраты на подрядчиков: 2.3M руб. (+28% к Q2).\n'
      );
    },
    sampleEn() {
      return (
        'Quarterly delivery report (Q3):\n' +
        'Revenue: $12.4M (plan $12.0M, last quarter $11.9M).\n' +
        'Margin: 18% (Q2: 22%, Q1: 21%).\n' +
        'Lead time: mean 14 days, median 9 days, P90 42 days.\n' +
        'Open P1 incidents: 3 (Q2: 1).\n' +
        'NPS: 38 (Q2: 41, Q1: 39).\n' +
        'Overdue AR: $1.1M across 2 customers.\n' +
        'Contractor spend: $2.3M (+28% vs Q2).\n'
      );
    },
  },
};
</script>

<style scoped>
.ri-page {
  min-height: calc(100vh - 40px);
  position: relative;
}
.ri-page__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}
.ri-page__orb {
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  filter: blur(60px);
  opacity: 0.55;
}
.ri-page__orb--1 {
  top: -180px;
  left: -200px;
  background: radial-gradient(circle at 30% 30%, rgba(32, 90, 255, 0.5), transparent 65%);
}
.ri-page__orb--2 {
  bottom: -200px;
  right: -160px;
  background: radial-gradient(circle at 70% 70%, rgba(0, 194, 255, 0.35), transparent 65%);
}

.ri-intro {
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.9), rgba(246, 249, 255, 0.75));
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 18px;
  padding: 20px 22px;
  box-shadow: 0 18px 42px rgba(10, 20, 45, 0.08);
  position: relative;
  z-index: 1;
}
.ri-intro__lead {
  margin: 0 0 10px;
  color: rgba(10, 20, 45, 0.9);
  line-height: 1.55;
}
.ri-intro__bullets {
  margin: 0;
  padding-left: 20px;
  color: rgba(10, 20, 45, 0.78);
  line-height: 1.55;
}

.ri-card {
  margin-top: 22px;
  background: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 20px;
  padding: 22px 24px;
  box-shadow: 0 24px 60px rgba(10, 20, 45, 0.09);
  position: relative;
  z-index: 1;
}
.ri-card__h {
  margin: 0 0 6px;
  font-size: 18px;
  font-weight: 700;
}
.ri-card__hint {
  margin: 0 0 16px;
  color: rgba(10, 20, 45, 0.7);
  font-size: 14px;
}

.ri-upload {
  display: flex;
  gap: 12px;
  align-items: stretch;
  flex-wrap: wrap;
}
.ri-dropzone {
  flex: 1;
  min-height: 86px;
  border: 1.6px dashed rgba(32, 90, 255, 0.4);
  background: rgba(32, 90, 255, 0.04);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 14px 18px;
  cursor: pointer;
  transition: 0.2s ease;
  color: rgba(10, 20, 45, 0.85);
  font-size: 14px;
}
.ri-dropzone:hover {
  background: rgba(32, 90, 255, 0.08);
}
.ri-dropzone--filled {
  border-style: solid;
  background: rgba(32, 90, 255, 0.09);
}
.ri-dropzone__input {
  display: none;
}
.ri-dropzone__placeholder {
  display: inline-flex;
  gap: 10px;
  align-items: center;
}
.ri-dropzone__plus {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: rgba(32, 90, 255, 0.18);
  color: #3454ff;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.ri-dropzone__filename {
  font-weight: 600;
}

.ri-or {
  text-align: center;
  color: rgba(10, 20, 45, 0.55);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 14px 0 10px;
}

.ri-field__label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  margin: 12px 0 6px;
  color: rgba(10, 20, 45, 0.78);
}

.ri-textarea {
  width: 100%;
  border: 1px solid rgba(10, 20, 45, 0.14);
  border-radius: 12px;
  padding: 10px 12px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, monospace;
  font-size: 13px;
  line-height: 1.5;
  background: #fff;
  resize: vertical;
  min-height: 120px;
  color: rgba(10, 20, 45, 0.92);
}
.ri-textarea--short {
  font-family: inherit;
  min-height: 60px;
  font-size: 14px;
}
.ri-textarea:focus {
  outline: none;
  border-color: rgba(32, 90, 255, 0.5);
  box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.12);
}

.ri-actions {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  flex-wrap: wrap;
}
.ri-btn {
  padding: 10px 18px;
  border-radius: 12px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  border: 1px solid rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.92);
  color: rgba(10, 20, 45, 0.92);
  transition: 0.18s ease;
}
.ri-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.35);
}
.ri-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.ri-btn--primary {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.96), rgba(0, 194, 255, 0.88));
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 16px rgba(32, 90, 255, 0.35);
}

.ri-error {
  margin-top: 10px;
  color: #b00020;
  font-size: 13px;
}

.ri-results {
  margin-top: 22px;
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 20px;
  padding: 22px 24px;
  box-shadow: 0 28px 70px rgba(10, 20, 45, 0.1);
  position: relative;
  z-index: 1;
}
.ri-results__header {
  display: flex;
  gap: 12px;
  align-items: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(10, 20, 45, 0.08);
  margin-bottom: 12px;
}
.ri-results__health-dot {
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #fbbf24;
  box-shadow: 0 0 0 4px rgba(251, 191, 36, 0.18);
}
.ri-results__header--green .ri-results__health-dot {
  background: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.18);
}
.ri-results__header--red .ri-results__health-dot {
  background: #ef4444;
  box-shadow: 0 0 0 4px rgba(239, 68, 68, 0.18);
}
.ri-results__health-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: rgba(10, 20, 45, 0.6);
}
.ri-results__title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
}
.ri-results__summary {
  margin: 0 0 14px;
  line-height: 1.55;
  color: rgba(10, 20, 45, 0.9);
}
.ri-results__h3 {
  font-size: 15px;
  margin: 18px 0 8px;
  font-weight: 700;
}

.ri-kpis {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 10px;
  margin: 6px 0 4px;
}
.ri-kpi {
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(246, 249, 255, 0.7);
  border-radius: 12px;
  padding: 10px 12px;
}
.ri-kpi__label {
  font-size: 12px;
  color: rgba(10, 20, 45, 0.6);
}
.ri-kpi__value {
  font-size: 18px;
  font-weight: 700;
  margin-top: 2px;
}
.ri-kpi__comment {
  font-size: 12px;
  color: rgba(10, 20, 45, 0.72);
  margin-top: 2px;
}

.ri-insights {
  display: grid;
  gap: 10px;
}
.ri-insight {
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-left: 4px solid rgba(10, 20, 45, 0.3);
  background: rgba(255, 255, 255, 0.95);
  border-radius: 12px;
  padding: 12px 14px;
}
.ri-insight--info { border-left-color: #3b82f6; }
.ri-insight--watch { border-left-color: #f59e0b; }
.ri-insight--warning { border-left-color: #f97316; }
.ri-insight--critical { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.04); }

.ri-insight__head {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 11px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(10, 20, 45, 0.6);
}
.ri-insight__title {
  margin: 4px 0 6px;
  font-size: 15px;
  font-weight: 700;
}
.ri-insight__evidence,
.ri-insight__why,
.ri-insight__action {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.5;
  color: rgba(10, 20, 45, 0.85);
}

.ri-questions ul {
  margin: 0;
  padding-left: 20px;
  color: rgba(10, 20, 45, 0.85);
  line-height: 1.55;
}
.ri-empty {
  color: rgba(10, 20, 45, 0.6);
  font-style: italic;
}
</style>
