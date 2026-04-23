<template>
  <div class="sf modern-ui">
    <header class="sf__head">
      <div>
        <h1>🧩 {{ $t('agileTraining.scrumSim.facTitle') }}</h1>
        <p class="sf__sub">{{ $t('agileTraining.scrumSim.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="sf__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <!-- Sessions list -->
    <section v-if="!activeSession" class="sf__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="sf__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="$t('agileTraining.scrumSim.newSessionTitle')" required maxlength="255" />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit" class="sf__btn sf__btn--primary">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="sf__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="sf__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="sf__list">
        <li v-for="s in sessions" :key="s.id" class="sf__row">
          <div>
            <div class="sf__row-title">{{ s.title }}</div>
            <div class="sf__row-meta">
              <span class="sf__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="sf__btn sf__btn--ghost" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
        </li>
      </ul>
    </section>

    <!-- Active session -->
    <section v-else class="sf__section">
      <div class="sf__active-head">
        <div>
          <div class="sf__active-title">{{ activeSession.title }}</div>
          <div class="sf__row-meta">
            <span class="sf__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="sf__active-actions">
          <button class="sf__btn sf__btn--ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="sf__btn sf__btn--ghost" @click="refreshOverview">🔄 {{ $t('agileTraining.scrumSim.refresh') }}</button>
          <button class="sf__btn sf__btn--danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="sf__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="sf__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit" class="sf__btn sf__btn--primary">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="sf__empty">{{ $t('agileTraining.facilitator.noGroups') }}</div>
      <ul v-else class="sf__groups">
        <li v-for="g in groups" :key="g.id" class="sf__group">
          <div class="sf__group-main">
            <div class="sf__group-name">{{ g.name }}</div>
            <div class="sf__row-meta">
              <span class="sf__phase-chip" :class="'sf__phase-chip--' + phaseClassOf(g)">{{ phaseLabelOf(g) }}</span>
              <span>· {{ $t('agileTraining.scrumSim.dayLabel', { n: g.current_day || 0 }) }}</span>
              <span>· {{ $t('agileTraining.scrumSim.participantsCount', { n: g.participants_count || 0 }) }}</span>
              <span v-if="g.metrics">· {{ g.metrics.done_core }}/{{ g.metrics.total_core }} {{ $t('agileTraining.scrumSim.coreDoneShort') }}</span>
            </div>
            <div class="sf__row-meta sf__row-meta--link">
              <a
                :href="`/g/${g.slug}`"
                target="_blank"
                rel="noopener noreferrer"
                class="sf__group-link"
                :title="$t('agileTraining.facilitator.openLink')"
              >/g/{{ g.slug }} ↗</a>
              <button class="sf__btn-mini" @click="copy(g.slug)" :title="$t('agileTraining.facilitator.copyLink')">📋</button>
              <span v-if="g.sprint_goal" class="sf__goal-inline">🎯 {{ g.sprint_goal }}</span>
            </div>
          </div>
          <div class="sf__group-actions">
            <button class="sf__btn sf__btn--ghost" @click="toggleGroup(g)">
              {{ expanded === g.id ? $t('agileTraining.facilitator.hide') : $t('agileTraining.facilitator.view') }}
            </button>
            <button class="sf__btn sf__btn--ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.resetAnswers') }}</button>
            <button class="sf__btn sf__btn--danger" @click="deleteGroup(g)">{{ $t('agileTraining.facilitator.deleteGroup') }}</button>
          </div>
          <div v-if="expanded === g.id" class="sf__group-details">
            <div v-if="loadingGroup" class="sf__hint">{{ $t('common.loading') }}…</div>
            <div v-else-if="groupState">
              <div class="sf__group-meta-row">
                <span v-if="groupState.sprint_goal" class="sf__goal-chip">🎯 {{ groupState.sprint_goal }}</span>
                <span class="sf__chip">{{ $t('agileTraining.scrumSim.capacity') }}: {{ groupState.team_capacity_per_day }}</span>
                <span v-if="groupState.review_metrics" class="sf__chip">
                  {{ $t('agileTraining.scrumSim.outcome') }}: {{ $t('agileTraining.scrumSim.outcomes.' + groupState.review_metrics.outcome) }}
                </span>
              </div>
              <ScrumBoard
                :tasks="groupState.tasks"
                :columns="boardColumns"
                :compact="true"
                :selectable="false"
              />
              <div v-if="(groupState.days || []).length" class="sf__days">
                <h4>{{ $t('agileTraining.scrumSim.dailyLog') }}</h4>
                <ul class="sf__days-list">
                  <li v-for="d in groupState.days" :key="d.day">
                    <strong>{{ $t('agileTraining.scrumSim.dayLabel', { n: d.day }) }}:</strong>
                    {{ (d.event && d.event.title) || $t('agileTraining.scrumSim.uneventfulDay') }}
                    <span v-if="d.decision && d.decision.key">· {{ decisionTitle(d.decision.key) }}</span>
                  </li>
                </ul>
              </div>
              <div v-if="(groupState.retro_picks || []).length" class="sf__retro-line">
                <strong>{{ $t('agileTraining.scrumSim.retroChosen') }}:</strong>
                <span v-for="(k, i) in groupState.retro_picks" :key="k">
                  {{ improvementTitle(k) }}<span v-if="i < groupState.retro_picks.length - 1">, </span>
                </span>
              </div>
            </div>
            <div v-else class="sf__empty">{{ $t('agileTraining.scrumSim.noTeamState') }}</div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import ScrumBoard from '@/components/ScrumSim/ScrumBoard.vue';

const REFRESH_INTERVAL_MS = 5000;

export default {
  name: 'AgileScrumSimFacilitator',
  components: { ScrumBoard },
  data() {
    return {
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: 'ru',
      activeSession: null,
      groups: [],
      newGroupName: '',
      expanded: null,
      loadingGroup: false,
      groupState: null,
      content: { decisions: [], improvements: [], context: { columns: [] } },
      refreshTimer: null,
    };
  },
  computed: {
    boardColumns() {
      return (this.content && this.content.context && this.content.context.columns) || undefined;
    },
  },
  async mounted() {
    this.loadSessions();
    try {
      const res = await axios.get('/api/agile-training/scrum-sim/content', { params: { locale: this.$i18n.locale || 'ru' } });
      this.content = res.data;
    } catch (_) { /* noop */ }
  },
  beforeUnmount() { this.stopRefresh(); },
  methods: {
    _authHeaders() {
      const token = localStorage.getItem('jwt_token') || localStorage.getItem('token') || '';
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    formatDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString(); } catch (_) { return iso; } },
    phaseClassOf(g) {
      if (!g.phase) return 'lobby';
      if (g.phase.startsWith('day_')) return 'day';
      return g.phase;
    },
    phaseLabelOf(g) {
      const p = g.phase || 'lobby';
      if (p.startsWith('day_')) return this.$t('agileTraining.scrumSim.phases.day', { n: g.current_day || 1 });
      return this.$t('agileTraining.scrumSim.phases.' + p);
    },
    decisionTitle(key) {
      const d = (this.content.decisions || []).find(x => x.key === key);
      return d ? d.title : key;
    },
    improvementTitle(key) {
      const i = (this.content.improvements || []).find(x => x.key === key);
      return i ? i.title : key;
    },
    copy(slug) {
      try {
        const url = `${window.location.origin}/g/${slug}`;
        navigator.clipboard.writeText(url);
      } catch (_) { /* noop */ }
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this._authHeaders() });
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'scrum_simulator');
      } catch (_) { this.sessions = []; }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = (this.newSessionTitle || '').trim();
      if (!title) return;
      try {
        const res = await axios.post('/api/agile-training/sessions', {
          title, locale: this.newSessionLocale || 'ru', exercise_key: 'scrum_simulator',
        }, { headers: this._authHeaders() });
        this.sessions.unshift({
          id: res.data.id, title: res.data.title, locale: res.data.locale,
          exercise_key: res.data.exercise_key, groups_count: 0, created_at: res.data.created_at,
        });
        this.newSessionTitle = '';
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async openSession(id) {
      try {
        const res = await axios.get(`/api/agile-training/sessions/${id}`, { headers: this._authHeaders() });
        this.activeSession = res.data;
        await this.refreshOverview();
        this.startRefresh();
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async refreshOverview() {
      if (!this.activeSession) return;
      try {
        const res = await axios.get(
          `/api/agile-training/scrum-sim/sessions/${this.activeSession.id}/overview`,
          { headers: this._authHeaders() }
        );
        const overview = res.data.groups || [];
        this.groups = overview.map(o => ({
          id: o.group.id,
          name: o.group.name,
          slug: o.group.slug,
          phase: o.phase,
          current_day: o.current_day,
          participants_count: o.participants_count,
          metrics: o.metrics,
          sprint_goal: o.sprint_goal,
          version: o.version,
        }));
        if (this.expanded) await this.fetchGroupState(this.expanded);
      } catch (_) { /* keep existing */ }
    },
    startRefresh() {
      this.stopRefresh();
      this.refreshTimer = setInterval(() => { this.refreshOverview().catch(() => {}); }, REFRESH_INTERVAL_MS);
    },
    stopRefresh() { if (this.refreshTimer) { clearInterval(this.refreshTimer); this.refreshTimer = null; } },
    closeSession() {
      this.stopRefresh();
      this.activeSession = null;
      this.groups = [];
      this.expanded = null;
      this.groupState = null;
    },
    async deleteSession() {
      if (!this.activeSession) return;
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this._authHeaders() });
        this.closeSession();
        await this.loadSessions();
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async addGroup() {
      if (!this.activeSession) return;
      const name = (this.newGroupName || '').trim();
      if (!name) return;
      try {
        const res = await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`, { name }, { headers: this._authHeaders() });
        this.groups.push({ id: res.data.id, name: res.data.name, slug: res.data.slug, participants_count: 0, phase: 'lobby', current_day: 0 });
        this.newGroupName = '';
        await this.refreshOverview();
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async deleteGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup'))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this._authHeaders() });
        this.groups = this.groups.filter(x => x.id !== g.id);
        if (this.expanded === g.id) { this.expanded = null; this.groupState = null; }
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async resetGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmResetGroup'))) return;
      try {
        await axios.post(`/api/agile-training/scrum-sim/groups/${g.id}/reset`, {}, { headers: this._authHeaders() });
        await this.refreshOverview();
        if (this.expanded === g.id) await this.fetchGroupState(g.id);
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async toggleGroup(g) {
      if (this.expanded === g.id) { this.expanded = null; this.groupState = null; return; }
      this.expanded = g.id;
      await this.fetchGroupState(g.id);
    },
    async fetchGroupState(groupId) {
      this.loadingGroup = true;
      this.groupState = null;
      try {
        const res = await axios.get(`/api/agile-training/scrum-sim/groups/${groupId}/state`, { headers: this._authHeaders() });
        this.groupState = res.data.state;
      } catch (_) { this.groupState = null; }
      finally { this.loadingGroup = false; }
    },
  },
};
</script>

<style scoped>
.sf { max-width: 1200px; margin: 24px auto 80px; padding: 0 20px; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif; }
.sf__head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.sf__head h1 { margin: 0; font-size: 26px; }
.sf__sub { color: #64748b; margin: 4px 0 0; }
.sf__back { color: #0ea5e9; text-decoration: none; font-weight: 600; }
.sf__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 18px; padding: 22px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05); }
.sf__hint { color: #64748b; font-size: 13px; }
.sf__empty { color: #94a3b8; font-size: 14px; padding: 14px 0; text-align: center; }

.sf__create, .sf__add-group { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.sf__create input, .sf__create select, .sf__add-group input {
  flex: 1; min-width: 200px; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; font-family: inherit; background: #fff;
}
.sf__btn {
  padding: 9px 16px; border-radius: 10px; border: 1px solid transparent;
  font-weight: 600; cursor: pointer; font-size: 13px; font-family: inherit;
  display: inline-flex; align-items: center; gap: 6px; transition: all 0.15s;
}
.sf__btn--primary { background: linear-gradient(135deg, #38bdf8, #0284c7); color: #fff; }
.sf__btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 10px rgba(14, 165, 233, 0.3); }
.sf__btn--ghost { background: #fff; border-color: #cbd5e1; color: #475569; }
.sf__btn--ghost:hover:not(:disabled) { border-color: #0ea5e9; color: #0ea5e9; }
.sf__btn--danger { background: #fff; border-color: #fca5a5; color: #ef4444; }
.sf__btn--danger:hover:not(:disabled) { background: #fee2e2; }
.sf__btn-mini { background: #f1f5f9; border: none; padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 11px; }

.sf__list, .sf__groups { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.sf__row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #f8fafc; }
.sf__row-title { font-weight: 700; color: #0f172a; }
.sf__row-meta { color: #64748b; font-size: 13px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.sf__row-meta--link { margin-top: 4px; }
.sf__badge { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }
.sf__group-link {
  color: #0ea5e9; text-decoration: none; font-weight: 600;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  padding: 2px 6px; border-radius: 6px; background: #ecfeff; border: 1px solid #bae6fd;
  transition: all 0.15s ease;
}
.sf__group-link:hover { background: #e0f2fe; border-color: #0ea5e9; }
.sf__goal-inline { color: #92400e; background: #fef3c7; border: 1px solid #fcd34d; padding: 2px 8px; border-radius: 6px; font-size: 12px; }

.sf__active-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.sf__active-title { font-weight: 700; font-size: 18px; }
.sf__active-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.sf__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 12px; }
.sf__groups-head h3 { margin: 0; font-size: 16px; }

.sf__group { border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; background: #f8fafc; }
.sf__group-main { display: flex; flex-direction: column; gap: 4px; margin-bottom: 10px; }
.sf__group-name { font-weight: 700; color: #0f172a; font-size: 15px; }
.sf__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.sf__phase-chip { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: #e0f2fe; color: #0369a1; border: 1px solid #7dd3fc; }
.sf__phase-chip--day { background: #dcfce7; color: #166534; border-color: #86efac; }
.sf__phase-chip--review { background: #ede9fe; color: #5b21b6; border-color: #c4b5fd; }
.sf__phase-chip--retro { background: #fce7f3; color: #9d174d; border-color: #f9a8d4; }
.sf__phase-chip--summary { background: #fef3c7; color: #92400e; border-color: #fcd34d; }

.sf__group-details { margin-top: 12px; padding-top: 12px; border-top: 1px dashed #cbd5e1; }
.sf__group-meta-row { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 10px; font-size: 12px; }
.sf__chip { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 2px 8px; border-radius: 999px; }
.sf__goal-chip { background: linear-gradient(135deg, #fef3c7, #fde68a); border: 1px solid #facc15; color: #78350f; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
.sf__days { margin-top: 12px; }
.sf__days h4 { margin: 0 0 6px; font-size: 13px; color: #334155; }
.sf__days-list { list-style: none; padding-left: 0; margin: 0; font-size: 13px; line-height: 1.6; color: #334155; }
.sf__retro-line { margin-top: 10px; font-size: 13px; color: #334155; }
</style>
