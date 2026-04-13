<template>
  <div class="take-maturity" :class="{ 'take-maturity--new': variant === 'new' }">
    <div v-if="loading" class="loading">{{ $t('maturity.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="teamSelfMode && teamSubmitDone" class="already-done team-self-done">
      <p>{{ $t('maturity.teamSelfThanks') }}</p>
    </div>
    <div v-else-if="!teamSelfMode && survey.completed" class="already-done">
      <p>{{ $t('maturity.alreadyCompleted') }}</p>
      <router-link :to="`${maturityBase}/results`" class="link-results">{{ $t('maturity.viewResults') }}</router-link>
    </div>
    <div v-else class="maturity-form">
      <header class="maturity-header">
        <h1>{{ teamSelfMode ? $t('maturity.teamSelfTitle') : $t('maturity.title') }}</h1>
        <p v-if="survey.team_name" class="team-name">{{ survey.team_name }}</p>
        <p class="survey-lang-hint">{{ $t('maturity.surveyLangHint') }}</p>
        <div class="survey-lang-toggle" role="group" :aria-label="$t('maturity.surveyLangAria')">
          <button
            type="button"
            :class="['lang-btn', { 'lang-btn--active': activeSurveyLang === 'ru' }]"
            @click="setSurveyLang('ru')"
          >
            {{ $t('maturity.surveyLangRu') }}
          </button>
          <button
            type="button"
            :class="['lang-btn', { 'lang-btn--active': activeSurveyLang === 'en' }]"
            @click="setSurveyLang('en')"
          >
            {{ $t('maturity.surveyLangEn') }}
          </button>
        </div>
        <div class="header-tools">
          <button v-if="survey.business_metrics_glossary && survey.business_metrics_glossary.length" type="button" class="glossary-toggle" @click="showGlossary = !showGlossary">
            {{ showGlossary ? $t('maturity.hideGlossary') : $t('maturity.showGlossary') }}
          </button>
          <button type="button" class="glossary-toggle" @click="showMetricsTree = !showMetricsTree">
            {{ showMetricsTree ? $t('maturity.hideMetricsTree') : $t('maturity.showMetricsTree') }}
          </button>
        </div>
        <div v-if="showGlossary && survey.business_metrics_glossary" class="glossary-block">
          <div v-for="m in survey.business_metrics_glossary" :key="m.id" class="glossary-item">
            <strong>{{ m.name }}</strong> — {{ m.description }}
          </div>
        </div>
        <MetricsTreePanel
          v-if="showMetricsTree"
          :title="$t('maturity.metricsTreeInlineTitle')"
          :survey-token="token"
          :ui-lang="activeSurveyLang"
          compact
          class="survey-metrics-tree"
        />
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
                {{ $t('maturity.whyImportantBtn') }}
              </button>
              <button
                type="button"
                class="clarify-trigger"
                :disabled="clarifyLoading === q.id"
                @click="askClarify(q)"
              >
                {{ clarifyLoading === q.id ? '...' : $t('maturity.askClarify') }}
              </button>
              <div v-if="q.why_important" class="question-why-hint" :class="{ visible: expandedWhy[q.id] }">
                <span class="why-label">{{ $t('maturity.whyImportantLabel') }}</span> {{ q.why_important }}
              </div>
            </div>
            <div class="yes-no">
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

            <div class="comment-block">
              <label class="comment-label">{{ $t('maturity.commentLabel') }}</label>
              <textarea
                v-model="comments[q.id]"
                class="comment-input"
                :disabled="answers[q.id] === null || answers[q.id] === undefined"
                :placeholder="$t('maturity.commentPlaceholder')"
                rows="2"
              />
            </div>
          </div>
          <div v-if="clarifyResult && clarifyResult.id === q.id" class="clarify-block">
              <strong>{{ $t('maturity.clarifyLead') }}</strong>
              <p class="clarify-text">{{ clarifyResult.content }}</p>
            </div>
          <div v-if="q.business_metrics" class="info-block info-business-metrics">
            <div class="info-block-title">{{ $t('maturity.businessMetricsTitle') }}</div>
            <p class="info-block-text">{{ q.business_metrics }}</p>
            <p class="business-metrics-disclaimer">{{ survey.business_metrics_disclaimer }}</p>
          </div>
          <div v-if="q.metrics_impact || q.negative_for_business" class="question-info">
            <div v-if="q.metrics_impact" class="info-block info-metrics">
              <div class="info-block-title">{{ $t('maturity.metricsImpactTitle') }}</div>
              <p class="info-block-text">{{ q.metrics_impact }}</p>
            </div>
            <div v-if="q.negative_for_business" class="info-block info-negative">
              <div class="info-block-title">{{ $t('maturity.negativeIfWeakTitle') }}</div>
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
          :disabled="!allFilled || submitting"
          @click="submit"
        >
          {{ teamSelfMode ? $t('maturity.teamSelfSubmit') : $t('maturity.submit') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import MetricsTreePanel from "@/components/metrics/MetricsTreePanel.vue";
import { maturitySurveyLangParams, setMaturitySurveyLangPreference } from '@/utils/maturitySurveyLang';

const QUESTIONS_PER_PAGE = 10;

export default {
  name: 'TakeMaturity',
  components: { MetricsTreePanel },
  props: {
    variant: { type: String, default: 'legacy' },
    teamSelfMode: { type: Boolean, default: false },
  },
  data() {
    return {
      token: '',
      teamSubmitDone: false,
      survey: { team_name: null, questions: [], completed: false },
      answers: {},
      comments: {},
      currentPage: 0,
      loading: true,
      error: null,
      submitting: false,
      questionsPerPage: QUESTIONS_PER_PAGE,
      expandedWhy: {},
      clarifyLoading: null,
      clarifyResult: null,
      showGlossary: false,
      showMetricsTree: false,
      i18nLocaleSnapshot: null
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
    },
    maturityBase() {
      return this.variant === "new" ? `/new/maturity/${this.token}` : `/maturity/${this.token}`;
    },
    activeSurveyLang() {
      const q = this.$route.query.lang;
      if (q === 'ru' || q === 'en') return q;
      try {
        const s = sessionStorage.getItem(`maturitySurveyLang:${this.token}`);
        if (s === 'ru' || s === 'en') return s;
      } catch (_e) {
        /* ignore */
      }
      const fromApi = this.survey.lang;
      if (fromApi === 'ru' || fromApi === 'en') return fromApi;
      try {
        const loc = this.$i18n?.locale;
        const z = typeof loc === 'string' ? loc : loc?.value;
        return z === 'en' ? 'en' : 'ru';
      } catch (_e) {
        return typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en' ? 'en' : 'ru';
      }
    }
  },
  async mounted() {
    try {
      const loc = this.$i18n?.locale;
      this.i18nLocaleSnapshot = typeof loc === 'string' ? loc : loc?.value;
    } catch (_e) {
      this.i18nLocaleSnapshot = null;
    }
    this.token = this.teamSelfMode
      ? this.$route.params.teamToken
      : this.$route.params.token;
    await this.loadSurvey();
  },
  beforeUnmount() {
    if (this.i18nLocaleSnapshot == null || !this.$i18n) return;
    const prev = this.i18nLocaleSnapshot;
    try {
      if (typeof this.$i18n.locale === 'string') {
        this.$i18n.locale = prev;
      } else if (this.$i18n.locale && typeof this.$i18n.locale === 'object' && 'value' in this.$i18n.locale) {
        this.$i18n.locale.value = prev;
      }
    } catch (_e) {
      /* ignore */
    }
  },
  methods: {
    _setI18nLocale(code) {
      if (!this.$i18n || (code !== 'ru' && code !== 'en')) return;
      try {
        if (typeof this.$i18n.locale === 'string') {
          this.$i18n.locale = code;
        } else if (this.$i18n.locale && typeof this.$i18n.locale === 'object' && 'value' in this.$i18n.locale) {
          this.$i18n.locale.value = code;
        }
      } catch (_e) {
        /* ignore */
      }
    },
    setSurveyLang(code) {
      if (code !== 'ru' && code !== 'en') return;
      setMaturitySurveyLangPreference(this.token, code);
      this.$router.replace({
        path: this.$route.path,
        query: { ...this.$route.query, lang: code }
      }).then(() => {
        this._setI18nLocale(code);
        this.loadSurvey();
      }).catch(() => {});
    },
    async loadSurvey() {
      try {
        const path = this.teamSelfMode
          ? `/api/maturity/team/${this.token}`
          : `/api/maturity/${this.token}`;
        const res = await axios.get(path, { params: maturitySurveyLangParams(this.token, this.$route) });
        this.survey = res.data;
        this.survey.business_metrics_disclaimer = res.data.business_metrics_disclaimer || '';
        this.survey.business_metrics_glossary = res.data.business_metrics_glossary || [];
        if (res.data.lang) {
          this._setI18nLocale(res.data.lang);
        }
        this.survey.questions.forEach(q => {
          if (this.answers[q.id] === undefined) this.answers[q.id] = null;
          if (this.comments[q.id] === undefined) this.comments[q.id] = '';
        });
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('maturity.loadSurveyError');
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
          question_text: q.text,
          lang: this.survey.lang || this.activeSurveyLang,
        });
        this.clarifyResult = { id: q.id, content: res.data.content || '' };
      } catch (e) {
        this.clarifyResult = { id: q.id, content: this.$t('maturity.clarifyErrorPrefix') + ' ' + (e.response?.data?.error || this.$t('maturity.serviceUnavailable')) };
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
        const commentsArr = [];
        const allowed = new Set(['no', 'rather_no', 'dont_know', 'rather_yes', 'yes']);
        for (let i = 0; i < total; i++) {
          const a = this.answers[i];
          arr.push(allowed.has(a) ? a : 'no');
          const c = (this.comments[i] || '').toString().trim();
          commentsArr.push(c ? c : null);
        }
        const langPayload = this.survey.lang === 'ru' || this.survey.lang === 'en'
          ? this.survey.lang
          : this.activeSurveyLang;
        if (this.teamSelfMode) {
          await axios.post(`/api/maturity/team/${this.token}/submit`, {
            answers: arr,
            comments: commentsArr,
            lang: langPayload
          });
          this.teamSubmitDone = true;
        } else {
          await axios.post(`/api/maturity/${this.token}/submit`, {
            answers: arr,
            comments: commentsArr,
            lang: langPayload
          });
          this.$router.push(`${this.maturityBase}/results`);
        }
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('maturity.submitSurveyError');
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
.survey-lang-hint {
  font-size: 0.82rem;
  color: #64748b;
  margin: 0.5rem 0 0.35rem;
  line-height: 1.35;
}
.survey-lang-toggle {
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.lang-btn {
  padding: 0.35rem 0.85rem;
  font-size: 0.85rem;
  border-radius: 999px;
  border: 1px solid #cbd5e1;
  background: #fff;
  color: #475569;
  cursor: pointer;
}
.lang-btn--active {
  border-color: #2563eb;
  background: #eff6ff;
  color: #1d4ed8;
  font-weight: 600;
}
.glossary-toggle {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: #0369a1;
  background: none;
  border: none;
  cursor: pointer;
  text-decoration: underline;
}
.header-tools {
  display: flex;
  justify-content: center;
  gap: 10px;
  flex-wrap: wrap;
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
.survey-metrics-tree {
  margin-top: 0.85rem;
  text-align: left;
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

.comment-block {
  margin-top: 0.75rem;
}

.comment-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.35rem;
}

.comment-input {
  width: 100%;
  box-sizing: border-box;
  resize: vertical;
  padding: 0.65rem 0.75rem;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  font-size: 0.9rem;
  line-height: 1.35;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.comment-input:focus {
  outline: none;
  border-color: #93c5fd;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12);
}

.comment-input:disabled {
  background: #f3f4f6;
  color: #6b7280;
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
.btn-rather-no.active { background: #ea580c; border-color: #ea580c; color: #fff; }
.btn-rather-yes.active { background: #65a30d; border-color: #65a30d; color: #fff; }
.btn-dont-know.active { background: #64748b; border-color: #64748b; color: #fff; }

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

/* —— New shell (variant new, /new/maturity/:token) —— */
.take-maturity.take-maturity--new {
  max-width: 820px;
  margin: 0 auto;
  padding: 20px 16px 40px;
  background: linear-gradient(180deg, rgba(247, 249, 255, 0.95) 0%, rgba(255, 255, 255, 0.4) 40%);
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.06);
  box-shadow: 0 20px 60px rgba(10, 20, 45, 0.08);
}

.take-maturity--new .maturity-header h1 {
  font-size: 1.65rem;
  letter-spacing: -0.02em;
  color: rgba(10, 20, 45, 0.92);
}

.take-maturity--new .question-block {
  border-radius: 16px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 12px 40px rgba(10, 20, 45, 0.06);
  background: rgba(255, 255, 255, 0.95);
}

.take-maturity--new .progress-bar {
  height: 10px;
  border-radius: 999px;
  background: rgba(10, 20, 45, 0.06);
}

.take-maturity--new .progress-fill {
  background: linear-gradient(90deg, rgba(32, 90, 255, 0.95), rgba(0, 194, 255, 0.85));
  border-radius: 999px;
}

.take-maturity--new .btn-answer {
  border-radius: 12px;
  padding: 0.65rem 1.35rem;
}

.take-maturity--new .btn-nav {
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(10, 20, 45, 0.1);
}

.take-maturity--new .btn-nav.next,
.take-maturity--new .btn-nav.submit {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
  color: #fff;
}

.take-maturity--new .btn-nav.next:hover:not(:disabled),
.take-maturity--new .btn-nav.submit:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-1px);
}

.take-maturity--new .btn-nav.prev:hover:not(:disabled) {
  filter: brightness(1.08);
}

.take-maturity--new .link-results {
  font-weight: 650;
  padding: 10px 18px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.12), rgba(0, 194, 255, 0.1));
  text-decoration: none;
}

.take-maturity--new .question-block {
  position: relative;
  overflow: hidden;
  animation: maturityCardIn 360ms ease-out;
}

.take-maturity--new .question-block::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(150deg, rgba(255, 255, 255, 0.28), transparent 40%);
  pointer-events: none;
}

.take-maturity--new .comment-input,
.take-maturity--new .glossary-block {
  background: rgba(248, 250, 255, 0.95);
  border-color: rgba(10, 20, 45, 0.12);
}

.take-maturity--new .comment-input:focus {
  border-color: rgba(32, 90, 255, 0.55);
  box-shadow: 0 0 0 5px rgba(32, 90, 255, 0.12);
}

.take-maturity--new .btn-answer {
  border-color: rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.9);
}

.take-maturity--new .btn-answer:hover:not(.active) {
  border-color: rgba(32, 90, 255, 0.45);
  box-shadow: 0 8px 20px rgba(32, 90, 255, 0.14);
  transform: translateY(-1px);
}

.take-maturity--new .btn-yes.active {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.95), rgba(16, 185, 129, 0.86));
  border-color: rgba(34, 197, 94, 0.6);
}

.take-maturity--new .btn-no.active {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.95), rgba(244, 63, 94, 0.88));
  border-color: rgba(239, 68, 68, 0.6);
}

.take-maturity--new .btn-dont-know.active {
  background: linear-gradient(135deg, rgba(100, 116, 139, 0.95), rgba(71, 85, 105, 0.88));
  border-color: rgba(100, 116, 139, 0.6);
}

.take-maturity--new .btn-rather-no.active {
  background: linear-gradient(135deg, rgba(234, 88, 12, 0.95), rgba(249, 115, 22, 0.88));
  border-color: rgba(234, 88, 12, 0.6);
}

.take-maturity--new .btn-rather-yes.active {
  background: linear-gradient(135deg, rgba(101, 163, 13, 0.95), rgba(132, 204, 22, 0.88));
  border-color: rgba(101, 163, 13, 0.6);
}

.take-maturity--new .btn-nav.prev {
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.9), rgba(100, 116, 139, 0.86));
}

.take-maturity--new .btn-nav {
  position: relative;
  overflow: hidden;
}

.take-maturity--new .btn-nav::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 18%, rgba(255, 255, 255, 0.3), transparent 82%);
  transform: translateX(-120%);
  transition: transform 0.6s ease;
}

.take-maturity--new .btn-nav:hover::after {
  transform: translateX(120%);
}

@keyframes maturityCardIn {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
