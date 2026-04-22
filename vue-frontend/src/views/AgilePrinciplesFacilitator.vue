<template>
  <div class="atf-page">
    <header class="atf-head">
      <button class="atf-back" @click="$router.push('/agile-training')">← {{ $t('agileTraining.common.back') }}</button>
      <h1>🃏 {{ $t('agileTraining.facilitator.title') }}</h1>
      <p class="atf-lead">{{ $t('agileTraining.facilitator.lead') }}</p>
    </header>

    <!-- Список сессий + создание -->
    <section v-if="!activeSessionId" class="atf-sessions">
      <div class="atf-sessions__head">
        <h2>{{ $t('agileTraining.facilitator.sessions') }}</h2>
        <form class="atf-new" @submit.prevent="createSession">
          <input
            v-model="newSessionTitle"
            type="text"
            :placeholder="$t('agileTraining.facilitator.newSessionPlaceholder')"
            maxlength="120"
          />
          <button type="submit" class="atf-btn atf-btn--primary" :disabled="creatingSession">
            {{ creatingSession ? $t('agileTraining.common.loading') : $t('agileTraining.facilitator.createSession') }}
          </button>
        </form>
      </div>

      <p v-if="!sessions.length && !loadingSessions" class="atf-empty">
        {{ $t('agileTraining.facilitator.noSessions') }}
      </p>

      <div class="atf-sessions__grid">
        <article
          v-for="s in sessions"
          :key="s.id"
          class="atf-session-card"
          @click="openSession(s.id)"
        >
          <h3>{{ s.title }}</h3>
          <div class="atf-session-card__meta">
            <span>{{ formatDate(s.created_at) }}</span>
            <span class="atf-badge">{{ $tc('agileTraining.facilitator.groupsCount', s.groups_count) }}</span>
          </div>
          <span class="atf-session-card__cta">{{ $t('agileTraining.facilitator.open') }} →</span>
        </article>
      </div>
    </section>

    <!-- Детали сессии -->
    <section v-else class="atf-session">
      <button class="atf-back" @click="closeSession">← {{ $t('agileTraining.facilitator.backToSessions') }}</button>

      <header class="atf-session__head">
        <h2>{{ currentSession?.title }}</h2>
        <div class="atf-session__actions">
          <button class="atf-btn atf-btn--ghost" @click="refreshSession">⟲ {{ $t('agileTraining.facilitator.refresh') }}</button>
          <button class="atf-btn atf-btn--danger" @click="deleteSession">🗑 {{ $t('agileTraining.facilitator.deleteSession') }}</button>
        </div>
      </header>

      <!-- Добавление группы -->
      <div class="atf-new-group">
        <form @submit.prevent="addGroup">
          <input
            v-model="newGroupName"
            type="text"
            :placeholder="$t('agileTraining.facilitator.groupPlaceholder')"
            maxlength="120"
          />
          <button type="submit" class="atf-btn atf-btn--primary" :disabled="creatingGroup">
            {{ creatingGroup ? $t('agileTraining.common.loading') : $t('agileTraining.facilitator.addGroup') }}
          </button>
        </form>
      </div>

      <!-- Группы -->
      <div v-if="currentSession?.groups?.length" class="atf-groups">
        <article v-for="g in currentSession.groups" :key="g.id" class="atf-group">
          <header class="atf-group__head">
            <div>
              <h4>{{ g.name }}</h4>
              <span class="atf-group__status" :class="'atf-group__status--' + g.status">
                {{ $t('agileTraining.facilitator.status.' + g.status) }}
              </span>
            </div>
            <div class="atf-group__stats">
              <span>👥 {{ g.participants }}</span>
              <span>🗳 {{ g.answers }}</span>
              <span>🧭 {{ g.principles_seen }}/{{ principlesTotal }}</span>
            </div>
          </header>

          <div class="atf-group__link">
            <code>{{ publicLink(g.slug) }}</code>
            <button class="atf-btn atf-btn--small" @click="copyLink(g.slug)">
              {{ copiedSlug === g.slug ? $t('agileTraining.common.copied') : $t('agileTraining.common.copy') }}
            </button>
          </div>

          <div class="atf-group__actions">
            <button class="atf-btn atf-btn--ghost atf-btn--small" @click="openGroupResults(g)">
              📊 {{ $t('agileTraining.facilitator.viewResults') }}
            </button>
            <button class="atf-btn atf-btn--ghost atf-btn--small" @click="resetGroup(g)">
              ♻ {{ $t('agileTraining.facilitator.resetGroup') }}
            </button>
            <button class="atf-btn atf-btn--danger atf-btn--small" @click="removeGroup(g)">
              🗑 {{ $t('agileTraining.facilitator.deleteGroup') }}
            </button>
          </div>
        </article>
      </div>

      <p v-else class="atf-empty">{{ $t('agileTraining.facilitator.noGroups') }}</p>

      <!-- Модалка результатов -->
      <div v-if="resultsModal.open" class="atf-modal-overlay" @click.self="closeResults">
        <div class="atf-modal" role="dialog" aria-modal="true">
          <header class="atf-modal__head">
            <h3>📊 {{ resultsModal.group?.name }} · {{ $t('agileTraining.facilitator.results') }}</h3>
            <button class="atf-modal__close" @click="closeResults">×</button>
          </header>
          <div class="atf-modal__body" v-if="resultsModal.data">
            <p class="atf-muted">
              {{ $t('agileTraining.facilitator.participantsTotal', { n: resultsModal.data.participants_count }) }}
            </p>

            <h4>🔥 {{ $t('agileTraining.facilitator.topControversial') }}</h4>
            <ul class="atf-top-list">
              <li v-for="row in resultsModal.data.top_controversial" :key="'c-'+row.key">
                <div class="atf-top-list__name">{{ row.short }}</div>
                <div class="atf-top-list__bar">
                  <div class="atf-top-list__fill" :style="{ width: row.relevant_pct + '%' }"></div>
                </div>
                <div class="atf-top-list__pct">{{ row.relevant_pct }}% {{ $t('agileTraining.common.relevant') }}</div>
              </li>
              <li v-if="!resultsModal.data.top_controversial.length" class="atf-muted">
                {{ $t('agileTraining.common.notEnoughData') }}
              </li>
            </ul>

            <h4>🎯 {{ $t('agileTraining.facilitator.topObvious') }}</h4>
            <ul class="atf-top-list">
              <li v-for="row in resultsModal.data.top_obvious" :key="'o-'+row.key">
                <div class="atf-top-list__name">{{ row.short }}</div>
                <div class="atf-top-list__bar">
                  <div class="atf-top-list__fill" :style="{ width: row.relevant_pct + '%' }"></div>
                </div>
                <div class="atf-top-list__pct">{{ row.relevant_pct }}% {{ $t('agileTraining.common.relevant') }}</div>
              </li>
              <li v-if="!resultsModal.data.top_obvious.length" class="atf-muted">
                {{ $t('agileTraining.common.notEnoughData') }}
              </li>
            </ul>

            <h4>🆚 {{ $t('agileTraining.facilitator.compare') }}</h4>
            <p v-if="!resultsModal.data.compare.has_others" class="atf-muted">
              {{ $t('agileTraining.facilitator.compareSolo') }}
            </p>
            <ul v-else class="atf-compare-list">
              <li v-for="row in resultsModal.data.compare.differences_top" :key="'d-'+row.key">
                <div class="atf-compare-list__name">{{ row.short }}</div>
                <div class="atf-compare-list__values">
                  <span>{{ $t('agileTraining.facilitator.thisGroup') }}: <strong>{{ row.this_group_pct }}%</strong></span>
                  <span>{{ $t('agileTraining.facilitator.otherGroups') }}: <strong>{{ row.other_groups_pct }}%</strong></span>
                  <span :class="row.diff >= 0 ? 'atf-diff atf-diff--up' : 'atf-diff atf-diff--down'">
                    {{ row.diff >= 0 ? '+' : '' }}{{ row.diff }} {{ $t('agileTraining.common.pp') }}
                  </span>
                </div>
              </li>
              <li v-if="!resultsModal.data.compare.differences_top.length" class="atf-muted">
                {{ $t('agileTraining.facilitator.compareNoDiff') }}
              </li>
            </ul>

            <details class="atf-raw">
              <summary>{{ $t('agileTraining.facilitator.allPrinciples') }}</summary>
              <ul class="atf-raw__list">
                <li v-for="row in resultsModal.data.per_principle" :key="'a-'+row.key">
                  <div class="atf-raw__name">{{ row.short }}</div>
                  <div class="atf-raw__bar"><div :style="{ width: row.relevant_pct + '%' }"></div></div>
                  <div class="atf-raw__meta">{{ row.relevant_pct }}% · {{ row.total }} {{ $t('agileTraining.common.votes') }}</div>
                </li>
              </ul>
            </details>
          </div>
          <div class="atf-modal__body" v-else>
            <p class="atf-muted">{{ $t('agileTraining.common.loading') }}…</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'AgilePrinciplesFacilitator',
  data() {
    return {
      sessions: [],
      loadingSessions: false,
      creatingSession: false,
      newSessionTitle: '',
      activeSessionId: null,
      currentSession: null,
      newGroupName: '',
      creatingGroup: false,
      copiedSlug: '',
      principlesTotal: 12,
      resultsModal: { open: false, group: null, data: null }
    };
  },
  async mounted() {
    await this.loadSessions();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    publicLink(slug) {
      return `${window.location.origin}/g/${slug}`;
    },
    async loadSessions() {
      this.loadingSessions = true;
      try {
        const res = await axios.get('/api/agile-training/sessions', { headers: this.authHeaders() });
        this.sessions = res.data.sessions || [];
      } catch (e) {
        console.error('load sessions error', e);
      } finally {
        this.loadingSessions = false;
      }
    },
    async createSession() {
      const title = this.newSessionTitle.trim();
      if (!title) return;
      this.creatingSession = true;
      try {
        const res = await axios.post('/api/agile-training/sessions',
          { title },
          { headers: this.authHeaders() });
        this.newSessionTitle = '';
        await this.loadSessions();
        this.openSession(res.data.id);
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to create session');
      } finally {
        this.creatingSession = false;
      }
    },
    async openSession(id) {
      this.activeSessionId = id;
      await this.refreshSession();
    },
    async refreshSession() {
      if (!this.activeSessionId) return;
      try {
        const res = await axios.get(`/api/agile-training/sessions/${this.activeSessionId}`,
          { headers: this.authHeaders() });
        this.currentSession = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load session');
        this.closeSession();
      }
    },
    closeSession() {
      this.activeSessionId = null;
      this.currentSession = null;
    },
    async deleteSession() {
      if (!confirm(this.$t('agileTraining.facilitator.confirmDeleteSession'))) return;
      try {
        await axios.delete(`/api/agile-training/sessions/${this.activeSessionId}`,
          { headers: this.authHeaders() });
        this.closeSession();
        await this.loadSessions();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to delete');
      }
    },
    async addGroup() {
      const name = this.newGroupName.trim();
      if (!name) return;
      this.creatingGroup = true;
      try {
        await axios.post(`/api/agile-training/sessions/${this.activeSessionId}/groups`,
          { name },
          { headers: this.authHeaders() });
        this.newGroupName = '';
        await this.refreshSession();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to add group');
      } finally {
        this.creatingGroup = false;
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
      if (!confirm(this.$t('agileTraining.facilitator.confirmResetGroup', { name: g.name }))) return;
      try {
        await axios.post(`/api/agile-training/groups/${g.id}/reset`, {}, { headers: this.authHeaders() });
        await this.refreshSession();
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to reset');
      }
    },
    async copyLink(slug) {
      const url = this.publicLink(slug);
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(url);
        } else {
          const ta = document.createElement('textarea');
          ta.value = url;
          ta.style.position = 'fixed';
          ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        this.copiedSlug = slug;
        setTimeout(() => { if (this.copiedSlug === slug) this.copiedSlug = ''; }, 1600);
      } catch (e) {
        alert('Failed to copy link');
      }
    },
    async openGroupResults(g) {
      this.resultsModal = { open: true, group: g, data: null };
      document.body.style.overflow = 'hidden';
      try {
        const res = await axios.get(`/api/agile-training/g/${g.slug}/results`);
        this.resultsModal.data = res.data;
      } catch (e) {
        this.resultsModal.data = null;
        alert(e.response?.data?.error || 'Failed to load results');
      }
    },
    closeResults() {
      this.resultsModal = { open: false, group: null, data: null };
      document.body.style.overflow = '';
    },
    formatDate(iso) {
      if (!iso) return '';
      return new Date(iso).toLocaleDateString(this.$i18n?.locale === 'en' ? 'en-US' : 'ru-RU', {
        year: 'numeric', month: 'short', day: 'numeric'
      });
    }
  }
};
</script>

<style scoped>
.atf-page {
  max-width: 1080px;
  margin: 28px auto;
  padding: 0 20px 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
  color: #0f172a;
}
.atf-back {
  background: transparent;
  border: none;
  color: #7c3aed;
  font-weight: 600;
  cursor: pointer;
  padding: 6px 0;
  font-size: 14px;
}
.atf-head h1 { margin: 12px 0 6px; font-size: 28px; letter-spacing: -0.3px; }
.atf-lead { color: #475569; max-width: 720px; line-height: 1.6; margin: 0 0 20px; }

.atf-sessions__head { display: flex; justify-content: space-between; align-items: center; gap: 16px; flex-wrap: wrap; margin-bottom: 20px; }
.atf-sessions__head h2 { margin: 0; font-size: 22px; }

.atf-new { display: flex; gap: 8px; flex-wrap: wrap; }
.atf-new input, .atf-new-group input {
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  min-width: 260px;
  font-size: 14px;
  font-family: inherit;
}
.atf-new input:focus, .atf-new-group input:focus { outline: none; border-color: #8b5cf6; box-shadow: 0 0 0 3px rgba(139,92,246,0.15); }

.atf-empty { color: #64748b; margin: 24px 0; }

.atf-sessions__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}
.atf-session-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.atf-session-card:hover { border-color: #8b5cf6; box-shadow: 0 8px 20px rgba(139,92,246,0.12); transform: translateY(-1px); }
.atf-session-card h3 { margin: 0; font-size: 17px; }
.atf-session-card__meta { display: flex; justify-content: space-between; color: #64748b; font-size: 13px; }
.atf-session-card__cta { color: #7c3aed; font-weight: 600; font-size: 13px; }
.atf-badge { background: #eef2ff; color: #4338ca; padding: 3px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }

.atf-session__head {
  display: flex; justify-content: space-between; align-items: center;
  margin: 16px 0 20px; gap: 12px; flex-wrap: wrap;
}
.atf-session__head h2 { margin: 0; font-size: 24px; }
.atf-session__actions { display: flex; gap: 8px; flex-wrap: wrap; }

.atf-new-group { margin: 20px 0 24px; }
.atf-new-group form { display: flex; gap: 8px; flex-wrap: wrap; }

.atf-groups { display: grid; gap: 14px; }
.atf-group {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 18px 20px;
  display: grid;
  gap: 12px;
}
.atf-group__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
.atf-group__head h4 { margin: 0; font-size: 17px; }
.atf-group__status {
  display: inline-block;
  margin-top: 4px;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}
.atf-group__status--not_started { background: #f1f5f9; color: #64748b; }
.atf-group__status--in_progress { background: #fef3c7; color: #92400e; }
.atf-group__status--completed { background: #dcfce7; color: #166534; }

.atf-group__stats { display: flex; gap: 12px; color: #475569; font-size: 14px; font-weight: 600; }

.atf-group__link {
  display: flex; gap: 10px; align-items: center; flex-wrap: wrap;
  background: #f8fafc; padding: 10px 12px; border-radius: 10px;
}
.atf-group__link code {
  flex: 1 1 220px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: #1e293b;
  word-break: break-all;
}

.atf-group__actions { display: flex; gap: 8px; flex-wrap: wrap; }

/* buttons */
.atf-btn {
  padding: 9px 16px;
  font-size: 14px;
  font-weight: 600;
  border-radius: 10px;
  border: 1px solid transparent;
  background: #fff;
  cursor: pointer;
  font-family: inherit;
  color: #1f2937;
  transition: all 0.15s ease;
}
.atf-btn--small { padding: 6px 12px; font-size: 13px; border-radius: 8px; }
.atf-btn--ghost { background: transparent; border-color: #cbd5e1; color: #334155; }
.atf-btn--ghost:hover { border-color: #94a3b8; background: #f1f5f9; }
.atf-btn--primary {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
  box-shadow: 0 4px 10px rgba(139, 92, 246, 0.3);
}
.atf-btn--primary:hover { box-shadow: 0 6px 14px rgba(139, 92, 246, 0.4); }
.atf-btn--primary:disabled { opacity: 0.6; cursor: not-allowed; }
.atf-btn--danger {
  background: #fff;
  color: #b91c1c;
  border-color: #fecaca;
}
.atf-btn--danger:hover { background: #fef2f2; border-color: #fca5a5; }

/* modal */
.atf-modal-overlay {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 20px;
}
.atf-modal {
  background: #fff;
  border-radius: 18px;
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow: hidden;
  display: flex; flex-direction: column;
  box-shadow: 0 30px 60px rgba(15, 23, 42, 0.25);
}
.atf-modal__head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e5e7eb;
}
.atf-modal__head h3 { margin: 0; font-size: 18px; }
.atf-modal__close {
  background: #f1f5f9; color: #334155;
  border: none; border-radius: 10px;
  width: 32px; height: 32px; cursor: pointer;
  font-size: 20px; line-height: 1;
}
.atf-modal__body { padding: 20px; overflow-y: auto; }
.atf-modal__body h4 { margin: 18px 0 10px; font-size: 15px; color: #334155; }
.atf-muted { color: #64748b; font-size: 13px; }

.atf-top-list, .atf-compare-list { list-style: none; padding: 0; margin: 0; display: grid; gap: 8px; }
.atf-top-list li {
  display: grid; grid-template-columns: 1fr 2fr auto; gap: 10px; align-items: center;
  background: #f8fafc; border-radius: 10px; padding: 10px 12px; font-size: 13px;
}
.atf-top-list__name { font-weight: 600; color: #0f172a; }
.atf-top-list__bar { height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.atf-top-list__fill { height: 100%; background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); }
.atf-top-list__pct { color: #334155; font-weight: 600; text-align: right; }

.atf-compare-list li {
  background: #f8fafc; border-radius: 10px; padding: 10px 12px; font-size: 13px;
}
.atf-compare-list__name { font-weight: 600; color: #0f172a; margin-bottom: 6px; }
.atf-compare-list__values { display: flex; gap: 14px; flex-wrap: wrap; color: #475569; }
.atf-diff { font-weight: 700; }
.atf-diff--up { color: #16a34a; }
.atf-diff--down { color: #b91c1c; }

.atf-raw { margin-top: 18px; }
.atf-raw summary { cursor: pointer; color: #7c3aed; font-weight: 600; }
.atf-raw__list { list-style: none; padding: 0; margin: 12px 0 0; display: grid; gap: 6px; }
.atf-raw__list li { display: grid; grid-template-columns: 1fr 2fr auto; gap: 10px; align-items: center; font-size: 12px; color: #475569; }
.atf-raw__bar { height: 6px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.atf-raw__bar div { height: 100%; background: #8b5cf6; }
.atf-raw__name { color: #0f172a; }
.atf-raw__meta { text-align: right; font-weight: 600; }
</style>
