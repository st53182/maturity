<template>
  <div class="rqf">
    <header class="rqf__head">
      <div>
        <h1>🎯 {{ $t('agileTraining.roleQuiz.facTitle') }}</h1>
        <p class="rqf__sub">{{ $t('agileTraining.roleQuiz.facSubtitle') }}</p>
      </div>
      <router-link class="rqf__back" to="/agile-training">
        ← {{ $t('agileTraining.hub.backHome') }}
      </router-link>
    </header>

    <!-- Sessions list -->
    <section v-if="!activeSession" class="rqf__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="rqf__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle"
               :placeholder="$t('agileTraining.roleQuiz.newSessionTitle')"
               required maxlength="255" />
        <select v-model="newSessionLocale" class="rqf__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="rqf__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="rqf__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="rqf__list">
        <li v-for="s in sessions" :key="s.id" class="rqf__item">
          <div>
            <div class="rqf__item-title">{{ s.title }}</div>
            <div class="rqf__item-meta">
              <span class="rqf__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>
                {{ $t('agileTraining.facilitator.groupsCount',
                      { n: s.groups_count || 0 }, s.groups_count || 0) }}
              </span>
            </div>
          </div>
          <button class="rqf__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- Active session -->
    <section v-else class="rqf__section">
      <div class="rqf__active-head">
        <div>
          <div class="rqf__active-title">{{ activeSession.title }}</div>
          <div class="rqf__item-meta">
            <span class="rqf__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="rqf__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.roleQuiz.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">
            ← {{ $t('agileTraining.facilitator.backToList') }}
          </button>
          <button class="btn-danger" @click="deleteSession">
            {{ $t('agileTraining.facilitator.deleteSession') }}
          </button>
        </div>
      </div>

      <div class="rqf__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="rqf__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName"
                 :placeholder="$t('agileTraining.facilitator.newGroupName')"
                 required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="rqf__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="rqf__groups">
        <li v-for="g in groups" :key="g.id" class="rqf__group">
          <div class="rqf__group-main">
            <div class="rqf__group-name">{{ g.name }}</div>
            <div class="rqf__item-meta">
              <span>
                {{ $t('agileTraining.facilitator.participants',
                       { n: g.participants_count || 0 }, g.participants_count || 0) }}
              </span>
            </div>
            <div class="rqf__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="rqf__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug
                   ? $t('agileTraining.facilitator.copied')
                   : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="rqf__group-actions">
            <button class="btn-ghost" @click="openGroupResults(g)">
              {{ $t('agileTraining.facilitator.viewResults') }}
            </button>
            <button class="btn-ghost" @click="resetGroup(g)">
              {{ $t('agileTraining.facilitator.reset') }}
            </button>
            <button class="btn-danger" @click="removeGroup(g)">
              {{ $t('agileTraining.facilitator.delete') }}
            </button>
          </div>
        </li>
      </ul>
    </section>

    <!-- Group results modal -->
    <div v-if="resultsModal.open" class="rqf__modal" @click.self="closeResults">
      <div class="rqf__modal-body">
        <div class="rqf__modal-head">
          <h3>{{ $t('agileTraining.roleQuiz.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="rqf__modal-close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="rqf__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="rqf__lead">
            {{ $t('agileTraining.facilitator.participants',
                  { n: resultsModal.data.participants_count || 0 },
                  resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.roleQuiz.avgHealth') }}:
            <b>{{ resultsModal.data.avg_health_pct || 0 }}%</b>
            · {{ $t('agileTraining.roleQuiz.accountableCorrect') }}:
            <b>{{ resultsModal.data.avg_accountable_correct || 0 }}</b>
          </p>

          <div class="rqf__color-totals">
            <span class="rqf__pill rqf__pill--green">🟢 {{ resultsModal.data.color_totals.green || 0 }}</span>
            <span class="rqf__pill rqf__pill--yellow">🟡 {{ resultsModal.data.color_totals.yellow || 0 }}</span>
            <span class="rqf__pill rqf__pill--red">🔴 {{ resultsModal.data.color_totals.red || 0 }}</span>
            <span class="rqf__pill rqf__pill--muted">◻ {{ resultsModal.data.color_totals.missing || 0 }}</span>
          </div>

          <h4 v-if="resultsModal.data.weak_situations?.length" class="rqf__section-h">
            🔴 {{ $t('agileTraining.roleQuiz.weakSituations') }}
          </h4>
          <ol v-if="resultsModal.data.weak_situations?.length" class="rqf__weak">
            <li v-for="w in resultsModal.data.weak_situations" :key="'w-' + w.key">
              <b>{{ w.title }}</b>
              <span class="rqf__pill rqf__pill--red">{{ w.red_pct }}% 🔴</span>
            </li>
          </ol>

          <h4 class="rqf__section-h">📊 {{ $t('agileTraining.roleQuiz.heatmap') }}</h4>
          <div class="rqf__heatmap">
            <table>
              <thead>
                <tr>
                  <th>{{ $t('agileTraining.roleQuiz.situationCol') }}</th>
                  <th v-for="r in ROLE_KEYS" :key="r">{{ roleTitle(r) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in resultsModal.data.situations" :key="s.key">
                  <td><b>{{ s.title }}</b></td>
                  <td v-for="r in ROLE_KEYS" :key="'cell-' + s.key + '-' + r">
                    <div class="rqf__cell">
                      <div v-for="lv in (s.roles[r]?.levels || [])" :key="lv.level || 'none'"
                           class="rqf__cell-row">
                        <span>{{ lv.level_title || $t('agileTraining.roleQuiz.notPicked') }}</span>
                        <b>{{ lv.pct }}%</b>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- per-participant drilldown -->
          <div v-if="resultsModal.participants.length" class="rqf__parts">
            <button class="rqf__parts-toggle"
                    @click="resultsModal.showParticipants = !resultsModal.showParticipants">
              {{ resultsModal.showParticipants ? '▾' : '▸' }}
              {{ $t('agileTraining.roleQuiz.participantsDrill') }}
              ({{ resultsModal.participants.length }})
            </button>
            <div v-if="resultsModal.showParticipants" class="rqf__parts-body">
              <div v-for="p in resultsModal.participants" :key="p.id" class="rqf__part">
                <button class="rqf__part-toggle" @click="togglePart(p.id)">
                  <span>{{ resultsModal.expanded[p.id] ? '▾' : '▸' }}</span>
                  <b>{{ p.display_name }}</b>
                  <span v-if="p.has_answer" class="rqf__pill">{{ p.health_pct }}%</span>
                  <span v-else class="rqf__pill rqf__pill--muted">
                    {{ $t('agileTraining.roleQuiz.noAnswer') }}
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id] && p.has_answer" class="rqf__part-body">
                  <table class="rqf__part-table">
                    <thead>
                      <tr>
                        <th>{{ $t('agileTraining.roleQuiz.situationCol') }}</th>
                        <th v-for="r in ROLE_KEYS" :key="r">{{ roleTitle(r) }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="s in p.situations" :key="s.key">
                        <td>{{ s.title }}</td>
                        <td v-for="r in ROLE_KEYS" :key="s.key + '-' + r"
                            :class="'rqf__cell-' + (s.roles[r]?.color || 'gray')">
                          <div>
                            <b>{{ s.roles[r]?.picked ? levelShort(s.roles[r].picked) : '—' }}</b>
                          </div>
                          <div class="rqf__hint">
                            {{ $t('agileTraining.roleQuiz.expected') }}:
                            {{ levelShort(s.roles[r]?.expected) }}
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Compare all groups modal -->
    <div v-if="compareAll.open" class="rqf__modal" @click.self="closeCompareAll">
      <div class="rqf__modal-body">
        <div class="rqf__modal-head">
          <h3>🏁 {{ $t('agileTraining.roleQuiz.leaderboard') }}</h3>
          <button class="rqf__modal-close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="rqf__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="rqf__lead">
            {{ $t('agileTraining.roleQuiz.avgHealth') }}:
            <b>{{ compareAll.data.totals.avg_health_pct || 0 }}%</b>
            · {{ $t('agileTraining.facilitator.participants',
                    { n: compareAll.data.totals.participants || 0 },
                    compareAll.data.totals.participants || 0) }}
          </p>
          <ol class="rqf__leaderboard">
            <li v-for="(g, idx) in compareAll.data.leaderboard" :key="g.id">
              <b>{{ idx + 1 }}.</b> {{ g.name }}
              <span class="rqf__pill rqf__pill--good">{{ g.avg_health_pct }}%</span>
              <span class="rqf__hint">
                · {{ $t('agileTraining.facilitator.participants',
                        { n: g.participants_count }, g.participants_count) }}
              </span>
            </li>
            <li v-if="!compareAll.data.leaderboard.length" class="rqf__hint">
              — {{ $t('agileTraining.roleQuiz.noAnswersYet') }}
            </li>
          </ol>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgileRoleQuizFacilitator',
  data() {
    return {
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: (typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en') ? 'en' : 'ru',
      activeSession: null,
      newGroupName: '',
      copiedSlug: '',
      resultsModal: {
        open: false, group: null, loading: false, data: null,
        participants: [], expanded: {}, showParticipants: false,
      },
      compareAll: { open: false, loading: false, data: null },
      ROLE_KEYS: ['po', 'sm', 'pm', 'coach', 'team', 'stakeholder'],
    };
  },
  computed: {
    groups() { return (this.activeSession && this.activeSession.groups) || []; },
  },
  async mounted() {
    await this.loadSessions();
  },
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
    roleTitle(key) {
      const path = 'agileTraining.roleQuiz.roles.' + key + '.title';
      if (this.$te(path)) return this.$t(path);
      return key;
    },
    levelShort(key) {
      if (!key) return '—';
      const path = 'agileTraining.roleQuiz.levels.' + key + '.short';
      if (this.$te(path)) return this.$t(path);
      return key;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions',
          { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || [])
          .filter(s => s.exercise_key === 'role_quiz');
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const r = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'role_quiz' },
          { headers: this.authHeaders() });
        this.newSessionTitle = '';
        await this.loadSessions();
        await this.openSession(r.data.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async openSession(id) {
      try {
        const r = await axios.get(`/api/agile-training/sessions/${id}`,
          { headers: this.authHeaders() });
        this.activeSession = r.data;
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    closeSession() { this.activeSession = null; },
    async deleteSession() {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`,
          { headers: this.authHeaders() });
        this.activeSession = null;
        await this.loadSessions();
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async addGroup() {
      const name = this.newGroupName.trim();
      if (!name) return;
      try {
        await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`,
          { name }, { headers: this.authHeaders() });
        this.newGroupName = '';
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async removeGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`,
          { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmResetGroup', { name: g.name }))) return;
      try {
        await axios.post(`/api/agile-training/role-quiz/groups/${g.id}/reset`, {},
          { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async copyLink(slug) {
      const url = this.publicLink(slug);
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(url);
        } else {
          const ta = document.createElement('textarea');
          ta.value = url; ta.style.position = 'fixed'; ta.style.left = '-9999px';
          document.body.appendChild(ta); ta.select(); document.execCommand('copy');
          document.body.removeChild(ta);
        }
        this.copiedSlug = slug;
        setTimeout(() => { if (this.copiedSlug === slug) this.copiedSlug = ''; }, 1600);
      } catch (_) { alert('Failed to copy link'); }
    },
    async openGroupResults(g) {
      this.resultsModal = {
        open: true, group: g, loading: true, data: null,
        participants: [], expanded: {}, showParticipants: false,
      };
      try {
        const [agg, parts] = await Promise.all([
          axios.get(`/api/agile-training/role-quiz/groups/${g.id}/results`,
            { headers: this.authHeaders() }),
          axios.get(`/api/agile-training/role-quiz/groups/${g.id}/participants`,
            { headers: this.authHeaders() }),
        ]);
        this.resultsModal.data = agg.data;
        this.resultsModal.participants = parts.data.participants || [];
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
      finally { this.resultsModal.loading = false; }
    },
    closeResults() { this.resultsModal.open = false; },
    togglePart(id) {
      this.resultsModal.expanded = {
        ...this.resultsModal.expanded,
        [id]: !this.resultsModal.expanded[id],
      };
    },
    async openCompareAll() {
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const r = await axios.get(
          `/api/agile-training/role-quiz/sessions/${this.activeSession.id}/results`,
          { headers: this.authHeaders() });
        this.compareAll.data = r.data;
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
      finally { this.compareAll.loading = false; }
    },
    closeCompareAll() { this.compareAll.open = false; },
  },
};
</script>

<style scoped>
.rqf { max-width: 1100px; margin: 32px auto 80px; padding: 0 16px; color: #0f172a; }
.rqf__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; flex-wrap: wrap; }
.rqf__head h1 { margin: 0; font-size: 22px; }
.rqf__sub { color: #475569; margin: 4px 0 0; font-size: 14px; }
.rqf__back { color: #4338ca; text-decoration: none; font-weight: 600; font-size: 13px; }
.rqf__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 16px; }
.rqf__section h2 { margin: 0 0 10px; font-size: 17px; }
.rqf__hint { color: #64748b; font-size: 13px; }
.rqf__empty { color: #64748b; padding: 12px 0; font-style: italic; }
.rqf__create, .rqf__add-group { display: flex; gap: 8px; margin: 8px 0 14px; flex-wrap: wrap; }
.rqf__create input, .rqf__add-group input {
  flex: 1; min-width: 200px; padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px;
}
.rqf__locale { padding: 9px 10px; border: 1px solid #cbd5e1; border-radius: 10px; }
.rqf__create button, .rqf__add-group button {
  background: #4338ca; color: #fff; border: none; padding: 9px 18px; border-radius: 10px; font-weight: 700; cursor: pointer;
}
.rqf__list { list-style: none; padding: 0; margin: 0; }
.rqf__item { display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 10px; margin: 6px 0; }
.rqf__item-title { font-weight: 700; }
.rqf__item-meta { color: #64748b; font-size: 12px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.rqf__badge { background: #eef2ff; color: #312e81; padding: 1px 8px; border-radius: 999px; font-weight: 700; font-size: 11px; letter-spacing: 0.04em; }
.rqf__open-btn { background: #fff; border: 1px solid #c7d2fe; color: #312e81; padding: 6px 12px; border-radius: 8px; font-weight: 700; cursor: pointer; }

.rqf__active-head { display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap; align-items: center; margin-bottom: 12px; }
.rqf__active-title { font-weight: 800; font-size: 16px; }
.rqf__active-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 6px 12px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-ghost:hover:not(:disabled) { border-color: #4338ca; color: #4338ca; }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { background: #fff; border: 1px solid #fca5a5; color: #b91c1c; padding: 6px 12px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-danger:hover { background: #fef2f2; }

.rqf__groups-head { display: flex; justify-content: space-between; gap: 12px; align-items: center; flex-wrap: wrap; }
.rqf__groups { list-style: none; padding: 0; margin: 0; }
.rqf__group { display: flex; justify-content: space-between; gap: 12px; padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 10px; margin: 6px 0; align-items: center; flex-wrap: wrap; }
.rqf__group-main { min-width: 0; flex: 1; }
.rqf__group-name { font-weight: 700; }
.rqf__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.rqf__link { display: flex; gap: 6px; align-items: center; margin-top: 4px; flex-wrap: wrap; }
.rqf__link code { background: #f1f5f9; padding: 2px 8px; border-radius: 6px; font-size: 12px; max-width: 320px; overflow: hidden; text-overflow: ellipsis; }
.rqf__copy { background: #fff; border: 1px solid #cbd5e1; padding: 3px 10px; border-radius: 6px; font-size: 11.5px; cursor: pointer; }

.rqf__modal { position: fixed; inset: 0; background: rgba(15,23,42,0.6); z-index: 100; display: flex; padding: 24px; overflow: auto; }
.rqf__modal-body { background: #fff; border-radius: 16px; padding: 20px; margin: auto; max-width: 1080px; width: 100%; max-height: 92vh; overflow: auto; }
.rqf__modal-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 8px; }
.rqf__modal-head h3 { margin: 0; font-size: 17px; }
.rqf__modal-close { background: transparent; border: none; cursor: pointer; font-size: 18px; color: #64748b; }
.rqf__lead { color: #475569; }
.rqf__color-totals { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0; }
.rqf__pill { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: #f1f5f9; }
.rqf__pill--green { background: #ecfdf5; color: #065f46; }
.rqf__pill--yellow { background: #fffbeb; color: #92400e; }
.rqf__pill--red { background: #fef2f2; color: #7f1d1d; }
.rqf__pill--muted { background: #f1f5f9; color: #475569; }
.rqf__pill--good { background: #ecfdf5; color: #065f46; }

.rqf__section-h { margin: 14px 0 6px; font-size: 14px; }
.rqf__weak { padding-left: 18px; margin: 0; }
.rqf__weak li { margin: 4px 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }

.rqf__heatmap { overflow: auto; border: 1px solid #e2e8f0; border-radius: 12px; margin-top: 6px; }
.rqf__heatmap table { border-collapse: collapse; width: 100%; min-width: 720px; font-size: 13px; }
.rqf__heatmap th, .rqf__heatmap td { padding: 8px; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }
.rqf__heatmap th { background: #f8fafc; position: sticky; top: 0; }
.rqf__cell { display: flex; flex-direction: column; gap: 2px; font-size: 12px; }
.rqf__cell-row { display: flex; justify-content: space-between; gap: 6px; }

.rqf__parts { margin-top: 14px; }
.rqf__parts-toggle { background: transparent; border: none; cursor: pointer; font-weight: 700; color: #4338ca; font-size: 13px; }
.rqf__part { border: 1px solid #e2e8f0; border-radius: 10px; margin: 6px 0; padding: 8px 10px; }
.rqf__part-toggle { background: transparent; border: none; cursor: pointer; display: flex; gap: 8px; align-items: center; font-size: 13px; color: #0f172a; }
.rqf__part-table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 12.5px; }
.rqf__part-table th, .rqf__part-table td { padding: 5px 8px; border: 1px solid #e2e8f0; vertical-align: top; }
.rqf__part-table th { background: #f8fafc; }
.rqf__cell-green td, .rqf__cell-green { background: #ecfdf5; }
.rqf__cell-yellow { background: #fffbeb; }
.rqf__cell-red { background: #fef2f2; }
.rqf__cell-missing { background: #f1f5f9; }

.rqf__leaderboard { padding-left: 18px; margin: 8px 0 0; }
.rqf__leaderboard li { margin: 4px 0; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
</style>
