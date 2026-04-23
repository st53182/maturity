<template>
  <div class="se-play" :class="{ 'se-play--board': step === 'build' }">
    <header class="se-play__top">
      <div class="se-play__brand">
        <span class="se-play__icon">🗓️</span>
        <div>
          <div class="se-play__brand-title">{{ $t('agileTraining.scrumEvents.playTitle') }}</div>
          <div class="se-play__brand-sub" v-if="group">{{ group.name }}</div>
        </div>
      </div>
      <div class="se-play__lang">
        <button type="button" class="se-lang__btn"
                :class="{ 'is-active': locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button type="button" class="se-lang__btn"
                :class="{ 'is-active': locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
    </header>

    <nav v-if="!loading && step !== 'start'" class="se-steps">
      <div v-for="(s, i) in steps" :key="s.key"
           class="se-steps__item"
           :class="{ 'is-active': step === s.key, 'is-done': stepIndex(step) > i }">
        <span class="se-steps__num">{{ i + 1 }}</span>
        <span class="se-steps__label">{{ $t(s.labelKey) }}</span>
      </div>
    </nav>

    <div v-if="loading" class="se-play__loading">{{ $t('common.loading') }}…</div>

    <!-- 0. Start -->
    <section v-else-if="step === 'start'" class="se-card se-card--center">
      <h1>{{ $t('agileTraining.scrumEvents.startTitle') }}</h1>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.startLead') }}</p>
      <ul class="se-defs">
        <li v-for="s in content.stages" :key="s.key">
          <b>{{ s.title }}</b> — {{ s.purpose }}
        </li>
      </ul>
      <label class="se-start__name">
        <span>{{ $t('agileTraining.common.yourName') }}</span>
        <input v-model="displayName" maxlength="60"
               :placeholder="$t('agileTraining.common.yourNamePh')" />
      </label>
      <button class="se-btn se-btn--primary" @click="startRun">
        {{ $t('agileTraining.scrumEvents.start') }}
      </button>
    </section>

    <!-- 1. Context -->
    <section v-else-if="step === 'context'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.contextTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.contextLead') }}</p>
      <ul class="se-context">
        <li v-for="s in content.stages" :key="s.key">
          <b>{{ s.title }}</b>
          <div class="se-fac__hint">{{ s.purpose }}</div>
        </li>
      </ul>
      <div class="se-card__actions">
        <span></span>
        <button class="se-btn se-btn--primary" @click="goStep('cards')">
          {{ $t('agileTraining.scrumEvents.next') }} →
        </button>
      </div>
    </section>

    <!-- 2. Cards overview -->
    <section v-else-if="step === 'cards'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.cardsTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.cardsLead') }}</p>
      <div v-for="cat in content.categories" :key="cat" class="se-cards-cat">
        <h3>{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</h3>
        <ul class="se-cards-list">
          <li v-for="c in (content.cards[cat] || [])" :key="c.key" class="se-chip">
            {{ c.title }}
          </li>
        </ul>
      </div>
      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('context')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary" @click="startBuilding">
          {{ $t('agileTraining.scrumEvents.buildCta') }} →
        </button>
      </div>
    </section>

    <!-- 3. Build — доска в стиле Miro: 5 событий + 5 колонок-категорий -->
    <section v-else-if="step === 'build'" class="se-card se-card--build">
      <div class="se-build__header">
        <div>
          <h2 class="se-build__title">{{ $t('agileTraining.scrumEvents.buildTitle') }}</h2>
          <p class="se-card__lead se-build__lead">{{ $t('agileTraining.scrumEvents.buildLead') }}</p>
        </div>
        <p class="se-build__swipe-hint" aria-hidden="true">{{ $t('agileTraining.scrumEvents.buildSwipeHint') }}</p>
      </div>

      <nav class="se-stage-tabs se-stage-tabs--board" aria-label="stages">
        <button v-for="s in content.stages" :key="s.key"
                type="button" class="se-stage-tab"
                :class="{ 'is-active': activeStage === s.key, 'is-filled': isStageFilled(s.key) }"
                @click="activeStage = s.key">
          <span class="se-stage-tab__mark">{{ isStageFilled(s.key) ? '✓' : '○' }}</span>
          <span class="se-stage-tab__text">{{ s.title }}</span>
        </button>
      </nav>

      <div v-if="activeStageObj" class="se-build__canvas">
        <div class="se-stage-body__intro se-build__event-banner">
          <span class="se-build__event-emoji">{{ stageEmoji(activeStage) }}</span>
          <p>{{ activeStageObj.purpose }}</p>
        </div>

        <div class="se-build__category-strip" role="tablist" aria-label="categories">
          <button v-for="cat in content.categories" :id="'se-strip-'+activeStage+'-'+cat" :key="'strip-'+cat"
                  type="button" role="tab"
                  class="se-build__strip-pill"
                  :class="{
                    'is-done': (selection[activeStage]?.[cat] || []).length > 0,
                    'is-active': activeBuildCat === cat
                  }"
                  :aria-selected="activeBuildCat === cat"
                  @click="focusBuildColumn(cat)">
            <span class="se-build__strip-ic">{{ categoryEmoji(cat) }}</span>
            <span class="se-build__strip-label">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</span>
            <span v-if="(selection[activeStage]?.[cat] || []).length" class="se-build__strip-badge">
              {{ (selection[activeStage]?.[cat] || []).length }}
            </span>
          </button>
        </div>

        <div ref="buildBoard" class="se-build__board">
          <div v-for="cat in content.categories" :id="'se-col-'+activeStage+'-'+cat" :key="activeStage + '-' + cat"
               class="se-build-col"
               :class="['se-build-col--' + categoryAccent(cat), { 'se-build-col--focus': activeBuildCat === cat }]">
            <header class="se-build-col__head">
              <span class="se-build-col__ic">{{ categoryEmoji(cat) }}</span>
              <div>
                <h3 class="se-build-col__title">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</h3>
                <p class="se-build-col__sub">
                  {{ $t('agileTraining.scrumEvents.pickedCount',
                    { n: (selection[activeStage]?.[cat] || []).length },
                    (selection[activeStage]?.[cat] || []).length) }}
                </p>
              </div>
            </header>
            <div class="se-build-col__notes">
              <button v-for="(c, idx) in (content.cards[cat] || [])" :key="c.key" type="button"
                      class="se-note"
                      :class="{ 'is-active': isPicked(activeStage, cat, c.key) }"
                      :style="{ '--note-rot': ((idx * 7 + cat.length * 3) % 5 - 2) * 0.4 + 'deg' }"
                      @click="togglePick(activeStage, cat, c.key)">
                <span class="se-note__text">{{ c.title }}</span>
              </button>
            </div>
          </div>
        </div>

        <div class="se-build__footer">
          <button v-if="!isStageFilled(activeStage)" type="button" class="se-btn se-btn--soft"
                  @click="goNextUnfilledStage">
            {{ nextStageButtonLabel }}
          </button>
          <span v-else class="se-build__stage-ok">✓ {{ $t('agileTraining.scrumEvents.stageComplete') }}</span>
        </div>
      </div>

      <div class="se-card__actions se-card__actions--build">
        <button class="se-btn se-btn--ghost" @click="goStep('cards')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary"
                :disabled="!allStagesFilled"
                @click="goStep('why')">
          {{ allStagesFilled
             ? $t('agileTraining.scrumEvents.seeWhyCta')
             : $t('agileTraining.scrumEvents.fillAllStages') }} →
        </button>
      </div>
    </section>

    <!-- 4. Why (ключевой этап «зачем») -->
    <section v-else-if="step === 'why'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.whyTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.whyLead') }}</p>
      <ul class="se-why">
        <li v-for="s in content.stages" :key="s.key" class="se-why__item">
          <div class="se-why__title">
            <span class="se-why__emoji">{{ stageEmoji(s.key) }}</span>
            <b>{{ s.title }}</b>
          </div>
          <div class="se-why__purpose">👉 {{ s.purpose }}</div>
          <div class="se-why__problem">🎯 {{ s.problem_it_solves }}</div>
        </li>
      </ul>
      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('build')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary" @click="submit">
          {{ submitting ? $t('common.loading') : $t('agileTraining.scrumEvents.saveAndErrors') }} →
        </button>
      </div>
    </section>

    <!-- 5. Errors -->
    <section v-else-if="step === 'errors'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.errorsTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.errorsLead') }}</p>
      <ul class="se-errors-list">
        <li v-for="e in content.errors" :key="e.key"
            class="se-err-card"
            :class="{ 'is-active': errorsSeen.includes(e.key) }"
            @click="toggleError(e.key)">
          <div class="se-err-card__title">⚠️ {{ e.title }}</div>
          <ul class="se-err-card__cons">
            <li v-for="(c, i) in e.consequences" :key="i">· {{ c }}</li>
          </ul>
        </li>
      </ul>
      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('why')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary" @click="onErrorsNext">
          {{ hasRed ? $t('agileTraining.scrumEvents.fixCta') : $t('agileTraining.scrumEvents.toResult') }} →
        </button>
      </div>
    </section>

    <!-- 6. Fix (rebuild only red/yellow categories) -->
    <section v-else-if="step === 'fix'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.fixTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.fixLead') }}</p>

      <div v-for="s in problematicStages" :key="'fix-' + s.key" class="se-fix-stage">
        <h3>{{ s.title }}
          <span class="se-pill" :class="'se-pill--' + (lastEval?.stages?.[s.key]?.color || 'gray')">
            {{ $t('agileTraining.scrumEvents.colors.' + (lastEval?.stages?.[s.key]?.color || 'gray')) }}
          </span>
        </h3>
        <div v-for="cat in content.categories" :key="'fix-' + s.key + '-' + cat">
          <div v-if="problemsByStage[s.key] && problemsByStage[s.key].includes(cat)"
               class="se-builder-cat">
            <div class="se-builder-cat__head">
              <h4>{{ $t('agileTraining.scrumEvents.cat.' + cat) }}
                <span class="se-fac__hint">
                  ({{ $t('agileTraining.scrumEvents.needsAttention') }})
                </span>
              </h4>
            </div>
            <ul class="se-cards-list">
              <li v-for="c in (content.cards[cat] || [])" :key="c.key">
                <button type="button" class="se-chip se-chip--selectable"
                        :class="{ 'is-active': isPicked(s.key, cat, c.key) }"
                        @click="togglePick(s.key, cat, c.key)">
                  {{ c.title }}
                </button>
              </li>
            </ul>
          </div>
        </div>
      </div>

      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('errors')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary" @click="submit">
          {{ submitting ? $t('common.loading') : $t('agileTraining.scrumEvents.toResult') }} →
        </button>
      </div>
    </section>

    <!-- 7. Final Miro-like board + эталон -->
    <section v-else-if="step === 'final'" class="se-card se-card--final">
      <h2>{{ $t('agileTraining.scrumEvents.finalTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.finalLead') }}</p>
      <div class="se-final__toolbar">
        <button
          type="button"
          class="se-btn se-btn--ghost"
          :disabled="pdfExporting"
          @click="exportFinalToPdf"
        >
          {{ pdfExporting ? $t('agileTraining.common.downloadPdfLoading') : $t('agileTraining.common.downloadPdf') }}
        </button>
      </div>

      <div ref="pdfExportRoot" class="se-pdf-export-root">
        <h3 class="se-section-title">{{ $t('agileTraining.scrumEvents.yourBoardTitle') }}</h3>
        <p class="se-final__debrief-hint">{{ $t('agileTraining.scrumEvents.finalDebriefHint') }}</p>

        <div class="se-board se-board--final-plain">
          <div v-for="s in content.stages" :key="'fin-' + s.key" class="se-col se-col--final">
            <div class="se-col__head">
              <h4>{{ s.title }}</h4>
              <span class="se-col__purpose">{{ s.purpose }}</span>
            </div>
            <div v-for="cat in content.categories" :key="'fin-' + s.key + '-' + cat"
                 class="se-col__cat">
              <div class="se-col__cat-title">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</div>
              <ul class="se-col__picks">
                <li v-for="k in (selection[s.key]?.[cat] || [])" :key="k" class="se-pick se-pick--plain">
                  {{ cardTitle(cat, k) }}
                </li>
                <li v-if="!(selection[s.key]?.[cat] || []).length" class="se-fac__hint">—</li>
              </ul>
            </div>
          </div>
        </div>

        <h3 class="se-section-title">📊 {{ $t('agileTraining.scrumEvents.groupComparison') }}</h3>
        <div v-if="!groupResults" class="se-fac__hint">—</div>
        <div v-else class="se-group-comp">
          <div v-for="stage in groupResults.stages" :key="'grp-' + stage.key" class="se-group-stage">
            <h4>{{ stage.title }}</h4>
            <div v-for="cat in content.categories" :key="'grp-' + stage.key + '-' + cat"
                 class="se-group-stage__cat">
              <div class="se-col__cat-title">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</div>
              <ul class="se-col__picks">
                <li v-for="it in (stage.categories[cat] || []).slice(0, 3)" :key="it.key"
                    class="se-pick">
                  <span>{{ it.title }}</span>
                  <span class="se-pick__pct">{{ it.pct }}%</span>
                </li>
                <li v-if="!(stage.categories[cat] || []).length" class="se-fac__hint">—</li>
              </ul>
            </div>
          </div>
        </div>
      </div>

      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('errors')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--ghost" @click="goStep('custom')">
          ✨ {{ $t('agileTraining.scrumEvents.tryCustomMode') }}
        </button>
        <button class="se-btn se-btn--primary" @click="replay">
          {{ $t('agileTraining.scrumEvents.replay') }}
        </button>
      </div>
    </section>

    <!-- 8. Custom mode -->
    <section v-else-if="step === 'custom'" class="se-card">
      <h2>{{ $t('agileTraining.scrumEvents.customTitle') }}</h2>
      <p class="se-card__lead">{{ $t('agileTraining.scrumEvents.customLead') }}</p>

      <div class="se-contexts">
        <button v-for="c in content.customs" :key="c.key"
                type="button"
                class="se-context-card"
                :class="{ 'is-active': custom.context_key === c.key }"
                @click="custom.context_key = c.key">
          <div class="se-context-card__title">{{ c.title }}</div>
          <div class="se-context-card__desc">{{ c.desc }}</div>
        </button>
      </div>

      <div v-if="custom.context_key">
        <div v-for="cat in content.categories" :key="'c-' + cat" class="se-builder-cat">
          <div class="se-builder-cat__head">
            <h4>{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</h4>
          </div>
          <ul class="se-cards-list">
            <li v-for="c in (content.cards[cat] || [])" :key="c.key">
              <button type="button" class="se-chip se-chip--selectable"
                      :class="{ 'is-active': (custom.selection[cat] || []).includes(c.key) }"
                      @click="toggleCustomPick(cat, c.key)">
                {{ c.title }}
              </button>
            </li>
          </ul>
        </div>

        <label class="se-custom__note">
          <span>{{ $t('agileTraining.scrumEvents.customNoteLabel') }}</span>
          <textarea v-model="custom.note" maxlength="400" rows="3"
                    :placeholder="$t('agileTraining.scrumEvents.customNotePh')"></textarea>
        </label>
      </div>

      <div class="se-card__actions">
        <button class="se-btn se-btn--ghost" @click="goStep('final')">
          ← {{ $t('agileTraining.scrumEvents.back') }}
        </button>
        <button class="se-btn se-btn--primary"
                :disabled="!custom.context_key || submitting"
                @click="saveCustom">
          {{ submitting ? $t('common.loading') : $t('agileTraining.scrumEvents.saveCustom') }}
        </button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';

const EMPTY_SELECTION = () => ({
  planning:  { goals: [], participants: [], artifacts: [], time: [], duration: [] },
  refinement: { goals: [], participants: [], artifacts: [], time: [], duration: [] },
  daily:     { goals: [], participants: [], artifacts: [], time: [], duration: [] },
  review:    { goals: [], participants: [], artifacts: [], time: [], duration: [] },
  retro:     { goals: [], participants: [], artifacts: [], time: [], duration: [] },
});

export default {
  name: 'AgileScrumEventsPlay',
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      loading: true,
      locale: 'ru',
      group: null,
      content: { stages: [], cards: {}, categories: [], errors: [], customs: [], reference: {} },
      participantToken: '',
      displayName: '',
      step: 'start',
      steps: [
        { key: 'context', labelKey: 'agileTraining.scrumEvents.stepContext' },
        { key: 'cards', labelKey: 'agileTraining.scrumEvents.stepCards' },
        { key: 'build', labelKey: 'agileTraining.scrumEvents.stepBuild' },
        { key: 'why', labelKey: 'agileTraining.scrumEvents.stepWhy' },
        { key: 'errors', labelKey: 'agileTraining.scrumEvents.stepErrors' },
        { key: 'final', labelKey: 'agileTraining.scrumEvents.stepFinal' },
      ],
      activeStage: 'planning',
      selection: EMPTY_SELECTION(),
      errorsSeen: [],
      lastEval: null,
      healthPct: 0,
      groupResults: null,
      submitting: false,
      custom: { context_key: '', selection: {}, note: '' },
      activeBuildCat: 'goals',
      pdfExporting: false,
    };
  },
  computed: {
    nextStageButtonLabel() {
      const stages = this.content.stages || [];
      const n = stages.length;
      if (n < 2) return this.$t('agileTraining.scrumEvents.cycleEvents');
      const start = stages.findIndex(s => s.key === this.activeStage);
      for (let k = 1; k <= n; k++) {
        const s = stages[(start + k) % n];
        if (s && !this.isStageFilled(s.key)) {
          return this.$t('agileTraining.scrumEvents.nextEventCta', { name: s.title });
        }
      }
      return this.$t('agileTraining.scrumEvents.cycleEvents');
    },
    activeStageObj() {
      return this.content.stages.find(s => s.key === this.activeStage) || null;
    },
    allStagesFilled() {
      return this.content.stages.every(s => this.isStageFilled(s.key));
    },
    problemsByStage() {
      const out = {};
      const stages = this.lastEval?.stages || {};
      for (const k in stages) {
        const cats = stages[k].categories || {};
        const red = [];
        for (const cat in cats) {
          const c = cats[cat];
          if ((c.red || []).length || (c.missing || []).length) red.push(cat);
        }
        if (red.length) out[k] = red;
      }
      return out;
    },
    problematicStages() {
      return this.content.stages.filter(s => this.problemsByStage[s.key]);
    },
    hasRed() {
      return Object.keys(this.problemsByStage).length > 0;
    },
  },
  watch: {
    activeStage() {
      const cats = this.content.categories || [];
      const st = this.selection[this.activeStage] || {};
      const firstEmpty = cats.find(c => !(st[c] || []).length);
      this.activeBuildCat = firstEmpty || cats[0] || 'goals';
    },
    locale(v) {
      localStorage.setItem('language', v);
      if (this.$i18n) this.$i18n.locale = v;
      this.reloadContent();
    },
  },
  async mounted() {
    this.locale = (localStorage.getItem('language') === 'en') ? 'en' : 'ru';
    if (this.$i18n) this.$i18n.locale = this.locale;
    this.participantToken = localStorage.getItem(`scrum_events_token_${this.slug}`) || '';
    this.displayName = localStorage.getItem(`scrum_events_name_${this.slug}`) || '';
    await this.reloadContent();
    this.loading = false;
  },
  methods: {
    setLocale(lc) { this.locale = lc; },
    stepIndex(key) { return this.steps.findIndex(s => s.key === key); },
    goStep(s) { this.step = s; window.scrollTo({ top: 0, behavior: 'smooth' }); },
    stageEmoji(key) {
      return {
        planning: '📋',
        refinement: '🔍',
        daily: '🔄',
        review: '📊',
        retro: '🛠️',
      }[key] || '•';
    },
    cardTitle(cat, key) {
      for (const c of (this.content.cards[cat] || [])) if (c.key === key) return c.title;
      return key;
    },
    categoryEmoji(cat) {
      const m = {
        goals: '🎯', participants: '👥', artifacts: '📋', time: '⏰', duration: '⏱️',
      };
      return m[cat] || '•';
    },
    categoryAccent(cat) {
      return {
        goals: 'goals', participants: 'people', artifacts: 'artifact', time: 'time', duration: 'duration',
      }[cat] || 'default';
    },
    focusBuildColumn(cat) {
      this.activeBuildCat = cat;
      this.$nextTick(() => {
        const id = `se-col-${this.activeStage}-${cat}`;
        const el = document.getElementById(id);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
      });
    },
    goNextUnfilledStage() {
      const stages = this.content.stages || [];
      const n = stages.length;
      const start = stages.findIndex(s => s.key === this.activeStage);
      for (let k = 1; k <= n; k++) {
        const s = stages[(start + k) % n];
        if (s && !this.isStageFilled(s.key)) {
          this.activeStage = s.key;
          this.$nextTick(() => {
            const c0 = (this.content.categories || [])[0];
            if (c0) this.focusBuildColumn(c0);
          });
          return;
        }
      }
    },
    isPicked(stageKey, cat, key) {
      return (this.selection[stageKey]?.[cat] || []).includes(key);
    },
    isStageFilled(stageKey) {
      const st = this.selection[stageKey] || {};
      return (this.content.categories || []).every(c => (st[c] || []).length > 0);
    },
    togglePick(stageKey, cat, key) {
      const arr = [...(this.selection[stageKey]?.[cat] || [])];
      const idx = arr.indexOf(key);
      if (idx >= 0) arr.splice(idx, 1); else arr.push(key);
      this.selection = {
        ...this.selection,
        [stageKey]: { ...this.selection[stageKey], [cat]: arr },
      };
    },
    toggleError(key) {
      const idx = this.errorsSeen.indexOf(key);
      if (idx >= 0) this.errorsSeen = this.errorsSeen.filter(x => x !== key);
      else this.errorsSeen = [...this.errorsSeen, key];
    },
    toggleCustomPick(cat, key) {
      const arr = [...(this.custom.selection[cat] || [])];
      const idx = arr.indexOf(key);
      if (idx >= 0) arr.splice(idx, 1); else arr.push(key);
      this.custom = {
        ...this.custom,
        selection: { ...this.custom.selection, [cat]: arr },
      };
    },
    pickClass(stageKey, cat, key) {
      const cats = this.lastEval?.stages?.[stageKey]?.categories?.[cat];
      if (!cats) return '';
      if ((cats.green || []).includes(key)) return 'se-pick--green';
      if ((cats.yellow || []).includes(key)) return 'se-pick--yellow';
      if ((cats.red || []).includes(key)) return 'se-pick--red';
      return '';
    },
    async reloadContent() {
      try {
        const params = { locale: this.locale };
        if (this.participantToken) params.participant_token = this.participantToken;
        const res = await axios.get(
          `/api/agile-training/scrum-events/g/${this.slug}/state`, { params });
        this.group = res.data.group;
        this.content = res.data.content || this.content;
        const answer = res.data.answer;
        if (answer && answer.data) {
          const sel = answer.data.selection || {};
          // merge into default shape
          const merged = EMPTY_SELECTION();
          for (const k in merged) {
            for (const cat in merged[k]) {
              merged[k][cat] = (sel[k]?.[cat] || []).slice();
            }
          }
          this.selection = merged;
          this.errorsSeen = (answer.data.errors_seen || []).slice();
          this.lastEval = answer.data.evaluation || null;
          this.healthPct = answer.health_pct || 0;
          const custom = answer.data.custom;
          if (custom) {
            this.custom = {
              context_key: custom.context_key || '',
              selection: custom.selection || {},
              note: custom.note || '',
            };
          }
        }
      } catch (e) { console.error(e); }
    },
    async startRun() {
      if (this.displayName) localStorage.setItem(`scrum_events_name_${this.slug}`, this.displayName);
      if (!this.participantToken) {
        try {
          const res = await axios.post(
            `/api/agile-training/g/${this.slug}/participant`,
            { display_name: this.displayName || null });
          this.participantToken = res.data.participant_token;
          localStorage.setItem(`scrum_events_token_${this.slug}`, this.participantToken);
          await this.reloadContent();
        } catch (e) {
          alert(e.response?.data?.error || 'Failed to join');
          return;
        }
      }
      if (this.healthPct) {
        await this.loadGroupResults();
        this.step = 'final';
      } else {
        this.step = 'context';
      }
    },
    startBuilding() {
      this.activeStage = this.content.stages?.[0]?.key || 'planning';
      this.activeBuildCat = (this.content.categories || [])[0] || 'goals';
      this.goStep('build');
    },
    async loadGroupResults() {
      try {
        const res = await axios.get(
          `/api/agile-training/scrum-events/g/${this.slug}/results`,
          { params: { locale: this.locale } });
        this.groupResults = res.data;
      } catch (_) { this.groupResults = null; }
    },
    async submit() {
      this.submitting = true;
      try {
        const body = {
          participant_token: this.participantToken,
          selection: this.selection,
          errors_seen: this.errorsSeen,
          custom: this.custom.context_key ? this.custom : null,
        };
        const res = await axios.post(
          `/api/agile-training/scrum-events/g/${this.slug}/answer`, body);
        this.lastEval = res.data.evaluation;
        this.healthPct = res.data.health_pct;
        if (this.step === 'why') {
          this.goStep('errors');
        } else if (this.step === 'fix') {
          await this.loadGroupResults();
          this.goStep('final');
        } else {
          await this.loadGroupResults();
          this.goStep('final');
        }
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.submitting = false;
      }
    },
    onErrorsNext() {
      if (this.hasRed) {
        this.goStep('fix');
      } else {
        this.submit().then(() => {}); // saves errors_seen and goes to final
      }
    },
    async saveCustom() {
      this.submitting = true;
      try {
        const body = {
          participant_token: this.participantToken,
          selection: this.selection,
          errors_seen: this.errorsSeen,
          custom: this.custom,
        };
        await axios.post(
          `/api/agile-training/scrum-events/g/${this.slug}/answer`, body);
        this.goStep('final');
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally { this.submitting = false; }
    },
    async replay() {
      if (!confirm(this.$t('agileTraining.scrumEvents.replayConfirm'))) return;
      this.selection = EMPTY_SELECTION();
      this.errorsSeen = [];
      this.lastEval = null;
      this.healthPct = 0;
      this.custom = { context_key: '', selection: {}, note: '' };
      this.goStep('context');
    },
    async exportFinalToPdf() {
      const el = this.$refs.pdfExportRoot;
      if (!el) return;
      this.pdfExporting = true;
      try {
        const res = await exportElementToPdf(el, `agile-scrum-events-${this.slug}`);
        if (!res.ok) throw new Error(res.error || 'export');
      } catch (e) {
        console.error(e);
        alert(this.$t('agileTraining.common.downloadPdfError'));
      } finally {
        this.pdfExporting = false;
      }
    },
  },
};
</script>

<style scoped>
.se-play { max-width: 1100px; margin: 0 auto; padding: 20px 18px 80px; color: #0f172a; }
.se-play--board { max-width: 1400px; }
.se-play__top { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.se-play__brand { display: flex; align-items: center; gap: 10px; }
.se-play__icon { font-size: 26px; }
.se-play__brand-title { font-weight: 800; font-size: 18px; }
.se-play__brand-sub { color: #64748b; font-size: 13px; }
.se-play__lang { display: flex; gap: 4px; }
.se-lang__btn {
  background: #e2e8f0 !important; color: #0f172a !important;
  border: none !important; border-radius: 999px !important;
  padding: 4px 10px !important; font-weight: 700; cursor: pointer;
  font-size: 12px; transition: background 0.15s ease;
}
.se-lang__btn:hover { background: #cbd5e1 !important; }
.se-lang__btn.is-active {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important;
}
.se-play__loading { color: #64748b; padding: 40px 0; text-align: center; }

.se-steps { display: flex; gap: 6px; overflow-x: auto; padding: 8px 0 14px; margin-bottom: 8px; border-bottom: 1px dashed #e2e8f0; }
.se-steps__item { display: flex; align-items: center; gap: 6px; padding: 6px 10px; border-radius: 999px; background: #f1f5f9; font-size: 12px; color: #64748b; white-space: nowrap; }
.se-steps__item.is-active { background: linear-gradient(135deg, #14b8a6, #0891b2); color: #fff; font-weight: 700; }
.se-steps__item.is-done { background: #dcfce7; color: #065f46; }
.se-steps__num { font-weight: 800; }

.se-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 22px 20px; margin-bottom: 16px; }
.se-card--center { text-align: center; }
.se-card h1 { font-size: 24px; margin: 0 0 8px; }
.se-card h2 { font-size: 20px; margin: 0 0 8px; }
.se-card__lead { color: #475569; margin: 0 0 16px; }
.se-card__actions { display: flex; justify-content: space-between; gap: 10px; margin-top: 22px; flex-wrap: wrap; }

.se-btn {
  border: none !important; cursor: pointer; font-weight: 700;
  border-radius: 12px !important; padding: 10px 18px !important;
  font-size: 14px; transition: transform 0.1s ease, box-shadow 0.15s ease, background 0.15s ease;
}
.se-btn--primary {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important;
  box-shadow: 0 6px 14px rgba(20, 184, 166, 0.25);
}
.se-btn--primary:hover { transform: translateY(-1px); box-shadow: 0 10px 20px rgba(20, 184, 166, 0.32); }
.se-btn--primary:active { transform: translateY(1px); }
.se-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.se-btn--ghost {
  background: #f1f5f9 !important; color: #0f172a !important;
  border: 1px solid #e2e8f0 !important;
}
.se-btn--ghost:hover { background: #e2e8f0 !important; }

.se-defs, .se-context { list-style: none; padding: 0; margin: 0 0 16px; display: flex; flex-direction: column; gap: 8px; text-align: left; }
.se-defs li, .se-context li { padding: 8px 10px; border: 1px dashed #e2e8f0; border-radius: 10px; background: #f8fafc; font-size: 14px; }
.se-start__name { display: flex; flex-direction: column; gap: 4px; margin: 16px 0; text-align: left; }
.se-start__name input { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; }

.se-cards-cat { margin-bottom: 14px; }
.se-cards-cat h3 { font-size: 14px; text-transform: uppercase; letter-spacing: 0.04em; color: #64748b; margin: 0 0 6px; }
.se-cards-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 6px; }
.se-chip {
  display: inline-block; padding: 6px 12px;
  background: #f8fafc; border: 1px solid #e2e8f0;
  border-radius: 999px; font-size: 13px;
}
.se-chip--selectable {
  cursor: pointer; background: #fff !important; color: #0f172a !important;
  border: 1px solid #cbd5e1 !important; transition: all 0.15s ease;
}
.se-chip--selectable:hover { background: #f1f5f9 !important; border-color: #94a3b8 !important; }
.se-chip--selectable.is-active {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important; border-color: transparent !important;
  box-shadow: 0 4px 10px rgba(20, 184, 166, 0.25);
}

.se-stage-tabs { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.se-stage-tabs--board { margin-bottom: 10px; }
.se-stage-tab {
  background: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #e2e8f0 !important;
  padding: 8px 14px !important; border-radius: 999px !important;
  cursor: pointer; font-weight: 700; font-size: 13px;
  display: inline-flex; align-items: center; gap: 6px;
}
.se-stage-tab__text { text-align: left; line-height: 1.25; max-width: 200px; }
.se-stage-tab:hover { background: #e2e8f0 !important; }
.se-stage-tab.is-active {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important; color: #fff !important;
  border-color: transparent !important;
  box-shadow: 0 4px 12px rgba(8, 145, 178, 0.22);
}
.se-stage-tab.is-filled:not(.is-active) { border-color: #a7f3d0; background: #f0fdf4 !important; }
.se-stage-tab.is-filled .se-stage-tab__mark { color: #10b981; }
.se-stage-tab.is-active.is-filled .se-stage-tab__mark { color: #dcfce7; }
.se-stage-body__intro { background: #ecfeff; border: 1px solid #a5f3fc; padding: 10px 12px; border-radius: 10px; color: #0f766e; margin-bottom: 12px; font-size: 13px; }

/* —— Сборка: доска Miro —— */
.se-card--build { padding: 20px 16px 24px; }
.se-build__header { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.se-build__title { margin: 0 0 4px; font-size: 20px; }
.se-build__lead { margin: 0; max-width: 720px; }
.se-build__swipe-hint { margin: 0; font-size: 12px; color: #64748b; max-width: 280px; line-height: 1.4; }
.se-build__canvas {
  background: #f1f5f9;
  background-image: radial-gradient(#cbd5e1 1px, transparent 1px);
  background-size: 16px 16px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  padding: 14px 10px 12px;
  margin-top: 8px;
}
.se-build__event-banner {
  display: flex; gap: 10px; align-items: flex-start;
  background: #fff !important; border: 1px solid #a5f3fc !important;
  border-radius: 12px; padding: 10px 12px; margin-bottom: 12px;
  box-shadow: 0 2px 6px rgba(0,0,0,.04);
}
.se-build__event-banner p { margin: 0; color: #0f766e; font-size: 14px; line-height: 1.45; }
.se-build__event-emoji { font-size: 22px; line-height: 1; flex-shrink: 0; }
.se-build__category-strip {
  display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; justify-content: center;
}
.se-build__strip-pill {
  display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
  padding: 6px 10px; border-radius: 999px; border: 1px solid #e2e8f0; background: #fff;
  font-size: 12px; font-weight: 700; color: #334155; transition: all 0.15s ease;
}
.se-build__strip-pill:hover { background: #f8fafc; border-color: #cbd5e1; }
.se-build__strip-pill.is-done { background: #ecfdf5; border-color: #6ee7b7; }
.se-build__strip-pill.is-active { outline: 2px solid #14b8a6; outline-offset: 1px; }
.se-build__strip-ic { font-size: 14px; }
.se-build__strip-label { max-width: 100px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
@media (min-width: 900px) { .se-build__strip-label { max-width: none; } }
.se-build__strip-badge {
  min-width: 1.1rem; text-align: center; background: #0d9488; color: #fff; border-radius: 999px;
  font-size: 10px; font-weight: 800; padding: 1px 5px; line-height: 1.2;
}
.se-build__board {
  display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; align-items: start;
  padding: 2px 0 8px;
}
.se-build-col {
  background: #fff; border-radius: 14px; padding: 10px 8px 12px; min-width: 0;
  box-shadow: 0 1px 3px rgba(0,0,0,.07);
  border: 1px solid #e2e8f0; border-top: 4px solid #94a3b8;
  transition: box-shadow 0.2s ease, border-color 0.2s ease, transform 0.15s;
}
.se-build-col--goals { border-top-color: #f59e0b; }
.se-build-col--people { border-top-color: #0ea5e9; }
.se-build-col--artifact { border-top-color: #8b5cf6; }
.se-build-col--time { border-top-color: #f43f5e; }
.se-build-col--duration { border-top-color: #22c55e; }
.se-build-col--focus { box-shadow: 0 4px 16px rgba(20, 184, 166, 0.2); border-color: #99f6e4; }
.se-build-col__head { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; padding: 0 2px; }
.se-build-col__ic { font-size: 20px; line-height: 1; }
.se-build-col__title { margin: 0; font-size: 13px; font-weight: 800; line-height: 1.2; color: #0f172a; }
.se-build-col__sub { margin: 2px 0 0; font-size: 11px; color: #64748b; font-weight: 600; }
.se-build-col__notes { display: flex; flex-direction: column; gap: 8px; max-height: 62vh; overflow-y: auto; padding-right: 2px; }
.se-note {
  position: relative; display: block; width: 100%; box-sizing: border-box;
  text-align: left; cursor: pointer; border: 2px solid transparent; font: inherit; font-size: 12px; line-height: 1.35;
  padding: 8px 8px 8px 9px; border-radius: 2px 10px 10px 3px; color: #0f172a;
  background: linear-gradient(145deg, #fffde7 0%, #fff9c4 50%, #fefce8 100%);
  box-shadow: 1px 2px 0 rgba(15, 23, 42, 0.08), 0 3px 10px rgba(0, 0, 0, 0.05);
  transform: rotate(var(--note-rot, 0deg));
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, color 0.15s ease;
}
.se-note:hover {
  z-index: 1;
  box-shadow: 1px 3px 0 rgba(15, 23, 42, 0.1), 0 6px 14px rgba(0, 0, 0, 0.08);
  transform: rotate(0deg) scale(1.01);
}
.se-note.is-active {
  z-index: 2;
  color: #fff;
  background: linear-gradient(145deg, #0d9488, #047857) !important;
  border: 2px solid #065f46 !important;
  box-shadow:
    0 0 0 2px rgba(255, 255, 255, 0.85),
    0 6px 18px rgba(4, 120, 87, 0.45);
  transform: rotate(0deg) scale(1.02);
}
.se-note.is-active .se-note__text::before {
  content: '✓ ';
  font-weight: 800;
}
.se-note__text { display: block; }
.se-build__footer { display: flex; align-items: center; justify-content: center; min-height: 40px; margin-top: 10px; gap: 8px; }
.se-build__stage-ok { font-size: 13px; font-weight: 700; color: #047857; }
.se-btn--soft {
  background: #e0f2fe !important; color: #0369a1 !important; border: 1px solid #7dd3fc !important;
  font-size: 13px !important; padding: 8px 16px !important;
}
.se-btn--soft:hover { background: #bae6fd !important; }
.se-card__actions--build { margin-top: 18px; }
@media (max-width: 1100px) {
  .se-build__board {
    display: flex; overflow-x: auto; scroll-snap-type: x mandatory; gap: 12px;
    padding-bottom: 10px; -webkit-overflow-scrolling: touch;
  }
  .se-build-col {
    flex: 0 0 min(90vw, 300px);
    max-width: 300px;
    scroll-snap-align: start;
  }
  .se-build-col__notes { max-height: 50vh; }
}
@media (max-width: 560px) {
  .se-stage-tab__text { max-width: 120px; font-size: 12px; }
  .se-build__strip-label { max-width: 72px; font-size: 10px; line-height: 1.15; }
  .se-build__strip-pill { padding: 8px 8px; }
  .se-build__strip-ic { font-size: 16px; }
}
.se-builder-cat { margin-bottom: 12px; }
.se-builder-cat__head h4 { margin: 0 0 6px; font-size: 14px; }

.se-why { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.se-why__item { padding: 12px; border-radius: 12px; border: 1px solid #e2e8f0; background: #f8fafc; }
.se-why__title { font-size: 15px; margin-bottom: 6px; }
.se-why__emoji { margin-right: 6px; }
.se-why__purpose { color: #0f766e; font-size: 14px; margin-bottom: 2px; }
.se-why__problem { color: #475569; font-size: 13px; }

.se-errors-list { list-style: none; padding: 0; margin: 0; display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.se-err-card {
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px;
  cursor: pointer; background: #fff; transition: all 0.15s ease;
}
.se-err-card:hover { background: #f8fafc; }
.se-err-card.is-active { background: #fee2e2; border-color: #fca5a5; }
.se-err-card__title { font-weight: 700; margin-bottom: 6px; }
.se-err-card__cons { list-style: none; padding: 0; margin: 0; color: #475569; font-size: 13px; }

.se-fix-stage { border: 1px dashed #e2e8f0; border-radius: 12px; padding: 12px; margin-bottom: 12px; background: #fff; }

.se-summary { display: flex; gap: 12px; margin-bottom: 14px; flex-wrap: wrap; }
.se-summary__box { flex: 1 1 200px; padding: 14px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; text-align: center; }
.se-summary__label { color: #64748b; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.se-summary__val { font-size: 32px; font-weight: 800; color: #0f766e; }

.se-board { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 12px; margin-top: 8px; }
.se-col {
  background: #f8fafc; border: 2px solid #e2e8f0; border-radius: 14px;
  padding: 12px; display: flex; flex-direction: column; gap: 10px;
}
.se-col--green { border-color: #10b981; background: #f0fdf4; }
.se-col--yellow { border-color: #f59e0b; background: #fffbeb; }
.se-col--red { border-color: #ef4444; background: #fef2f2; }
.se-col__head h4 { margin: 0; font-size: 14px; font-weight: 800; }
.se-col__purpose { color: #475569; font-size: 12px; display: block; margin-top: 4px; }
.se-col__cat { border-top: 1px dashed #e2e8f0; padding-top: 6px; }
.se-col__cat-title { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
.se-col__picks { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
.se-pick { padding: 4px 6px; border-radius: 8px; background: #fff; border: 1px solid transparent; display: flex; justify-content: space-between; align-items: center; }
.se-pick--green { background: #dcfce7; border-color: #86efac; }
.se-pick--yellow { background: #fef3c7; border-color: #fde68a; }
.se-pick--red { background: #fee2e2; border-color: #fca5a5; }
.se-pick__pct { color: #64748b; font-weight: 700; font-size: 11px; }
.se-col__missing { font-size: 11px; color: #991b1b; margin-top: 4px; }

.se-pill { display: inline-block; background: #e2e8f0; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.se-pill--green { background: #dcfce7; color: #047857; }
.se-pill--yellow { background: #fef3c7; color: #92400e; }
.se-pill--red { background: #fee2e2; color: #991b1b; }
.se-pill--gray { background: #e2e8f0; color: #475569; }

.se-final__toolbar { margin: 0 0 16px; }
.se-pdf-export-root { padding-top: 4px; }
.se-final__debrief-hint { color: #64748b; font-size: 14px; margin: 0 0 16px; line-height: 1.5; }
.se-board--final-plain { margin-top: 0; }
.se-col--final { border-color: #e2e8f0; background: #f8fafc; }
.se-pick--plain { background: #f1f5f9; border: 1px solid #e2e8f0; color: #0f172a; }
.se-final-legend {
  display: flex; flex-wrap: wrap; align-items: flex-start; gap: 12px 20px;
  padding: 12px 14px; margin-bottom: 18px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px;
}
.se-final-legend__title { font-weight: 800; font-size: 13px; color: #0f172a; min-width: 100%; }
@media (min-width: 600px) { .se-final-legend__title { min-width: 140px; } }
.se-final-legend__list { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 12px; color: #475569; }
.se-leg { display: inline-block; width: 10px; height: 10px; border-radius: 3px; margin-right: 4px; vertical-align: middle; }
.se-leg--green { background: #22c55e; }
.se-leg--yellow { background: #f59e0b; }
.se-leg--red { background: #ef4444; }
.se-leg--missing { background: transparent; border: 1px dashed #b91c1c; }
.se-ref__intro { color: #475569; font-size: 13px; margin: 0 0 12px; }
.se-ref-stage {
  border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px 12px 6px; margin-bottom: 12px; background: #fff;
}
.se-ref-stage__title { margin: 0 0 10px; font-size: 15px; display: flex; align-items: center; gap: 6px; }
.se-ref-stage__emoji { font-size: 18px; }
.se-ref-cat { border-top: 1px dashed #e2e8f0; padding: 8px 0; }
.se-ref-cat:first-of-type { border-top: none; padding-top: 0; }
.se-ref-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
@media (max-width: 700px) { .se-ref-cols { grid-template-columns: 1fr; } }
.se-ref-block { font-size: 12px; }
.se-ref-block__label { font-weight: 700; color: #64748b; margin-bottom: 4px; }
.se-ref-pills { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px; }
.se-ref-pill { padding: 3px 8px; border-radius: 6px; font-size: 12px; line-height: 1.3; }
.se-ref-pill--expected { background: #dcfce7; border: 1px solid #86efac; color: #14532d; }
.se-ref-pill--acceptable { background: #fef3c7; border: 1px solid #fde68a; color: #92400e; }

.se-section-title { margin: 18px 0 8px; font-size: 15px; font-weight: 800; }
.se-group-comp { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; }
.se-group-stage { border: 1px solid #e2e8f0; border-radius: 12px; padding: 10px; background: #fff; }
.se-group-stage h4 { margin: 0 0 6px; font-size: 13px; }
.se-group-stage__cat { margin-top: 6px; }

.se-fac__hint { color: #64748b; font-size: 12px; }

.se-contexts { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 14px; }
.se-context-card {
  flex: 1 1 220px; text-align: left; background: #fff !important;
  border: 1px solid #cbd5e1 !important; border-radius: 12px !important; padding: 12px !important;
  cursor: pointer; transition: all 0.15s ease;
}
.se-context-card:hover { background: #f8fafc !important; }
.se-context-card.is-active {
  border-color: #0891b2 !important; background: #ecfeff !important;
  box-shadow: 0 6px 14px rgba(8, 145, 178, 0.18);
}
.se-context-card__title { font-weight: 700; margin-bottom: 4px; font-size: 14px; }
.se-context-card__desc { color: #475569; font-size: 12px; }
.se-custom__note { display: flex; flex-direction: column; gap: 4px; margin-top: 14px; }
.se-custom__note textarea { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; font-family: inherit; }

@media (max-width: 900px) {
  .se-board, .se-group-comp { grid-template-columns: 1fr 1fr; }
  .se-errors-list { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .se-board, .se-group-comp { grid-template-columns: 1fr; }
}
</style>
