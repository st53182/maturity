<template>
  <div class="sh-fac">
    <header class="sh-fac__head">
      <div>
        <h1>🤝 {{ $t('agileTraining.stakeholderMatrix.facTitle') }}</h1>
        <p class="sh-fac__sub">{{ $t('agileTraining.stakeholderMatrix.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="sh-fac__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <section v-if="!activeSession" class="sh-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="sh-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="$t('agileTraining.stakeholderMatrix.newSessionTitle')" required maxlength="255" />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="sh-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="sh-fac__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="sh-fac__list">
        <li v-for="s in sessions" :key="s.id" class="sh-fac__row">
          <div>
            <div class="sh-fac__row-title">{{ s.title }}</div>
            <div class="sh-fac__row-meta">
              <span>{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>· {{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="sh-fac__btn" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
        </li>
      </ul>
    </section>

    <section v-else class="sh-fac__section">
      <div class="sh-fac__active">
        <div>
          <div class="sh-fac__row-title">{{ activeSession.title }}</div>
          <div class="sh-fac__row-meta">{{ (activeSession.locale || 'ru').toUpperCase() }} · {{ formatDate(activeSession.created_at) }}</div>
        </div>
        <div>
          <button class="sh-fac__btn" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="sh-fac__btn sh-fac__btn--danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>
      <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
      <form class="sh-fac__create" @submit.prevent="addGroup">
        <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
        <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
      </form>
      <ul v-if="groups.length" class="sh-fac__groups">
        <li v-for="g in groups" :key="g.id" class="sh-fac__group">
          <div>
            <strong>{{ g.name }}</strong>
            <div class="sh-fac__row-meta">participants: {{ g.participants_count }} · saved: {{ g.answers_count }}</div>
            <code class="sh-fac__code">{{ publicLink(g.slug) }}</code>
            <button type="button" class="sh-fac__btn" @click="copyLink(g.slug)">
              {{ copied === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
            </button>
            <a :href="publicLink(g.slug)" target="_blank" rel="noopener">{{ $t('agileTraining.facilitator.open') }} ↗</a>
          </div>
          <div>
            <button class="sh-fac__btn" @click="openPlacements(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="sh-fac__btn" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.resetGroup') }}</button>
            <button class="sh-fac__btn sh-fac__btn--danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <div v-if="modal.open" class="sh-fac__modal" @click.self="closeModal">
      <div class="sh-fac__modal-in">
        <h3>{{ modal.group && modal.group.name }}</h3>
        <div v-if="modal.loading">{{ $t('common.loading') }}…</div>
        <ul v-else class="sh-fac__plist">
          <li v-for="p in participants" :key="p.id">
            <strong>{{ p.display_name }}</strong>
            <span v-if="!p.has_answer">—</span>
            <pre v-else class="sh-fac__pre">{{ summarize(p) }}</pre>
          </li>
        </ul>
        <button class="sh-fac__btn" @click="closeModal">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'StakeholderMatrixFacilitator',
  data() {
    return {
      loadingSessions: true,
      sessions: [],
      activeSession: null,
      groups: [],
      newSessionTitle: '',
      newSessionLocale: 'ru',
      newGroupName: '',
      copied: '',
      modal: { open: false, loading: false, group: null },
      participants: [],
    };
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    authHeaders() {
      const t = localStorage.getItem('token') || localStorage.getItem('authToken');
      return t ? { Authorization: 'Bearer ' + t } : {};
    },
    formatDate(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleDateString(this.$i18n.locale === 'en' ? 'en-GB' : 'ru-RU');
      } catch (_) { return iso; }
    },
    publicLink(slug) {
      return `${window.location.origin}/g/${slug}`;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        this.sessions = (res.data.sessions || []).filter((s) => s.exercise_key === 'stakeholder_matrix');
      } catch (_) {
        this.sessions = [];
      } finally {
        this.loadingSessions = false;
      }
    },
    async createSession() {
      if (!(this.newSessionTitle || '').trim()) return;
      const res = await axios.post(
        '/api/agile-training/sessions',
        { title: this.newSessionTitle.trim(), locale: this.newSessionLocale, exercise_key: 'stakeholder_matrix' },
        { headers: this.authHeaders() },
      );
      this.sessions.unshift({
        id: res.data.id,
        title: res.data.title,
        locale: res.data.locale,
        exercise_key: res.data.exercise_key,
        groups_count: 0,
        created_at: res.data.created_at,
      });
      this.newSessionTitle = '';
    },
    async openSession(id) {
      const res = await axios.get(`/api/agile-training/sessions/${id}`, { headers: this.authHeaders() });
      this.activeSession = res.data;
      this.groups = (res.data.groups || []).map((g) => ({
        id: g.id, name: g.name, slug: g.slug, participants_count: g.participants, answers_count: g.answers,
      }));
    },
    closeSession() {
      this.activeSession = null;
      this.groups = [];
    },
    async deleteSession() {
      if (!this.activeSession || !window.confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this.authHeaders() });
      this.closeSession();
      await this.loadSessions();
    },
    async addGroup() {
      if (!this.activeSession) return;
      const name = (this.newGroupName || '').trim();
      if (!name) return;
      const res = await axios.post(
        `/api/agile-training/sessions/${this.activeSession.id}/groups`,
        { name },
        { headers: this.authHeaders() },
      );
      this.groups.push({
        id: res.data.id, name: res.data.name, slug: res.data.slug, participants_count: 0, answers_count: 0,
      });
      this.newGroupName = '';
    },
    async removeGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this.authHeaders() });
      this.groups = this.groups.filter((x) => x.id !== g.id);
    },
    async resetGroup(g) {
      if (!window.confirm('Reset all answers in this group?')) return;
      await axios.post(`/api/agile-training/stakeholder-matrix/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
      g.answers_count = 0;
    },
    copyLink(slug) {
      navigator.clipboard.writeText(this.publicLink(slug));
      this.copied = slug;
      setTimeout(() => { this.copied = ''; }, 1500);
    },
    async openPlacements(g) {
      this.modal = { open: true, loading: true, group: g };
      this.participants = [];
      const res = await axios.get(`/api/agile-training/stakeholder-matrix/groups/${g.id}/participants`, { headers: this.authHeaders() });
      this.participants = res.data.participants || [];
      this.modal.loading = false;
    },
    closeModal() {
      this.modal = { open: false, loading: false, group: null };
      this.participants = [];
    },
    summarize(p) {
      if (!p.placements_r1) return '—';
      try {
        return JSON.stringify({ r1: p.placements_r1, r2: p.placements_r2, ev: p.event_key }, null, 0);
      } catch (_) { return '—'; }
    },
  },
};
</script>

<style scoped>
.sh-fac { max-width: 900px; margin: 0 auto; padding: 20px; font-family: var(--vl-font, system-ui); }
.sh-fac__head { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; margin-bottom: 20px; }
.sh-fac__sub { color: #64748b; margin: 0.3rem 0 0; }
.sh-fac__back { text-decoration: none; color: #1d4ed8; font-weight: 600; }
.sh-fac__section h2, .sh-fac__section h3 { margin-top: 1rem; }
.sh-fac__create { display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0; }
.sh-fac__create input, .sh-fac__create select { padding: 8px 10px; border-radius: 8px; border: 1px solid #cbd5e1; min-width: 200px; }
.sh-fac__list { list-style: none; padding: 0; }
.sh-fac__row, .sh-fac__group { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 10px; padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
.sh-fac__row-title { font-weight: 700; }
.sh-fac__row-meta { color: #64748b; font-size: 13px; }
.sh-fac__btn { border: 1px solid #cbd5e1; background: #fff; border-radius: 8px; padding: 6px 12px; cursor: pointer; font-weight: 600; }
.sh-fac__btn--danger { color: #b91c1c; border-color: #fecaca; }
.sh-fac__code { display: block; font-size: 12px; margin: 4px 0; }
.sh-fac__active { display: flex; flex-wrap: wrap; justify-content: space-between; gap: 8px; margin-bottom: 10px; }
.sh-fac__modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); display: flex; align-items: center; justify-content: center; z-index: 50; padding: 16px; }
.sh-fac__modal-in { background: #fff; border-radius: 12px; max-width: 640px; width: 100%; max-height: 80vh; overflow: auto; padding: 16px; }
.sh-fac__plist { list-style: none; padding: 0; }
.sh-fac__pre { font-size: 11px; white-space: pre-wrap; background: #f1f5f9; padding: 8px; border-radius: 6px; }
</style>
