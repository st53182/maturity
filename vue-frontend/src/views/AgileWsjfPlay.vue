<template>
  <div class="wsjf-play">
    <header class="wsjf-play__top">
      <div class="wsjf-play__brand">
        <span class="wsjf-play__icon">⚖️</span>
        <div>
          <div class="wsjf-play__brand-title">{{ $t('agileTraining.wsjf.playTitle') }}</div>
          <div class="wsjf-play__brand-sub" v-if="group">{{ group.name }}</div>
        </div>
      </div>
      <div class="wsjf-play__lang">
        <button type="button" class="wsjf-lang__btn"
                :class="{ 'is-active': locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button type="button" class="wsjf-lang__btn"
                :class="{ 'is-active': locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
    </header>

    <!-- Прогресс -->
    <nav v-if="!loading && step !== 'start'" class="wsjf-steps">
      <div v-for="(s, i) in steps" :key="s.key"
           class="wsjf-steps__item"
           :class="{ 'is-active': stepBucket(step) === s.key, 'is-done': stepIndex(step) > i }">
        <span class="wsjf-steps__num">{{ i + 1 }}</span>
        <span class="wsjf-steps__label">{{ $t(s.labelKey) }}</span>
      </div>
    </nav>

    <div v-if="loading" class="wsjf-play__loading">{{ $t('common.loading') }}…</div>

    <!-- 0. Start -->
    <section v-else-if="step === 'start'" class="wsjf-card wsjf-card--center">
      <h1>{{ $t('agileTraining.wsjf.startTitle') }}</h1>
      <p class="wsjf-card__lead">{{ $t('agileTraining.wsjf.startLead') }}</p>
      <ul class="wsjf-defs">
        <li>🎯 {{ $t('agileTraining.wsjf.startBullet1') }}</li>
        <li>⏱ {{ $t('agileTraining.wsjf.startBullet2') }}</li>
        <li>🧠 {{ $t('agileTraining.wsjf.startBullet3') }}</li>
      </ul>
      <label class="wsjf-start__name">
        <span>{{ $t('agileTraining.common.yourName') }}</span>
        <input v-model="displayName" maxlength="60"
               :placeholder="$t('agileTraining.common.yourNamePh')" />
      </label>
      <button class="wsjf-btn wsjf-btn--primary" @click="startRun">
        {{ $t('agileTraining.wsjf.start') }}
      </button>
    </section>

    <!-- 1. Role -->
    <section v-else-if="step === 'role'" class="wsjf-card">
      <h2>{{ $t('agileTraining.wsjf.roleTitle') }}</h2>
      <p class="wsjf-card__lead">{{ $t('agileTraining.wsjf.roleLead') }}</p>
      <ul class="wsjf-roles-grid">
        <li v-for="r in content.roles" :key="r.key"
            class="wsjf-role-card"
            :class="{ 'is-selected': roleKey === r.key }"
            @click="roleKey = r.key">
          <div class="wsjf-role-card__title">{{ r.title }}</div>
          <div class="wsjf-role-card__focus">{{ r.focus }}</div>
          <p class="wsjf-role-card__desc">{{ r.desc }}</p>
        </li>
      </ul>
      <div class="wsjf-card__actions">
        <span></span>
        <button class="wsjf-btn wsjf-btn--primary" :disabled="!roleKey" @click="goStep('context')">
          {{ $t('agileTraining.wsjf.next') }} →
        </button>
      </div>
    </section>

    <!-- 2. Context -->
    <section v-else-if="step === 'context'" class="wsjf-card">
      <h2>{{ content.context?.title || $t('agileTraining.wsjf.contextTitle') }}</h2>
      <p class="wsjf-card__lead">{{ content.context?.lead }}</p>
      <div class="wsjf-options">
        <article v-for="o in content.options" :key="o.key" class="wsjf-option">
          <div class="wsjf-option__head">
            <h3>{{ o.title }}</h3>
            <span class="wsjf-option__short">{{ o.short }}</span>
          </div>
          <p class="wsjf-option__desc">{{ o.description }}</p>
          <div class="wsjf-option__meta">
            <span class="wsjf-chip wsjf-chip--money">💰 {{ o.revenue_label }}</span>
            <span class="wsjf-chip wsjf-chip--time">⏱ {{ o.time_label }}</span>
          </div>
          <div class="wsjf-option__cols">
            <div>
              <b>✅ {{ $t('agileTraining.wsjf.strengths') }}</b>
              <ul><li v-for="s in o.strengths" :key="s">{{ s }}</li></ul>
            </div>
            <div>
              <b>⚠️ {{ $t('agileTraining.wsjf.risks') }}</b>
              <ul><li v-for="rk in o.risks" :key="rk">{{ rk }}</li></ul>
            </div>
          </div>
        </article>
      </div>
      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost" @click="goStep('role')">
          ← {{ $t('agileTraining.wsjf.back') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary" @click="goStep('scores')">
          {{ $t('agileTraining.wsjf.goToScores') }} →
        </button>
      </div>
    </section>

    <!-- 3. Scores -->
    <section v-else-if="stepBucket(step) === 'scores'" class="wsjf-card">
      <h2>
        {{ step === 'revise_scores'
           ? $t('agileTraining.wsjf.reviseScoresTitle')
           : $t('agileTraining.wsjf.scoresTitle') }}
      </h2>
      <p class="wsjf-card__lead">{{ $t('agileTraining.wsjf.scoresLead') }}</p>
      <div class="wsjf-scale-legend">
        <span class="wsjf-fac__hint">1 — {{ $t('agileTraining.wsjf.legend.low') }}</span>
        <span class="wsjf-fac__hint">5 — {{ $t('agileTraining.wsjf.legend.mid') }}</span>
        <span class="wsjf-fac__hint">13 — {{ $t('agileTraining.wsjf.legend.high') }}</span>
      </div>
      <div v-for="o in content.options" :key="o.key" class="wsjf-score-block">
        <div class="wsjf-score-block__head">
          <h3>{{ o.title }}</h3>
          <span class="wsjf-option__short">{{ o.short }}</span>
        </div>
        <div class="wsjf-score-block__dims">
          <div v-for="dim in dims" :key="dim.key" class="wsjf-dim">
            <div class="wsjf-dim__label">
              <b>{{ $t('agileTraining.wsjf.dim.' + dim.key) }}</b>
              <span class="wsjf-fac__hint">— {{ $t('agileTraining.wsjf.dim.' + dim.key + 'Hint') }}</span>
            </div>
            <div class="wsjf-scale">
              <button v-for="v in content.scale" :key="dim.key + '-' + v"
                      type="button" class="wsjf-scale__btn"
                      :class="{ 'is-active': currentScores[o.key][dim.key] === v }"
                      @click="currentScores[o.key][dim.key] = v">
                {{ v }}
              </button>
            </div>
          </div>
        </div>
      </div>
      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost"
                @click="goStep(step === 'revise_scores' ? 'event' : 'context')">
          ← {{ $t('agileTraining.wsjf.back') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary" @click="goStep('priorities')">
          {{ $t('agileTraining.wsjf.calcPriority') }} →
        </button>
      </div>
    </section>

    <!-- 4. Priorities -->
    <section v-else-if="step === 'priorities'" class="wsjf-card">
      <h2>{{ $t('agileTraining.wsjf.prioritiesTitle') }}</h2>
      <p class="wsjf-card__lead">{{ $t('agileTraining.wsjf.prioritiesLead') }}</p>
      <div class="wsjf-formula">
        <code>{{ $t('agileTraining.wsjf.formula') }}</code>
      </div>
      <ul class="wsjf-priorities">
        <li v-for="row in rankedRows" :key="row.key"
            class="wsjf-priority"
            :class="{ 'is-top': row.isTop }">
          <div class="wsjf-priority__head">
            <b>{{ row.title }}</b>
            <span class="wsjf-priority__score">{{ row.wsjf }}</span>
          </div>
          <div class="wsjf-priority__bar">
            <span :style="{ width: row.pct + '%' }"></span>
          </div>
          <div class="wsjf-priority__dims">
            <span>V: {{ row.scores.value }}</span>
            <span>U: {{ row.scores.urgency }}</span>
            <span>C: {{ row.scores.complexity }}</span>
          </div>
        </li>
      </ul>
      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost" @click="goStep(inReviseFlow ? 'revise_scores' : 'scores')">
          ← {{ $t('agileTraining.wsjf.back') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary" @click="goStep(inReviseFlow ? 'revise_choose' : 'choose')">
          {{ $t('agileTraining.wsjf.goToChoose') }} →
        </button>
      </div>
    </section>

    <!-- 5. Choose / Revise-Choose -->
    <section v-else-if="stepBucket(step) === 'choose'" class="wsjf-card">
      <h2>
        {{ step === 'revise_choose'
           ? $t('agileTraining.wsjf.reviseChooseTitle')
           : $t('agileTraining.wsjf.chooseTitle') }}
      </h2>
      <p class="wsjf-card__lead">{{ $t('agileTraining.wsjf.chooseLead') }}</p>
      <ul class="wsjf-choice">
        <li v-for="o in content.options" :key="o.key"
            class="wsjf-choice__item"
            :class="{ 'is-selected': currentChoice === o.key }"
            @click="currentChoice = o.key">
          <div class="wsjf-choice__head">
            <b>{{ o.title }}</b>
            <span class="wsjf-fac__hint">WSJF: {{ wsjfOf(o.key) }}</span>
          </div>
          <div class="wsjf-choice__short">{{ o.short }}</div>
        </li>
      </ul>
      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost"
                @click="goStep(inReviseFlow ? 'revise_scores' : 'priorities')">
          ← {{ $t('agileTraining.wsjf.back') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary"
                :disabled="!currentChoice || saving"
                @click="submitCurrentRound">
          {{ saving
             ? $t('common.saving') + '…'
             : (inReviseFlow
                ? $t('agileTraining.wsjf.finish')
                : $t('agileTraining.wsjf.lockIn')) }} →
        </button>
      </div>
    </section>

    <!-- 6. Consequences -->
    <section v-else-if="step === 'consequences'" class="wsjf-card">
      <h2>{{ $t('agileTraining.wsjf.consequencesTitle') }}</h2>
      <p class="wsjf-card__lead" v-if="consequences.summary_key">
        {{ $t('agileTraining.wsjf.consequences.' + consequences.summary_key) }}
      </p>
      <div class="wsjf-cons-cols">
        <div class="wsjf-cons-col wsjf-cons-col--gain">
          <h3>✅ {{ $t('agileTraining.wsjf.youGained') }}</h3>
          <ul>
            <li v-for="k in consequences.gained" :key="'g-' + k">
              {{ $t('agileTraining.wsjf.consequences.' + k) }}
            </li>
          </ul>
        </div>
        <div class="wsjf-cons-col wsjf-cons-col--loss">
          <h3>⚠️ {{ $t('agileTraining.wsjf.youLost') }}</h3>
          <ul>
            <li v-for="k in consequences.lost" :key="'l-' + k">
              {{ $t('agileTraining.wsjf.consequences.' + k) }}
            </li>
          </ul>
        </div>
      </div>

      <!-- подсветка ошибок -->
      <div v-if="initialErrors.length" class="wsjf-warnings">
        <h4>🧭 {{ $t('agileTraining.wsjf.heyLook') }}</h4>
        <ul>
          <li v-for="er in initialErrors" :key="er">
            {{ $t('agileTraining.wsjf.err.' + er) }}
          </li>
        </ul>
      </div>

      <div class="wsjf-card__actions">
        <span></span>
        <button class="wsjf-btn wsjf-btn--primary" @click="goStep('event')">
          {{ $t('agileTraining.wsjf.nextNews') }} →
        </button>
      </div>
    </section>

    <!-- 7. Event + Revise -->
    <section v-else-if="step === 'event'" class="wsjf-card">
      <div class="wsjf-event">
        <span class="wsjf-event__badge">📰 {{ $t('agileTraining.wsjf.breaking') }}</span>
        <h2>{{ eventTitle }}</h2>
        <p class="wsjf-event__lead">{{ eventLead }}</p>
      </div>
      <div class="wsjf-note">
        {{ $t('agileTraining.wsjf.eventNote') }}
      </div>
      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost" @click="goStep('consequences')">
          ← {{ $t('agileTraining.wsjf.back') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary" @click="startRevise">
          {{ $t('agileTraining.wsjf.rethink') }} →
        </button>
      </div>
    </section>

    <!-- 8. Final -->
    <section v-else-if="step === 'final'" class="wsjf-card">
      <h2>{{ $t('agileTraining.wsjf.finalTitle') }}</h2>
      <p class="wsjf-card__lead" v-if="adaptationStatus">
        {{ $t('agileTraining.wsjf.adaptationLead.' + adaptationStatus) }}
      </p>

      <div class="wsjf-final-grid">
        <div class="wsjf-final-card">
          <div class="wsjf-fac__hint">{{ $t('agileTraining.wsjf.initialChoice') }}</div>
          <b>{{ optionTitle(initialChoice) || '—' }}</b>
        </div>
        <div class="wsjf-final-card">
          <div class="wsjf-fac__hint">{{ $t('agileTraining.wsjf.revisedChoice') }}</div>
          <b>{{ optionTitle(revisedChoice) || '—' }}</b>
        </div>
        <div class="wsjf-final-card"
             :class="{ 'wsjf-final-card--changed': initialChoice !== revisedChoice && revisedChoice }">
          <div class="wsjf-fac__hint">{{ $t('agileTraining.wsjf.changedMind') }}</div>
          <b>
            {{ initialChoice !== revisedChoice && revisedChoice
               ? $t('agileTraining.wsjf.yesChanged')
               : $t('agileTraining.wsjf.noKept') }}
          </b>
        </div>
      </div>

      <div v-if="groupResults" class="wsjf-group">
        <h3>👥 {{ $t('agileTraining.wsjf.yourGroup') }}</h3>
        <p class="wsjf-fac__hint">
          {{ $t('agileTraining.facilitator.participants',
                { n: groupResults.total_participants || 0 }, groupResults.total_participants || 0) }}
          · {{ $t('agileTraining.wsjf.answersCount',
                   { n: groupResults.total_answers || 0 }, groupResults.total_answers || 0) }}
        </p>
        <div class="wsjf-group-cols">
          <div>
            <b>{{ $t('agileTraining.wsjf.initialChoice') }}</b>
            <ul class="wsjf-group-list">
              <li v-for="o in content.options" :key="'ig-' + o.key">
                <span>{{ o.title }}</span>
                <b>{{ groupResults.initial_counts[o.key] || 0 }}</b>
              </li>
            </ul>
          </div>
          <div>
            <b>{{ $t('agileTraining.wsjf.revisedChoice') }}</b>
            <ul class="wsjf-group-list">
              <li v-for="o in content.options" :key="'rg-' + o.key">
                <span>{{ o.title }}</span>
                <b>{{ groupResults.revised_counts[o.key] || 0 }}</b>
              </li>
            </ul>
          </div>
          <div>
            <b>{{ $t('agileTraining.wsjf.adaptations') }}</b>
            <ul class="wsjf-group-list">
              <li v-for="(cnt, key) in groupResults.adaptation_counts" :key="'a-' + key">
                <span>{{ $t('agileTraining.wsjf.adaptation.' + key) }}</span>
                <b>{{ cnt }}</b>
              </li>
              <li v-if="!Object.keys(groupResults.adaptation_counts || {}).length"
                  class="wsjf-fac__hint">
                — {{ $t('agileTraining.wsjf.noAdaptationYet') }}
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="wsjf-card__actions">
        <button class="wsjf-btn wsjf-btn--ghost" @click="loadGroupResults">
          🔄 {{ $t('agileTraining.wsjf.refreshGroup') }}
        </button>
        <button class="wsjf-btn wsjf-btn--primary" @click="restart">
          {{ $t('agileTraining.wsjf.tryAgain') }}
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

const DEFAULT_OPTION_KEYS = ['hybrid', 'electric', 'hydrogen'];

function blankScores() {
  const out = {};
  for (const k of DEFAULT_OPTION_KEYS) {
    out[k] = { value: 0, urgency: 0, complexity: 0 };
  }
  return out;
}

export default {
  name: 'AgileWsjfPlay',
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
    };
  },
  computed: {
    dims() {
      return [
        { key: 'value' },
        { key: 'urgency' },
        { key: 'complexity' },
      ];
    },
    steps() {
      return [
        { key: 'role', labelKey: 'agileTraining.wsjf.step.role' },
        { key: 'context', labelKey: 'agileTraining.wsjf.step.context' },
        { key: 'scores', labelKey: 'agileTraining.wsjf.step.scores' },
        { key: 'priorities', labelKey: 'agileTraining.wsjf.step.priorities' },
        { key: 'choose', labelKey: 'agileTraining.wsjf.step.choose' },
        { key: 'consequences', labelKey: 'agileTraining.wsjf.step.consequences' },
        { key: 'event', labelKey: 'agileTraining.wsjf.step.event' },
        { key: 'final', labelKey: 'agileTraining.wsjf.step.final' },
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
        const scores = this.currentScores[o.key] || { value: 1, urgency: 1, complexity: 1 };
        const c = Math.max(1, Number(scores.complexity) || 1);
        const wsjf = Math.round(((Number(scores.value) || 1) + (Number(scores.urgency) || 1)) / c * 100) / 100;
        return { key: o.key, title: o.title, scores, wsjf };
      });
      const maxW = Math.max(...rows.map(r => r.wsjf), 1);
      const ranked = [...rows].sort((a, b) => b.wsjf - a.wsjf);
      const topKey = ranked[0]?.key;
      return ranked.map(r => ({
        ...r,
        isTop: r.key === topKey,
        pct: Math.round((r.wsjf / maxW) * 100),
      }));
    },
  },
  watch: {
    locale(v) {
      if (typeof localStorage !== 'undefined') {
        localStorage.setItem('language', v);
        localStorage.setItem(`wsjf_locale_${this.slug}`, v);
      }
      if (this.$i18n) this.$i18n.locale = v;
      this.reloadContent();
    },
  },
  async mounted() {
    try {
      const stored = localStorage.getItem(`wsjf_locale_${this.slug}`) || localStorage.getItem('language');
      if (stored && ['ru', 'en'].includes(stored)) this.locale = stored;
      const token = localStorage.getItem(`wsjf_token_${this.slug}`);
      if (token) this.participantToken = token;
      const name = localStorage.getItem(`wsjf_name_${this.slug}`);
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
    wsjfOf(key) {
      const row = this.rankedRows.find(r => r.key === key);
      return row ? row.wsjf : '—';
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
      const fix = (src) => {
        const out = {};
        for (const k of keys) {
          out[k] = {
            value: src?.[k]?.value || 0,
            urgency: src?.[k]?.urgency || 0,
            complexity: src?.[k]?.complexity || 0,
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
          `/api/agile-training/wsjf/g/${this.slug}/state`, { params });
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
        hybrid: {
          gained: ['gain.quick_revenue', 'gain.proven_tech'],
          lost: ['loss.weak_future', 'loss.market_shift_risk'],
          summary_key: 'summary.hybrid',
        },
        electric: {
          gained: ['gain.balance', 'gain.market_growth', 'gain.contract_secured'],
          lost: ['loss.tech_risk', 'loss.capex'],
          summary_key: 'summary.electric',
        },
        hydrogen: {
          gained: ['gain.breakthrough', 'gain.first_mover'],
          lost: ['loss.long_dry_period', 'loss.tech_risk_high'],
          summary_key: 'summary.hydrogen',
        },
      };
      return map[choice] || { gained: [], lost: [], summary_key: null };
    },
    async startRun() {
      if (this.displayName) {
        localStorage.setItem(`wsjf_name_${this.slug}`, this.displayName);
      }
      if (!this.participantToken) {
        try {
          const res = await axios.post(
            `/api/agile-training/g/${this.slug}/participant`,
            { display_name: this.displayName || null },
          );
          this.participantToken = res.data.participant_token;
          localStorage.setItem(`wsjf_token_${this.slug}`, this.participantToken);
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
        return s && s.value && s.urgency && s.complexity;
      });
    },
    async submitCurrentRound() {
      if (!this.currentChoice) return;
      const round = this.inReviseFlow ? 'revised' : 'initial';
      const scores = round === 'initial' ? this.initialScores : this.revisedScores;
      // если какая-то оценка 0 — подставим 1, чтобы не ронять формулу
      for (const k of Object.keys(scores)) {
        for (const dim of ['value', 'urgency', 'complexity']) {
          if (!scores[k][dim]) scores[k][dim] = 1;
        }
      }
      this.saving = true;
      try {
        const res = await axios.post(
          `/api/agile-training/wsjf/g/${this.slug}/answer`, {
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
          `/api/agile-training/wsjf/g/${this.slug}/results`,
          { params: { locale: this.locale } });
        this.groupResults = res.data;
      } catch (_) { this.groupResults = null; }
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
.wsjf-play {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px 16px 60px;
  color: #1f1f3a;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.wsjf-play__top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.wsjf-play__brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.wsjf-play__icon {
  font-size: 26px;
}
.wsjf-play__brand-title {
  font-size: 17px;
  font-weight: 700;
}
.wsjf-play__brand-sub {
  font-size: 13px;
  color: #6b6b8c;
}
.wsjf-play__lang {
  display: flex;
  gap: 6px;
}
.wsjf-lang__btn {
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
.wsjf-lang__btn:hover {
  background: #f3f3ff !important;
  color: #4f46e5;
}
.wsjf-lang__btn.is-active {
  background: #6366f1 !important;
  color: #fff;
  border-color: #6366f1 !important;
}

.wsjf-steps {
  display: flex;
  gap: 6px;
  overflow-x: auto;
  padding: 4px 0 12px;
  margin-bottom: 10px;
  border-bottom: 1px dashed #eee6ff;
}
.wsjf-steps__item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  font-size: 12px;
  color: #8484a8;
  white-space: nowrap;
}
.wsjf-steps__num {
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
.wsjf-steps__item.is-active .wsjf-steps__num {
  background: #6366f1; color: #fff;
}
.wsjf-steps__item.is-active .wsjf-steps__label {
  color: #4f46e5; font-weight: 600;
}
.wsjf-steps__item.is-done .wsjf-steps__num {
  background: #c7d2fe; color: #3730a3;
}

.wsjf-play__loading {
  padding: 30px; text-align: center; color: #8484a8;
}

.wsjf-card {
  background: #fff;
  border: 1px solid #ececff;
  border-radius: 18px;
  padding: 22px;
  box-shadow: 0 2px 10px rgba(40, 40, 90, .05);
  margin-bottom: 16px;
}
.wsjf-card--center { text-align: center; }
.wsjf-card h1 { margin: 0 0 6px; font-size: 22px; }
.wsjf-card h2 { margin: 0 0 6px; font-size: 19px; }
.wsjf-card__lead { margin: 0 0 12px; color: #5a5a80; font-size: 14px; line-height: 1.5; }
.wsjf-card__actions {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.wsjf-btn {
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: background .15s, transform .1s, box-shadow .15s;
  border: 1px solid transparent;
}
.wsjf-btn--primary {
  background: #6366f1 !important;
  color: #fff;
  border: 1px solid #6366f1 !important;
}
.wsjf-btn--primary:hover:not(:disabled) {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  box-shadow: 0 6px 14px rgba(79, 70, 229, .3);
}
.wsjf-btn--primary:active:not(:disabled) {
  transform: translateY(1px);
  background: #4338ca !important;
  border-color: #4338ca !important;
}
.wsjf-btn--primary:disabled {
  background: #c7d2fe !important;
  border-color: #c7d2fe !important;
  cursor: not-allowed;
}
.wsjf-btn--ghost {
  background: #fff !important;
  color: #4f46e5 !important;
  border: 1px solid #d8d8f0 !important;
}
.wsjf-btn--ghost:hover:not(:disabled) {
  background: #f1f1ff !important;
  box-shadow: 0 2px 6px rgba(79, 70, 229, .15);
}
.wsjf-btn--ghost:active:not(:disabled) { transform: translateY(1px); }

.wsjf-defs {
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
.wsjf-start__name {
  display: flex; flex-direction: column; gap: 4px;
  margin: 10px auto;
  max-width: 360px;
  text-align: left;
  font-size: 13px;
  color: #5a5a80;
}
.wsjf-start__name input {
  padding: 10px 12px;
  border: 1px solid #d8d8f0;
  border-radius: 10px;
  font-size: 14px;
}

/* роли */
.wsjf-roles-grid {
  list-style: none;
  margin: 0; padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 12px;
}
.wsjf-role-card {
  background: #fafaff;
  border: 2px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s, transform .1s;
}
.wsjf-role-card:hover {
  border-color: #c7d2fe;
  background: #f3f3ff;
  transform: translateY(-1px);
}
.wsjf-role-card.is-selected {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .15);
}
.wsjf-role-card__title { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.wsjf-role-card__focus {
  color: #6b6b8c;
  font-size: 12.5px;
  margin-bottom: 8px;
}
.wsjf-role-card__desc {
  margin: 0;
  font-size: 13px;
  color: #3a3a6b;
  line-height: 1.5;
}

/* контекст */
.wsjf-options {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-top: 10px;
}
.wsjf-option {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
}
.wsjf-option__head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 10px; flex-wrap: wrap;
}
.wsjf-option__head h3 { margin: 0; font-size: 16px; }
.wsjf-option__short {
  color: #4f46e5;
  background: #eef0ff;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.wsjf-option__desc { margin: 8px 0; color: #3a3a6b; font-size: 13.5px; line-height: 1.5; }
.wsjf-option__meta { display: flex; gap: 6px; flex-wrap: wrap; }
.wsjf-chip {
  display: inline-flex; gap: 4px;
  padding: 3px 10px; border-radius: 999px;
  font-size: 12.5px; font-weight: 600;
}
.wsjf-chip--money { background: #e9f7ec; color: #1f7a3b; }
.wsjf-chip--time  { background: #fff3e0; color: #a85a00; }
.wsjf-option__cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
  margin-top: 10px;
  font-size: 13px;
}
@media (max-width: 640px) {
  .wsjf-option__cols { grid-template-columns: 1fr; }
}
.wsjf-option__cols ul {
  margin: 4px 0 0;
  padding-left: 18px;
  color: #3a3a6b;
}

/* оценки */
.wsjf-scale-legend {
  display: flex; gap: 14px;
  margin-bottom: 12px; flex-wrap: wrap;
}
.wsjf-score-block {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 10px;
}
.wsjf-score-block__head {
  display: flex; justify-content: space-between; align-items: baseline;
  margin-bottom: 10px; gap: 8px; flex-wrap: wrap;
}
.wsjf-score-block__head h3 { margin: 0; font-size: 15px; }
.wsjf-score-block__dims {
  display: flex; flex-direction: column; gap: 10px;
}
.wsjf-dim__label {
  display: flex; gap: 6px; margin-bottom: 6px;
  font-size: 13px; flex-wrap: wrap;
}
.wsjf-scale {
  display: flex; gap: 6px; flex-wrap: wrap;
}
.wsjf-scale__btn {
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
.wsjf-scale__btn:hover {
  background: #f1f1ff !important;
  border-color: #c7d2fe !important;
}
.wsjf-scale__btn.is-active {
  background: #6366f1 !important;
  color: #fff;
  border-color: #6366f1 !important;
  box-shadow: 0 4px 10px rgba(79, 70, 229, .25);
}
.wsjf-scale__btn:active { transform: translateY(1px); }

/* приоритеты */
.wsjf-formula {
  background: #eef0ff;
  color: #3a3a6b;
  padding: 10px 14px;
  border-radius: 10px;
  margin: 6px 0 14px;
  font-size: 14px;
}
.wsjf-formula code {
  background: transparent;
  color: #4f46e5;
  font-weight: 700;
}
.wsjf-priorities {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.wsjf-priority {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 12px;
  padding: 12px 14px;
}
.wsjf-priority.is-top {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .12);
}
.wsjf-priority__head {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  margin-bottom: 6px;
}
.wsjf-priority__score {
  font-weight: 800;
  color: #4f46e5;
}
.wsjf-priority__bar {
  height: 8px;
  background: #eee6ff;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 6px;
}
.wsjf-priority__bar > span {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  transition: width .2s;
}
.wsjf-priority__dims {
  display: flex; gap: 10px; color: #6b6b8c; font-size: 12.5px;
}

/* выбор */
.wsjf-choice {
  list-style: none;
  margin: 0; padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.wsjf-choice__item {
  background: #fafaff;
  border: 2px solid #eee6ff;
  border-radius: 12px;
  padding: 12px 14px;
  cursor: pointer;
  transition: border-color .15s, background .15s;
}
.wsjf-choice__item:hover {
  background: #f3f3ff;
  border-color: #c7d2fe;
}
.wsjf-choice__item.is-selected {
  border-color: #6366f1;
  background: #eef0ff;
  box-shadow: 0 4px 12px rgba(79, 70, 229, .15);
}
.wsjf-choice__head {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 14.5px;
}
.wsjf-choice__short {
  color: #6b6b8c;
  font-size: 12.5px;
  margin-top: 3px;
}

/* последствия */
.wsjf-cons-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 8px;
}
@media (max-width: 640px) {
  .wsjf-cons-cols { grid-template-columns: 1fr; }
}
.wsjf-cons-col {
  padding: 14px;
  border-radius: 12px;
  border: 1px solid;
}
.wsjf-cons-col h3 { margin: 0 0 8px; font-size: 15px; }
.wsjf-cons-col ul { margin: 0; padding-left: 18px; font-size: 13.5px; line-height: 1.5; }
.wsjf-cons-col--gain { background: #f0faf3; border-color: #c9ecd2; color: #1f5b33; }
.wsjf-cons-col--loss { background: #fdf2f2; border-color: #f4c2c2; color: #7a2a2a; }

.wsjf-warnings {
  margin-top: 14px;
  padding: 12px 14px;
  background: #fff8e6;
  border: 1px solid #f4dfa0;
  border-radius: 12px;
  color: #8a5a00;
}
.wsjf-warnings h4 { margin: 0 0 6px; font-size: 14px; }
.wsjf-warnings ul { margin: 0; padding-left: 18px; font-size: 13px; }

/* событие */
.wsjf-event {
  padding: 16px;
  background: linear-gradient(135deg, #eef0ff 0%, #fbeffb 100%);
  border-radius: 14px;
  margin-bottom: 10px;
}
.wsjf-event__badge {
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
.wsjf-event h2 { margin: 0 0 6px; font-size: 18px; color: #1f1f3a; }
.wsjf-event__lead { margin: 0; color: #3a3a6b; font-size: 14px; line-height: 1.5; }
.wsjf-note {
  margin-top: 10px;
  background: #f3f3ff;
  padding: 10px 14px;
  border-radius: 10px;
  color: #3a3a6b;
  font-size: 13.5px;
}

/* финал */
.wsjf-final-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 14px 0 20px;
}
@media (max-width: 640px) {
  .wsjf-final-grid { grid-template-columns: 1fr; }
}
.wsjf-final-card {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 12px;
  padding: 14px;
  text-align: center;
}
.wsjf-final-card b { display: block; margin-top: 4px; font-size: 15px; }
.wsjf-final-card--changed {
  background: #eef7ff;
  border-color: #bfd8f5;
}
.wsjf-final-card--changed b { color: #2057b8; }

.wsjf-group { margin-top: 10px; }
.wsjf-group h3 { margin: 0 0 6px; font-size: 16px; }
.wsjf-group-cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-top: 8px;
}
@media (max-width: 720px) {
  .wsjf-group-cols { grid-template-columns: 1fr; }
}
.wsjf-group-list {
  list-style: none;
  margin: 6px 0 0;
  padding: 0;
}
.wsjf-group-list li {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 8px;
  margin-bottom: 4px;
  font-size: 13px;
}

.wsjf-fac__hint { font-size: 12px; color: #6b6b8c; }
</style>
