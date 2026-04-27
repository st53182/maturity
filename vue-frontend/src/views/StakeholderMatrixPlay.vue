<template>
  <div class="sh-play modern-ui" v-if="!loadError && !initialLoading">
    <div class="sh-play__lang" role="group" :aria-label="$t('agileTraining.common.language')">
      <button type="button" :class="{ active: locale === 'ru' }" @click="switchLang('ru')">RU</button>
      <button type="button" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
    </div>

    <header class="sh-play__head">
      <h1 class="sh-play__title">{{ $t('agileTraining.stakeholderMatrix.playTitle') }}</h1>
      <p class="sh-play__group" v-if="groupName">· {{ groupName }}</p>
      <p v-if="activeCase" class="sh-play__case-tag">
        <span>{{ activeCase.emoji }}</span> {{ activeCase.title }}
      </p>
    </header>

    <div v-if="!participantToken" class="sh-card sh-join">
      <label class="sh-label">{{ $t('agileTraining.stakeholderMatrix.nameLabel') }}</label>
      <input v-model="joinName" class="sh-input" maxlength="80" :placeholder="$t('agileTraining.stakeholderMatrix.namePlaceholder')" />
      <button type="button" class="sh-btn sh-btn--primary" :disabled="joining" @click="joinGroup">
        {{ $t('agileTraining.stakeholderMatrix.join') }}
      </button>
      <p v-if="joinError" class="sh-err">{{ joinError }}</p>
    </div>

    <div v-else class="sh-flow">
      <nav class="sh-steps" aria-label="Progress">
        <span v-for="(s, i) in screenOrder" :key="s" class="sh-steps__item" :class="{ 'sh-steps__item--on': s === screen, 'sh-steps__item--done': stepIndex(s) < stepIndex(screen) }">
          {{ i + 1 }}
        </span>
      </nav>
      <p v-if="saveState === 'saving'" class="sh-hint">{{ $t('agileTraining.stakeholderMatrix.saving') }}</p>
      <p v-else-if="saveState === 'saved'" class="sh-hint sh-hint--ok">{{ $t('agileTraining.stakeholderMatrix.saved') }}</p>

      <!-- 1. context = case picker -->
      <section v-if="screen === 'context'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.context.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.context.lead') }}</p>
        <div class="sh-cases">
          <article
            v-for="c in localizedCases"
            :key="c.key"
            class="sh-case"
            :class="{ 'sh-case--on': caseKey === c.key }"
            @click="pickCase(c.key)"
            tabindex="0"
            role="button"
            @keydown.enter.prevent="pickCase(c.key)"
            @keydown.space.prevent="pickCase(c.key)"
          >
            <div class="sh-case__head">
              <span class="sh-case__emoji">{{ c.emoji }}</span>
              <h3 class="sh-case__title">{{ c.title }}</h3>
            </div>
            <p class="sh-case__lead">{{ c.lead }}</p>
            <p class="sh-case__goal"><span>👉</span> {{ $t('agileTraining.stakeholderMatrix.screens.context.goalLabel') }}: {{ c.goal }}</p>
            <p class="sh-case__flavor"><strong>{{ $t('agileTraining.stakeholderMatrix.screens.context.flavorLabel') }}:</strong> {{ c.flavor }}</p>
            <div class="sh-case__cta">
              <span v-if="caseKey === c.key" class="sh-case__check">✓</span>
              <span v-else>{{ $t('agileTraining.stakeholderMatrix.screens.context.pickCta') }}</span>
            </div>
          </article>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!caseKey" @click="goScreen('roles')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
      </section>

      <!-- 2. personas -->
      <section v-else-if="screen === 'roles'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.roles.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.roles.lead') }}</p>
        <div class="sh-personas">
          <article v-for="rid in roleIds" :key="rid" class="sh-persona">
            <div class="sh-persona__head">
              <span class="sh-persona__emoji">{{ persona(rid).emoji }}</span>
              <div>
                <p class="sh-persona__name">{{ persona(rid).name }}</p>
                <p class="sh-persona__role">{{ persona(rid).role }}</p>
              </div>
            </div>
            <p class="sh-persona__motivation">
              <span class="sh-persona__label">{{ $t('agileTraining.stakeholderMatrix.screens.roles.motivationLabel') }}.</span>
              {{ persona(rid).motivation }}
            </p>
            <p class="sh-persona__quote">{{ persona(rid).quote }}</p>
          </article>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('context')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('matrix_r1')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
      </section>

      <!-- 3. matrix r1 -->
      <section v-else-if="screen === 'matrix_r1'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.matrix.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.leadR1') }}</p>
        <MatrixGrid
          :round-key="'r1'"
          :locale="locale"
          :placements="placementsR1"
          :all-role-ids="roleIds"
          :content-copy="contentCopy"
          :level-labels-y="contentCopy.level_labels"
          :level-labels-x="contentCopy.level_labels_x"
          :role-label="roleLabel"
          :persona-map="currentPersonas"
          @update:placements="onPlacementsR1"
        />
        <CoverageMeter :placements="placementsR1" :locale="locale" />
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('roles')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!allRolesPlaced(placementsR1)" @click="goScreen('discussion')">
            {{ $t('agileTraining.stakeholderMatrix.next') }} →
          </button>
        </div>
        <p v-if="!allRolesPlaced(placementsR1)" class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.needAll') }}</p>
      </section>

      <!-- 4. discussion -->
      <section v-else-if="screen === 'discussion'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.discussion.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.discussion.lead') }}</p>
        <div v-for="rid in placedRolesR1" :key="rid" class="sh-discuss-block">
          <h3 class="sh-discuss-h">
            <span class="sh-discuss-emoji">{{ persona(rid).emoji }}</span>
            {{ persona(rid).name }}
            <small>· {{ persona(rid).role }}</small>
          </h3>
          <label class="sh-label">{{ $t('agileTraining.stakeholderMatrix.discussion.q1') }}</label>
          <textarea v-model="discussion[rid].why_power" class="sh-ta" rows="2" @input="markDirty" />
          <label class="sh-label">{{ $t('agileTraining.stakeholderMatrix.discussion.q2') }}</label>
          <textarea v-model="discussion[rid].why_interest" class="sh-ta" rows="2" @input="markDirty" />
          <label class="sh-label">{{ $t('agileTraining.stakeholderMatrix.discussion.q3') }}</label>
          <textarea v-model="discussion[rid].if_ignore" class="sh-ta" rows="2" @input="markDirty" />
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('matrix_r1')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('strategy')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
        <AiBlock
          :disabled="!participantToken"
          :remaining="aiRemaining"
          :title="$t('agileTraining.stakeholderMatrix.aiTitle')"
          :placeholder="$t('agileTraining.stakeholderMatrix.aiPlaceholder')"
          @ask="askAi('discussion', $event)"
        />
      </section>

      <!-- 5. strategy with starters -->
      <section v-else-if="screen === 'strategy'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.strategy.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.strategy.lead') }}</p>
        <div v-for="key in ['hh', 'hl', 'lh', 'll']" :key="key" class="sh-strat-row">
          <label class="sh-label">{{ contentCopy.strategy_quadrant_hints[key] }}</label>
          <textarea v-model="strategyQuadrant[key]" class="sh-ta" rows="3" @input="markDirty" />
          <p class="sh-starter-h">{{ $t('agileTraining.stakeholderMatrix.screens.strategy.starterLabel') }}</p>
          <div class="sh-starters">
            <button
              v-for="(s, i) in starters(key)"
              :key="key + '-' + i"
              type="button"
              class="sh-starter"
              @click="appendStarter(key, s)"
            >
              + {{ s }}
            </button>
          </div>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('discussion')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('consequences')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
        <AiBlock
          :disabled="!participantToken"
          :remaining="aiRemaining"
          :title="$t('agileTraining.stakeholderMatrix.aiTitle')"
          :placeholder="$t('agileTraining.stakeholderMatrix.aiPlaceholder')"
          @ask="askAi('strategy', $event)"
        />
      </section>

      <!-- 6. consequences + reactions -->
      <section v-else-if="screen === 'consequences'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.consequences.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.consequences.lead') }}</p>
        <ul class="sh-bullets">
          <li v-for="(line, i) in consequenceListR1" :key="'c'+i">{{ line }}</li>
        </ul>
        <p v-if="!consequenceListR1.length" class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.consequences.empty') }}</p>
        <h3 v-if="strengthsR1.length" class="sh-subh">{{ $t('agileTraining.stakeholderMatrix.screens.consequences.strong') }}</h3>
        <ul v-if="strengthsR1.length" class="sh-bullets sh-bullets--pos">
          <li v-for="(line, i) in strengthsR1" :key="'s'+i">{{ line }}</li>
        </ul>

        <h3 class="sh-subh">{{ $t('agileTraining.stakeholderMatrix.screens.consequences.reactionsTitle') }}</h3>
        <div class="sh-reactions">
          <article v-for="r in reactionsR1" :key="'r-' + r.rid" class="sh-reaction" :class="'sh-reaction--' + r.bucket">
            <div class="sh-reaction__head">
              <span class="sh-reaction__emoji">{{ r.persona.emoji }}</span>
              <div>
                <p class="sh-reaction__name">{{ r.persona.name }}</p>
                <p class="sh-reaction__role">{{ r.persona.role }} · <em>{{ bucketLabel(r.bucket) }}</em></p>
              </div>
            </div>
            <p class="sh-reaction__quote">{{ r.quote }}</p>
          </article>
        </div>

        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('strategy')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('event')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
        <AiBlock
          :disabled="!participantToken"
          :remaining="aiRemaining"
          :title="$t('agileTraining.stakeholderMatrix.aiTitle')"
          :placeholder="$t('agileTraining.stakeholderMatrix.aiPlaceholder')"
          @ask="askAi('consequences', $event)"
        />
      </section>

      <!-- 7. event with impacts -->
      <section v-else-if="screen === 'event'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.event.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.event.lead') }}</p>
        <div class="sh-event-grid">
          <article
            v-for="ev in localizedEvents"
            :key="ev.key"
            class="sh-event-card"
            :class="{ 'sh-event-card--on': eventKey === ev.key }"
            @click="eventKey = ev.key; markDirty(); persist()"
            tabindex="0"
            role="button"
            @keydown.enter.prevent="eventKey = ev.key; markDirty(); persist()"
            @keydown.space.prevent="eventKey = ev.key; markDirty(); persist()"
          >
            <div class="sh-event-card__head">
              <span class="sh-event-card__emoji">{{ ev.emoji }}</span>
              <h3 class="sh-event-card__title">{{ ev.title }}</h3>
            </div>
            <p class="sh-event-card__lead">{{ ev.lead }}</p>
            <p class="sh-event-card__impact-h">{{ $t('agileTraining.stakeholderMatrix.screens.event.impactLabel') }}:</p>
            <ul class="sh-event-card__impact">
              <li v-for="im in ev.impacts" :key="ev.key + '-' + im.rid">
                <span class="sh-event-card__impact-emoji">{{ persona(im.rid).emoji }}</span>
                <span class="sh-event-card__impact-name">{{ persona(im.rid).name }}</span>
                <span class="sh-event-card__impact-note">— {{ im.note }}</span>
              </li>
            </ul>
          </article>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('consequences')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!eventKey" @click="prepRound2">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
      </section>

      <!-- 8. matrix r2 -->
      <section v-else-if="screen === 'matrix_r2'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.matrix.h2R2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.leadR2') }}</p>
        <div v-if="activeEvent" class="sh-event-recap">
          <span class="sh-event-card__emoji">{{ activeEvent.emoji }}</span>
          <strong>{{ activeEvent.title }}.</strong>
          <span>{{ activeEvent.lead }}</span>
        </div>
        <MatrixGrid
          :round-key="'r2'"
          :locale="locale"
          :placements="placementsR2"
          :all-role-ids="roleIds"
          :content-copy="contentCopy"
          :level-labels-y="contentCopy.level_labels"
          :level-labels-x="contentCopy.level_labels_x"
          :role-label="roleLabel"
          :persona-map="currentPersonas"
          :highlight-rids="eventTargetRids"
          @update:placements="onPlacementsR2"
        />
        <CoverageMeter :placements="placementsR2" :locale="locale" />
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('event')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!allRolesPlaced(placementsR2)" @click="goScreen('final')">{{ $t('agileTraining.stakeholderMatrix.finish') }} →</button>
        </div>
      </section>

      <!-- 9. final + diff -->
      <section v-else-if="screen === 'final'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.final.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.final.lead') }}</p>
        <div class="sh-two-col">
          <div>
            <h3>{{ $t('agileTraining.stakeholderMatrix.screens.final.round1') }}</h3>
            <ul class="sh-bullets">
              <li v-for="(line, i) in consequenceListR1" :key="'f1'+i">{{ line }}</li>
            </ul>
          </div>
          <div>
            <h3>{{ $t('agileTraining.stakeholderMatrix.screens.final.round2') }}</h3>
            <ul class="sh-bullets">
              <li v-for="(line, i) in consequenceListR2" :key="'f2'+i">{{ line }}</li>
            </ul>
            <ul v-if="strengthsR2.length" class="sh-bullets sh-bullets--pos">
              <li v-for="(line, i) in strengthsR2" :key="'f2p'+i">{{ line }}</li>
            </ul>
          </div>
        </div>

        <h3 class="sh-subh">{{ $t('agileTraining.stakeholderMatrix.screens.final.diffTitle') }}</h3>
        <p v-if="!roundDiff.length" class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.final.diffEmpty') }}</p>
        <ul v-else class="sh-diff">
          <li v-for="d in roundDiff" :key="'d-' + d.rid" class="sh-diff__item" :class="'sh-diff__item--' + d.kind">
            <span class="sh-diff__emoji">{{ d.persona.emoji }}</span>
            <strong>{{ d.persona.name }}</strong>
            <span class="sh-diff__role">· {{ d.persona.role }}</span>
            <span class="sh-diff__arrow">{{ diffArrow(d.kind) }}</span>
            <span class="sh-diff__kind">{{ diffLabel(d.kind) }}</span>
          </li>
        </ul>

        <h3 class="sh-subh">{{ $t('agileTraining.stakeholderMatrix.screens.final.reflect') }}</h3>
        <p class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.final.reflectLead') }}</p>
        <div class="sh-actions sh-actions--final">
          <button type="button" class="sh-btn sh-btn--primary sh-btn--print" @click="printReport">
            <span aria-hidden="true">📄</span>
            {{ $t('agileTraining.stakeholderMatrix.actions.print') }}
          </button>
          <button type="button" class="sh-btn" @click="showSummary = !showSummary">
            {{ showSummary
              ? $t('agileTraining.stakeholderMatrix.actions.hideSummary')
              : $t('agileTraining.stakeholderMatrix.actions.showSummary') }}
          </button>
          <button type="button" class="sh-btn sh-btn--ghost" @click="downloadJson">
            {{ $t('agileTraining.stakeholderMatrix.actions.json') }}
          </button>
        </div>

        <SummaryReport
          v-if="showSummary"
          dom-id="sh-report"
          :group-name="groupName"
          :participant-name="participantName"
          :locale="locale"
          :active-case="activeCase"
          :active-event="activeEvent"
          :placements-r1="placementsR1"
          :placements-r2="placementsR2"
          :discussion="discussion"
          :strategy-quadrant="strategyQuadrant"
          :strategy-hints="contentCopy.strategy_quadrant_hints"
          :reactions="reactionsR1"
          :diff="roundDiff"
          :consequences-r1="consequenceListR1"
          :consequences-r2="consequenceListR2"
          :strengths-r1="strengthsR1"
          :strengths-r2="strengthsR2"
          :personas="currentPersonas"
          :level-labels="contentCopy.level_labels || []"
          :level-labels-x="contentCopy.level_labels_x || []"
          :cell-strategy="contentCopy.cell_strategy || {}"
          :axis-x="(contentCopy.axis && contentCopy.axis.x) || ''"
          :axis-y="(contentCopy.axis && contentCopy.axis.y) || ''"
        />

        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('matrix_r2')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
        </div>
      </section>

      <!-- always-mounted hidden report just for printing -->
      <SummaryReport
        v-if="!showSummary && screen === 'final'"
        class="sh-report-print-only"
        dom-id="sh-report-print"
        :group-name="groupName"
        :participant-name="participantName"
        :locale="locale"
        :active-case="activeCase"
        :active-event="activeEvent"
        :placements-r1="placementsR1"
        :placements-r2="placementsR2"
        :discussion="discussion"
        :strategy-quadrant="strategyQuadrant"
        :strategy-hints="contentCopy.strategy_quadrant_hints"
        :reactions="reactionsR1"
        :diff="roundDiff"
        :consequences-r1="consequenceListR1"
        :consequences-r2="consequenceListR2"
        :strengths-r1="strengthsR1"
        :strengths-r2="strengthsR2"
        :personas="currentPersonas"
        :level-labels="contentCopy.level_labels || []"
        :level-labels-x="contentCopy.level_labels_x || []"
        :cell-strategy="contentCopy.cell_strategy || {}"
        :axis-x="(contentCopy.axis && contentCopy.axis.x) || ''"
        :axis-y="(contentCopy.axis && contentCopy.axis.y) || ''"
      />
    </div>
  </div>
  <div v-else class="sh-play sh-play--load">
    <p v-if="loadError" class="sh-err">{{ loadError }}</p>
    <p v-else>{{ $t('common.loading') }}…</p>
  </div>
</template>

<script>
import axios from 'axios';
import { syncI18nFallback } from '@/i18n';
import MatrixGrid from './stakeholderMatrix/MatrixGrid.vue';
import AiBlock from './stakeholderMatrix/AiBlock.vue';
import CoverageMeter from './stakeholderMatrix/CoverageMeter.vue';
import SummaryReport from './stakeholderMatrix/SummaryReport.vue';
import { computeConsequencesClient, computeStrengthsClient } from './stakeholderMatrix/logic.js';
import {
  PERSONAS, CASES, EVENTS, STRATEGY_STARTERS,
  buildReactions, diffRounds,
} from './stakeholderMatrix/content.js';

const TOKEN_KEY = 'at_stakeholder_m_token_';
const LS_KEY = 'at_stakeholder_m_state_';

export default {
  name: 'StakeholderMatrixPlay',
  components: { MatrixGrid, AiBlock, CoverageMeter, SummaryReport },
  props: { slug: { type: String, required: true } },
  data() {
    return {
      initialLoading: true,
      loadError: '',
      groupName: '',
      contentCopy: { axis: {}, level_labels: [], level_labels_x: [], cell_strategy: {}, event_labels: {}, strategy_quadrant_hints: {} },
      roleIds: [],
      eventKeys: [],
      caseKeys: [],
      locale: 'ru',
      screen: 'context',
      joinName: '',
      joining: false,
      joinError: '',
      participantToken: '',
      placementsR1: {},
      placementsR2: {},
      discussion: {},
      strategyQuadrant: { hh: '', hl: '', lh: '', ll: '' },
      eventKey: null,
      caseKey: null,
      aiRemaining: 12,
      saveState: 'idle',
      saveTimer: null,
      dirty: false,
      showSummary: false,
      participantName: '',
    };
  },
  computed: {
    screenOrder() {
      return ['context', 'roles', 'matrix_r1', 'discussion', 'strategy', 'consequences', 'event', 'matrix_r2', 'final'];
    },
    currentPersonas() {
      return PERSONAS[this.locale === 'en' ? 'en' : 'ru'] || PERSONAS.ru;
    },
    localizedCases() {
      return (CASES[this.locale === 'en' ? 'en' : 'ru'] || CASES.ru).filter(
        (c) => !this.caseKeys.length || this.caseKeys.includes(c.key),
      );
    },
    localizedEvents() {
      return (EVENTS[this.locale === 'en' ? 'en' : 'ru'] || EVENTS.ru).filter(
        (e) => !this.eventKeys.length || this.eventKeys.includes(e.key),
      );
    },
    activeCase() {
      return this.localizedCases.find((c) => c.key === this.caseKey) || null;
    },
    activeEvent() {
      return this.localizedEvents.find((e) => e.key === this.eventKey) || null;
    },
    eventTargetRids() {
      return (this.activeEvent && this.activeEvent.impacts ? this.activeEvent.impacts.map((i) => i.rid) : []);
    },
    placedRolesR1() {
      return this.roleIds.filter((rid) => this.placementsR1[rid] && this.placementsR1[rid].infl != null);
    },
    consequenceListR1() {
      return computeConsequencesClient(this.placementsR1, this.locale);
    },
    consequenceListR2() {
      return computeConsequencesClient(this.placementsR2, this.locale);
    },
    strengthsR1() {
      return computeStrengthsClient(this.placementsR1, this.locale);
    },
    strengthsR2() {
      return computeStrengthsClient(this.placementsR2, this.locale);
    },
    reactionsR1() {
      return buildReactions(this.placementsR1, this.locale, PERSONAS);
    },
    roundDiff() {
      return diffRounds(this.placementsR1, this.placementsR2, PERSONAS, this.locale);
    },
  },
  watch: {
    placementsR1: { deep: true, handler() { this.markDirty(); } },
    placementsR2: { deep: true, handler() { this.markDirty(); } },
  },
  async mounted() {
    this.participantToken = this.readToken();
    const ls = this.loadLocal();
    if (ls && ls.slug === this.slug) {
      this.applyState(ls, false);
    }
    this.locale = this.$i18n.locale === 'en' ? 'en' : 'ru';
    await this.bootstrap();
  },
  beforeUnmount() {
    if (this.saveTimer) clearTimeout(this.saveTimer);
  },
  methods: {
    readToken() {
      try { return localStorage.getItem(TOKEN_KEY + this.slug) || ''; } catch (_) { return ''; }
    },
    writeToken(t) {
      try { localStorage.setItem(TOKEN_KEY + this.slug, t || ''); } catch (_) { /* noop */ }
    },
    loadLocal() {
      try {
        const raw = localStorage.getItem(LS_KEY + this.slug);
        if (!raw) return null;
        return JSON.parse(raw);
      } catch (_) { return null; }
    },
    saveLocal() {
      try {
        const payload = {
          slug: this.slug,
          screen: this.screen,
          placementsR1: this.placementsR1,
          placementsR2: this.placementsR2,
          discussion: this.discussion,
          strategyQuadrant: this.strategyQuadrant,
          eventKey: this.eventKey,
          caseKey: this.caseKey,
        };
        localStorage.setItem(LS_KEY + this.slug, JSON.stringify(payload));
      } catch (_) { /* noop */ }
    },
    applyState(partial, fromServer) {
      if (partial.screen && this.screenOrder.includes(partial.screen)) this.screen = partial.screen;
      if (partial.placementsR1) this.placementsR1 = { ...partial.placementsR1 };
      if (partial.placementsR2) this.placementsR2 = { ...partial.placementsR2 };
      if (partial.discussion) {
        this.discussion = { ...this.discussion, ...partial.discussion };
      }
      if (partial.strategyQuadrant) {
        this.strategyQuadrant = { hh: partial.strategyQuadrant.hh || '', hl: partial.strategyQuadrant.hl || '', lh: partial.strategyQuadrant.lh || '', ll: partial.strategyQuadrant.ll || '' };
      }
      if (partial.eventKey !== undefined) this.eventKey = partial.eventKey;
      if (partial.caseKey !== undefined) this.caseKey = partial.caseKey;
      if (fromServer) this.saveLocal();
    },
    stepIndex(name) {
      return this.screenOrder.indexOf(name);
    },
    switchLang(code) {
      this.$i18n.locale = code;
      this.locale = code;
      syncI18nFallback();
      try { localStorage.setItem('language', code); } catch (_) { /* noop */ }
      this.bootstrap();
    },
    persona(rid) {
      return this.currentPersonas[rid] || { emoji: '👤', name: rid, role: rid, motivation: '', quote: '' };
    },
    roleLabel(rid) {
      const p = this.currentPersonas[rid];
      if (p) return `${p.name} · ${p.role}`;
      return this.$t('agileTraining.stakeholderMatrix.roles.' + rid);
    },
    bucketLabel(b) {
      return this.$t('agileTraining.stakeholderMatrix.coverage.' + b);
    },
    starters(quadrant) {
      const lc = this.locale === 'en' ? 'en' : 'ru';
      return (STRATEGY_STARTERS[lc] && STRATEGY_STARTERS[lc][quadrant]) || [];
    },
    appendStarter(key, line) {
      const cur = (this.strategyQuadrant[key] || '').trim();
      const sep = cur ? '\n• ' : '• ';
      this.strategyQuadrant[key] = cur + sep + line;
      this.markDirty();
    },
    pickCase(k) {
      this.caseKey = k;
      this.markDirty();
      this.persist();
    },
    diffArrow(kind) {
      switch (kind) {
        case 'up': return '⬆';
        case 'down': return '⬇';
        case 'placed': return '＋';
        case 'removed': return '✕';
        default: return '↔';
      }
    },
    diffLabel(kind) {
      return this.$t('agileTraining.stakeholderMatrix.diff.' + kind);
    },
    allRolesPlaced(map) {
      return this.roleIds.length && this.roleIds.every((rid) => map[rid] && [0, 1, 2].includes(map[rid].infl) && [0, 1, 2].includes(map[rid].int));
    },
    ensureDiscussionShape() {
      this.roleIds.forEach((rid) => {
        if (!this.discussion[rid]) {
          this.discussion[rid] = { why_power: '', why_interest: '', if_ignore: '' };
        }
      });
    },
    syncDiscussionKeys() {
      this.placedRolesR1.forEach((rid) => {
        if (!this.discussion[rid]) {
          this.discussion = { ...this.discussion, [rid]: { why_power: '', why_interest: '', if_ignore: '' } };
        }
      });
    },
    onPlacementsR1(v) { this.placementsR1 = { ...v }; },
    onPlacementsR2(v) { this.placementsR2 = { ...v }; },
    goScreen(name) {
      if (!this.screenOrder.includes(name)) return;
      if (name === 'discussion') {
        this.placedRolesR1.forEach((rid) => {
          if (!this.discussion[rid]) {
            this.discussion = { ...this.discussion, [rid]: { why_power: '', why_interest: '', if_ignore: '' } };
          }
        });
      }
      this.screen = name;
      this.persist();
    },
    prepRound2() {
      if (!this.placementsR2 || !Object.keys(this.placementsR2).length) {
        this.placementsR2 = JSON.parse(JSON.stringify(this.placementsR1));
      }
      this.goScreen('matrix_r2');
    },
    markDirty() {
      this.dirty = true;
      this.debouncedPersist();
    },
    debouncedPersist() {
      this.saveState = 'saving';
      if (this.saveTimer) clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(() => this.persist(), 450);
    },
    async persist() {
      this.saveLocal();
      if (!this.participantToken) {
        this.saveState = 'idle';
        return;
      }
      try {
        await axios.post(`/api/agile-training/stakeholder-matrix/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          screen: this.screen,
          placements_r1: this.placementsR1,
          placements_r2: this.placementsR2,
          discussion: this.discussion,
          strategy_quadrant: this.strategyQuadrant,
          event_key: this.eventKey,
          case_key: this.caseKey,
        });
        this.saveState = 'saved';
        this.dirty = false;
        setTimeout(() => { if (!this.dirty) this.saveState = 'idle'; }, 1200);
      } catch (e) {
        this.saveState = 'idle';
        console.error(e);
      }
    },
    async bootstrap() {
      this.initialLoading = true;
      this.loadError = '';
      try {
        const res = await axios.get(`/api/agile-training/stakeholder-matrix/g/${this.slug}/state`, {
          params: { locale: this.locale, participant_token: this.participantToken || undefined },
        });
        this.groupName = (res.data.group && res.data.group.name) || '';
        this.contentCopy = { ...this.contentCopy, ...(res.data.content || {}) };
        this.roleIds = res.data.content && res.data.content.role_ids ? res.data.content.role_ids : this.roleIds;
        this.eventKeys = res.data.content && res.data.content.event_keys ? res.data.content.event_keys : this.eventKeys;
        this.caseKeys = res.data.content && res.data.content.case_keys ? res.data.content.case_keys : this.caseKeys;
        if (res.data.answer) {
          const a = res.data.answer;
          this.applyState({
            screen: a.screen,
            placementsR1: a.placements_r1,
            placementsR2: a.placements_r2,
            discussion: a.discussion,
            strategyQuadrant: a.strategy_quadrant,
            eventKey: a.event_key,
            caseKey: a.case_key,
          }, true);
          this.aiRemaining = a.ai_calls_remaining != null ? a.ai_calls_remaining : 12;
        } else {
          this.aiRemaining = 12;
        }
        this.ensureDiscussionShape();
        this.syncDiscussionKeys();
      } catch (e) {
        this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.initialLoading = false;
      }
    },
    async joinGroup() {
      this.joining = true;
      this.joinError = '';
      try {
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, {
          display_name: (this.joinName || '').trim() || undefined,
        });
        this.participantToken = res.data.participant_token;
        this.participantName = (this.joinName || '').trim();
        this.writeToken(this.participantToken);
        this.ensureDiscussionShape();
        await this.bootstrap();
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.joining = false;
      }
    },
    async askAi(mode, userInput) {
      if (!this.participantToken || !userInput || !String(userInput).trim()) return;
      try {
        const res = await axios.post(`/api/agile-training/stakeholder-matrix/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken,
          mode,
          user_input: userInput,
          locale: this.locale,
        });
        this.aiRemaining = res.data.ai_calls_remaining != null ? res.data.ai_calls_remaining : this.aiRemaining;
        alert(res.data.reply || '');
      } catch (e) {
        const err = (e.response && e.response.data && e.response.data.error) || '';
        if (err === 'ai_limit_exceeded') {
          alert(this.$t('agileTraining.stakeholderMatrix.aiLimit'));
        }
      }
    },
    async printReport() {
      const wasHidden = !this.showSummary;
      if (wasHidden) {
        this.showSummary = true;
        await this.$nextTick();
        await new Promise((r) => setTimeout(r, 60));
      }
      try { window.print(); } catch (_) { /* noop */ }
    },
    downloadJson() {
      const data = {
        group: this.groupName,
        slug: this.slug,
        case_key: this.caseKey,
        placements_r1: this.placementsR1,
        placements_r2: this.placementsR2,
        discussion: this.discussion,
        strategy_quadrant: this.strategyQuadrant,
        event_key: this.eventKey,
        consequences_r1: this.consequenceListR1,
        consequences_r2: this.consequenceListR2,
        round_diff: this.roundDiff,
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = `stakeholder-matrix-${this.slug}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    },
  },
};
</script>

<style scoped>
.sh-play { max-width: 1080px; margin: 0 auto; padding: 16px 16px 48px; font-family: var(--vl-font, inherit); }
.sh-play--load { text-align: center; padding: 40px; }
.sh-play__lang { display: flex; gap: 6px; margin-bottom: 12px; }
.sh-play__lang button {
  border: 1px solid rgba(15, 23, 42, 0.2);
  background: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  font-weight: 600;
  cursor: pointer;
}
.sh-play__lang button.active { background: #1d4ed8; color: #fff; border-color: #1d4ed8; }
.sh-play__head { margin-bottom: 16px; }
.sh-play__title { font-size: 1.4rem; margin: 0 0 4px; }
.sh-play__group { color: #64748b; margin: 0; }
.sh-play__case-tag { color: #1d4ed8; font-weight: 600; margin: 4px 0 0; display: inline-flex; gap: 6px; align-items: center; background: rgba(29,78,216,0.08); padding: 4px 10px; border-radius: 999px; }
.sh-card { background: #fff; border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 12px; padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }
.sh-card--wide { }
.sh-lead { line-height: 1.55; color: #334155; }
.sh-goal { font-weight: 600; color: #0f172a; }
.sh-hint { font-size: 13px; color: #64748b; margin: 0 0 8px; }
.sh-hint--ok { color: #15803d; }
.sh-label { display: block; font-size: 13px; font-weight: 600; margin: 10px 0 4px; color: #475569; }
.sh-input, .sh-ta { width: 100%; border-radius: 10px; border: 1px solid rgba(15, 23, 42, 0.15); padding: 8px 10px; font: inherit; box-sizing: border-box; }
.sh-btn { display: inline-flex; align-items: center; justify-content: center; padding: 8px 16px; border-radius: 10px; border: 1px solid rgba(15, 23, 42, 0.15); background: #fff; font-weight: 600; cursor: pointer; }
.sh-btn--primary { background: #1d4ed8; color: #fff; border-color: #1d4ed8; }
.sh-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sh-err { color: #b91c1c; }
.sh-steps { display: flex; flex-wrap: wrap; gap: 4px; margin-bottom: 10px; }
.sh-steps__item { min-width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; border-radius: 6px; background: #e2e8f0; font-size: 11px; font-weight: 700; color: #475569; }
.sh-steps__item--on { background: #1d4ed8; color: #fff; }
.sh-steps__item--done { background: #cbd5e1; }
.sh-nav { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 16px; }
.sh-note { color: #64748b; font-size: 13px; margin-top: 8px; }

/* case picker */
.sh-cases { display: grid; gap: 12px; margin-top: 12px; grid-template-columns: 1fr; }
@media (min-width: 760px) { .sh-cases { grid-template-columns: 1fr 1fr 1fr; } }
.sh-case { background: #f8fafc; border: 1px solid rgba(15,23,42,0.1); border-radius: 14px; padding: 14px; cursor: pointer; transition: transform .12s ease, box-shadow .12s ease, border-color .12s ease, background .12s ease; outline: none; }
.sh-case:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(15,23,42,0.08); }
.sh-case:focus-visible { box-shadow: 0 0 0 3px rgba(29,78,216,0.35); }
.sh-case--on { border-color: #1d4ed8; background: rgba(29,78,216,0.06); box-shadow: 0 8px 24px rgba(29,78,216,0.18); }
.sh-case__head { display: flex; gap: 10px; align-items: center; margin-bottom: 4px; }
.sh-case__emoji { font-size: 26px; }
.sh-case__title { margin: 0; font-size: 16px; }
.sh-case__lead { color: #334155; line-height: 1.5; margin: 6px 0; font-size: 14px; }
.sh-case__goal { color: #0f172a; font-weight: 600; font-size: 13px; margin: 6px 0; }
.sh-case__flavor { color: #475569; font-size: 12.5px; line-height: 1.5; }
.sh-case__cta { margin-top: 10px; font-weight: 700; font-size: 13px; color: #1d4ed8; display: inline-flex; align-items: center; gap: 6px; }
.sh-case__check { background: #1d4ed8; color: #fff; width: 22px; height: 22px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }

/* personas */
.sh-personas { display: grid; gap: 10px; margin-top: 12px; grid-template-columns: 1fr; }
@media (min-width: 700px) { .sh-personas { grid-template-columns: 1fr 1fr; } }
@media (min-width: 1000px) { .sh-personas { grid-template-columns: 1fr 1fr 1fr; } }
.sh-persona { border: 1px solid rgba(15,23,42,0.1); border-radius: 12px; padding: 12px; background: #fff; }
.sh-persona__head { display: flex; gap: 10px; align-items: center; }
.sh-persona__emoji { font-size: 28px; }
.sh-persona__name { margin: 0; font-weight: 700; }
.sh-persona__role { margin: 0; font-size: 12px; color: #64748b; }
.sh-persona__label { color: #1d4ed8; font-weight: 700; margin-right: 4px; }
.sh-persona__motivation { font-size: 13.5px; line-height: 1.5; color: #334155; margin: 8px 0 4px; }
.sh-persona__quote { font-style: italic; font-size: 13px; color: #475569; border-left: 3px solid #1d4ed8; padding: 4px 8px; background: rgba(29,78,216,0.04); margin: 0; }

.sh-discuss-block { border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 10px; }
.sh-discuss-h { font-size: 15px; margin: 0 0 4px; display: flex; gap: 8px; align-items: center; }
.sh-discuss-h small { font-weight: 400; color: #64748b; font-size: 12px; }
.sh-discuss-emoji { font-size: 20px; }
.sh-subh { font-size: 15px; margin: 16px 0 6px; }
.sh-bullets { margin: 0; padding-left: 20px; line-height: 1.5; }
.sh-bullets--pos { color: #14532d; }

/* strategy starters */
.sh-strat-row { margin: 14px 0; }
.sh-starter-h { margin: 6px 0 4px; font-size: 11.5px; color: #64748b; text-transform: uppercase; font-weight: 700; letter-spacing: .04em; }
.sh-starters { display: flex; flex-wrap: wrap; gap: 6px; }
.sh-starter { background: rgba(29,78,216,0.06); border: 1px dashed rgba(29,78,216,0.4); border-radius: 999px; padding: 4px 10px; font-size: 12.5px; color: #1d4ed8; cursor: pointer; font: inherit; }
.sh-starter:hover { background: rgba(29,78,216,0.12); }

/* reactions */
.sh-reactions { display: grid; gap: 10px; grid-template-columns: 1fr; margin-top: 8px; }
@media (min-width: 700px) { .sh-reactions { grid-template-columns: 1fr 1fr; } }
.sh-reaction { border: 1px solid rgba(15,23,42,0.1); border-radius: 12px; padding: 10px; background: #fff; }
.sh-reaction--close { background: #eef2ff; border-color: #c7d2fe; }
.sh-reaction--satisfied { background: #f1f5f9; }
.sh-reaction--informed { background: #fff; }
.sh-reaction--minimal { background: #fefce8; border-color: #fde68a; }
.sh-reaction__head { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.sh-reaction__emoji { font-size: 22px; }
.sh-reaction__name { margin: 0; font-weight: 700; font-size: 14px; }
.sh-reaction__role { margin: 0; font-size: 11.5px; color: #64748b; }
.sh-reaction__quote { margin: 0; line-height: 1.5; font-size: 13.5px; color: #1f2937; }

/* events */
.sh-event-grid { display: grid; gap: 10px; grid-template-columns: 1fr; margin-top: 8px; }
@media (min-width: 760px) { .sh-event-grid { grid-template-columns: 1fr 1fr; } }
.sh-event-card { background: #fff; border: 1px solid rgba(15,23,42,0.1); border-radius: 12px; padding: 12px; cursor: pointer; outline: none; transition: border-color .1s ease, background .1s ease, box-shadow .1s ease, transform .1s ease; }
.sh-event-card:hover { transform: translateY(-1px); box-shadow: 0 8px 20px rgba(15,23,42,0.08); }
.sh-event-card:focus-visible { box-shadow: 0 0 0 3px rgba(29,78,216,0.35); }
.sh-event-card--on { border-color: #1d4ed8; background: rgba(29,78,216,0.06); box-shadow: 0 8px 24px rgba(29,78,216,0.18); }
.sh-event-card__head { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; }
.sh-event-card__emoji { font-size: 22px; }
.sh-event-card__title { margin: 0; font-size: 15px; }
.sh-event-card__lead { color: #334155; line-height: 1.45; font-size: 13.5px; margin: 2px 0 6px; }
.sh-event-card__impact-h { font-size: 11px; color: #64748b; margin: 6px 0 4px; text-transform: uppercase; letter-spacing: .04em; font-weight: 700; }
.sh-event-card__impact { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.sh-event-card__impact li { display: flex; gap: 6px; align-items: baseline; font-size: 12.5px; color: #1f2937; line-height: 1.4; }
.sh-event-card__impact-emoji { font-size: 14px; }
.sh-event-card__impact-name { font-weight: 700; }
.sh-event-card__impact-note { color: #475569; }

.sh-event-recap { display: flex; gap: 8px; align-items: flex-start; padding: 10px 12px; border-radius: 10px; background: rgba(29,78,216,0.06); border: 1px solid rgba(29,78,216,0.2); margin-bottom: 12px; flex-wrap: wrap; line-height: 1.45; font-size: 13.5px; color: #1f2937; }

.sh-two-col { display: grid; gap: 16px; }
@media (min-width: 700px) { .sh-two-col { grid-template-columns: 1fr 1fr; } }
.sh-actions { margin-top: 12px; }

/* diff */
.sh-diff { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-direction: column; gap: 6px; }
.sh-diff__item { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; padding: 6px 10px; border-radius: 10px; background: #f8fafc; border: 1px solid rgba(15,23,42,0.08); font-size: 13.5px; }
.sh-diff__item--up { background: #ecfdf5; border-color: #bbf7d0; }
.sh-diff__item--down { background: #fef2f2; border-color: #fecaca; }
.sh-diff__item--placed { background: #eef2ff; border-color: #c7d2fe; }
.sh-diff__item--removed { background: #f5f5f4; border-color: #e7e5e4; }
.sh-diff__emoji { font-size: 20px; }
.sh-diff__role { color: #64748b; font-size: 12.5px; }
.sh-diff__arrow { font-size: 16px; color: #1d4ed8; font-weight: 700; }
.sh-diff__kind { color: #1f2937; }

.sh-actions { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 12px; align-items: center; }
.sh-actions--final { padding: 12px; background: #f0f9ff; border: 1px solid rgba(29,78,216,0.18); border-radius: 12px; }
.sh-btn--print { font-size: 14px; }
.sh-btn--ghost { background: transparent; border: none; color: #1d4ed8; text-decoration: underline; padding: 6px 8px; }
.sh-btn--ghost:hover { color: #1e40af; }

.sh-report-print-only { display: none; }
</style>

<style>
@media print {
  @page { margin: 14mm; }
  html, body { background: #fff !important; }
  body * { visibility: hidden !important; }
  .sh-report-print-only,
  .sh-report-print-only *,
  #sh-report,
  #sh-report * {
    visibility: visible !important;
  }
  .sh-report-print-only {
    display: block !important;
    position: absolute !important;
    left: 0; top: 0;
    width: 100%;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    box-shadow: none !important;
  }
  #sh-report {
    position: absolute !important;
    left: 0; top: 0;
    width: 100%;
    margin: 0 !important;
    border: none !important;
    box-shadow: none !important;
  }
  .sh-play, .sh-card, .sh-flow { box-shadow: none !important; border: none !important; padding: 0 !important; background: #fff !important; }
}
</style>
