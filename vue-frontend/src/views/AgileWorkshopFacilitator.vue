<template>
  <div class="wfac">
    <header class="wfac__head">
      <div>
        <h1>{{ titleIcon }} {{ facTitle }}</h1>
        <p class="wfac__sub">{{ facSub }}</p>
      </div>
      <router-link class="wfac__back" to="/agile-training">
        ← {{ $t('agileTraining.hub.backHome') }}
      </router-link>
    </header>

    <section v-if="!activeSession" class="wfac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="wfac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="newSessionPh" required maxlength="255" />
        <select v-model="newSessionLocale" class="wfac__locale">
          <option value="ru">RU</option>
          <option value="en">EN</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <ul v-if="!loadingSessions && sessions.length" class="wfac__list">
        <li v-for="s in sessions" :key="s.id" class="wfac__item">
          <div>
            <div class="wfac__item-title">{{ s.title }}</div>
            <div class="wfac__meta">
              <span class="wfac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
            </div>
          </div>
          <button type="button" class="wfac__open" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
      <div v-else-if="loadingSessions" class="wfac__hint">{{ $t('common.loading') }}…</div>
      <div v-else class="wfac__hint">{{ $t('agileTraining.facilitator.noSessions') }}</div>
    </section>

    <section v-else class="wfac__section">
      <div class="wfac__active-head">
        <div>
          <div class="wfac__active-title">{{ activeSession.title }}</div>
          <div class="wfac__meta">
            <span class="wfac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
          </div>
        </div>
        <div class="wfac__actions">
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>
      <div class="wfac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="wfac__add" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>
      <ul v-if="groups.length" class="wfac__groups">
        <li v-for="g in groups" :key="g.id" class="wfac__group">
          <div>
            <b>{{ g.name }}</b>
            <div class="wfac__meta">
              <code>{{ publicLink(g.slug) }}</code>
              <button type="button" class="wfac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="wfac__g-actions">
            <button class="btn-ghost" @click="openGroup(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.reset') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
      <div v-else class="wfac__hint">{{ $t('agileTraining.facilitator.noGroups') }}</div>
    </section>

    <div v-if="modal.open" class="wfac__modal" @click.self="modal.open = false">
      <div class="wfac__modal-body">
        <div class="wfac__modal-head">
          <h3>{{ modal.group?.name }}</h3>
          <button type="button" @click="modal.open = false">✕</button>
        </div>
        <div v-if="modal.loading" class="wfac__hint">{{ $t('common.loading') }}…</div>
        <ul v-else class="wfac__parts">
          <li v-for="p in modal.participants" :key="p.id">
            <b>{{ p.display_name }}</b>
            <span v-if="p.has_data" class="wfac__ok">✓</span>
            <pre v-if="p.data" class="wfac__pre">{{ formatData(p.data) }}</pre>
            <p v-else class="wfac__hint">—</p>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

const EX = {
  product_stories: { icon: '📘', t: 'agileTraining.workshops.productStories.facTitle', st: 'agileTraining.workshops.productStories.facSubtitle' },
  user_story_map: { icon: '🗺️', t: 'agileTraining.workshops.userStoryMap.facTitle', st: 'agileTraining.workshops.userStoryMap.facSubtitle' },
  kanban_system: { icon: '📶', t: 'agileTraining.workshops.kanbanSystem.facTitle', st: 'agileTraining.workshops.kanbanSystem.facSubtitle' },
};

export default {
  name: 'AgileWorkshopFacilitator',
  data() {
    return {
      exerciseKey: 'product_stories',
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: (typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en') ? 'en' : 'ru',
      activeSession: null,
      newGroupName: '',
      copiedSlug: '',
      modal: { open: false, loading: false, group: null, participants: [] },
    };
  },
  computed: {
    groups() { return (this.activeSession && this.activeSession.groups) || []; },
    keyConf() { return EX[this.exerciseKey] || EX.product_stories; },
    titleIcon() { return this.keyConf.icon; },
    facTitle() { return this.$t(this.keyConf.t); },
    facSub() { return this.$t(this.keyConf.st); },
    newSessionPh() { return this.$t(`agileTraining.workshops.${this.exerciseKey === 'user_story_map' ? 'userStoryMap' : (this.exerciseKey === 'kanban_system' ? 'kanbanSystem' : 'productStories')}.newSessionTitle`); },
  },
  created() {
    this.exerciseKey = this.$route.meta.exerciseKey || 'product_stories';
  },
  watch: {
    '$route'() {
      this.exerciseKey = this.$route.meta.exerciseKey || 'product_stories';
      this.activeSession = null;
      this.loadSessions();
    },
  },
  async mounted() { await this.loadSessions(); },
  methods: {
    authHeaders() {
      const t = localStorage.getItem('token');
      return t ? { Authorization: `Bearer ${t}` } : {};
    },
    publicLink(slug) { return `${window.location.origin}/g/${slug}`; },
    formatDate(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleDateString(
          this.$i18n?.locale === 'en' ? 'en-US' : 'ru-RU',
          { day: '2-digit', month: 'short', year: 'numeric' },
        );
      } catch (_) { return iso; }
    },
    formatData(d) { return JSON.stringify(d, null, 2); },
    baseWs() { return `/api/agile-training/ws/${this.exerciseKey}`; },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || []).filter(s => s.exercise_key === this.exerciseKey);
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      if (!this.newSessionTitle.trim()) return;
      try {
        const r = await axios.post(
          '/api/agile-training/sessions',
          { title: this.newSessionTitle.trim(), locale: this.newSessionLocale, exercise_key: this.exerciseKey },
          { headers: this.authHeaders() },
        );
        this.newSessionTitle = '';
        await this.loadSessions();
        await this.openSession(r.data.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async openSession(id) {
      try {
        const r = await axios.get(`/api/agile-training/sessions/${id}`, { headers: this.authHeaders() });
        this.activeSession = r.data;
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    closeSession() { this.activeSession = null; },
    async deleteSession() {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this.authHeaders() });
        this.activeSession = null;
        await this.loadSessions();
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async addGroup() {
      if (!this.newGroupName.trim() || !this.activeSession) return;
      try {
        await axios.post(
          `/api/agile-training/sessions/${this.activeSession.id}/groups`,
          { name: this.newGroupName.trim() },
          { headers: this.authHeaders() },
        );
        this.newGroupName = '';
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async copyLink(slug) {
      const url = this.publicLink(slug);
      try {
        await navigator.clipboard.writeText(url);
        this.copiedSlug = slug;
        setTimeout(() => { this.copiedSlug = ''; }, 1500);
      } catch (_) { alert(url); }
    },
    async openGroup(g) {
      this.modal = { open: true, loading: true, group: g, participants: [] };
      try {
        const r = await axios.get(
          `${this.baseWs()}/groups/${g.id}/participants`,
          { headers: this.authHeaders() },
        );
        this.modal.participants = r.data.participants || [];
      } catch (e) {
        console.error(e);
        alert(e.response?.data?.error || 'Failed');
        this.modal.open = false;
      } finally { this.modal.loading = false; }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmResetGroup', { name: g.name }))) return;
      try {
        await axios.post(
          `${this.baseWs()}/groups/${g.id}/reset`,
          {},
          { headers: this.authHeaders() },
        );
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async removeGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
  },
};
</script>

<style scoped>
.wfac { max-width: 960px; margin: 0 auto; padding: 24px 16px 60px; color: #0f172a; }
.wfac__head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 20px; }
.wfac__head h1 { margin: 0; font-size: 22px; }
.wfac__sub { margin: 6px 0 0; color: #64748b; font-size: 14px; max-width: 640px; }
.wfac__back { color: #7c3aed; font-weight: 700; text-decoration: none; }
.wfac__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 14px; }
.wfac__create, .wfac__add { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.wfac__create input, .wfac__add input { flex: 1; min-width: 200px; padding: 8px 12px; border-radius: 10px; border: 1px solid #cbd5e1; }
.wfac__locale { padding: 8px; border-radius: 10px; }
.wfac__list, .wfac__groups { list-style: none; margin: 0; padding: 0; }
.wfac__item, .wfac__group { display: flex; justify-content: space-between; align-items: center; padding: 12px; border: 1px solid #e2e8f0; border-radius: 12px; margin-bottom: 8px; gap: 8px; flex-wrap: wrap; }
.wfac__open { background: #7c3aed; color: #fff; border: none; padding: 8px 16px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.wfac__meta { font-size: 12px; color: #64748b; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.wfac__badge { background: #e2e8f0; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 800; }
.wfac__hint { color: #64748b; font-size: 14px; }
.wfac__active-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin-bottom: 12px; }
.wfac__active-title { font-size: 18px; font-weight: 800; }
.wfac__actions { display: flex; gap: 6px; flex-wrap: wrap; }
.wfac__groups-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; margin: 8px 0; align-items: center; }
.wfac__g-actions { display: flex; gap: 4px; flex-wrap: wrap; }
.wfac__copy { background: #e2e8f0; border: none; padding: 4px 8px; border-radius: 8px; font-size: 12px; cursor: pointer; }
.wfac__modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; padding: 24px; overflow-y: auto; }
.wfac__modal-body { background: #fff; border-radius: 16px; max-width: 800px; width: 100%; padding: 16px; margin-top: 20px; }
.wfac__modal-head { display: flex; justify-content: space-between; margin-bottom: 8px; }
.wfac__pre { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; font-size: 11px; overflow: auto; max-height: 320px; white-space: pre-wrap; }
.wfac__parts { list-style: none; margin: 0; padding: 0; }
.wfac__parts li { margin-bottom: 14px; border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; }
.wfac__ok { color: #16a34a; margin-left: 6px; }
.btn-ghost { background: #f1f5f9; border: 1px solid #e2e8f0; padding: 6px 12px; border-radius: 10px; cursor: pointer; }
.btn-danger { background: #fee2e2; border: none; color: #b91c1c; padding: 6px 12px; border-radius: 10px; cursor: pointer; }
</style>
