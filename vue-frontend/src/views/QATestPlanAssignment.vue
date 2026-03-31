<template>
  <div class="qa-doc-page">
    <button type="button" class="doc-back" @click="$router.push('/qa')">← {{ $t('qa.backToList') }}</button>

    <header class="doc-header">
      <h1>{{ $t('qa.testPlanTaskTitle') }}</h1>
      <p class="doc-intro">{{ $t('qa.testPlanTaskIntro') }}</p>
      <div class="doc-toolbar">
        <button type="button" class="doc-btn" :disabled="aiLoading" @click="askAi">{{ aiLoading ? '…' : $t('qa.docAiHelp') }}</button>
        <button type="button" class="doc-btn" :disabled="evaluateLoading" @click="evaluate">{{ evaluateLoading ? '…' : $t('qa.docEvaluate') }}</button>
        <button type="button" class="doc-btn success" :disabled="saveLoading" @click="save">{{ saveLoading ? '…' : $t('qa.docSave') }}</button>
        <button type="button" class="doc-btn" @click="resetForm">{{ $t('qa.docNewTemplate') }}</button>
        <button type="button" class="doc-btn" :disabled="!items.length" @click="openSelectedSaved">{{ $t('qa.docOpenFilledTemplate') }}</button>
        <button type="button" class="doc-btn secondary" :disabled="exporting" @click="exportPdf">{{ exporting ? '…' : $t('qa.docExportPdf') }}</button>
      </div>
      <div v-if="items.length" class="doc-open-row">
        <select v-model="selectedSavedId" class="doc-select">
          <option :value="null">{{ $t('qa.docSelectSavedTemplate') }}</option>
          <option v-for="it in items" :key="it.id" :value="it.id">
            #{{ it.id }} — {{ it.payload?.test_plan_identifier || '—' }}
          </option>
        </select>
      </div>
      <p v-if="error" class="doc-error">{{ error }}</p>
      <div v-if="qualityScore !== null" class="doc-quality">
        <strong>{{ $t('qa.docQualityScore') }}: {{ qualityScore }}/10</strong>
        <p>{{ qualityFeedback }}</p>
      </div>
      <div v-if="aiText" class="doc-ai-box">
        <strong>{{ $t('qa.docAiSuggestion') }}</strong>
        <p>{{ aiText }}</p>
      </div>
    </header>

    <div ref="pdfContent" class="doc-form-wrap">
      <section class="doc-section">
        <h3>{{ $t('qa.tpIdentifier') }}</h3>
        <input v-model="form.test_plan_identifier" type="text" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpIntroduction') }}</h3>
        <textarea v-model="form.introduction" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpTestItems') }}</h3>
        <textarea v-model="form.test_items" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpTestableFeatures') }}</h3>
        <textarea v-model="form.testable_features" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpNonTestableFeatures') }}</h3>
        <textarea v-model="form.non_testable_features" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpApproach') }}</h3>
        <textarea v-model="form.approach" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpPassFail') }}</h3>
        <textarea v-model="form.pass_fail_criteria" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpDeliverables') }}</h3>
        <textarea v-model="form.test_deliverables" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpTasks') }}</h3>
        <textarea v-model="form.testing_tasks" rows="6" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpEnvironment') }}</h3>
        <textarea v-model="form.environmental_needs" rows="4" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpResponsibilities') }}</h3>
        <textarea v-model="form.responsibilities" rows="3" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpDefects') }}</h3>
        <textarea v-model="form.known_defects" rows="5" />
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tpApprovals') }}</h3>
        <textarea v-model="form.approvals" rows="3" />
      </section>
    </div>

    <section class="doc-list">
      <h2>{{ $t('qa.docMySaved') }}</h2>
      <p v-if="loadingList">{{ $t('qa.docLoading') }}</p>
      <p v-else-if="!items.length">{{ $t('qa.docEmpty') }}</p>
      <div v-else class="doc-list-grid">
        <article v-for="item in items" :key="item.id" class="doc-item">
          <strong>{{ item.payload?.test_plan_identifier || '—' }}</strong>
          <span>{{ formatDate(item.updated_at || item.created_at) }}</span>
          <span>{{ $t('qa.docQualityScore') }}: {{ item.quality_score ?? '—' }}</span>
          <div class="doc-item-actions">
            <button type="button" class="doc-btn small" @click="loadItem(item)">{{ $t('qa.docOpen') }}</button>
            <button type="button" class="doc-btn small danger" @click="removeItem(item)">{{ $t('qa.userStoryDelete') }}</button>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

function defaultForm() {
  return {
    test_plan_identifier: '',
    introduction: '',
    test_items: '',
    testable_features: '',
    non_testable_features: '',
    approach: '',
    pass_fail_criteria: '',
    test_deliverables: '',
    testing_tasks: '',
    environmental_needs: '',
    responsibilities: '',
    known_defects: '',
    approvals: '',
  };
}

export default {
  name: 'QATestPlanAssignment',
  data() {
    return {
      form: defaultForm(),
      editingId: null,
      items: [],
      loadingList: false,
      aiLoading: false,
      evaluateLoading: false,
      saveLoading: false,
      exporting: false,
      error: '',
      aiText: '',
      qualityScore: null,
      qualityFeedback: '',
      selectedSavedId: null,
    };
  },
  mounted() {
    this.loadItems();
  },
  methods: {
    getAuthToken() {
      return localStorage.getItem('token') || localStorage.getItem('access_token') || '';
    },
    authConfig() {
      const token = this.getAuthToken();
      return { headers: token ? { Authorization: `Bearer ${token}` } : {} };
    },
    async askAi() {
      this.aiLoading = true;
      this.error = '';
      try {
        const { data } = await axios.post('/api/qa-test-docs/plan/ai-help', {
          section: 'general',
          prompt: 'Помоги улучшить текущий Test Plan',
          form: this.form,
        }, this.authConfig());
        this.aiText = data.suggested_text || '';
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка AI-запроса';
      } finally {
        this.aiLoading = false;
      }
    },
    async evaluate() {
      this.evaluateLoading = true;
      this.error = '';
      try {
        const { data } = await axios.post('/api/qa-test-docs/plan/evaluate', { payload: this.form }, this.authConfig());
        this.qualityScore = Number(data.score || 0);
        this.qualityFeedback = data.feedback || '';
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка оценки';
      } finally {
        this.evaluateLoading = false;
      }
    },
    async save() {
      this.saveLoading = true;
      this.error = '';
      try {
        const payload = {
          team_name: '',
          payload: this.form,
          quality_score: this.qualityScore,
          quality_feedback: this.qualityFeedback,
        };
        if (this.editingId) await axios.put(`/api/qa-test-docs/plan/submissions/${this.editingId}`, payload, this.authConfig());
        else await axios.post('/api/qa-test-docs/plan/submit', payload, this.authConfig());
        await this.loadItems();
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка сохранения';
      } finally {
        this.saveLoading = false;
      }
    },
    async loadItems() {
      this.loadingList = true;
      try {
        const { data } = await axios.get('/api/qa-test-docs/plan/submissions', this.authConfig());
        this.items = data.items || [];
        if (!this.selectedSavedId && this.items.length) this.selectedSavedId = this.items[0].id;
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        this.items = [];
      } finally {
        this.loadingList = false;
      }
    },
    loadItem(item) {
      this.editingId = item.id;
      this.form = { ...defaultForm(), ...(item.payload || {}) };
      this.qualityScore = item.quality_score ?? null;
      this.qualityFeedback = item.quality_feedback || '';
      this.selectedSavedId = item.id;
    },
    openSelectedSaved() {
      const found = this.items.find((x) => x.id === this.selectedSavedId);
      if (found) this.loadItem(found);
    },
    resetForm() {
      this.editingId = null;
      this.form = defaultForm();
      this.qualityScore = null;
      this.qualityFeedback = '';
      this.aiText = '';
    },
    async removeItem(item) {
      if (!confirm(this.$t('qa.userStoryDeleteConfirm'))) return;
      this.error = '';
      try {
        await axios.delete(`/api/qa-test-docs/plan/submissions/${item.id}`, this.authConfig());
        if (this.editingId === item.id) {
          this.editingId = null;
          this.form = defaultForm();
          this.qualityScore = null;
          this.qualityFeedback = '';
        }
        await this.loadItems();
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка удаления';
      }
    },
    formatDate(iso) {
      if (!iso) return '';
      return new Date(iso).toLocaleString('ru-RU');
    },
    async exportPdf() {
      if (this.exporting) return;
      const el = this.$refs.pdfContent;
      if (!el) return;
      this.exporting = true;
      try {
        const canvas = await html2canvas(el, { scale: 2, useCORS: true, logging: false, backgroundColor: '#ffffff' });
        const imgData = canvas.toDataURL('image/jpeg', 0.92);
        const pdf = new jsPDF('p', 'mm', 'a4');
        const w = pdf.internal.pageSize.getWidth();
        const h = pdf.internal.pageSize.getHeight();
        const ratio = Math.min(w / canvas.width, h / canvas.height);
        const imgW = canvas.width * ratio;
        const imgH = canvas.height * ratio;
        pdf.addImage(imgData, 'JPEG', (w - imgW) / 2, 10, imgW, imgH);
        pdf.save(`test-plan-${Date.now()}.pdf`);
      } finally {
        this.exporting = false;
      }
    },
  },
};
</script>

<style scoped>
.qa-doc-page { max-width: 980px; margin: 0 auto; padding: 24px 16px; }
.doc-back { margin-bottom: 16px; }
.doc-header { margin-bottom: 16px; }
.doc-toolbar { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.doc-open-row { margin-top: 10px; }
.doc-select { min-width: 280px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 7px 10px; }
.doc-btn { border: 1px solid #d1d5db; background: #fff; border-radius: 8px; padding: 8px 12px; cursor: pointer; }
.doc-btn.success { background: #059669; border-color: #059669; color: #fff; }
.doc-btn.secondary { background: #334155; border-color: #334155; color: #fff; }
.doc-btn.danger { background: #dc2626; border-color: #dc2626; color: #fff; }
.doc-btn.small { padding: 6px 10px; font-size: 12px; }
.doc-error { color: #dc2626; margin-top: 10px; }
.doc-quality, .doc-ai-box { margin-top: 10px; padding: 10px; border: 1px solid #e2e8f0; border-radius: 8px; background: #f8fafc; }
.doc-form-wrap { display: grid; gap: 10px; }
.doc-section { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fff; }
.doc-section h3 { margin: 0 0 8px; font-size: 15px; }
.doc-section input, .doc-section textarea { width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; }
.doc-list { margin-top: 24px; }
.doc-list-grid { display: grid; gap: 10px; }
.doc-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; display: grid; gap: 6px; }
.doc-item-actions { display: flex; gap: 8px; }
</style>
