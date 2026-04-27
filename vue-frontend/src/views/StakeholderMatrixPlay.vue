<template>
  <div class="sh-play modern-ui" v-if="!loadError && !initialLoading">
    <div class="sh-play__lang" role="group" :aria-label="$t('agileTraining.common.language')">
      <button type="button" :class="{ active: locale === 'ru' }" @click="switchLang('ru')">RU</button>
      <button type="button" :class="{ active: locale === 'en' }" @click="switchLang('en')">EN</button>
    </div>

    <header class="sh-play__head">
      <h1 class="sh-play__title">{{ $t('agileTraining.stakeholderMatrix.playTitle') }}</h1>
      <p class="sh-play__group" v-if="groupName">· {{ groupName }}</p>
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

      <!-- 1 context -->
      <section v-if="screen === 'context'" class="sh-card">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.context.h2') }}</h2>
        <p class="sh-lead">{{ contentCopy.scenario_lead }}</p>
        <p class="sh-goal">👉 {{ contentCopy.goal }}</p>
        <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('roles')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
      </section>

      <!-- 2 roles bank -->
      <section v-else-if="screen === 'roles'" class="sh-card">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.roles.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.roles.lead') }}</p>
        <div class="sh-role-bank">
          <div v-for="rid in roleIds" :key="rid" class="sh-role-tile">
            <span class="sh-role-tile__emoji">{{ roleEmoji(rid) }}</span>
            <span class="sh-role-tile__label">{{ $t('agileTraining.stakeholderMatrix.roles.' + rid) }}</span>
          </div>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('context')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" @click="goScreen('matrix_r1')">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
      </section>

      <!-- 3 matrix r1 -->
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
          @update:placements="onPlacementsR1"
        />
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('roles')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!allRolesPlaced(placementsR1)" @click="goScreen('discussion')">
            {{ $t('agileTraining.stakeholderMatrix.next') }} →
          </button>
        </div>
        <p v-if="!allRolesPlaced(placementsR1)" class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.needAll') }}</p>
      </section>

      <!-- 4 discussion -->
      <section v-else-if="screen === 'discussion'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.discussion.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.discussion.lead') }}</p>
        <div v-for="rid in placedRolesR1" :key="rid" class="sh-discuss-block">
          <h3 class="sh-discuss-h">{{ roleLabel(rid) }}</h3>
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

      <!-- 5 strategy 2x2 text -->
      <section v-else-if="screen === 'strategy'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.strategy.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.strategy.lead') }}</p>
        <div v-for="key in ['hh', 'hl', 'lh', 'll']" :key="key" class="sh-strat-row">
          <label class="sh-label">{{ contentCopy.strategy_quadrant_hints[key] }}</label>
          <textarea v-model="strategyQuadrant[key]" class="sh-ta" rows="2" @input="markDirty" />
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

      <!-- 6 consequences -->
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

      <!-- 7 event -->
      <section v-else-if="screen === 'event'" class="sh-card">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.event.h2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.event.lead') }}</p>
        <div class="sh-event-grid">
          <button
            v-for="ek in eventKeys"
            :key="ek"
            type="button"
            class="sh-event-btn"
            :class="{ 'sh-event-btn--on': eventKey === ek }"
            @click="eventKey = ek; markDirty(); persist()"
          >
            <span class="sh-event-emoji">{{ eventEmoji(ek) }}</span>
            {{ contentCopy.event_labels[ek] }}
          </button>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('consequences')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!eventKey" @click="prepRound2">{{ $t('agileTraining.stakeholderMatrix.next') }} →</button>
        </div>
      </section>

      <!-- 8 matrix r2 -->
      <section v-else-if="screen === 'matrix_r2'" class="sh-card sh-card--wide">
        <h2>{{ $t('agileTraining.stakeholderMatrix.screens.matrix.h2R2') }}</h2>
        <p class="sh-lead">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.leadR2') }}</p>
        <MatrixGrid
          :round-key="'r2'"
          :locale="locale"
          :placements="placementsR2"
          :all-role-ids="roleIds"
          :content-copy="contentCopy"
          :level-labels-y="contentCopy.level_labels"
          :level-labels-x="contentCopy.level_labels_x"
          :role-label="roleLabel"
          @update:placements="onPlacementsR2"
        />
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('event')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
          <button type="button" class="sh-btn sh-btn--primary" :disabled="!allRolesPlaced(placementsR2)" @click="goScreen('final')">{{ $t('agileTraining.stakeholderMatrix.finish') }} →</button>
        </div>
      </section>

      <!-- 9 final -->
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
        <h3 class="sh-subh">{{ $t('agileTraining.stakeholderMatrix.screens.final.reflect') }}</h3>
        <p class="sh-note">{{ $t('agileTraining.stakeholderMatrix.screens.final.reflectLead') }}</p>
        <div class="sh-actions">
          <button type="button" class="sh-btn" @click="downloadJson">{{ $t('agileTraining.stakeholderMatrix.download') }}</button>
        </div>
        <div class="sh-nav">
          <button type="button" class="sh-btn" @click="goScreen('matrix_r2')">← {{ $t('agileTraining.stakeholderMatrix.back') }}</button>
        </div>
      </section>
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
import { computeConsequencesClient, computeStrengthsClient } from './stakeholderMatrix/logic.js';

const TOKEN_KEY = 'at_stakeholder_m_token_';
const LS_KEY = 'at_stakeholder_m_state_';

export default {
  name: 'StakeholderMatrixPlay',
  components: { MatrixGrid, AiBlock },
  props: { slug: { type: String, required: true } },
  data() {
    return {
      initialLoading: true,
      loadError: '',
      groupName: '',
      contentCopy: { axis: {}, level_labels: [], level_labels_x: [], cell_strategy: {}, event_labels: {}, strategy_quadrant_hints: {} },
      roleIds: [],
      eventKeys: [],
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
      aiRemaining: 12,
      saveState: 'idle',
      saveTimer: null,
      dirty: false,
    };
  },
  computed: {
    screenOrder() {
      return ['context', 'roles', 'matrix_r1', 'discussion', 'strategy', 'consequences', 'event', 'matrix_r2', 'final'];
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
    },
    roleLabel(rid) {
      return this.$t('agileTraining.stakeholderMatrix.roles.' + rid);
    },
    roleEmoji() {
      return '👤';
    },
    eventEmoji(ek) {
      const m = { delays: '⏱️', resistance: '⚡', budget_up: '💰', tech_issues: '🔧' };
      return m[ek] || '▫️';
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
    onPlacementsR1(v) {
      this.placementsR1 = { ...v };
    },
    onPlacementsR2(v) {
      this.placementsR2 = { ...v };
    },
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
        if (res.data.answer) {
          const a = res.data.answer;
          this.applyState({
            screen: a.screen,
            placementsR1: a.placements_r1,
            placementsR2: a.placements_r2,
            discussion: a.discussion,
            strategyQuadrant: a.strategy_quadrant,
            eventKey: a.event_key,
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
    downloadJson() {
      const data = {
        group: this.groupName,
        slug: this.slug,
        placements_r1: this.placementsR1,
        placements_r2: this.placementsR2,
        discussion: this.discussion,
        strategy_quadrant: this.strategyQuadrant,
        event_key: this.eventKey,
        consequences_r1: this.consequenceListR1,
        consequences_r2: this.consequenceListR2,
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
.sh-play { max-width: 1020px; margin: 0 auto; padding: 16px 16px 48px; font-family: var(--vl-font, inherit); }
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
.sh-card { background: #fff; border: 1px solid rgba(15, 23, 42, 0.08); border-radius: 12px; padding: 18px; box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06); }
.sh-card--wide { }
.sh-lead { line-height: 1.5; color: #334155; }
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
.sh-role-bank { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 8px; margin-top: 10px; }
.sh-role-tile { border: 1px solid rgba(15, 23, 42, 0.1); border-radius: 10px; padding: 8px 10px; display: flex; gap: 6px; align-items: center; background: #f8fafc; }
.sh-role-tile__label { font-size: 13px; font-weight: 600; }
.sh-discuss-block { border-top: 1px solid #e2e8f0; padding-top: 12px; margin-top: 10px; }
.sh-discuss-h { font-size: 15px; margin: 0 0 4px; }
.sh-subh { font-size: 15px; margin: 16px 0 6px; }
.sh-bullets { margin: 0; padding-left: 20px; line-height: 1.5; }
.sh-bullets--pos { color: #14532d; }
.sh-event-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
@media (min-width: 600px) { .sh-event-grid { grid-template-columns: 1fr 1fr; } }
.sh-event-btn { text-align: left; padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(15, 23, 42, 0.12); background: #fff; cursor: pointer; font: inherit; line-height: 1.4; }
.sh-event-btn--on { border-color: #1d4ed8; background: rgba(29, 78, 216, 0.08); }
.sh-event-emoji { margin-right: 6px; }
.sh-two-col { display: grid; gap: 16px; }
@media (min-width: 700px) { .sh-two-col { grid-template-columns: 1fr 1fr; } }
.sh-actions { margin-top: 12px; }
</style>
