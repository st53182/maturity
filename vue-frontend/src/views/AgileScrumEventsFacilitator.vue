<template>
  <div class="se-fac">
    <header class="se-fac__head">
      <div>
        <h1>🗓️ {{ $t('agileTraining.scrumEvents.facTitle') }}</h1>
        <p class="se-fac__sub">{{ $t('agileTraining.scrumEvents.facSubtitle') }}</p>
      </div>
      <router-link class="se-fac__back" to="/agile-training">
        ← {{ $t('agileTraining.hub.backHome') }}
      </router-link>
    </header>

    <!-- список сессий -->
    <section v-if="!activeSession" class="se-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="se-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle"
               :placeholder="$t('agileTraining.scrumEvents.newSessionTitle')"
               required maxlength="255" />
        <select v-model="newSessionLocale" class="se-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="se-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="se-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="se-fac__list">
        <li v-for="s in sessions" :key="s.id" class="se-fac__item">
          <div>
            <div class="se-fac__item-title">{{ s.title }}</div>
            <div class="se-fac__item-meta">
              <span class="se-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>
                {{ $t('agileTraining.facilitator.groupsCount',
                      { n: s.groups_count || 0 }, s.groups_count || 0) }}
              </span>
            </div>
          </div>
          <button class="se-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- активная сессия -->
    <section v-else class="se-fac__section">
      <div class="se-fac__active-head">
        <div>
          <div class="se-fac__active-title">{{ activeSession.title }}</div>
          <div class="se-fac__item-meta">
            <span class="se-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="se-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            🏁 {{ $t('agileTraining.scrumEvents.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">
            ← {{ $t('agileTraining.facilitator.backToList') }}
          </button>
          <button class="btn-danger" @click="deleteSession">
            {{ $t('agileTraining.facilitator.deleteSession') }}
          </button>
        </div>
      </div>

      <div class="se-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="se-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName"
                 :placeholder="$t('agileTraining.facilitator.newGroupName')"
                 required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="se-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="se-fac__groups">
        <li v-for="g in groups" :key="g.id" class="se-fac__group">
          <div class="se-fac__group-main">
            <div class="se-fac__group-name">{{ g.name }}</div>
            <div class="se-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants',
                           { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.scrumEvents.answersCount',
                           { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
            </div>
            <div class="se-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="se-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug
                   ? $t('agileTraining.facilitator.copied')
                   : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="se-fac__group-actions">
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
    <div v-if="resultsModal.open" class="se-modal" @click.self="closeResults">
      <div class="se-modal__body se-modal__body--wide">
        <div class="se-modal__head">
          <h3>{{ $t('agileTraining.scrumEvents.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="se-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="se-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="se-modal__lead">
            {{ $t('agileTraining.facilitator.participants',
                  { n: resultsModal.data.participants_count || 0 },
                  resultsModal.data.participants_count || 0) }}
            · {{ $t('agileTraining.scrumEvents.avgHealth') }}:
            <b>{{ resultsModal.data.avg_health_pct || 0 }}%</b>
          </p>

          <div v-if="resultsModal.data.facilitator_content" class="se-fac__reference">
            <h4 class="se-section-title">📋 {{ $t('agileTraining.scrumEvents.facilitatorReferenceTitle') }}</h4>
            <p class="se-fac__reference-lead">{{ $t('agileTraining.scrumEvents.facilitatorReferenceLead') }}</p>
            <div v-for="s in resultsModal.data.facilitator_content.stages" :key="'fref-'+s.key" class="se-ref-stage">
              <h5 class="se-ref-stage__title">
                <span class="se-ref-stage__emoji">{{ stageEmoji(s.key) }}</span> {{ s.title }}
              </h5>
              <div v-for="cat in resultsModal.data.facilitator_content.categories" :key="'fref-'+s.key+'-'+cat" class="se-ref-cat">
                <div class="se-col__cat-title">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</div>
                <div class="se-ref-cols">
                  <div class="se-ref-block se-ref-block--exp">
                    <div class="se-ref-block__label">{{ $t('agileTraining.scrumEvents.refExpected') }}</div>
                    <ul class="se-ref-pills">
                      <li
                        v-for="k in (resultsModal.data.facilitator_content.reference?.[s.key]?.expected?.[cat] || [])"
                        :key="'e-'+s.key+'-'+cat+'-'+k"
                        class="se-ref-pill se-ref-pill--expected"
                      >{{ refCardTitle(resultsModal.data.facilitator_content, cat, k) }}</li>
                      <li
                        v-if="!(resultsModal.data.facilitator_content.reference?.[s.key]?.expected?.[cat] || []).length"
                        class="se-fac__hint"
                      >—</li>
                    </ul>
                  </div>
                  <div class="se-ref-block se-ref-block--acc">
                    <div class="se-ref-block__label">{{ $t('agileTraining.scrumEvents.refAcceptable') }}</div>
                    <ul class="se-ref-pills">
                      <li
                        v-for="k in (resultsModal.data.facilitator_content.reference?.[s.key]?.acceptable?.[cat] || [])"
                        :key="'a-'+s.key+'-'+cat+'-'+k"
                        class="se-ref-pill se-ref-pill--acceptable"
                      >{{ refCardTitle(resultsModal.data.facilitator_content, cat, k) }}</li>
                      <li
                        v-if="!(resultsModal.data.facilitator_content.reference?.[s.key]?.acceptable?.[cat] || []).length"
                        class="se-fac__hint"
                      >—</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="se-board">
            <div v-for="stage in resultsModal.data.stages" :key="stage.key"
                 class="se-col" :class="'se-col--' + stage.key">
              <div class="se-col__head">
                <h4>{{ stage.title }}</h4>
                <div class="se-col__colors">
                  <span class="se-pill se-pill--green">🟢 {{ stage.colors.green || 0 }}</span>
                  <span class="se-pill se-pill--yellow">🟡 {{ stage.colors.yellow || 0 }}</span>
                  <span class="se-pill se-pill--red">🔴 {{ stage.colors.red || 0 }}</span>
                </div>
              </div>
              <div v-for="cat in categoryOrder" :key="cat" class="se-col__cat">
                <div class="se-col__cat-title">{{ catLabel(cat) }}</div>
                <ul class="se-col__picks">
                  <li v-for="item in (stage.categories[cat] || []).slice(0, 5)" :key="item.key"
                      class="se-pick">
                    <span class="se-pick__title">{{ item.title }}</span>
                    <span class="se-pick__pct">{{ item.pct }}%</span>
                  </li>
                  <li v-if="!(stage.categories[cat] || []).length" class="se-fac__hint">—</li>
                </ul>
              </div>
            </div>
          </div>

          <h4 class="se-section-title">⚠️ {{ $t('agileTraining.scrumEvents.errorsSeenTop') }}</h4>
          <ul class="se-errors">
            <li v-for="e in resultsModal.data.errors_seen" :key="e.key">
              <b>{{ $t('agileTraining.scrumEvents.errors.' + e.key + '.title') }}</b>
              <span class="se-fac__hint">· {{ e.count }} ({{ e.pct }}%)</span>
            </li>
            <li v-if="!resultsModal.data.errors_seen.length" class="se-fac__hint">
              — {{ $t('agileTraining.scrumEvents.noErrorsMarked') }}
            </li>
          </ul>

          <!-- drill-down -->
          <div v-if="resultsModal.participants.length" class="se-parts">
            <button class="se-fac__participants-toggle"
                    @click="resultsModal.showParticipants = !resultsModal.showParticipants">
              {{ resultsModal.showParticipants ? '▾' : '▸' }}
              {{ $t('agileTraining.scrumEvents.participantsDrill') }}
              ({{ resultsModal.participants.length }})
            </button>
            <div v-if="resultsModal.showParticipants" class="se-parts__body">
              <div v-for="p in resultsModal.participants" :key="p.id" class="se-part">
                <button class="se-part__toggle" @click="togglePart(p.id)">
                  <span>{{ resultsModal.expanded[p.id] ? '▾' : '▸' }}</span>
                  <b>{{ p.display_name }}</b>
                  <span v-if="p.has_answer" class="se-pill">
                    {{ p.health_pct }}%
                  </span>
                  <span v-if="!p.has_answer" class="se-pill se-pill--muted">
                    {{ $t('agileTraining.scrumEvents.noAnswer') }}
                  </span>
                </button>
                <div v-if="resultsModal.expanded[p.id] && p.has_answer" class="se-part__body">
                  <div class="se-board se-board--mini">
                    <div v-for="stage in p.stages" :key="stage.key"
                         class="se-col se-col--mini" :class="'se-col--' + stage.color">
                      <div class="se-col__head">
                        <h5>{{ stage.title }}
                          <span class="se-pill" :class="'se-pill--' + (stage.color || 'gray')">
                            {{ stage.score }}/{{ stage.max_score }}
                          </span>
                        </h5>
                      </div>
                      <div v-for="cat in categoryOrder" :key="cat" class="se-col__cat">
                        <div class="se-col__cat-title">{{ catLabel(cat) }}</div>
                        <ul class="se-col__picks">
                          <li v-for="pk in (stage.categories[cat]?.picks || [])" :key="pk.key"
                              class="se-pick"
                              :class="{
                                'se-pick--green': (stage.categories[cat]?.green || []).includes(pk.key),
                                'se-pick--yellow': (stage.categories[cat]?.yellow || []).includes(pk.key),
                                'se-pick--red': (stage.categories[cat]?.red || []).includes(pk.key),
                              }">
                            {{ pk.title }}
                          </li>
                          <li v-if="!(stage.categories[cat]?.picks || []).length"
                              class="se-fac__hint">—</li>
                        </ul>
                      </div>
                    </div>
                  </div>

                  <div v-if="(p.errors_seen || []).length" class="se-part__errors">
                    ⚠️ <b>{{ $t('agileTraining.scrumEvents.errorsSeen') }}:</b>
                    <span v-for="(e, i) in p.errors_seen" :key="e">
                      {{ $t('agileTraining.scrumEvents.errors.' + e + '.title') }}<span v-if="i < p.errors_seen.length - 1">, </span>
                    </span>
                  </div>

                  <div v-if="p.custom" class="se-part__custom">
                    ✨ <b>{{ $t('agileTraining.scrumEvents.customMode') }}:</b>
                    <span v-if="p.custom.context_key">
                      {{ $t('agileTraining.scrumEvents.customs.' + p.custom.context_key + '.title') }}
                    </span>
                    <div v-if="p.custom.note" class="se-fac__hint">„{{ p.custom.note }}“</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка: сравнение всех групп -->
    <div v-if="compareAll.open" class="se-modal" @click.self="closeCompareAll">
      <div class="se-modal__body se-modal__body--wide">
        <div class="se-modal__head">
          <h3>🏁 {{ $t('agileTraining.scrumEvents.leaderboard') }}</h3>
          <button class="se-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="se-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="se-modal__lead">
            {{ $t('agileTraining.scrumEvents.avgHealth') }}:
            <b>{{ compareAll.data.totals.avg_health_pct || 0 }}%</b>
            · {{ $t('agileTraining.facilitator.participants',
                    { n: compareAll.data.totals.participants || 0 },
                    compareAll.data.totals.participants || 0) }}
          </p>

          <div v-if="compareAll.data.facilitator_content" class="se-fac__reference se-fac__reference--compare">
            <h4 class="se-section-title">📋 {{ $t('agileTraining.scrumEvents.facilitatorReferenceTitle') }}</h4>
            <p class="se-fac__reference-lead">{{ $t('agileTraining.scrumEvents.facilitatorReferenceLead') }}</p>
            <div v-for="s in compareAll.data.facilitator_content.stages" :key="'cfref-'+s.key" class="se-ref-stage">
              <h5 class="se-ref-stage__title">
                <span class="se-ref-stage__emoji">{{ stageEmoji(s.key) }}</span> {{ s.title }}
              </h5>
              <div v-for="cat in compareAll.data.facilitator_content.categories" :key="'cfref-'+s.key+'-'+cat" class="se-ref-cat">
                <div class="se-col__cat-title">{{ $t('agileTraining.scrumEvents.cat.' + cat) }}</div>
                <div class="se-ref-cols">
                  <div class="se-ref-block se-ref-block--exp">
                    <div class="se-ref-block__label">{{ $t('agileTraining.scrumEvents.refExpected') }}</div>
                    <ul class="se-ref-pills">
                      <li
                        v-for="k in (compareAll.data.facilitator_content.reference?.[s.key]?.expected?.[cat] || [])"
                        :key="'ce-'+s.key+'-'+cat+'-'+k"
                        class="se-ref-pill se-ref-pill--expected"
                      >{{ refCardTitle(compareAll.data.facilitator_content, cat, k) }}</li>
                      <li
                        v-if="!(compareAll.data.facilitator_content.reference?.[s.key]?.expected?.[cat] || []).length"
                        class="se-fac__hint"
                      >—</li>
                    </ul>
                  </div>
                  <div class="se-ref-block se-ref-block--acc">
                    <div class="se-ref-block__label">{{ $t('agileTraining.scrumEvents.refAcceptable') }}</div>
                    <ul class="se-ref-pills">
                      <li
                        v-for="k in (compareAll.data.facilitator_content.reference?.[s.key]?.acceptable?.[cat] || [])"
                        :key="'ca-'+s.key+'-'+cat+'-'+k"
                        class="se-ref-pill se-ref-pill--acceptable"
                      >{{ refCardTitle(compareAll.data.facilitator_content, cat, k) }}</li>
                      <li
                        v-if="!(compareAll.data.facilitator_content.reference?.[s.key]?.acceptable?.[cat] || []).length"
                        class="se-fac__hint"
                      >—</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <h4 class="se-section-title">🏆 {{ $t('agileTraining.scrumEvents.bestGroups') }}</h4>
          <ol class="se-leaderboard">
            <li v-for="(g, idx) in compareAll.data.leaderboard" :key="g.id">
              <b>{{ idx + 1 }}.</b> {{ g.name }}
              <span class="se-pill se-pill--good">{{ g.avg_health_pct }}%</span>
              <span class="se-fac__hint">
                · {{ $t('agileTraining.facilitator.participants',
                         { n: g.participants_count }, g.participants_count) }}
              </span>
            </li>
            <li v-if="!compareAll.data.leaderboard.length" class="se-fac__hint">
              — {{ $t('agileTraining.scrumEvents.noAnswersYet') }}
            </li>
          </ol>

          <h4 class="se-section-title">📊 {{ $t('agileTraining.scrumEvents.groupScoreboard') }}</h4>
          <table class="se-heatmap">
            <thead>
              <tr>
                <th>{{ $t('agileTraining.facilitator.groups') }}</th>
                <th>{{ $t('agileTraining.facilitator.participants', { n: 2 }, 2) }}</th>
                <th>{{ $t('agileTraining.scrumEvents.avgHealth') }}</th>
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
  name: 'AgileScrumEventsFacilitator',
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
      categoryOrder: ['goals', 'participants', 'artifacts', 'time', 'duration'],
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
    catLabel(cat) { return this.$t('agileTraining.scrumEvents.cat.' + cat); },
    heatmapClass(v) {
      if (v >= 70) return 'se-heatmap__ok';
      if (v >= 40) return 'se-heatmap__warn';
      return 'se-heatmap__bad';
    },
    stageEmoji(key) {
      return { planning: '📋', daily: '🔄', review: '📊', retro: '🛠️' }[key] || '•';
    },
    refCardTitle(fc, cat, key) {
      for (const c of (fc.cards[cat] || [])) if (c.key === key) return c.title;
      return key;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const r = await axios.get('/api/agile-training/sessions',
          { headers: this.authHeaders() });
        this.sessions = (r.data.sessions || [])
          .filter(s => s.exercise_key === 'scrum_events');
      } catch (e) { console.error(e); }
      finally { this.loadingSessions = false; }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      try {
        const r = await axios.post('/api/agile-training/sessions',
          { title, locale: this.newSessionLocale, exercise_key: 'scrum_events' },
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
        await axios.post(`/api/agile-training/scrum-events/groups/${g.id}/reset`, {},
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
          `/api/agile-training/scrum-events/groups/${g.id}/results`,
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
          `/api/agile-training/scrum-events/groups/${g.id}/participants`,
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
          `/api/agile-training/scrum-events/sessions/${this.activeSession.id}/results`,
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
.se-fac { max-width: 1120px; margin: 0 auto; padding: 24px 20px 60px; color: #0f172a; }
.se-fac__head { display: flex; justify-content: space-between; align-items: flex-end; flex-wrap: wrap; gap: 12px; margin-bottom: 22px; }
.se-fac__head h1 { margin: 0 0 6px; font-size: 24px; }
.se-fac__sub { margin: 0; color: #64748b; font-size: 14px; }
.se-fac__back { color: #0891b2 !important; text-decoration: none; font-weight: 600; }
.se-fac__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 22px 20px; margin-bottom: 16px; }

.se-fac__create, .se-fac__add-group { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.se-fac__create input, .se-fac__add-group input, .se-fac__locale {
  flex: 1 1 220px; padding: 8px 12px; border-radius: 12px; border: 1px solid #cbd5e1; font-size: 14px;
}
.se-fac__create button, .se-fac__add-group button {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important; border: none !important; border-radius: 12px !important;
  padding: 8px 18px !important; font-weight: 700; cursor: pointer;
}

.se-fac__empty, .se-fac__hint { color: #64748b; font-size: 13px; }
.se-fac__list, .se-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.se-fac__item, .se-fac__group {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 14px; border: 1px solid #e2e8f0; border-radius: 14px;
  gap: 12px; flex-wrap: wrap;
}
.se-fac__item-title, .se-fac__group-name { font-weight: 700; font-size: 15px; margin-bottom: 4px; }
.se-fac__item-meta { display: flex; gap: 8px; align-items: center; font-size: 12px; color: #64748b; flex-wrap: wrap; }
.se-fac__badge { background: #e2e8f0; padding: 2px 8px; border-radius: 10px; font-weight: 700; }
.se-fac__group-main { flex: 1; min-width: 220px; }
.se-fac__link { margin-top: 8px; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.se-fac__link code { background: #f1f5f9; padding: 4px 8px; border-radius: 8px; font-size: 12px; }
.se-fac__copy {
  background: #e2e8f0 !important; border: none !important; padding: 4px 12px !important;
  border-radius: 10px !important; font-weight: 700; cursor: pointer; font-size: 12px;
}
.se-fac__copy:hover { background: #cbd5e1 !important; }
.se-fac__open-btn {
  background: linear-gradient(135deg, #14b8a6, #0891b2) !important;
  color: #fff !important; border: none !important; border-radius: 12px !important;
  padding: 8px 16px !important; cursor: pointer; font-weight: 700;
}
.se-fac__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.se-fac__active-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 18px; flex-wrap: wrap; }
.se-fac__active-title { font-size: 20px; font-weight: 800; margin-bottom: 4px; }
.se-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.se-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; margin-top: 10px; }

/* Modal */
.se-modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.5); z-index: 1000; display: flex; align-items: flex-start; justify-content: center; overflow-y: auto; padding: 20px; }
.se-modal__body { background: #fff; border-radius: 18px; width: 100%; max-width: 880px; padding: 22px; position: relative; }
.se-modal__body--wide { max-width: 1080px; }
.se-modal__head { display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 14px; }
.se-modal__close { background: #f1f5f9 !important; border: none !important; width: 32px; height: 32px; border-radius: 10px !important; cursor: pointer; font-weight: 700; }
.se-modal__close:hover { background: #e2e8f0 !important; }
.se-modal__lead { color: #475569; font-size: 14px; margin: 0 0 12px; }

/* Board */
.se-board { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.se-board--mini { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 8px; }
.se-col {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px;
  padding: 12px; display: flex; flex-direction: column; gap: 10px;
}
.se-col--mini { padding: 8px; gap: 6px; }
.se-col--green { border-color: #86efac; background: #f0fdf4; }
.se-col--yellow { border-color: #fde68a; background: #fffbeb; }
.se-col--red { border-color: #fca5a5; background: #fef2f2; }
.se-col__head { display: flex; flex-direction: column; gap: 6px; }
.se-col__head h4, .se-col__head h5 { margin: 0; font-size: 14px; font-weight: 800; }
.se-col__colors { display: flex; gap: 4px; flex-wrap: wrap; }
.se-col__cat { border-top: 1px dashed #e2e8f0; padding-top: 6px; }
.se-col__cat-title { font-size: 11px; color: #64748b; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 4px; }
.se-col__picks { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
.se-pick { display: flex; justify-content: space-between; align-items: center; padding: 4px 6px; border-radius: 8px; background: #fff; border: 1px solid transparent; }
.se-pick--green { background: #dcfce7; border-color: #86efac; }
.se-pick--yellow { background: #fef3c7; border-color: #fde68a; }
.se-pick--red { background: #fee2e2; border-color: #fca5a5; }
.se-pick__title { flex: 1; margin-right: 6px; }
.se-pick__pct { color: #64748b; font-weight: 700; }

.se-pill { display: inline-block; background: #e2e8f0; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.se-pill--good { background: #86efac; color: #064e3b; }
.se-pill--green { background: #dcfce7; color: #047857; }
.se-pill--yellow { background: #fef3c7; color: #92400e; }
.se-pill--red { background: #fee2e2; color: #991b1b; }
.se-pill--muted { background: #f1f5f9; color: #64748b; }
.se-pill--gray { background: #e2e8f0; color: #475569; }

.se-section-title { margin: 18px 0 8px; font-size: 15px; font-weight: 800; }
.se-errors { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; font-size: 13px; }
.se-leaderboard { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 6px; font-size: 14px; }
.se-leaderboard li { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.se-heatmap { width: 100%; border-collapse: collapse; margin-top: 8px; }
.se-heatmap th, .se-heatmap td { text-align: left; padding: 8px; border-bottom: 1px solid #e2e8f0; font-size: 13px; }
.se-heatmap__ok { background: #dcfce7; color: #047857; font-weight: 700; }
.se-heatmap__warn { background: #fef3c7; color: #92400e; font-weight: 700; }
.se-heatmap__bad { background: #fee2e2; color: #991b1b; font-weight: 700; }

/* participant drill-down */
.se-parts { margin-top: 16px; border-top: 1px dashed #e2e8f0; padding-top: 10px; }
.se-fac__participants-toggle {
  background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; padding: 8px 14px !important;
  border-radius: 12px !important; cursor: pointer; font-weight: 700; font-size: 13px;
}
.se-fac__participants-toggle:hover { background: #e2e8f0 !important; }
.se-parts__body { display: flex; flex-direction: column; gap: 8px; margin-top: 10px; }
.se-part { border: 1px solid #e2e8f0; border-radius: 14px; background: #fff; overflow: hidden; }
.se-part__toggle {
  width: 100%; background: #f8fafc !important; border: none !important; padding: 10px 14px !important;
  cursor: pointer; display: flex; align-items: center; gap: 8px; text-align: left;
  font-size: 14px;
}
.se-part__toggle:hover { background: #f1f5f9 !important; }
.se-part__body { padding: 10px 14px 14px; }
.se-part__errors { margin-top: 8px; font-size: 13px; color: #991b1b; }
.se-part__custom { margin-top: 8px; font-size: 13px; color: #0891b2; }

/* Reference answer — debrief with participants */
.se-fac__reference { margin: 0 0 20px; padding: 14px; background: #f0fdfa; border: 1px solid #a7f3d0; border-radius: 14px; }
.se-fac__reference--compare { background: #fffbeb; border-color: #fde68a; }
.se-fac__reference-lead { color: #475569; font-size: 13px; margin: 0 0 10px; line-height: 1.45; }
.se-ref-stage { margin-top: 12px; }
.se-ref-stage__title { margin: 0 0 8px; font-size: 14px; font-weight: 800; display: flex; align-items: center; gap: 6px; }
.se-ref-stage__emoji { font-size: 16px; }
.se-ref-cat { border-top: 1px dashed #cbd5e1; padding: 8px 0; }
.se-ref-cat:first-of-type { border-top: none; padding-top: 0; }
.se-ref-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.se-ref-block { font-size: 12px; }
.se-ref-block__label { font-weight: 700; color: #64748b; margin-bottom: 4px; }
.se-ref-pills { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: 4px; }
.se-ref-pill { padding: 3px 8px; border-radius: 6px; font-size: 12px; line-height: 1.3; }
.se-ref-pill--expected { background: #dcfce7; border: 1px solid #86efac; color: #14532d; }
.se-ref-pill--acceptable { background: #fef3c7; border: 1px solid #fde68a; color: #92400e; }
@media (max-width: 700px) { .se-ref-cols { grid-template-columns: 1fr; } }

@media (max-width: 900px) {
  .se-board, .se-board--mini { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 560px) {
  .se-board, .se-board--mini { grid-template-columns: 1fr; }
}
</style>
