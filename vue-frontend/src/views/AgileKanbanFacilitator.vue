<template>
  <div class="kf">
    <header class="kf__head">
      <div>
        <h1>🧩 {{ $t('agileTraining.kanban.facTitle') }}</h1>
        <p class="kf__sub">{{ $t('agileTraining.kanban.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="kf__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <!-- Sessions list -->
    <section v-if="!activeSession" class="kf__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="kf__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="$t('agileTraining.kanban.newSessionTitle')" required maxlength="255" />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="kf__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="kf__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="kf__list">
        <li v-for="s in sessions" :key="s.id" class="kf__row">
          <div>
            <div class="kf__row-title">{{ s.title }}</div>
            <div class="kf__row-meta">
              <span class="kf__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="btn-ghost" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
        </li>
      </ul>
    </section>

    <!-- Active session -->
    <section v-else class="kf__section">
      <div class="kf__active-head">
        <div>
          <div class="kf__active-title">{{ activeSession.title }}</div>
          <div class="kf__row-meta">
            <span class="kf__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="kf__active-actions">
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="kf__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="kf__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="kf__empty">{{ $t('agileTraining.facilitator.noGroups') }}</div>
      <ul v-else class="kf__groups">
        <li v-for="g in groups" :key="g.id" class="kf__group">
          <div class="kf__group-main">
            <div class="kf__group-name">{{ g.name }}</div>
            <div class="kf__row-meta">
              <span>{{ $t('agileTraining.kanban.facilitator.participantsCount', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span v-if="g.with_board_count">· {{ g.with_board_count }} {{ $t('agileTraining.kanban.facilitator.withBoards') }}</span>
            </div>
            <div class="kf__row-meta kf__row-meta--link">
              <a
                :href="`/g/${g.slug}`"
                target="_blank"
                rel="noopener noreferrer"
                class="kf__group-link"
                :title="$t('agileTraining.facilitator.openLink')"
              >/g/{{ g.slug }} ↗</a>
              <button class="btn-mini" @click="copy(g.slug)" :title="$t('agileTraining.facilitator.copyLink')">📋</button>
            </div>
          </div>
          <div class="kf__group-actions">
            <button class="btn-ghost" @click="toggleGroup(g)">
              {{ expanded === g.id ? $t('agileTraining.facilitator.hide') : $t('agileTraining.facilitator.view') }}
            </button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.resetAnswers') }}</button>
            <button class="btn-danger" @click="deleteGroup(g)">{{ $t('agileTraining.facilitator.deleteGroup') }}</button>
          </div>
          <div v-if="expanded === g.id" class="kf__group-details">
            <div v-if="loadingGroup" class="kf__hint">{{ $t('common.loading') }}…</div>
            <div v-else-if="!participants.length" class="kf__empty">{{ $t('agileTraining.kanban.facilitator.noParticipants') }}</div>
            <div v-else class="kf__parts">
              <aside class="kf__parts-list">
                <button
                  v-for="p in participants"
                  :key="p.id"
                  :class="['kf__part', { 'kf__part--active': selectedParticipantId === p.id }]"
                  @click="selectedParticipantId = p.id"
                >
                  <div class="kf__part-name">{{ p.display_name }}</div>
                  <div class="kf__part-meta">
                    <span v-if="p.case_key">· {{ caseLabel(p.case_key) }}</span>
                    <span v-if="p.stage">· {{ p.stage }}</span>
                    <span v-if="p.cards_count !== undefined">· {{ p.cards_count }} 🧩</span>
                  </div>
                </button>
              </aside>
              <main class="kf__part-detail" v-if="selectedParticipant">
                <div class="kf__part-h">{{ selectedParticipant.display_name }}</div>

                <div class="kf__part-block" v-if="selectedParticipant.dissatisfaction && (selectedParticipant.dissatisfaction.internal || selectedParticipant.dissatisfaction.client)">
                  <div class="kf__part-h2">🔥 {{ $t('agileTraining.kanban.summary.dissatisfaction') }}</div>
                  <div v-if="selectedParticipant.dissatisfaction.internal"><strong>{{ $t('agileTraining.kanban.dissatisfaction.internalQ') }}:</strong> {{ selectedParticipant.dissatisfaction.internal }}</div>
                  <div v-if="selectedParticipant.dissatisfaction.client"><strong>{{ $t('agileTraining.kanban.dissatisfaction.clientQ') }}:</strong> {{ selectedParticipant.dissatisfaction.client }}</div>
                </div>

                <div class="kf__part-block" v-if="(selectedParticipant.demand || []).length">
                  <div class="kf__part-h2">📥 {{ $t('agileTraining.kanban.summary.demand') }}</div>
                  <ul><li v-for="(d, i) in selectedParticipant.demand" :key="i"><strong>{{ d.type }}</strong> — {{ d.source }} · {{ d.frequency }} · {{ d.expectations }}</li></ul>
                </div>

                <div class="kf__part-block" v-if="(selectedParticipant.classes || []).length">
                  <div class="kf__part-h2">🏷️ {{ $t('agileTraining.kanban.summary.classes') }}</div>
                  <ul>
                    <li v-for="c in selectedParticipant.classes" :key="c.id">
                      <span class="kf__pill" :style="{ background: c.color }">{{ c.name }}</span>
                      <span v-if="c.criteria"> — {{ c.criteria }}</span>
                    </li>
                  </ul>
                </div>

                <div class="kf__part-block" v-if="(selectedParticipant.policies || []).length">
                  <div class="kf__part-h2">📋 {{ $t('agileTraining.kanban.summary.policies') }}</div>
                  <ul><li v-for="p in selectedParticipant.policies" :key="p.id">{{ p.text }}</li></ul>
                </div>

                <div class="kf__part-block" v-if="(selectedParticipant.workflow || []).length">
                  <div class="kf__part-h2">🧩 {{ $t('agileTraining.kanban.summary.board') }}</div>
                  <KanbanBoard
                    :workflow="selectedParticipant.workflow || []"
                    :swimlanes="selectedParticipant.swimlanes || []"
                    :classes="selectedParticipant.classes || []"
                    :cards="selectedParticipant.cards || []"
                    :column-limits="selectedParticipant.column_limits || {}"
                    :editable="false"
                    :t="boardT"
                  />
                </div>
              </main>
              <main class="kf__part-detail kf__part-detail--empty" v-else>
                {{ $t('agileTraining.kanban.facilitator.pickParticipant') }}
              </main>
            </div>
          </div>
        </li>
      </ul>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import KanbanBoard from '@/components/Kanban/KanbanBoard.vue';

export default {
  name: 'AgileKanbanFacilitator',
  components: { KanbanBoard },
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
      participants: [],
      selectedParticipantId: null,
      content: { cases: [] },
    };
  },
  computed: {
    selectedParticipant() {
      return this.participants.find(p => p.id === this.selectedParticipantId) || null;
    },
    boardT() {
      return {
        wipLabel: this.$t('agileTraining.kanban.board.wipLabel'),
        wipPh: this.$t('agileTraining.kanban.board.wipPh'),
        addCard: '', addSwimlane: '', seedSwimlanes: '',
        removeSwimlane: '', renameSwimlane: '',
        cardTitle: '', cardClass: '', cardNote: '',
        cardSave: '', cardCancel: '', cardDelete: '',
        noClass: '—',
        emptyColumns: this.$t('agileTraining.kanban.board.emptyColumns'),
        emptyLanes: '',
        overLimit: this.$t('agileTraining.kanban.board.overLimit'),
      };
    },
  },
  async mounted() {
    this.loadSessions();
    try {
      const res = await axios.get('/api/agile-training/kanban/content', { params: { locale: this.$i18n.locale || 'ru' } });
      this.content = res.data;
    } catch (_) { /* noop */ }
  },
  methods: {
    _authHeaders() {
      const token = localStorage.getItem('jwt_token') || localStorage.getItem('token') || '';
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    formatDate(iso) { if (!iso) return ''; try { return new Date(iso).toLocaleDateString(); } catch (_) { return iso; } },
    caseLabel(key) {
      const c = (this.content.cases || []).find(x => x.key === key);
      return c ? c.label : key;
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
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'kanban_system');
      } catch (_) { this.sessions = []; }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = (this.newSessionTitle || '').trim();
      if (!title) return;
      try {
        const res = await axios.post('/api/agile-training/sessions', {
          title, locale: this.newSessionLocale || 'ru', exercise_key: 'kanban_system',
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
        this.groups = (res.data.groups || []).map(g => ({
          id: g.id, name: g.name, slug: g.slug,
          participants_count: g.participants, answers_count: g.answers, with_board_count: 0,
        }));
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    closeSession() { this.activeSession = null; this.groups = []; this.expanded = null; this.participants = []; this.selectedParticipantId = null; },
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
        this.groups.push({ id: res.data.id, name: res.data.name, slug: res.data.slug, participants_count: 0, answers_count: 0, with_board_count: 0 });
        this.newGroupName = '';
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async deleteGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup'))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this._authHeaders() });
        this.groups = this.groups.filter(x => x.id !== g.id);
        if (this.expanded === g.id) this.expanded = null;
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async resetGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmResetGroup'))) return;
      try {
        await axios.post(`/api/agile-training/kanban/groups/${g.id}/reset`, {}, { headers: this._authHeaders() });
        if (this.expanded === g.id) await this.toggleGroup(g);
      } catch (e) { alert((e.response && e.response.data && e.response.data.error) || e.message); }
    },
    async toggleGroup(g) {
      if (this.expanded === g.id) { this.expanded = null; this.participants = []; this.selectedParticipantId = null; return; }
      this.expanded = g.id;
      this.loadingGroup = true;
      this.participants = [];
      this.selectedParticipantId = null;
      try {
        const res = await axios.get(`/api/agile-training/kanban/groups/${g.id}/participants`, { headers: this._authHeaders() });
        this.participants = res.data.participants || [];
        const rr = await axios.get(`/api/agile-training/kanban/groups/${g.id}/results`, { headers: this._authHeaders() });
        g.with_board_count = rr.data.with_board_count || 0;
        if (this.participants.length) this.selectedParticipantId = this.participants[0].id;
      } catch (_) { this.participants = []; }
      finally { this.loadingGroup = false; }
    },
  },
};
</script>

<style scoped>
.kf { max-width: 1200px; margin: 24px auto 80px; padding: 0 20px; color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif; }
.kf__head { display: flex; justify-content: space-between; align-items: flex-end; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.kf__head h1 { margin: 0; font-size: 26px; }
.kf__sub { color: #64748b; margin: 4px 0 0; }
.kf__back { color: #0ea5e9; text-decoration: none; font-weight: 600; }
.kf__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 18px; padding: 22px; box-shadow: 0 4px 20px rgba(15, 23, 42, 0.05); }
.kf__create, .kf__add-group { display: flex; gap: 8px; margin-bottom: 14px; flex-wrap: wrap; }
.kf__create input, .kf__create select, .kf__add-group input {
  flex: 1; min-width: 200px; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; font-family: inherit;
}
.kf__create button, .kf__add-group button {
  padding: 10px 18px; background: linear-gradient(135deg, #38bdf8, #0284c7);
  color: #fff; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 14px;
}
.btn-ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 8px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; font-family: inherit; }
.btn-ghost:hover { border-color: #0ea5e9; color: #0ea5e9; }
.btn-danger { background: #fff; border: 1px solid #fca5a5; color: #ef4444; padding: 8px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; font-family: inherit; }
.btn-mini { background: #f1f5f9; border: none; padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 11px; }
.kf__list, .kf__groups { list-style: none; padding: 0; margin: 0; display: grid; gap: 10px; }
.kf__row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #f8fafc; }
.kf__row-title { font-weight: 700; color: #0f172a; }
.kf__row-meta { color: #64748b; font-size: 13px; display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }
.kf__row-meta--link { margin-top: 4px; }
.kf__group-link {
  color: #0ea5e9; text-decoration: none; font-weight: 600;
  font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  padding: 2px 6px; border-radius: 6px; background: #ecfeff; border: 1px solid #bae6fd;
  transition: all 0.15s ease;
}
.kf__group-link:hover { background: #e0f2fe; border-color: #0ea5e9; text-decoration: underline; }
.kf__badge { background: #0ea5e9; color: #fff; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.kf__hint, .kf__empty { color: #64748b; padding: 16px; text-align: center; }
.kf__active-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; padding-bottom: 16px; border-bottom: 1px solid #e5e7eb; }
.kf__active-title { font-size: 20px; font-weight: 700; }
.kf__active-actions { display: flex; gap: 8px; }
.kf__groups-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; gap: 12px; flex-wrap: wrap; }
.kf__groups-head h3 { margin: 0; }
.kf__group { padding: 14px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #f8fafc; display: grid; gap: 8px; }
.kf__group-main { display: flex; flex-direction: column; gap: 4px; }
.kf__group-name { font-weight: 700; color: #0f172a; }
.kf__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.kf__group-details { margin-top: 10px; padding-top: 10px; border-top: 1px dashed #cbd5e1; }
.kf__parts { display: grid; grid-template-columns: 220px 1fr; gap: 12px; }
@media (max-width: 800px) { .kf__parts { grid-template-columns: 1fr; } }
.kf__parts-list { display: flex; flex-direction: column; gap: 6px; max-height: 460px; overflow-y: auto; }
.kf__part { background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px 10px; cursor: pointer; text-align: left; font-family: inherit; }
.kf__part:hover { border-color: #0ea5e9; }
.kf__part--active { background: #f0f9ff; border-color: #0ea5e9; }
.kf__part-name { font-weight: 700; font-size: 13px; color: #0f172a; }
.kf__part-meta { color: #64748b; font-size: 11px; margin-top: 2px; display: flex; gap: 4px; flex-wrap: wrap; }
.kf__part-detail { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 16px; }
.kf__part-detail--empty { color: #94a3b8; text-align: center; padding: 40px 16px; }
.kf__part-h { font-size: 16px; font-weight: 700; margin-bottom: 12px; color: #0f172a; }
.kf__part-h2 { font-weight: 700; color: #0c4a6e; margin-bottom: 4px; font-size: 14px; }
.kf__part-block { margin-top: 14px; padding-top: 14px; border-top: 1px dashed #e2e8f0; }
.kf__part-block:first-of-type { margin-top: 0; padding-top: 0; border-top: none; }
.kf__part-block ul { margin: 4px 0 0; padding-left: 20px; color: #1e293b; line-height: 1.6; font-size: 13px; }
.kf__pill { display: inline-block; padding: 2px 10px; border-radius: 999px; color: #fff; font-size: 11px; font-weight: 700; margin-right: 4px; }
</style>
