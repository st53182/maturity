<template>
  <div class="ice-fac">
    <header class="ice-fac__head">
      <div>
        <h1>🧊 {{ $t('agileTraining.iceberg.facTitle') }}</h1>
        <p class="ice-fac__sub">{{ $t('agileTraining.iceberg.facSubtitle') }}</p>
      </div>
      <div class="ice-fac__head-actions">
        <router-link class="ice-fac__back" to="/agile-training">← {{ $t('agileTraining.hub.backHome') }}</router-link>
      </div>
    </header>

    <!-- Список сессий + создание -->
    <section v-if="!activeSession" class="ice-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="ice-fac__create" @submit.prevent="createSession">
        <input
          v-model="newSessionTitle"
          :placeholder="$t('agileTraining.facilitator.newSessionTitle')"
          required
          maxlength="255"
        />
        <select v-model="newSessionLocale" class="ice-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="ice-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="ice-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="ice-fac__list">
        <li v-for="s in sessions" :key="s.id" class="ice-fac__item">
          <div class="ice-fac__item-main">
            <div class="ice-fac__item-title">{{ s.title }}</div>
            <div class="ice-fac__item-meta">
              <span class="ice-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="ice-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- Активная сессия -->
    <section v-else class="ice-fac__section">
      <div class="ice-fac__active-head">
        <div>
          <div class="ice-fac__active-title">{{ activeSession.title }}</div>
          <div class="ice-fac__item-meta">
            <span class="ice-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="ice-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            📊 {{ $t('agileTraining.facilitator.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="ice-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="ice-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="ice-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="ice-fac__groups">
        <li v-for="g in groups" :key="g.id" class="ice-fac__group">
          <div class="ice-fac__group-main">
            <div class="ice-fac__group-name">{{ g.name }}</div>
            <div class="ice-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.iceberg.answersCount', { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.iceberg.avgDepth') }}: <b>{{ g.avg_score || 0 }}</b></span>
              <span>·</span>
              <span :class="['ice-fac__status', 'ice-fac__status--' + (g.status || 'not_started')]">
                {{ $t('agileTraining.facilitator.status.' + (g.status || 'not_started')) }}
              </span>
            </div>
            <div class="ice-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="ice-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="ice-fac__group-actions">
            <button class="btn-ghost" @click="openGroupResults(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.reset') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <!-- Модалка результатов одной группы -->
    <div v-if="resultsModal.open" class="ice-modal" @click.self="closeResults">
      <div class="ice-modal__body">
        <div class="ice-modal__head">
          <h3>{{ $t('agileTraining.iceberg.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="ice-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="ice-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <div class="ice-totals">
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ resultsModal.data.participants_count }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.facilitator.totalsParticipants') }}</span>
            </div>
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ resultsModal.data.group_totals.answers }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.facilitator.totalsAnswers') }}</span>
            </div>
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ resultsModal.data.group_totals.avg_score }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.iceberg.avgDepth') }}</span>
            </div>
          </div>

          <h4 class="ice-section-title">🏔 {{ $t('agileTraining.iceberg.primaryLevelDistribution') }}</h4>
          <p class="ice-hint">{{ $t('agileTraining.iceberg.primaryLevelHint') }}</p>
          <div class="ice-bars">
            <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-bars__row">
              <div class="ice-bars__label">{{ $t('agileTraining.iceberg.level.' + lk) }}</div>
              <div class="ice-bars__track">
                <div class="ice-bars__fill" :class="'ice-bars__fill--' + lk"
                     :style="{ width: (resultsModal.data.group_totals.primary_level_pct[lk] || 0) + '%' }" />
              </div>
              <div class="ice-bars__val">{{ resultsModal.data.group_totals.primary_level_pct[lk] || 0 }}%</div>
            </div>
          </div>

          <h4 class="ice-section-title">📋 {{ $t('agileTraining.iceberg.caseByCase') }}</h4>
          <div v-for="row in resultsModal.data.per_case" :key="row.key" class="ice-case-row">
            <div class="ice-case-row__head">
              <div class="ice-case-row__title">
                <span class="ice-case-row__cat">{{ row.category }}</span>
                <b>{{ row.title }}</b>
              </div>
              <div class="ice-case-row__stats">
                <span class="ice-pill">{{ $t('agileTraining.iceberg.answersCount', { n: row.stats.total }, row.stats.total) }}</span>
                <span class="ice-pill ice-pill--score">{{ $t('agileTraining.iceberg.avgDepth') }}: {{ row.stats.avg_score }}</span>
              </div>
            </div>
            <p class="ice-case-row__scenario">{{ row.scenario }}</p>
            <div class="ice-bars ice-bars--small">
              <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-bars__row">
                <div class="ice-bars__label">{{ $t('agileTraining.iceberg.level.' + lk) }}</div>
                <div class="ice-bars__track">
                  <div class="ice-bars__fill" :class="'ice-bars__fill--' + lk"
                       :style="{ width: (row.stats.primary_level_pct[lk] || 0) + '%' }" />
                </div>
                <div class="ice-bars__val">{{ row.stats.primary_level_pct[lk] || 0 }}%</div>
              </div>
            </div>
            <p class="ice-case-row__expert" v-if="row.summary">
              <b>💡 {{ $t('agileTraining.iceberg.expertSummary') }}:</b> {{ row.summary }}
            </p>
          </div>

          <section class="ice-participants">
            <h4 class="ice-section-title">👥 {{ $t('agileTraining.facilitator.participantsTitle') }}</h4>
            <p class="ice-modal__lead">{{ $t('agileTraining.facilitator.participantsLead') }}</p>
            <p v-if="!resultsModal.participants.length" class="ice-fac__hint">
              {{ $t('agileTraining.facilitator.participantsEmpty') }}
            </p>
            <ul v-else class="ice-participants__list">
              <li v-for="p in resultsModal.participants" :key="'ip-'+p.id" class="ice-participants__item">
                <button
                  type="button"
                  class="ice-fac__participants-toggle"
                  :class="{ 'is-open': !!resultsModal.expandedP[p.id] }"
                  @click="toggleParticipant(p.id)"
                >
                  <span class="ice-participants__name">
                    <span class="ice-participants__avatar">{{ (p.display_name || p.anonymous_label).slice(0,2).toUpperCase() }}</span>
                    <span>{{ p.display_name || $t('agileTraining.facilitator.anonymous') }}</span>
                    <span class="ice-participants__anon">{{ p.anonymous_label }}</span>
                  </span>
                  <span class="ice-participants__stats">
                    <span class="ice-pill">{{ $t('agileTraining.facilitator.casesAnswered', { n: p.cases_answered }) }}</span>
                    <span class="ice-pill ice-pill--score">{{ $t('agileTraining.facilitator.depthScoreAvg') }}: {{ p.avg_depth_score }}</span>
                    <span class="ice-participants__arrow">{{ resultsModal.expandedP[p.id] ? '−' : '+' }}</span>
                  </span>
                </button>
                <div v-if="resultsModal.expandedP[p.id]" class="ice-participants__body">
                  <p v-if="!p.answers.length" class="ice-fac__hint">
                    {{ $t('agileTraining.facilitator.noAnswersForParticipant') }}
                  </p>
                  <ul v-else class="ice-participants__cases">
                    <li v-for="a in p.answers" :key="'ipa-'+p.id+'-'+a.case_key" class="ice-participants__case">
                      <button
                        type="button"
                        class="ice-fac__case-toggle"
                        :class="{ 'is-open': isCaseOpen(p.id, a.case_key) }"
                        @click="toggleCase(p.id, a.case_key)"
                      >
                        <span class="ice-participants__case-head">
                          <span class="ice-case-row__cat" v-if="a.case_category">{{ a.case_category }}</span>
                          <strong>{{ a.case_title }}</strong>
                        </span>
                        <span class="ice-participants__case-stats">
                          <span class="ice-pill ice-pill--score">{{ $t('agileTraining.facilitator.depthScore') }}: {{ a.depth_score }}</span>
                          <span v-if="a.primary_level" class="ice-pill">{{ levelName(a.primary_level) }}</span>
                          <span class="ice-participants__arrow">{{ isCaseOpen(p.id, a.case_key) ? '−' : '+' }}</span>
                        </span>
                      </button>
                      <div v-if="isCaseOpen(p.id, a.case_key)" class="ice-participants__case-body">
                        <div class="ice-participants__section">
                          <div class="ice-participants__k">🧊 {{ $t('agileTraining.facilitator.placementsLabel') }}</div>
                          <div v-for="lk in LEVEL_KEYS" :key="'pl-'+p.id+'-'+a.case_key+'-'+lk" class="ice-participants__lvl">
                            <div class="ice-participants__lvl-name">{{ levelName(lk) }}</div>
                            <div class="ice-participants__lvl-items">
                              <span v-if="!(a.placements_by_level && a.placements_by_level[lk] && a.placements_by_level[lk].length)" class="ice-participants__dim">—</span>
                              <span
                                v-for="it in (a.placements_by_level && a.placements_by_level[lk] || [])"
                                :key="'pli-'+p.id+'-'+it.key"
                                class="ice-participants__chip"
                                :class="{ 'ice-participants__chip--match': it.match, 'ice-participants__chip--miss': !it.match }"
                                :title="it.match ? $t('agileTraining.facilitator.expertMatch') : $t('agileTraining.facilitator.expertMismatch')"
                              >
                                {{ it.label }}<span v-if="!it.match"> · {{ levelName(it.expert_level) }}</span>
                              </span>
                            </div>
                          </div>
                          <div v-if="a.custom_items && a.custom_items.length" class="ice-participants__lvl">
                            <div class="ice-participants__lvl-name">✍ {{ $t('agileTraining.facilitator.customItem') }}</div>
                            <div class="ice-participants__lvl-items">
                              <span v-for="(ci, i) in a.custom_items" :key="'ci-'+p.id+'-'+i" class="ice-participants__chip ice-participants__chip--custom">
                                {{ ci.text }} <em v-if="ci.level" class="ice-participants__dim">({{ levelName(ci.level) }})</em>
                              </span>
                            </div>
                          </div>
                        </div>

                        <div v-if="a.chain && a.chain.length" class="ice-participants__section">
                          <div class="ice-participants__k">🔗 {{ $t('agileTraining.facilitator.chainLabel') }}</div>
                          <ul class="ice-participants__chain">
                            <li v-for="step in a.chain" :key="'ch-'+p.id+'-'+a.case_key+'-'+step.level">
                              <strong>{{ levelName(step.level) }}:</strong> {{ step.text }}
                            </li>
                          </ul>
                        </div>

                        <div v-if="a.superficial && a.superficial.length" class="ice-participants__section">
                          <div class="ice-participants__k">🧠 {{ $t('agileTraining.facilitator.superficialLabel') }}</div>
                          <ul class="ice-participants__sup">
                            <li v-for="s in a.superficial" :key="'sup-'+p.id+'-'+s.key" :class="s.correct ? 'is-ok' : 'is-bad'">
                              <div class="ice-participants__sup-text">«{{ s.text }}»</div>
                              <div class="ice-participants__sup-meta">
                                <span class="ice-participants__sup-label">
                                  {{ $t('agileTraining.facilitator.sympUser') }}:
                                  <b>{{ s.user_is_symptom ? $t('agileTraining.facilitator.isSymptom') : $t('agileTraining.facilitator.isRealCause') }}</b>
                                </span>
                                <span class="ice-participants__sup-label">
                                  {{ $t('agileTraining.facilitator.sympExpert') }}:
                                  <b>{{ s.expert_is_symptom ? $t('agileTraining.facilitator.isSymptom') : $t('agileTraining.facilitator.isRealCause') }}</b>
                                </span>
                                <span class="ice-participants__sup-verdict" :class="s.correct ? 'is-ok' : 'is-bad'">
                                  {{ s.correct ? '✓ ' + $t('agileTraining.facilitator.sympCorrect') : '✕ ' + $t('agileTraining.facilitator.sympIncorrect') }}
                                </span>
                              </div>
                            </li>
                          </ul>
                        </div>

                        <div v-if="a.interventions && a.interventions.length" class="ice-participants__section">
                          <div class="ice-participants__k">🛠 {{ $t('agileTraining.facilitator.interventionsLabel') }}</div>
                          <ul class="ice-participants__iv">
                            <li v-for="iv in a.interventions" :key="'iv-'+p.id+'-'+a.case_key+'-'+iv.level">
                              <div class="ice-participants__iv-head"><strong>{{ levelName(iv.level) }}</strong></div>
                              <div class="ice-participants__iv-text">{{ iv.text }}</div>
                            </li>
                          </ul>
                        </div>
                      </div>
                    </li>
                  </ul>
                </div>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </div>

    <!-- Модалка сравнения групп -->
    <div v-if="compareAll.open" class="ice-modal" @click.self="closeCompareAll">
      <div class="ice-modal__body ice-modal__body--wide">
        <div class="ice-modal__head">
          <h3>📊 {{ $t('agileTraining.facilitator.compareAllTitle') }}</h3>
          <button class="ice-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="ice-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="ice-modal__lead">{{ $t('agileTraining.facilitator.compareAllLead') }}</p>

          <div class="ice-totals">
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ compareAll.data.totals.groups }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.facilitator.totalsGroups') }}</span>
            </div>
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ compareAll.data.totals.participants }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.facilitator.totalsParticipants') }}</span>
            </div>
            <div class="ice-totals__item">
              <span class="ice-totals__val">{{ compareAll.data.totals.answers }}</span>
              <span class="ice-totals__lbl">{{ $t('agileTraining.facilitator.totalsAnswers') }}</span>
            </div>
          </div>

          <h4 class="ice-section-title">🏁 {{ $t('agileTraining.iceberg.groupScoreboard') }}</h4>
          <div class="ice-scoreboard">
            <table class="ice-heatmap">
              <thead>
                <tr>
                  <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                  <th>{{ $t('agileTraining.iceberg.avgDepth') }}</th>
                  <th v-for="lk in LEVEL_KEYS" :key="lk">{{ $t('agileTraining.iceberg.level.' + lk) }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="g in compareAll.data.groups" :key="g.id">
                  <td><b>{{ g.name }}</b></td>
                  <td><b>{{ g.avg_score }}</b></td>
                  <td v-for="lk in LEVEL_KEYS" :key="lk" :class="heatmapClass(g.primary_level_pct[lk] || 0)">
                    {{ g.primary_level_pct[lk] || 0 }}%
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <h4 class="ice-section-title">🔥 {{ $t('agileTraining.iceberg.mostSplit') }}</h4>
          <p class="ice-hint">{{ $t('agileTraining.iceberg.mostSplitHint') }}</p>
          <div v-if="!compareAll.data.most_split.length" class="ice-fac__empty">{{ $t('agileTraining.facilitator.noData') }}</div>
          <ul class="ice-top__list">
            <li v-for="r in compareAll.data.most_split" :key="r.key">
              <div class="ice-top__title">{{ r.title }}</div>
              <div class="ice-top__meta">
                <span class="ice-case-row__cat">{{ r.category }}</span>
                <span>Δ {{ r.spread }}</span>
                <span>avg {{ r.avg_score }}</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * Страница фасилитатора для упражнения «Айсберг» (системное мышление).
 * Общие эндпоинты сессии живут в /api/agile-training/sessions/...,
 * специфичные — в /api/agile-training/iceberg/...
 */
import axios from 'axios';

export default {
  name: 'AgileIcebergFacilitator',
  data() {
    const lang = (typeof localStorage !== 'undefined' && localStorage.getItem('language')) || null;
    return {
      LEVEL_KEYS: ['events', 'patterns', 'structures', 'mental_models'],
      sessions: [],
      loadingSessions: false,
      newSessionTitle: '',
      newSessionLocale: lang === 'en' ? 'en' : 'ru',
      activeSession: null,
      groups: [],
      newGroupName: '',
      copiedSlug: '',
      resultsModal: { open: false, group: null, loading: false, data: null, participants: [], expandedP: {}, expandedC: {} },
      compareAll: { open: false, loading: false, data: null },
    };
  },
  async mounted() { await this.loadSessions(); },
  methods: {
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: 'Bearer ' + token } : {};
    },
    publicLink(slug) { return `${window.location.origin}/g/${slug}`; },
    formatDate(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      return Number.isNaN(+d) ? iso : d.toLocaleDateString();
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        const all = res.data.sessions || [];
        this.sessions = all.filter(s => (s.exercise_key || 'agile_principles') === 'iceberg');
      } catch (e) {
        console.error('loadSessions', e);
      } finally {
        this.loadingSessions = false;
      }
    },
    async createSession() {
      try {
        const res = await axios.post('/api/agile-training/sessions', {
          title: this.newSessionTitle,
          locale: this.newSessionLocale,
          exercise_key: 'iceberg',
        }, { headers: this.authHeaders() });
        this.newSessionTitle = '';
        await this.loadSessions();
        if (res.data && res.data.id) await this.openSession(res.data.id);
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to create session');
      }
    },
    async openSession(id) {
      try {
        const res = await axios.get(
          `/api/agile-training/iceberg/sessions/${id}/results`,
          { headers: this.authHeaders() },
        );
        this.activeSession = res.data.session;
        this.groups = (res.data.groups || []).map(g => ({
          ...g,
          participants_count: g.participants,
          answers_count: g.answers,
        }));
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to open session');
      }
    },
    async refreshSession() {
      if (this.activeSession) await this.openSession(this.activeSession.id);
    },
    closeSession() { this.activeSession = null; this.groups = []; },
    async deleteSession() {
      if (!this.activeSession) return;
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this.authHeaders() });
        this.closeSession();
        await this.loadSessions();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to delete');
      }
    },
    async addGroup() {
      if (!this.activeSession) return;
      try {
        await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`, {
          name: this.newGroupName,
        }, { headers: this.authHeaders() });
        this.newGroupName = '';
        await this.refreshSession();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to add group');
      }
    },
    async removeGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this.authHeaders() });
        await this.refreshSession();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to delete group');
      }
    },
    async resetGroup(g) {
      if (!confirm(this.$t('agileTraining.facilitator.confirmReset', { name: g.name }))) return;
      try {
        await axios.post(`/api/agile-training/iceberg/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
        await this.refreshSession();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to reset');
      }
    },
    async copyLink(slug) {
      const link = this.publicLink(slug);
      try {
        await navigator.clipboard.writeText(link);
        this.copiedSlug = slug;
        setTimeout(() => { if (this.copiedSlug === slug) this.copiedSlug = ''; }, 1600);
      } catch (_) { alert('Failed to copy link'); }
    },
    async openGroupResults(g) {
      this.resultsModal = { open: true, group: g, loading: true, data: null, participants: [], expandedP: {}, expandedC: {} };
      try {
        const res = await axios.get(`/api/agile-training/iceberg/groups/${g.id}/results`, {
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
        const parts = await axios.get(`/api/agile-training/iceberg/groups/${g.id}/participants`,
          { headers: this.authHeaders() });
        this.resultsModal.participants = parts.data.participants || [];
      } catch (e) {
        this.resultsModal.participants = [];
      }
    },
    toggleParticipant(pid) {
      const cur = !!this.resultsModal.expandedP[pid];
      this.resultsModal.expandedP = { ...this.resultsModal.expandedP, [pid]: !cur };
    },
    toggleCase(pid, caseKey) {
      const key = pid + ':' + caseKey;
      const cur = !!this.resultsModal.expandedC[key];
      this.resultsModal.expandedC = { ...this.resultsModal.expandedC, [key]: !cur };
    },
    isCaseOpen(pid, caseKey) {
      return !!this.resultsModal.expandedC[pid + ':' + caseKey];
    },
    levelName(lk) {
      return this.$t('agileTraining.iceberg.level.' + lk);
    },
    closeResults() { this.resultsModal = { open: false, group: null, loading: false, data: null, participants: [], expandedP: {}, expandedC: {} }; },
    async openCompareAll() {
      if (!this.activeSession) return;
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const res = await axios.get(
          `/api/agile-training/iceberg/sessions/${this.activeSession.id}/results`,
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
      let level = 'low';
      if (pct >= 50) level = 'high';
      else if (pct >= 25) level = 'mid';
      return 'ice-heatmap__cell ice-heatmap__cell--' + level;
    },
  },
};
</script>

<style scoped>
.ice-fac {
  max-width: 1100px;
  margin: 32px auto 64px;
  padding: 0 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  color: #0f172a;
}
.ice-fac__head {
  display: flex; justify-content: space-between; align-items: flex-start;
  margin-bottom: 24px; gap: 16px;
}
.ice-fac__head h1 { margin: 0 0 4px; font-size: 28px; letter-spacing: -0.3px; }
.ice-fac__sub { margin: 0; color: #64748b; }
.ice-fac__back {
  padding: 8px 14px; border-radius: 999px; background: #fff;
  border: 1px solid #e5e7eb; color: #111; text-decoration: none;
  font-weight: 600; font-size: 13px;
}
.ice-fac__section {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 16px;
  padding: 20px; margin-bottom: 20px;
}
.ice-fac__section h2, .ice-fac__section h3 { margin: 0 0 14px; }
.ice-fac__create { display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap; }
.ice-fac__create input, .ice-fac__add-group input, .ice-fac__locale {
  flex: 1; min-width: 180px; padding: 10px 14px; border: 1px solid #cbd5e1;
  border-radius: 10px; font: inherit;
}
.ice-fac__locale { flex: 0 0 auto; }
.ice-fac__create button, .ice-fac__add-group button, .ice-fac__open-btn {
  padding: 10px 18px; border: none !important; border-radius: 10px !important;
  background: linear-gradient(135deg, #0ea5e9, #0369a1) !important;
  color: #fff !important; font-weight: 600; cursor: pointer;
  box-shadow: 0 6px 14px rgba(14,165,233,0.3) !important;
  transition: transform 0.1s ease, box-shadow 0.2s ease, filter 0.15s ease;
}
.ice-fac__create button:hover:not(:disabled), .ice-fac__add-group button:hover:not(:disabled), .ice-fac__open-btn:hover:not(:disabled) {
  transform: translateY(-1px); box-shadow: 0 10px 22px rgba(14,165,233,0.45) !important; filter: brightness(1.05);
}
.ice-fac__create button:active:not(:disabled), .ice-fac__add-group button:active:not(:disabled), .ice-fac__open-btn:active:not(:disabled) {
  transform: translateY(1px); box-shadow: 0 2px 6px rgba(14,165,233,0.3) !important;
}
.ice-fac__create button:disabled, .ice-fac__add-group button:disabled, .ice-fac__open-btn:disabled {
  opacity: 0.5; cursor: not-allowed;
}
.ice-fac__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.ice-fac__item, .ice-fac__group {
  display: flex; justify-content: space-between; gap: 16px; align-items: flex-start;
  padding: 14px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fafafa;
}
.ice-fac__item-title { font-weight: 600; margin-bottom: 4px; }
.ice-fac__item-meta { color: #64748b; font-size: 13px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.ice-fac__badge {
  background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 999px;
  font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
}
.ice-fac__hint, .ice-fac__empty { color: #64748b; padding: 10px 0; }
.ice-fac__active-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 14px; }
.ice-fac__active-title { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.ice-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-ghost { padding: 8px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; color: #0f172a; cursor: pointer; font: inherit; font-weight: 600; transition: all 0.15s ease; }
.btn-ghost:hover:not(:disabled) { border-color: #0369a1; color: #0369a1; background: #f0f9ff; }
.btn-ghost:active:not(:disabled) { background: #e0f2fe; transform: translateY(1px); }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 8px 14px; border-radius: 10px; border: 1px solid #fecaca; background: #fff1f2; color: #b91c1c; cursor: pointer; font: inherit; font-weight: 600; transition: all 0.15s ease; }
.btn-danger:hover:not(:disabled) { background: #fee2e2; border-color: #ef4444; color: #991b1b; }
.btn-danger:active:not(:disabled) { background: #fecaca; transform: translateY(1px); }
.ice-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 10px; }
.ice-fac__add-group { display: flex; gap: 8px; flex-wrap: wrap; }
.ice-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.ice-fac__group-main { flex: 1; min-width: 0; }
.ice-fac__group-name { font-weight: 700; margin-bottom: 4px; }
.ice-fac__status { padding: 1px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }
.ice-fac__status--not_started { background: #f1f5f9; color: #475569; }
.ice-fac__status--in_progress { background: #fef3c7; color: #92400e; }
.ice-fac__status--completed { background: #dcfce7; color: #166534; }
.ice-fac__link { margin-top: 8px; display: flex; gap: 8px; align-items: center; }
.ice-fac__link code { background: #f8fafc; padding: 4px 8px; border-radius: 6px; font-size: 12px; word-break: break-all; }
.ice-fac__copy { padding: 6px 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; color: #334155; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.15s ease; }
.ice-fac__copy:hover:not(:disabled) { border-color: #0369a1; color: #0369a1; background: #f0f9ff; }
.ice-fac__copy:active:not(:disabled) { background: #e0f2fe; transform: translateY(1px); }
.ice-fac__group-actions { display: flex; gap: 6px; flex-direction: column; align-items: flex-end; }

.ice-modal { position: fixed; inset: 0; background: rgba(15,23,42,0.55); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 1000; }
.ice-modal__body { background: #fff; border-radius: 18px; max-width: 820px; width: 100%; max-height: 92vh; overflow-y: auto; padding: 22px 24px; }
.ice-modal__body--wide { max-width: 1080px; }
.ice-modal__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.ice-modal__head h3 { margin: 0; font-size: 20px; }
.ice-modal__close { background: transparent; border: none; font-size: 22px; cursor: pointer; color: #475569; }
.ice-modal__lead { color: #475569; margin: 0 0 14px; }

.ice-totals { display: flex; gap: 14px; margin-bottom: 18px; flex-wrap: wrap; }
.ice-totals__item { background: #ecfeff; border: 1px solid #a5f3fc; border-radius: 14px; padding: 12px 16px; min-width: 120px; display: flex; flex-direction: column; gap: 2px; }
.ice-totals__val { font-size: 24px; font-weight: 700; color: #0369a1; }
.ice-totals__lbl { color: #64748b; font-size: 12px; }

.ice-section-title { margin: 16px 0 4px; }
.ice-hint { color: #64748b; font-size: 13px; margin: 0 0 10px; }

.ice-bars { display: flex; flex-direction: column; gap: 6px; }
.ice-bars--small .ice-bars__row { grid-template-columns: 140px 1fr 44px; }
.ice-bars__row { display: grid; grid-template-columns: 160px 1fr 44px; gap: 8px; align-items: center; }
.ice-bars__label { font-size: 13px; color: #334155; }
.ice-bars__track { background: #eef2f7; border-radius: 999px; height: 10px; overflow: hidden; }
.ice-bars__fill { height: 100%; background: #94a3b8; border-radius: 999px; transition: width 0.3s ease; }
.ice-bars__fill--events { background: #bae6fd; }
.ice-bars__fill--patterns { background: #7dd3fc; }
.ice-bars__fill--structures { background: #0ea5e9; }
.ice-bars__fill--mental_models { background: #0c4a6e; }
.ice-bars__val { font-size: 12px; color: #64748b; text-align: right; }

.ice-case-row { padding: 14px 0; border-top: 1px solid #eef2f7; }
.ice-case-row:first-of-type { border-top: none; }
.ice-case-row__head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.ice-case-row__cat { color: #0369a1; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-right: 6px; }
.ice-case-row__scenario { color: #334155; margin: 0 0 10px; line-height: 1.55; }
.ice-case-row__expert { color: #475569; margin: 10px 0 0; font-size: 13px; line-height: 1.5; background: #f8fafc; padding: 10px 12px; border-radius: 10px; }

/* Participants drill-down */
.ice-participants { margin-top: 24px; }
.ice-participants__list { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-direction: column; gap: 8px; }
.ice-participants__item { border: 1px solid #e5e7eb; border-radius: 12px; overflow: hidden; background: #fff; }
.ice-fac__participants-toggle {
  width: 100%; display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: #fafafa; border: none; cursor: pointer; font: inherit;
  gap: 12px; text-align: left; transition: background 0.15s ease;
}
.ice-fac__participants-toggle:hover:not(:disabled) { background: #f0f9ff; }
.ice-fac__participants-toggle.is-open { background: #e0f2fe; }
.ice-participants__name { display: flex; align-items: center; gap: 10px; font-weight: 600; color: #0f172a; min-width: 0; }
.ice-participants__avatar {
  width: 28px; height: 28px; border-radius: 50%;
  background: linear-gradient(135deg, #0ea5e9, #0369a1); color: #fff;
  display: inline-flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 700;
}
.ice-participants__anon { color: #64748b; font-size: 12px; font-weight: 500; }
.ice-participants__stats { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.ice-participants__arrow { font-weight: 700; color: #64748b; font-size: 18px; margin-left: 4px; min-width: 18px; text-align: center; }
.ice-participants__body { padding: 14px 16px 16px; background: #fff; border-top: 1px solid #eef2f7; }
.ice-participants__cases { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.ice-participants__case { background: #f0f9ff; border-radius: 10px; overflow: hidden; }
.ice-fac__case-toggle {
  width: 100%; display: flex; justify-content: space-between; align-items: center;
  padding: 10px 14px; background: transparent; border: none; cursor: pointer; font: inherit;
  gap: 12px; text-align: left; transition: background 0.15s ease;
}
.ice-fac__case-toggle:hover:not(:disabled) { background: #e0f2fe; }
.ice-fac__case-toggle.is-open { background: #bae6fd; }
.ice-participants__case-head { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
.ice-participants__case-stats { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.ice-participants__case-body {
  padding: 12px 14px 14px; background: #fff; border-top: 1px solid #dbeafe;
  display: flex; flex-direction: column; gap: 14px;
}
.ice-participants__section { display: flex; flex-direction: column; gap: 6px; }
.ice-participants__k { font-weight: 700; color: #0f172a; font-size: 13px; }
.ice-participants__lvl {
  display: grid; grid-template-columns: 180px 1fr; gap: 8px; align-items: start;
  padding: 4px 0;
}
.ice-participants__lvl-name { font-size: 12px; color: #475569; font-weight: 600; }
.ice-participants__lvl-items { display: flex; gap: 6px; flex-wrap: wrap; }
.ice-participants__chip {
  display: inline-flex; padding: 3px 9px; border-radius: 999px;
  font-size: 12px; font-weight: 500; border: 1px solid transparent; line-height: 1.3;
}
.ice-participants__chip--match { background: #dcfce7; color: #166534; border-color: #86efac; }
.ice-participants__chip--miss { background: #fef3c7; color: #92400e; border-color: #fcd34d; }
.ice-participants__chip--custom { background: #f5f3ff; color: #6d28d9; border-color: #ddd6fe; font-style: italic; }
.ice-participants__dim { color: #94a3b8; font-size: 11px; }
.ice-participants__chain { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.ice-participants__chain li { padding: 8px 10px; background: #f8fafc; border-left: 3px solid #0ea5e9; border-radius: 6px; font-size: 13px; color: #334155; line-height: 1.45; }
.ice-participants__sup { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.ice-participants__sup li { padding: 8px 10px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #e2e8f0; font-size: 12px; }
.ice-participants__sup li.is-ok { border-left-color: #22c55e; }
.ice-participants__sup li.is-bad { border-left-color: #ef4444; background: #fef2f2; }
.ice-participants__sup-text { color: #0f172a; font-size: 13px; margin-bottom: 4px; font-style: italic; }
.ice-participants__sup-meta { display: flex; gap: 12px; flex-wrap: wrap; color: #475569; }
.ice-participants__sup-label { font-size: 11px; }
.ice-participants__sup-verdict { font-size: 11px; font-weight: 700; padding: 1px 8px; border-radius: 999px; }
.ice-participants__sup-verdict.is-ok { background: #dcfce7; color: #166534; }
.ice-participants__sup-verdict.is-bad { background: #fee2e2; color: #991b1b; }
.ice-participants__iv { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; }
.ice-participants__iv li { padding: 8px 10px; background: #f0f9ff; border-radius: 8px; border-left: 3px solid #0ea5e9; }
.ice-participants__iv-head { font-size: 11px; color: #0369a1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.3px; margin-bottom: 3px; }
.ice-participants__iv-text { font-size: 13px; color: #0f172a; line-height: 1.5; white-space: pre-wrap; }
@media (max-width: 640px) {
  .ice-participants__lvl { grid-template-columns: 1fr; gap: 2px; }
}
.ice-case-row__stats { display: flex; gap: 6px; flex-wrap: wrap; }
.ice-pill { background: #f1f5f9; color: #334155; padding: 2px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
.ice-pill--score { background: #ecfeff; color: #0369a1; }

.ice-top__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.ice-top__list li { background: #f8fafc; border-radius: 10px; padding: 10px 12px; }
.ice-top__title { font-weight: 600; margin-bottom: 4px; }
.ice-top__meta { display: flex; gap: 10px; flex-wrap: wrap; color: #64748b; font-size: 12px; align-items: center; }

.ice-scoreboard { overflow-x: auto; margin: 8px 0 18px; }
.ice-heatmap { border-collapse: collapse; width: 100%; font-size: 12px; }
.ice-heatmap th, .ice-heatmap td { border: 1px solid #eef2f7; padding: 8px 10px; text-align: center; vertical-align: middle; }
.ice-heatmap thead th { background: #f8fafc; }
.ice-heatmap tbody td:first-child { text-align: left; min-width: 160px; }
.ice-heatmap__cell--low { background: #e0f2fe; }
.ice-heatmap__cell--mid { background: #7dd3fc; color: #0c4a6e; }
.ice-heatmap__cell--high { background: #0ea5e9; color: #fff; font-weight: 700; }

@media (max-width: 720px) {
  .ice-fac__group { flex-direction: column; }
  .ice-fac__group-actions { align-items: flex-start; flex-direction: row; flex-wrap: wrap; }
  .ice-bars__row { grid-template-columns: 100px 1fr 40px; }
}
</style>
