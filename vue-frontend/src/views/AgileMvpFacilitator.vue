<template>
  <div class="mvp-fac">
    <header class="mvp-fac__head">
      <div>
        <h1>🚀 {{ $t('agileTraining.mvp.facTitle') }}</h1>
        <p class="mvp-fac__sub">{{ $t('agileTraining.mvp.facSubtitle') }}</p>
      </div>
      <div class="mvp-fac__head-actions">
        <router-link class="mvp-fac__back" to="/agile-training">← {{ $t('agileTraining.hub.backHome') }}</router-link>
      </div>
    </header>

    <section v-if="!activeSession" class="mvp-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="mvp-fac__create" @submit.prevent="createSession">
        <input
          v-model="newSessionTitle"
          :placeholder="$t('agileTraining.mvp.newSessionTitle')"
          required
          maxlength="255"
        />
        <select v-model="newSessionLocale" class="mvp-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="mvp-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="mvp-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="mvp-fac__list">
        <li v-for="s in sessions" :key="s.id" class="mvp-fac__item">
          <div class="mvp-fac__item-main">
            <div class="mvp-fac__item-title">{{ s.title }}</div>
            <div class="mvp-fac__item-meta">
              <span class="mvp-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="mvp-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <section v-else class="mvp-fac__section">
      <div class="mvp-fac__active-head">
        <div>
          <div class="mvp-fac__active-title">{{ activeSession.title }}</div>
          <div class="mvp-fac__item-meta">
            <span class="mvp-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="mvp-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.mvp.leaderboard') }}
          </button>
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="mvp-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="mvp-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="mvp-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="mvp-fac__groups">
        <li v-for="g in groups" :key="g.id" class="mvp-fac__group">
          <div class="mvp-fac__group-main">
            <div class="mvp-fac__group-name">{{ g.name }}</div>
            <div class="mvp-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.mvp.answersCount', { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.mvp.avgScore') }}: <b>{{ g.avg_score || 0 }}</b></span>
            </div>
            <div class="mvp-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="mvp-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="mvp-fac__group-actions">
            <button class="btn-ghost" @click="openGroupResults(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.reset') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <!-- Модалка: результаты одной группы -->
    <div v-if="resultsModal.open" class="mvp-modal" @click.self="closeResults">
      <div class="mvp-modal__body">
        <div class="mvp-modal__head">
          <h3>{{ $t('agileTraining.mvp.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="mvp-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="mvp-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="mvp-modal__lead">
            {{ $t('agileTraining.facilitator.participants', { n: resultsModal.data.participants_count || 0 }, resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.mvp.answersCount', { n: resultsModal.data.answers_count || 0 }, resultsModal.data.answers_count || 0) }}
            · {{ $t('agileTraining.mvp.avgScore') }}: <b>{{ resultsModal.data.avg_score || 0 }}</b>
          </p>

          <div v-for="row in resultsModal.data.per_case" :key="row.key" class="mvp-case-row">
            <div class="mvp-case-row__head">
              <div class="mvp-case-row__title">
                <span class="mvp-case-row__cat">{{ row.category }}</span>
                <b>{{ row.title }}</b>
              </div>
              <span class="mvp-pill">
                {{ $t('agileTraining.mvp.answersCount', { n: row.total_answers || 0 }, row.total_answers || 0) }}
              </span>
            </div>
            <p class="mvp-case-row__hyp"><b>💡</b> {{ row.hypothesis }}</p>

            <div class="mvp-stages">
              <div v-for="stage in STAGES" :key="stage" class="mvp-stage-col">
                <div class="mvp-stage-col__head">{{ $t('agileTraining.mvp.stage.' + stage) }}</div>
                <div class="mvp-status-bars">
                  <div class="mvp-status-bars__row">
                    <div class="mvp-status-bars__label mvp-status-bars__label--ok">✅</div>
                    <div class="mvp-status-bars__track">
                      <div class="mvp-status-bars__fill mvp-status-bars__fill--ok"
                           :style="{ width: (row.stage_status[stage].pct.success || 0) + '%' }" />
                    </div>
                    <div class="mvp-status-bars__val">{{ row.stage_status[stage].pct.success || 0 }}%</div>
                  </div>
                  <div class="mvp-status-bars__row">
                    <div class="mvp-status-bars__label mvp-status-bars__label--mid">➖</div>
                    <div class="mvp-status-bars__track">
                      <div class="mvp-status-bars__fill mvp-status-bars__fill--mid"
                           :style="{ width: (row.stage_status[stage].pct.partial || 0) + '%' }" />
                    </div>
                    <div class="mvp-status-bars__val">{{ row.stage_status[stage].pct.partial || 0 }}%</div>
                  </div>
                  <div class="mvp-status-bars__row">
                    <div class="mvp-status-bars__label mvp-status-bars__label--bad">❌</div>
                    <div class="mvp-status-bars__track">
                      <div class="mvp-status-bars__fill mvp-status-bars__fill--bad"
                           :style="{ width: (row.stage_status[stage].pct.fail || 0) + '%' }" />
                    </div>
                    <div class="mvp-status-bars__val">{{ row.stage_status[stage].pct.fail || 0 }}%</div>
                  </div>
                </div>
              </div>
            </div>

            <div class="mvp-features">
              <div class="mvp-features__title">{{ $t('agileTraining.mvp.featurePicksTitle') }}</div>
              <ul class="mvp-features__list">
                <li v-for="f in sortedFeatures(row.features)" :key="f.key" class="mvp-features__item">
                  <span :class="['mvp-feat-tag', 'mvp-feat-tag--' + f.weight]">
                    {{ $t('agileTraining.mvp.weight.' + f.weight) }}
                  </span>
                  <span class="mvp-features__name">{{ f.title }}</span>
                  <div class="mvp-features__bar">
                    <div class="mvp-features__fill" :style="{ width: f.pct + '%' }" />
                  </div>
                  <span class="mvp-features__pct">{{ f.pct }}%</span>
                </li>
              </ul>
            </div>
          </div>

          <section class="mvp-participants">
            <h4>👥 {{ $t('agileTraining.facilitator.participantsTitle') }}</h4>
            <p class="mvp-modal__lead">{{ $t('agileTraining.facilitator.participantsLead') }}</p>
            <p v-if="!resultsModal.participants.length" class="mvp-fac__hint">
              {{ $t('agileTraining.facilitator.participantsEmpty') }}
            </p>
            <ul v-else class="mvp-participants__list">
              <li v-for="p in resultsModal.participants" :key="'mpp-'+p.id" class="mvp-participants__item">
                <button
                  type="button"
                  class="mvp-fac__participants-toggle"
                  :class="{ 'is-open': !!resultsModal.expanded[p.id] }"
                  @click="toggleParticipant(p.id)"
                >
                  <span class="mvp-participants__name">
                    <span class="mvp-participants__avatar">{{ (p.display_name || p.anonymous_label).slice(0,2).toUpperCase() }}</span>
                    <span>{{ p.display_name || $t('agileTraining.facilitator.anonymous') }}</span>
                    <span class="mvp-participants__anon">{{ p.anonymous_label }}</span>
                  </span>
                  <span class="mvp-participants__stats">
                    <span class="mvp-pill">{{ $t('agileTraining.facilitator.casesAnswered', { n: p.cases_answered }) }}</span>
                    <span class="mvp-pill mvp-pill--score">{{ $t('agileTraining.mvp.totalScore') }}: {{ p.total_score }}</span>
                    <span class="mvp-participants__arrow">{{ resultsModal.expanded[p.id] ? '−' : '+' }}</span>
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id]" class="mvp-participants__body">
                  <p v-if="!p.answers.length" class="mvp-fac__hint">
                    {{ $t('agileTraining.facilitator.noAnswersForParticipant') }}
                  </p>
                  <ol v-else class="mvp-participants__cases">
                    <li v-for="a in p.answers" :key="'mpa-'+p.id+'-'+a.case_key" class="mvp-participants__case">
                      <div class="mvp-participants__case-head">
                        <span class="mvp-case-row__cat" v-if="a.case_category">{{ a.case_category }}</span>
                        <strong>{{ a.case_title }}</strong>
                        <span class="mvp-pill mvp-pill--score">{{ $t('agileTraining.mvp.totalScore') }}: {{ a.total_score }}</span>
                      </div>
                      <div class="mvp-participants__stages">
                        <div v-for="stage in STAGES" :key="'pst-'+p.id+'-'+a.case_key+'-'+stage" class="mvp-participants__stage">
                          <div class="mvp-participants__stage-head">
                            <strong>{{ $t('agileTraining.mvp.stage.' + stage) }}</strong>
                            <span v-if="a.stages[stage] && a.stages[stage].status"
                                  :class="['mvp-badge-status', 'mvp-badge-status--' + a.stages[stage].status]">
                              {{ $t('agileTraining.mvp.status.' + a.stages[stage].status) }}
                            </span>
                            <span v-else class="mvp-fac__hint">—</span>
                          </div>
                          <div v-if="a.stages[stage] && a.stages[stage].features.length" class="mvp-participants__chips">
                            <span
                              v-for="f in a.stages[stage].features"
                              :key="'pfc-'+p.id+'-'+a.case_key+'-'+stage+'-'+f.key"
                              :class="['mvp-feat-chip', 'mvp-feat-chip--' + f.weight]"
                              :title="f.weight"
                            >
                              {{ f.title }}
                            </span>
                          </div>
                        </div>
                      </div>
                    </li>
                  </ol>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>

    <!-- Модалка: сравнение всех групп / leaderboard -->
    <div v-if="compareAll.open" class="mvp-modal" @click.self="closeCompareAll">
      <div class="mvp-modal__body mvp-modal__body--wide">
        <div class="mvp-modal__head">
          <h3>🏁 {{ $t('agileTraining.mvp.leaderboardTitle') }}</h3>
          <button class="mvp-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="mvp-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="mvp-modal__lead">{{ $t('agileTraining.mvp.leaderboardLead') }}</p>

          <div class="mvp-totals">
            <div class="mvp-totals__item">
              <span class="mvp-totals__val">{{ compareAll.data.totals.groups }}</span>
              <span class="mvp-totals__lbl">{{ $t('agileTraining.facilitator.totalsGroups') }}</span>
            </div>
            <div class="mvp-totals__item">
              <span class="mvp-totals__val">{{ compareAll.data.totals.participants }}</span>
              <span class="mvp-totals__lbl">{{ $t('agileTraining.facilitator.totalsParticipants') }}</span>
            </div>
            <div class="mvp-totals__item">
              <span class="mvp-totals__val">{{ compareAll.data.totals.answers }}</span>
              <span class="mvp-totals__lbl">{{ $t('agileTraining.facilitator.totalsAnswers') }}</span>
            </div>
          </div>

          <div class="mvp-leaderboards">
            <div class="mvp-leaderboard">
              <h4>⚡ {{ $t('agileTraining.mvp.fastestHypothesis') }}</h4>
              <p class="mvp-fac__hint">{{ $t('agileTraining.mvp.fastestHypothesisHint') }}</p>
              <ol class="mvp-leaderboard__list">
                <li v-for="g in compareAll.data.leaderboard_fastest" :key="'lf-'+g.id">
                  <span class="mvp-leaderboard__name">{{ g.name }}</span>
                  <span class="mvp-leaderboard__val">{{ g.stage_success_pct.mvp }}%</span>
                </li>
              </ol>
            </div>

            <div class="mvp-leaderboard">
              <h4>🏆 {{ $t('agileTraining.mvp.bestProduct') }}</h4>
              <p class="mvp-fac__hint">{{ $t('agileTraining.mvp.bestProductHint') }}</p>
              <ol class="mvp-leaderboard__list">
                <li v-for="g in compareAll.data.leaderboard_best" :key="'lb-'+g.id">
                  <span class="mvp-leaderboard__name">{{ g.name }}</span>
                  <span class="mvp-leaderboard__val">{{ g.avg_score }}</span>
                </li>
              </ol>
            </div>
          </div>

          <h4 class="mvp-section-title">📊 {{ $t('agileTraining.mvp.groupScoreboard') }}</h4>
          <table class="mvp-heatmap">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                <th v-for="stage in STAGES" :key="stage">{{ $t('agileTraining.mvp.stage.' + stage) }}</th>
                <th>{{ $t('agileTraining.mvp.avgScore') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="g in compareAll.data.groups" :key="g.id">
                <td><b>{{ g.name }}</b></td>
                <td v-for="stage in STAGES" :key="stage" :class="heatmapClass(g.stage_success_pct[stage])">
                  {{ g.stage_success_pct[stage] }}%
                </td>
                <td><b>{{ g.avg_score }}</b></td>
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

const STAGES = ['mvp', 'mmp', 'mlp'];

export default {
  name: 'AgileMvpFacilitator',
  data() {
    return {
      STAGES,
      loadingSessions: false,
      sessions: [],
      newSessionTitle: '',
      newSessionLocale: (typeof localStorage !== 'undefined' && localStorage.getItem('language') === 'en') ? 'en' : 'ru',
      activeSession: null,
      newGroupName: '',
      copiedSlug: '',
      resultsModal: { open: false, group: null, loading: false, data: null, participants: [], expanded: {} },
      compareAll: { open: false, loading: false, data: null },
    };
  },
  computed: {
    groups() {
      return (this.activeSession && this.activeSession.groups) || [];
    },
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    publicLink(slug) { return `${window.location.origin}/g/${slug}`; },
    formatDate(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleDateString(this.$i18n?.locale === 'en' ? 'en-US' : 'ru-RU',
          { day: '2-digit', month: 'short', year: 'numeric' });
      } catch (e) { return iso; }
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'mvp');
      } catch (e) {
        console.error('load sessions error', e);
      } finally {
        this.loadingSessions = false;
      }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const res = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'mvp' },
          { headers: this.authHeaders() });
        this.newSessionTitle = '';
        await this.loadSessions();
        await this.openSession(res.data.id);
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to create session');
      }
    },
    async openSession(id) {
      try {
        const res = await axios.get(`/api/agile-training/sessions/${id}`, { headers: this.authHeaders() });
        this.activeSession = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load session');
      }
    },
    closeSession() { this.activeSession = null; },
    async deleteSession() {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this.authHeaders() });
        this.activeSession = null;
        await this.loadSessions();
      } catch (e) { alert(e.response?.data?.error || 'Failed to delete'); }
    },
    async addGroup() {
      const name = this.newGroupName.trim();
      if (!name) return;
      try {
        await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`,
          { name }, { headers: this.authHeaders() });
        this.newGroupName = '';
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed to add group'); }
    },
    async removeGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed to delete group'); }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmResetGroup', { name: g.name }))) return;
      try {
        await axios.post(`/api/agile-training/mvp/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
        await this.openSession(this.activeSession.id);
      } catch (e) { alert(e.response?.data?.error || 'Failed to reset'); }
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
    sortedFeatures(features) {
      const weightOrder = { critical: 0, improve: 1, optional: 2 };
      return [...features].sort((a, b) => {
        const w = (weightOrder[a.weight] ?? 3) - (weightOrder[b.weight] ?? 3);
        if (w !== 0) return w;
        return (b.pct || 0) - (a.pct || 0);
      });
    },
    async openGroupResults(g) {
      this.resultsModal = { open: true, group: g, loading: true, data: null, participants: [], expanded: {} };
      try {
        const res = await axios.get(`/api/agile-training/mvp/groups/${g.id}/results`, {
          headers: this.authHeaders(),
          params: { locale: this.activeSession?.locale || 'ru' },
        });
        this.resultsModal.data = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load results');
        this.resultsModal.open = false;
      } finally {
        this.resultsModal.loading = false;
      }
      try {
        const parts = await axios.get(`/api/agile-training/mvp/groups/${g.id}/participants`,
          { headers: this.authHeaders() });
        this.resultsModal.participants = parts.data.participants || [];
      } catch (e) {
        this.resultsModal.participants = [];
      }
    },
    toggleParticipant(pid) {
      const cur = !!this.resultsModal.expanded[pid];
      this.resultsModal.expanded = { ...this.resultsModal.expanded, [pid]: !cur };
    },
    closeResults() {
      this.resultsModal = { open: false, group: null, loading: false, data: null, participants: [], expanded: {} };
    },
    async openCompareAll() {
      if (!this.activeSession) return;
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const res = await axios.get(
          `/api/agile-training/mvp/sessions/${this.activeSession.id}/results`,
          { headers: this.authHeaders(), params: { locale: this.activeSession.locale || 'ru' } },
        );
        this.compareAll.data = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load comparison');
        this.compareAll.open = false;
      } finally {
        this.compareAll.loading = false;
      }
    },
    closeCompareAll() { this.compareAll = { open: false, loading: false, data: null }; },
    heatmapClass(pct) {
      if (pct >= 75) return 'mvp-heat--hot';
      if (pct >= 50) return 'mvp-heat--warm';
      if (pct >= 25) return 'mvp-heat--cool';
      return 'mvp-heat--cold';
    },
  },
};
</script>

<style scoped>
.mvp-fac { max-width: 1120px; margin: 0 auto; padding: 24px 20px 80px; color: #0f172a; }
.mvp-fac__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.mvp-fac__head h1 { margin: 0 0 6px; font-size: 26px; }
.mvp-fac__sub { color: #475569; margin: 0; font-size: 14px; }
.mvp-fac__back { color: #0f172a; text-decoration: none; font-weight: 600; font-size: 14px; }
.mvp-fac__section { margin-bottom: 28px; }
.mvp-fac__section h2 { font-size: 18px; margin-bottom: 10px; }

.mvp-fac__create, .mvp-fac__add-group { display: flex; gap: 8px; align-items: center; margin-bottom: 14px; flex-wrap: wrap; }
.mvp-fac__create input, .mvp-fac__add-group input {
  flex: 1; min-width: 220px; padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1;
  font-size: 14px; background: #fff;
}
.mvp-fac__locale { padding: 10px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; }
.mvp-fac__create button, .mvp-fac__add-group button {
  background: linear-gradient(135deg, #fb923c, #f97316) !important;
  color: #fff !important; border: none !important; border-radius: 10px !important;
  padding: 10px 18px !important; font-weight: 600; cursor: pointer;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.mvp-fac__create button:hover:not(:disabled), .mvp-fac__add-group button:hover:not(:disabled) {
  transform: translateY(-1px); box-shadow: 0 8px 18px rgba(249, 115, 22, 0.3);
}
.mvp-fac__create button:active:not(:disabled), .mvp-fac__add-group button:active:not(:disabled) {
  transform: translateY(0); box-shadow: 0 4px 8px rgba(249, 115, 22, 0.25);
}

.mvp-fac__hint { color: #64748b; font-size: 13px; }
.mvp-fac__empty { color: #64748b; font-style: italic; padding: 12px 0; }
.mvp-fac__list, .mvp-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.mvp-fac__item, .mvp-fac__group { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 14px 16px; display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.mvp-fac__item-main, .mvp-fac__group-main { flex: 1; min-width: 220px; }
.mvp-fac__item-title, .mvp-fac__group-name { font-weight: 600; color: #0f172a; }
.mvp-fac__item-meta { display: flex; gap: 8px; align-items: center; color: #64748b; font-size: 12px; flex-wrap: wrap; margin-top: 4px; }
.mvp-fac__badge { background: #ffedd5; color: #9a3412; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.mvp-fac__open-btn {
  background: linear-gradient(135deg, #fb923c, #f97316) !important;
  color: #fff !important; border: none !important; border-radius: 10px !important;
  padding: 8px 18px !important; cursor: pointer; font-weight: 600;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}
.mvp-fac__open-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(249, 115, 22, 0.3); }

.mvp-fac__link { display: flex; align-items: center; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.mvp-fac__link code { background: #f8fafc; padding: 4px 8px; border-radius: 8px; font-size: 12px; color: #334155; }
.mvp-fac__copy {
  background: #fff !important; color: #9a3412 !important;
  border: 1px solid #fdba74 !important; border-radius: 8px !important;
  padding: 4px 12px !important; cursor: pointer; font-size: 12px; font-weight: 600;
  transition: all 0.15s ease;
}
.mvp-fac__copy:hover:not(:disabled) { background: #fff7ed !important; }

.mvp-fac__active-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 16px; flex-wrap: wrap; }
.mvp-fac__active-title { font-size: 22px; font-weight: 700; }
.mvp-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.mvp-fac__groups-head { display: flex; justify-content: space-between; align-items: flex-end; gap: 12px; flex-wrap: wrap; margin-bottom: 12px; }
.mvp-fac__groups-head h3 { margin: 0; }
.mvp-fac__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.btn-ghost { background: #fff; color: #0f172a; border: 1px solid #cbd5e1; border-radius: 10px; padding: 8px 14px; cursor: pointer; font-size: 13px; transition: all 0.15s ease; }
.btn-ghost:hover:not(:disabled) { background: #fff7ed; border-color: #fdba74; color: #9a3412; }
.btn-ghost:active:not(:disabled) { background: #ffedd5; }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { background: #fff; color: #b91c1c; border: 1px solid #fca5a5; border-radius: 10px; padding: 8px 14px; cursor: pointer; font-size: 13px; transition: all 0.15s ease; }
.btn-danger:hover:not(:disabled) { background: #fee2e2; border-color: #ef4444; }

/* Modal */
.mvp-modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55); display: flex; align-items: flex-start; justify-content: center; z-index: 100; padding: 20px; overflow-y: auto; }
.mvp-modal__body { background: #fff; border-radius: 18px; max-width: 820px; width: 100%; padding: 22px; margin: 40px auto; box-shadow: 0 25px 50px rgba(0,0,0,0.3); max-height: calc(100vh - 80px); overflow-y: auto; }
.mvp-modal__body--wide { max-width: 960px; }
.mvp-modal__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 12px; }
.mvp-modal__head h3 { margin: 0; font-size: 20px; }
.mvp-modal__close {
  background: transparent !important; border: none !important;
  color: #64748b !important; font-size: 24px; cursor: pointer; line-height: 1;
  padding: 4px 10px !important; box-shadow: none !important;
}
.mvp-modal__close:hover { color: #0f172a !important; }
.mvp-modal__lead { color: #475569; margin: 0 0 14px; font-size: 14px; }

.mvp-section-title { margin: 18px 0 8px; font-size: 16px; }

.mvp-case-row { background: #fff7ed; border-radius: 14px; padding: 14px 16px; margin-bottom: 14px; border: 1px solid #fed7aa; }
.mvp-case-row__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.mvp-case-row__cat { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #fdba74; color: #7c2d12; font-size: 11px; font-weight: 700; text-transform: uppercase; margin-right: 6px; }
.mvp-case-row__hyp { color: #475569; margin: 6px 0 10px; font-size: 13px; line-height: 1.5; font-style: italic; }
.mvp-pill { display: inline-flex; padding: 2px 10px; border-radius: 999px; background: #fff; color: #9a3412; font-size: 11px; font-weight: 700; border: 1px solid #fed7aa; }
.mvp-pill--score { background: #fff7ed; color: #ea580c; }

.mvp-stages { display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 10px 0; }
.mvp-stage-col { background: #fff; border-radius: 10px; padding: 10px 12px; border: 1px solid #fed7aa; }
.mvp-stage-col__head { font-weight: 700; color: #9a3412; font-size: 12px; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 8px; }
.mvp-status-bars { display: flex; flex-direction: column; gap: 4px; }
.mvp-status-bars__row { display: grid; grid-template-columns: 24px 1fr 44px; align-items: center; gap: 6px; }
.mvp-status-bars__label { font-size: 13px; text-align: center; }
.mvp-status-bars__track { background: #f1f5f9; border-radius: 6px; height: 8px; overflow: hidden; }
.mvp-status-bars__fill { height: 100%; border-radius: 6px; transition: width 0.3s ease; }
.mvp-status-bars__fill--ok { background: linear-gradient(90deg, #22c55e, #16a34a); }
.mvp-status-bars__fill--mid { background: linear-gradient(90deg, #f59e0b, #d97706); }
.mvp-status-bars__fill--bad { background: linear-gradient(90deg, #ef4444, #dc2626); }
.mvp-status-bars__val { font-size: 11px; color: #64748b; font-weight: 600; text-align: right; }

.mvp-features { margin-top: 10px; }
.mvp-features__title { font-weight: 700; color: #9a3412; font-size: 12px; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 8px; }
.mvp-features__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.mvp-features__item { display: grid; grid-template-columns: 90px 1fr 1fr 40px; align-items: center; gap: 8px; font-size: 13px; }
.mvp-features__name { color: #0f172a; }
.mvp-features__bar { background: #fff; border-radius: 6px; height: 8px; overflow: hidden; border: 1px solid #fed7aa; }
.mvp-features__fill { height: 100%; background: linear-gradient(90deg, #fb923c, #f97316); border-radius: 6px; }
.mvp-features__pct { font-size: 11px; color: #64748b; font-weight: 600; text-align: right; }
.mvp-feat-tag { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; text-transform: uppercase; }
.mvp-feat-tag--critical { background: #fee2e2; color: #991b1b; }
.mvp-feat-tag--improve { background: #dbeafe; color: #1e40af; }
.mvp-feat-tag--optional { background: #f1f5f9; color: #475569; }

/* Participants drill-down */
.mvp-participants { margin-top: 22px; }
.mvp-participants__list { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-direction: column; gap: 8px; }
.mvp-participants__item { border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fff; }
.mvp-fac__participants-toggle {
  width: 100%; display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: #fafafa; border: none; cursor: pointer; font: inherit;
  gap: 12px; text-align: left; transition: background 0.15s ease;
}
.mvp-fac__participants-toggle:hover:not(:disabled) { background: #fff7ed; }
.mvp-fac__participants-toggle.is-open { background: #ffedd5; }
.mvp-participants__name { display: flex; align-items: center; gap: 10px; font-weight: 600; color: #0f172a; min-width: 0; }
.mvp-participants__avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #fb923c, #ea580c); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.mvp-participants__anon { color: #64748b; font-size: 12px; font-weight: 500; }
.mvp-participants__stats { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.mvp-participants__arrow { font-weight: 700; color: #64748b; font-size: 18px; margin-left: 4px; min-width: 18px; text-align: center; }
.mvp-participants__body { padding: 14px 16px 16px; background: #fff; border-top: 1px solid #eef2f7; }
.mvp-participants__cases { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 12px; }
.mvp-participants__case { padding: 10px 12px; background: #fff7ed; border-radius: 10px; border-left: 3px solid #fb923c; }
.mvp-participants__case-head { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }
.mvp-participants__stages { display: flex; flex-direction: column; gap: 8px; }
.mvp-participants__stage { background: #fff; border-radius: 8px; padding: 8px 10px; border: 1px solid #fed7aa; }
.mvp-participants__stage-head { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; font-size: 12px; }
.mvp-participants__chips { display: flex; gap: 6px; flex-wrap: wrap; }
.mvp-feat-chip { display: inline-flex; padding: 3px 9px; border-radius: 999px; font-size: 12px; font-weight: 500; border: 1px solid transparent; }
.mvp-feat-chip--critical { background: #fee2e2; color: #991b1b; border-color: #fca5a5; }
.mvp-feat-chip--improve { background: #dbeafe; color: #1e40af; border-color: #93c5fd; }
.mvp-feat-chip--optional { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }
.mvp-badge-status { display: inline-flex; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; }
.mvp-badge-status--success { background: #dcfce7; color: #166534; }
.mvp-badge-status--partial { background: #fef3c7; color: #92400e; }
.mvp-badge-status--fail { background: #fee2e2; color: #991b1b; }

/* Leaderboard */
.mvp-totals { display: flex; gap: 10px; margin-bottom: 16px; flex-wrap: wrap; }
.mvp-totals__item { background: #fff7ed; padding: 10px 14px; border-radius: 10px; display: flex; flex-direction: column; gap: 2px; border: 1px solid #fed7aa; min-width: 100px; }
.mvp-totals__val { font-size: 22px; font-weight: 800; color: #9a3412; }
.mvp-totals__lbl { font-size: 11px; color: #64748b; text-transform: uppercase; letter-spacing: 0.3px; }
.mvp-leaderboards { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.mvp-leaderboard { background: #fff7ed; border-radius: 14px; padding: 14px 16px; border: 1px solid #fed7aa; }
.mvp-leaderboard h4 { margin: 0 0 4px; font-size: 15px; }
.mvp-leaderboard__list { list-style: decimal inside; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 4px; }
.mvp-leaderboard__list li { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 6px 10px; border-radius: 8px; font-size: 13px; }
.mvp-leaderboard__name { font-weight: 600; }
.mvp-leaderboard__val { font-weight: 700; color: #9a3412; }

.mvp-heatmap { width: 100%; border-collapse: collapse; background: #fff; border-radius: 12px; overflow: hidden; }
.mvp-heatmap th, .mvp-heatmap td { padding: 8px 10px; text-align: center; font-size: 13px; border-bottom: 1px solid #f1f5f9; }
.mvp-heatmap th { background: #fff7ed; color: #9a3412; text-transform: uppercase; font-size: 11px; letter-spacing: 0.3px; }
.mvp-heatmap td:first-child, .mvp-heatmap th:first-child { text-align: left; }
.mvp-heat--hot { background: #dcfce7; color: #14532d; font-weight: 700; }
.mvp-heat--warm { background: #fef9c3; color: #854d0e; font-weight: 600; }
.mvp-heat--cool { background: #ffedd5; color: #9a3412; }
.mvp-heat--cold { background: #fee2e2; color: #991b1b; }

@media (max-width: 720px) {
  .mvp-stages { grid-template-columns: 1fr; }
  .mvp-features__item { grid-template-columns: 1fr; gap: 4px; }
  .mvp-leaderboards { grid-template-columns: 1fr; }
}
</style>
