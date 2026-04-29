<template>
  <div class="rice-fac">
    <header class="rice-fac__head">
      <div>
        <h1>⚖️ {{ $t('agileTraining.rice.facTitle') }}</h1>
        <p class="rice-fac__sub">{{ $t('agileTraining.rice.facSubtitle') }}</p>
      </div>
      <div>
        <router-link class="rice-fac__back" to="/agile-training">
          ← {{ $t('agileTraining.hub.backHome') }}
        </router-link>
      </div>
    </header>

    <!-- список сессий -->
    <section v-if="!activeSession" class="rice-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="rice-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle"
               :placeholder="$t('agileTraining.rice.newSessionTitle')"
               required maxlength="255" />
        <select v-model="newSessionLocale" class="rice-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="rice-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="rice-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="rice-fac__list">
        <li v-for="s in sessions" :key="s.id" class="rice-fac__item">
          <div class="rice-fac__item-main">
            <div class="rice-fac__item-title">{{ s.title }}</div>
            <div class="rice-fac__item-meta">
              <span class="rice-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>
                {{ $t('agileTraining.facilitator.groupsCount',
                      { n: s.groups_count || 0 }, s.groups_count || 0) }}
              </span>
            </div>
          </div>
          <button class="rice-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- активная сессия -->
    <section v-else class="rice-fac__section">
      <div class="rice-fac__active-head">
        <div>
          <div class="rice-fac__active-title">{{ activeSession.title }}</div>
          <div class="rice-fac__item-meta">
            <span class="rice-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="rice-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.rice.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">
            ← {{ $t('agileTraining.facilitator.backToList') }}
          </button>
          <button class="btn-danger" @click="deleteSession">
            {{ $t('agileTraining.facilitator.deleteSession') }}
          </button>
        </div>
      </div>

      <div class="rice-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="rice-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName"
                 :placeholder="$t('agileTraining.facilitator.newGroupName')"
                 required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="rice-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="rice-fac__groups">
        <li v-for="g in groups" :key="g.id" class="rice-fac__group">
          <div class="rice-fac__group-main">
            <div class="rice-fac__group-name">{{ g.name }}</div>
            <div class="rice-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants',
                           { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.rice.answersCount',
                           { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
            </div>
            <div class="rice-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="rice-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug
                   ? $t('agileTraining.facilitator.copied')
                   : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="rice-fac__group-actions">
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
    <div v-if="resultsModal.open" class="rice-modal" @click.self="closeResults">
      <div class="rice-modal__body">
        <div class="rice-modal__head">
          <h3>{{ $t('agileTraining.rice.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="rice-modal__close" @click="closeResults">✕</button>
        </div>

        <div v-if="resultsModal.loading" class="rice-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="rice-modal__lead">
            {{ $t('agileTraining.facilitator.participants',
                  { n: resultsModal.data.participants_count || 0 }, resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.rice.answersCount',
                    { n: resultsModal.data.answers_count || 0 }, resultsModal.data.answers_count || 0) }}
          </p>

          <!-- adaptation pills -->
          <div class="rice-adapt">
            <span v-for="(cnt, key) in resultsModal.data.adaptation_counts"
                  :key="key"
                  class="rice-pill"
                  :class="'rice-pill--' + key">
              {{ $t('agileTraining.rice.adaptation.' + key) }}: <b>{{ cnt }}</b>
            </span>
            <span v-if="!Object.keys(resultsModal.data.adaptation_counts || {}).length"
                  class="rice-fac__hint">
              — {{ $t('agileTraining.rice.noAdaptationYet') }}
            </span>
          </div>

          <h4 class="rice-section-title">🛣️ {{ $t('agileTraining.rice.choicesFlow') }}</h4>
          <table class="rice-table">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.rice.option') }}</th>
                <th>{{ $t('agileTraining.rice.initialPct') }}</th>
                <th>{{ $t('agileTraining.rice.revisedPct') }}</th>
                <th>{{ $t('agileTraining.rice.avgReach') }}</th>
                <th>{{ $t('agileTraining.rice.avgImpact') }}</th>
                <th>{{ $t('agileTraining.rice.avgConfidence') }}</th>
                <th>{{ $t('agileTraining.rice.avgEffort') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="o in resultsModal.data.options" :key="o.key">
                <td><b>{{ o.title }}</b>
                  <div class="rice-fac__hint">
                    {{ $t('agileTraining.rice.expected') }}:
                    {{ o.expected_scores.reach }}/{{ o.expected_scores.impact }}/{{ o.expected_scores.confidence }}/{{ o.expected_scores.effort }}
                  </div>
                </td>
                <td><span class="rice-bar"><span :style="{width: o.initial_pct + '%'}"></span></span>
                  {{ o.initial_pct }}%</td>
                <td><span class="rice-bar rice-bar--rev"><span :style="{width: o.revised_pct + '%'}"></span></span>
                  {{ o.revised_pct }}%</td>
                <td>{{ o.avg_reach }}</td>
                <td>{{ o.avg_impact }}</td>
                <td>{{ o.avg_confidence }}</td>
                <td>{{ o.avg_effort }}</td>
              </tr>
            </tbody>
          </table>

          <div class="rice-cols">
            <div>
              <h4>🎭 {{ $t('agileTraining.rice.byRole') }}</h4>
              <ul class="rice-roles">
                <li v-for="r in resultsModal.data.by_role" :key="r.role_key">
                  <b>{{ r.role_title }}</b>
                  <span class="rice-fac__hint">
                    · {{ $t('agileTraining.facilitator.participants',
                           { n: r.participants }, r.participants) }}
                  </span>
                  <ul class="rice-roles__picks">
                    <li v-for="(cnt, key) in r.revised" :key="'rev-' + key">
                      <b>{{ optionTitle(key) }}</b>: {{ cnt }}
                    </li>
                    <li v-if="!Object.keys(r.revised || {}).length" class="rice-fac__hint">
                      — {{ $t('agileTraining.rice.noRevisedYet') }}
                    </li>
                  </ul>
                </li>
              </ul>
            </div>
            <div>
              <h4>⚠️ {{ $t('agileTraining.rice.topTraps') }}</h4>
              <ul class="rice-errors">
                <li v-for="(cnt, key) in resultsModal.data.error_counts" :key="key">
                  <span>{{ $t('agileTraining.rice.err.' + key) }}</span>
                  <b>{{ cnt }}</b>
                </li>
                <li v-if="!Object.keys(resultsModal.data.error_counts || {}).length"
                    class="rice-fac__hint">
                  — {{ $t('agileTraining.rice.noErrors') }}
                </li>
              </ul>

              <h4 style="margin-top: 14px">🗞 {{ $t('agileTraining.rice.eventsShown') }}</h4>
              <ul class="rice-errors">
                <li v-for="(cnt, key) in resultsModal.data.event_counts" :key="'ev-' + key">
                  <span>{{ eventTitle(key) }}</span>
                  <b>{{ cnt }}</b>
                </li>
              </ul>
            </div>
          </div>

          <!-- drill-down -->
          <div v-if="resultsModal.participants.length" class="rice-participants">
            <button class="rice-fac__participants-toggle"
                    @click="resultsModal.showParticipants = !resultsModal.showParticipants">
              {{ resultsModal.showParticipants ? '▾' : '▸' }}
              {{ $t('agileTraining.rice.participantsDrill') }}
              ({{ resultsModal.participants.length }})
            </button>
            <div v-if="resultsModal.showParticipants" class="rice-participants__body">
              <div v-for="p in resultsModal.participants" :key="p.id" class="rice-part">
                <button class="rice-part__toggle" @click="togglePart(p.id)">
                  <span>{{ resultsModal.expanded[p.id] ? '▾' : '▸' }}</span>
                  <b>{{ p.display_name }}</b>
                  <span v-if="p.has_answer" class="rice-pill rice-pill--muted">
                    {{ p.role_title || p.role_key }}
                  </span>
                  <span v-if="p.has_answer && p.initial_choice" class="rice-pill">
                    {{ p.initial_choice.title }}
                    <template v-if="p.revised_choice && p.revised_choice.key !== p.initial_choice.key">
                      → <b>{{ p.revised_choice.title }}</b>
                    </template>
                  </span>
                  <span v-if="p.has_answer && p.adaptation"
                        class="rice-pill"
                        :class="'rice-pill--' + p.adaptation">
                    {{ $t('agileTraining.rice.adaptation.' + p.adaptation) }}
                  </span>
                  <span v-if="!p.has_answer" class="rice-pill rice-pill--muted">
                    {{ $t('agileTraining.rice.noAnswer') }}
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id] && p.has_answer" class="rice-part__body">
                  <div v-if="p.event" class="rice-part__event">
                    🗞 <b>{{ p.event.title }}</b>
                    <div class="rice-fac__hint">{{ p.event.lead }}</div>
                  </div>
                  <template v-for="stage in ['initial', 'revised']" :key="stage">
                    <div v-if="p[stage]" class="rice-part__stage">
                      <div class="rice-part__stage-title">
                        {{ $t('agileTraining.rice.round.' + stage) }}
                        <span v-if="p[stage].choice" class="rice-pill">
                          {{ p[stage].choice.title }}
                        </span>
                      </div>
                      <table class="rice-table rice-table--compact">
                        <thead>
                          <tr>
                            <th>{{ $t('agileTraining.rice.option') }}</th>
                            <th>{{ $t('agileTraining.rice.dimAbbr.reach') }}</th>
                            <th>{{ $t('agileTraining.rice.dimAbbr.impact') }}</th>
                            <th>{{ $t('agileTraining.rice.dimAbbr.confidence') }}</th>
                            <th>{{ $t('agileTraining.rice.dimAbbr.effort') }}</th>
                            <th>WSJF</th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="row in p[stage].scores" :key="row.key"
                              :class="{ 'rice-row--pick': p[stage].choice && row.key === p[stage].choice.key }">
                            <td>{{ row.title }}</td>
                            <td>{{ row.reach }}</td>
                            <td>{{ row.impact }}</td>
                            <td>{{ row.confidence }}</td>
                            <td>{{ row.effort }}</td>
                            <td><b>{{ row.rice }}</b></td>
                          </tr>
                        </tbody>
                      </table>
                      <div v-if="p[stage].eval && p[stage].eval.errors && p[stage].eval.errors.length"
                           class="rice-part__errors">
                        <span v-for="er in p[stage].eval.errors" :key="er" class="rice-pill rice-pill--warn">
                          {{ $t('agileTraining.rice.err.' + er) }}
                        </span>
                      </div>
                    </div>
                  </template>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка: сравнение всех групп -->
    <div v-if="compareAll.open" class="rice-modal" @click.self="closeCompareAll">
      <div class="rice-modal__body rice-modal__body--wide">
        <div class="rice-modal__head">
          <h3>🏁 {{ $t('agileTraining.rice.compareAll') }}</h3>
          <button class="rice-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="rice-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <h4 class="rice-section-title">📊 {{ $t('agileTraining.rice.groupScoreboard') }}</h4>
          <table class="rice-table">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                <th>{{ $t('agileTraining.facilitator.participants', { n: 2 }, 2) }}</th>
                <th>{{ $t('agileTraining.rice.initialChoice') }}</th>
                <th>{{ $t('agileTraining.rice.revisedChoice') }}</th>
                <th>{{ $t('agileTraining.rice.changedMind') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in compareAll.data.groups" :key="g.id">
                <td><b>{{ g.name }}</b></td>
                <td>{{ g.participants_count }}</td>
                <td>
                  <span v-for="(cnt, key) in g.initial_counts" :key="'i-' + key"
                        class="rice-pill rice-pill--muted">
                    {{ optionTitleFromCompare(key) }}: {{ cnt }}
                  </span>
                  <span v-if="!Object.keys(g.initial_counts || {}).length" class="rice-fac__hint">—</span>
                </td>
                <td>
                  <span v-for="(cnt, key) in g.revised_counts" :key="'r-' + key"
                        class="rice-pill">
                    {{ optionTitleFromCompare(key) }}: {{ cnt }}
                  </span>
                  <span v-if="!Object.keys(g.revised_counts || {}).length" class="rice-fac__hint">—</span>
                </td>
                <td><b>{{ g.changed_mind_count }}</b></td>
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
  name: 'AgileRiceFacilitator',
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
      optionsIndex: {},
      eventsIndex: {},
    };
  },
  computed: {
    groups() { return (this.activeSession && this.activeSession.groups) || []; },
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
    optionTitle(key) {
      return this.optionsIndex[key] || key;
    },
    optionTitleFromCompare(key) {
      return (this.compareAll.data?.content?.options || [])
        .find(o => o.key === key)?.title || key;
    },
    eventTitle(key) {
      return this.eventsIndex[key] || key;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions',
          { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || [])
          .filter(s => s.exercise_key === 'rice');
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const r = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'rice' },
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
        await axios.post(`/api/agile-training/rice/groups/${g.id}/reset`, {},
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
        const r = await axios.get(`/api/agile-training/rice/groups/${g.id}/results`, {
          headers: this.authHeaders(),
          params: { locale: this.activeSession?.locale || 'ru' },
        });
        this.resultsModal.data = r.data;
        const oi = {}; for (const o of r.data.options || []) { oi[o.key] = o.title; }
        this.optionsIndex = oi;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed');
        this.resultsModal.open = false;
        return;
      } finally {
        this.resultsModal.loading = false;
      }
      try {
        const parts = await axios.get(
          `/api/agile-training/rice/groups/${g.id}/participants`,
          { headers: this.authHeaders(),
            params: { locale: this.activeSession?.locale || 'ru' } },
        );
        this.resultsModal.participants = parts.data.participants || [];
        // build event titles index from drill-down
        const ei = {};
        for (const p of this.resultsModal.participants) {
          if (p.event && p.event.key) ei[p.event.key] = p.event.title;
        }
        this.eventsIndex = ei;
      } catch (_) {
        this.resultsModal.participants = [];
      }
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
          `/api/agile-training/rice/sessions/${this.activeSession.id}/results`,
          { headers: this.authHeaders(),
            params: { locale: this.activeSession?.locale || 'ru' } },
        );
        this.compareAll.data = r.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed');
        this.compareAll.open = false;
      } finally {
        this.compareAll.loading = false;
      }
    },
    closeCompareAll() {
      this.compareAll = { open: false, loading: false, data: null };
    },
  },
};
</script>

<style scoped>
.rice-fac {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px 20px 60px;
  color: #1f1f3a;
}
.rice-fac__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 18px;
}
.rice-fac__head h1 { margin: 0 0 6px; font-size: 26px; }
.rice-fac__sub { margin: 0; color: #5a5a80; font-size: 14px; }
.rice-fac__back {
  color: #4f46e5;
  text-decoration: none;
  font-weight: 600;
  border: 1px solid #e3e3ff;
  padding: 8px 14px;
  border-radius: 10px;
  background: #fff;
}
.rice-fac__back:hover { background: #f3f3ff; }

.rice-fac__section {
  background: #fff;
  border: 1px solid #ececff;
  border-radius: 16px;
  padding: 22px;
  box-shadow: 0 1px 2px rgba(40, 40, 90, .04);
  margin-bottom: 16px;
}
.rice-fac__section h2 { margin: 0 0 12px; font-size: 18px; }
.rice-fac__section h3 { margin: 0; font-size: 16px; }

.rice-fac__create, .rice-fac__add-group {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.rice-fac__create input,
.rice-fac__add-group input,
.rice-fac__locale {
  flex: 1 1 220px;
  padding: 10px 12px;
  border: 1px solid #d8d8f0;
  border-radius: 10px;
  font-size: 14px;
  background: #fff;
}
.rice-fac__create button,
.rice-fac__add-group button {
  background: #6366f1 !important;
  color: #fff;
  border: 1px solid #6366f1 !important;
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: background .15s, transform .1s, box-shadow .15s;
}
.rice-fac__create button:hover,
.rice-fac__add-group button:hover {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  box-shadow: 0 4px 10px rgba(79, 70, 229, .25);
}
.rice-fac__create button:active,
.rice-fac__add-group button:active {
  transform: translateY(1px);
  background: #4338ca !important;
  border-color: #4338ca !important;
}

.rice-fac__list, .rice-fac__groups {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.rice-fac__item, .rice-fac__group {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 12px;
  flex-wrap: wrap;
}
.rice-fac__item-title, .rice-fac__group-name { font-weight: 600; font-size: 15px; }
.rice-fac__item-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b6b8c;
  font-size: 12.5px;
  margin-top: 4px;
  flex-wrap: wrap;
}
.rice-fac__badge {
  background: #eef0ff;
  color: #4f46e5;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 11px;
}
.rice-fac__empty {
  padding: 16px;
  text-align: center;
  color: #6b6b8c;
  font-size: 14px;
}
.rice-fac__hint {
  font-size: 12px;
  color: #6b6b8c;
}
.rice-fac__link {
  margin-top: 6px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.rice-fac__link code {
  background: #f1f1ff;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12.5px;
  color: #3a3a6b;
  word-break: break-all;
}
.rice-fac__copy, .rice-fac__open-btn {
  background: #6366f1 !important;
  border: 1px solid #6366f1 !important;
  color: #fff;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 13px;
  cursor: pointer;
  font-weight: 600;
  transition: background .15s, transform .1s, box-shadow .15s;
}
.rice-fac__copy:hover, .rice-fac__open-btn:hover {
  background: #4f46e5 !important;
  border-color: #4f46e5 !important;
  box-shadow: 0 4px 10px rgba(79, 70, 229, .25);
}
.rice-fac__copy:active, .rice-fac__open-btn:active {
  transform: translateY(1px);
  background: #4338ca !important;
  border-color: #4338ca !important;
}

.rice-fac__active-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}
.rice-fac__active-title { font-size: 20px; font-weight: 700; }
.rice-fac__active-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.rice-fac__groups-head {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin: 18px 0 10px;
  flex-wrap: wrap;
}
.rice-fac__group-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* Модалка */
.rice-modal {
  position: fixed;
  inset: 0;
  background: rgba(30, 30, 60, .45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  z-index: 1000;
}
.rice-modal__body {
  background: #fff;
  border-radius: 16px;
  width: 100%;
  max-width: 1100px;
  max-height: 92vh;
  overflow-y: auto;
  padding: 22px;
}
.rice-modal__body--wide { max-width: 1200px; }
.rice-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}
.rice-modal__head h3 { margin: 0; font-size: 18px; }
.rice-modal__close {
  background: #fff !important;
  color: #5a5a80;
  border: 1px solid #e0e0f0 !important;
  padding: 4px 10px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
  transition: background .15s, color .15s;
}
.rice-modal__close:hover {
  background: #f1f1ff !important;
  color: #4f46e5;
}
.rice-modal__lead {
  margin: 0 0 14px;
  color: #6b6b8c;
  font-size: 13px;
}

.rice-section-title {
  margin: 18px 0 10px;
  font-size: 15px;
  color: #3a3a6b;
}
.rice-adapt {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.rice-pill {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  padding: 3px 10px;
  border-radius: 999px;
  background: #eef0ff;
  color: #3a3a6b;
  font-size: 12.5px;
  font-weight: 600;
}
.rice-pill--muted { background: #f0f0f6; color: #6b6b8c; }
.rice-pill--warn { background: #fff3e0; color: #a85a00; }
.rice-pill--stayed_right { background: #e9f7ec; color: #1f7a3b; }
.rice-pill--adapted_well { background: #e5f1ff; color: #2057b8; }
.rice-pill--stayed_risky { background: #fff0f0; color: #a83030; }
.rice-pill--over_adjusted { background: #fff3e0; color: #a85a00; }
.rice-pill--no_change { background: #f0f0f6; color: #6b6b8c; }

.rice-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;
  margin-bottom: 12px;
}
.rice-table th, .rice-table td {
  text-align: left;
  padding: 8px 10px;
  border-bottom: 1px solid #eee6ff;
  vertical-align: top;
}
.rice-table th {
  color: #6b6b8c;
  font-weight: 600;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: .4px;
}
.rice-table--compact { font-size: 12.5px; margin-bottom: 4px; }
.rice-row--pick {
  background: #eef0ff;
}
.rice-bar {
  display: inline-block;
  width: 80px;
  height: 8px;
  background: #eee6ff;
  border-radius: 4px;
  overflow: hidden;
  vertical-align: middle;
  margin-right: 6px;
}
.rice-bar > span {
  display: block;
  height: 100%;
  background: #6366f1;
}
.rice-bar--rev > span {
  background: #22c55e;
}

.rice-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-top: 10px;
}
@media (max-width: 800px) {
  .rice-cols { grid-template-columns: 1fr; }
}
.rice-roles, .rice-errors {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rice-roles__picks {
  list-style: none;
  padding-left: 14px;
  margin: 4px 0 0;
  font-size: 13px;
  color: #3a3a6b;
}
.rice-errors li {
  display: flex;
  justify-content: space-between;
  padding: 6px 10px;
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 8px;
  font-size: 13px;
}

.rice-participants {
  margin-top: 18px;
  padding-top: 12px;
  border-top: 1px dashed #eee6ff;
}
.rice-fac__participants-toggle {
  background: #fff !important;
  border: 1px solid #eee6ff !important;
  color: #3a3a6b;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background .15s;
}
.rice-fac__participants-toggle:hover {
  background: #f3f3ff !important;
}
.rice-participants__body {
  margin-top: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.rice-part {
  background: #fafaff;
  border: 1px solid #eee6ff;
  border-radius: 10px;
  padding: 8px 12px;
}
.rice-part__toggle {
  background: transparent !important;
  border: none !important;
  width: 100%;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  padding: 4px 0;
  cursor: pointer;
  color: #1f1f3a;
  flex-wrap: wrap;
}
.rice-part__toggle:hover { color: #4f46e5; }
.rice-part__body {
  padding: 10px 0 4px;
  border-top: 1px dashed #eee6ff;
  margin-top: 6px;
}
.rice-part__event {
  background: #eef0ff;
  padding: 8px 12px;
  border-radius: 8px;
  margin-bottom: 10px;
  font-size: 13px;
}
.rice-part__stage { margin-bottom: 10px; }
.rice-part__stage-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #3a3a6b;
  margin-bottom: 6px;
}
.rice-part__errors {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 4px;
}

.btn-ghost {
  background: #fff !important;
  color: #4f46e5 !important;
  border: 1px solid #d8d8f0 !important;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background .15s, transform .1s, box-shadow .15s;
}
.btn-ghost:hover:not(:disabled) {
  background: #f1f1ff !important;
  box-shadow: 0 2px 6px rgba(79, 70, 229, .15);
}
.btn-ghost:active:not(:disabled) { transform: translateY(1px); }
.btn-ghost:disabled {
  opacity: .5;
  cursor: not-allowed;
}
.btn-danger {
  background: #fff !important;
  color: #d03a3a !important;
  border: 1px solid #f1c2c2 !important;
  padding: 8px 14px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  transition: background .15s, color .15s;
}
.btn-danger:hover {
  background: #fbeaea !important;
  color: #a83030 !important;
}
</style>
