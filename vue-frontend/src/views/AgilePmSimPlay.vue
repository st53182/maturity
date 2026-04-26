<template>
  <div class="pmsim" :class="{ 'pmsim--dead': isDead, 'pmsim--at-risk': isAtRisk }">
    <header class="pmsim__top">
      <div class="pmsim__brand">
        <span class="pmsim__logo">📡</span>
        <div>
          <div class="pmsim__title">{{ $t('agileTraining.pmSim.title') }}</div>
          <div class="pmsim__sub">
            <strong>{{ group.name || '…' }}</strong>
            <span class="pmsim__dot">•</span>
            <span>{{ $t('agileTraining.pmSim.weekOf', { w: state.current_week, total: state.total_weeks }) }}</span>
            <span class="pmsim__dot">•</span>
            <span :class="['pmsim__status', `pmsim__status--${state.status}`]">{{ statusLabel }}</span>
          </div>
        </div>
      </div>
      <div class="pmsim__lang">
        <button :class="{ act: locale==='ru' }" @click="switchLang('ru')">RU</button>
        <button :class="{ act: locale==='en' }" @click="switchLang('en')">EN</button>
      </div>
    </header>

    <!-- LOBBY: name + role -->
    <section v-if="!participantToken" class="pmsim__panel">
      <h2>{{ $t('agileTraining.pmSim.welcomeTitle') }}</h2>
      <p class="pmsim__lead">{{ $t('agileTraining.pmSim.welcomeIntro') }}</p>
      <div class="pmsim__form">
        <input v-model="displayName" :placeholder="$t('agileTraining.pmSim.yourName')" maxlength="60" />
        <button class="pmsim__btn pmsim__btn--primary" :disabled="!displayName.trim() || joining" @click="joinGroup">
          {{ $t('agileTraining.pmSim.join') }}
        </button>
      </div>
      <div class="pmsim__error" v-if="joinError">{{ joinError }}</div>
    </section>

    <section v-else-if="state.phase === 'lobby' || state.phase === 'intro'" class="pmsim__panel">
      <h2>{{ $t('agileTraining.pmSim.lobbyTitle') }}</h2>
      <p class="pmsim__lead">{{ $t('agileTraining.pmSim.welcomeIntro') }}</p>

      <h3>{{ $t('agileTraining.pmSim.pickRole') }}</h3>
      <div class="pmsim__roles">
        <button
          v-for="r in roleList"
          :key="r.key"
          :class="['pmsim__role', { 'pmsim__role--active': myRole === r.key, 'pmsim__role--taken': roleTaken(r.key) && myRole !== r.key }]"
          @click="changeRole(r.key)">
          <span class="pmsim__role-icon">{{ r.icon }}</span>
          <strong>{{ r.label }}</strong>
          <span class="pmsim__role-desc">{{ r.desc }}</span>
        </button>
      </div>

      <div class="pmsim__participants">
        <div class="pmsim__pcount">{{ $t('agileTraining.pmSim.team') }}: {{ participantsList.length }}</div>
        <ul>
          <li v-for="p in participantsList" :key="p.token">
            <span>{{ p.name }}</span>
            <span class="pmsim__pill" v-if="p.role">{{ roleLabelByKey(p.role) }}</span>
            <span v-else class="pmsim__pill pmsim__pill--ghost">—</span>
          </li>
        </ul>
      </div>

      <div class="pmsim__cta">
        <button v-if="isPO" class="pmsim__btn pmsim__btn--primary" @click="startGame">
          {{ $t('agileTraining.pmSim.startGame') }}
        </button>
        <span v-else class="pmsim__hint">{{ $t('agileTraining.pmSim.waitForPO') }}</span>
      </div>
    </section>

    <!-- PLAYING -->
    <template v-else-if="state.phase === 'playing'">
      <!-- Dashboard -->
      <section class="pmsim__dashboard">
        <div class="pmsim__metric pmsim__metric--money">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.revenue') }}</div>
          <div class="pmsim__m-value">${{ formatNumber(state.revenue_total) }}</div>
          <div class="pmsim__m-sub" v-if="state.revenue_per_week">+${{ formatNumber(state.revenue_per_week) }}/w</div>
        </div>
        <div class="pmsim__metric">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.users') }}</div>
          <div class="pmsim__m-value">{{ formatNumber(state.metrics.users) }}</div>
          <div class="pmsim__m-sub">{{ $t('agileTraining.pmSim.metric.active') }}: {{ formatNumber(state.metrics.active_users) }}</div>
        </div>
        <div class="pmsim__metric"
             :class="metricClass('satisfaction', state.metrics.satisfaction)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.satisfaction') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.satisfaction) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.satisfaction}%`"></span></div>
        </div>
        <div class="pmsim__metric" :class="metricClass('stability', state.metrics.stability)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.stability') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.stability) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.stability}%`"></span></div>
        </div>
        <div class="pmsim__metric" :class="metricClass('trust', state.metrics.trust)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.trust') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.trust) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.trust}%`"></span></div>
        </div>
        <div class="pmsim__metric pmsim__metric--debt" :class="metricClass('tech_debt', state.metrics.tech_debt, true)">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.techDebt') }}</div>
          <div class="pmsim__m-value">{{ Math.round(state.metrics.tech_debt) }}</div>
          <div class="pmsim__m-bar"><span :style="`width:${state.metrics.tech_debt}%`"></span></div>
        </div>
        <div class="pmsim__metric">
          <div class="pmsim__m-label">{{ $t('agileTraining.pmSim.metric.budget') }}</div>
          <div class="pmsim__m-value">${{ formatNumber(state.budget) }}</div>
          <div class="pmsim__m-sub">{{ $t('agileTraining.pmSim.metric.capacity') }}: {{ state.capacity_left }}/{{ 100 }}</div>
        </div>
      </section>

      <section class="pmsim__charts">
        <h3>{{ $t('agileTraining.pmSim.metricsHistory') }}</h3>
        <div class="pmsim__chart-wrap">
          <Chart :data="state.metrics_history" field="users" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.users')" color="#2563eb" />
          <Chart :data="state.metrics_history" field="revenue_total" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.revenue')" color="#059669" />
          <Chart :data="state.metrics_history" field="satisfaction" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.satisfaction')" color="#7c3aed" :max="100" />
          <Chart :data="state.metrics_history" field="stability" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.stability')" color="#0ea5e9" :max="100" />
          <Chart :data="state.metrics_history" field="trust" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.trust')" color="#f59e0b" :max="100" />
          <Chart :data="state.metrics_history" field="tech_debt" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.techDebt')" color="#dc2626" :max="100" />
        </div>
      </section>

      <!-- Risks -->
      <section class="pmsim__risks" v-if="riskBadges.length">
        <span v-for="r in riskBadges" :key="r" class="pmsim__risk">⚠ {{ r }}</span>
      </section>

      <!-- Event card -->
      <section v-if="state.current_event && !state.event_resolved" class="pmsim__event">
        <header>
          <span class="pmsim__event-type">{{ eventTypeLabel(state.current_event.type) }}</span>
          <h2>{{ state.current_event.title }}</h2>
        </header>
        <p class="pmsim__event-desc">{{ state.current_event.description }}</p>

        <div class="pmsim__options">
          <article
            v-for="opt in state.current_event.options"
            :key="opt.id"
            :class="['pmsim__option', { 'pmsim__option--mine': myEventVote === opt.id, 'pmsim__option--leading': leadingEventOption === opt.id && eventVotesTotal > 0 }]">
            <div class="pmsim__option-head">
              <strong>{{ opt.title }}</strong>
              <span class="pmsim__votes">{{ (state.votes.event && state.votes.event[opt.id]) || 0 }}</span>
            </div>
            <p>{{ opt.description }}</p>
            <button class="pmsim__btn pmsim__btn--ghost" @click="voteEvent(opt.id)">
              {{ myEventVote === opt.id ? $t('agileTraining.pmSim.voted') : $t('agileTraining.pmSim.vote') }}
            </button>
          </article>
        </div>

        <div class="pmsim__decision-bar">
          <span>{{ $t('agileTraining.pmSim.poDecision') }}</span>
          <select v-model="poDecision" :disabled="!isPO">
            <option value="">— {{ $t('agileTraining.pmSim.pickOption') }} —</option>
            <option v-for="opt in state.current_event.options" :key="opt.id" :value="opt.id">{{ opt.title }}</option>
          </select>
          <button class="pmsim__btn pmsim__btn--primary" :disabled="!isPO || !poDecision || submitting" @click="confirmEventDecision">
            {{ $t('agileTraining.pmSim.confirmDecision') }}
          </button>
        </div>
        <div v-if="!isPO" class="pmsim__hint">{{ $t('agileTraining.pmSim.poConfirmsHint') }}</div>
      </section>

      <!-- Feature window -->
      <section v-if="state.feature_choice_open" class="pmsim__features">
        <h2>{{ $t('agileTraining.pmSim.featureCycleTitle', { c: state.cycle_index }) }}</h2>
        <p class="pmsim__hint">{{ $t('agileTraining.pmSim.featureRules') }}</p>
        <p class="pmsim__capacity-line">
          {{ $t('agileTraining.pmSim.metric.capacity') }}: <strong>{{ state.capacity_left }}</strong>
          <span v-if="featureCapacityUsed > 0"> · {{ $t('agileTraining.pmSim.using') }}: {{ featureCapacityUsed }}</span>
        </p>
        <div class="pmsim__feature-grid">
          <article
            v-for="f in state.feature_options"
            :key="f.key"
            :class="['pmsim__feature', { 'pmsim__feature--picked': featurePicks.includes(f.key) }]"
            @click="toggleFeaturePick(f)">
            <header>
              <strong>{{ f.title }}</strong>
              <span class="pmsim__feat-cap">{{ f.capacity }} cap</span>
            </header>
            <p>{{ f.description }}</p>
            <ul class="pmsim__feat-effects">
              <li v-for="(v,k) in f.effects" :key="k">
                <span class="pmsim__fe-key">{{ effectLabel(k) }}</span>
                <span class="pmsim__fe-value" :class="effectClass(v)">{{ effectValue(v) }}</span>
              </li>
            </ul>
            <div class="pmsim__feat-pick" v-if="featurePicks.includes(f.key)">✓ {{ $t('agileTraining.pmSim.picked') }}</div>
            <div class="pmsim__votes-row">
              <span class="pmsim__pill">{{ $t('agileTraining.pmSim.votes') }}: {{ (state.votes.feature && state.votes.feature[f.key]) || 0 }}</span>
              <button class="pmsim__btn pmsim__btn--ghost" @click.stop="voteFeature(f.key)">
                {{ myFeatureVote === f.key ? $t('agileTraining.pmSim.voted') : $t('agileTraining.pmSim.vote') }}
              </button>
            </div>
          </article>
        </div>
        <div class="pmsim__decision-bar">
          <button class="pmsim__btn pmsim__btn--primary"
                  :disabled="!isPO || !canConfirmFeatures || submitting"
                  @click="confirmFeatureRelease">
            {{ $t('agileTraining.pmSim.releaseFeatures') }}
          </button>
          <button class="pmsim__btn pmsim__btn--ghost" :disabled="!isPO" @click="confirmFeatureRelease(true)">
            {{ $t('agileTraining.pmSim.skipFeatures') }}
          </button>
        </div>
      </section>

      <!-- Released features -->
      <section v-if="(state.feature_releases || []).length" class="pmsim__released">
        <h3>{{ $t('agileTraining.pmSim.released') }}</h3>
        <div class="pmsim__released-list">
          <span v-for="r in state.feature_releases" :key="r.key + r.week" class="pmsim__released-pill">
            <strong>w{{ r.week }}:</strong> {{ r.title }}
          </span>
        </div>
      </section>

      <!-- Last consequences -->
      <section v-if="state.consequences_text" class="pmsim__consequences">
        <strong>{{ $t('agileTraining.pmSim.lastConsequences') }}:</strong> {{ state.consequences_text }}
      </section>

      <!-- AI helper -->
      <section class="pmsim__ai">
        <h3>{{ $t('agileTraining.pmSim.aiCoach') }}</h3>
        <textarea v-model="aiInput" rows="2" :placeholder="$t('agileTraining.pmSim.aiHint')"></textarea>
        <div class="pmsim__ai-row">
          <button class="pmsim__btn pmsim__btn--ghost" :disabled="aiBusy || aiCallsLeft<=0" @click="askAi('tradeoff')">{{ $t('agileTraining.pmSim.aiTradeoff') }}</button>
          <button class="pmsim__btn pmsim__btn--ghost" :disabled="aiBusy || aiCallsLeft<=0" @click="askAi('userVoice')">{{ $t('agileTraining.pmSim.aiUserVoice') }}</button>
          <button class="pmsim__btn pmsim__btn--ghost" :disabled="aiBusy || aiCallsLeft<=0" @click="askAi('explain')">{{ $t('agileTraining.pmSim.aiExplain') }}</button>
          <span class="pmsim__ai-counter">{{ aiCallsLeft }}/{{ state.my && state.my.ai_calls_limit }}</span>
        </div>
        <pre class="pmsim__ai-reply" v-if="aiReply">{{ aiReply }}</pre>
      </section>

      <!-- History -->
      <section class="pmsim__history" v-if="(state.history || []).length">
        <h3>{{ $t('agileTraining.pmSim.history') }}</h3>
        <ol>
          <li v-for="(h,i) in [...state.history].reverse()" :key="i">
            <strong>w{{ h.week }}</strong>
            <template v-if="h.kind === 'event'">
              · {{ h.event.title }} → <em>{{ h.option.title }}</em>
              <span class="pmsim__history-effects" v-if="h.consequences && h.consequences.length">— {{ h.consequences.join(', ') }}</span>
            </template>
            <template v-else-if="h.kind === 'feature'">
              · 🚀 {{ (h.released || []).map(r => r.title).join(', ') || $t('agileTraining.pmSim.skipped') }}
            </template>
          </li>
        </ol>
      </section>

      <!-- Leaderboard hint -->
      <section v-if="state.leaderboard_unlocked_weeks && state.leaderboard_unlocked_weeks.length" class="pmsim__leader-hint">
        <strong>{{ $t('agileTraining.pmSim.leaderboardOpened') }}:</strong>
        {{ state.leaderboard_unlocked_weeks.map(w => 'w'+w).join(', ') }}
      </section>
    </template>

    <!-- FINISHED -->
    <section v-else-if="state.phase === 'finished'" class="pmsim__final" id="pmsim-final">
      <h2>{{ isDead ? $t('agileTraining.pmSim.gameOver') : $t('agileTraining.pmSim.finalTitle') }}</h2>
      <div class="pmsim__final-summary">
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.metric.revenue') }}</div>
          <div class="pmsim__final-value">${{ formatNumber(state.revenue_total) }}</div>
        </div>
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.metric.users') }}</div>
          <div class="pmsim__final-value">{{ formatNumber(state.metrics.users) }}</div>
        </div>
        <div class="pmsim__final-card">
          <div class="pmsim__final-label">{{ $t('agileTraining.pmSim.status') }}</div>
          <div :class="['pmsim__final-value', `pmsim__status--${state.status}`]">{{ statusLabel }}</div>
          <div class="pmsim__hint" v-if="state.death_reason">{{ state.death_reason }}</div>
        </div>
      </div>

      <div class="pmsim__chart-wrap">
        <Chart :data="state.metrics_history" field="revenue_total" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.revenue')" color="#059669" />
        <Chart :data="state.metrics_history" field="users" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.users')" color="#2563eb" />
        <Chart :data="state.metrics_history" field="satisfaction" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.satisfaction')" color="#7c3aed" :max="100" />
        <Chart :data="state.metrics_history" field="trust" :total-weeks="state.total_weeks" :label="$t('agileTraining.pmSim.metric.trust')" color="#f59e0b" :max="100" />
      </div>

      <div class="pmsim__final-events">
        <h3>{{ $t('agileTraining.pmSim.allDecisions') }}</h3>
        <ol>
          <li v-for="(h,i) in state.history" :key="i">
            <strong>w{{ h.week }}</strong>
            <template v-if="h.kind === 'event'"> · {{ h.event.title }} → <em>{{ h.option.title }}</em></template>
            <template v-else-if="h.kind === 'feature'"> · 🚀 {{ (h.released || []).map(r => r.title).join(', ') || $t('agileTraining.pmSim.skipped') }}</template>
          </li>
        </ol>
      </div>

      <div class="pmsim__cta">
        <button class="pmsim__btn pmsim__btn--primary" @click="printReport">🖨 {{ $t('agileTraining.pmSim.exportPdf') }}</button>
      </div>
    </section>

    <div v-if="loading" class="pmsim__loading">{{ $t('agileTraining.pmSim.loading') }}</div>
    <div v-if="loadError" class="pmsim__error">{{ loadError }}</div>
  </div>
</template>

<script>
import axios from 'axios';
import Chart from '@/components/PmSimChart.vue';

const TOKEN_KEY_PREFIX = 'pmsim:token:';
const NAME_KEY_PREFIX = 'pmsim:name:';
const POLL_INTERVAL_MS = 4000;

function read(prefix, slug) {
  try { return localStorage.getItem(prefix + slug) || ''; } catch (_) { return ''; }
}
function write(prefix, slug, val) {
  try { localStorage.setItem(prefix + slug, val || ''); } catch (_) { /* noop */ }
}

export default {
  name: 'AgilePmSimPlay',
  components: { Chart },
  props: { slug: { type: String, required: true } },
  data() {
    return {
      group: {}, sessionInfo: {},
      state: {
        phase: 'lobby', current_week: 0, total_weeks: 20, cycle_index: 1, status: 'alive',
        metrics: { users: 0, active_users: 0, satisfaction: 0, stability: 0, tech_debt: 0, trust: 0 },
        revenue_total: 0, revenue_per_week: 0, budget: 0, capacity_left: 0,
        feature_choice_open: false, feature_options: [], feature_releases: [],
        history: [], metrics_history: [], votes: { event: {}, feature: {} },
        my_vote: { event: null, feature: null },
        leaderboard_unlocked_weeks: [], current_event: null, event_resolved: true,
        my: null,
      },
      lastVersion: -1,
      participantToken: '',
      displayName: '',
      joining: false, joinError: '',
      loading: true, loadError: '',
      submitting: false,
      poDecision: '',
      featurePicks: [],
      aiInput: '', aiReply: '', aiBusy: false,
      pollTimer: null,
      locale: this.$i18n.locale,
    };
  },
  computed: {
    isPO() { return !!(this.state.my && this.state.my.is_po); },
    myRole() { return (this.state.my && this.state.my.role) || ''; },
    myEventVote() { return this.state.my_vote && this.state.my_vote.event; },
    myFeatureVote() { return this.state.my_vote && this.state.my_vote.feature; },
    isDead() { return this.state.status === 'dead'; },
    isAtRisk() { return this.state.status === 'at_risk'; },
    statusLabel() {
      const k = this.state.status || 'alive';
      return this.$t(`agileTraining.pmSim.statusLabel.${k}`);
    },
    eventVotesTotal() {
      const v = this.state.votes && this.state.votes.event || {};
      return Object.values(v).reduce((a, b) => a + (Number(b) || 0), 0);
    },
    leadingEventOption() {
      const v = this.state.votes && this.state.votes.event || {};
      let best = null, max = -1;
      Object.keys(v).forEach((k) => { if (v[k] > max) { max = v[k]; best = k; } });
      return best;
    },
    aiCallsLeft() {
      const my = this.state.my;
      if (!my) return 0;
      return Math.max(0, (my.ai_calls_limit || 0) - (my.ai_calls || 0));
    },
    roleList() {
      return [
        { key: 'po', icon: '👑', label: this.$t('agileTraining.pmSim.roleLabel.po'), desc: this.$t('agileTraining.pmSim.roleDesc.po') },
        { key: 'analyst', icon: '📊', label: this.$t('agileTraining.pmSim.roleLabel.analyst'), desc: this.$t('agileTraining.pmSim.roleDesc.analyst') },
        { key: 'tech', icon: '🛠', label: this.$t('agileTraining.pmSim.roleLabel.tech'), desc: this.$t('agileTraining.pmSim.roleDesc.tech') },
        { key: 'growth', icon: '🚀', label: this.$t('agileTraining.pmSim.roleLabel.growth'), desc: this.$t('agileTraining.pmSim.roleDesc.growth') },
        { key: 'advocate', icon: '💚', label: this.$t('agileTraining.pmSim.roleLabel.advocate'), desc: this.$t('agileTraining.pmSim.roleDesc.advocate') },
      ];
    },
    participantsList() {
      const map = this.state.participants || {};
      return Object.keys(map).map((tk) => ({ token: tk, name: map[tk].name || '…', role: map[tk].role }));
    },
    riskBadges() {
      const r = [];
      const m = this.state.metrics || {};
      if (m.users && m.users < 4000) r.push(this.$t('agileTraining.pmSim.risk.users'));
      if (m.satisfaction < 40) r.push(this.$t('agileTraining.pmSim.risk.satisfaction'));
      if (m.stability < 40) r.push(this.$t('agileTraining.pmSim.risk.stability'));
      if (m.trust < 40) r.push(this.$t('agileTraining.pmSim.risk.trust'));
      if (m.tech_debt > 80) r.push(this.$t('agileTraining.pmSim.risk.techDebt'));
      if (this.state.monetization_on && this.state.revenue_per_week === 0) r.push(this.$t('agileTraining.pmSim.risk.noRevenue'));
      return r;
    },
    featureCapacityUsed() {
      const map = {};
      (this.state.feature_options || []).forEach((f) => { map[f.key] = f.capacity; });
      return this.featurePicks.reduce((sum, k) => sum + (Number(map[k]) || 0), 0);
    },
    canConfirmFeatures() {
      if (!this.featurePicks.length) return false;
      if (this.featureCapacityUsed > this.state.capacity_left) return false;
      const big = this.featurePicks.filter((k) => {
        const f = (this.state.feature_options || []).find((x) => x.key === k);
        return f && (f.capacity || 0) >= 40;
      }).length;
      return big <= 1 && this.featurePicks.length <= 2;
    },
  },
  watch: {
    '$i18n.locale'(val) { if (val !== this.locale) { this.locale = val; this.loadState(true).catch(()=>{}); } },
    'state.feature_choice_open'(val) { if (!val) this.featurePicks = []; },
  },
  async mounted() {
    this.participantToken = read(TOKEN_KEY_PREFIX, this.slug);
    this.displayName = read(NAME_KEY_PREFIX, this.slug);
    try { await this.loadState(true); }
    catch (e) { this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error'; }
    finally { this.loading = false; }
    this.startPolling();
  },
  beforeUnmount() { this.stopPolling(); },
  methods: {
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* noop */ }
    },
    startPolling() {
      this.stopPolling();
      this.pollTimer = setInterval(() => this.loadState(false).catch(()=>{}), POLL_INTERVAL_MS);
    },
    stopPolling() { if (this.pollTimer) { clearInterval(this.pollTimer); this.pollTimer = null; } },
    formatNumber(n) {
      if (n === undefined || n === null) return '0';
      const k = Math.abs(n);
      if (k >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
      if (k >= 1_000) return (n / 1_000).toFixed(k >= 10_000 ? 0 : 1).replace('.0', '') + 'k';
      return String(Math.round(n));
    },
    metricClass(_key, value, inverted) {
      const v = Number(value) || 0;
      const bad = inverted ? v >= 80 : v <= 30;
      const warn = inverted ? v >= 60 : v <= 50;
      if (bad) return 'pmsim__metric--bad';
      if (warn) return 'pmsim__metric--warn';
      return 'pmsim__metric--ok';
    },
    eventTypeLabel(type) {
      return this.$t(`agileTraining.pmSim.eventType.${type || 'user'}`);
    },
    roleLabelByKey(k) { return this.$t(`agileTraining.pmSim.roleLabel.${k || 'analyst'}`); },
    roleTaken(k) {
      return Object.values(this.state.roles || {}).includes(k);
    },
    effectLabel(k) {
      const map = {
        users: 'users', users_pct: 'users %', active_users: 'active', active_users_pct: 'active %',
        satisfaction: 'sat', stability: 'stab', tech_debt: 'tech debt', trust: 'trust',
        churn_bump: 'churn', growth_pct: 'growth %', capacity_delta: 'capacity', budget_delta: 'budget',
        revenue_per_week: 'revenue/w', revenue_potential: 'revenue', monetization_on: 'monetize',
        ad_strength: 'ads', tech_debt_delta: 'tech debt', investor_pressure_delta: 'investor pressure',
        first_week_satisfaction_dip: 'sat dip',
      };
      return map[k] || k;
    },
    effectClass(v) {
      if (typeof v === 'boolean') return '';
      const num = Number(v);
      if (Number.isFinite(num)) {
        if (num > 0) return 'pmsim__fe--up';
        if (num < 0) return 'pmsim__fe--down';
      }
      return '';
    },
    effectValue(v) {
      if (typeof v === 'boolean') return v ? 'on' : 'off';
      const num = Number(v);
      if (Number.isFinite(num)) return (num > 0 ? '+' : '') + num;
      return String(v);
    },
    async loadState(updateLocal) {
      const params = { locale: this.locale };
      if (this.participantToken) params.participant_token = this.participantToken;
      const res = await axios.get(`/api/agile-training/pm-sim/g/${this.slug}/state`, { params });
      this.group = res.data.group || {};
      this.sessionInfo = res.data.session || {};
      const s = res.data.state;
      if (s) {
        if (!updateLocal && this.state && s.version === this.lastVersion) return;
        this.state = s;
        this.lastVersion = s.version;
      }
    },
    async joinGroup() {
      this.joining = true; this.joinError = '';
      try {
        const body = { display_name: this.displayName || undefined };
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, body);
        this.participantToken = res.data.participant_token;
        write(TOKEN_KEY_PREFIX, this.slug, this.participantToken);
        write(NAME_KEY_PREFIX, this.slug, this.displayName);
        await this.loadState(true);
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.joining = false; }
    },
    async changeRole(role) {
      if (!this.participantToken) return;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/join`, {
          participant_token: this.participantToken, role: role || null,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async startGame() {
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/start`, {
          participant_token: this.participantToken,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async voteEvent(optionId) {
      const same = this.myEventVote === optionId;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/vote`, {
          participant_token: this.participantToken, kind: 'event', choice: same ? '' : optionId,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async voteFeature(key) {
      const same = this.myFeatureVote === key;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/vote`, {
          participant_token: this.participantToken, kind: 'feature', choice: same ? '' : key,
        });
        await this.loadState(true);
      } catch (_) { /* ignore */ }
    },
    async confirmEventDecision() {
      if (!this.poDecision) return;
      this.submitting = true;
      try {
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/event/decide`, {
          participant_token: this.participantToken, option_id: this.poDecision,
        });
        this.poDecision = '';
        await this.loadState(true);
      } catch (e) {
        this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.submitting = false; }
    },
    toggleFeaturePick(f) {
      const idx = this.featurePicks.indexOf(f.key);
      if (idx >= 0) { this.featurePicks.splice(idx, 1); return; }
      const big = this.state.feature_options.find((x) => x.key === f.key && (x.capacity || 0) >= 40);
      if (big && this.featurePicks.some((k) => {
        const ff = this.state.feature_options.find((x) => x.key === k);
        return !!ff;
      })) {
        this.featurePicks = [f.key];
        return;
      }
      const wouldBig = this.featurePicks.filter((k) => {
        const ff = this.state.feature_options.find((x) => x.key === k);
        return ff && (ff.capacity || 0) >= 40;
      }).length + ((f.capacity || 0) >= 40 ? 1 : 0);
      if (wouldBig > 1) { this.featurePicks = [f.key]; return; }
      if (this.featurePicks.length >= 2) {
        this.featurePicks = [this.featurePicks[this.featurePicks.length - 1], f.key];
        return;
      }
      this.featurePicks.push(f.key);
    },
    async confirmFeatureRelease(skip) {
      this.submitting = true;
      try {
        const keys = skip ? [] : this.featurePicks.slice();
        await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/feature/release`, {
          participant_token: this.participantToken, feature_keys: keys,
        });
        this.featurePicks = [];
        await this.loadState(true);
      } catch (e) {
        this.loadError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally { this.submitting = false; }
    },
    async askAi(mode) {
      if (this.aiBusy) return;
      this.aiBusy = true;
      try {
        const res = await axios.post(`/api/agile-training/pm-sim/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken, mode, user_input: this.aiInput, locale: this.locale,
        });
        this.aiReply = res.data.reply || '';
        await this.loadState(true);
      } catch (e) {
        this.aiReply = (e.response && e.response.data && e.response.data.error) || 'Error';
      } finally { this.aiBusy = false; }
    },
    printReport() {
      window.print();
    },
  },
};
</script>

<style scoped>
.pmsim { max-width: 1200px; margin: 0 auto; padding: 16px; color: #1f2937; }
.pmsim__top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.pmsim__brand { display: flex; align-items: center; gap: 12px; }
.pmsim__logo { font-size: 28px; }
.pmsim__title { font-size: 22px; font-weight: 700; color: #111827; }
.pmsim__sub { font-size: 13px; color: #6b7280; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.pmsim__dot { color: #9ca3af; }
.pmsim__status { font-weight: 700; padding: 2px 8px; border-radius: 999px; }
.pmsim__status--alive { color: #065f46; background: #d1fae5; }
.pmsim__status--at_risk { color: #92400e; background: #fef3c7; }
.pmsim__status--dead { color: #7f1d1d; background: #fee2e2; }

.pmsim__lang button { border: 1px solid #cbd5e1; background: #fff; padding: 4px 10px; border-radius: 6px; margin-left: 4px; cursor: pointer; }
.pmsim__lang .act { background: #eef2ff; border-color: #6366f1; color: #4338ca; }

.pmsim__panel { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 22px; margin: 12px 0; }
.pmsim__lead { color: #374151; line-height: 1.55; }
.pmsim__form { display: flex; gap: 10px; margin-top: 14px; }
.pmsim__form input { flex: 1; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 8px; }
.pmsim__btn { border: 1px solid #cbd5e1; background: #fff; padding: 9px 14px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.pmsim__btn--primary { background: linear-gradient(135deg,#6366f1,#22c55e); color: #fff; border-color: transparent; }
.pmsim__btn--primary:disabled { opacity: 0.55; cursor: not-allowed; }
.pmsim__btn--ghost { background: #f8fafc; }
.pmsim__error { color: #b91c1c; margin-top: 8px; }
.pmsim__hint { color: #6b7280; font-size: 13px; margin-top: 6px; }

.pmsim__roles { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; margin-top: 8px; }
.pmsim__role { text-align: left; border: 1px solid #e2e8f0; background: #fff; border-radius: 10px; padding: 10px 12px; cursor: pointer; display: flex; flex-direction: column; gap: 4px; }
.pmsim__role-icon { font-size: 22px; }
.pmsim__role-desc { color: #6b7280; font-size: 12px; }
.pmsim__role--active { border-color: #6366f1; background: #eef2ff; }
.pmsim__role--taken { opacity: 0.7; border-style: dashed; }

.pmsim__participants { margin-top: 14px; }
.pmsim__participants ul { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-wrap: wrap; gap: 8px; }
.pmsim__participants li { background: #f1f5f9; padding: 6px 10px; border-radius: 999px; font-size: 13px; display: inline-flex; align-items: center; gap: 6px; }
.pmsim__pcount { font-size: 13px; color: #6b7280; }
.pmsim__pill { background: #e0e7ff; color: #4338ca; padding: 1px 8px; border-radius: 999px; font-size: 11px; }
.pmsim__pill--ghost { background: #f1f5f9; color: #6b7280; }

.pmsim__cta { margin-top: 14px; display: flex; gap: 12px; align-items: center; }

.pmsim__dashboard { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 8px 0; }
.pmsim__metric { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 10px 12px; }
.pmsim__metric--money { background: linear-gradient(135deg,#ecfdf5,#d1fae5); border-color: #34d399; }
.pmsim__metric--debt { background: #fff7ed; border-color: #fdba74; }
.pmsim__metric--bad { background: #fef2f2; border-color: #fca5a5; }
.pmsim__metric--warn { background: #fffbeb; border-color: #fcd34d; }
.pmsim__m-label { font-size: 12px; color: #64748b; text-transform: uppercase; letter-spacing: 0.04em; }
.pmsim__m-value { font-size: 22px; font-weight: 700; color: #0f172a; }
.pmsim__m-sub { font-size: 12px; color: #6b7280; }
.pmsim__m-bar { height: 6px; background: #e2e8f0; border-radius: 999px; margin-top: 6px; overflow: hidden; }
.pmsim__m-bar > span { display: block; height: 100%; background: #6366f1; }

.pmsim__charts h3 { margin: 14px 0 6px; }
.pmsim__chart-wrap { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px; }

.pmsim__risks { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
.pmsim__risk { background: #fef3c7; color: #92400e; padding: 4px 8px; border-radius: 6px; font-size: 12px; }

.pmsim__event { background: #fff; border: 2px solid #6366f1; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__event-type { background: #ede9fe; color: #4338ca; padding: 2px 10px; border-radius: 999px; font-size: 12px; text-transform: uppercase; }
.pmsim__event h2 { margin: 6px 0 8px; }
.pmsim__event-desc { color: #374151; }

.pmsim__options { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; margin: 12px 0; }
.pmsim__option { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; }
.pmsim__option--mine { border-color: #22c55e; background: #f0fdf4; }
.pmsim__option--leading { border-color: #6366f1; }
.pmsim__option-head { display: flex; justify-content: space-between; align-items: center; }
.pmsim__votes { background: #e0e7ff; color: #4338ca; padding: 2px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }

.pmsim__decision-bar { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 10px; }
.pmsim__decision-bar select { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; }

.pmsim__features { background: #fff; border: 2px dashed #22c55e; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__capacity-line { font-size: 13px; color: #475569; }
.pmsim__feature-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px; }
.pmsim__feature { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; cursor: pointer; transition: all .15s ease; }
.pmsim__feature:hover { border-color: #6366f1; }
.pmsim__feature--picked { border-color: #22c55e; background: #f0fdf4; }
.pmsim__feature header { display: flex; justify-content: space-between; }
.pmsim__feat-cap { background: #e0e7ff; color: #4338ca; padding: 1px 8px; border-radius: 999px; font-size: 12px; }
.pmsim__feat-effects { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-wrap: wrap; gap: 6px; font-size: 12px; }
.pmsim__feat-effects li { background: #fff; padding: 2px 8px; border-radius: 999px; border: 1px solid #e2e8f0; }
.pmsim__fe-key { color: #64748b; margin-right: 4px; }
.pmsim__fe-value.pmsim__fe--up { color: #047857; }
.pmsim__fe-value.pmsim__fe--down { color: #b91c1c; }
.pmsim__feat-pick { color: #047857; font-weight: 700; margin-top: 6px; font-size: 12px; }
.pmsim__votes-row { display: flex; justify-content: space-between; align-items: center; margin-top: 6px; }

.pmsim__released { margin: 10px 0; }
.pmsim__released-list { display: flex; flex-wrap: wrap; gap: 6px; }
.pmsim__released-pill { background: #ecfdf5; border: 1px solid #34d399; color: #065f46; padding: 3px 8px; border-radius: 999px; font-size: 12px; }

.pmsim__consequences { background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px 10px; font-size: 14px; }

.pmsim__ai { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; margin: 10px 0; }
.pmsim__ai textarea { width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; }
.pmsim__ai-row { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-top: 6px; }
.pmsim__ai-counter { margin-left: auto; color: #6b7280; font-size: 12px; }
.pmsim__ai-reply { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 10px; white-space: pre-wrap; font-family: inherit; margin-top: 8px; }

.pmsim__history ol { padding-left: 20px; }
.pmsim__history li { font-size: 13px; color: #334155; margin: 2px 0; }
.pmsim__history-effects { color: #6b7280; }

.pmsim__leader-hint { background: #eff6ff; border: 1px solid #93c5fd; color: #1e40af; padding: 8px 12px; border-radius: 8px; }

.pmsim__final { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 16px; margin: 12px 0; }
.pmsim__final-summary { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px; }
.pmsim__final-card { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; text-align: center; }
.pmsim__final-label { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.04em; }
.pmsim__final-value { font-size: 28px; font-weight: 700; color: #0f172a; }
.pmsim__final-events { margin-top: 12px; }
.pmsim__final-events ol { padding-left: 20px; }

.pmsim__loading { padding: 16px; color: #6b7280; }

@media print {
  .pmsim__top, .pmsim__lang, .pmsim__ai, .pmsim__cta, .pmsim__decision-bar, .pmsim__btn { display: none !important; }
  .pmsim__panel, .pmsim__final { box-shadow: none; border-color: #cbd5e1; }
  body { background: #fff; }
}
</style>
