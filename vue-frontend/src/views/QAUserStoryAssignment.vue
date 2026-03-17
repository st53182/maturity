<template>
  <div class="qa-user-story-page">
    <button type="button" class="us-back" @click="$router.push('/qa')">← {{ $t('qa.backToList') }}</button>

    <header class="us-header">
      <h1>{{ $t('qa.userStoryTaskTitle') }}</h1>
      <p class="us-intro">{{ $t('qa.userStoryTaskIntro') }}</p>
    </header>

    <section v-if="!submitted" class="us-form-section">
      <div class="us-field">
        <label>{{ $t('qa.userStoryTeamName') }}</label>
        <input v-model="form.team_name" type="text" :placeholder="$t('qa.userStoryTeamNamePlaceholder')" />
      </div>
      <div class="us-field">
        <label>{{ $t('qa.userStoryLabel') }}</label>
        <textarea
          v-model="form.user_story"
          class="us-textarea"
          rows="4"
          :placeholder="$t('qa.userStoryPlaceholder')"
        />
      </div>
      <div class="us-field">
        <label>{{ $t('qa.userStoryACLabel') }}</label>
        <textarea
          v-model="form.ac_text"
          class="us-textarea"
          rows="12"
          :placeholder="$t('qa.userStoryACPlaceholder')"
        />
        <span class="us-hint">{{ $t('qa.userStoryACHint') }}</span>
      </div>
      <div class="us-actions">
        <button
          type="button"
          class="us-btn primary"
          :disabled="!form.user_story.trim() || evaluateLoading"
          @click="evaluate"
        >
          {{ evaluateLoading ? '…' : $t('qa.userStoryCheckQuality') }}
        </button>
        <button
          type="button"
          class="us-btn success"
          :disabled="!canSubmit || submitLoading"
          @click="submit"
        >
          {{ submitLoading ? '…' : $t('qa.userStorySendToDev') }}
        </button>
      </div>
      <div v-if="lastScore !== null" class="us-result">
        <span class="us-score" :class="scoreClass(lastScore)">{{ $t('qa.userStoryScore') }}: {{ lastScore }} / 10</span>
        <span class="us-ac-count">{{ $t('qa.userStoryACCount') }}: {{ lastAcCount }}</span>
        <p v-if="lastFeedback" class="us-feedback">{{ lastFeedback }}</p>
      </div>
      <p v-if="formError" class="us-error">{{ formError }}</p>
    </section>

    <section v-else class="us-success-msg">
      <p>{{ $t('qa.userStorySentMessage') }}</p>
      <button type="button" class="us-btn secondary" @click="submitted = false; formError = ''">{{ $t('qa.userStoryAddAnother') }}</button>
    </section>

    <section class="us-pool-section">
      <h2 class="us-pool-title">{{ $t('qa.userStoryPoolTitle') }}</h2>
      <p v-if="poolLoading" class="us-loading">{{ $t('qa.userStoryPoolLoading') }}</p>
      <p v-else-if="!pool.length" class="us-empty">{{ $t('qa.userStoryPoolEmpty') }}</p>
      <div v-else class="us-pool-list">
        <div v-for="item in pool" :key="item.id" class="us-pool-card">
          <div class="us-pool-card-head">
            <strong>{{ item.team_name || '—' }}</strong>
            <span class="us-pool-date">{{ formatDate(item.created_at) }}</span>
            <span class="us-pool-badges">Оценка: {{ item.score }}/10, AC: {{ item.ac_count }}</span>
          </div>
          <p class="us-pool-story">{{ item.user_story }}</p>
          <ul v-if="item.ac_list && item.ac_list.length" class="us-pool-ac">
            <li v-for="(c, i) in item.ac_list" :key="i">{{ c }}</li>
          </ul>
          <div class="us-pool-actions">
            <button type="button" class="us-btn small" @click="startEdit(item)">{{ $t('qa.userStoryEdit') }}</button>
            <button type="button" class="us-btn small danger" @click="confirmDelete(item)">{{ $t('qa.userStoryDelete') }}</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Модалка редактирования -->
    <div v-if="editing" class="us-modal-overlay" @click.self="editing = null">
      <div class="us-modal">
        <h3>{{ $t('qa.userStoryEditTitle') }}</h3>
        <div class="us-field">
          <label>{{ $t('qa.userStoryTeamName') }}</label>
          <input v-model="editForm.team_name" type="text" />
        </div>
        <div class="us-field">
          <label>{{ $t('qa.userStoryLabel') }}</label>
          <textarea v-model="editForm.user_story" class="us-textarea" rows="3" />
        </div>
        <div class="us-field">
          <label>{{ $t('qa.userStoryACLabel') }}</label>
          <textarea v-model="editForm.ac_text" class="us-textarea" rows="8" />
        </div>
        <div class="us-modal-actions">
          <button type="button" class="us-btn secondary" @click="editing = null">{{ $t('qa.userStoryCancel') }}</button>
          <button type="button" class="us-btn primary" :disabled="saveLoading" @click="saveEdit">{{ saveLoading ? '…' : $t('qa.userStorySave') }}</button>
        </div>
      </div>
    </div>

    <!-- Подтверждение удаления -->
    <div v-if="deleting" class="us-modal-overlay" @click.self="deleting = null">
      <div class="us-modal">
        <h3>{{ $t('qa.userStoryDeleteConfirm') }}</h3>
        <p>{{ deleting.team_name || 'Запись' }} — {{ formatDate(deleting.created_at) }}</p>
        <div class="us-modal-actions">
          <button type="button" class="us-btn secondary" @click="deleting = null">{{ $t('qa.userStoryCancel') }}</button>
          <button type="button" class="us-btn danger" :disabled="deleteLoading" @click="doDelete">{{ deleteLoading ? '…' : $t('qa.userStoryDelete') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'QAUserStoryAssignment',
  data() {
    return {
      form: {
        team_name: '',
        user_story: '',
        ac_text: '',
      },
      lastScore: null,
      lastFeedback: '',
      lastAcCount: 0,
      evaluateLoading: false,
      submitLoading: false,
      formError: '',
      submitted: false,
      pool: [],
      poolLoading: false,
      editing: null,
      editForm: { team_name: '', user_story: '', ac_text: '' },
      saveLoading: false,
      deleting: null,
      deleteLoading: false,
    };
  },
  computed: {
    acList() {
      return (this.form.ac_text || '')
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean);
    },
    canSubmit() {
      return this.lastScore !== null && this.lastScore >= 8 && this.lastAcCount >= 10;
    },
  },
  mounted() {
    this.loadPool();
  },
  methods: {
    async evaluate() {
      if (!this.form.user_story.trim()) return;
      this.evaluateLoading = true;
      this.formError = '';
      try {
        const { data } = await axios.post('/api/qa-user-story/evaluate', {
          team_name: this.form.team_name,
          user_story: this.form.user_story,
          acceptance_criteria: this.acList.length ? this.acList : (this.form.ac_text || '').split('\n').map(s => s.trim()).filter(Boolean),
        });
        this.lastScore = data.score != null ? Number(data.score) : 0;
        this.lastFeedback = data.feedback || '';
        this.lastAcCount = data.ac_count != null ? Number(data.ac_count) : 0;
      } catch (e) {
        this.formError = e.response?.data?.error || 'Ошибка запроса';
      } finally {
        this.evaluateLoading = false;
      }
    },
    async submit() {
      if (!this.canSubmit) return;
      this.submitLoading = true;
      this.formError = '';
      try {
        await axios.post('/api/qa-user-story/submit', {
          team_name: this.form.team_name,
          user_story: this.form.user_story,
          acceptance_criteria: this.acList,
          score: this.lastScore,
          ac_count: this.lastAcCount,
        });
        this.submitted = true;
        this.loadPool();
      } catch (e) {
        this.formError = e.response?.data?.error || 'Ошибка отправки';
      } finally {
        this.submitLoading = false;
      }
    },
    async loadPool() {
      this.poolLoading = true;
      try {
        const { data } = await axios.get('/api/qa-user-story/submissions');
        this.pool = (data.items || []).map(it => ({
          ...it,
          ac_list: Array.isArray(it.acceptance_criteria) ? it.acceptance_criteria : [],
        }));
      } catch (e) {
        this.pool = [];
      } finally {
        this.poolLoading = false;
      }
    },
    formatDate(iso) {
      if (!iso) return '';
      try {
        return new Date(iso).toLocaleString('ru-RU', { day: 'numeric', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
      } catch {
        return iso;
      }
    },
    scoreClass(score) {
      if (score >= 8) return 'score-high';
      if (score >= 5) return 'score-mid';
      return 'score-low';
    },
    startEdit(item) {
      this.editing = item;
      this.editForm = {
        team_name: item.team_name || '',
        user_story: item.user_story || '',
        ac_text: (item.ac_list || []).join('\n'),
      };
    },
    async saveEdit() {
      if (!this.editing) return;
      this.saveLoading = true;
      try {
        const acList = this.editForm.ac_text.split('\n').map(s => s.trim()).filter(Boolean);
        await axios.put(`/api/qa-user-story/submissions/${this.editing.id}`, {
          team_name: this.editForm.team_name,
          user_story: this.editForm.user_story,
          acceptance_criteria: acList,
        });
        this.editing = null;
        this.loadPool();
      } catch (e) {
        this.formError = e.response?.data?.error || 'Ошибка сохранения';
      } finally {
        this.saveLoading = false;
      }
    },
    confirmDelete(item) {
      this.deleting = item;
    },
    async doDelete() {
      if (!this.deleting) return;
      this.deleteLoading = true;
      try {
        await axios.delete(`/api/qa-user-story/submissions/${this.deleting.id}`);
        this.deleting = null;
        this.loadPool();
      } catch (e) {
        this.formError = e.response?.data?.error || 'Ошибка удаления';
      } finally {
        this.deleteLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.qa-user-story-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 24px 16px;
}

.us-back {
  margin-bottom: 16px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  color: #475569;
}

.us-back:hover {
  background: #e2e8f0;
}

.us-header {
  margin-bottom: 24px;
}

.us-header h1 {
  font-size: 1.6rem;
  color: #1e293b;
  margin: 0 0 8px;
}

.us-intro {
  color: #475569;
  line-height: 1.5;
  margin: 0;
}

.us-form-section .us-field,
.us-modal .us-field {
  margin-bottom: 16px;
}

.us-form-section label,
.us-modal label {
  display: block;
  font-weight: 600;
  color: #334155;
  margin-bottom: 6px;
}

.us-form-section input,
.us-form-section .us-textarea,
.us-modal input,
.us-modal .us-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.95rem;
}

.us-textarea {
  resize: vertical;
  min-height: 80px;
}

.us-hint {
  font-size: 0.85rem;
  color: #64748b;
  margin-top: 4px;
  display: block;
}

.us-actions {
  display: flex;
  gap: 12px;
  margin: 20px 0 16px;
}

.us-btn {
  padding: 10px 20px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.95rem;
}

.us-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.us-btn.primary {
  background: #0d9488;
  color: #fff;
}

.us-btn.success {
  background: #059669;
  color: #fff;
}

.us-btn.secondary {
  background: #e2e8f0;
  color: #334155;
}

.us-btn.danger {
  background: #dc2626;
  color: #fff;
}

.us-btn.small {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.us-result {
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  margin-top: 12px;
}

.us-score { font-weight: 600; margin-right: 12px; }
.us-score.score-high { color: #059669; }
.us-score.score-mid { color: #d97706; }
.us-score.score-low { color: #dc2626; }
.us-ac-count { color: #64748b; font-size: 0.9rem; }
.us-feedback { margin: 10px 0 0; color: #475569; }
.us-error { color: #dc2626; margin-top: 12px; }

.us-success-msg {
  padding: 24px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 12px;
  margin-bottom: 32px;
}

.us-success-msg p { margin: 0 0 16px; font-weight: 600; color: #065f46; }

.us-pool-section {
  margin-top: 40px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.us-pool-title {
  font-size: 1.25rem;
  color: #1e293b;
  margin: 0 0 16px;
}

.us-loading,
.us-empty {
  color: #64748b;
  margin: 0;
}

.us-pool-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.us-pool-card {
  padding: 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
}

.us-pool-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 10px;
}

.us-pool-date {
  font-size: 0.85rem;
  color: #64748b;
}

.us-pool-badges {
  font-size: 0.85rem;
  color: #475569;
  margin-left: auto;
}

.us-pool-story {
  margin: 0 0 10px;
  color: #334155;
  line-height: 1.5;
}

.us-pool-ac {
  margin: 0 0 12px;
  padding-left: 20px;
  color: #475569;
  font-size: 0.9rem;
}

.us-pool-actions {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}

.us-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.us-modal {
  background: #fff;
  padding: 24px;
  border-radius: 12px;
  max-width: 560px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.us-modal h3 {
  margin: 0 0 20px;
  font-size: 1.2rem;
}

.us-modal-actions {
  display: flex;
  gap: 12px;
  margin-top: 20px;
}
</style>
