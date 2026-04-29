<template>
  <div class="rice-play">
    <header class="rice-play__top">
      <div class="rice-play__brand">
        <span class="rice-play__icon">⚖️</span>
        <div>
          <div class="rice-play__brand-title">{{ $t('agileTraining.rice.playTitle') }}</div>
          <div class="rice-play__brand-sub" v-if="group">{{ group.name }}</div>
        </div>
      </div>
      <div class="rice-play__lang">
        <button type="button" class="rice-lang__btn"
                :class="{ 'is-active': locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button type="button" class="rice-lang__btn"
                :class="{ 'is-active': locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
    </header>

    <!-- Прогресс -->
    <nav v-if="!loading && step !== 'start'" class="rice-steps">
      <div v-for="(s, i) in steps" :key="s.key"
           class="rice-steps__item"
           :class="{ 'is-active': stepBucket(step) === s.key, 'is-done': stepIndex(step) > i }">
        <span class="rice-steps__num">{{ i + 1 }}</span>
        <span class="rice-steps__label">{{ $t(s.labelKey) }}</span>
      </div>
    </nav>

    <div v-if="loading" class="rice-play__loading">{{ $t('common.loading') }}…</div>

    <!-- 0. Start -->
    <section v-else-if="step === 'start'" class="rice-card rice-card--center">
      <h1>{{ $t('agileTraining.rice.startTitle') }}</h1>
      <p class="rice-card__lead">{{ $t('agileTraining.rice.startLead') }}</p>
      <ul class="rice-defs">
        <li>🎯 {{ $t('agileTraining.rice.startBullet1') }}</li>
        <li>⏱ {{ $t('agileTraining.rice.startBullet2') }}</li>
        <li>🧠 {{ $t('agileTraining.rice.startBullet3') }}</li>
      </ul>
      <label class="rice-start__name">
        <span>{{ $t('agileTraining.common.yourName') }}</span>
        <input v-model="displayName" maxlength="60"
               :placeholder="$t('agileTraining.common.yourNamePh')" />
      </label>
      <button class="rice-btn rice-btn--primary" @click="startRun">
        {{ $t('agileTraining.rice.start') }}
      </button>
    </section>

    <!-- 1. Role -->
    <section v-else-if="step === 'role'" class="rice-card">
      <h2>{{ $t('agileTraining.rice.roleTitle') }}</h2>
      <p class="rice-card__lead">{{ $t('agileTraining.rice.roleLead') }}</p>
      <ul class="rice-roles-grid">
        <li v-for="r in content.roles" :key="r.key"
            class="rice-role-card"
            :class="{ 'is-selected': roleKey === r.key }"
            @click="roleKey = r.key">
          <div class="rice-role-card__title">{{ r.title }}</div>
          <div class="rice-role-card__focus">{{ r.focus }}</div>
          <p class="rice-role-card__desc">{{ r.desc }}</p>
        </li>
      </ul>
      <div class="rice-card__actions">
        <span></span>
        <button class="rice-btn rice-btn--primary" :disabled="!roleKey" @click="goStep('context')">
          {{ $t('agileTraining.rice.next') }} →
        </button>
      </div>
    </section>

    <!-- 2. Context -->
    <section v-else-if="step === 'context'" class="rice-card">
      <h2>{{ content.context?.title || $t('agileTraining.rice.contextTitle') }}</h2>
      <p class="rice-card__lead">{{ content.context?.lead }}</p>
      <div class="rice-options">
        <article v-for="o in content.options" :key="o.key" class="rice-option">
          <div class="rice-option__head">
            <h3>{{ o.title }}</h3>
            <span class="rice-option__short">{{ o.short }}</span>
          </div>
          <p class="rice-option__desc">{{ o.description }}</p>
          <div class="rice-option__meta">
            <span class="rice-chip rice-chip--money">💰 {{ o.revenue_label }}</span>
            <span class="rice-chip rice-chip--time">⏱ {{ o.time_label }}</span>
          </div>
          <div class="rice-option__cols">
            <div>
              <b>✅ {{ $t('agileTraining.rice.strengths') }}</b>
              <ul><li v-for="s in o.strengths" :key="s">{{ s }}</li></ul>
            </div>
            <div>
              <b>⚠️ {{ $t('agileTraining.rice.risks') }}</b>
              <ul><li v-for="rk in o.risks" :key="rk">{{ rk }}</li></ul>
            </div>
          </div>
          <div v-if="o.context_facts && o.context_facts.length" class="rice-option__facts">
            <b>📌 {{ $t('agileTraining.rice.contextFacts') }}</b>
            <ul>
              <li v-for="f in o.context_facts" :key="f">{{ f }}</li>
            </ul>
          </div>
          <div v-if="o.data_quality && o.data_quality.length" class="rice-option__facts">
            <b>🧪 {{ $t('agileTraining.rice.dataQualityFlags') }}</b>
            <ul>
              <li v-for="dq in o.data_quality" :key="dq">{{ dq }}</li>
            </ul>
          </div>
        </article>
      </div>
      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost" @click="goStep('role')">
          ← {{ $t('agileTraining.rice.back') }}
        </button>
        <button class="rice-btn rice-btn--primary" @click="goStep('scores')">
          {{ $t('agileTraining.rice.goToScores') }} →
        </button>
      </div>
    </section>

    <!-- 3. Scores -->
    <section v-else-if="stepBucket(step) === 'scores'" class="rice-card">
      <h2>
        {{ step === 'revise_scores'
           ? $t('agileTraining.rice.reviseScoresTitle')
           : $t('agileTraining.rice.scoresTitle') }}
      </h2>
      <p class="rice-card__lead">{{ $t('agileTraining.rice.scoresLead') }}</p>
      <div class="rice-scale-legend">
        <span class="rice-fac__hint">1 — {{ $t('agileTraining.rice.legend.low') }}</span>
        <span class="rice-fac__hint">5 — {{ $t('agileTraining.rice.legend.mid') }}</span>
        <span class="rice-fac__hint">13 — {{ $t('agileTraining.rice.legend.high') }}</span>
      </div>
      <div v-for="o in content.options" :key="o.key" class="rice-score-block">
        <div class="rice-score-block__head">
          <h3>{{ o.title }}</h3>
          <span class="rice-option__short">{{ o.short }}</span>
        </div>
        <div class="rice-score-block__dims">
          <div v-for="dim in dims" :key="dim.key" class="rice-dim">
            <div class="rice-dim__label">
              <b>{{ $t('agileTraining.rice.dim.' + dim.key) }}</b>
              <span class="rice-fac__hint">— {{ $t('agileTraining.rice.dim.' + dim.key + 'Hint') }}</span>
            </div>
            <div class="rice-scale">
              <button v-for="v in content.scale" :key="dim.key + '-' + v"
                      type="button" class="rice-scale__btn"
                      :class="{ 'is-active': currentScores[o.key][dim.key] === v }"
                      @click="currentScores[o.key][dim.key] = v">
                {{ v }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost"
                @click="goStep(step === 'revise_scores' ? 'event' : 'context')">
          ← {{ $t('agileTraining.rice.back') }}
        </button>
        <button class="rice-btn rice-btn--primary" @click="goStep('priorities')">
          {{ $t('agileTraining.rice.calcPriority') }} →
        </button>
      </div>
    </section>

    <!-- 4. Priorities -->
    <section v-else-if="step === 'priorities'" class="rice-card">
      <h2>{{ $t('agileTraining.rice.prioritiesTitle') }}</h2>
      <p class="rice-card__lead">{{ $t('agileTraining.rice.prioritiesLead') }}</p>
      <div class="rice-formula">
        <code>{{ $t('agileTraining.rice.formula') }}</code>
      </div>
      <ul class="rice-priorities">
        <li v-for="row in rankedRows" :key="row.key"
            class="rice-priority"
            :class="{ 'is-top': row.isTop }">
          <div class="rice-priority__head">
            <b>{{ row.title }}</b>
            <span class="rice-priority__score">{{ row.rice }}</span>
          </div>
          <div class="rice-priority__bar">
            <span :style="{ width: row.pct + '%' }"></span>
          </div>
          <div class="rice-priority__dims">
            <span>{{ $t('agileTraining.rice.dimAbbr.reach') }}: {{ row.scores.reach }}</span>
            <span>{{ $t('agileTraining.rice.dimAbbr.impact') }}: {{ row.scores.impact }}</span>
            <span>{{ $t('agileTraining.rice.dimAbbr.confidence') }}: {{ row.scores.confidence }}</span>
            <span>{{ $t('agileTraining.rice.dimAbbr.effort') }}: {{ row.scores.effort }}</span>
          </div>
        </li>
      </ul>
      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost" @click="goStep(inReviseFlow ? 'revise_scores' : 'scores')">
          ← {{ $t('agileTraining.rice.back') }}
        </button>
        <button class="rice-btn rice-btn--primary" @click="goStep(inReviseFlow ? 'revise_choose' : 'choose')">
          {{ $t('agileTraining.rice.goToChoose') }} →
        </button>
      </div>
    </section>

    <!-- 5. Choose / Revise-Choose -->
    <section v-else-if="stepBucket(step) === 'choose'" class="rice-card">
      <h2>
        {{ step === 'revise_choose'
           ? $t('agileTraining.rice.reviseChooseTitle')
           : $t('agileTraining.rice.chooseTitle') }}
      </h2>
      <p class="rice-card__lead">{{ $t('agileTraining.rice.chooseLead') }}</p>
      <ul class="rice-choice">
        <li v-for="o in content.options" :key="o.key"
            class="rice-choice__item"
            :class="{ 'is-selected': currentChoice === o.key }"
            @click="currentChoice = o.key">
          <div class="rice-choice__head">
            <b>{{ o.title }}</b>
            <span class="rice-fac__hint">RICE: {{ riceOf(o.key) }}</span>
          </div>
          <div class="rice-choice__short">{{ o.short }}</div>
        </li>
      </ul>
      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost"
                @click="goStep(inReviseFlow ? 'revise_scores' : 'priorities')">
          ← {{ $t('agileTraining.rice.back') }}
        </button>
        <button class="rice-btn rice-btn--primary"
                :disabled="!currentChoice || saving"
                @click="submitCurrentRound">
          {{ saving
             ? $t('common.saving') + '…'
             : (inReviseFlow
                ? $t('agileTraining.rice.finish')
                : $t('agileTraining.rice.lockIn')) }} →
        </button>
      </div>
    </section>

    <!-- 6. Consequences -->
    <section v-else-if="step === 'consequences'" class="rice-card">
      <h2>{{ $t('agileTraining.rice.consequencesTitle') }}</h2>
      <p class="rice-card__lead" v-if="consequences.summary_key">
        {{ $t('agileTraining.rice.consequences.' + consequences.summary_key) }}
      </p>
      <div class="rice-cons-cols">
        <div class="rice-cons-col rice-cons-col--gain">
          <h3>✅ {{ $t('agileTraining.rice.youGained') }}</h3>
          <ul>
            <li v-for="k in consequences.gained" :key="'g-' + k">
              {{ $t('agileTraining.rice.consequences.' + k) }}
            </li>
          </ul>
        </div>
        <div class="rice-cons-col rice-cons-col--loss">
          <h3>⚠️ {{ $t('agileTraining.rice.youLost') }}</h3>
          <ul>
            <li v-for="k in consequences.lost" :key="'l-' + k">
              {{ $t('agileTraining.rice.consequences.' + k) }}
            </li>
          </ul>
        </div>
      </div>

      <!-- подсветка ошибок -->
      <div v-if="initialErrors.length" class="rice-warnings">
        <h4>🧭 {{ $t('agileTraining.rice.heyLook') }}</h4>
        <ul>
          <li v-for="er in initialErrors" :key="er">
            {{ $t('agileTraining.rice.err.' + er) }}
          </li>
        </ul>
      </div>

      <div class="rice-card__actions">
        <span></span>
        <button class="rice-btn rice-btn--primary" @click="goStep('event')">
          {{ $t('agileTraining.rice.nextNews') }} →
        </button>
      </div>
    </section>

    <!-- 7. Event + Revise -->
    <section v-else-if="step === 'event'" class="rice-card">
      <div class="rice-event">
        <span class="rice-event__badge">📰 {{ $t('agileTraining.rice.breaking') }}</span>
        <h2>{{ eventTitle }}</h2>
        <p class="rice-event__lead">{{ eventLead }}</p>
      </div>
      <div class="rice-note">
        {{ $t('agileTraining.rice.eventNote') }}
      </div>
      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost" @click="goStep('consequences')">
          ← {{ $t('agileTraining.rice.back') }}
        </button>
        <button class="rice-btn rice-btn--primary" @click="startRevise">
          {{ $t('agileTraining.rice.rethink') }} →
        </button>
      </div>
    </section>

    <!-- 8. Final -->
    <section v-else-if="step === 'final'" class="rice-card">
      <h2>{{ $t('agileTraining.rice.finalTitle') }}</h2>
      <p class="rice-card__lead" v-if="adaptationStatus">
        {{ $t('agileTraining.rice.adaptationLead.' + adaptationStatus) }}
      </p>
      <p class="rice-pdf-bar">
        <button
          type="button"
          class="rice-btn rice-btn--ghost"
          :disabled="pdfExporting"
          @click="exportResultPdf"
        >
          {{ pdfExporting ? $t('agileTraining.common.downloadPdfLoading') : $t('agileTraining.common.downloadPdf') }}
        </button>
      </p>

      <div ref="pdfExportRoot" class="rice-pdf-root">
        <div class="rice-final-grid">
          <div class="rice-final-card">
            <div class="rice-fac__hint">{{ $t('agileTraining.rice.initialChoice') }}</div>
            <b>{{ optionTitle(initialChoice) || '—' }}</b>
          </div>
          <div class="rice-final-card">
            <div class="rice-fac__hint">{{ $t('agileTraining.rice.revisedChoice') }}</div>
            <b>{{ optionTitle(revisedChoice) || '—' }}</b>
          </div>
          <div class="rice-final-card"
               :class="{ 'rice-final-card--changed': initialChoice !== revisedChoice && revisedChoice }">
            <div class="rice-fac__hint">{{ $t('agileTraining.rice.changedMind') }}</div>
            <b>
              {{ initialChoice !== revisedChoice && revisedChoice
                 ? $t('agileTraining.rice.yesChanged')
                 : $t('agileTraining.rice.noKept') }}
            </b>
          </div>
        </div>

        <div v-if="groupResults" class="rice-group">
          <h3>👥 {{ $t('agileTraining.rice.yourGroup') }}</h3>
          <p class="rice-fac__hint">
            {{ $t('agileTraining.facilitator.participants',
                  { n: groupResults.total_participants || 0 }, groupResults.total_participants || 0) }}
            · {{ $t('agileTraining.rice.answersCount',
                     { n: groupResults.total_answers || 0 }, groupResults.total_answers || 0) }}
          </p>
          <div class="rice-group-cols">
            <div>
              <b>{{ $t('agileTraining.rice.initialChoice') }}</b>
              <ul class="rice-group-list">
                <li v-for="o in content.options" :key="'ig-' + o.key">
                  <span>{{ o.title }}</span>
                  <b>{{ groupResults.initial_counts[o.key] || 0 }}</b>
                </li>
              </ul>
            </div>
            <div>
              <b>{{ $t('agileTraining.rice.revisedChoice') }}</b>
              <ul class="rice-group-list">
                <li v-for="o in content.options" :key="'rg-' + o.key">
                  <span>{{ o.title }}</span>
                  <b>{{ groupResults.revised_counts[o.key] || 0 }}</b>
                </li>
              </ul>
            </div>
            <div>
              <b>{{ $t('agileTraining.rice.adaptations') }}</b>
              <ul class="rice-group-list">
                <li v-for="(cnt, key) in groupResults.adaptation_counts" :key="'a-' + key">
                  <span>{{ $t('agileTraining.rice.adaptation.' + key) }}</span>
                  <b>{{ cnt }}</b>
                </li>
                <li v-if="!Object.keys(groupResults.adaptation_counts || {}).length"
                    class="rice-fac__hint">
                  — {{ $t('agileTraining.rice.noAdaptationYet') }}
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div class="rice-card__actions">
        <button class="rice-btn rice-btn--ghost" @click="loadGroupResults">
          🔄 {{ $t('agileTraining.rice.refreshGroup') }}
        </button>
        <button class="rice-btn rice-btn--primary" @click="restart">
          {{ $t('agileTraining.rice.tryAgain') }}
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';

const DEFAULT_OPTION_KEYS = ['smart_onboarding', 'referral_rework', 'search_quality'];

function blankScores() {
  const out = {};
  for (const k of DEFAULT_OPTION_KEYS) {
    out[k] = { reach: 0, impact: 0, confidence: 0, effort: 0 };
  }
  return out;
}

export default {
  name: 'AgileRicePlay',
  props: { slug: { type: String, required: true } },
  data() {
    return {
      loading: true,
      saving: false,
      locale: 'ru',
      step: 'start',
      group: null,
      content: { scale: [1, 2, 3, 5, 8, 13], roles: [], options: [], events: [] },

      displayName: '',
      participantToken: '',

      roleKey: '',
      initialScores: blankScores(),
      initialChoice: '',
      revisedScores: blankScores(),
      revisedChoice: '',

      consequences: { gained: [], lost: [], summary_key: null },
      initialErrors: [],
      eventKey: '',
      eventTitle: '',
      eventLead: '',
      adaptationStatus: '',
      groupResults: null,
      pdfExporting: false,
    };
  },
  computed: {
    dims() {
      return [
        { key: 'reach' },
        { key: 'impact' },
        { key: 'confidence' },
        { key: 'effort' },
      ];
    },
    steps() {
      return [
        { key: 'role', labelKey: 'agileTraining.rice.step.role' },
        { key: 'context', labelKey: 'agileTraining.rice.step.context' },
        { key: 'scores', labelKey: 'agileTraining.rice.step.scores' },
        { key: 'priorities', labelKey: 'agileTraining.rice.step.priorities' },
        { key: 'choose', labelKey: 'agileTraining.rice.step.choose' },
        { key: 'consequences', labelKey: 'agileTraining.rice.step.consequences' },
        { key: 'event', labelKey: 'agileTraining.rice.step.event' },
        { key: 'final', labelKey: 'agileTraining.rice.step.final' },
      ];
    },
    inReviseFlow() {
      return this.step === 'revise_scores' || this.step === 'revise_choose';
    },
    currentScores() {
      return this.inReviseFlow ? this.revisedScores : this.initialScores;
    },
    currentChoice: {
      get() { return this.inReviseFlow ? this.revisedChoice : this.initialChoice; },
      set(v) {
        if (this.inReviseFlow) this.revisedChoice = v;
        else this.initialChoice = v;
      },
    },
    rankedRows() {
      const rows = this.content.options.map(o => {
        const s = this.currentScores[o.key] || {};
        const v = Math.max(1, Number(s.reach) || 1);
        const t = Math.max(1, Number(s.impact) || 1);
        const r = Math.max(1, Number(s.confidence) || 1);
        const effort = Math.max(1, Number(s.effort) || 1);
        const scores = { reach: v, impact: t, confidence: r, effort };
        const rice = Math.round((v * t * r) / effort * 100) / 100;
        return { key: o.key, title: o.title, scores, rice };
      });
      const maxW = Math.max(...rows.map(r => r.rice), 1);
      const ranked = [...rows].sort((a, b) => b.rice - a.rice);
      const topKey = ranked[0]?.key;
      return ranked.map(r => ({
        ...r,
        isTop: r.key === topKey,
        pct: Math.round((r.rice / maxW) * 100),
      }));
    },
  },
  watch: {
    locale(v) {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('language', v);
        localStorage.setItem(`rice_locale_${this.slug}`, v);
      }
      if (this.$i18n) this.$i18n.locale = v;
      this.reloadContent();
    },
  },
  async mounted() {
    try {
      const stored = localStorage.getItem(`rice_locale_${this.slug}`) || localStorage.getItem('language');
      if (stored && ['ru', 'en'].includes(stored)) this.locale = stored;
      const token = localStorage.getItem(`rice_token_${this.slug}`);
      if (token) this.participantToken = token;
      const name = localStorage.getItem(`rice_name_${this.slug}`);
      if (name) this.displayName = name;

      await this.reloadContent();
      this.ensureScoreShape();
      // автоматический respond, если участник уже что-то делал
      if (this.participantToken && this.revisedChoice) {
        this.step = 'final';
        await this.loadGroupResults();
      } else if (this.participantToken && this.initialChoice) {
        this.step = 'event';
      } else if (this.participantToken && this.roleKey) {
        this.step = 'context';
      } else {
        this.step = 'start';
      }
    } finally {
      this.loading = false;
    }
  },
  methods: {
    setLocale(l) {
      if (!['ru', 'en'].includes(l)) return;
      this.locale = l;
    },
    optionTitle(key) {
      return (this.content.options.find(o => o.key === key) || {}).title || '';
    },
    riceOf(key) {
      const row = this.rankedRows.find(r => r.key === key);
      return row ? row.rice : '—';
    },
    stepBucket(s) {
      if (s === 'revise_scores') return 'scores';
      if (s === 'revise_choose') return 'choose';
      return s;
    },
    stepIndex(s) {
      const bucket = this.stepBucket(s);
      const i = this.steps.findIndex(x => x.key === bucket);
      return i === -1 ? 0 : i;
    },
    goStep(s) {
      this.step = s;
      if (typeof window !== 'undefined') {
        window.scrollTo({ top: 0, behavior: 'smooth' });
      }
    },
    ensureScoreShape() {
      // восстанавливаем пустые объекты, если API вернул меньше ключей
      const keys = this.content.options.map(o => o.key);
      const num = (v, legacy) => {
        const n = v !== undefined && v !== null && v !== '' ? Number(v) : NaN;
        if (Number.isFinite(n)) return n;
        const ln = legacy !== undefined && legacy !== null && legacy !== '' ? Number(legacy) : NaN;
        return Number.isFinite(ln) ? ln : 0;
      };
      const fix = (src) => {
        const out = {};
        for (const k of keys) {
          const b = src?.[k] || {};
          out[k] = {
            reach: num(b.reach, b.value),
            impact: num(b.impact, b.time),
            confidence: num(b.confidence, b.risk),
            effort: num(b.effort, b.size),
          };
        }
        return out;
      };
      this.initialScores = fix(this.initialScores);
      this.revisedScores = fix(this.revisedScores);
    },
    async reloadContent() {
      try {
        const params = { locale: this.locale };
        if (this.participantToken) params.participant_token = this.participantToken;
        const res = await axios.get(
          `/api/agile-training/rice/g/${this.slug}/state`, { params });
        this.group = res.data.group;
        this.content = res.data.content || this.content;
        const answer = res.data.answer;
        if (answer) {
          this.roleKey = answer.role_key;
          this.initialChoice = answer.initial_choice || '';
          this.revisedChoice = answer.revised_choice || '';
          this.eventKey = answer.event_key || '';
          this.adaptationStatus = answer.adaptation || '';
          const data = answer.data || {};
          if (data.initial?.scores) this.initialScores = this.clone(data.initial.scores);
          if (data.revised?.scores) this.revisedScores = this.clone(data.revised.scores);
          if (data.initial?.eval) {
            this.initialErrors = data.initial.eval.errors || [];
          }
          if (this.eventKey) {
            const ev = (this.content.events || []).find(e => e.key === this.eventKey);
            if (ev) { this.eventTitle = ev.title; this.eventLead = ev.lead; }
          }
          if (this.initialChoice) {
            this.consequences = this.localConsequences(this.initialChoice);
          }
        }
        this.ensureScoreShape();
      } catch (e) {
        console.error(e);
      }
    },
    clone(o) {
      const out = {};
      for (const k in o) out[k] = { ...o[k] };
      return out;
    },
    localConsequences(choice) {
      // дублирует серверное CONSEQUENCES для плавного UI без лишних запросов
      const map = {
        smart_onboarding: {
          gained: ['gain.quick_activation', 'gain.clean_learning'],
          lost: ['loss.not_biggest_reach'],
          summary_key: 'summary.onboarding',
        },
        referral_rework: {
          gained: ['gain.visible_growth'],
          lost: ['loss.low_confidence_bet', 'loss.quality_risk'],
          summary_key: 'summary.referral',
        },
        search_quality: {
          gained: ['gain.core_retention', 'gain.product_quality'],
          lost: ['loss.harder_to_explain'],
          summary_key: 'summary.search',
        },
      };
      return map[choice] || { gained: [], lost: [], summary_key: null };
    },
    async startRun() {
      if (this.displayName) {
        localStorage.setItem(`rice_name_${this.slug}`, this.displayName);
      }
      if (!this.participantToken) {
        try {
          const res = await axios.post(
            `/api/agile-training/g/${this.slug}/participant`,
            { display_name: this.displayName || null },
          );
          this.participantToken = res.data.participant_token;
          localStorage.setItem(`rice_token_${this.slug}`, this.participantToken);
          await this.reloadContent();
        } catch (e) {
          alert(e.response?.data?.error || 'Failed to join');
          return;
        }
      }
      this.goStep('role');
    },
    allScoresFilled(scores) {
      return this.content.options.every(o => {
        const s = scores[o.key];
        return s && s.reach && s.impact && s.confidence && s.effort;
      });
    },
    async submitCurrentRound() {
      if (!this.currentChoice) return;
      const round = this.inReviseFlow ? 'revised' : 'initial';
      const scores = round === 'initial' ? this.initialScores : this.revisedScores;
      // если какая-то оценка 0 — подставим 1, чтобы не ронять формулу
      for (const k of Object.keys(scores)) {
        for (const dim of ['reach', 'impact', 'confidence', 'effort']) {
          if (!scores[k][dim]) scores[k][dim] = 1;
        }
      }
      this.saving = true;
      try {
        const res = await axios.post(
          `/api/agile-training/rice/g/${this.slug}/answer`, {
            participant_token: this.participantToken,
            role_key: this.roleKey,
            round,
            scores,
            choice: this.currentChoice,
            locale: this.locale,
          });
        const data = res.data;
        if (round === 'initial') {
          this.initialErrors = data.eval?.errors || [];
          this.consequences = data.consequences || { gained: [], lost: [], summary_key: null };
          if (data.event) {
            this.eventKey = data.event.key;
            this.eventTitle = data.event.title;
            this.eventLead = data.event.lead;
          }
          this.goStep('consequences');
        } else {
          this.adaptationStatus = data.adaptation || '';
          await this.loadGroupResults();
          this.goStep('final');
        }
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.saving = false;
      }
    },
    startRevise() {
      // копируем начальные оценки в revised как стартовое состояние
      this.revisedScores = this.clone(this.initialScores);
      this.revisedChoice = this.initialChoice;
      this.goStep('revise_scores');
    },
    async loadGroupResults() {
      try {
        const res = await axios.get(
          `/api/agile-training/rice/g/${this.slug}/results`,
          { params: { locale: this.locale } });
        this.groupResults = res.data;
      } catch (_) { this.groupResults = null; }
    },
    async exportResultPdf() {
      const el = this.$refs.pdfExportRoot;
      if (!el) return;
      this.pdfExporting = true;
      try {
        const res = await exportElementToPdf(el, `agile-rice-${this.slug}`);
        if (!res.ok) throw new Error(res.error || 'export');
      } catch (e) {
        console.error(e);
        alert(this.$t('agileTraining.common.downloadPdfError'));
      } finally {
        this.pdfExporting = false;
      }
    },
    restart() {
      // не удаляем ответ на сервере, но позволяем пройти ещё раз локально
      this.initialScores = blankScores();
      this.revisedScores = blankScores();
      this.initialChoice = '';
      this.revisedChoice = '';
      this.adaptationStatus = '';
      this.consequences = { gained: [], lost: [], summary_key: null };
      this.initialErrors = [];
      this.goStep('role');
    },
  },
};
</script>

<style scoped>
.rice-pdf-bar { margin: 0 0 12px; }
.rice-pdf-root { min-height: 20px; }
.rice-play {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px 16px 60px;
  color: #1f1f3a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.rice-play__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.rice-play__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.rice-play__icon {
  font-size: 26px;
}
.rice-play__brand-title {
  font-size: 17px;
  font-weight: 700;
}
.rice-play__brand-sub {
  font-size: 13px;
  color: #6b6b8c;
}
.rice-play__lang {
  display: flex;
  gap: 6px;
}
.rice-lang__btn {
  background: #fff !important;
  border: 1px solid #e0e0f0 !important;
  color: #6b6b8c;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 12.5px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s, color .15s, border-color .15s;
}
.rice-lang__btn:hover {
  background: #f3f3ff !important;
  color: #4f46e5;
}
.rice-lang__btn.is-active {
  background: #6366f1 !important;
  color: #fff;
  border-color: #6366f1 !important;
}

.rice-steps {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 4px 0 12px;
  margin-bottom: 10px;
  border-bottom: 1px dashed #eee6ff;
}
.rice-steps__item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #8484a8;
  white-space: nowrap;
}
.rice-steps__num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #eee6ff;
  color: #6b6b8c;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
}
.rice-steps__item.is-active .rice-steps__num {
  background: #6366f1; color: #fff;
}
.rice-steps__item.is-active .rice-steps__label {
  color: #4f46e5; font-weight: 600;
}
.rice-steps__item.is-done .rice-steps__num {
  background: #c7d2fe; color: #3730a3;
}

.rice-play__loading {
  padding: 30px; text-align: center; color: #8484a8;
}

.rice-card {
  background: #fff;
  border: 1px solid #ececff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 2px 10px rgba(40, 40, 90, .05);
  margin-bottom: 16px;
}
.rice-card--center { text-align: center; }
.rice-card h1 { margin: 0 0 6px; font-size: 22px; }
.rice-card h2 { margin: 0 0 6px; font-size: 19px; }
.rice-card__lead { margin: 0 0 12px; color: #5a5a80; font-size: 14px; line-height: 1.5; }
.rice-card__actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.rice-btn {
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s, transform .1s, box-shadow .15s;
  border: 1px solid transparent;
}
.rice-btn--primary {
  background: #6366f1 !important;
  color: #fff;
  border: 1px solid #6366f1 !important;
}
.rice-btn--primary:hover:not(:disabled) {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  box-shadow: 0 6px 14px rgba(79, 70, 229, .3);
}
.rice-btn--primary:active:not(:disabled) {
  transform: translateY(1px);
  background: #4338ca !important;
  border-color: #4338ca !important;
}
.rice-btn--primary:disabled {
  background: #c7d2fe !important;
  border-color: #c7d2fe !important;
  cursor: not-allowed;
}
.rice-btn--ghost {
  background: #fff !important;
  color: #4f46e5 !important;
  border: 1px solid #d8d8f0 !important;
}
.rice-btn--ghost:hover:not(:disabled) {
  background: #f1f1ff !important;
  box-shadow: 0 2px 6px rgba(79, 70, 229, .15);
}
.rice-btn--ghost:active:not(:disabled) { transform: translateY(1px); }

.rice-defs {
  text-align: left;
  list-style: none;
  margin: 10px auto 16px;
  padding: 0;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}
.rice-start__name {
  display: flex; flex-direction: column; gap: 4px;
  margin: 10px auto;
  max-width: 360px;
  text-align: left;
  font-size: 13px;
  color: #5a5a80;
}
.rice-start__name input {
  padding: 10px 12px;
  border: 1px solid #d8d8f0;
  border-radius: 10px;
  font-size: 14px;
}

/* роли */
.rice-roles-grid {
  list-style: none;
  margin: 0; padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.rice-role-card {
  background: #fafaff;
  border: 2px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s, transform .1s;
}
.rice-role-card:hover {
  border-color: #c7d2fe;
  background: #f3f3ff;
  transform: translateY(-1px);
}
.rice-role-card.is-selected {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .15);
}
.rice-role-card__title { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.rice-role-card__focus {
  color: #6b6b8c;
  font-size: 12.5px;
  margin-bottom: 8px;
}
.rice-role-card__desc {
  margin: 0;
  font-size: 13px;
  color: #3a3a6b;
  line-height: 1.5;
}

/* контекст */
.rice-options {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 10px;
}
.rice-option {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
}
.rice-option__head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 10px; flex-wrap: wrap;
}
.rice-option__head h3 { margin: 0; font-size: 16px; }
.rice-option__short {
  color: #4f46e5;
  background: #eef0ff;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.rice-option__desc { margin: 8px 0; color: #3a3a6b; font-size: 13.5px; line-height: 1.5; }
.rice-option__meta { display: flex; gap: 6px; flex-wrap: wrap; }
.rice-chip {
  display: inline-flex; gap: 4px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 12.5px; font-weight: 600;
}
.rice-chip--money { background: #e9f7ec; color: #1f7a3b; }
.rice-chip--time  { background: #fff3e0; color: #a85a00; }
.rice-option__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 10px;
  font-size: 13px;
}
@media (max-width: 640px) {
  .rice-option__cols { grid-template-columns: 1fr; }
}
.rice-option__cols ul {
  margin: 4px 0 0;
  padding-left: 18px;
  color: #3a3a6b;
}

/* оценки */
.rice-scale-legend {
  display: flex; gap: 14px;
  margin-bottom: 12px; flex-wrap: wrap;
}
.rice-score-block {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 10px;
}
.rice-score-block__head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 10px; gap: 8px; flex-wrap: wrap;
}
.rice-score-block__head h3 { margin: 0; font-size: 15px; }
.rice-score-block__dims {
  display: flex; flex-direction: column; gap: 10px;
}
.rice-dim__label {
  display: flex; gap: 6px; margin-bottom: 6px;
  font-size: 13px; flex-wrap: wrap;
}
.rice-scale {
  display: flex; gap: 6px; flex-wrap: wrap;
}
.rice-scale__btn {
  background: #fff !important;
  color: #3a3a6b;
  border: 1px solid #d8d8f0 !important;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  min-width: 44px;
  transition: background .15s, color .15s, border-color .15s, transform .1s;
}
.rice-scale__btn:hover {
  background: #f1f1ff !important;
  border-color: #c7d2fe !important;
}
.rice-scale__btn.is-active {
  background: #6366f1 !important;
  color: #fff;
  border-color: #6366f1 !important;
  box-shadow: 0 4px 10px rgba(79, 70, 229, .25);
}
.rice-scale__btn:active { transform: translateY(1px); }

/* приоритеты */
.rice-formula {
  background: #eef0ff;
  color: #3a3a6b;
  padding: 10px 14px;
  border-radius: 10px;
  margin: 6px 0 14px;
  font-size: 14px;
}
.rice-formula code {
  background: transparent;
  color: #4f46e5;
  font-weight: 700;
}
.rice-priorities {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rice-priority {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 12px;
  padding: 12px 14px;
}
.rice-priority.is-top {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .12);
}
.rice-priority__head {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  margin-bottom: 6px;
}
.rice-priority__score {
  font-weight: 800;
  color: #4f46e5;
}
.rice-priority__bar {
  height: 8px;
  background: #eee6ff;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}
.rice-priority__bar > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width .2s;
}
.rice-priority__dims {
  display: flex; gap: 10px; color: #6b6b8c; font-size: 12.5px;
}

/* выбор */
.rice-choice {
  list-style: none;
  margin: 0; padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rice-choice__item {
  background: #fafaff;
  border: 2px solid #eee6ff;
  border-radius: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.rice-choice__item:hover {
  background: #f3f3ff;
  border-color: #c7d2fe;
}
.rice-choice__item.is-selected {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .15);
}
.rice-choice__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 14.5px;
}
.rice-choice__short {
  color: #6b6b8c;
  font-size: 12.5px;
  margin-top: 3px;
}

/* последствия */
.rice-cons-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 8px;
}
@media (max-width: 640px) {
  .rice-cons-cols { grid-template-columns: 1fr; }
}
.rice-cons-col {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid;
}
.rice-cons-col h3 { margin: 0 0 8px; font-size: 15px; }
.rice-cons-col ul { margin: 0; padding-left: 18px; font-size: 13.5px; line-height: 1.5; }
.rice-cons-col--gain { background: #f0faf3; border-color: #c9ecd2; color: #1f5b33; }
.rice-cons-col--loss { background: #fdf2f2; border-color: #f4c2c2; color: #7a2a2a; }

.rice-warnings {
  margin-top: 14px;
  padding: 12px 14px;
  background: #fff8e6;
  border: 1px solid #f4dfa0;
  border-radius: 12px;
  color: #8a5a00;
}
.rice-warnings h4 { margin: 0 0 6px; font-size: 14px; }
.rice-warnings ul { margin: 0; padding-left: 18px; font-size: 13px; }

/* событие */
.rice-event {
  padding: 16px;
  background: linear-gradient(135deg, #eef0ff 0%, #fbeffb 100%);
  border-radius: 14px;
  margin-bottom: 10px;
}
.rice-event__badge {
  display: inline-block;
  background: #4f46e5;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: .6px;
  padding: 3px 10px;
  border-radius: 999px;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.rice-event h2 { margin: 0 0 6px; font-size: 18px; color: #1f1f3a; }
.rice-event__lead { margin: 0; color: #3a3a6b; font-size: 14px; line-height: 1.5; }
.rice-note {
  margin-top: 10px;
  background: #f3f3ff;
  padding: 10px 14px;
  border-radius: 10px;
  color: #3a3a6b;
  font-size: 13.5px;
}

/* финал */
.rice-final-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 14px 0 20px;
}
@media (max-width: 640px) {
  .rice-final-grid { grid-template-columns: 1fr; }
}
.rice-final-card {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}
.rice-final-card b { display: block; margin-top: 4px; font-size: 15px; }
.rice-final-card--changed {
  background: #eef7ff;
  border-color: #bfd8f5;
}
.rice-final-card--changed b { color: #2057b8; }

.rice-group { margin-top: 10px; }
.rice-group h3 { margin: 0 0 6px; font-size: 16px; }
.rice-group-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 8px;
}
@media (max-width: 720px) {
  .rice-group-cols { grid-template-columns: 1fr; }
}
.rice-group-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
}
.rice-group-list li {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 8px;
  margin-bottom: 4px;
  font-size: 13px;
}

.rice-fac__hint { font-size: 12px; color: #6b6b8c; }
</style>
