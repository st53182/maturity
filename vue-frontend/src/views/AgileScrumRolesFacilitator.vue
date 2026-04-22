<template>
  <div class="sr-fac">
    <header class="sr-fac__head">
      <div>
        <h1>🧩 {{ $t('agileTraining.scrumRoles.facTitle') }}</h1>
        <p class="sr-fac__sub">{{ $t('agileTraining.scrumRoles.facSubtitle') }}</p>
      </div>
      <router-link class="sr-fac__back" to="/agile-training">
        ← {{ $t('agileTraining.hub.backHome') }}
      </router-link>
    </header>

    <!-- список сессий -->
    <section v-if="!activeSession" class="sr-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="sr-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle"
               :placeholder="$t('agileTraining.scrumRoles.newSessionTitle')"
               required maxlength="255" />
        <select v-model="newSessionLocale" class="sr-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="sr-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="sr-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="sr-fac__list">
        <li v-for="s in sessions" :key="s.id" class="sr-fac__item">
          <div>
            <div class="sr-fac__item-title">{{ s.title }}</div>
            <div class="sr-fac__item-meta">
              <span class="sr-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>
                {{ $t('agileTraining.facilitator.groupsCount',
                      { n: s.groups_count || 0 }, s.groups_count || 0) }}
              </span>
            </div>
          </div>
          <button class="sr-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- активная сессия -->
    <section v-else class="sr-fac__section">
      <div class="sr-fac__active-head">
        <div>
          <div class="sr-fac__active-title">{{ activeSession.title }}</div>
          <div class="sr-fac__item-meta">
            <span class="sr-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="sr-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.scrumRoles.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">
            ← {{ $t('agileTraining.facilitator.backToList') }}
          </button>
          <button class="btn-danger" @click="deleteSession">
            {{ $t('agileTraining.facilitator.deleteSession') }}
          </button>
        </div>
      </div>

      <div class="sr-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="sr-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName"
                 :placeholder="$t('agileTraining.facilitator.newGroupName')"
                 required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="sr-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="sr-fac__groups">
        <li v-for="g in groups" :key="g.id" class="sr-fac__group">
          <div class="sr-fac__group-main">
            <div class="sr-fac__group-name">{{ g.name }}</div>
            <div class="sr-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants',
                           { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.scrumRoles.answersCount',
                           { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
            </div>
            <div class="sr-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="sr-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug
                   ? $t('agileTraining.facilitator.copied')
                   : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="sr-fac__group-actions">
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

    <!-- Модалка: результаты группы -->
    <div v-if="resultsModal.open" class="sr-modal" @click.self="closeResults">
      <div class="sr-modal__body sr-modal__body--wide">
        <div class="sr-modal__head">
          <h3>{{ $t('agileTraining.scrumRoles.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="sr-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="sr-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="sr-modal__lead">
            {{ $t('agileTraining.facilitator.participants',
                  { n: resultsModal.data.participants_count || 0 },
                  resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.scrumRoles.avgHealth') }}:
            <b>{{ resultsModal.data.avg_health_pct || 0 }}%</b>
          </p>

          <div class="sr-color-totals">
            <span class="sr-pill sr-pill--green">🟢 {{ resultsModal.data.color_totals.green || 0 }}</span>
            <span class="sr-pill sr-pill--yellow">🟡 {{ resultsModal.data.color_totals.yellow || 0 }}</span>
            <span class="sr-pill sr-pill--red">🔴 {{ resultsModal.data.color_totals.red || 0 }}</span>
            <span class="sr-pill sr-pill--muted">◻ {{ $t('agileTraining.scrumRoles.missingLabel') }}: {{ resultsModal.data.color_totals.missing || 0 }}</span>
          </div>

          <h4 class="sr-section-title">📊 {{ $t('agileTraining.scrumRoles.heatmap') }}</h4>
          <div class="sr-heatmap">
            <table>
              <thead>
                <tr>
                  <th>{{ $t('agileTraining.scrumRoles.card') }}</th>
                  <th v-for="r in ROLE_KEYS" :key="r">{{ roleTitle(r) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in resultsModal.data.cards" :key="c.key">
                  <td><b>{{ c.title }}</b></td>
                  <td v-for="r in ROLE_KEYS" :key="'c-' + c.key + '-' + r">
                    <div class="sr-cell">
                      <div v-for="lv in (c.roles[r]?.levels || [])" :key="lv.level || 'none'"
                           class="sr-cell__row" :class="'sr-cell__row--' + (lv.level || 'none')">
                        <span>{{ levelLabel(lv.level) }}</span>
                        <span class="sr-cell__pct">{{ lv.pct }}%</span>
                      </div>
                      <div class="sr-cell__colors">
                        <span v-for="(cnt, col) in c.roles[r]?.colors" :key="col"
                              class="sr-pill" :class="'sr-pill--' + col">{{ colorEmoji(col) }} {{ cnt }}</span>
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 class="sr-section-title">⚠️ {{ $t('agileTraining.scrumRoles.errorsSeenTop') }}</h4>
          <ul class="sr-errors">
            <li v-for="e in resultsModal.data.errors_seen" :key="e.key">
              <b>{{ $t('agileTraining.scrumRoles.errors.' + e.key + '.title') }}</b>
              <span class="sr-fac__hint">· {{ e.count }} ({{ e.pct }}%)</span>
            </li>
            <li v-if="!resultsModal.data.errors_seen.length" class="sr-fac__hint">
              — {{ $t('agileTraining.scrumRoles.noErrorsMarked') }}
            </li>
          </ul>

          <div v-if="resultsModal.data.custom_cards?.length">
            <h4 class="sr-section-title">✨ {{ $t('agileTraining.scrumRoles.customCards') }}</h4>
            <ul class="sr-custom-list">
              <li v-for="(cc, i) in resultsModal.data.custom_cards" :key="'cc-' + i">
                <b>{{ cc.title }}</b>
                <span class="sr-fac__hint">
                  <template v-for="(lv, r) in cc.assigned || {}" :key="'cc-' + i + '-' + r">
                    <span v-if="lv"> · {{ roleTitle(r) }}: {{ levelLabel(lv) }}</span>
                  </template>
                </span>
              </li>
            </ul>
          </div>

          <div v-if="resultsModal.data.custom_roles?.length">
            <h4 class="sr-section-title">🧑‍🤝‍🧑 {{ $t('agileTraining.scrumRoles.customRoles') }}</h4>
            <ul class="sr-custom-list">
              <li v-for="(cr, i) in resultsModal.data.custom_roles" :key="'cr-' + i">
                <b>{{ cr.title }}</b>
                <span class="sr-fac__hint" v-if="cr.desc"> · {{ cr.desc }}</span>
              </li>
            </ul>
          </div>

          <!-- drill-down -->
          <div v-if="resultsModal.participants.length" class="sr-parts">
            <button class="sr-fac__participants-toggle"
                    @click="resultsModal.showParticipants = !resultsModal.showParticipants">
              {{ resultsModal.showParticipants ? '▾' : '▸' }}
              {{ $t('agileTraining.scrumRoles.participantsDrill') }}
              ({{ resultsModal.participants.length }})
            </button>
            <div v-if="resultsModal.showParticipants" class="sr-parts__body">
              <div v-for="p in resultsModal.participants" :key="p.id" class="sr-part">
                <button class="sr-part__toggle" @click="togglePart(p.id)">
                  <span>{{ resultsModal.expanded[p.id] ? '▾' : '▸' }}</span>
                  <b>{{ p.display_name }}</b>
                  <span v-if="p.has_answer" class="sr-pill">{{ p.health_pct }}%</span>
                  <span v-if="!p.has_answer" class="sr-pill sr-pill--muted">
                    {{ $t('agileTraining.scrumRoles.noAnswer') }}
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id] && p.has_answer" class="sr-part__body">
                  <table class="sr-part-table">
                    <thead>
                      <tr>
                        <th>{{ $t('agileTraining.scrumRoles.card') }}</th>
                        <th v-for="r in ROLE_KEYS" :key="r">{{ roleTitle(r) }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="c in p.cards" :key="c.key">
                        <td>{{ c.title }}</td>
                        <td v-for="r in ROLE_KEYS" :key="c.key + '-' + r"
                            :class="'sr-cell--' + (c.roles[r]?.color || 'gray')">
                          <div>
                            <b>{{ c.roles[r]?.picked ? levelLabel(c.roles[r].picked) : '—' }}</b>
                          </div>
                          <div class="sr-fac__hint">
                            {{ $t('agileTraining.scrumRoles.expected') }}:
                            {{ levelLabel(c.roles[r]?.expected) }}
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>

                  <div v-if="(p.errors_seen || []).length" class="sr-part__errors">
                    ⚠️ <b>{{ $t('agileTraining.scrumRoles.errorsSeen') }}:</b>
                    <span v-for="(e, i) in p.errors_seen" :key="e">
                      {{ $t('agileTraining.scrumRoles.errors.' + e + '.title') }}<span v-if="i < p.errors_seen.length - 1">, </span>
                    </span>
                  </div>

                  <div v-if="(p.custom_cards || []).length" class="sr-part__custom">
                    ✨ <b>{{ $t('agileTraining.scrumRoles.customCards') }}:</b>
                    <ul>
                      <li v-for="(cc, i) in p.custom_cards" :key="'pcc-' + p.id + '-' + i">
                        {{ cc.title }}
                      </li>
                    </ul>
                  </div>
                  <div v-if="p.custom_role" class="sr-part__custom">
                    🧑‍🤝‍🧑 <b>{{ $t('agileTraining.scrumRoles.customRole') }}:</b>
                    {{ p.custom_role.title }}<span v-if="p.custom_role.desc"> — {{ p.custom_role.desc }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка: сравнение всех групп -->
    <div v-if="compareAll.open" class="sr-modal" @click.self="closeCompareAll">
      <div class="sr-modal__body sr-modal__body--wide">
        <div class="sr-modal__head">
          <h3>🏁 {{ $t('agileTraining.scrumRoles.leaderboard') }}</h3>
          <button class="sr-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="sr-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="sr-modal__lead">
            {{ $t('agileTraining.scrumRoles.avgHealth') }}:
            <b>{{ compareAll.data.totals.avg_health_pct || 0 }}%</b>
            · {{ $t('agileTraining.facilitator.participants',
                    { n: compareAll.data.totals.participants || 0 },
                    compareAll.data.totals.participants || 0) }}
          </p>
          <ol class="sr-leaderboard">
            <li v-for="(g, idx) in compareAll.data.leaderboard" :key="g.id">
              <b>{{ idx + 1 }}.</b> {{ g.name }}
              <span class="sr-pill sr-pill--good">{{ g.avg_health_pct }}%</span>
              <span class="sr-fac__hint">
                · {{ $t('agileTraining.facilitator.participants',
                         { n: g.participants_count }, g.participants_count) }}
              </span>
            </li>
            <li v-if="!compareAll.data.leaderboard.length" class="sr-fac__hint">
              — {{ $t('agileTraining.scrumRoles.noAnswersYet') }}
            </li>
          </ol>

          <h4 class="sr-section-title">📊 {{ $t('agileTraining.scrumRoles.groupScoreboard') }}</h4>
          <table class="sr-heatmap__group">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                <th>{{ $t('agileTraining.facilitator.participants', { n: 2 }, 2) }}</th>
                <th>{{ $t('agileTraining.scrumRoles.avgHealth') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in compareAll.data.groups" :key="g.id">
                <td><b>{{ g.name }}</b></td>
                <td>{{ g.participants_count }}</td>
                <td :class="heatmapClass(g.avg_health_pct)">{{ g.avg_health_pct }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgileScrumRolesFacilitator',
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
      ROLE_KEYS: ['po', 'team', 'sm'],
      rolesIndex: {},
    };
  },
  computed: {
    groups() { return (this.activeSession && this.activeSession.groups) || []; },
  },
  async mounted() {
    await this.loadSessions();
    this.rolesIndex = {
      po: this.$t('agileTraining.scrumRoles.roles.po.title'),
      team: this.$t('agileTraining.scrumRoles.roles.team.title'),
      sm: this.$t('agileTraining.scrumRoles.roles.sm.title'),
    };
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
    roleTitle(key) { return this.$t('agileTraining.scrumRoles.roles.' + key + '.title'); },
    levelLabel(key) {
      if (!key) return '—';
      return this.$t('agileTraining.scrumRoles.levels.' + key);
    },
    colorEmoji(c) { return { green: '🟢', yellow: '🟡', red: '🔴', missing: '◻' }[c] || '·'; },
    heatmapClass(v) {
      if (v >= 70) return 'sr-heatmap__ok';
      if (v >= 40) return 'sr-heatmap__warn';
      return 'sr-heatmap__bad';
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions',
          { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || [])
          .filter(s => s.exercise_key === 'scrum_roles');
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const r = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'scrum_roles' },
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
        await axios.post(`/api/agile-training/scrum-roles/groups/${g.id}/reset`, {},
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
        const r = await axios.get(
          `/api/agile-training/scrum-roles/groups/${g.id}/results`,
          { headers: this.authHeaders(),
            params: { locale: this.activeSession?.locale || 'ru' } });
        this.resultsModal.data = r.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed');
        this.resultsModal.open = false;
        return;
      } finally {
        this.resultsModal.loading = false;
      }
      try {
        const parts = await axios.get(
          `/api/agile-training/scrum-roles/groups/${g.id}/participants`,
          { headers: this.authHeaders(),
            params: { locale: this.activeSession?.locale || 'ru' } });
        this.resultsModal.participants = parts.data.participants || [];
      } catch (_) { this.resultsModal.participants = []; }
    },
    togglePart(id) {
      this.resultsModal.expanded = {
        ...this.resultsModal.expanded,
        [id]: !this.resultsModal.expanded[id],
      };
    },
    closeResults() {
      this.resultsModal = {
        open: false, group: null, loading: false, data: null,
        participants: [], expanded: {}, showParticipants: false,
      };
    },
    async openCompareAll() {
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const r = await axios.get(
          `/api/agile-training/scrum-roles/sessions/${this.activeSession.id}/results`,
          { headers: this.authHeaders(),
            params: { locale: this.activeSession?.locale || 'ru' } });
        this.compareAll.data = r.data;
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
      finally { this.compareAll.loading = false; }
    },
    closeCompareAll() { this.compareAll = { open: false, loading: false, data: null }; },
  },
};
</script>

<style scoped>
.sr-fac { max-width: 1200px; margin: 0 auto; padding: 24px 20px 60px; color: #0f172a; }
.sr-fac__head { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; margin-bottom: 22px; }
.sr-fac__head h1 { margin: 0 0 6px; font-size: 24px; }
.sr-fac__sub { margin: 0; color: #64748b; font-size: 14px; }
.sr-fac__back { color: #7c3aed !important; text-decoration: none; font-weight: 600; }
.sr-fac__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 22px 20px; margin-bottom: 16px; }

.sr-fac__create, .sr-fac__add-group { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.sr-fac__create input, .sr-fac__add-group input, .sr-fac__locale {
  flex: 1 1 220px; padding: 8px 12px; border-radius: 12px; border: 1px solid #cbd5e1; font-size: 14px;
}
.sr-fac__create button, .sr-fac__add-group button {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  color: #fff !important; border: none !important; border-radius: 12px !important;
  padding: 8px 18px !important; font-weight: 700; cursor: pointer;
}

.sr-fac__empty, .sr-fac__hint { color: #64748b; font-size: 13px; }
.sr-fac__list, .sr-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.sr-fac__item, .sr-fac__group {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; border: 1px solid #e2e8f0; border-radius: 14px;
  gap: 12px; flex-wrap: wrap;
}
.sr-fac__item-title, .sr-fac__group-name { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.sr-fac__item-meta { display: flex; gap: 8px; align-items: center; font-size: 12px; color: #64748b; flex-wrap: wrap; }
.sr-fac__badge { background: #e2e8f0; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
.sr-fac__group-main { flex: 1; min-width: 220px; }
.sr-fac__link { margin-top: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.sr-fac__link code { background: #f1f5f9; padding: 4px 8px; border-radius: 8px; font-size: 12px; }
.sr-fac__copy {
  background: #e2e8f0 !important; border: none !important; padding: 4px 12px !important;
  border-radius: 10px !important; font-weight: 700; cursor: pointer; font-size: 12px;
}
.sr-fac__copy:hover { background: #cbd5e1 !important; }
.sr-fac__open-btn {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
  color: #fff !important; border: none !important; border-radius: 12px !important;
  padding: 8px 16px !important; cursor: pointer; font-weight: 700;
}
.sr-fac__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.sr-fac__active-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.sr-fac__active-title { font-size: 20px; font-weight: 800; margin-bottom: 4px; }
.sr-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.sr-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 10px; }

.sr-modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 20px; }
.sr-modal__body { background: #fff; border-radius: 18px; width: 100%; max-width: 960px; padding: 22px; position: relative; }
.sr-modal__body--wide { max-width: 1160px; }
.sr-modal__head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 14px; }
.sr-modal__close { background: #f1f5f9 !important; border: none !important; width: 32px; height: 32px; border-radius: 10px !important; cursor: pointer; font-weight: 700; }
.sr-modal__close:hover { background: #e2e8f0 !important; }
.sr-modal__lead { color: #475569; font-size: 14px; margin: 0 0 12px; }

.sr-color-totals { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 12px; }
.sr-pill { display: inline-block; background: #e2e8f0; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.sr-pill--good { background: #86efac; color: #064e3b; }
.sr-pill--green { background: #dcfce7; color: #047857; }
.sr-pill--yellow { background: #fef3c7; color: #92400e; }
.sr-pill--red { background: #fee2e2; color: #991b1b; }
.sr-pill--missing { background: #f1f5f9; color: #64748b; }
.sr-pill--muted { background: #f1f5f9; color: #64748b; }

.sr-section-title { margin: 18px 0 8px; font-size: 15px; font-weight: 800; }

.sr-heatmap { overflow-x: auto; }
.sr-heatmap table { width: 100%; border-collapse: collapse; min-width: 720px; }
.sr-heatmap th, .sr-heatmap td { text-align: left; padding: 8px; border: 1px solid #e2e8f0; font-size: 12px; vertical-align: top; }
.sr-cell { display: flex; flex-direction: column; gap: 4px; }
.sr-cell__row { display: flex; justify-content: space-between; padding: 2px 6px; border-radius: 8px; background: #f8fafc; font-size: 11px; }
.sr-cell__row--responsible { background: #dcfce7; }
.sr-cell__row--participates { background: #fef3c7; }
.sr-cell__row--should_not   { background: #fee2e2; }
.sr-cell__row--none         { background: #f1f5f9; color: #64748b; font-style: italic; }
.sr-cell__pct { font-weight: 700; color: #475569; }
.sr-cell__colors { display: flex; gap: 4px; flex-wrap: wrap; }

.sr-errors, .sr-leaderboard, .sr-custom-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; font-size: 14px; }
.sr-custom-list li { padding: 6px 10px; border: 1px dashed #e2e8f0; border-radius: 10px; background: #f8fafc; }

.sr-heatmap__group { width: 100%; border-collapse: collapse; margin-top: 8px; }
.sr-heatmap__group th, .sr-heatmap__group td { text-align: left; padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
.sr-heatmap__ok { background: #dcfce7; color: #047857; font-weight: 700; }
.sr-heatmap__warn { background: #fef3c7; color: #92400e; font-weight: 700; }
.sr-heatmap__bad { background: #fee2e2; color: #991b1b; font-weight: 700; }

.sr-parts { margin-top: 16px; border-top: 1px dashed #e2e8f0; padding-top: 10px; }
.sr-fac__participants-toggle {
  background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; padding: 8px 14px !important;
  border-radius: 12px !important; cursor: pointer; font-weight: 700; font-size: 13px;
}
.sr-fac__participants-toggle:hover { background: #e2e8f0 !important; }
.sr-parts__body { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.sr-part { border: 1px solid #e2e8f0; border-radius: 14px; background: #fff; overflow: hidden; }
.sr-part__toggle {
  width: 100%; background: #f8fafc !important; border: none !important; padding: 10px 14px !important;
  cursor: pointer; display: flex; align-items: center; gap: 8px; text-align: left; font-size: 14px;
}
.sr-part__toggle:hover { background: #f1f5f9 !important; }
.sr-part__body { padding: 10px 14px 14px; }
.sr-part-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.sr-part-table th, .sr-part-table td { padding: 6px 8px; border: 1px solid #e2e8f0; vertical-align: top; }
.sr-cell--green { background: #dcfce7; }
.sr-cell--yellow { background: #fef3c7; }
.sr-cell--red { background: #fee2e2; }
.sr-cell--missing { background: #f1f5f9; }
.sr-part__errors { margin-top: 8px; font-size: 13px; color: #991b1b; }
.sr-part__custom { margin-top: 8px; font-size: 13px; color: #7c3aed; }
.sr-part__custom ul { margin: 4px 0 0 16px; padding: 0; }
</style>
