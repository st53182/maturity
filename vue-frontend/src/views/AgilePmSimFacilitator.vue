<template>
  <div class="pmf modern-ui">
    <header class="pmf__head">
      <div>
        <h1>📡 {{ $t('agileTraining.pmSim.facTitle') }}</h1>
        <p class="pmf__sub">{{ $t('agileTraining.pmSim.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="pmf__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <!-- Sessions list -->
    <section v-if="!activeSession" class="pmf__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="pmf__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="$t('agileTraining.pmSim.newSessionTitle')" required maxlength="255" />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit" class="pmf__btn pmf__btn--primary">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="pmf__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="pmf__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="pmf__list">
        <li v-for="s in sessions" :key="s.id" class="pmf__row">
          <div>
            <div class="pmf__row-title">{{ s.title }}</div>
            <div class="pmf__row-meta">
              <span class="pmf__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="pmf__btn pmf__btn--ghost" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
        </li>
      </ul>
    </section>

    <!-- Active session -->
    <section v-else class="pmf__section">
      <div class="pmf__active-head">
        <div>
          <div class="pmf__active-title">{{ activeSession.title }}</div>
          <div class="pmf__row-meta">
            <span class="pmf__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="pmf__active-actions">
          <button class="pmf__btn pmf__btn--ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="pmf__btn pmf__btn--ghost" @click="refreshOverview">🔄 {{ $t('agileTraining.scrumSim.refresh') }}</button>
          <button class="pmf__btn pmf__btn--danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <!-- Leaderboard controls -->
      <div class="pmf__leader-controls">
        <h3>🏆 {{ $t('agileTraining.pmSim.leaderboard') }}</h3>
        <div class="pmf__leader-buttons">
          <span class="pmf__hint">{{ $t('agileTraining.pmSim.openLeaderboardForTeams') }}:</span>
          <button v-for="w in [5,10,15,20]" :key="w" class="pmf__btn pmf__btn--ghost" @click="openLeaderboard(w)">w{{ w }}</button>
        </div>
        <table class="pmf__leader" v-if="leaderboard.length">
          <thead>
            <tr>
              <th>#</th>
              <th>{{ $t('agileTraining.pmSim.team') }}</th>
              <th>{{ $t('agileTraining.pmSim.metric.revenue') }}</th>
              <th>{{ $t('agileTraining.pmSim.metric.users') }}</th>
              <th>{{ $t('agileTraining.pmSim.metric.satisfaction') }}</th>
              <th>{{ $t('agileTraining.pmSim.metric.stability') }}</th>
              <th>{{ $t('agileTraining.pmSim.status') }}</th>
              <th>{{ $t('agileTraining.pmSim.weekShort') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(g, i) in leaderboard" :key="g.group.id">
              <td>{{ i + 1 }}</td>
              <td>{{ g.group.name }}</td>
              <td><strong>${{ formatNumber(g.revenue_total) }}</strong></td>
              <td>{{ formatNumber(g.metrics.users) }}</td>
              <td>{{ Math.round(g.metrics.satisfaction || 0) }}</td>
              <td>{{ Math.round(g.metrics.stability || 0) }}</td>
              <td>
                <span :class="`pmf__status pmf__status--${g.status}`">{{ statusLabel(g.status) }}</span>
              </td>
              <td>{{ g.current_week }}/20</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pmf__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="pmf__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit" class="pmf__btn pmf__btn--primary">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="pmf__empty">{{ $t('agileTraining.facilitator.noGroups') }}</div>
      <ul v-else class="pmf__groups">
        <li v-for="g in groups" :key="g.group.id" class="pmf__group">
          <div class="pmf__group-main">
            <div class="pmf__group-name">{{ g.group.name }}</div>
            <div class="pmf__row-meta">
              <span :class="`pmf__phase pmf__phase--${g.phase}`">{{ phaseLabel(g.phase) }}</span>
              <span>· w{{ g.current_week }}/20</span>
              <span>· 👥 {{ g.participants_count }}</span>
              <span :class="`pmf__status pmf__status--${g.status}`">· {{ statusLabel(g.status) }}</span>
            </div>
            <div class="pmf__row-meta pmf__row-meta--link">
              <a :href="`/g/${g.group.slug}`" target="_blank" rel="noopener noreferrer" class="pmf__link">/g/{{ g.group.slug }} ↗</a>
              <button class="pmf__btn-mini" @click="copy(g.group.slug)" title="copy">📋</button>
            </div>
            <div class="pmf__metric-row">
              <span class="pmf__chip">💰 ${{ formatNumber(g.revenue_total) }}</span>
              <span class="pmf__chip">👤 {{ formatNumber(g.metrics.users || 0) }}</span>
              <span class="pmf__chip">😊 {{ Math.round(g.metrics.satisfaction || 0) }}</span>
              <span class="pmf__chip">🛠 {{ Math.round(g.metrics.stability || 0) }}</span>
              <span class="pmf__chip">🤝 {{ Math.round(g.metrics.trust || 0) }}</span>
              <span class="pmf__chip pmf__chip--debt">💣 {{ Math.round(g.metrics.tech_debt || 0) }}</span>
            </div>
          </div>
          <div class="pmf__group-actions">
            <button v-if="g.phase === 'lobby' || g.phase === 'intro'" class="pmf__btn pmf__btn--primary" @click="startGroup(g)">▶ {{ $t('agileTraining.pmSim.startGame') }}</button>
            <button class="pmf__btn pmf__btn--ghost" @click="toggleGroup(g)">
              {{ expanded === g.group.id ? $t('agileTraining.facilitator.hide') : $t('agileTraining.facilitator.view') }}
            </button>
            <button class="pmf__btn pmf__btn--ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.resetAnswers') }}</button>
            <button class="pmf__btn pmf__btn--danger" @click="deleteGroup(g)">{{ $t('agileTraining.facilitator.deleteGroup') }}</button>
          </div>

          <div v-if="expanded === g.group.id" class="pmf__group-details">
            <div v-if="loadingGroup" class="pmf__hint">{{ $t('common.loading') }}…</div>
            <div v-else-if="groupState">
              <div class="pmf__detail-row">
                <strong>{{ $t('agileTraining.pmSim.currentEvent') }}:</strong>
                <span v-if="groupState.current_event && !groupState.event_resolved">{{ groupState.current_event.title }}</span>
                <span v-else class="pmf__hint">—</span>
              </div>
              <div class="pmf__detail-row">
                <strong>{{ $t('agileTraining.pmSim.featureWindow') }}:</strong>
                <span>{{ groupState.feature_choice_open ? $t('agileTraining.pmSim.open') : $t('agileTraining.pmSim.closed') }}</span>
              </div>
              <div v-if="(groupState.feature_releases || []).length" class="pmf__detail-row">
                <strong>{{ $t('agileTraining.pmSim.released') }}:</strong>
                <span v-for="r in groupState.feature_releases" :key="r.key+'-'+r.week" class="pmf__pill">w{{ r.week }}: {{ r.title }}</span>
              </div>

              <div class="pmf__force">
                <h4>{{ $t('agileTraining.pmSim.forceEvent') }}</h4>
                <select v-model="forceEventId">
                  <option value="">— {{ $t('agileTraining.pmSim.pickEvent') }} —</option>
                  <option v-for="ev in eventCatalog" :key="ev.id" :value="ev.id">[{{ ev.type }}] {{ ev.title }}</option>
                </select>
                <button class="pmf__btn pmf__btn--ghost" :disabled="!forceEventId" @click="forceEvent(g)">{{ $t('agileTraining.pmSim.applyEvent') }}</button>
              </div>

              <div class="pmf__comment">
                <h4>{{ $t('agileTraining.pmSim.comment') }}</h4>
                <textarea v-model="commentDraft" rows="2" :placeholder="$t('agileTraining.pmSim.commentPlaceholder')"></textarea>
                <button class="pmf__btn pmf__btn--ghost" :disabled="!commentDraft.trim()" @click="postComment(g)">{{ $t('agileTraining.pmSim.send') }}</button>
                <ul class="pmf__comments" v-if="(groupState.facilitator_comments || []).length">
                  <li v-for="(c, i) in groupState.facilitator_comments" :key="i">
                    <span class="pmf__pill">w{{ c.week }}</span> {{ c.text }}
                  </li>
                </ul>
              </div>

              <div class="pmf__history">
                <h4>{{ $t('agileTraining.pmSim.history') }}</h4>
                <ol>
                  <li v-for="(h, i) in groupState.history" :key="i">
                    w{{ h.week }} ·
                    <template v-if="h.kind === 'event'">{{ h.event.title }} → <em>{{ h.option.title }}</em></template>
                    <template v-else-if="h.kind === 'feature'">🚀 {{ (h.released || []).map(r => r.title).join(', ') || '—' }}</template>
                  </li>
                </ol>
              </div>
            </div>
            <div v-else class="pmf__empty">—</div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

const REFRESH_INTERVAL_MS = 5000;

export default {
  name: 'AgilePmSimFacilitator',
  data() {
    return {
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: 'ru',
      activeSession: null,
      groups: [],
      leaderboard: [],
      newGroupName: '',
      expanded: null,
      loadingGroup: false,
      groupState: null,
      eventCatalog: [],
      forceEventId: '',
      commentDraft: '',
      refreshTimer: null,
    };
  },
  async mounted() {
    this.loadSessions();
  },
  beforeUnmount() { this.stopRefresh(); },
  methods: {
    _authHeaders() {
      const token = localStorage.getItem('jwt_token') || localStorage.getItem('token') || '';
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    formatDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString(); } catch (_) { return iso; } },
    formatNumber(n) {
      if (!n && n !== 0) return '0';
      const k = Math.abs(n);
      if (k >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
      if (k >= 1_000) return (n / 1_000).toFixed(k >= 10_000 ? 0 : 1).replace('.0', '') + 'k';
      return String(Math.round(n));
    },
    statusLabel(s) { return this.$t(`agileTraining.pmSim.statusLabel.${s || 'alive'}`); },
    phaseLabel(p) { return this.$t(`agileTraining.pmSim.phaseLabel.${p || 'lobby'}`); },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this._authHeaders() });
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'pm_sim');
      } finally { this.loadingSessions = false; }
    },
    async createSession() {
      try {
        const title = this.newSessionTitle.trim();
        if (!title) return;
        await axios.post('/api/agile-training/sessions', {
          title, locale: this.newSessionLocale || 'ru', exercise_key: 'pm_sim',
        }, { headers: this._authHeaders() });
        this.newSessionTitle = '';
        await this.loadSessions();
      } catch (_) { /* ignore */ }
    },
    async openSession(id) {
      try {
        const res = await axios.get(`/api/agile-training/sessions/${id}`, { headers: this._authHeaders() });
        this.activeSession = res.data.session || res.data;
        await this.refreshOverview();
        await this.loadEventCatalog();
        this.startRefresh();
      } catch (_) { /* ignore */ }
    },
    closeSession() {
      this.activeSession = null;
      this.groups = [];
      this.leaderboard = [];
      this.expanded = null;
      this.groupState = null;
      this.stopRefresh();
    },
    async refreshOverview() {
      if (!this.activeSession) return;
      try {
        const res = await axios.get(
          `/api/agile-training/pm-sim/sessions/${this.activeSession.id}/overview`,
          { headers: this._authHeaders() }
        );
        this.groups = res.data.groups || [];
        this.leaderboard = [...this.groups].sort((a, b) => (b.revenue_total || 0) - (a.revenue_total || 0));
        if (this.expanded) await this.loadGroupState(this.expanded);
      } catch (_) { /* ignore */ }
    },
    startRefresh() { this.stopRefresh(); this.refreshTimer = setInterval(() => this.refreshOverview(), REFRESH_INTERVAL_MS); },
    stopRefresh() { if (this.refreshTimer) { clearInterval(this.refreshTimer); this.refreshTimer = null; } },
    async loadEventCatalog() {
      try {
        const r = await axios.get('/api/agile-training/pm-sim/events/catalog', {
          headers: this._authHeaders(), params: { locale: (this.activeSession && this.activeSession.locale) || 'ru' }
        });
        this.eventCatalog = r.data.events || [];
      } catch (_) { /* ignore */ }
    },
    async addGroup() {
      try {
        const name = this.newGroupName.trim();
        if (!name || !this.activeSession) return;
        await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`, { name }, { headers: this._authHeaders() });
        this.newGroupName = '';
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    async deleteSession() {
      if (!this.activeSession) return;
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this._authHeaders() });
        this.closeSession();
        await this.loadSessions();
      } catch (_) { /* ignore */ }
    },
    async deleteGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup'))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.group.id}`, { headers: this._authHeaders() });
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    async startGroup(g) {
      try {
        await axios.post(`/api/agile-training/pm-sim/groups/${g.group.id}/start`, {}, { headers: this._authHeaders() });
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.pmSim.confirmReset'))) return;
      try {
        await axios.post(`/api/agile-training/pm-sim/groups/${g.group.id}/reset`, {}, { headers: this._authHeaders() });
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    async toggleGroup(g) {
      if (this.expanded === g.group.id) { this.expanded = null; this.groupState = null; return; }
      this.expanded = g.group.id;
      await this.loadGroupState(g.group.id);
    },
    async loadGroupState(groupId) {
      this.loadingGroup = true;
      try {
        const r = await axios.get(`/api/agile-training/pm-sim/groups/${groupId}/state`, { headers: this._authHeaders() });
        this.groupState = r.data.state;
      } catch (_) { this.groupState = null; }
      finally { this.loadingGroup = false; }
    },
    async forceEvent(g) {
      if (!this.forceEventId) return;
      try {
        await axios.post(`/api/agile-training/pm-sim/groups/${g.group.id}/force-event`, { event_id: this.forceEventId }, { headers: this._authHeaders() });
        this.forceEventId = '';
        await this.loadGroupState(g.group.id);
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    async postComment(g) {
      if (!this.commentDraft.trim()) return;
      try {
        await axios.post(`/api/agile-training/pm-sim/groups/${g.group.id}/comment`, { text: this.commentDraft }, { headers: this._authHeaders() });
        this.commentDraft = '';
        await this.loadGroupState(g.group.id);
      } catch (_) { /* ignore */ }
    },
    async openLeaderboard(week) {
      if (!this.activeSession) return;
      try {
        await axios.post(
          `/api/agile-training/pm-sim/sessions/${this.activeSession.id}/leaderboard`,
          { week },
          { headers: this._authHeaders() }
        );
        await this.refreshOverview();
      } catch (_) { /* ignore */ }
    },
    copy(slug) {
      try {
        const url = `${window.location.origin}/g/${slug}`;
        navigator.clipboard.writeText(url);
      } catch (_) { /* ignore */ }
    },
  },
};
</script>

<style scoped>
.pmf { max-width: 1200px; margin: 0 auto; padding: 16px; }
.pmf__head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.pmf__sub { color: #6b7280; }
.pmf__back { color: #6366f1; text-decoration: none; }
.pmf__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 16px; margin-bottom: 14px; }

.pmf__create, .pmf__add-group { display: flex; gap: 8px; margin: 8px 0; flex-wrap: wrap; }
.pmf__create input, .pmf__add-group input, .pmf__force select, .pmf__comment textarea { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; }
.pmf__create input { flex: 1; min-width: 200px; }
.pmf__btn { border: 1px solid #cbd5e1; background: #fff; padding: 8px 12px; border-radius: 8px; cursor: pointer; font-weight: 600; }
.pmf__btn--primary { background: linear-gradient(135deg, #6366f1, #22c55e); color: #fff; border-color: transparent; }
.pmf__btn--ghost { background: #f8fafc; }
.pmf__btn--danger { color: #b91c1c; }
.pmf__btn-mini { background: transparent; border: none; cursor: pointer; }

.pmf__list, .pmf__groups { list-style: none; padding: 0; margin: 0; }
.pmf__row, .pmf__group { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 10px; padding: 10px; border-bottom: 1px solid #f1f5f9; }
.pmf__group { flex-direction: column; align-items: stretch; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px; margin-bottom: 8px; }
.pmf__group-main { width: 100%; }
.pmf__group-name { font-weight: 700; font-size: 16px; }
.pmf__row-meta { color: #6b7280; font-size: 13px; display: flex; gap: 6px; flex-wrap: wrap; align-items: center; }
.pmf__row-meta--link { margin-top: 4px; }
.pmf__link { color: #6366f1; text-decoration: none; }
.pmf__metric-row { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.pmf__chip { background: #eef2ff; color: #4338ca; padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.pmf__chip--debt { background: #fff7ed; color: #c2410c; }

.pmf__phase { padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.pmf__phase--lobby { background: #f1f5f9; color: #475569; }
.pmf__phase--intro { background: #fef3c7; color: #92400e; }
.pmf__phase--playing { background: #d1fae5; color: #065f46; }
.pmf__phase--finished { background: #ede9fe; color: #5b21b6; }
.pmf__status { font-weight: 700; padding: 1px 8px; border-radius: 999px; }
.pmf__status--alive { background: #d1fae5; color: #065f46; }
.pmf__status--at_risk { background: #fef3c7; color: #92400e; }
.pmf__status--dead { background: #fee2e2; color: #7f1d1d; }

.pmf__group-actions { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
.pmf__group-details { width: 100%; padding: 10px; margin-top: 8px; background: #f8fafc; border-radius: 10px; }
.pmf__detail-row { margin: 4px 0; font-size: 14px; color: #374151; }
.pmf__pill { background: #ecfdf5; border: 1px solid #34d399; color: #065f46; padding: 1px 8px; border-radius: 999px; font-size: 12px; margin-right: 4px; }

.pmf__force, .pmf__comment, .pmf__history { margin-top: 10px; }
.pmf__force select, .pmf__comment textarea { width: 100%; max-width: 600px; }
.pmf__comment textarea { display: block; width: 100%; }
.pmf__comments { list-style: none; padding: 0; margin: 6px 0 0; }
.pmf__comments li { font-size: 13px; color: #334155; margin: 2px 0; }
.pmf__history ol { padding-left: 20px; }
.pmf__history li { font-size: 13px; color: #475569; }

.pmf__leader { width: 100%; border-collapse: collapse; margin-top: 8px; }
.pmf__leader th, .pmf__leader td { text-align: left; padding: 6px 8px; border-bottom: 1px solid #f1f5f9; font-size: 13px; }
.pmf__leader th { color: #64748b; font-weight: 600; }
.pmf__leader-buttons { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin: 6px 0; }
.pmf__hint { color: #6b7280; font-size: 13px; }
.pmf__empty { color: #94a3b8; padding: 8px; }
.pmf__badge { background: #e0e7ff; color: #4338ca; padding: 1px 8px; border-radius: 999px; font-size: 11px; }
.pmf__active-head { display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px; }
.pmf__active-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.pmf__active-title { font-size: 18px; font-weight: 700; }
.pmf__groups-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin: 14px 0 6px; }
</style>
