<template>
  <div class="cyn-fac">
    <header class="cyn-fac__head">
      <div>
        <h1>🧭 {{ $t('agileTraining.cynefin.facTitle') }}</h1>
        <p class="cyn-fac__sub">{{ $t('agileTraining.cynefin.facSubtitle') }}</p>
      </div>
      <div class="cyn-fac__head-actions">
        <router-link class="cyn-fac__back" to="/agile-training">← {{ $t('agileTraining.hub.backHome') }}</router-link>
      </div>
    </header>

    <!-- Список сессий и создание -->
    <section v-if="!activeSession" class="cyn-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="cyn-fac__create" @submit.prevent="createSession">
        <input
          v-model="newSessionTitle"
          :placeholder="$t('agileTraining.facilitator.newSessionTitle')"
          required
          maxlength="255"
        />
        <select v-model="newSessionLocale" class="cyn-fac__locale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="cyn-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="sessions.length === 0" class="cyn-fac__empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </div>
      <ul v-else class="cyn-fac__list">
        <li v-for="s in sessions" :key="s.id" class="cyn-fac__item">
          <div class="cyn-fac__item-main">
            <div class="cyn-fac__item-title">{{ s.title }}</div>
            <div class="cyn-fac__item-meta">
              <span class="cyn-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }) }}</span>
            </div>
          </div>
          <button class="cyn-fac__open-btn" @click="openSession(s.id)">
            {{ $t('agileTraining.facilitator.open') }}
          </button>
        </li>
      </ul>
    </section>

    <!-- Активная сессия -->
    <section v-else class="cyn-fac__section">
      <div class="cyn-fac__active-head">
        <div>
          <div class="cyn-fac__active-title">{{ activeSession.title }}</div>
          <div class="cyn-fac__item-meta">
            <span class="cyn-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="cyn-fac__active-actions">
          <button class="btn-ghost" @click="openCompareAll" :disabled="!groups.length">
            📊 {{ $t('agileTraining.facilitator.compareAll') }}
          </button>
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="cyn-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="cyn-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="groups.length === 0" class="cyn-fac__empty">
        {{ $t('agileTraining.facilitator.noGroups') }}
      </div>
      <ul v-else class="cyn-fac__groups">
        <li v-for="g in groups" :key="g.id" class="cyn-fac__group">
          <div class="cyn-fac__group-main">
            <div class="cyn-fac__group-name">{{ g.name }}</div>
            <div class="cyn-fac__item-meta">
              <span>{{ $t('agileTraining.facilitator.participants', { n: g.participants_count || 0 }) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.cynefin.answersCount', { n: g.answers_count || 0 }) }}</span>
              <span>·</span>
              <span :class="['cyn-fac__status', 'cyn-fac__status--' + (g.status || 'not_started')]">
                {{ $t('agileTraining.facilitator.status.' + (g.status || 'not_started')) }}
              </span>
            </div>
            <div class="cyn-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="cyn-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
            </div>
          </div>
          <div class="cyn-fac__group-actions">
            <button class="btn-ghost" @click="openGroupResults(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.facilitator.reset') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <!-- Модалка результатов одной группы -->
    <div v-if="resultsModal.open" class="cyn-modal" @click.self="closeResults">
      <div class="cyn-modal__body">
        <div class="cyn-modal__head">
          <h3>{{ $t('agileTraining.cynefin.groupResults') }}: {{ resultsModal.group?.name }}</h3>
          <button class="cyn-modal__close" @click="closeResults">✕</button>
        </div>
        <div v-if="resultsModal.loading" class="cyn-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="resultsModal.data">
          <p class="cyn-modal__lead">
            {{ $t('agileTraining.facilitator.participants', { n: resultsModal.data.participants_count || 0 }) }}
          </p>
          <div v-for="row in resultsModal.data.per_case" :key="row.key" class="cyn-case-row">
            <div class="cyn-case-row__head">
              <div class="cyn-case-row__title">
                <span class="cyn-case-row__cat">{{ row.category }}</span>
                <b>{{ row.title }}</b>
              </div>
              <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + row.expert_domain]">
                {{ $t('agileTraining.cynefin.expertDomain') }}: {{ $t('agileTraining.cynefin.domain.' + row.expert_domain) }}
              </span>
            </div>
            <p class="cyn-case-row__scenario">{{ row.scenario }}</p>
            <div class="cyn-bars">
              <div v-for="dk in DOMAIN_KEYS" :key="dk" class="cyn-bars__row">
                <div class="cyn-bars__label">{{ $t('agileTraining.cynefin.domain.' + dk) }}</div>
                <div class="cyn-bars__track">
                  <div class="cyn-bars__fill"
                       :class="{ 'cyn-bars__fill--expert': dk === row.expert_domain }"
                       :style="{ width: (row.stats.percent[dk] || 0) + '%' }" />
                </div>
                <div class="cyn-bars__val">{{ row.stats.percent[dk] || 0 }}%</div>
              </div>
            </div>
            <p class="cyn-case-row__rationale" v-if="row.expert_rationale">
              <b>💡</b> {{ row.expert_rationale }}
            </p>
          </div>
        </div>
      </div>
    </div>

    <!-- Модалка сравнения всех групп -->
    <div v-if="compareAll.open" class="cyn-modal" @click.self="closeCompareAll">
      <div class="cyn-modal__body cyn-modal__body--wide">
        <div class="cyn-modal__head">
          <h3>📊 {{ $t('agileTraining.facilitator.compareAllTitle') }}</h3>
          <button class="cyn-modal__close" @click="closeCompareAll">✕</button>
        </div>
        <div v-if="compareAll.loading" class="cyn-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="compareAll.data">
          <p class="cyn-modal__lead">{{ $t('agileTraining.facilitator.compareAllLead') }}</p>

          <div class="cyn-totals">
            <div class="cyn-totals__item">
              <span class="cyn-totals__val">{{ compareAll.data.totals.groups }}</span>
              <span class="cyn-totals__lbl">{{ $t('agileTraining.facilitator.totalsGroups') }}</span>
            </div>
            <div class="cyn-totals__item">
              <span class="cyn-totals__val">{{ compareAll.data.totals.participants }}</span>
              <span class="cyn-totals__lbl">{{ $t('agileTraining.facilitator.totalsParticipants') }}</span>
            </div>
            <div class="cyn-totals__item">
              <span class="cyn-totals__val">{{ compareAll.data.totals.answers }}</span>
              <span class="cyn-totals__lbl">{{ $t('agileTraining.facilitator.totalsAnswers') }}</span>
            </div>
          </div>

          <div class="cyn-top">
            <div class="cyn-top__col">
              <h4>🔥 {{ $t('agileTraining.facilitator.mostSplit') }}</h4>
              <p class="cyn-top__hint">{{ $t('agileTraining.cynefin.mostSplitHint') }}</p>
              <div v-if="!compareAll.data.most_split.length" class="cyn-fac__empty">{{ $t('agileTraining.facilitator.noData') }}</div>
              <ul class="cyn-top__list">
                <li v-for="r in compareAll.data.most_split" :key="r.key">
                  <div class="cyn-top__title">{{ r.title }}</div>
                  <div class="cyn-top__meta">
                    <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + r.expert_domain]">
                      {{ $t('agileTraining.cynefin.domain.' + r.expert_domain) }}
                    </span>
                    <span>Δ {{ r.spread }}%</span>
                    <span>avg {{ r.avg_expert_pct }}%</span>
                  </div>
                </li>
              </ul>
            </div>
            <div class="cyn-top__col">
              <h4>🤝 {{ $t('agileTraining.facilitator.mostAligned') }}</h4>
              <p class="cyn-top__hint">{{ $t('agileTraining.cynefin.mostAlignedHint') }}</p>
              <div v-if="!compareAll.data.most_aligned.length" class="cyn-fac__empty">{{ $t('agileTraining.facilitator.noData') }}</div>
              <ul class="cyn-top__list">
                <li v-for="r in compareAll.data.most_aligned" :key="r.key">
                  <div class="cyn-top__title">{{ r.title }}</div>
                  <div class="cyn-top__meta">
                    <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + r.expert_domain]">
                      {{ $t('agileTraining.cynefin.domain.' + r.expert_domain) }}
                    </span>
                    <span>Δ {{ r.spread }}%</span>
                    <span>avg {{ r.avg_expert_pct }}%</span>
                  </div>
                </li>
              </ul>
            </div>
          </div>

          <h4 class="cyn-heatmap__title">🧊 {{ $t('agileTraining.cynefin.heatmapTitle') }}</h4>
          <p class="cyn-top__hint">{{ $t('agileTraining.cynefin.heatmapHint') }}</p>
          <div class="cyn-heatmap-wrap">
            <table class="cyn-heatmap">
              <thead>
                <tr>
                  <th>{{ $t('agileTraining.facilitator.principleColumn') }}</th>
                  <th v-for="g in compareAll.data.groups" :key="g.id">{{ g.name }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in compareAll.data.cross_cases" :key="row.key">
                  <td>
                    <div><b>{{ row.title }}</b></div>
                    <div class="cyn-heatmap__expert">
                      <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + row.expert_domain]">
                        {{ $t('agileTraining.cynefin.domain.' + row.expert_domain) }}
                      </span>
                    </div>
                  </td>
                  <td v-for="cell in row.by_group" :key="cell.group_id"
                      :class="heatmapClass(cell.expert_pct, cell.total)"
                      :title="cellTitle(row, cell)">
                    <template v-if="cell.total">{{ cell.expert_pct }}%</template>
                    <template v-else>—</template>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/**
 * Страница фасилитатора для упражнения Cynefin.
 * Использует общие эндпоинты сессий (/api/agile-training/sessions/...) и
 * специфичные для Cynefin (/api/agile-training/cynefin/...).
 *
 * Стиль и UX близок к AgilePrinciplesFacilitator, но данные и модалки
 * работают с доменами/кейсами, а не с принципами.
 */
import axios from 'axios';

export default {
  name: 'AgileCynefinFacilitator',
  data() {
    const lang = (typeof localStorage !== 'undefined' && localStorage.getItem('language')) || null;
    return {
      DOMAIN_KEYS: ['obvious', 'complicated', 'complex', 'chaotic'],
      sessions: [],
      loadingSessions: false,
      newSessionTitle: '',
      newSessionLocale: lang === 'en' ? 'en' : 'ru',
      activeSession: null,
      groups: [],
      newGroupName: '',
      copiedSlug: '',
      resultsModal: { open: false, group: null, loading: false, data: null },
      compareAll: { open: false, loading: false, data: null },
    };
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: 'Bearer ' + token } : {};
    },
    publicLink(slug) {
      return `${window.location.origin}/g/${slug}`;
    },
    formatDate(iso) {
      if (!iso) return '';
      const d = new Date(iso);
      if (Number.isNaN(+d)) return iso;
      return d.toLocaleDateString();
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        const all = res.data.sessions || [];
        this.sessions = all.filter(s => (s.exercise_key || 'agile_principles') === 'cynefin');
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
          exercise_key: 'cynefin',
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
        // Используем cynefin results — он возвращает и описание сессии, и
        // группы с актуальными счётчиками (participants/answers/status/slug).
        const res = await axios.get(
          `/api/agile-training/cynefin/sessions/${id}/results`,
          { headers: this.authHeaders() },
        );
        this.activeSession = res.data.session;
        // Нормализуем имена для шаблона (participants_count/answers_count).
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
    closeSession() {
      this.activeSession = null;
      this.groups = [];
    },
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
        await axios.post(`/api/agile-training/cynefin/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
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
      } catch (_) {
        alert('Failed to copy link');
      }
    },
    async openGroupResults(g) {
      this.resultsModal = { open: true, group: g, loading: true, data: null };
      try {
        const res = await axios.get(`/api/agile-training/cynefin/groups/${g.id}/results`, {
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
    },
    closeResults() {
      this.resultsModal = { open: false, group: null, loading: false, data: null };
    },
    async openCompareAll() {
      if (!this.activeSession) return;
      this.compareAll = { open: true, loading: true, data: null };
      try {
        const res = await axios.get(
          `/api/agile-training/cynefin/sessions/${this.activeSession.id}/results`,
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
    closeCompareAll() {
      this.compareAll = { open: false, loading: false, data: null };
    },
    heatmapClass(pct, total) {
      if (!total) return 'cyn-heatmap__cell cyn-heatmap__cell--empty';
      let level = 'low';
      if (pct >= 70) level = 'high';
      else if (pct >= 40) level = 'mid';
      return 'cyn-heatmap__cell cyn-heatmap__cell--' + level;
    },
    cellTitle(row, cell) {
      if (!cell.total) return this.$t('agileTraining.facilitator.noAnswersYet');
      const parts = [`${cell.group_name}: ${cell.total} ${this.$t('agileTraining.cynefin.answersShort')}`];
      this.DOMAIN_KEYS.forEach((dk) => {
        parts.push(`${this.$t('agileTraining.cynefin.domain.' + dk)}: ${cell.percent_by_domain[dk] || 0}%`);
      });
      return parts.join('\n');
    },
  },
};
</script>

<style scoped>
.cyn-fac {
  max-width: 1100px;
  margin: 32px auto 64px;
  padding: 0 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  color: #0f172a;
}
.cyn-fac__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  gap: 16px;
}
.cyn-fac__head h1 { margin: 0 0 4px; font-size: 28px; letter-spacing: -0.3px; }
.cyn-fac__sub { margin: 0; color: #64748b; }
.cyn-fac__back {
  padding: 8px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #e5e7eb;
  color: #111;
  text-decoration: none;
  font-weight: 600;
  font-size: 13px;
}
.cyn-fac__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px; margin-bottom: 20px; }
.cyn-fac__section h2, .cyn-fac__section h3 { margin: 0 0 14px; }
.cyn-fac__create {
  display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;
}
.cyn-fac__create input, .cyn-fac__add-group input, .cyn-fac__locale {
  flex: 1; min-width: 180px; padding: 10px 14px; border: 1px solid #cbd5e1;
  border-radius: 10px; font: inherit;
}
.cyn-fac__locale { flex: 0 0 auto; }
.cyn-fac__create button, .cyn-fac__add-group button, .cyn-fac__open-btn {
  padding: 10px 18px; border: none; border-radius: 10px; background: #111; color: #fff;
  font-weight: 600; cursor: pointer;
}
.cyn-fac__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.cyn-fac__item, .cyn-fac__group {
  display: flex; justify-content: space-between; gap: 16px; align-items: flex-start;
  padding: 14px 16px; border: 1px solid #e5e7eb; border-radius: 12px; background: #fafafa;
}
.cyn-fac__item-title { font-weight: 600; margin-bottom: 4px; }
.cyn-fac__item-meta { color: #64748b; font-size: 13px; display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
.cyn-fac__badge {
  background: #ede9fe; color: #6d28d9; padding: 2px 8px; border-radius: 999px;
  font-weight: 700; font-size: 11px; letter-spacing: 0.5px;
}
.cyn-fac__hint, .cyn-fac__empty { color: #64748b; padding: 10px 0; }
.cyn-fac__active-head { display: flex; justify-content: space-between; flex-wrap: wrap; gap: 12px; margin-bottom: 14px; }
.cyn-fac__active-title { font-size: 22px; font-weight: 700; margin-bottom: 4px; }
.cyn-fac__active-actions { display: flex; gap: 8px; flex-wrap: wrap; }
.btn-ghost { padding: 8px 14px; border-radius: 10px; border: 1px solid #cbd5e1; background: #fff; color: #0f172a; cursor: pointer; font: inherit; font-weight: 600; }
.btn-ghost:hover { border-color: #7c3aed; color: #7c3aed; }
.btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { padding: 8px 14px; border-radius: 10px; border: 1px solid #fecaca; background: #fff1f2; color: #b91c1c; cursor: pointer; font: inherit; font-weight: 600; }
.cyn-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 10px; }
.cyn-fac__add-group { display: flex; gap: 8px; flex-wrap: wrap; }
.cyn-fac__groups { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.cyn-fac__group-main { flex: 1; min-width: 0; }
.cyn-fac__group-name { font-weight: 700; margin-bottom: 4px; }
.cyn-fac__status { padding: 1px 8px; border-radius: 999px; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; }
.cyn-fac__status--not_started { background: #f1f5f9; color: #475569; }
.cyn-fac__status--in_progress { background: #fef3c7; color: #92400e; }
.cyn-fac__status--completed { background: #dcfce7; color: #166534; }
.cyn-fac__link { margin-top: 8px; display: flex; gap: 8px; align-items: center; }
.cyn-fac__link code { background: #f8fafc; padding: 4px 8px; border-radius: 6px; font-size: 12px; word-break: break-all; }
.cyn-fac__copy { padding: 6px 12px; border-radius: 8px; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; font-size: 12px; font-weight: 600; }
.cyn-fac__group-actions { display: flex; gap: 6px; flex-direction: column; align-items: flex-end; }

/* Модалка */
.cyn-modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.55); display: flex; align-items: center; justify-content: center; padding: 16px; z-index: 1000; }
.cyn-modal__body { background: #fff; border-radius: 18px; max-width: 760px; width: 100%; max-height: 92vh; overflow-y: auto; padding: 22px 24px; }
.cyn-modal__body--wide { max-width: 1080px; }
.cyn-modal__head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.cyn-modal__head h3 { margin: 0; font-size: 20px; }
.cyn-modal__close { background: transparent; border: none; font-size: 22px; cursor: pointer; color: #475569; }
.cyn-modal__lead { color: #475569; margin: 0 0 14px; }

.cyn-case-row { padding: 14px 0; border-top: 1px solid #eef2f7; }
.cyn-case-row:first-of-type { border-top: none; }
.cyn-case-row__head { display: flex; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.cyn-case-row__cat { color: #7c3aed; font-size: 12px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-right: 6px; }
.cyn-case-row__scenario { color: #334155; margin: 0 0 10px; line-height: 1.55; }
.cyn-case-row__rationale { color: #475569; margin: 10px 0 0; font-size: 13px; line-height: 1.5; }

.cyn-bars { display: flex; flex-direction: column; gap: 6px; }
.cyn-bars__row { display: grid; grid-template-columns: 130px 1fr 44px; gap: 8px; align-items: center; }
.cyn-bars__label { font-size: 13px; color: #334155; }
.cyn-bars__track { background: #eef2f7; border-radius: 999px; height: 10px; overflow: hidden; }
.cyn-bars__fill { height: 100%; background: #cbd5e1; border-radius: 999px; transition: width 0.3s ease; }
.cyn-bars__fill--expert { background: #22c55e; }
.cyn-bars__val { font-size: 12px; color: #64748b; text-align: right; }

.cyn-dom-pill {
  padding: 2px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; letter-spacing: 0.3px;
}
.cyn-dom-pill--obvious { background: #dcfce7; color: #166534; }
.cyn-dom-pill--complicated { background: #dbeafe; color: #1d4ed8; }
.cyn-dom-pill--complex { background: #fce7f3; color: #9d174d; }
.cyn-dom-pill--chaotic { background: #fee2e2; color: #b91c1c; }

.cyn-totals { display: flex; gap: 14px; margin-bottom: 18px; flex-wrap: wrap; }
.cyn-totals__item { background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 14px; padding: 12px 16px; min-width: 120px; display: flex; flex-direction: column; gap: 2px; }
.cyn-totals__val { font-size: 24px; font-weight: 700; color: #6d28d9; }
.cyn-totals__lbl { color: #64748b; font-size: 12px; }

.cyn-top { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 18px; }
.cyn-top h4 { margin: 0 0 4px; }
.cyn-top__hint { color: #64748b; font-size: 12px; margin: 0 0 8px; }
.cyn-top__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.cyn-top__list li { background: #f8fafc; border-radius: 10px; padding: 10px 12px; }
.cyn-top__title { font-weight: 600; margin-bottom: 4px; }
.cyn-top__meta { display: flex; gap: 8px; flex-wrap: wrap; color: #64748b; font-size: 12px; align-items: center; }

.cyn-heatmap__title { margin: 16px 0 2px; }
.cyn-heatmap-wrap { overflow-x: auto; margin-top: 8px; }
.cyn-heatmap { border-collapse: collapse; width: 100%; font-size: 12px; }
.cyn-heatmap th, .cyn-heatmap td { border: 1px solid #eef2f7; padding: 8px 10px; text-align: center; vertical-align: middle; }
.cyn-heatmap thead th { background: #f8fafc; }
.cyn-heatmap tbody td:first-child { text-align: left; min-width: 200px; }
.cyn-heatmap__expert { margin-top: 4px; }
.cyn-heatmap__cell--low { background: #fee2e2; }
.cyn-heatmap__cell--mid { background: #fef9c3; }
.cyn-heatmap__cell--high { background: #dcfce7; }
.cyn-heatmap__cell--empty { color: #94a3b8; background: #fafafa; }

@media (max-width: 720px) {
  .cyn-top { grid-template-columns: 1fr; }
  .cyn-fac__group { flex-direction: column; }
  .cyn-fac__group-actions { align-items: flex-start; flex-direction: row; flex-wrap: wrap; }
  .cyn-bars__row { grid-template-columns: 100px 1fr 40px; }
}
</style>
