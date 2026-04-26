<template>
  <div class="po-fac">
    <header class="po-fac__head">
      <div>
        <h1>🛣️ {{ $t('agileTraining.poPath.facTitle') }}</h1>
        <p class="po-fac__sub">{{ $t('agileTraining.poPath.facSubtitle') }}</p>
      </div>
      <router-link to="/agile-training" class="po-fac__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
    </header>

    <section v-if="!activeSession" class="po-fac__section">
      <h2>{{ $t('agileTraining.facilitator.mySessions') }}</h2>
      <form class="po-fac__create" @submit.prevent="createSession">
        <input v-model="newSessionTitle" :placeholder="$t('agileTraining.poPath.newSessionTitle')" required maxlength="255" />
        <select v-model="newSessionLocale">
          <option value="ru">{{ $t('agileTraining.common.languageRu') }}</option>
          <option value="en">{{ $t('agileTraining.common.languageEn') }}</option>
        </select>
        <button type="submit">{{ $t('agileTraining.facilitator.createSession') }}</button>
      </form>
      <div v-if="loadingSessions" class="po-fac__hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="!sessions.length" class="po-fac__empty">{{ $t('agileTraining.facilitator.noSessions') }}</div>
      <ul v-else class="po-fac__list">
        <li v-for="s in sessions" :key="s.id" class="po-fac__row">
          <div>
            <div class="po-fac__row-title">{{ s.title }}</div>
            <div class="po-fac__row-meta">
              <span class="po-fac__badge">{{ (s.locale || 'ru').toUpperCase() }}</span>
              <span>{{ formatDate(s.created_at) }}</span>
              <span>·</span>
              <span>{{ $t('agileTraining.facilitator.groupsCount', { n: s.groups_count || 0 }, s.groups_count || 0) }}</span>
            </div>
          </div>
          <button class="btn-ghost" @click="openSession(s.id)">{{ $t('agileTraining.facilitator.open') }}</button>
        </li>
      </ul>
    </section>

    <section v-else class="po-fac__section">
      <div class="po-fac__active-head">
        <div>
          <div class="po-fac__active-title">{{ activeSession.title }}</div>
          <div class="po-fac__row-meta">
            <span class="po-fac__badge">{{ (activeSession.locale || 'ru').toUpperCase() }}</span>
            <span>{{ formatDate(activeSession.created_at) }}</span>
          </div>
        </div>
        <div class="po-fac__active-actions">
          <button class="btn-ghost" @click="closeSession">← {{ $t('agileTraining.facilitator.backToList') }}</button>
          <button class="btn-danger" @click="deleteSession">{{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </div>

      <div class="po-fac__groups-head">
        <h3>{{ $t('agileTraining.facilitator.groups') }}</h3>
        <form class="po-fac__add-group" @submit.prevent="addGroup">
          <input v-model="newGroupName" :placeholder="$t('agileTraining.facilitator.newGroupName')" required maxlength="120" />
          <button type="submit">{{ $t('agileTraining.facilitator.addGroup') }}</button>
        </form>
      </div>

      <div v-if="!groups.length" class="po-fac__empty">{{ $t('agileTraining.facilitator.noGroups') }}</div>
      <ul v-else class="po-fac__groups">
        <li v-for="g in groups" :key="g.id" class="po-fac__group">
          <div class="po-fac__group-main">
            <div class="po-fac__group-name">{{ g.name }}</div>
            <div class="po-fac__row-meta">
              <span>{{ $t('agileTraining.poPath.fac.participantsCount', { n: g.participants_count || 0 }, g.participants_count || 0) }}</span>
              <span v-if="g.needs_action_count" class="po-fac__pill po-fac__pill--warn">⏳ {{ $t('agileTraining.poPath.fac.needsAction', { n: g.needs_action_count }) }}</span>
              <span v-if="g.completed_count" class="po-fac__pill po-fac__pill--ok">✓ {{ $t('agileTraining.poPath.fac.completed', { n: g.completed_count }) }}</span>
            </div>
            <div class="po-fac__link">
              <code>{{ publicLink(g.slug) }}</code>
              <button class="po-fac__copy" @click="copyLink(g.slug)">
                {{ copiedSlug === g.slug ? $t('agileTraining.facilitator.copied') : $t('agileTraining.facilitator.copyLink') }}
              </button>
              <a class="po-fac__open-link" :href="publicLink(g.slug)" target="_blank" rel="noopener">
                {{ $t('agileTraining.poPath.fac.openGroup') }} ↗
              </a>
            </div>
          </div>
          <div class="po-fac__group-actions">
            <button class="btn-ghost" @click="openGroup(g)">{{ $t('agileTraining.poPath.fac.viewParticipants') }}</button>
            <button class="btn-ghost" @click="resetGroup(g)">{{ $t('agileTraining.poPath.fac.resetGroup') }}</button>
            <button class="btn-danger" @click="removeGroup(g)">{{ $t('agileTraining.facilitator.delete') }}</button>
          </div>
        </li>
      </ul>
    </section>

    <div v-if="modal.open" class="po-modal" @click.self="closeModal">
      <div class="po-modal__body">
        <div class="po-modal__head">
          <div>
            <h3>{{ modal.group?.name }}</h3>
            <p class="po-modal__sub">{{ $t('agileTraining.poPath.fac.modalSub') }}</p>
          </div>
          <button class="po-modal__close" @click="closeModal">✕</button>
        </div>

        <div v-if="modal.loading" class="po-fac__hint">{{ $t('common.loading') }}…</div>
        <div v-else-if="modal.error" class="po-fac__error">{{ modal.error }}</div>
        <div v-else class="po-modal__grid">
          <aside class="po-modal__list">
            <ul class="po-modal__people">
              <li
                v-for="p in participants"
                :key="p.id"
                class="po-modal__person"
                :class="{ 'po-modal__person--active': selectedParticipantId === p.id, 'po-modal__person--needs': p.needs_action }"
                @click="selectParticipant(p.id)"
              >
                <div class="po-modal__person-name">{{ p.display_name }}</div>
                <div class="po-modal__person-stages">
                  <span
                    v-for="st in stages"
                    :key="'s_' + p.id + '_' + st"
                    class="po-modal__chip"
                    :class="['po-modal__chip--' + (p.stage_statuses?.[st] || 'draft')]"
                    :title="stageLabel(st) + ' · ' + statusLabel(p.stage_statuses?.[st] || 'draft')"
                  >{{ statusEmoji(p.stage_statuses?.[st] || 'draft') }}</span>
                </div>
                <div class="po-modal__person-meta">
                  <span>{{ $t('agileTraining.poPath.fac.stageNow') }}: <b>{{ stageLabel(p.current_stage) }}</b></span>
                  <span v-if="p.needs_action" class="po-modal__needs">⏳ {{ $t('agileTraining.poPath.fac.awaitsReview') }}</span>
                </div>
              </li>
            </ul>
          </aside>

          <main class="po-modal__detail">
            <div v-if="!detail" class="po-fac__empty">{{ $t('agileTraining.poPath.fac.pickPerson') }}</div>
            <template v-else>
              <header class="po-modal__det-head">
                <div>
                  <h4>{{ detailParticipantLabel }}</h4>
                  <div class="po-modal__det-meta">
                    {{ $t('agileTraining.poPath.fac.joined') }}: {{ formatDate(detail.participant.joined_at) }} · AI {{ detail.answer?.ai_calls || 0 }}
                  </div>
                </div>
              </header>

              <nav class="po-modal__tabs">
                <button
                  v-for="st in stages"
                  :key="'tab_' + st"
                  class="po-modal__tab"
                  :class="{ 'po-modal__tab--active': activeStageTab === st }"
                  @click="activeStageTab = st"
                >
                  <span class="po-modal__tab-emoji">{{ statusEmoji(detailStageStatus(st)) }}</span>
                  {{ stageLabel(st) }}
                </button>
              </nav>

              <section v-if="activeStageData" class="po-modal__stage">
                <div class="po-modal__stage-head">
                  <span class="po-modal__status" :class="['po-modal__status--' + activeStageData.status]">
                    {{ statusEmoji(activeStageData.status) }} {{ statusLabel(activeStageData.status) }}
                  </span>
                  <span v-if="activeStageData.confidence != null" class="po-modal__confidence">
                    {{ $t('agileTraining.poPath.fac.confidence') }}: {{ activeStageData.confidence }}/5
                  </span>
                </div>

                <div class="po-modal__fields">
                  <div v-for="key in stageFieldKeys(activeStageTab)" :key="'f_' + key" class="po-modal__field">
                    <div class="po-modal__field-label">{{ fieldLabel(activeStageTab, key) }}</div>
                    <div class="po-modal__field-value" v-if="activeStageData.data?.[key]">{{ activeStageData.data[key] }}</div>
                    <div v-else class="po-modal__field-empty">—</div>
                  </div>

                  <div v-if="activeStageTab === 'fit' && (activeStageData.ai_questions || []).length" class="po-modal__field">
                    <div class="po-modal__field-label">{{ $t('agileTraining.poPath.fac.aiQuestions') }}</div>
                    <ol class="po-modal__qa">
                      <li v-for="q in activeStageData.ai_questions" :key="q.id">
                        <div class="po-modal__qa-q">❓ {{ q.q }}</div>
                        <div class="po-modal__qa-a" v-if="q.answer">↳ {{ q.answer }}</div>
                        <div v-else class="po-modal__qa-a po-modal__qa-a--empty">—</div>
                      </li>
                    </ol>
                  </div>
                </div>

                <div v-if="(activeStageData.comments || []).length" class="po-modal__history">
                  <div class="po-modal__field-label">{{ $t('agileTraining.poPath.fac.history') }}</div>
                  <ul>
                    <li v-for="(c, i) in activeStageData.comments" :key="'c_' + i" :class="['po-modal__c', 'po-modal__c--' + (c.verdict || c.kind || 'note')]">
                      <span class="po-modal__c-tag">{{ commentTag(c) }}</span>
                      <span class="po-modal__c-text">{{ c.text }}</span>
                      <span class="po-modal__c-time">{{ formatDate(c.ts) }}</span>
                    </li>
                  </ul>
                </div>

                <div class="po-modal__review">
                  <textarea
                    v-model="reviewText"
                    rows="3"
                    :placeholder="$t('agileTraining.poPath.fac.commentPlaceholder')"
                    maxlength="2000"
                  ></textarea>
                  <div class="po-modal__review-actions">
                    <button class="btn-ghost" :disabled="reviewing" @click="postComment">
                      {{ $t('agileTraining.poPath.fac.justComment') }}
                    </button>
                    <button class="btn-warn" :disabled="reviewing" @click="reviewAction('reject')">
                      ↩ {{ $t('agileTraining.poPath.fac.reject') }}
                    </button>
                    <button class="btn-ok" :disabled="reviewing || activeStageData.status === 'approved'" @click="reviewAction('approve')">
                      ✓ {{ $t('agileTraining.poPath.fac.approve') }}
                    </button>
                  </div>
                </div>
              </section>
            </template>
          </main>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgilePoPathFacilitator',
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
      stages: ['jtbd', 'value', 'fit', 'canvas'],
      modal: { open: false, loading: false, error: '', group: null },
      participants: [],
      selectedParticipantId: null,
      detail: null,
      activeStageTab: 'jtbd',
      reviewText: '',
      reviewing: false,
    };
  },
  computed: {
    detailParticipantLabel() {
      if (!this.detail) return '';
      return this.detail.participant.display_name || ('#' + this.detail.participant.id);
    },
    activeStageData() {
      if (!this.detail || !this.detail.answer) return null;
      return this.detail.answer.stages[this.activeStageTab] || null;
    },
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    _authHeaders() {
      const t = localStorage.getItem('token') || localStorage.getItem('authToken');
      return t ? { Authorization: 'Bearer ' + t } : {};
    },
    formatDate(iso) {
      if (!iso) return '';
      try {
        const d = new Date(iso);
        return d.toLocaleString(this.$i18n.locale === 'en' ? 'en-GB' : 'ru-RU');
      } catch (_) { return iso; }
    },
    publicLink(slug) { return `${window.location.origin}/g/${slug}`; },
    stageLabel(st) {
      const map = {
        jtbd: this.$t('agileTraining.poPath.stages.jtbd.short'),
        value: this.$t('agileTraining.poPath.stages.value.short'),
        fit: this.$t('agileTraining.poPath.stages.fit.short'),
        canvas: this.$t('agileTraining.poPath.stages.canvas.short'),
        done: this.$t('agileTraining.poPath.summary.short'),
      };
      return map[st] || st;
    },
    statusLabel(s) { return this.$t('agileTraining.poPath.status.' + s) || s; },
    statusEmoji(s) {
      switch (s) {
        case 'draft': return '🟡';
        case 'submitted':
        case 'in_review': return '🔵';
        case 'needs_revision': return '🔴';
        case 'approved': return '🟢';
        default: return '⚪';
      }
    },
    fieldLabel(stage, key) { return this.$t('agileTraining.poPath.fields.' + stage + '.' + key + '.label') || key; },
    stageFieldKeys(stage) {
      const map = {
        jtbd: ['job_statement', 'context', 'motivation', 'barriers', 'fears'],
        value: ['pains', 'gains', 'product', 'pain_relievers'],
        fit: ['customer', 'why_choose', 'alternatives', 'usage_context'],
        canvas: ['problem', 'segments', 'early_adopters', 'value_prop', 'solution', 'channels', 'revenue', 'costs', 'metrics', 'unfair_advantage'],
      };
      return map[stage] || [];
    },
    commentTag(c) {
      if (!c) return '';
      if (c.verdict === 'approved') return '✓ ' + this.$t('agileTraining.poPath.fac.tagApproved');
      if (c.verdict === 'needs_revision') return '↩ ' + this.$t('agileTraining.poPath.fac.tagRejected');
      return '💬 ' + this.$t('agileTraining.poPath.fac.tagNote');
    },
    detailStageStatus(st) {
      if (!this.detail || !this.detail.answer) return 'draft';
      return (this.detail.answer.stages[st] || {}).status || 'draft';
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this._authHeaders() });
        this.sessions = (res.data.sessions || []).filter(s => s.exercise_key === 'po_path');
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
          title, locale: this.newSessionLocale || 'ru', exercise_key: 'po_path',
        }, { headers: this._authHeaders() });
        this.sessions.unshift({
          id: res.data.id, title: res.data.title, locale: res.data.locale,
          exercise_key: res.data.exercise_key, groups_count: 0, created_at: res.data.created_at,
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
          id: g.id, name: g.name, slug: g.slug,
          participants_count: g.participants, answers_count: g.answers,
          needs_action_count: 0, completed_count: 0,
        }));
        for (const g of this.groups) this.refreshGroupTotals(g);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    closeSession() { this.activeSession = null; this.groups = []; },
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
          id: res.data.id, name: res.data.name, slug: res.data.slug,
          participants_count: 0, answers_count: 0, needs_action_count: 0, completed_count: 0,
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
      if (!window.confirm(this.$t('agileTraining.poPath.fac.resetConfirm'))) return;
      try {
        await axios.post(`/api/agile-training/po-path/groups/${g.id}/reset`, {}, { headers: this._authHeaders() });
        await this.refreshGroupTotals(g);
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      }
    },
    async refreshGroupTotals(g) {
      try {
        const res = await axios.get(`/api/agile-training/po-path/groups/${g.id}/results`, { headers: this._authHeaders() });
        g.participants_count = res.data.participants_count;
        g.answers_count = res.data.answers_count;
        g.needs_action_count = res.data.needs_action_count;
        g.completed_count = res.data.completed_count;
      } catch (_) { /* ignore */ }
    },
    copyLink(slug) {
      const url = this.publicLink(slug);
      try {
        navigator.clipboard.writeText(url);
        this.copiedSlug = slug;
        setTimeout(() => { if (this.copiedSlug === slug) this.copiedSlug = ''; }, 1500);
      } catch (_) { /* noop */ }
    },
    async openGroup(g) {
      this.modal = { open: true, loading: true, error: '', group: g };
      this.participants = [];
      this.detail = null;
      this.selectedParticipantId = null;
      this.activeStageTab = 'jtbd';
      try {
        const res = await axios.get(`/api/agile-training/po-path/groups/${g.id}/participants`, { headers: this._authHeaders() });
        this.participants = res.data.participants || [];
        const first = this.participants.find(p => p.has_answer) || this.participants[0];
        if (first) await this.selectParticipant(first.id);
      } catch (e) {
        this.modal.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.modal.loading = false;
      }
    },
    closeModal() {
      this.modal = { open: false, loading: false, error: '', group: null };
      this.participants = [];
      this.detail = null;
      this.selectedParticipantId = null;
    },
    async selectParticipant(pid) {
      const g = this.modal.group;
      if (!g) return;
      this.selectedParticipantId = pid;
      this.detail = null;
      try {
        const res = await axios.get(`/api/agile-training/po-path/groups/${g.id}/participants/${pid}`, { headers: this._authHeaders() });
        this.detail = res.data;
        if (this.detail.answer && this.detail.answer.current_stage && this.detail.answer.current_stage !== 'done') {
          this.activeStageTab = this.detail.answer.current_stage;
        }
      } catch (e) {
        this.modal.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      }
    },
    async refreshDetailAndList() {
      const g = this.modal.group;
      if (!g) return;
      try {
        const list = await axios.get(`/api/agile-training/po-path/groups/${g.id}/participants`, { headers: this._authHeaders() });
        this.participants = list.data.participants || [];
        if (this.selectedParticipantId) {
          await this.selectParticipant(this.selectedParticipantId);
        }
        this.refreshGroupTotals(g);
      } catch (_) { /* ignore */ }
    },
    async reviewAction(action) {
      if (!this.detail) return;
      const stage = this.activeStageTab;
      this.reviewing = true;
      try {
        await axios.post(
          `/api/agile-training/po-path/groups/${this.modal.group.id}/participants/${this.detail.participant.id}/review`,
          { stage, action, comment: this.reviewText },
          { headers: this._authHeaders() },
        );
        this.reviewText = '';
        await this.refreshDetailAndList();
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      } finally {
        this.reviewing = false;
      }
    },
    async postComment() {
      if (!this.detail) return;
      const text = (this.reviewText || '').trim();
      if (!text) return;
      this.reviewing = true;
      try {
        await axios.post(
          `/api/agile-training/po-path/groups/${this.modal.group.id}/participants/${this.detail.participant.id}/comment`,
          { stage: this.activeStageTab, text },
          { headers: this._authHeaders() },
        );
        this.reviewText = '';
        await this.refreshDetailAndList();
      } catch (e) {
        alert((e.response && e.response.data && e.response.data.error) || e.message);
      } finally {
        this.reviewing = false;
      }
    },
  },
};
</script>

<style scoped>
.po-fac { max-width: 1200px; margin: 24px auto 60px; padding: 0 20px; color: #0f172a; font-family: inherit; }
.po-fac__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 24px; }
.po-fac__head h1 { margin: 0; font-size: 26px; }
.po-fac__sub { color: #64748b; margin: 6px 0 0; max-width: 720px; line-height: 1.5; }
.po-fac__back { color: #7c3aed; text-decoration: none; font-weight: 600; }

.po-fac__section { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px 22px; }
.po-fac__create { display: grid; grid-template-columns: 1fr 140px auto; gap: 10px; margin-bottom: 16px; }
.po-fac__create input, .po-fac__create select { padding: 9px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px; }
.po-fac__create button { padding: 9px 18px; border: none; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; font-weight: 600; cursor: pointer; }

.po-fac__list, .po-fac__groups { list-style: none; padding: 0; margin: 0; }
.po-fac__row { display: flex; justify-content: space-between; align-items: center; gap: 12px; padding: 12px 14px; border: 1px solid #e5e7eb; border-radius: 12px; margin-bottom: 8px; }
.po-fac__row-title { font-weight: 700; }
.po-fac__row-meta { display: flex; gap: 6px; color: #64748b; font-size: 13px; margin-top: 2px; flex-wrap: wrap; align-items: center; }
.po-fac__badge { background: #ede9fe; color: #6d28d9; font-weight: 700; font-size: 11px; padding: 2px 8px; border-radius: 999px; }
.po-fac__pill { font-size: 12px; padding: 2px 8px; border-radius: 999px; font-weight: 600; }
.po-fac__pill--warn { background: #fef3c7; color: #b45309; }
.po-fac__pill--ok { background: #dcfce7; color: #166534; }

.po-fac__empty { color: #94a3b8; padding: 12px 0; }
.po-fac__hint { color: #64748b; padding: 12px 0; }
.po-fac__error { padding: 12px; background: #fee2e2; color: #b91c1c; border-radius: 10px; }

.btn-ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-ghost:hover { border-color: #7c3aed; color: #7c3aed; }
.btn-danger { background: #fff; border: 1px solid #fecaca; color: #b91c1c; padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-warn { background: #fff7ed; border: 1px solid #fdba74; color: #c2410c; padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-ok { background: linear-gradient(135deg, #34d399, #059669); border: none; color: #fff; padding: 7px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; }
.btn-ok:disabled, .btn-warn:disabled, .btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

.po-fac__active-head { display: flex; justify-content: space-between; gap: 12px; align-items: flex-start; margin-bottom: 14px; }
.po-fac__active-title { font-size: 20px; font-weight: 700; }
.po-fac__active-actions { display: flex; gap: 8px; }
.po-fac__groups-head { display: flex; justify-content: space-between; align-items: center; gap: 12px; margin: 18px 0 10px; }
.po-fac__add-group { display: flex; gap: 8px; }
.po-fac__add-group input { padding: 7px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px; }
.po-fac__add-group button { padding: 7px 16px; border: none; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; font-weight: 600; cursor: pointer; }

.po-fac__group { padding: 14px 16px; border: 1px solid #e5e7eb; border-radius: 14px; margin-bottom: 10px; display: flex; gap: 12px; justify-content: space-between; align-items: flex-start; }
.po-fac__group-name { font-weight: 700; }
.po-fac__link { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; margin-top: 8px; }
.po-fac__link code { background: #f1f5f9; padding: 4px 10px; border-radius: 8px; font-size: 12px; color: #475569; }
.po-fac__copy { background: transparent; border: 1px dashed #cbd5e1; color: #475569; padding: 4px 10px; border-radius: 8px; font-size: 12px; cursor: pointer; }
.po-fac__copy:hover { border-color: #7c3aed; color: #7c3aed; }
.po-fac__open-link { color: #7c3aed; font-weight: 600; font-size: 13px; text-decoration: none; }
.po-fac__group-actions { display: flex; gap: 6px; flex-wrap: wrap; }

.po-modal { position: fixed; inset: 0; background: rgba(15,23,42,.55); display: flex; align-items: center; justify-content: center; z-index: 50; padding: 20px; }
.po-modal__body { background: #fff; border-radius: 16px; width: min(1100px, 100%); max-height: 92vh; overflow: hidden; display: flex; flex-direction: column; }
.po-modal__head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 16px 20px; border-bottom: 1px solid #e5e7eb; }
.po-modal__head h3 { margin: 0; }
.po-modal__sub { color: #64748b; margin: 4px 0 0; font-size: 13px; }
.po-modal__close { background: transparent; border: none; font-size: 18px; cursor: pointer; color: #64748b; }
.po-modal__grid { display: grid; grid-template-columns: 320px 1fr; min-height: 60vh; max-height: calc(92vh - 80px); }
.po-modal__list { border-right: 1px solid #e5e7eb; overflow: auto; padding: 8px; }
.po-modal__detail { padding: 18px 22px; overflow: auto; }

.po-modal__people { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.po-modal__person { padding: 10px 12px; border-radius: 10px; cursor: pointer; border: 1px solid transparent; }
.po-modal__person:hover { background: #f8fafc; }
.po-modal__person--active { background: #ede9fe; border-color: #c4b5fd; }
.po-modal__person--needs::before { content: '⏳ '; }
.po-modal__person-name { font-weight: 600; font-size: 14px; }
.po-modal__person-stages { display: flex; gap: 4px; margin-top: 4px; }
.po-modal__chip { font-size: 14px; }
.po-modal__person-meta { color: #64748b; font-size: 12px; margin-top: 4px; display: flex; flex-direction: column; }
.po-modal__needs { color: #b45309; }

.po-modal__det-head { display: flex; justify-content: space-between; align-items: flex-start; }
.po-modal__det-head h4 { margin: 0; font-size: 18px; }
.po-modal__det-meta { color: #64748b; font-size: 12px; margin-top: 4px; }
.po-modal__tabs { display: flex; gap: 4px; margin: 14px 0; flex-wrap: wrap; }
.po-modal__tab { background: #f8fafc; border: 1px solid #e5e7eb; padding: 7px 12px; border-radius: 999px; cursor: pointer; font-size: 13px; font-weight: 600; color: #475569; }
.po-modal__tab--active { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; border-color: transparent; }
.po-modal__tab-emoji { margin-right: 4px; }

.po-modal__stage-head { display: flex; gap: 10px; align-items: center; margin-bottom: 8px; }
.po-modal__status { font-weight: 700; font-size: 13px; padding: 3px 10px; border-radius: 999px; background: #f1f5f9; color: #334155; }
.po-modal__status--approved { background: #dcfce7; color: #166534; }
.po-modal__status--needs_revision { background: #fee2e2; color: #b91c1c; }
.po-modal__status--submitted, .po-modal__status--in_review { background: #dbeafe; color: #1d4ed8; }
.po-modal__confidence { font-size: 12px; color: #64748b; }

.po-modal__fields { display: grid; gap: 10px; }
.po-modal__field { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 12px; }
.po-modal__field-label { font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
.po-modal__field-value { white-space: pre-wrap; line-height: 1.5; }
.po-modal__field-empty { color: #94a3b8; }

.po-modal__qa { padding-left: 18px; margin: 0; }
.po-modal__qa-q { font-weight: 600; }
.po-modal__qa-a { color: #475569; margin-top: 2px; }
.po-modal__qa-a--empty { color: #94a3b8; }

.po-modal__history { margin-top: 14px; }
.po-modal__history ul { list-style: none; padding: 0; margin: 6px 0 0; display: flex; flex-direction: column; gap: 6px; }
.po-modal__c { background: #f8fafc; border-left: 3px solid #cbd5e1; padding: 8px 10px; border-radius: 6px; display: grid; grid-template-columns: auto 1fr auto; gap: 8px; align-items: baseline; font-size: 13px; }
.po-modal__c--approved { border-left-color: #16a34a; }
.po-modal__c--needs_revision { border-left-color: #dc2626; }
.po-modal__c-tag { font-weight: 600; color: #334155; font-size: 12px; }
.po-modal__c-time { color: #94a3b8; font-size: 11px; }

.po-modal__review { margin-top: 18px; }
.po-modal__review textarea { width: 100%; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 14px; resize: vertical; }
.po-modal__review-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 8px; flex-wrap: wrap; }

@media (max-width: 800px) {
  .po-modal__grid { grid-template-columns: 1fr; max-height: none; }
  .po-modal__list { max-height: 200px; border-right: none; border-bottom: 1px solid #e5e7eb; }
}
</style>
