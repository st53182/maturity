<template>
  <div class="maturity-results" :class="{ 'maturity-results--new': variant === 'new' }">
    <div v-if="loading" class="loading">{{ $t('maturity.loading') }}</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else class="results-content">
      <div ref="pdfContent" class="pdf-block">
        <h1 class="results-title">{{ $t('maturity.resultsTitle') }}</h1>
        <p class="meta">
          <span v-if="teamName" class="team">{{ teamName }}</span>
          <span v-if="completedAt" class="date">{{ formattedDate }}</span>
        </p>
        <p class="average-line">
          {{ $t('maturity.overallScore') }}: <strong>{{ averageScore.toFixed(2) }}</strong>
        </p>
        <p v-if="teamComparison && teamComparison.submission_count > 0" class="team-comparison-hint">
          {{ $t('maturity.teamComparisonHint', { count: teamComparison.submission_count }) }}
        </p>
        <p v-if="aiUsageRemaining !== null" class="ai-usage-line">{{ $t('maturity.results.aiUsageRemaining', { count: aiUsageRemaining }) }}</p>

        <div
          v-for="group in radarGroups"
          :key="group.title"
          v-show="chartDataForGroup(group).labels.length"
          class="group-block"
        >
          <div class="radar-wrap">
            <RadarChart :chart-data="chartDataForGroup(group)" :title="group.title" />
          </div>
          <div class="themes-list">
            <button
              v-for="cat in themesInGroup(group)"
              :key="cat.theme"
              type="button"
              class="theme-row"
              @click="openDetail(cat.theme)"
            >
              <span class="theme-name">{{ displayThemeName(cat.theme) }}</span>
              <span class="theme-score" :class="scoreClass(cat.avg)">{{ formatScore(cat.avg) }}</span>
            </button>
          </div>
        </div>

        <div v-if="recommendationsHtml || recommendationsPlan.initiatives.length" class="recommendations-block">
          <h2 class="rec-title">{{ $t('maturity.recommendationsTitle') }}</h2>
          <div class="rec-actions">
            <button type="button" class="btn-rec" @click="editingRecommendations = !editingRecommendations">
              {{ editingRecommendations ? $t('maturity.results.cancelEdit') : $t('maturity.results.edit') }}
            </button>
            <button type="button" class="btn-rec" :disabled="savingRecommendations" @click="saveRecommendations">
              {{ savingRecommendations ? $t('maturity.results.saving') : $t('maturity.results.save') }}
            </button>
          </div>
          <div v-if="editingRecommendations" class="group-plan-editor">
            <label class="plan-label">{{ $t('maturity.results.diagnosis') }}</label>
            <textarea v-model="recommendationsPlan.diagnosis" class="plan-input" rows="3" />

            <h4>{{ $t('maturity.results.initiatives') }}</h4>
            <article v-for="(item, idx) in recommendationsPlan.initiatives" :key="'team-init-' + idx" class="initiative-card">
              <div class="initiative-head">
                <strong>{{ $t('maturity.results.initiativeN', { n: idx + 1 }) }}</strong>
                <div class="initiative-actions">
                  <button type="button" class="btn-rec" @click="toggleTeamInitiativeCollapse(idx)">
                    {{ isTeamInitiativeCollapsed(idx) ? $t('maturity.results.expand') : $t('maturity.results.collapse') }}
                  </button>
                  <button type="button" class="btn-rec" @click="removeTeamInitiative(idx)">{{ $t('maturity.results.delete') }}</button>
                </div>
              </div>
              <div v-if="!isTeamInitiativeCollapsed(idx)">
                <label class="plan-label">{{ $t('maturity.results.fieldTitle') }}</label>
                <input v-model="item.title" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.fieldObjective') }}</label>
                <textarea v-model="item.objective" class="plan-input" rows="2" />
                <label class="plan-label">{{ $t('maturity.results.ownerRole') }}</label>
                <input v-model="item.owner" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.successMetricLabel') }}</label>
                <input v-model="item.success_metric" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.businessEffect') }}</label>
                <textarea v-model="item.business_impact" class="plan-input" rows="2" />
                <label class="plan-label">{{ $t('maturity.results.customerEffect') }}</label>
                <textarea v-model="item.customer_impact" class="plan-input" rows="2" />
                <label class="plan-label">{{ $t('maturity.results.stepsLabel') }}</label>
                <textarea
                  class="plan-input"
                  rows="6"
                  :value="(item.steps || []).join('\n')"
                  @input="syncPlanSteps(item, $event)"
                />
              </div>
            </article>
            <button type="button" class="btn-rec" @click="addTeamInitiative">{{ $t('maturity.results.addInitiative') }}</button>
          </div>
          <div v-html="recommendationsHtml" class="rec-html"></div>
        </div>

        <div v-if="hasDontKnow" class="recommendations-block dont-know-rec-block">
          <h2 class="rec-title">{{ $t('maturity.results.dontKnowTitle') }}</h2>
          <p class="rec-hint">{{ $t('maturity.results.dontKnowHint') }}</p>
          <button
            type="button"
            class="btn-rec btn-dont-know-rec"
            :disabled="loadingDontKnowRecs"
            @click="fetchDontKnowRecommendations"
          >
            {{ loadingDontKnowRecs ? $t('maturity.results.dontKnowGenerating') : $t('maturity.results.dontKnowFetch') }}
          </button>
          <div v-if="dontKnowHtml" class="rec-actions">
            <button type="button" class="btn-rec" @click="editingDontKnow = !editingDontKnow">
              {{ editingDontKnow ? $t('maturity.results.cancelEdit') : $t('maturity.results.edit') }}
            </button>
            <button type="button" class="btn-rec" :disabled="savingDontKnow" @click="saveDontKnowRecommendations">
              {{ savingDontKnow ? $t('maturity.results.saving') : $t('maturity.results.save') }}
            </button>
          </div>
          <div v-if="editingDontKnow" class="group-plan-editor">
            <label class="plan-label">{{ $t('maturity.results.diagnosis') }}</label>
            <textarea v-model="dontKnowPlan.diagnosis" class="plan-input" rows="3" />

            <h4>{{ $t('maturity.results.initiatives') }}</h4>
            <article v-for="(item, idx) in dontKnowPlan.initiatives" :key="'dk-init-' + idx" class="initiative-card">
              <div class="initiative-head">
                <strong>{{ $t('maturity.results.initiativeN', { n: idx + 1 }) }}</strong>
                <div class="initiative-actions">
                  <button type="button" class="btn-rec" @click="toggleDontKnowInitiativeCollapse(idx)">
                    {{ isDontKnowInitiativeCollapsed(idx) ? $t('maturity.results.expand') : $t('maturity.results.collapse') }}
                  </button>
                  <button type="button" class="btn-rec" @click="removeDontKnowInitiative(idx)">{{ $t('maturity.results.delete') }}</button>
                </div>
              </div>
              <div v-if="!isDontKnowInitiativeCollapsed(idx)">
                <label class="plan-label">{{ $t('maturity.results.fieldTitle') }}</label>
                <input v-model="item.title" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.fieldObjective') }}</label>
                <textarea v-model="item.objective" class="plan-input" rows="2" />
                <label class="plan-label">{{ $t('maturity.results.ownerRole') }}</label>
                <input v-model="item.owner" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.successMetricLabel') }}</label>
                <input v-model="item.success_metric" class="plan-input" />
                <label class="plan-label">{{ $t('maturity.results.businessEffect') }}</label>
                <textarea v-model="item.business_impact" class="plan-input" rows="2" />
                <label class="plan-label">{{ $t('maturity.results.customerEffect') }}</label>
                <textarea v-model="item.customer_impact" class="plan-input" rows="2" />
              </div>
            </article>
            <button type="button" class="btn-rec" @click="addDontKnowInitiative">{{ $t('maturity.results.addInitiative') }}</button>
          </div>
          <div v-if="dontKnowHtml" v-html="dontKnowHtml" class="rec-html"></div>
        </div>
      </div>

      <div class="actions">
        <button type="button" class="btn-edit" @click="$router.push(`${maturityBase}/edit`)">
          {{ $t('maturity.results.changeAnswers') }}
        </button>
        <button type="button" class="btn-show-all" @click="showAllModal = true">
          {{ $t('maturity.results.showAll') }}
        </button>
        <button
          type="button"
          class="btn-rec"
          :disabled="loadingRecs"
          @click="fetchRecommendations"
        >
          {{ loadingRecs ? $t('maturity.generatingRecs') : $t('maturity.getRecommendations') }}
        </button>
        <button type="button" class="btn-pdf" :disabled="exporting" @click="exportPdf">
          {{ exporting ? $t('maturity.exporting') : $t('maturity.downloadPdf') }}
        </button>
      </div>

      <Teleport to="body">
        <!-- Модальное окно: карточки вопросов и ответов по выбранной теме -->
        <div v-if="selectedTheme" class="detail-overlay" @click.self="selectedTheme = null">
          <div class="detail-modal">
            <div class="detail-header">
              <h3>{{ displayThemeName(selectedTheme) }}</h3>
              <div class="detail-header-actions">
                <button type="button" class="btn-pdf-modal" :disabled="modalExporting" @click="exportThemePdf">
                  {{ modalExporting ? $t('maturity.results.exportingShort') : $t('maturity.results.downloadPdfShort') }}
                </button>
                <button type="button" class="detail-close" :aria-label="$t('maturity.results.closeAria')" @click="selectedTheme = null">×</button>
              </div>
            </div>
            <div ref="themeModalCards" class="detail-cards">
              <div
                v-for="item in questionsForTheme(selectedTheme)"
                :key="item.id"
                class="detail-card"
              >
                <p class="detail-question">{{ item.text }}</p>
                <div class="detail-answer" :class="item.answerClass">
                  {{ item.answerLabel }}
                </div>
                <div v-if="item.why_important" class="detail-why">
                  <strong>{{ $t('maturity.whyImportantLabel') }}</strong> {{ item.why_important }}
                </div>
                <div v-if="item.metrics_impact" class="detail-metrics">
                  <strong>{{ $t('maturity.metricsImpactTitle') }}:</strong> {{ item.metrics_impact }}
                </div>
                <div v-if="item.negative_for_business" class="detail-negative">
                  <strong>{{ $t('maturity.negativeIfWeakTitle') }}:</strong> {{ item.negative_for_business }}
                </div>
                <div v-if="item.business_metrics" class="detail-business-metrics">
                  <strong>{{ $t('maturity.businessMetricsTitle') }}:</strong> {{ item.business_metrics }}
                  <p v-if="businessMetricsDisclaimer" class="detail-disclaimer">{{ businessMetricsDisclaimer }}</p>
                </div>
                <div v-if="item.comment" class="detail-comment">
                  <strong>{{ $t('maturity.commentLabel') }}:</strong> {{ item.comment }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Модальное окно: все вопросы и ответы -->
        <div v-if="showAllModal" class="detail-overlay" @click.self="showAllModal = false">
          <div class="detail-modal detail-modal-full">
            <div class="detail-header">
              <h3>{{ $t('maturity.results.allQuestionsTitle') }}</h3>
              <div class="detail-header-actions">
                <button type="button" class="btn-pdf-modal" :disabled="modalExporting" @click="exportAllQuestionsPdf">
                  {{ modalExporting ? $t('maturity.results.exportingShort') : $t('maturity.results.downloadPdfShort') }}
                </button>
                <button type="button" class="detail-close" :aria-label="$t('maturity.results.closeAria')" @click="showAllModal = false">×</button>
              </div>
            </div>
            <div ref="allModalCards" class="detail-cards detail-cards-full">
              <p v-if="!allQuestionsWithAnswers.length" class="detail-empty">{{ $t('maturity.results.noQuestionData') }}</p>
              <div
                v-for="item in allQuestionsWithAnswers"
                :key="item.id"
                class="detail-card"
              >
                <p class="detail-question"><span class="detail-q-num">{{ item.id + 1 }}.</span> {{ item.text }}</p>
                <div class="detail-answer" :class="item.answerClass">
                  {{ item.answerLabel }}
                </div>
                <div v-if="item.why_important" class="detail-why">
                  <strong>{{ $t('maturity.whyImportantLabel') }}</strong> {{ item.why_important }}
                </div>
                <div v-if="item.metrics_impact" class="detail-metrics">
                  <strong>{{ $t('maturity.metricsImpactTitle') }}:</strong> {{ item.metrics_impact }}
                </div>
                <div v-if="item.negative_for_business" class="detail-negative">
                  <strong>{{ $t('maturity.negativeIfWeakTitle') }}:</strong> {{ item.negative_for_business }}
                </div>
                <div v-if="item.business_metrics" class="detail-business-metrics">
                  <strong>{{ $t('maturity.businessMetricsTitle') }}:</strong> {{ item.business_metrics }}
                  <p v-if="businessMetricsDisclaimer" class="detail-disclaimer">{{ businessMetricsDisclaimer }}</p>
                </div>
                <div v-if="item.comment" class="detail-comment">
                  <strong>{{ $t('maturity.commentLabel') }}:</strong> {{ item.comment }}
                </div>
              </div>
            </div>
          </div>
        </div>
      </Teleport>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import RadarChart from '@/components/RadarChart.vue';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

function emptyTeamPlan() {
  return { diagnosis: '', initiatives: [], roadmap: [], risks: [] };
}

function normalizeTeamPlan(plan) {
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
    roadmap: Array.isArray(src.roadmap) ? src.roadmap : [],
    risks: Array.isArray(src.risks) ? src.risks : []
  };
}

export default {
  name: 'MaturityResults',
  components: { RadarChart },
  props: {
    variant: { type: String, default: 'legacy' },
  },
  data() {
    return {
      token: '',
      teamName: '',
      completedAt: null,
      results: {},
      radarGroups: [],
      answers: [],
      comments: [],
      questions: [],
      selectedTheme: null,
      showAllModal: false,
      loading: true,
      error: null,
      exporting: false,
      recommendationsHtml: '',
      loadingRecs: false,
      dontKnowHtml: '',
      loadingDontKnowRecs: false,
      editingRecommendations: false,
      savingRecommendations: false,
      recommendationsPlan: emptyTeamPlan(),
      teamInitiativeCollapsed: {},
      editingDontKnow: false,
      savingDontKnow: false,
      dontKnowPlan: emptyTeamPlan(),
      dontKnowInitiativeCollapsed: {},
      modalExporting: false,
      businessMetricsDisclaimer: '',
      businessMetricsGlossary: [],
      aiUsageRemaining: null,
      teamComparison: null
    };
  },
  computed: {
    hasDontKnow() {
      if (!Array.isArray(this.answers)) return false;
      return this.answers.some((a) => a === 'dont_know');
    },
    questionsByTheme() {
      const map = {};
      if (!this.questions.length || !Array.isArray(this.answers)) return map;
      for (const q of this.questions) {
        if (!map[q.theme]) map[q.theme] = [];
        const raw = this.answers[q.id];
        map[q.theme].push({
          ...q,
          answerRaw: raw,
          answerLabel: this.formatAnswerLabel(raw),
          answerClass: this.answerCssClass(raw),
          comment: (Array.isArray(this.comments) && this.comments[q.id]) ? this.comments[q.id] : ''
        });
      }
      return map;
    },
    allQuestionsWithAnswers() {
      const questions = this.questions || [];
      const answers = Array.isArray(this.answers) ? this.answers : [];
      const comments = Array.isArray(this.comments) ? this.comments : [];
      if (!questions.length) return [];
      return questions.map(q => {
        const raw = answers[q.id];
        return {
          ...q,
          answerRaw: raw,
          answerLabel: this.formatAnswerLabel(raw),
          answerClass: this.answerCssClass(raw),
          comment: comments[q.id] || ''
        };
      });
    },
    averageScore() {
      if (!this.results || !Object.keys(this.results).length) return 0;
      let total = 0;
      let count = 0;
      for (const cat of Object.values(this.results)) {
        const vals = Object.values(cat).map((v) => parseFloat(v) || 0);
        total += vals.reduce((a, b) => a + b, 0); // 0..3 по теме
        count++;
      }
      return count ? total / count : 0;
    },
    formattedDate() {
      if (!this.completedAt) return '';
      const locTag = this.surveyLang === 'en' ? 'en-US' : 'ru-RU';
      try {
        return new Date(this.completedAt).toLocaleDateString(locTag, {
          day: 'numeric',
          month: 'long',
          year: 'numeric'
        });
      } catch {
        return this.completedAt;
      }
    },
    maturityBase() {
      return this.variant === 'new' ? `/new/maturity/${this.token}` : `/maturity/${this.token}`;
    },
    surveyLang() {
      try {
        const loc = this.$i18n?.locale;
        const s = typeof loc === 'string' ? loc : loc?.value;
        return s === 'en' ? 'en' : 'ru';
      } catch (_e) {
        return typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en' ? 'en' : 'ru';
      }
    },
  },
  async mounted() {
    this.token = this.$route.params.token;
    await this.loadResults();
    await this.loadTeamComparison();
    await this.fetchAiUsage();
  },
  watch: {
    selectedTheme() {
      this.syncBodyScrollLock();
    },
    showAllModal() {
      this.syncBodyScrollLock();
    }
  },
  beforeUnmount() {
    document.body.style.overflow = '';
  },
  methods: {
    displayThemeName(ruKey) {
      if (ruKey == null || ruKey === '') return '';
      const tm = this.$i18n?.global?.tm;
      if (typeof tm !== 'function') return ruKey;
      const tl = tm('maturity.themeLabels') || {};
      const rg = tm('maturity.radarGroupLabels') || {};
      if (tl && typeof tl === 'object' && tl[ruKey]) return tl[ruKey];
      if (rg && typeof rg === 'object' && rg[ruKey]) return rg[ruKey];
      return ruKey;
    },
    syncBodyScrollLock() {
      document.body.style.overflow = this.selectedTheme || this.showAllModal ? 'hidden' : '';
    },
    chartDataForGroup(group) {
      if (!group || !group.categories || !this.results) {
        return { labels: [], datasets: [] };
      }
      const labels = [];
      const managerData = [];
      const teamRes = this.teamComparison && this.teamComparison.team_results;
      const teamData = [];
      for (const cat of group.categories) {
        const subs = this.results[cat];
        if (!subs) continue;
        const vals = Object.values(subs).map(v => parseFloat(v) || 0);
        const score = vals.reduce((a, b) => a + b, 0);
        labels.push(this.displayThemeName(cat));
        managerData.push(score);
        if (teamRes && teamRes[cat]) {
          const tv = Object.values(teamRes[cat]).map(v => parseFloat(v) || 0);
          teamData.push(tv.reduce((a, b) => a + b, 0));
        } else {
          teamData.push(0);
        }
      }
      const datasets = [
        {
          label: this.$t('maturity.radarDatasetManager'),
          data: managerData,
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          borderColor: 'rgba(75, 192, 192, 1)',
          borderWidth: 2
        }
      ];
      if (teamRes && this.teamComparison.submission_count > 0) {
        datasets.push({
          label: this.$t('maturity.radarDatasetTeam'),
          data: teamData,
          backgroundColor: 'rgba(153, 102, 255, 0.2)',
          borderColor: 'rgba(153, 102, 255, 1)',
          borderWidth: 2
        });
      }
      return { labels, datasets };
    },
    async loadResults() {
      try {
        const res = await axios.get(`/api/maturity/${this.token}/results`, {
          params: { lang: this.surveyLang }
        });
        this.teamName = res.data.team_name;
        this.completedAt = res.data.completed_at;
        this.results = res.data.results || {};
        this.radarGroups = res.data.radar_groups || [];
        this.answers = res.data.answers || [];
        this.comments = res.data.comments || [];
        this.questions = res.data.questions || [];
        this.businessMetricsDisclaimer = res.data.business_metrics_disclaimer || '';
        this.businessMetricsGlossary = res.data.business_metrics_glossary || [];
        this.recommendationsHtml = res.data.recommendations_html || '';
        this.recommendationsPlan = normalizeTeamPlan(res.data.recommendations_plan);
        this.dontKnowHtml = res.data.dont_know_recommendations_html || '';
        this.dontKnowPlan = normalizeTeamPlan(res.data.dont_know_recommendations_plan);
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('maturity.results.loadResultsError');
      } finally {
        this.loading = false;
      }
    },
    async loadTeamComparison() {
      const auth = localStorage.getItem('token');
      if (!auth) return;
      try {
        const res = await axios.get(`/api/maturity/${this.token}/team-comparison`, {
          headers: { Authorization: `Bearer ${auth}` },
          params: { lang: this.surveyLang }
        });
        this.teamComparison = res.data;
      } catch (_e) {
        this.teamComparison = null;
      }
    },
    themesInGroup(group) {
      if (!group || !group.categories || !this.results) return [];
      return group.categories
        .filter(cat => this.results[cat])
        .map(cat => {
          const vals = Object.values(this.results[cat]).map(v => parseFloat(v) || 0);
          const score = vals.reduce((a, b) => a + b, 0); // 0..3
          return { theme: cat, avg: score };
        });
    },
    questionsForTheme(theme) {
      return this.questionsByTheme[theme] || [];
    },
    formatAnswerLabel(raw) {
      if (raw === true) return this.$t('maturity.yes');
      if (raw === false) return this.$t('maturity.no');
      if (raw === 'yes') return this.$t('maturity.yes');
      if (raw === 'no') return this.$t('maturity.no');
      if (raw === 'rather_yes') return this.$t('maturity.ratherYes');
      if (raw === 'rather_no') return this.$t('maturity.ratherNo');
      if (raw === 'dont_know') return this.$t('maturity.dontKnow');
      return this.$t('maturity.dontKnow');
    },
    answerCssClass(raw) {
      if (raw === true || raw === 'yes') return 'answer-yes';
      if (raw === false || raw === 'no') return 'answer-no';
      if (raw === 'rather_yes') return 'answer-rather-yes';
      if (raw === 'rather_no') return 'answer-rather-no';
      return 'answer-dont-know';
    },
    openDetail(theme) {
      this.selectedTheme = theme;
    },
    formatScore(avg) {
      return avg != null ? avg.toFixed(1) : '—';
    },
    scoreClass(avg) {
      if (avg >= 2.5) return 'score-high';
      if (avg >= 1.5) return 'score-mid';
      return 'score-low';
    },
    async fetchRecommendations() {
      if (this.loadingRecs) return;
      this.loadingRecs = true;
      this.recommendationsHtml = '';
      try {
        const res = await axios.post(`/api/maturity/${this.token}/recommendations`);
        this.recommendationsHtml = res.data.content || '';
        this.recommendationsPlan = normalizeTeamPlan(res.data.plan);
        this.editingRecommendations = false;
        await this.fetchAiUsage();
      } catch (e) {
        this.recommendationsHtml = '<p class="rec-error">' + (e.response?.data?.error || this.$t('maturity.results.recsLoadError')) + '</p>';
      } finally {
        this.loadingRecs = false;
      }
    },
    async fetchDontKnowRecommendations() {
      if (this.loadingDontKnowRecs) return;
      this.loadingDontKnowRecs = true;
      this.dontKnowHtml = '';
      try {
        const res = await axios.post(`/api/maturity/${this.token}/recommendations/dont-know`);
        this.dontKnowHtml = res.data.content || '';
        this.dontKnowPlan = normalizeTeamPlan(res.data.plan);
        this.editingDontKnow = false;
        await this.fetchAiUsage();
      } catch (e) {
        this.dontKnowHtml = '<p class="rec-error">' + (e.response?.data?.error || this.$t('maturity.results.errorGeneric')) + '</p>';
      } finally {
        this.loadingDontKnowRecs = false;
      }
    },
    async saveRecommendations() {
      if (this.savingRecommendations) return;
      this.savingRecommendations = true;
      try {
        const payload = {
          plan: normalizeTeamPlan(this.recommendationsPlan),
          content: this.recommendationsHtml || ''
        };
        const res = await axios.put(`/api/maturity/${this.token}/recommendations`, payload);
        this.recommendationsHtml = res.data?.content || this.recommendationsHtml;
        this.recommendationsPlan = normalizeTeamPlan(res.data?.plan);
        this.editingRecommendations = false;
      } catch (e) {
        alert(e.response?.data?.error || this.$t('maturity.results.saveRecsError'));
      } finally {
        this.savingRecommendations = false;
      }
    },
    isTeamInitiativeCollapsed(idx) {
      return !!this.teamInitiativeCollapsed[idx];
    },
    toggleTeamInitiativeCollapse(idx) {
      this.teamInitiativeCollapsed = {
        ...this.teamInitiativeCollapsed,
        [idx]: !this.teamInitiativeCollapsed[idx]
      };
    },
    syncPlanSteps(item, e) {
      const raw = e.target?.value ?? '';
      item.steps = raw.split('\n').map((s) => s.trimEnd());
    },
    addTeamInitiative() {
      this.recommendationsPlan.initiatives.push({
        title: '',
        objective: '',
        owner: '',
        success_metric: '',
        business_impact: '',
        customer_impact: '',
        steps: []
      });
    },
    removeTeamInitiative(idx) {
      this.recommendationsPlan.initiatives.splice(idx, 1);
      this.teamInitiativeCollapsed = Object.fromEntries(
        Object.entries(this.teamInitiativeCollapsed).filter(([k]) => Number(k) !== idx)
      );
    },
    async saveDontKnowRecommendations() {
      if (this.savingDontKnow) return;
      this.savingDontKnow = true;
      try {
        const payload = {
          plan: normalizeTeamPlan(this.dontKnowPlan),
          content: this.dontKnowHtml || ''
        };
        const res = await axios.put(`/api/maturity/${this.token}/recommendations/dont-know`, payload);
        this.dontKnowHtml = res.data?.content || this.dontKnowHtml;
        this.dontKnowPlan = normalizeTeamPlan(res.data?.plan);
        this.editingDontKnow = false;
      } catch (e) {
        alert(e.response?.data?.error || this.$t('maturity.results.saveRecsError'));
      } finally {
        this.savingDontKnow = false;
      }
    },
    isDontKnowInitiativeCollapsed(idx) {
      return !!this.dontKnowInitiativeCollapsed[idx];
    },
    toggleDontKnowInitiativeCollapse(idx) {
      this.dontKnowInitiativeCollapsed = {
        ...this.dontKnowInitiativeCollapsed,
        [idx]: !this.dontKnowInitiativeCollapsed[idx]
      };
    },
    addDontKnowInitiative() {
      this.dontKnowPlan.initiatives.push({
        title: '',
        objective: '',
        owner: '',
        success_metric: '',
        business_impact: '',
        customer_impact: '',
        steps: []
      });
    },
    removeDontKnowInitiative(idx) {
      this.dontKnowPlan.initiatives.splice(idx, 1);
      this.dontKnowInitiativeCollapsed = Object.fromEntries(
        Object.entries(this.dontKnowInitiativeCollapsed).filter(([k]) => Number(k) !== idx)
      );
    },
    async exportPdf() {
      if (this.exporting) return;
      const el = this.$refs.pdfContent;
      if (!el) return;
      this.exporting = true;
      try {
        const canvas = await html2canvas(el, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff'
        });
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
        const dateStr = this.formattedDate.replace(/\s/g, '-') || 'report';
        const name = (this.teamName || 'maturity').replace(/[^\w\s-]/g, '').slice(0, 30);
        const fname = this.$t('maturity.results.pdfFilename', { name, date: dateStr });
        pdf.save(fname);
      } catch (e) {
        console.error(e);
        alert(this.$t('maturity.pdfError'));
      } finally {
        this.exporting = false;
      }
    },
    async exportElementToPdf(el, filePrefix) {
      if (!el) return;
      this.modalExporting = true;
      try {
        const canvas = await html2canvas(el, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff'
        });
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
        pdf.save(`${filePrefix}-${this.token || 'report'}.pdf`);
      } catch (e) {
        console.error(e);
        alert(this.$t('maturity.pdfError'));
      } finally {
        this.modalExporting = false;
      }
    },
    async exportThemePdf() {
      const slug = (this.selectedTheme || 'theme').replace(/[^\w\s-]/g, '').trim() || 'theme';
      await this.exportElementToPdf(this.$refs.themeModalCards, `${this.$t('maturity.results.pdfThemePrefix')}-${slug}`);
    },
    async exportAllQuestionsPdf() {
      await this.exportElementToPdf(this.$refs.allModalCards, this.$t('maturity.results.pdfAllPrefix'));
    },
    async fetchAiUsage() {
      try {
        const { data } = await axios.get('/api/ai-usage', { params: { survey_token: this.token } });
        this.aiUsageRemaining = data?.remaining ?? null;
      } catch {
        this.aiUsageRemaining = null;
      }
    }
  }
};
</script>

<style scoped>
.maturity-results {
  max-width: 900px;
  margin: 2rem auto;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.loading, .error {
  text-align: center;
  padding: 2rem;
}

.error { color: #c00; }

.results-title {
  font-size: 1.5rem;
  color: #111;
  margin-bottom: 0.5rem;
}

.pdf-block {
  background: #fff;
  padding: 1.5rem;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
}

.meta {
  color: #6b7280;
  margin-bottom: 1rem;
}

.meta .team { font-weight: 600; color: #111; }
.meta .date { margin-left: 1rem; }

.average-line {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
}

.team-comparison-hint {
  margin: -0.75rem 0 1.25rem;
  font-size: 0.95rem;
  color: #5b21b6;
}

.ai-usage-line {
  margin: -0.5rem 0 1.2rem;
  color: #475569;
  font-size: 0.92rem;
}

.group-block {
  margin: 1.5rem 0;
  overflow: visible;
}

.radar-wrap {
  margin-bottom: 0.75rem;
  height: 770px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.themes-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-top: 0.5rem;
  min-height: 3rem;
}

.theme-row {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  font-size: 0.875rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
}

.theme-row:hover {
  background: #e0f2fe;
  border-color: #7dd3fc;
}

.theme-name {
  color: #334155;
}

.theme-score {
  font-weight: 600;
  min-width: 2rem;
  text-align: right;
}

.theme-score.score-high { color: #059669; }
.theme-score.score-mid { color: #d97706; }
.theme-score.score-low { color: #dc2626; }

/* Модальное окно с карточками вопросов/ответов */
.detail-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 1rem;
}

.detail-modal {
  background: #fff;
  border-radius: 12px;
  max-width: 640px;
  width: 100%;
  max-height: 90vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}
.detail-modal-full {
  max-width: 800px;
  max-height: 95vh;
}
.detail-cards-full {
  min-height: 200px;
}
.detail-empty {
  padding: 2rem;
  color: #6b7280;
  margin: 0;
}
.detail-q-num {
  color: #6b7280;
  margin-right: 0.25rem;
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e5e7eb;
  background: #f9fafb;
}

.detail-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-pdf-modal {
  padding: 0.45rem 0.8rem;
  border: none;
  border-radius: 8px;
  background: #2563eb;
  color: #fff;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-pdf-modal:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.detail-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #111;
}

.detail-close {
  width: 2rem;
  height: 2rem;
  padding: 0;
  font-size: 1.5rem;
  line-height: 1;
  color: #6b7280;
  background: none;
  border: none;
  cursor: pointer;
  border-radius: 6px;
}

.detail-close:hover {
  background: #e5e7eb;
  color: #111;
}

.detail-cards {
  overflow-y: auto;
  padding: 1rem 1.25rem;
}

.detail-card {
  padding: 1rem;
  margin-bottom: 1rem;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}

.detail-card:last-child {
  margin-bottom: 0;
}

.detail-question {
  font-weight: 600;
  color: #111;
  margin: 0 0 0.5rem 0;
  font-size: 0.9375rem;
}

.detail-answer {
  display: inline-block;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.detail-answer.answer-yes {
  background: #d1fae5;
  color: #065f46;
}

.detail-answer.answer-no {
  background: #fee2e2;
  color: #991b1b;
}

.detail-answer.answer-dont-know {
  background: #e2e8f0;
  color: #334155;
}

.detail-answer.answer-rather-no {
  background: #ffedd5;
  color: #9a3412;
}

.detail-answer.answer-rather-yes {
  background: #ecfccb;
  color: #3f6212;
}

.dont-know-rec-block .rec-hint {
  font-size: 0.9rem;
  color: #64748b;
  margin: 0 0 0.75rem 0;
}

.detail-why,
.detail-metrics,
.detail-negative {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #4b5563;
  margin: 0.5rem 0 0 0;
}

.detail-why strong,
.detail-metrics strong,
.detail-negative strong {
  color: #374151;
}

.detail-business-metrics {
  margin-top: 0.5rem;
  font-size: 0.8125rem;
  color: #713f12;
  background: #fefce8;
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
}
.detail-disclaimer {
  font-size: 0.75rem;
  color: #6b7280;
  font-style: italic;
  margin: 0.35rem 0 0 0;
}

.detail-comment {
  font-size: 0.8125rem;
  line-height: 1.5;
  color: #334155;
  margin: 0.5rem 0 0 0;
  background: #eff6ff;
  border-left: 3px solid #3b82f6;
  padding: 0.5rem 0.75rem;
  border-radius: 0 6px 6px 0;
}

.detail-comment strong {
  color: #1d4ed8;
}

.recommendations-block {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e5e7eb;
}
.rec-actions {
  display: flex;
  gap: 8px;
  margin: 10px 0;
  flex-wrap: wrap;
}
.rec-editor {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 10px;
  margin-bottom: 10px;
  box-sizing: border-box;
  font-family: inherit;
}
.group-plan-editor {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
  margin-bottom: 12px;
  background: #f8fafc;
}
.plan-label {
  display: block;
  margin: 8px 0 6px;
  font-size: 12px;
  color: #374151;
  font-weight: 600;
  text-transform: uppercase;
}
.plan-input {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  padding: 8px 10px;
  box-sizing: border-box;
  font-family: inherit;
}
.initiative-card {
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  padding: 10px;
  margin-bottom: 10px;
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

.rec-title {
  font-size: 1.2rem;
  margin-bottom: 1rem;
  color: #111;
}

.rec-html {
  font-size: 0.95rem;
  line-height: 1.6;
  color: #374151;
}

.rec-html :deep(p) { margin-bottom: 0.75rem; }
.rec-html :deep(ul) { margin: 0.5rem 0 1rem 1.5rem; }
.rec-html :deep(li) { margin-bottom: 0.25rem; }
.rec-error { color: #c00; }

.actions {
  margin-top: 1.5rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.btn-edit, .btn-show-all, .btn-rec, .btn-pdf {
  padding: 0.75rem 1.5rem;
  color: #fff;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
}

.btn-edit {
  background: #64748b;
}
.btn-edit:hover { background: #475569; }

.btn-show-all {
  background: #0d9488;
}
.btn-show-all:hover { background: #0f766e; }

.btn-rec {
  background: #059669;
}

.btn-rec:hover:not(:disabled) { background: #047857; }

.btn-pdf {
  background: #2563eb;
}

.btn-pdf:hover:not(:disabled) { background: #1d4ed8; }

.btn-rec:disabled, .btn-pdf:disabled { opacity: 0.6; cursor: not-allowed; }

/* —— New UI (/new/maturity/.../results) —— */
.maturity-results.maturity-results--new {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px 16px 48px;
}

.maturity-results--new .results-content {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 22px 70px rgba(10, 20, 45, 0.08);
  padding: 20px 18px 28px;
}

.maturity-results--new .results-title {
  color: rgba(10, 20, 45, 0.92);
}

.maturity-results--new .btn-edit,
.maturity-results--new .btn-show-all,
.maturity-results--new .btn-rec,
.maturity-results--new .btn-pdf {
  border-radius: 12px;
  box-shadow: 0 8px 22px rgba(10, 20, 45, 0.08);
  transition: transform 0.18s ease, filter 0.18s ease;
}

.maturity-results--new .btn-edit:hover,
.maturity-results--new .btn-show-all:hover,
.maturity-results--new .btn-rec:hover:not(:disabled),
.maturity-results--new .btn-pdf:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.05);
}

.maturity-results--new .btn-pdf {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
}

.maturity-results--new .results-content {
  position: relative;
  overflow: hidden;
  backdrop-filter: blur(8px);
}

.maturity-results--new .results-content::before {
  content: "";
  position: absolute;
  top: -120%;
  left: -26%;
  width: 36%;
  height: 320%;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.36), transparent);
  transform: rotate(16deg);
  animation: resultsShine 9s linear infinite;
  pointer-events: none;
}

.maturity-results--new .group-block {
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 16px;
  padding: 14px;
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.9), rgba(246, 249, 255, 0.85));
  box-shadow: 0 16px 42px rgba(10, 20, 45, 0.08);
}

.maturity-results--new .theme-row {
  border-radius: 11px;
  border-color: rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.88);
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.maturity-results--new .theme-row:hover {
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.3);
  box-shadow: 0 10px 24px rgba(32, 90, 255, 0.12);
}

.maturity-results--new .detail-modal {
  border-radius: 16px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(246, 249, 255, 0.95));
}

.maturity-results--new .detail-card {
  border-radius: 12px;
  border-color: rgba(10, 20, 45, 0.11);
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 20px rgba(10, 20, 45, 0.07);
}

.maturity-results--new .recommendations-block {
  border-top-color: rgba(10, 20, 45, 0.12);
}

.maturity-results--new .btn-edit,
.maturity-results--new .btn-show-all,
.maturity-results--new .btn-rec,
.maturity-results--new .btn-pdf {
  position: relative;
  overflow: hidden;
}

.maturity-results--new .btn-edit::after,
.maturity-results--new .btn-show-all::after,
.maturity-results--new .btn-rec::after,
.maturity-results--new .btn-pdf::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 20%, rgba(255, 255, 255, 0.34), transparent 80%);
  transform: translateX(-125%);
  transition: transform 0.6s ease;
}

.maturity-results--new .btn-edit:hover::after,
.maturity-results--new .btn-show-all:hover::after,
.maturity-results--new .btn-rec:hover::after,
.maturity-results--new .btn-pdf:hover::after {
  transform: translateX(125%);
}

@keyframes resultsShine {
  0% {
    transform: translateX(-220px) rotate(16deg);
  }
  45%,
  100% {
    transform: translateX(1050px) rotate(16deg);
  }
}
</style>
