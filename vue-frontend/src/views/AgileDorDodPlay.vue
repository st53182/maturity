<template>
  <div class="dd-play">
    <header class="dd-play__top">
      <div class="dd-play__brand">
        <span class="dd-play__icon">📋</span>
        <div>
          <div class="dd-play__brand-title">{{ $t('agileTraining.dorDod.playTitle') }}</div>
          <div class="dd-play__brand-sub" v-if="group">{{ group.name }}</div>
        </div>
      </div>
      <div class="dd-play__lang">
        <button type="button" class="dd-lang__btn"
                :class="{ 'is-active': locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button type="button" class="dd-lang__btn"
                :class="{ 'is-active': locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
    </header>

    <!-- Прогресс-индикатор -->
    <nav v-if="!loading && step !== 'start'" class="dd-steps">
      <div v-for="(s, i) in steps" :key="s.key"
           class="dd-steps__item"
           :class="{ 'is-active': step === s.key, 'is-done': stepIndex(step) > i }">
        <span class="dd-steps__num">{{ i + 1 }}</span>
        <span class="dd-steps__label">{{ $t(s.labelKey) }}</span>
      </div>
    </nav>

    <div v-if="loading" class="dd-play__loading">{{ $t('common.loading') }}…</div>

    <!-- 0. Start -->
    <section v-else-if="step === 'start'" class="dd-card dd-card--center">
      <h1>{{ $t('agileTraining.dorDod.startTitle') }}</h1>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.startLead') }}</p>
      <ul class="dd-defs">
        <li><b>DoR</b> — {{ $t('agileTraining.dorDod.defDor') }}</li>
        <li><b>DoD</b> — {{ $t('agileTraining.dorDod.defDod') }}</li>
      </ul>
      <label class="dd-start__name">
        <span>{{ $t('agileTraining.common.yourName') }}</span>
        <input v-model="displayName" maxlength="60" :placeholder="$t('agileTraining.common.yourNamePh')" />
      </label>
      <button class="dd-btn dd-btn--primary" @click="startRun">{{ $t('agileTraining.dorDod.start') }}</button>
    </section>

    <!-- 1. Team -->
    <section v-else-if="step === 'team'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.teamTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.teamLead') }}</p>
      <ul class="dd-teams">
        <li v-for="t in content.teams" :key="t.key"
            class="dd-team-card" :class="{ 'is-selected': teamKey === t.key }"
            @click="teamKey = t.key">
          <div class="dd-team-card__title">{{ t.title }}</div>
          <div class="dd-team-card__short">{{ t.short }}</div>
          <div class="dd-team-card__ctx">{{ t.context }}</div>
        </li>
      </ul>
      <div class="dd-card__actions">
        <span></span>
        <button class="dd-btn dd-btn--primary" :disabled="!teamKey" @click="goStep('intro')">
          {{ $t('agileTraining.dorDod.next') }} →
        </button>
      </div>
    </section>

    <!-- 2. Intro (контекст проблемы) -->
    <section v-else-if="step === 'intro'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.introTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.introLead') }}</p>
      <ul class="dd-problems">
        <li>📉 {{ $t('agileTraining.dorDod.problem1') }}</li>
        <li>🔁 {{ $t('agileTraining.dorDod.problem2') }}</li>
        <li>🤷 {{ $t('agileTraining.dorDod.problem3') }}</li>
      </ul>
      <div class="dd-task">
        <b>👉 {{ $t('agileTraining.dorDod.taskTitle') }}</b>
        <p>{{ $t('agileTraining.dorDod.taskText') }}</p>
      </div>
      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost" @click="goStep('team')">← {{ $t('agileTraining.dorDod.back') }}</button>
        <button class="dd-btn dd-btn--primary" @click="goStep('rules')">
          {{ $t('agileTraining.dorDod.next') }} →
        </button>
      </div>
    </section>

    <!-- 3. Rules overview -->
    <section v-else-if="step === 'rules'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.rulesTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.rulesLead') }}</p>
      <ul class="dd-rules-grid">
        <li v-for="r in content.rules" :key="r.key" class="dd-rule">
          <div class="dd-rule__title">{{ r.title }}</div>
          <div class="dd-rule__desc">{{ r.desc }}</div>
        </li>
      </ul>
      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost" @click="goStep('intro')">← {{ $t('agileTraining.dorDod.back') }}</button>
        <button class="dd-btn dd-btn--primary" @click="goStep('distribute')">
          {{ $t('agileTraining.dorDod.distributeCta') }} →
        </button>
      </div>
    </section>

    <!-- 4. Distribute DoR/DoD -->
    <section v-else-if="step === 'distribute' || step === 'improve_distribute'" class="dd-card">
      <h2>{{ step === 'improve_distribute'
            ? $t('agileTraining.dorDod.improveTitle')
            : $t('agileTraining.dorDod.distributeTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.distributeLead') }}</p>

      <div class="dd-columns">
        <div class="dd-col-bin">
          <div class="dd-col-bin__head">🎯 DoR · {{ dor.length }}</div>
          <ul class="dd-col-bin__list">
            <li v-for="k in dor" :key="'dor-'+k" class="dd-chip dd-chip--dor">
              <span>{{ ruleTitle(k) }}</span>
              <button type="button" class="dd-chip__x" @click="remove(k)">✕</button>
            </li>
            <li v-if="!dor.length" class="dd-col-bin__empty">—</li>
          </ul>
        </div>
        <div class="dd-col-bin">
          <div class="dd-col-bin__head">✅ DoD · {{ dod.length }}</div>
          <ul class="dd-col-bin__list">
            <li v-for="k in dod" :key="'dod-'+k" class="dd-chip dd-chip--dod">
              <span>{{ ruleTitle(k) }}</span>
              <button type="button" class="dd-chip__x" @click="remove(k)">✕</button>
            </li>
            <li v-if="!dod.length" class="dd-col-bin__empty">—</li>
          </ul>
        </div>
      </div>

      <h3 class="dd-subtitle">{{ $t('agileTraining.dorDod.availableRules') }}</h3>
      <ul class="dd-rules-grid">
        <li v-for="r in content.rules" :key="r.key"
            class="dd-rule dd-rule--selectable"
            :class="{
              'dd-rule--in-dor': dor.includes(r.key),
              'dd-rule--in-dod': dod.includes(r.key),
            }">
          <div class="dd-rule__title">{{ r.title }}</div>
          <div class="dd-rule__desc">{{ r.desc }}</div>
          <div class="dd-rule__ctrls">
            <button type="button" class="dd-btn dd-btn--tiny dd-btn--dor"
                    :class="{ 'is-active': dor.includes(r.key) }"
                    @click="toDor(r.key)">→ DoR</button>
            <button type="button" class="dd-btn dd-btn--tiny dd-btn--dod"
                    :class="{ 'is-active': dod.includes(r.key) }"
                    @click="toDod(r.key)">→ DoD</button>
          </div>
        </li>
      </ul>

      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost"
                @click="step === 'improve_distribute' ? goStep('antipatterns') : goStep('rules')">
          ← {{ $t('agileTraining.dorDod.back') }}
        </button>
        <button class="dd-btn dd-btn--primary"
                :disabled="!dor.length && !dod.length"
                @click="goStep(step === 'improve_distribute' ? 'improve_mapping' : 'mapping')">
          {{ $t('agileTraining.dorDod.mappingCta') }} →
        </button>
      </div>
    </section>

    <!-- 5. Mapping (rule → effect) -->
    <section v-else-if="step === 'mapping' || step === 'improve_mapping'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.mappingTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.mappingLead') }}</p>
      <div v-if="priorityEffectsForTeam.length" class="dd-priority">
        ⭐ {{ $t('agileTraining.dorDod.priorityForTeam') }}:
        <span v-for="e in priorityEffectsForTeam" :key="'pri-'+e.key" class="dd-priority__chip">
          {{ e.title }}
        </span>
      </div>

      <div v-if="!selectedRules.length" class="dd-empty-state">
        {{ $t('agileTraining.dorDod.selectFirst') }}
      </div>

      <ul class="dd-map-list" v-else>
        <li v-for="r in selectedRules" :key="r.key" class="dd-map-row">
          <div class="dd-map-row__title">
            <b>{{ r.title }}</b>
            <span v-if="dor.includes(r.key)" class="dd-tag dd-tag--dor">DoR</span>
            <span v-if="dod.includes(r.key)" class="dd-tag dd-tag--dod">DoD</span>
          </div>
          <div class="dd-map-row__effects">
            <label v-for="e in content.effects" :key="r.key+'-'+e.key"
                   class="dd-eff-chip"
                   :class="{ 'is-active': (mapping[r.key] || []).includes(e.key) }">
              <input type="checkbox"
                     :checked="(mapping[r.key] || []).includes(e.key)"
                     @change="toggleEffect(r.key, e.key)">
              <span>{{ e.title }}</span>
            </label>
          </div>
        </li>
      </ul>

      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost"
                @click="goStep(step === 'improve_mapping' ? 'improve_distribute' : 'distribute')">
          ← {{ $t('agileTraining.dorDod.back') }}
        </button>
        <button class="dd-btn dd-btn--primary"
                :disabled="submitting"
                @click="submitRound(step === 'improve_mapping' ? 'improved' : 'initial')">
          {{ submitting ? $t('common.loading') : $t('agileTraining.dorDod.seeConsequences') }} →
        </button>
      </div>
    </section>

    <!-- 6. Simulate consequences -->
    <section v-else-if="step === 'simulate'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.simulateTitle') }}</h2>
      <div class="dd-outcome" :class="'dd-outcome--'+(simulation?.outcome || 'stable')">
        <div class="dd-outcome__icon">{{ outcomeIcon }}</div>
        <div>
          <div class="dd-outcome__title">
            {{ $t('agileTraining.dorDod.outcome.' + (simulation?.outcome || 'stable')) }}
          </div>
          <div class="dd-outcome__lead">
            {{ $t('agileTraining.dorDod.outcomeLead.' + (simulation?.outcome || 'stable')) }}
          </div>
        </div>
      </div>

      <h3 class="dd-subtitle">🔍 {{ $t('agileTraining.dorDod.whyTitle') }}</h3>
      <ul class="dd-reasons">
        <li v-for="r in (simulation?.reasons || [])" :key="r">
          · {{ $t('agileTraining.dorDod.' + r) }}
        </li>
      </ul>

      <h3 class="dd-subtitle">🗺 {{ $t('agileTraining.dorDod.mappingFeedback') }}</h3>
      <div v-if="!mappingInsights.length" class="dd-fac__hint">—</div>
      <ul class="dd-insights" v-else>
        <li v-for="ins in mappingInsights" :key="ins.rule" class="dd-insights__row">
          <b>{{ ruleTitle(ins.rule) }}</b>:
          <span v-if="ins.aligned.length" class="dd-insights__ok">
            ✓ {{ ins.aligned.map(e => effectTitle(e)).join(', ') }}
          </span>
          <span v-if="ins.extra.length" class="dd-insights__extra">
            ? {{ ins.extra.map(e => effectTitle(e)).join(', ') }}
          </span>
          <span v-if="ins.provocative.length" class="dd-insights__prov">
            ⚠ {{ ins.provocative.map(e => effectTitle(e)).join(', ') }}
          </span>
          <span v-if="!ins.aligned.length && !ins.extra.length && !ins.provocative.length"
                class="dd-fac__hint">
            — {{ $t('agileTraining.dorDod.noMapping') }}
          </span>
        </li>
      </ul>

      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost" @click="goStep('mapping')">← {{ $t('agileTraining.dorDod.back') }}</button>
        <button class="dd-btn dd-btn--primary" @click="goStep('antipatterns')">
          {{ $t('agileTraining.dorDod.next') }} →
        </button>
      </div>
    </section>

    <!-- 7. Antipatterns -->
    <section v-else-if="step === 'antipatterns'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.antipatternsTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.antipatternsLead') }}</p>

      <div v-if="activeAntipatterns.length" class="dd-ap-list">
        <div v-for="ap in activeAntipatterns" :key="ap" class="dd-ap-card">
          <div class="dd-ap-card__title">⚠ {{ $t('agileTraining.dorDod.ap.' + ap) }}</div>
          <div class="dd-ap-card__desc">{{ $t('agileTraining.dorDod.apDesc.' + ap) }}</div>
        </div>
      </div>
      <div v-else class="dd-ap-card dd-ap-card--good">
        ✅ {{ $t('agileTraining.dorDod.noAntipatterns') }}
      </div>

      <h3 class="dd-subtitle">{{ $t('agileTraining.dorDod.knownAntipatterns') }}</h3>
      <ul class="dd-known-ap">
        <li v-for="ap in knownAntipatterns" :key="'k-'+ap">
          <b>{{ $t('agileTraining.dorDod.ap.' + ap) }}</b>
          <div class="dd-fac__hint">{{ $t('agileTraining.dorDod.apDesc.' + ap) }}</div>
        </li>
      </ul>

      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost" @click="goStep('simulate')">← {{ $t('agileTraining.dorDod.back') }}</button>
        <button class="dd-btn dd-btn--primary" @click="enterImprovement">
          {{ $t('agileTraining.dorDod.improveNow') }} →
        </button>
      </div>
    </section>

    <!-- 9. Final -->
    <section v-else-if="step === 'final'" class="dd-card">
      <h2>{{ $t('agileTraining.dorDod.finalTitle') }}</h2>
      <p class="dd-card__lead">{{ $t('agileTraining.dorDod.finalLead') }}</p>

      <div class="dd-score-row">
        <div class="dd-score-box">
          <div class="dd-score-box__label">{{ $t('agileTraining.dorDod.scoreInitial') }}</div>
          <div class="dd-score-box__val">{{ scoreInitial }}</div>
          <div v-if="outcomeInitial" class="dd-pill" :class="outcomeClass(outcomeInitial)">
            {{ $t('agileTraining.dorDod.outcome.' + outcomeInitial) }}
          </div>
        </div>
        <div class="dd-score-arrow">→</div>
        <div class="dd-score-box dd-score-box--strong">
          <div class="dd-score-box__label">{{ $t('agileTraining.dorDod.scoreImproved') }}</div>
          <div class="dd-score-box__val">{{ scoreImproved }}</div>
          <div v-if="outcomeImproved" class="dd-pill" :class="outcomeClass(outcomeImproved)">
            {{ $t('agileTraining.dorDod.outcome.' + outcomeImproved) }}
          </div>
        </div>
      </div>

      <div v-if="delta" class="dd-delta">
        <div v-if="delta.resolved.length">
          ✅ <b>{{ $t('agileTraining.dorDod.resolvedAntipatterns') }}:</b>
          {{ delta.resolved.map(a => $t('agileTraining.dorDod.ap.' + a)).join(', ') }}
        </div>
        <div v-if="delta.introduced.length">
          ⚠️ <b>{{ $t('agileTraining.dorDod.introducedAntipatterns') }}:</b>
          {{ delta.introduced.map(a => $t('agileTraining.dorDod.ap.' + a)).join(', ') }}
        </div>
        <div v-if="!delta.resolved.length && !delta.introduced.length && delta.score_delta === 0"
             class="dd-fac__hint">
          {{ $t('agileTraining.dorDod.nothingChanged') }}
        </div>
      </div>

      <h3 class="dd-subtitle">📊 {{ $t('agileTraining.dorDod.groupStats') }}</h3>
      <div v-if="!groupResults" class="dd-fac__hint">—</div>
      <div v-else class="dd-group-stats">
        <div v-for="team in groupResults.teams.filter(t => t.participants)" :key="team.key"
             class="dd-team-stat">
          <div class="dd-team-stat__title">{{ team.title }}
            <span class="dd-pill dd-pill--muted">
              {{ $t('agileTraining.facilitator.participants', { n: team.participants }, team.participants) }}
            </span>
          </div>
          <div class="dd-team-stat__bars">
            <div class="dd-bar">
              <span class="dd-bar__label">{{ $t('agileTraining.dorDod.avgInitial') }}</span>
              <span class="dd-bar__val">{{ team.avg_initial }}</span>
            </div>
            <div class="dd-bar">
              <span class="dd-bar__label">{{ $t('agileTraining.dorDod.avgImproved') }}</span>
              <span class="dd-bar__val">{{ team.avg_improved }}</span>
            </div>
          </div>
          <div v-if="team.dor_top.length" class="dd-team-stat__top">
            🎯 {{ $t('agileTraining.dorDod.topDor') }}:
            <span v-for="t in team.dor_top.slice(0, 3)" :key="'t-dor-'+t.rule">{{ ruleTitle(t.rule) }} ({{ t.count }}), </span>
          </div>
          <div v-if="team.dod_top.length" class="dd-team-stat__top">
            ✅ {{ $t('agileTraining.dorDod.topDod') }}:
            <span v-for="t in team.dod_top.slice(0, 3)" :key="'t-dod-'+t.rule">{{ ruleTitle(t.rule) }} ({{ t.count }}), </span>
          </div>
        </div>
      </div>

      <div class="dd-card__actions">
        <button class="dd-btn dd-btn--ghost" @click="goStep('antipatterns')">← {{ $t('agileTraining.dorDod.back') }}</button>
        <button class="dd-btn dd-btn--primary" @click="replay">{{ $t('agileTraining.dorDod.replay') }}</button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgileDorDodPlay',
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      loading: true,
      locale: 'ru',
      group: null,
      content: { teams: [], rules: [], effects: [] },
      participantToken: '',
      displayName: '',
      step: 'start',
      teamKey: '',
      dor: [],
      dod: [],
      mapping: {},
      submitting: false,
      lastEval: null,
      simulation: null,
      scoreInitial: 0,
      scoreImproved: null,
      outcomeInitial: null,
      outcomeImproved: null,
      delta: null,
      groupResults: null,
      steps: [
        { key: 'team', labelKey: 'agileTraining.dorDod.stepTeam' },
        { key: 'intro', labelKey: 'agileTraining.dorDod.stepIntro' },
        { key: 'rules', labelKey: 'agileTraining.dorDod.stepRules' },
        { key: 'distribute', labelKey: 'agileTraining.dorDod.stepDistribute' },
        { key: 'mapping', labelKey: 'agileTraining.dorDod.stepMapping' },
        { key: 'simulate', labelKey: 'agileTraining.dorDod.stepSimulate' },
        { key: 'antipatterns', labelKey: 'agileTraining.dorDod.stepAntipatterns' },
        { key: 'improve_distribute', labelKey: 'agileTraining.dorDod.stepImprove' },
        { key: 'final', labelKey: 'agileTraining.dorDod.stepFinal' },
      ],
      knownAntipatterns: [
        'dor_too_strict', 'dor_too_soft', 'dod_too_weak', 'dor_dod_mixed',
        'critical_missing', 'speed_illusion', 'value_too_late',
      ],
    };
  },
  computed: {
    rulesIndex() {
      const m = {};
      for (const r of this.content.rules) m[r.key] = r;
      return m;
    },
    effectsIndex() {
      const m = {};
      for (const e of this.content.effects) m[e.key] = e;
      return m;
    },
    selectedRules() {
      const keys = [...this.dor, ...this.dod];
      const seen = new Set();
      const out = [];
      for (const k of keys) {
        if (seen.has(k)) continue;
        seen.add(k);
        const r = this.rulesIndex[k];
        if (r) out.push(r);
      }
      return out;
    },
    activeAntipatterns() {
      return (this.lastEval && this.lastEval.antipatterns) || [];
    },
    mappingInsights() {
      return (this.lastEval && this.lastEval.mapping_insights) || [];
    },
    priorityEffectsForTeam() {
      const team = this.content.teams.find(t => t.key === this.teamKey);
      if (!team) return [];
      return team.priority_effects.map(k => this.effectsIndex[k]).filter(Boolean);
    },
    outcomeIcon() {
      const o = this.simulation?.outcome;
      if (o === 'blocked') return '🚧';
      if (o === 'rework_heavy') return '🔁';
      if (o === 'predictable') return '🎯';
      return '🙂';
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
    this.participantToken = localStorage.getItem(`dor_dod_token_${this.slug}`) || '';
    this.displayName = localStorage.getItem(`dor_dod_name_${this.slug}`) || '';
    await this.reloadContent();
    this.loading = false;
  },
  methods: {
    setLocale(lc) { this.locale = lc; },
    stepIndex(key) {
      const i = this.steps.findIndex(s => s.key === key);
      // improve_mapping считаем как шаг 8 (improve_distribute)
      if (i === -1 && key === 'improve_mapping') return this.steps.findIndex(s => s.key === 'improve_distribute');
      return i;
    },
    goStep(s) {
      this.step = s;
      window.scrollTo({ top: 0, behavior: 'smooth' });
    },
    ruleTitle(k) { return this.rulesIndex[k]?.title || k; },
    effectTitle(k) { return this.effectsIndex[k]?.title || k; },
    shuffle(arr) {
      const out = Array.isArray(arr) ? [...arr] : [];
      for (let i = out.length - 1; i > 0; i -= 1) {
        const j = Math.floor(Math.random() * (i + 1));
        [out[i], out[j]] = [out[j], out[i]];
      }
      return out;
    },
    async reloadContent() {
      try {
        const params = { locale: this.locale };
        if (this.participantToken) params.participant_token = this.participantToken;
        const res = await axios.get(`/api/agile-training/dor-dod/g/${this.slug}/state`, { params });
        this.group = res.data.group;
        const raw = res.data.content || this.content;
        // Перемешиваем карточки правил и эффекты, чтобы задание не
        // «решалось» по порядку (раньше сначала шли все DoR, потом DoD).
        this.content = {
          ...raw,
          rules: this.shuffle(raw.rules),
          effects: this.shuffle(raw.effects),
        };
        const answer = res.data.answer;
        if (answer) {
          this.teamKey = answer.team_key;
          const initial = answer.data?.initial;
          if (initial) {
            this.scoreInitial = answer.data?.eval_initial?.score_raw || 0;
            this.outcomeInitial = answer.data?.sim_initial?.outcome || null;
          }
          const improved = answer.data?.improved;
          if (improved) {
            this.dor = [...improved.dor]; this.dod = [...improved.dod];
            this.mapping = this.cloneMapping(improved.mapping);
            this.scoreImproved = answer.data?.eval_improved?.score_raw || 0;
            this.outcomeImproved = answer.data?.sim_improved?.outcome || null;
            this.lastEval = answer.data?.eval_improved || null;
            this.simulation = answer.data?.sim_improved || null;
          } else if (initial) {
            this.dor = [...initial.dor]; this.dod = [...initial.dod];
            this.mapping = this.cloneMapping(initial.mapping);
            this.lastEval = answer.data?.eval_initial || null;
            this.simulation = answer.data?.sim_initial || null;
          }
        }
      } catch (e) { console.error(e); }
    },
    cloneMapping(m) {
      const out = {};
      for (const k in (m || {})) out[k] = [...(m[k] || [])];
      return out;
    },
    async startRun() {
      if (this.displayName) localStorage.setItem(`dor_dod_name_${this.slug}`, this.displayName);
      if (!this.participantToken) {
        try {
          const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, {
            display_name: this.displayName || null,
          });
          this.participantToken = res.data.participant_token;
          localStorage.setItem(`dor_dod_token_${this.slug}`, this.participantToken);
          await this.reloadContent();
        } catch (e) {
          alert(e.response?.data?.error || 'Failed to join');
          return;
        }
      }
      // восстанавливаем логическую точку возврата
      if (this.scoreImproved !== null && this.scoreImproved !== undefined) {
        this.step = 'final';
        await this.loadGroupResults();
      } else if (this.scoreInitial) {
        this.step = 'antipatterns';
      } else if (this.teamKey) {
        this.step = 'intro';
      } else {
        this.step = 'team';
      }
    },
    async loadGroupResults() {
      try {
        const res = await axios.get(`/api/agile-training/dor-dod/g/${this.slug}/results`, {
          params: { locale: this.locale },
        });
        this.groupResults = res.data;
      } catch (_) { this.groupResults = null; }
    },
    toDor(k) {
      this.dod = this.dod.filter(x => x !== k);
      if (this.dor.includes(k)) {
        this.dor = this.dor.filter(x => x !== k);
      } else {
        this.dor = [...this.dor, k];
      }
      this.pruneMapping();
    },
    toDod(k) {
      this.dor = this.dor.filter(x => x !== k);
      if (this.dod.includes(k)) {
        this.dod = this.dod.filter(x => x !== k);
      } else {
        this.dod = [...this.dod, k];
      }
      this.pruneMapping();
    },
    remove(k) {
      this.dor = this.dor.filter(x => x !== k);
      this.dod = this.dod.filter(x => x !== k);
      this.pruneMapping();
    },
    pruneMapping() {
      const keep = new Set([...this.dor, ...this.dod]);
      const next = {};
      for (const k in this.mapping) if (keep.has(k)) next[k] = this.mapping[k];
      this.mapping = next;
    },
    toggleEffect(ruleKey, effectKey) {
      const cur = this.mapping[ruleKey] ? [...this.mapping[ruleKey]] : [];
      const idx = cur.indexOf(effectKey);
      if (idx >= 0) cur.splice(idx, 1); else cur.push(effectKey);
      this.mapping = { ...this.mapping, [ruleKey]: cur };
    },
    async submitRound(roundKey) {
      this.submitting = true;
      try {
        const body = {
          participant_token: this.participantToken,
          team_key: this.teamKey,
          round: roundKey,
          dor: this.dor,
          dod: this.dod,
          mapping: this.mapping,
        };
        const res = await axios.post(`/api/agile-training/dor-dod/g/${this.slug}/answer`, body);
        this.lastEval = res.data.eval;
        this.simulation = res.data.simulation;
        this.delta = res.data.delta;
        if (roundKey === 'improved') {
          this.scoreImproved = res.data.eval?.score_raw || 0;
          this.outcomeImproved = res.data.simulation?.outcome || null;
          await this.loadGroupResults();
          this.goStep('final');
        } else {
          this.scoreInitial = res.data.eval?.score_raw || 0;
          this.outcomeInitial = res.data.simulation?.outcome || null;
          this.goStep('simulate');
        }
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.submitting = false;
      }
    },
    enterImprovement() {
      this.goStep('improve_distribute');
    },
    async replay() {
      if (!confirm(this.$t('agileTraining.dorDod.replayConfirm'))) return;
      this.dor = []; this.dod = []; this.mapping = {};
      this.scoreInitial = 0; this.scoreImproved = null;
      this.outcomeInitial = null; this.outcomeImproved = null;
      this.simulation = null; this.lastEval = null; this.delta = null;
      this.teamKey = '';
      this.goStep('team');
    },
    outcomeClass(o) {
      if (o === 'predictable' || o === 'stable') return 'dd-pill--good';
      if (o === 'rework_heavy') return 'dd-pill--warn';
      if (o === 'blocked') return 'dd-pill--bad';
      return '';
    },
  },
};
</script>

<style scoped>
.dd-play { max-width: 960px; margin: 0 auto; padding: 20px 18px 80px; color: #0f172a; }
.dd-play__top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.dd-play__brand { display: flex; align-items: center; gap: 10px; }
.dd-play__icon { font-size: 26px; }
.dd-play__brand-title { font-weight: 800; font-size: 18px; }
.dd-play__brand-sub { color: #64748b; font-size: 13px; }
.dd-play__lang { display: flex; gap: 4px; }
.dd-lang__btn {
  background: #e2e8f0 !important; color: #0f172a !important;
  border: none !important; border-radius: 999px !important;
  padding: 4px 10px !important; font-weight: 700; cursor: pointer;
  font-size: 12px; transition: background 0.15s ease;
}
.dd-lang__btn:hover { background: #cbd5e1 !important; }
.dd-lang__btn.is-active {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important;
}

.dd-play__loading { color: #64748b; padding: 40px 0; text-align: center; }

/* stepper */
.dd-steps { display: flex; gap: 6px; overflow-x: auto; padding: 8px 0 14px; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; }
.dd-steps__item { display: flex; align-items: center; gap: 6px; background: #f1f5f9; padding: 6px 10px; border-radius: 999px; font-size: 12px; white-space: nowrap; color: #64748b; }
.dd-steps__item.is-active { background: #ccfbf1; color: #0f766e; font-weight: 700; }
.dd-steps__item.is-done { background: #d1fae5; color: #065f46; }
.dd-steps__num { background: #fff; padding: 1px 6px; border-radius: 999px; font-weight: 700; }

/* cards */
.dd-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 22px 22px 24px; margin-bottom: 16px; }
.dd-card--center { text-align: center; }
.dd-card__lead { color: #475569; line-height: 1.5; }
.dd-card h1 { margin: 0 0 8px; font-size: 24px; }
.dd-card h2 { margin: 0 0 8px; font-size: 20px; }
.dd-card h3 { margin: 0 0 8px; font-size: 16px; }
.dd-card__actions {
  display: flex; justify-content: space-between; align-items: center;
  gap: 10px; margin-top: 18px; flex-wrap: wrap;
}

.dd-defs { list-style: none; padding: 0; margin: 14px 0; display: flex; flex-direction: column; gap: 6px; color: #334155; }
.dd-start__name { display: flex; flex-direction: column; gap: 6px; align-items: center; margin: 16px 0; }
.dd-start__name input { padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; font-size: 14px; width: min(320px, 100%); }

.dd-btn {
  background: #e2e8f0 !important; color: #0f172a !important;
  border: none !important; border-radius: 10px !important;
  padding: 10px 18px !important; font-weight: 600; cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.dd-btn:hover:not(:disabled) { transform: translateY(-1px); }
.dd-btn:active:not(:disabled) { transform: translateY(0); }
.dd-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.dd-btn--primary {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important;
}
.dd-btn--primary:hover:not(:disabled) { box-shadow: 0 8px 18px rgba(8, 145, 178, 0.3); }
.dd-btn--ghost {
  background: transparent !important; color: #0f766e !important;
  border: 1px solid #14b8a6 !important;
}
.dd-btn--ghost:hover:not(:disabled) { background: #f0fdfa !important; }
.dd-btn--tiny { padding: 4px 10px !important; font-size: 12px; border-radius: 8px !important; }
.dd-btn--dor { background: #e0f2fe !important; color: #075985 !important; }
.dd-btn--dor.is-active { background: linear-gradient(135deg, #0891b2, #0e7490) !important; color: #fff !important; }
.dd-btn--dor:hover:not(:disabled) { background: #bae6fd !important; }
.dd-btn--dor.is-active:hover:not(:disabled) { filter: brightness(1.05); }
.dd-btn--dod { background: #dcfce7 !important; color: #14532d !important; }
.dd-btn--dod.is-active { background: linear-gradient(135deg, #16a34a, #15803d) !important; color: #fff !important; }
.dd-btn--dod:hover:not(:disabled) { background: #bbf7d0 !important; }
.dd-btn--dod.is-active:hover:not(:disabled) { filter: brightness(1.05); }

/* teams */
.dd-teams { list-style: none; padding: 0; margin: 14px 0 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; }
.dd-team-card {
  border: 2px solid #e2e8f0; border-radius: 14px; padding: 14px;
  cursor: pointer; background: #fff;
  transition: border-color 0.15s ease, transform 0.15s ease, box-shadow 0.15s ease;
}
.dd-team-card:hover { transform: translateY(-2px); box-shadow: 0 10px 20px rgba(15, 118, 110, 0.12); }
.dd-team-card.is-selected { border-color: #14b8a6; background: #f0fdfa; }
.dd-team-card__title { font-weight: 700; font-size: 16px; margin-bottom: 4px; }
.dd-team-card__short { color: #64748b; font-size: 12px; margin-bottom: 6px; }
.dd-team-card__ctx { color: #334155; font-size: 13px; line-height: 1.4; }

/* problems */
.dd-problems { list-style: none; padding: 0; display: flex; flex-direction: column; gap: 8px; margin: 14px 0; color: #334155; }
.dd-problems li { background: #fef3c7; padding: 10px 12px; border-radius: 10px; }
.dd-task { background: #ccfbf1; border-left: 4px solid #0891b2; padding: 12px 14px; border-radius: 10px; margin-top: 10px; }
.dd-task b { display: block; margin-bottom: 4px; }

/* rules grid */
.dd-rules-grid {
  list-style: none; padding: 0; margin: 14px 0 0;
  display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px;
}
.dd-rule {
  background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
  padding: 12px 14px; transition: border-color 0.15s ease, transform 0.15s ease;
}
.dd-rule--selectable:hover { transform: translateY(-1px); }
.dd-rule--in-dor { border-color: #0891b2; background: #e0f2fe; }
.dd-rule--in-dod { border-color: #16a34a; background: #dcfce7; }
.dd-rule__title { font-weight: 700; margin-bottom: 4px; }
.dd-rule__desc { color: #475569; font-size: 12px; line-height: 1.4; margin-bottom: 8px; }
.dd-rule__ctrls { display: flex; gap: 6px; flex-wrap: wrap; }

.dd-subtitle { margin: 18px 0 8px; font-size: 15px; color: #0f172a; }

/* bins */
.dd-columns { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 700px) { .dd-columns { grid-template-columns: 1fr; } }
.dd-col-bin { border: 2px dashed #cbd5e1; border-radius: 14px; padding: 10px; min-height: 120px; background: #f8fafc; }
.dd-col-bin__head { font-weight: 700; padding: 4px 8px; margin-bottom: 8px; }
.dd-col-bin__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.dd-col-bin__empty { color: #94a3b8; font-size: 12px; padding: 8px; text-align: center; }
.dd-chip {
  display: flex; justify-content: space-between; align-items: center; gap: 6px;
  padding: 6px 10px; border-radius: 999px; font-size: 13px;
}
.dd-chip--dor { background: #e0f2fe; color: #075985; }
.dd-chip--dod { background: #dcfce7; color: #14532d; }
.dd-chip__x {
  background: transparent !important; border: none !important; cursor: pointer;
  font-size: 12px; color: inherit;
  padding: 0 4px; opacity: 0.7;
}
.dd-chip__x:hover { opacity: 1; }

/* mapping */
.dd-priority { background: #fef9c3; border-left: 4px solid #f59e0b; padding: 10px 12px; border-radius: 10px; margin: 12px 0; font-size: 13px; }
.dd-priority__chip { display: inline-block; background: #fff; color: #92400e; padding: 2px 8px; border-radius: 999px; font-weight: 600; margin: 0 4px 4px 0; }
.dd-empty-state { color: #64748b; text-align: center; padding: 24px; }
.dd-map-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 14px; }
.dd-map-row { border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; background: #f8fafc; }
.dd-map-row__title { font-size: 14px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.dd-map-row__effects { display: flex; flex-wrap: wrap; gap: 6px; }
.dd-eff-chip {
  display: flex; align-items: center; gap: 6px;
  padding: 6px 10px; border-radius: 999px;
  background: #fff; border: 1px solid #e2e8f0;
  font-size: 12px; cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}
.dd-eff-chip input { display: none; }
.dd-eff-chip:hover { background: #f0fdfa; border-color: #14b8a6; }
.dd-eff-chip.is-active { background: #ccfbf1; border-color: #14b8a6; color: #0f766e; font-weight: 600; }
.dd-eff-chip--prov { border-color: #fed7aa; }
.dd-eff-chip--prov.is-active { background: #fed7aa; border-color: #f97316; color: #9a3412; }

.dd-tag { font-size: 10px; padding: 1px 6px; border-radius: 999px; font-weight: 700; }
.dd-tag--dor { background: #bae6fd; color: #075985; }
.dd-tag--dod { background: #bbf7d0; color: #14532d; }
.dd-tag--neutral { background: #e2e8f0; color: #334155; }

/* outcome */
.dd-outcome { display: flex; gap: 14px; padding: 16px; border-radius: 14px; align-items: center; margin-top: 8px; }
.dd-outcome--blocked { background: #fee2e2; }
.dd-outcome--rework_heavy { background: #fef3c7; }
.dd-outcome--stable { background: #e0f2fe; }
.dd-outcome--predictable { background: #d1fae5; }
.dd-outcome__icon { font-size: 38px; }
.dd-outcome__title { font-weight: 700; font-size: 18px; }
.dd-outcome__lead { color: #475569; font-size: 13px; margin-top: 4px; }
.dd-reasons { list-style: none; padding: 0; margin: 8px 0 0; color: #475569; font-size: 13px; display: flex; flex-direction: column; gap: 4px; }

.dd-insights { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 6px; }
.dd-insights__row { background: #f8fafc; padding: 8px 10px; border-radius: 8px; font-size: 13px; }
.dd-insights__ok { color: #14532d; margin-left: 4px; }
.dd-insights__extra { color: #9a3412; margin-left: 6px; }
.dd-insights__prov { color: #991b1b; margin-left: 6px; }

/* antipatterns */
.dd-ap-list { display: flex; flex-direction: column; gap: 10px; margin-top: 10px; }
.dd-ap-card { background: #fee2e2; color: #991b1b; padding: 12px 14px; border-radius: 12px; }
.dd-ap-card--good { background: #d1fae5; color: #065f46; }
.dd-ap-card__title { font-weight: 700; margin-bottom: 4px; }
.dd-ap-card__desc { font-size: 13px; line-height: 1.4; }
.dd-known-ap { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 6px; }
.dd-known-ap li { background: #f8fafc; padding: 8px 10px; border-radius: 8px; font-size: 13px; }
.dd-fac__hint { color: #64748b; font-size: 12px; font-style: italic; }

/* final */
.dd-score-row { display: flex; gap: 10px; align-items: center; justify-content: center; margin: 14px 0; flex-wrap: wrap; }
.dd-score-box { background: #f8fafc; padding: 14px 20px; border-radius: 14px; text-align: center; min-width: 140px; }
.dd-score-box--strong { background: #ccfbf1; }
.dd-score-box__label { color: #64748b; font-size: 12px; }
.dd-score-box__val { font-size: 28px; font-weight: 800; color: #0f766e; }
.dd-score-arrow { font-size: 20px; color: #94a3b8; }
.dd-pill { background: #ccfbf1; color: #0f766e; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; display: inline-block; margin-top: 4px; }
.dd-pill--muted { background: #e2e8f0; color: #334155; }
.dd-pill--good { background: #d1fae5; color: #065f46; }
.dd-pill--warn { background: #fef3c7; color: #92400e; }
.dd-pill--bad { background: #fee2e2; color: #991b1b; }
.dd-delta { background: #f8fafc; border-radius: 12px; padding: 12px; font-size: 13px; display: flex; flex-direction: column; gap: 6px; }

.dd-group-stats { display: flex; flex-direction: column; gap: 12px; }
.dd-team-stat { background: #f8fafc; padding: 12px 14px; border-radius: 12px; }
.dd-team-stat__title { font-weight: 700; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.dd-team-stat__bars { display: flex; gap: 14px; margin: 6px 0; flex-wrap: wrap; font-size: 13px; }
.dd-bar { display: flex; flex-direction: column; }
.dd-bar__label { color: #64748b; font-size: 11px; }
.dd-bar__val { font-weight: 700; color: #0f766e; font-size: 16px; }
.dd-team-stat__top { font-size: 12px; color: #475569; margin-top: 2px; }
</style>
