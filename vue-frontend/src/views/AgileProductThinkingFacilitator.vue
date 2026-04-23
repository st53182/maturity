<template>
  <div class="pt-fac">
    <header class="pt-fac__head">
      <div>
        <h1>🧠 {{ $t('agileTraining.productThinking.facTitle') }}</h1>
        <p class="pt-fac__sub">{{ $t('agileTraining.productThinking.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="pt-fac__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <section v-if="!activeSession" class="pt-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="pt-fac__create" @submit.prevent="createSession">
        <input
          v-model="newSessionTitle"
          :placeholder="$t('agileTraining.productThinking.newSessionTitle')"
          required
          maxlength="255"
        />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="pt-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="pt-fac__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="pt-fac__list">
        <li v-for="s in sessions" :key="s.id" class="pt-fac__row">
          <div>
            <div class="pt-fac__row-title">{{ s.title }}</div>
            <div class="pt-fac__row-meta">
              <span class="pt-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <div>
            <button class="btn-ghost" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <section v-else class="pt-fac__section">
      <div class="pt-fac__active-head">
        <div>
          <div class="pt-fac__active-title">{{ activeSession.title }}</div>
          <div class="pt-fac__row-meta">
            <span class="pt-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="pt-fac__active-actions">
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="pt-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="pt-fac__add-group" @submit.prevent="addGroup">
          <input
            v-model="newGroupName"
            :placeholder="$t('agileTraining.facilitator.newGroupName')"
            required
            maxlength="120"
          />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="pt-fac__empty">{{ $t('agileTraining.facilitator.noGroups') }}</div>
      <ul v-else class="pt-fac__groups">
        <li v-for="g in groups" :key="g.id" class="pt-fac__group">
          <div class="pt-fac__group-main">
            <div class="pt-fac__group-name">{{ g.name }}</div>
            <div class="pt-fac__row-meta">
              <span>{{ $t('agileTraining.productThinking.facilitator.participantsCount', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.productThinking.facilitator.answersCount', { n: g.answers_count || 0 }, g.answers_count || 0) }}</span>
            </div>
            <div class="pt-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="pt-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
              <a class="pt-fac__open-link" :href="publicLink(g.slug)" target="_blank" rel="noopener">
                {{ $t('agileTraining.productThinking.facilitator.openGroup') }} ↗
              </a>
            </div>
          </div>
          <div class="pt-fac__group-actions">
            <button class="btn-ghost" @click="openParticipants(g)">{{ $t('agileTraining.facilitator.viewResults') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.productThinking.facilitator.resetGroup') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <div v-if="modal.open" class="pt-modal" @click.self="closeModal">
      <div class="pt-modal__body">
        <div class="pt-modal__head">
          <div>
            <h3>{{ $t('agileTraining.productThinking.facilitator.participantsTitle') }}: {{ modal.group?.name }}</h3>
            <p class="pt-modal__sub">
              {{ $t('agileTraining.productThinking.facilitator.participantsCount', { n: totalParticipants }, totalParticipants) }}
              · {{ $t('agileTraining.productThinking.facilitator.answersCount', { n: totalAnswers }, totalAnswers) }}
            </p>
          </div>
          <button class="pt-modal__close" @click="closeModal">✕</button>
        </div>
        <div v-if="modal.loading" class="pt-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="modal.error" class="pt-fac__error">{{ modal.error }}</div>
        <div v-else>
          <div v-if="!participants.length" class="pt-fac__empty">
            {{ $t('agileTraining.productThinking.facilitator.noAnswers') }}
          </div>

          <section v-if="selectedExamples.length" class="pt-examples">
            <h4>{{ $t('agileTraining.productThinking.facilitator.examplesTitle') }}</h4>
            <div class="pt-examples__grid">
              <article v-for="p in selectedExamples" :key="'ex_' + p.id" class="pt-ex">
                <div class="pt-ex__name">{{ p.display_name }}</div>
                <div class="pt-ex__section" v-if="p.user_story">
                  <div class="pt-ex__h">👤 User Story</div>
                  <p>«{{ p.user_story }}»</p>
                </div>
                <div class="pt-ex__section" v-if="p.job_story">
                  <div class="pt-ex__h">🎬 Job Story</div>
                  <p>«{{ p.job_story }}»</p>
                </div>
                <div class="pt-ex__section" v-if="(p.tasks || []).length">
                  <div class="pt-ex__h">🧩 Tasks</div>
                  <ol>
                    <li v-for="t in p.tasks" :key="t.id || t.title">{{ t.title }}</li>
                  </ol>
                </div>
                <div class="pt-ex__section" v-if="(p.improved_tasks || []).length">
                  <div class="pt-ex__h">✨ Improved</div>
                  <ol>
                    <li v-for="t in p.improved_tasks" :key="t.id || t.title">{{ t.title }}</li>
                  </ol>
                </div>
              </article>
            </div>
          </section>

          <section v-if="participants.length" class="pt-discussion">
            <h4>{{ $t('agileTraining.productThinking.facilitator.discussionTitle') }}</h4>
            <ul>
              <li>{{ $t('agileTraining.productThinking.facilitator.discussion1') }}</li>
              <li>{{ $t('agileTraining.productThinking.facilitator.discussion2') }}</li>
              <li>{{ $t('agileTraining.productThinking.facilitator.discussion3') }}</li>
            </ul>
          </section>

          <ul class="pt-fac__participants">
            <li v-for="p in participants" :key="p.id" class="pt-part">
              <div class="pt-part__head">
                <div class="pt-part__name">{{ p.display_name }}</div>
                <div class="pt-part__meta">
                  <span v-if="p.stage">{{ $t('agileTraining.productThinking.facilitator.stageLabel') }}: <b>{{ p.stage }}</b></span>
                  <span v-if="p.chosen_technique">· {{ $t('agileTraining.productThinking.facilitator.techniqueLabel') }}: <b>{{ techLabel(p.chosen_technique) }}</b></span>
                  <span v-if="(p.tasks || []).length">· {{ $t('agileTraining.productThinking.facilitator.tasksCountLabel') }}: {{ p.tasks.length }}</span>
                </div>
                <button
                  v-if="p.has_answer"
                  class="pt-part__pick"
                  @click="togglePick(p.id)"
                  :class="{ 'pt-part__pick--active': pickedIds.has(p.id) }"
                >
                  {{ pickedIds.has(p.id)
                    ? $t('agileTraining.productThinking.facilitator.hideExample')
                    : $t('agileTraining.productThinking.facilitator.pickExample') }}
                </button>
              </div>
              <div class="pt-part__body" v-if="p.has_answer">
                <div class="pt-part__col" v-if="p.user_story">
                  <div class="pt-part__h">👤 User Story</div>
                  <p>«{{ p.user_story }}»</p>
                </div>
                <div class="pt-part__col" v-if="p.job_story">
                  <div class="pt-part__h">🎬 Job Story</div>
                  <p>«{{ p.job_story }}»</p>
                </div>
                <div class="pt-part__col" v-if="(p.tasks || []).length">
                  <div class="pt-part__h">🧩 Tasks</div>
                  <ol>
                    <li v-for="t in p.tasks" :key="t.id || t.title">{{ t.title }}<span v-if="t.note" class="pt-muted"> — {{ t.note }}</span></li>
                  </ol>
                </div>
                <div class="pt-part__col" v-if="(p.improved_tasks || []).length">
                  <div class="pt-part__h">✨ Improved</div>
                  <ol>
                    <li v-for="t in p.improved_tasks" :key="t.id || t.title">{{ t.title }}<span v-if="t.note" class="pt-muted"> — {{ t.note }}</span></li>
                  </ol>
                </div>
              </div>
              <div v-else class="pt-part__empty">—</div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgileProductThinkingFacilitator',
  data() {
    return {
      loadingSessions: true,
      sessions: [],
      activeSession: null,
      groups: [],
      newSessionTitle: '',
      newSessionLocale: 'ru',
      newGroupName: '',
      copiedSlug: '',
      modal: { open: false, loading: false, error: '', group: null },
      participants: [],
      pickedIds: new Set(),
    };
  },
  computed: {
    totalParticipants() { return (this.modal.group && this.modal.group.participants_count) || this.participants.length; },
    totalAnswers() { return this.participants.filter(p => p.has_answer).length; },
    selectedExamples() {
      return this.participants.filter(p => this.pickedIds.has(p.id));
    },
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    _authHeaders() {
      const token = localStorage.getItem('token') || localStorage.getItem('authToken');
      return token ? { Authorization: 'Bearer ' + token } : {};
    },
    formatDate(iso) {
      if (!iso) return '';
      try {
        const d = new Date(iso);
        return d.toLocaleDateString(this.$i18n.locale === 'en' ? 'en-GB' : 'ru-RU');
      } catch (_) { return iso; }
    },
    publicLink(slug) {
      return `${window.location.origin}/g/${slug}`;
    },
    techLabel(t) {
      if (t === 'spidr') return this.$t('agileTraining.productThinking.summary.techniqueSpidr');
      if (t === 'seven_dim') return this.$t('agileTraining.productThinking.summary.techniqueSevenDim');
      return t;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this._authHeaders() });
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'product_thinking');
      } catch (_) {
        this.sessions = [];
      } finally {
        this.loadingSessions = false;
      }
    },
    async createSession() {
      const title = (this.newSessionTitle || '').trim();
      if (!title) return;
      try {
        const res = await axios.post('/api/agile-training/sessions', {
          title,
          locale: this.newSessionLocale || 'ru',
          exercise_key: 'product_thinking',
        }, { headers: this._authHeaders() });
        this.sessions.unshift({
          id: res.data.id,
          title: res.data.title,
          locale: res.data.locale,
          exercise_key: res.data.exercise_key,
          groups_count: 0,
          created_at: res.data.created_at,
        });
        this.newSessionTitle = '';
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    async openSession(sessionId) {
      try {
        const res = await axios.get(`/api/agile-training/sessions/${sessionId}`, { headers: this._authHeaders() });
        this.activeSession = res.data;
        this.groups = (res.data.groups || []).map(g => ({
          id: g.id,
          name: g.name,
          slug: g.slug,
          participants_count: g.participants,
          answers_count: g.answers,
        }));
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    closeSession() {
      this.activeSession = null;
      this.groups = [];
    },
    async deleteSession() {
      if (!this.activeSession) return;
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSession.id}`, { headers: this._authHeaders() });
        this.closeSession();
        await this.loadSessions();
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    async addGroup() {
      if (!this.activeSession) return;
      const name = (this.newGroupName || '').trim();
      if (!name) return;
      try {
        const res = await axios.post(`/api/agile-training/sessions/${this.activeSession.id}/groups`, { name }, { headers: this._authHeaders() });
        this.groups.push({
          id: res.data.id,
          name: res.data.name,
          slug: res.data.slug,
          participants_count: 0,
          answers_count: 0,
        });
        this.newGroupName = '';
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    async removeGroup(g) {
      if (!window.confirm(this.$t('agileTraining.facilitator.confirmDeleteGroup', { name: g.name }))) return;
      try {
        await axios.delete(`/api/agile-training/groups/${g.id}`, { headers: this._authHeaders() });
        this.groups = this.groups.filter(x => x.id !== g.id);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    async resetGroup(g) {
      if (!window.confirm(this.$t('agileTraining.productThinking.facilitator.resetConfirm'))) return;
      try {
        await axios.post(`/api/agile-training/product-thinking/groups/${g.id}/reset`, {}, { headers: this._authHeaders() });
        g.answers_count = 0;
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    copyLink(slug) {
      const url = this.publicLink(slug);
      try {
        navigator.clipboard.writeText(url);
        this.copiedSlug = slug;
        setTimeout(() => { if (this.copiedSlug === slug) this.copiedSlug = ''; }, 1500);
      } catch (_) { /* noop */ }
    },
    togglePick(pid) {
      const next = new Set(this.pickedIds);
      if (next.has(pid)) next.delete(pid); else next.add(pid);
      this.pickedIds = next;
    },
    async openParticipants(g) {
      this.modal = { open: true, loading: true, error: '', group: g };
      this.participants = [];
      this.pickedIds = new Set();
      try {
        const res = await axios.get(`/api/agile-training/product-thinking/groups/${g.id}/participants`, { headers: this._authHeaders() });
        this.participants = res.data.participants || [];
        const rr = await axios.get(`/api/agile-training/product-thinking/groups/${g.id}/results`, { headers: this._authHeaders() });
        if (rr.data) {
          g.participants_count = rr.data.participants_count;
          g.answers_count = rr.data.answers_count;
        }
      } catch (e) {
        this.modal.error = (e.response && e.response.data && e.response.data.error) || e.message || this.$t('agileTraining.productThinking.facilitator.loadError');
      } finally {
        this.modal.loading = false;
      }
    },
    closeModal() {
      this.modal = { open: false, loading: false, error: '', group: null };
      this.participants = [];
      this.pickedIds = new Set();
    },
  },
};
</script>

<style scoped>
.pt-fac { max-width: 1080px; margin: 24px auto 60px; padding: 0 20px; color: #0f172a; font-family: inherit; }
.pt-fac__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 24px; }
.pt-fac__head h1 { margin: 0; font-size: 26px; }
.pt-fac__sub { color: #64748b; margin: 6px 0 0; max-width: 720px; line-height: 1.5; }
.pt-fac__back { color: #7c3aed; text-decoration: none; font-weight: 600; }

.pt-fac__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px 22px; }
.pt-fac__create {
  display: grid; grid-template-columns: 1fr 140px auto; gap: 10px; margin-bottom: 16px;
}
.pt-fac__create input, .pt-fac__create select {
  padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 10px;
  font-family: inherit; font-size: 14px; color: #0f172a;
}
.pt-fac__create button {
  padding: 9px 18px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff;
  font-weight: 600; cursor: pointer;
}

.pt-fac__list, .pt-fac__groups, .pt-fac__participants { list-style: none; padding: 0; margin: 0; }
.pt-fac__row {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  padding: 12px 14px; border: 1px solid #e5e7eb; border-radius: 12px; margin-bottom: 8px;
}
.pt-fac__row-title { font-weight: 700; }
.pt-fac__row-meta {
  display: flex; gap: 6px; color: #64748b; font-size: 13px; margin-top: 2px; flex-wrap: wrap; align-items: center;
}
.pt-fac__badge {
  background: #ede9fe; color: #6d28d9; font-weight: 700; font-size: 11px;
  padding: 2px 8px; border-radius: 999px; letter-spacing: 0.3px;
}
.pt-fac__empty { color: #94a3b8; padding: 12px 0; }
.pt-fac__hint { color: #64748b; padding: 12px 0; }
.pt-fac__error { padding: 12px; background: #fee2e2; color: #b91c1c; border-radius: 10px; }

.btn-ghost {
  background: #fff; border: 1px solid #cbd5e1; color: #475569;
  padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px;
}
.btn-ghost:hover { border-color: #7c3aed; color: #7c3aed; }
.btn-danger {
  background: #fff; border: 1px solid #fecaca; color: #b91c1c;
  padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px;
}
.btn-danger:hover { background: #fef2f2; }

.pt-fac__active-head {
  display: flex; justify-content: space-between; gap: 12px; align-items: flex-start;
  margin-bottom: 14px;
}
.pt-fac__active-title { font-size: 20px; font-weight: 700; }
.pt-fac__active-actions { display: flex; gap: 8px; }

.pt-fac__groups-head {
  display: flex; justify-content: space-between; align-items: center; gap: 12px;
  margin: 18px 0 10px;
}
.pt-fac__groups-head h3 { margin: 0; font-size: 16px; }
.pt-fac__add-group { display: flex; gap: 8px; }
.pt-fac__add-group input { padding: 7px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-family: inherit; font-size: 13px; }
.pt-fac__add-group button {
  padding: 7px 14px; border: none; border-radius: 8px;
  background: #7c3aed; color: #fff; font-weight: 600; cursor: pointer; font-size: 13px;
}

.pt-fac__group {
  display: grid; grid-template-columns: 1fr auto; gap: 14px;
  padding: 14px 16px; border: 1px solid #e5e7eb; border-radius: 12px;
  margin-bottom: 10px;
}
.pt-fac__group-name { font-weight: 700; font-size: 15px; }
.pt-fac__link {
  display: flex; gap: 8px; align-items: center; margin-top: 6px; flex-wrap: wrap;
}
.pt-fac__link code {
  background: #f8fafc; padding: 4px 8px; border-radius: 6px; font-size: 12px;
  color: #475569; border: 1px solid #e2e8f0;
}
.pt-fac__copy, .pt-fac__open-link {
  font-size: 12px; color: #7c3aed; background: transparent;
  border: 1px solid #c4b5fd; padding: 3px 8px; border-radius: 6px; cursor: pointer;
  text-decoration: none;
}
.pt-fac__copy:hover, .pt-fac__open-link:hover { background: #faf5ff; }
.pt-fac__group-actions { display: flex; flex-direction: column; gap: 6px; }

.pt-modal {
  position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45);
  display: flex; align-items: center; justify-content: center; z-index: 100;
  padding: 20px;
}
.pt-modal__body {
  background: #fff; border-radius: 16px; padding: 20px 22px;
  max-width: 900px; width: 100%; max-height: 90vh; overflow-y: auto;
}
.pt-modal__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; margin-bottom: 14px; }
.pt-modal__head h3 { margin: 0; font-size: 18px; }
.pt-modal__sub { color: #64748b; font-size: 13px; margin: 4px 0 0; }
.pt-modal__close {
  background: transparent; border: none; font-size: 20px; color: #64748b; cursor: pointer;
}

.pt-examples {
  background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 14px;
  padding: 14px 16px; margin-bottom: 16px;
}
.pt-examples h4 { margin: 0 0 8px; color: #6d28d9; }
.pt-examples__grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px;
}
.pt-ex {
  background: #fff; border-radius: 10px; padding: 12px 14px;
}
.pt-ex__name { font-weight: 700; color: #312e81; margin-bottom: 6px; }
.pt-ex__section { margin-top: 6px; font-size: 13px; }
.pt-ex__h { font-weight: 600; color: #5b21b6; font-size: 12px; text-transform: uppercase; }
.pt-ex p, .pt-ex ol { margin: 4px 0 0; }
.pt-ex ol { padding-left: 20px; color: #1e293b; line-height: 1.5; }

.pt-discussion {
  background: #eff6ff; border-radius: 12px; padding: 12px 16px; margin-bottom: 16px;
}
.pt-discussion h4 { margin: 0 0 6px; color: #1e3a8a; }
.pt-discussion ul { margin: 0; padding-left: 20px; color: #1e293b; line-height: 1.7; }

.pt-part {
  border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px;
}
.pt-part__head {
  display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap;
}
.pt-part__name { font-weight: 700; color: #0f172a; }
.pt-part__meta { color: #64748b; font-size: 13px; margin-top: 2px; }
.pt-part__pick {
  background: transparent; border: 1px solid #c4b5fd; color: #7c3aed;
  padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600;
}
.pt-part__pick--active {
  background: #7c3aed; color: #fff; border-color: #7c3aed;
}
.pt-part__body {
  margin-top: 10px; display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
@media (max-width: 720px) { .pt-part__body { grid-template-columns: 1fr; } }
.pt-part__col {
  background: #f8fafc; border-radius: 10px; padding: 10px 12px;
}
.pt-part__h { font-weight: 700; color: #5b21b6; font-size: 13px; margin-bottom: 4px; }
.pt-part__col p, .pt-part__col ol { margin: 0; color: #1e293b; line-height: 1.55; font-size: 14px; }
.pt-part__col ol { padding-left: 20px; }
.pt-part__empty { color: #94a3b8; margin-top: 8px; }
.pt-muted { color: #94a3b8; }
</style>
