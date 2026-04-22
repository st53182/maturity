<template>
  <div class="mvp-play">
    <header class="mvp-play__top">
      <div class="mvp-play__brand">
        <span class="mvp-play__icon">🚀</span>
        <div>
          <div class="mvp-play__brand-title">{{ $t('agileTraining.mvp.playTitle') }}</div>
          <div class="mvp-play__brand-sub" v-if="group">{{ group.name }}</div>
        </div>
      </div>
      <div class="mvp-play__lang">
        <button
          type="button"
          class="mvp-lang__btn"
          :class="{ 'is-active': locale === 'ru' }"
          @click="setLocale('ru')"
        >RU</button>
        <button
          type="button"
          class="mvp-lang__btn"
          :class="{ 'is-active': locale === 'en' }"
          @click="setLocale('en')"
        >EN</button>
      </div>
    </header>

    <div v-if="loading" class="mvp-play__loading">{{ $t('common.loading') }}…</div>

    <!-- Start screen -->
    <section v-else-if="step === 'start'" class="mvp-card mvp-card--center">
      <h1 class="mvp-card__title">{{ $t('agileTraining.mvp.startTitle') }}</h1>
      <p class="mvp-card__lead">{{ $t('agileTraining.mvp.startLead') }}</p>
      <ul class="mvp-card__how">
        <li><b>MVP</b> — {{ $t('agileTraining.mvp.defMvp') }}</li>
        <li><b>MMP</b> — {{ $t('agileTraining.mvp.defMmp') }}</li>
        <li><b>MLP</b> — {{ $t('agileTraining.mvp.defMlp') }}</li>
      </ul>
      <label class="mvp-start__name">
        <span>{{ $t('agileTraining.common.yourName') }}</span>
        <input v-model="displayName" maxlength="60" :placeholder="$t('agileTraining.common.yourNamePh')" />
      </label>
      <button class="mvp-btn mvp-btn--primary" @click="startRun">{{ $t('agileTraining.mvp.start') }}</button>
    </section>

    <!-- Case picker -->
    <section v-else-if="step === 'cases'" class="mvp-card">
      <h2 class="mvp-card__title">{{ $t('agileTraining.mvp.pickCase') }}</h2>
      <p class="mvp-card__lead">{{ $t('agileTraining.mvp.pickCaseLead') }}</p>
      <ul class="mvp-cases">
        <li v-for="c in cases" :key="c.key" class="mvp-case">
          <div class="mvp-case__info">
            <div class="mvp-case__head">
              <span class="mvp-case__cat">{{ c.category }}</span>
              <span class="mvp-case__status" v-if="caseStatus(c.key)">
                {{ caseStatus(c.key) }}
              </span>
            </div>
            <h3>{{ c.title }}</h3>
            <p class="mvp-case__hyp">💡 {{ c.hypothesis }}</p>
          </div>
          <button class="mvp-btn mvp-btn--primary" @click="pickCase(c.key)">
            {{ caseHasProgress(c.key) ? $t('agileTraining.mvp.continueCase') : $t('agileTraining.mvp.startCase') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- Hypothesis intro -->
    <section v-else-if="step === 'hypothesis' && activeCase" class="mvp-card">
      <div class="mvp-card__head">
        <span class="mvp-case__cat">{{ activeCase.category }}</span>
        <h2>{{ activeCase.title }}</h2>
      </div>
      <div class="mvp-hyp">
        <div class="mvp-hyp__label">{{ $t('agileTraining.mvp.hypothesisLabel') }}</div>
        <div class="mvp-hyp__text">«{{ activeCase.hypothesis }}»</div>
      </div>
      <h4>{{ $t('agileTraining.mvp.context') }}</h4>
      <ul class="mvp-context">
        <li v-for="(c, i) in activeCase.context" :key="'ctx-'+i">{{ c }}</li>
      </ul>
      <div class="mvp-card__actions">
        <button class="mvp-btn mvp-btn--ghost" @click="goBackToCases">← {{ $t('agileTraining.mvp.backToCases') }}</button>
        <button class="mvp-btn mvp-btn--primary" @click="goToStage('mvp')">
          {{ $t('agileTraining.mvp.assembleMvp') }} →
        </button>
      </div>
    </section>

    <!-- Stage: select features -->
    <section v-else-if="step === 'stage' && activeCase" class="mvp-card">
      <div class="mvp-card__head">
        <span :class="['mvp-stage-badge', 'mvp-stage-badge--'+stage]">{{ $t('agileTraining.mvp.stage.'+stage) }}</span>
        <h2>{{ stageTitle }}</h2>
      </div>
      <p class="mvp-card__lead">{{ stageBrief }}</p>
      <div class="mvp-counter">
        <div class="mvp-counter__text">
          {{ $t('agileTraining.mvp.selectedOf', { n: selectedInStage.length, max: stageLimit }) }}
        </div>
        <div class="mvp-counter__bar">
          <div class="mvp-counter__fill" :style="{ width: (selectedInStage.length / stageLimit * 100) + '%' }" />
        </div>
      </div>
      <div v-if="previouslyLocked.length" class="mvp-lockeds">
        <div class="mvp-lockeds__title">{{ $t('agileTraining.mvp.alreadyIn') }}</div>
        <div class="mvp-lockeds__chips">
          <span v-for="lf in previouslyLockedFeatures" :key="'lkd-'+lf.key"
                class="mvp-feat-chip mvp-feat-chip--locked">
            🔒 {{ lf.title }}
          </span>
        </div>
      </div>
      <ul class="mvp-features-grid">
        <li
          v-for="f in activeCase.features"
          :key="f.key"
          :class="[
            'mvp-feature',
            'mvp-feature--' + f.weight,
            {
              'is-selected': isSelected(f.key),
              'is-locked': isLocked(f.key),
              'is-disabled': !isSelected(f.key) && !isLocked(f.key) && selectedInStage.length >= stageLimit,
            }
          ]"
          @click="toggleFeature(f.key)"
        >
          <div class="mvp-feature__head">
            <span :class="['mvp-feat-tag', 'mvp-feat-tag--'+f.weight]">{{ $t('agileTraining.mvp.weight.'+f.weight) }}</span>
            <span v-if="isLocked(f.key)" class="mvp-feature__lock">🔒</span>
            <span v-else-if="isSelected(f.key)" class="mvp-feature__check">✓</span>
          </div>
          <div class="mvp-feature__title">{{ f.title }}</div>
          <div class="mvp-feature__desc">{{ f.desc }}</div>
        </li>
      </ul>
      <div class="mvp-card__actions">
        <button class="mvp-btn mvp-btn--ghost" @click="goBackFromStage">← {{ $t('agileTraining.common.back') }}</button>
        <button
          class="mvp-btn mvp-btn--primary"
          :disabled="selectedInStage.length === 0 || submitting"
          @click="submitStage"
        >
          {{ submitting ? $t('common.loading') + '…' : $t('agileTraining.mvp.checkResult') }}
        </button>
      </div>
    </section>

    <!-- Stage result -->
    <section v-else-if="step === 'result' && stageResult && activeCase" class="mvp-card">
      <div class="mvp-card__head">
        <span :class="['mvp-stage-badge', 'mvp-stage-badge--'+stage]">{{ $t('agileTraining.mvp.stage.'+stage) }}</span>
        <h2>{{ $t('agileTraining.mvp.resultTitle') }}</h2>
      </div>

      <div :class="['mvp-verdict', 'mvp-verdict--'+stageResult.status]">
        <div class="mvp-verdict__icon">
          {{ stageResult.status === 'success' ? '✅' : stageResult.status === 'partial' ? '⚠️' : '❌' }}
        </div>
        <div class="mvp-verdict__body">
          <div class="mvp-verdict__title">{{ stageVerdictTitle }}</div>
          <div class="mvp-verdict__reaction">{{ stageReactionText }}</div>
        </div>
      </div>

      <div v-if="stageResult.antipatterns && stageResult.antipatterns.length" class="mvp-aps">
        <div class="mvp-aps__title">⚡ {{ $t('agileTraining.mvp.antipatterns') }}</div>
        <ul>
          <li v-for="ap in stageResult.antipatterns" :key="ap">
            {{ $t('agileTraining.mvp.ap.' + ap) }}
          </li>
        </ul>
      </div>

      <div v-if="stageResult.hint_keys && stageResult.hint_keys.length" class="mvp-hints">
        <div class="mvp-hints__title">💡 {{ $t('agileTraining.mvp.hintsTitle') }}</div>
        <div class="mvp-hints__chips">
          <span v-for="k in stageResult.hint_keys" :key="'hint-'+k" class="mvp-feat-chip mvp-feat-chip--hint">
            {{ featureTitle(k) }}
          </span>
        </div>
      </div>

      <div class="mvp-picks">
        <div class="mvp-picks__title">{{ $t('agileTraining.mvp.yourPicks') }}</div>
        <div class="mvp-picks__chips">
          <span v-for="k in stageResult.selected" :key="'sel-'+k"
                :class="['mvp-feat-chip', 'mvp-feat-chip--' + featureWeight(k)]">
            {{ featureTitle(k) }}
          </span>
        </div>
      </div>

      <div class="mvp-card__actions">
        <button class="mvp-btn mvp-btn--ghost" @click="retryStage">
          ↺ {{ $t('agileTraining.mvp.retryStage') }}
        </button>
        <button v-if="stage !== 'mlp'" class="mvp-btn mvp-btn--primary" @click="nextStage">
          {{ $t('agileTraining.mvp.goToStage.' + nextStageKey) }} →
        </button>
        <button v-else class="mvp-btn mvp-btn--primary" @click="goToFinal">
          🏁 {{ $t('agileTraining.mvp.goToFinal') }}
        </button>
      </div>
    </section>

    <!-- Final recap for this case -->
    <section v-else-if="step === 'final' && activeCase" class="mvp-card">
      <h2>🏁 {{ $t('agileTraining.mvp.finalTitle') }}</h2>
      <p class="mvp-card__lead">{{ $t('agileTraining.mvp.finalLead') }}</p>

      <div class="mvp-recap">
        <div v-for="s in STAGES" :key="'recap-'+s"
             :class="['mvp-recap__item', 'mvp-recap__item--'+(caseData[s] && caseData[s].status || 'empty')]">
          <div class="mvp-recap__head">
            <span :class="['mvp-stage-badge', 'mvp-stage-badge--'+s]">{{ $t('agileTraining.mvp.stage.'+s) }}</span>
            <span v-if="caseData[s] && caseData[s].status"
                  :class="['mvp-badge-status', 'mvp-badge-status--'+caseData[s].status]">
              {{ $t('agileTraining.mvp.status.' + caseData[s].status) }}
            </span>
          </div>
          <div class="mvp-recap__explain">{{ $t('agileTraining.mvp.explain.'+s) }}</div>
          <div v-if="caseData[s] && caseData[s].features.length" class="mvp-recap__chips">
            <span v-for="k in caseData[s].features" :key="'rc-'+s+'-'+k"
                  :class="['mvp-feat-chip', 'mvp-feat-chip--' + featureWeight(k)]">
              {{ featureTitle(k) }}
            </span>
          </div>
        </div>
      </div>

      <div class="mvp-group-hint" v-if="groupResults">
        <div class="mvp-group-hint__title">👥 {{ $t('agileTraining.mvp.groupHint') }}</div>
        <div class="mvp-group-hint__text">
          {{ $t('agileTraining.mvp.groupStats', {
            answers: groupResults.answers_count || 0,
            avg: groupResults.avg_score || 0
          }) }}
        </div>
      </div>

      <div class="mvp-card__actions">
        <button class="mvp-btn mvp-btn--ghost" @click="goBackToCases">
          ← {{ $t('agileTraining.mvp.backToCases') }}
        </button>
        <button class="mvp-btn mvp-btn--primary" @click="nextCase" v-if="hasMoreCases">
          {{ $t('agileTraining.mvp.nextCase') }} →
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

const STAGES = ['mvp', 'mmp', 'mlp'];

export default {
  name: 'AgileMvpPlay',
  props: {
    slug: { type: String, required: true },
    group: { type: Object, default: null },
  },
  data() {
    return {
      STAGES,
      loading: true,
      locale: 'ru',
      cases: [],
      stageLimits: { mvp: 3, mmp: 6, mlp: 9 },
      answers: {},              // { case_key: { mvp: {features, status}, mmp: {...}, mlp: {...} } }
      step: 'start',
      displayName: '',
      participantToken: '',
      activeCaseKey: null,
      stage: 'mvp',
      pending: [],              // фичи, выбранные на текущей итерации (расширяют previouslyLocked)
      submitting: false,
      stageResult: null,
      groupResults: null,
    };
  },
  computed: {
    activeCase() {
      return this.cases.find(c => c.key === this.activeCaseKey) || null;
    },
    caseData() {
      return this.answers[this.activeCaseKey] || { mvp: null, mmp: null, mlp: null };
    },
    stageLimit() { return this.stageLimits[this.stage] || 3; },
    previouslyLocked() {
      if (this.stage === 'mvp') return [];
      if (this.stage === 'mmp') return ((this.caseData.mvp && this.caseData.mvp.features) || []);
      if (this.stage === 'mlp') return ((this.caseData.mmp && this.caseData.mmp.features) || []);
      return [];
    },
    previouslyLockedFeatures() {
      const ac = this.activeCase;
      if (!ac) return [];
      const set = new Set(this.previouslyLocked);
      return ac.features.filter(f => set.has(f.key));
    },
    selectedInStage() {
      // total = previouslyLocked ∪ pending
      const set = new Set(this.previouslyLocked);
      for (const k of this.pending) set.add(k);
      return [...set];
    },
    stageTitle() {
      return this.$t('agileTraining.mvp.stageTitle.' + this.stage);
    },
    stageBrief() {
      return this.$t('agileTraining.mvp.stageBrief.' + this.stage, { max: this.stageLimit });
    },
    nextStageKey() {
      if (this.stage === 'mvp') return 'mmp';
      if (this.stage === 'mmp') return 'mlp';
      return 'mlp';
    },
    stageVerdictTitle() {
      return this.$t('agileTraining.mvp.verdict.' + this.stage + '.' + this.stageResult.status);
    },
    stageReactionText() {
      const r = this.stageResult.reaction_locales || {};
      return r[this.locale] || r.ru || r.en || '';
    },
    hasMoreCases() {
      if (!this.cases.length) return false;
      // есть кейс без `mlp.status === success`?
      const idx = this.cases.findIndex(c => c.key === this.activeCaseKey);
      return this.cases.slice(idx + 1).length > 0;
    },
  },
  watch: {
    locale(v) {
      localStorage.setItem('language', v);
      if (this.$i18n) this.$i18n.locale = v;
      this.reloadContent();
    },
  },
  async mounted() {
    this.locale = (localStorage.getItem('language') === 'en') ? 'en' : 'ru';
    if (this.$i18n) this.$i18n.locale = this.locale;
    this.participantToken = localStorage.getItem(`mvp_token_${this.slug}`) || '';
    this.displayName = localStorage.getItem(`mvp_name_${this.slug}`) || '';
    await this.reloadContent();
    this.loading = false;
  },
  methods: {
    setLocale(lc) { this.locale = lc; },
    async reloadContent() {
      try {
        const params = { locale: this.locale };
        if (this.participantToken) params.participant_token = this.participantToken;
        const res = await axios.get(`/api/agile-training/mvp/g/${this.slug}/state`, { params });
        this.cases = res.data.cases || [];
        this.stageLimits = res.data.stage_limits || this.stageLimits;
        this.answers = res.data.answers || {};
      } catch (e) {
        console.error('state load failed', e);
      }
    },
    async startRun() {
      if (this.displayName) localStorage.setItem(`mvp_name_${this.slug}`, this.displayName);
      if (!this.participantToken) {
        try {
          const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, {
            display_name: this.displayName || null,
          });
          this.participantToken = res.data.participant_token;
          localStorage.setItem(`mvp_token_${this.slug}`, this.participantToken);
          await this.reloadContent();
        } catch (e) {
          alert(e.response?.data?.error || 'Failed to join');
          return;
        }
      }
      this.step = 'cases';
      this.loadGroupResults();
    },
    async loadGroupResults() {
      try {
        const res = await axios.get(`/api/agile-training/mvp/g/${this.slug}/results`, {
          params: { locale: this.locale },
        });
        this.groupResults = res.data;
      } catch (e) {
        this.groupResults = null;
      }
    },
    caseHasProgress(key) {
      const d = this.answers[key];
      return !!(d && (d.mvp?.status || d.mmp?.status || d.mlp?.status));
    },
    caseStatus(key) {
      const d = this.answers[key];
      if (!d) return '';
      if (d.mlp?.status) return '🏁 ' + this.$t('agileTraining.mvp.stage.mlp') + ': ' + this.$t('agileTraining.mvp.status.' + d.mlp.status);
      if (d.mmp?.status) return '⭐ ' + this.$t('agileTraining.mvp.stage.mmp') + ': ' + this.$t('agileTraining.mvp.status.' + d.mmp.status);
      if (d.mvp?.status) return '🚀 ' + this.$t('agileTraining.mvp.stage.mvp') + ': ' + this.$t('agileTraining.mvp.status.' + d.mvp.status);
      return '';
    },
    pickCase(key) {
      this.activeCaseKey = key;
      this.stageResult = null;
      this.step = 'hypothesis';
    },
    goBackToCases() {
      this.activeCaseKey = null;
      this.stage = 'mvp';
      this.pending = [];
      this.stageResult = null;
      this.step = 'cases';
    },
    goToStage(s) {
      this.stage = s;
      // резюмируем "pending" — новые фичи, которых ещё нет в previouslyLocked,
      // но есть в уже сохранённой итерации этой стадии
      const prev = (this.caseData[s] && this.caseData[s].features) || [];
      const locked = new Set(this.previouslyLockedFor(s));
      this.pending = prev.filter(k => !locked.has(k));
      this.stageResult = null;
      this.step = 'stage';
    },
    previouslyLockedFor(stage) {
      if (stage === 'mvp') return [];
      if (stage === 'mmp') return ((this.caseData.mvp && this.caseData.mvp.features) || []);
      if (stage === 'mlp') return ((this.caseData.mmp && this.caseData.mmp.features) || []);
      return [];
    },
    goBackFromStage() {
      if (this.stage === 'mvp') {
        this.step = 'hypothesis';
      } else {
        // возвращаемся на результат предыдущей итерации
        const prev = this.stage === 'mmp' ? 'mvp' : 'mmp';
        this.stage = prev;
        this.stageResult = this.buildSyntheticResult(prev);
        this.step = 'result';
      }
    },
    buildSyntheticResult(stage) {
      // для отображения кнопки «продолжить» при возврате — используем минимум из сохранённых данных
      const saved = this.caseData[stage];
      if (!saved || !saved.status) return null;
      return {
        stage,
        selected: saved.features || [],
        status: saved.status,
        antipatterns: [],
        hint_keys: [],
        reaction_locales: {},
      };
    },
    isLocked(key) {
      return this.previouslyLocked.includes(key);
    },
    isSelected(key) {
      return this.previouslyLocked.includes(key) || this.pending.includes(key);
    },
    toggleFeature(key) {
      if (this.isLocked(key)) return;
      const idx = this.pending.indexOf(key);
      if (idx >= 0) {
        this.pending.splice(idx, 1);
        return;
      }
      if (this.selectedInStage.length >= this.stageLimit) return;
      this.pending.push(key);
    },
    async submitStage() {
      if (this.submitting) return;
      this.submitting = true;
      try {
        const res = await axios.post(`/api/agile-training/mvp/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          case_key: this.activeCaseKey,
          stage: this.stage,
          features: this.selectedInStage,
        });
        this.stageResult = res.data.stage_result;
        // обновим локальный кэш ответов
        this.answers = { ...this.answers, [this.activeCaseKey]: res.data.data };
        this.step = 'result';
        this.loadGroupResults();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.submitting = false;
      }
    },
    retryStage() {
      this.stageResult = null;
      // sync pending с последним сохранённым состоянием этой стадии
      const prev = (this.caseData[this.stage] && this.caseData[this.stage].features) || [];
      const locked = new Set(this.previouslyLockedFor(this.stage));
      this.pending = prev.filter(k => !locked.has(k));
      this.step = 'stage';
    },
    nextStage() {
      const next = this.nextStageKey;
      this.goToStage(next);
    },
    goToFinal() {
      this.stageResult = null;
      this.step = 'final';
    },
    nextCase() {
      const idx = this.cases.findIndex(c => c.key === this.activeCaseKey);
      const next = this.cases[idx + 1];
      if (next) {
        this.pickCase(next.key);
      } else {
        this.goBackToCases();
      }
    },
    featureTitle(key) {
      if (!this.activeCase) return key;
      const f = this.activeCase.features.find(f => f.key === key);
      return f ? f.title : key;
    },
    featureWeight(key) {
      if (!this.activeCase) return 'optional';
      const f = this.activeCase.features.find(f => f.key === key);
      return f ? f.weight : 'optional';
    },
  },
};
</script>

<style scoped>
.mvp-play { max-width: 780px; margin: 0 auto; padding: 20px 16px 60px; color: #0f172a; }
.mvp-play__top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 20px; }
.mvp-play__brand { display: flex; align-items: center; gap: 10px; }
.mvp-play__icon { font-size: 28px; }
.mvp-play__brand-title { font-weight: 700; font-size: 15px; color: #0f172a; }
.mvp-play__brand-sub { color: #64748b; font-size: 12px; }
.mvp-play__lang { display: flex; gap: 4px; background: #fff7ed; padding: 3px; border-radius: 10px; border: 1px solid #fed7aa; }
.mvp-lang__btn {
  background: transparent !important; border: none !important; color: #9a3412 !important;
  padding: 4px 12px !important; border-radius: 8px !important; font-weight: 600; cursor: pointer; font-size: 12px;
  transition: all 0.15s ease; box-shadow: none !important;
}
.mvp-lang__btn.is-active { background: #fff !important; color: #ea580c !important; box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important; }
.mvp-lang__btn:hover:not(.is-active) { background: #ffedd5 !important; }

.mvp-play__loading { padding: 40px; text-align: center; color: #64748b; }

.mvp-card { background: #fff; border-radius: 20px; padding: 24px; box-shadow: 0 4px 16px rgba(15, 23, 42, 0.06); margin-bottom: 16px; }
.mvp-card--center { text-align: center; }
.mvp-card__title { margin: 0 0 10px; font-size: 22px; }
.mvp-card__lead { color: #475569; margin: 0 0 16px; line-height: 1.5; }
.mvp-card__head { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap; }
.mvp-card__head h2 { margin: 0; font-size: 20px; }
.mvp-card__how { list-style: none; padding: 0; margin: 0 0 16px; display: flex; flex-direction: column; gap: 8px; text-align: left; max-width: 420px; margin-left: auto; margin-right: auto; }
.mvp-card__how li { background: #fff7ed; border-radius: 10px; padding: 10px 14px; border: 1px solid #fed7aa; font-size: 14px; }
.mvp-card__actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 20px; flex-wrap: wrap; }

.mvp-start__name { display: flex; flex-direction: column; gap: 6px; max-width: 320px; margin: 0 auto 16px; text-align: left; font-size: 13px; color: #475569; }
.mvp-start__name input { padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; font-size: 14px; }

.mvp-btn {
  border-radius: 10px !important; padding: 10px 20px !important; font-weight: 700; font-size: 14px;
  cursor: pointer; transition: all 0.15s ease; border: none !important; font-family: inherit;
}
.mvp-btn--primary {
  background: linear-gradient(135deg, #fb923c, #f97316) !important; color: #fff !important;
  box-shadow: 0 4px 10px rgba(249, 115, 22, 0.25);
}
.mvp-btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(249, 115, 22, 0.35); }
.mvp-btn--primary:active:not(:disabled) { transform: translateY(0); box-shadow: 0 2px 6px rgba(249, 115, 22, 0.25); }
.mvp-btn--primary:disabled { opacity: 0.55; cursor: not-allowed; transform: none; box-shadow: 0 2px 4px rgba(0,0,0,0.08); }
.mvp-btn--ghost {
  background: #fff !important; color: #9a3412 !important; border: 1px solid #fdba74 !important;
}
.mvp-btn--ghost:hover:not(:disabled) { background: #fff7ed !important; border-color: #fb923c !important; }
.mvp-btn--ghost:active:not(:disabled) { background: #ffedd5 !important; }

.mvp-cases { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.mvp-case { background: #fff7ed; border-radius: 14px; padding: 14px 16px; border: 1px solid #fed7aa; display: flex; gap: 12px; align-items: center; justify-content: space-between; flex-wrap: wrap; }
.mvp-case__info { flex: 1; min-width: 220px; }
.mvp-case__head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; flex-wrap: wrap; }
.mvp-case__cat { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #fdba74; color: #7c2d12; font-size: 11px; font-weight: 700; text-transform: uppercase; }
.mvp-case__status { color: #0f172a; font-size: 12px; background: #fff; padding: 2px 8px; border-radius: 999px; border: 1px solid #fed7aa; }
.mvp-case h3 { margin: 0 0 4px; font-size: 16px; }
.mvp-case__hyp { color: #64748b; font-size: 13px; margin: 0; font-style: italic; line-height: 1.4; }

.mvp-hyp { background: linear-gradient(135deg, #fff7ed, #fff); border-radius: 14px; padding: 16px; border: 1px solid #fed7aa; margin-bottom: 16px; }
.mvp-hyp__label { color: #9a3412; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 6px; }
.mvp-hyp__text { font-size: 17px; line-height: 1.5; color: #0f172a; font-style: italic; }
.mvp-context { list-style: none; padding: 0; margin: 0 0 16px; display: flex; flex-direction: column; gap: 6px; }
.mvp-context li { background: #f8fafc; padding: 8px 12px; border-radius: 8px; border-left: 3px solid #fb923c; font-size: 13px; color: #334155; }

.mvp-stage-badge { display: inline-flex; padding: 4px 12px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.mvp-stage-badge--mvp { background: #fee2e2; color: #991b1b; }
.mvp-stage-badge--mmp { background: #dbeafe; color: #1e40af; }
.mvp-stage-badge--mlp { background: #dcfce7; color: #166534; }

.mvp-counter { margin-bottom: 14px; }
.mvp-counter__text { color: #9a3412; font-weight: 600; font-size: 13px; margin-bottom: 4px; }
.mvp-counter__bar { background: #fff7ed; border-radius: 8px; height: 8px; overflow: hidden; border: 1px solid #fed7aa; }
.mvp-counter__fill { background: linear-gradient(90deg, #fb923c, #f97316); height: 100%; transition: width 0.3s ease; }

.mvp-lockeds { background: #f0f9ff; border-radius: 10px; padding: 10px 12px; margin-bottom: 14px; border: 1px dashed #7dd3fc; }
.mvp-lockeds__title { color: #0369a1; font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.mvp-lockeds__chips { display: flex; flex-wrap: wrap; gap: 6px; }

.mvp-features-grid { list-style: none; padding: 0; margin: 0 0 14px; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 10px; }
.mvp-feature { background: #fff; border-radius: 12px; padding: 12px 14px; border: 2px solid #e5e7eb; cursor: pointer; transition: all 0.18s ease; position: relative; user-select: none; }
.mvp-feature:hover:not(.is-disabled):not(.is-locked) { transform: translateY(-2px); box-shadow: 0 8px 16px rgba(249, 115, 22, 0.12); border-color: #fdba74; }
.mvp-feature:active:not(.is-disabled):not(.is-locked) { transform: translateY(0); }
.mvp-feature.is-selected { border-color: #f97316; background: #fff7ed; box-shadow: 0 6px 14px rgba(249, 115, 22, 0.22); }
.mvp-feature.is-locked { border-color: #7dd3fc; background: #f0f9ff; cursor: not-allowed; opacity: 0.85; }
.mvp-feature.is-disabled { opacity: 0.5; cursor: not-allowed; }
.mvp-feature__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.mvp-feature__title { font-weight: 700; color: #0f172a; font-size: 14px; margin-bottom: 4px; }
.mvp-feature__desc { color: #64748b; font-size: 12px; line-height: 1.4; }
.mvp-feature__check { color: #ea580c; font-weight: 900; font-size: 18px; }
.mvp-feature__lock { font-size: 14px; }

.mvp-feat-tag { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
.mvp-feat-tag--critical { background: #fee2e2; color: #991b1b; }
.mvp-feat-tag--improve { background: #dbeafe; color: #1e40af; }
.mvp-feat-tag--optional { background: #f1f5f9; color: #475569; }

.mvp-feat-chip { display: inline-flex; padding: 3px 10px; border-radius: 999px; font-size: 12px; font-weight: 500; border: 1px solid transparent; }
.mvp-feat-chip--critical { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.mvp-feat-chip--improve { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
.mvp-feat-chip--optional { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
.mvp-feat-chip--locked { background: #f0f9ff; color: #0369a1; border-color: #7dd3fc; }
.mvp-feat-chip--hint { background: #fef9c3; color: #854d0e; border-color: #fde047; }

/* Verdict */
.mvp-verdict { display: flex; gap: 14px; padding: 16px; border-radius: 14px; margin-bottom: 16px; border: 1px solid transparent; }
.mvp-verdict__icon { font-size: 36px; line-height: 1; }
.mvp-verdict__title { font-weight: 700; font-size: 17px; margin-bottom: 4px; }
.mvp-verdict__reaction { color: #334155; line-height: 1.55; font-size: 14px; }
.mvp-verdict--success { background: #dcfce7; border-color: #86efac; }
.mvp-verdict--success .mvp-verdict__title { color: #166534; }
.mvp-verdict--partial { background: #fef3c7; border-color: #fcd34d; }
.mvp-verdict--partial .mvp-verdict__title { color: #92400e; }
.mvp-verdict--fail { background: #fee2e2; border-color: #fca5a5; }
.mvp-verdict--fail .mvp-verdict__title { color: #991b1b; }

.mvp-aps, .mvp-hints, .mvp-picks { margin-bottom: 14px; }
.mvp-aps__title, .mvp-hints__title, .mvp-picks__title { font-weight: 700; color: #9a3412; font-size: 13px; margin-bottom: 6px; }
.mvp-aps ul { list-style: disc inside; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; color: #7f1d1d; }
.mvp-aps li { background: #fee2e2; padding: 6px 10px; border-radius: 8px; font-size: 13px; }
.mvp-hints__chips, .mvp-picks__chips { display: flex; flex-wrap: wrap; gap: 6px; }

/* Final recap */
.mvp-recap { display: flex; flex-direction: column; gap: 10px; margin-bottom: 16px; }
.mvp-recap__item { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px 14px; }
.mvp-recap__item--success { border-color: #86efac; background: #f0fdf4; }
.mvp-recap__item--partial { border-color: #fcd34d; background: #fffbeb; }
.mvp-recap__item--fail { border-color: #fca5a5; background: #fef2f2; }
.mvp-recap__head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 6px; flex-wrap: wrap; }
.mvp-recap__explain { color: #475569; font-size: 13px; margin-bottom: 6px; line-height: 1.45; }
.mvp-recap__chips { display: flex; flex-wrap: wrap; gap: 6px; }

.mvp-badge-status { display: inline-flex; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; }
.mvp-badge-status--success { background: #dcfce7; color: #166534; }
.mvp-badge-status--partial { background: #fef3c7; color: #92400e; }
.mvp-badge-status--fail { background: #fee2e2; color: #991b1b; }

.mvp-group-hint { background: #fff7ed; border-radius: 12px; padding: 12px 14px; border: 1px solid #fed7aa; margin-bottom: 8px; }
.mvp-group-hint__title { color: #9a3412; font-size: 12px; font-weight: 700; margin-bottom: 4px; text-transform: uppercase; letter-spacing: 0.3px; }
.mvp-group-hint__text { color: #0f172a; font-size: 13px; line-height: 1.5; }

@media (max-width: 520px) {
  .mvp-play { padding: 16px 12px 40px; }
  .mvp-card { padding: 18px; }
  .mvp-features-grid { grid-template-columns: 1fr; }
  .mvp-verdict { flex-direction: column; text-align: center; align-items: center; }
}
</style>
