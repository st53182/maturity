<template>
  <div class="dd-fac">
    <header class="dd-fac__head">
      <div>
        <h1>📋 {{ $t('agileTraining.dorDod.facTitle') }}</h1>
        <p class="dd-fac__sub">{{ $t('agileTraining.dorDod.facSubtitle') }}</p>
      </div>
      <div>
        <router-link class="dd-fac__back" to="/agile-training">← {{ $t('agileTraining.hub.backHome') }}</router-link>
      </div>
    </header>

    <section v-if="!activeSession" class="dd-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="dd-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle"
               :placeholder="$t('agileTraining.dorDod.newSessionTitle')"
               required maxlength="255" />
        <select v-model="newSessionLocale" class="dd-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="dd-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="dd-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="dd-fac__list">
        <li v-for="s in sessions" :key="s.id" class="dd-fac__item">
          <div class="dd-fac__item-main">
            <div class="dd-fac__item-title">{{ s.title }}</div>
            <div class="dd-fac__item-meta">
              <span class="dd-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="dd-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <section v-else class="dd-fac__section">
      <div class="dd-fac__active-head">
        <div>
          <div class="dd-fac__active-title">{{ activeSession.title }}</div>
          <div class="dd-fac__item-meta">
            <span class="dd-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="dd-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.dorDod.leaderboard') }}
          </button>
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="dd-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="dd-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName"
                 :placeholder="$t('agileTraining.facilitator.newGroupName')"
                 required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="dd-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="dd-fac__groups">
        <li v-for="g in groups" :key="g.id" class="dd-fac__group">
          <div class="dd-fac__group-main">
            <div class="dd-fac__group-name">{{ g.name }}</div>
            <div class="dd-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.dorDod.answersCount', { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
            </div>
            <div class="dd-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="dd-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="dd-fac__group-actions">
            <button class="btn-ghost" @click="openGroupResults(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.reset') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <!-- Модалка: результаты одной группы -->
    <div v-if="resultsModal.open" class="dd-modal" @click.self="closeResults">
      <div class="dd-modal__body">
        <div class="dd-modal__head">
          <h3>{{ $t('agileTraining.dorDod.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="dd-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="dd-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="dd-modal__lead">
            {{ $t('agileTraining.facilitator.participants', { n: resultsModal.data.participants_count || 0 }, resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.dorDod.answersCount', { n: resultsModal.data.answers_count || 0 }, resultsModal.data.answers_count || 0) }}
          </p>

          <div v-for="team in resultsModal.data.teams" :key="team.key"
               class="dd-team" :class="{ 'dd-team--empty': !team.participants }">
            <div class="dd-team__head">
              <div class="dd-team__title">{{ team.title }}</div>
              <span class="dd-pill">
                {{ $t('agileTraining.facilitator.participants', { n: team.participants || 0 }, team.participants || 0) }}
              </span>
              <span v-if="team.participants" class="dd-pill dd-pill--muted">
                {{ $t('agileTraining.dorDod.avgScore') }}:
                <b>{{ team.avg_initial }}</b>
              </span>
            </div>

            <div v-if="team.participants" class="dd-team__body">
              <div class="dd-col">
                <h4>🎯 {{ $t('agileTraining.dorDod.dor') }}</h4>
                <ul class="dd-rules">
                  <li v-for="r in team.rules.filter(x => x.dor_count > 0).sort((a,b) => b.dor_pct - a.dor_pct)"
                      :key="r.key" class="dd-rules__item">
                    <span class="dd-rules__title">
                      {{ r.title }}
                      <span v-if="r.expected_column === 'dod'" class="dd-tag dd-tag--warn">
                        {{ $t('agileTraining.dorDod.usuallyDod') }}
                      </span>
                      <span v-else-if="r.expected_column === 'either'" class="dd-tag dd-tag--neutral">
                        {{ $t('agileTraining.dorDod.eitherShort') }}
                      </span>
                    </span>
                    <span class="dd-rules__bar"><span :style="{ width: r.dor_pct + '%' }"></span></span>
                    <span class="dd-rules__pct">{{ r.dor_pct }}%</span>
                  </li>
                </ul>
              </div>
              <div class="dd-col">
                <h4>✅ {{ $t('agileTraining.dorDod.dod') }}</h4>
                <ul class="dd-rules">
                  <li v-for="r in team.rules.filter(x => x.dod_count > 0).sort((a,b) => b.dod_pct - a.dod_pct)"
                      :key="r.key" class="dd-rules__item">
                    <span class="dd-rules__title">
                      {{ r.title }}
                      <span v-if="r.expected_column === 'dor'" class="dd-tag dd-tag--warn">
                        {{ $t('agileTraining.dorDod.usuallyDor') }}
                      </span>
                      <span v-else-if="r.expected_column === 'either'" class="dd-tag dd-tag--neutral">
                        {{ $t('agileTraining.dorDod.eitherShort') }}
                      </span>
                    </span>
                    <span class="dd-rules__bar dd-rules__bar--dod"><span :style="{ width: r.dod_pct + '%' }"></span></span>
                    <span class="dd-rules__pct">{{ r.dod_pct }}%</span>
                  </li>
                </ul>
              </div>
              <div class="dd-col">
                <h4>💡 {{ $t('agileTraining.dorDod.topEffects') }}</h4>
                <ul class="dd-effects">
                  <li v-for="e in team.effect_picks.filter(x => x.count > 0).sort((a,b) => b.count - a.count)"
                      :key="e.key" :class="{ 'dd-effects__item--prov': e.provocative }"
                      class="dd-effects__item">
                    <span>{{ e.title }}
                      <span v-if="e.provocative" class="dd-tag dd-tag--warn">
                        {{ $t('agileTraining.dorDod.provocative') }}
                      </span>
                    </span>
                    <b>{{ e.pct }}%</b>
                  </li>
                </ul>

                <h4 style="margin-top: 14px;">⚠️ {{ $t('agileTraining.dorDod.antipatternsTop') }}</h4>
                <ul class="dd-ap">
                  <li v-for="(count, key) in team.antipatterns" :key="key">
                    <span>{{ $t('agileTraining.dorDod.ap.' + key) }}</span>
                    <b>{{ count }}</b>
                  </li>
                  <li v-if="Object.keys(team.antipatterns).length === 0" class="dd-fac__hint">
                    — {{ $t('agileTraining.dorDod.noAntipatterns') }}
                  </li>
                </ul>
              </div>
            </div>
            <div v-else class="dd-team__empty">
              {{ $t('agileTraining.dorDod.noParticipantsForTeam') }}
            </div>
          </div>

          <!-- drill-down: per-participant -->
          <div v-if="resultsModal.participants.length" class="dd-participants">
            <button class="dd-fac__participants-toggle" @click="resultsModal.showParticipants = !resultsModal.showParticipants">
              {{ resultsModal.showParticipants ? '▾' : '▸' }}
              {{ $t('agileTraining.dorDod.participantsDrill') }}
              ({{ resultsModal.participants.length }})
            </button>
            <div v-if="resultsModal.showParticipants" class="dd-participants__body">
              <div v-for="p in resultsModal.participants" :key="p.id" class="dd-part">
                <button class="dd-part__toggle" @click="togglePart(p.id)">
                  <span>{{ resultsModal.expanded[p.id] ? '▾' : '▸' }}</span>
                  <b>{{ p.display_name }}</b>
                  <span v-if="p.has_answer" class="dd-pill dd-pill--muted">
                    {{ p.team_title || p.team_key }}
                  </span>
                  <span v-if="p.has_answer" class="dd-pill">
                    {{ $t('agileTraining.dorDod.score') }}:
                    {{ p.score_initial }}
                  </span>
                  <span v-if="p.has_answer && p.outcome_initial"
                        class="dd-pill" :class="outcomeClass(p.outcome_initial)">
                    {{ $t('agileTraining.dorDod.outcome.' + p.outcome_initial) }}
                  </span>
                  <span v-if="!p.has_answer" class="dd-pill dd-pill--muted">
                    {{ $t('agileTraining.dorDod.noAnswer') }}
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id] && p.has_answer" class="dd-part__body">
                  <template v-for="stage in ['initial']" :key="stage">
                  <div v-if="p[stage]" class="dd-part__stage">
                    <div class="dd-part__stage-title">
                      {{ $t('agileTraining.dorDod.round.' + stage) }}
                    </div>
                    <div class="dd-part__cols">
                      <div>
                        <div class="dd-part__col-title">🎯 DoR</div>
                        <ul><li v-for="r in p[stage].dor" :key="r.key">{{ r.title }}</li>
                          <li v-if="!p[stage].dor.length" class="dd-fac__hint">—</li></ul>
                      </div>
                      <div>
                        <div class="dd-part__col-title">✅ DoD</div>
                        <ul><li v-for="r in p[stage].dod" :key="r.key">{{ r.title }}</li>
                          <li v-if="!p[stage].dod.length" class="dd-fac__hint">—</li></ul>
                      </div>
                      <div>
                        <div class="dd-part__col-title">💡 {{ $t('agileTraining.dorDod.mapping') }}</div>
                        <ul>
                          <li v-for="(effs, rk) in p[stage].mapping" :key="rk">
                            <b>{{ ruleTitle(rk) }}</b>:
                            <span v-for="(e, i) in effs" :key="e.key">
                              <span :class="{ 'dd-provocative': e.provocative }">{{ e.title }}</span><span v-if="i < effs.length - 1">, </span>
                            </span>
                            <span v-if="!effs.length" class="dd-fac__hint">—</span>
                          </li>
                          <li v-if="!Object.keys(p[stage].mapping).length" class="dd-fac__hint">—</li>
                        </ul>
                      </div>
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
    <div v-if="compareAll.open" class="dd-modal" @click.self="closeCompareAll">
      <div class="dd-modal__body dd-modal__body--wide">
        <div class="dd-modal__head">
          <h3>🏁 {{ $t('agileTraining.dorDod.leaderboard') }}</h3>
          <button class="dd-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="dd-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <div class="dd-leaderboard">
            <div class="dd-leaderboard__col">
              <h4>🏆 {{ $t('agileTraining.dorDod.bestHealth') }}</h4>
              <ol>
                <li v-for="(g, idx) in (compareAll.data.leaderboard_best || []).slice(0, 5)" :key="g.id">
                  <b>{{ idx + 1 }}.</b> {{ g.name }} · {{ g.health_pct }}%
                  <span class="dd-fac__hint">
                    (avg {{ g.avg_initial }})
                  </span>
                </li>
              </ol>
            </div>
          </div>

          <h4 class="dd-section-title">📊 {{ $t('agileTraining.dorDod.groupScoreboard') }}</h4>
          <table class="dd-heatmap">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                <th>{{ $t('agileTraining.facilitator.participants', { n: 2 }, 2) }}</th>
                <th>{{ $t('agileTraining.dorDod.scoreInitial') }}</th>
                <th>{{ $t('agileTraining.dorDod.healthPct') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in compareAll.data.groups" :key="g.id">
                <td><b>{{ g.name }}</b></td>
                <td>{{ g.participants_count }}</td>
                <td>{{ g.avg_initial }}</td>
                <td :class="heatmapClass(g.health_pct)">{{ g.health_pct }}%</td>
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
  name: 'AgileDorDodFacilitator',
  data() {
    return {
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: (typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en') ? 'en' : 'ru',
      activeSession: null,
      newGroupName: '',
      copiedSlug: '',
      resultsModal: { open: false, group: null, loading: false, data: null, participants: [], expanded: {}, showParticipants: false },
      compareAll: { open: false, loading: false, data: null },
      rulesIndex: {},
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
        return new Date(iso).toLocaleDateString(this.$i18n?.locale === 'en' ? 'en-US' : 'ru-RU',
          { day: '2-digit', month: 'short', year: 'numeric' });
      } catch (_) { return iso; }
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || []).filter(s => s.exercise_key === 'dor_dod');
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const r = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'dor_dod' },
          { headers: this.authHeaders() });
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
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed'); }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmResetGroup', { name: g.name }))) return;
      try {
        await axios.post(`/api/agile-training/dor-dod/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
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
      this.resultsModal = { open: true, group: g, loading: true, data: null, participants: [], expanded: {}, showParticipants: false };
      try {
        const r = await axios.get(`/api/agile-training/dor-dod/groups/${g.id}/results`, {
          headers: this.authHeaders(),
          params: { locale: this.activeSession?.locale || 'ru' },
        });
        this.resultsModal.data = r.data;
        // build rule title index for participant drill-down
        const ri = {};
        for (const team of r.data.teams) {
          for (const rule of team.rules) { ri[rule.key] = rule.title; }
        }
        this.rulesIndex = ri;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed');
        this.resultsModal.open = false;
      } finally {
        this.resultsModal.loading = false;
      }
      try {
        const parts = await axios.get(`/api/agile-training/dor-dod/groups/${g.id}/participants`, {
          headers: this.authHeaders(),
          params: { locale: this.activeSession?.locale || 'ru' },
        });
        this.resultsModal.participants = parts.data.participants || [];
      } catch (e) {
        this.resultsModal.participants = [];
      }
    },
    togglePart(id) {
      this.resultsModal.expanded = { ...this.resultsModal.expanded, [id]: !this.resultsModal.expanded[id] };
    },
    closeResults() {
      this.resultsModal = { open: false, group: null, loading: false, data: null, participants: [], expanded: {}, showParticipants: false };
    },
    async openCompareAll() {
      if (!this.activeSession) return;
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const r = await axios.get(
          `/api/agile-training/dor-dod/sessions/${this.activeSession.id}/results`,
          { headers: this.authHeaders(), params: { locale: this.activeSession.locale || 'ru' } },
        );
        this.compareAll.data = r.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed');
        this.compareAll.open = false;
      } finally { this.compareAll.loading = false; }
    },
    closeCompareAll() { this.compareAll = { open: false, loading: false, data: null }; },
    heatmapClass(pct) {
      if (pct >= 75) return 'dd-heat--hot';
      if (pct >= 50) return 'dd-heat--warm';
      if (pct >= 25) return 'dd-heat--cool';
      return 'dd-heat--cold';
    },
    outcomeClass(o) {
      if (o === 'predictable') return 'dd-pill--good';
      if (o === 'stable') return 'dd-pill--good';
      if (o === 'rework_heavy') return 'dd-pill--warn';
      if (o === 'blocked') return 'dd-pill--bad';
      return '';
    },
    ruleTitle(key) { return this.rulesIndex[key] || key; },
  },
};
</script>

<style scoped>
.dd-fac { max-width: 1120px; margin: 0 auto; padding: 24px 20px 80px; color: #0f172a; }
.dd-fac__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.dd-fac__head h1 { margin: 0 0 6px; font-size: 26px; }
.dd-fac__sub { color: #475569; margin: 0; font-size: 14px; }
.dd-fac__back { color: #0f172a; text-decoration: none; font-weight: 600; font-size: 14px; }
.dd-fac__section { margin-bottom: 28px; }
.dd-fac__section h2 { font-size: 18px; margin-bottom: 10px; }

.dd-fac__create, .dd-fac__add-group { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.dd-fac__create input, .dd-fac__add-group input {
  flex: 1; min-width: 220px; padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1;
  font-size: 14px; background: #fff;
}
.dd-fac__locale { padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; }
.dd-fac__create button, .dd-fac__add-group button {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important; border: none !important; border-radius: 10px !important;
  padding: 10px 18px !important; font-weight: 600; cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.dd-fac__create button:hover:not(:disabled), .dd-fac__add-group button:hover:not(:disabled) {
  transform: translateY(-1px); box-shadow: 0 8px 18px rgba(8, 145, 178, 0.3);
}
.dd-fac__create button:active:not(:disabled), .dd-fac__add-group button:active:not(:disabled) {
  transform: translateY(0); box-shadow: 0 4px 8px rgba(8, 145, 178, 0.25);
}

.dd-fac__hint { color: #64748b; font-size: 13px; }
.dd-fac__empty { color: #64748b; font-style: italic; padding: 12px 0; }
.dd-fac__list, .dd-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.dd-fac__item, .dd-fac__group { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.dd-fac__item-main, .dd-fac__group-main { flex: 1; min-width: 220px; }
.dd-fac__item-title, .dd-fac__group-name { font-weight: 600; color: #0f172a; }
.dd-fac__item-meta { display: flex; gap: 8px; align-items: center; color: #64748b; font-size: 12px; flex-wrap: wrap; margin-top: 4px; }
.dd-fac__badge { background: #ccfbf1; color: #0f766e; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.dd-fac__open-btn {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important; border: none !important; border-radius: 10px !important;
  padding: 8px 16px !important; font-weight: 600; cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.dd-fac__open-btn:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 6px 14px rgba(8, 145, 178, 0.3); }
.dd-fac__open-btn:active:not(:disabled) { transform: translateY(0); }
.dd-fac__link { display: flex; gap: 8px; align-items: center; margin-top: 8px; flex-wrap: wrap; }
.dd-fac__link code { background: #f1f5f9; padding: 4px 8px; border-radius: 6px; font-size: 12px; }
.dd-fac__copy {
  background: #e2e8f0 !important; color: #0f172a !important; border: none !important;
  border-radius: 8px !important; padding: 4px 10px !important; font-size: 12px; font-weight: 600;
  cursor: pointer; transition: background 0.15s ease;
}
.dd-fac__copy:hover { background: #cbd5e1 !important; }

.dd-fac__active-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 16px; }
.dd-fac__active-title { font-size: 20px; font-weight: 700; }
.dd-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.dd-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap; }
.dd-fac__group-actions { display: flex; gap: 8px; flex-wrap: wrap; }

.dd-fac__participants-toggle {
  background: transparent !important; color: #0f766e !important;
  border: 1px dashed #14b8a6 !important; border-radius: 8px !important;
  padding: 6px 12px !important; font-weight: 600; cursor: pointer;
  transition: background 0.15s ease;
}
.dd-fac__participants-toggle:hover { background: #f0fdfa !important; }

/* modal */
.dd-modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.6); display: flex; align-items: flex-start; justify-content: center; padding: 40px 16px; z-index: 1000; overflow-y: auto; }
.dd-modal__body { background: #fff; border-radius: 16px; max-width: 980px; width: 100%; padding: 24px; }
.dd-modal__body--wide { max-width: 1100px; }
.dd-modal__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.dd-modal__close {
  background: #e2e8f0 !important; color: #0f172a !important; border: none !important;
  border-radius: 50% !important; width: 32px !important; height: 32px !important; font-size: 16px;
  cursor: pointer; transition: background 0.15s ease;
}
.dd-modal__close:hover { background: #cbd5e1 !important; }
.dd-modal__lead { color: #475569; margin: 0 0 14px; font-size: 13px; }

.dd-pill { background: #ccfbf1; color: #0f766e; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.dd-pill--muted { background: #e2e8f0; color: #334155; }
.dd-pill--good { background: #d1fae5; color: #065f46; }
.dd-pill--warn { background: #fef3c7; color: #92400e; }
.dd-pill--bad { background: #fee2e2; color: #991b1b; }

.dd-team { border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; margin-bottom: 14px; }
.dd-team--empty { opacity: 0.6; }
.dd-team__head { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.dd-team__title { font-weight: 700; font-size: 15px; margin-right: 8px; }
.dd-team__body { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 14px; }
.dd-team__empty { color: #64748b; font-style: italic; }
@media (max-width: 860px) { .dd-team__body { grid-template-columns: 1fr; } }
.dd-col h4 { margin: 0 0 8px; font-size: 13px; color: #334155; }
.dd-rules { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.dd-rules__item { display: grid; grid-template-columns: 1fr 80px 36px; gap: 8px; align-items: center; font-size: 13px; }
.dd-rules__title { color: #0f172a; }
.dd-rules__bar { background: #e2e8f0; border-radius: 999px; height: 8px; overflow: hidden; }
.dd-rules__bar span { display: block; height: 100%; background: linear-gradient(90deg, #14b8a6, #0891b2); border-radius: 999px; }
.dd-rules__bar--dod span { background: linear-gradient(90deg, #22c55e, #16a34a); }
.dd-rules__pct { font-size: 11px; color: #64748b; text-align: right; }
.dd-effects { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.dd-effects__item { display: flex; justify-content: space-between; gap: 8px; font-size: 13px; padding: 4px 8px; border-radius: 6px; background: #f8fafc; }
.dd-effects__item--prov { background: #fff7ed; }
.dd-ap { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.dd-ap li { display: flex; justify-content: space-between; font-size: 12px; color: #991b1b; background: #fef2f2; padding: 4px 8px; border-radius: 6px; }

.dd-tag { font-size: 10px; padding: 2px 6px; border-radius: 999px; margin-left: 4px; font-weight: 700; }
.dd-tag--warn { background: #fef3c7; color: #92400e; }
.dd-tag--neutral { background: #e2e8f0; color: #334155; }

/* participants drill-down */
.dd-participants { margin-top: 14px; border-top: 1px dashed #e2e8f0; padding-top: 12px; }
.dd-participants__body { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.dd-part { border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; }
.dd-part__toggle {
  background: transparent !important; border: none !important; width: 100%;
  display: flex; align-items: center; gap: 8px; padding: 10px 14px;
  cursor: pointer; text-align: left; flex-wrap: wrap; font-size: 13px;
}
.dd-part__toggle:hover { background: #eefdfa !important; }
.dd-part__body { padding: 0 14px 14px; }
.dd-part__stage { border-top: 1px dashed #e2e8f0; padding-top: 10px; margin-top: 10px; }
.dd-part__stage-title { font-weight: 700; font-size: 13px; margin-bottom: 6px; color: #0f766e; }
.dd-part__cols { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; font-size: 12px; }
.dd-part__cols ul { list-style: disc; padding-left: 18px; margin: 0; }
.dd-part__col-title { font-weight: 600; margin-bottom: 4px; }
.dd-provocative { color: #9a3412; }
@media (max-width: 720px) { .dd-part__cols { grid-template-columns: 1fr; } }

/* leaderboard */
.dd-leaderboard { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; margin-bottom: 20px; }
@media (max-width: 760px) { .dd-leaderboard { grid-template-columns: 1fr; } }
.dd-leaderboard__col h4 { margin: 0 0 8px; font-size: 14px; }
.dd-leaderboard__col ol { padding-left: 20px; margin: 0; display: flex; flex-direction: column; gap: 4px; font-size: 13px; }
.dd-section-title { margin: 6px 0 8px; font-size: 14px; }
.dd-heatmap { width: 100%; border-collapse: collapse; font-size: 13px; }
.dd-heatmap th, .dd-heatmap td { border: 1px solid #e2e8f0; padding: 8px 10px; text-align: center; }
.dd-heatmap th { background: #f1f5f9; }
.dd-heat--hot { background: #d1fae5; color: #065f46; font-weight: 700; }
.dd-heat--warm { background: #fef9c3; color: #713f12; font-weight: 600; }
.dd-heat--cool { background: #fde68a; color: #78350f; }
.dd-heat--cold { background: #fee2e2; color: #991b1b; font-weight: 600; }
</style>
