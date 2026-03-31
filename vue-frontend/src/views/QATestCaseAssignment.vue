<template>
  <div class="qa-doc-page">
    <button type="button" class="doc-back" @click="$router.push('/qa')">← {{ $t('qa.backToList') }}</button>

    <header class="doc-header">
      <h1>{{ $t('qa.testCaseTaskTitle') }}</h1>
      <p class="doc-intro">{{ $t('qa.testCaseTaskIntro') }}</p>
      <div class="doc-toolbar">
        <button type="button" class="doc-btn" @click="loadExample">{{ $t('qa.docLoadExample') }}</button>
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
            #{{ it.id }} — {{ it.payload?.test_title || '—' }}
          </option>
        </select>
      </div>
      <p v-if="error" class="doc-error">{{ error }}</p>
      <div v-if="fieldSuggestion.open" class="field-suggest-box">
        <div class="field-suggest-head">
          <strong>{{ $t('qa.docFieldSuggestionsTitle') }}: {{ fieldSuggestion.label }}</strong>
          <button type="button" class="doc-btn small" @click="fieldSuggestion.open = false">{{ $t('qa.docKeepAsIs') }}</button>
        </div>
        <div class="field-suggest-list">
          <div v-for="(opt, i) in fieldSuggestion.options" :key="i" class="field-suggest-item">
            <p>{{ opt }}</p>
            <button type="button" class="doc-btn small" @click="applyFieldSuggestion(opt)">{{ $t('qa.docUseOption') }} {{ i + 1 }}</button>
          </div>
        </div>
      </div>
      <div v-if="qualityScore !== null" class="doc-quality">
        <strong>{{ $t('qa.docQualityScore') }}: {{ qualityScore }}/10</strong>
        <p>{{ qualityFeedback }}</p>
      </div>
      <div v-if="aiTips.length" class="doc-ai-box">
        <strong>{{ $t('qa.docAiSuggestion') }}</strong>
        <ul><li v-for="(tip, i) in aiTips" :key="i">{{ tip }}</li></ul>
      </div>
    </header>

    <div ref="pdfContent" class="doc-form-wrap">
      <section class="doc-section">
        <h3>{{ $t('qa.tcHeader') }}</h3>
        <div class="grid-two">
          <div class="field-with-ai"><input v-model="form.test_title" :placeholder="$t('qa.tcTestTitle')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_title'" @click="askAiForField('test_title', $t('qa.tcTestTitle'))">{{ aiFieldLoading==='test_title' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.priority" :placeholder="$t('qa.tcPriority')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='priority'" @click="askAiForField('priority', $t('qa.tcPriority'))">{{ aiFieldLoading==='priority' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.test_case_id" :placeholder="$t('qa.tcCaseId')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_case_id'" @click="askAiForField('test_case_id', $t('qa.tcCaseId'))">{{ aiFieldLoading==='test_case_id' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.test_number" :placeholder="$t('qa.tcTestNumber')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_number'" @click="askAiForField('test_number', $t('qa.tcTestNumber'))">{{ aiFieldLoading==='test_number' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.test_date" :placeholder="$t('qa.tcTestDate')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_date'" @click="askAiForField('test_date', $t('qa.tcTestDate'))">{{ aiFieldLoading==='test_date' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.priority_key" :placeholder="$t('qa.tcPriorityKey')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='priority_key'" @click="askAiForField('priority_key', $t('qa.tcPriorityKey'))">{{ aiFieldLoading==='priority_key' ? '…' : 'AI' }}</button></div>
        </div>
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tcDetails') }}</h3>
        <div class="grid-two">
          <div class="field-with-ai"><input v-model="form.test_description" :placeholder="$t('qa.tcDescription')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_description'" @click="askAiForField('test_description', $t('qa.tcDescription'))">{{ aiFieldLoading==='test_description' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.test_designed_by" :placeholder="$t('qa.tcDesignedBy')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_designed_by'" @click="askAiForField('test_designed_by', $t('qa.tcDesignedBy'))">{{ aiFieldLoading==='test_designed_by' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.test_executed_by" :placeholder="$t('qa.tcExecutedBy')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_executed_by'" @click="askAiForField('test_executed_by', $t('qa.tcExecutedBy'))">{{ aiFieldLoading==='test_executed_by' ? '…' : 'AI' }}</button></div>
          <div class="field-with-ai"><input v-model="form.execution_date" :placeholder="$t('qa.tcExecutionDate')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='execution_date'" @click="askAiForField('execution_date', $t('qa.tcExecutionDate'))">{{ aiFieldLoading==='execution_date' ? '…' : 'AI' }}</button></div>
        </div>
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tcConditions') }}</h3>
        <div class="field-with-ai"><textarea v-model="form.test_dependencies" rows="3" :placeholder="$t('qa.tcDependencies')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_dependencies'" @click="askAiForField('test_dependencies', $t('qa.tcDependencies'))">{{ aiFieldLoading==='test_dependencies' ? '…' : 'AI' }}</button></div>
        <div class="field-with-ai"><textarea v-model="form.test_conditions" rows="3" :placeholder="$t('qa.tcTestConditions')" /><button type="button" class="mini-ai-btn" :disabled="aiFieldLoading==='test_conditions'" @click="askAiForField('test_conditions', $t('qa.tcTestConditions'))">{{ aiFieldLoading==='test_conditions' ? '…' : 'AI' }}</button></div>
      </section>
      <section class="doc-section">
        <h3>{{ $t('qa.tcSteps') }}</h3>
        <div class="steps-actions">
          <button type="button" class="doc-btn small" @click="addRow">{{ $t('qa.tcAddRow') }}</button>
          <button type="button" class="doc-btn small" :disabled="form.steps.length <= 1" @click="removeLastRow">{{ $t('qa.tcRemoveLastRow') }}</button>
          <span class="steps-count">{{ $t('qa.tcRowsCount') }}: {{ form.steps.length }}</span>
        </div>
        <div class="steps-table-wrap">
          <table class="steps-table">
            <colgroup>
              <col class="col-id">
              <col class="col-desc">
              <col class="col-expected">
              <col class="col-actual">
              <col class="col-passfail">
              <col class="col-notes">
            </colgroup>
            <thead>
              <tr>
                <th>ID</th><th>{{ $t('qa.tcStepDescription') }}</th><th>{{ $t('qa.tcExpected') }}</th><th>{{ $t('qa.tcActual') }}</th><th>{{ $t('qa.tcPassFail') }}</th><th>{{ $t('qa.tcNotes') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(s, i) in form.steps" :key="i">
                <td><div class="cell-with-ai"><input v-model="s.step_id" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.step_id`" @click="askAiForField(`steps.${i}.step_id`, 'Step ID')">AI</button></div></td>
                <td><div class="cell-with-ai"><textarea v-model="s.step_description" rows="2" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.step_description`" @click="askAiForField(`steps.${i}.step_description`, $t('qa.tcStepDescription'))">AI</button></div></td>
                <td><div class="cell-with-ai"><textarea v-model="s.expected_results" rows="2" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.expected_results`" @click="askAiForField(`steps.${i}.expected_results`, $t('qa.tcExpected'))">AI</button></div></td>
                <td><div class="cell-with-ai"><textarea v-model="s.actual_results" rows="2" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.actual_results`" @click="askAiForField(`steps.${i}.actual_results`, $t('qa.tcActual'))">AI</button></div></td>
                <td><div class="cell-with-ai"><input v-model="s.pass_fail" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.pass_fail`" @click="askAiForField(`steps.${i}.pass_fail`, $t('qa.tcPassFail'))">AI</button></div></td>
                <td><div class="cell-with-ai"><input v-model="s.additional_notes" /><button type="button" class="cell-ai-btn" :disabled="aiFieldLoading===`steps.${i}.additional_notes`" @click="askAiForField(`steps.${i}.additional_notes`, $t('qa.tcNotes'))">AI</button></div></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>

    <section class="doc-list">
      <h2>{{ $t('qa.docMySaved') }}</h2>
      <p v-if="loadingList">{{ $t('qa.docLoading') }}</p>
      <p v-else-if="!items.length">{{ $t('qa.docEmpty') }}</p>
      <div v-else class="doc-list-grid">
        <article v-for="item in items" :key="item.id" class="doc-item">
          <strong>{{ item.payload?.test_title || '—' }}</strong>
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

function makeSteps() {
  return Array.from({ length: 18 }).map((_, i) => ({
    step_id: `${i + 1}.0`,
    step_description: '',
    expected_results: '',
    actual_results: '',
    pass_fail: '',
    additional_notes: '',
  }));
}

function makeStepByIndex(index) {
  return {
    step_id: `${index + 1}.0`,
    step_description: '',
    expected_results: '',
    actual_results: '',
    pass_fail: '',
    additional_notes: '',
  };
}

function defaultForm() {
  return {
    test_title: '',
    priority: '',
    test_case_id: '',
    test_number: '',
    test_date: '',
    priority_key: '',
    test_description: '',
    test_designed_by: '',
    test_executed_by: '',
    execution_date: '',
    test_dependencies: '',
    test_conditions: '',
    steps: makeSteps(),
  };
}

function exampleForm() {
  const steps = makeSteps();
  steps[0].step_description = 'Открыть страницу входа GrowBoard';
  steps[0].expected_results = 'Страница входа отображается без ошибок';
  steps[1].step_description = 'Ввести валидные учетные данные и нажать «Войти»';
  steps[1].expected_results = 'Пользователь авторизуется и попадает на дашборд';
  steps[2].step_description = 'Перейти в скрытый раздел /qa и открыть задание 7';
  steps[2].expected_results = 'Страница Test Case загружается, форма доступна';
  steps[3].step_description = 'Нажать «Помощь AI»';
  steps[3].expected_results = 'Появляются подсказки и/или предложенные шаги';
  steps[4].step_description = 'Нажать «Оценить качество»';
  steps[4].expected_results = 'Отображается оценка 1-10 и комментарий';

  return {
    test_title: 'Проверка заполнения и AI-помощи Test Case',
    priority: 'HIGH',
    test_case_id: 'GB-TC-001',
    test_number: '1',
    test_date: new Date().toLocaleDateString('ru-RU'),
    priority_key: 'HIGH',
    test_description: 'Проверить создание тест-кейса, AI-помощь, оценку качества и сохранение.',
    test_designed_by: 'QA Engineer',
    test_executed_by: '',
    execution_date: '',
    test_dependencies: 'Активный тестовый аккаунт и доступ к /qa/test-case',
    test_conditions: 'Пользователь авторизован; API доступно',
    steps,
  };
}

export default {
  name: 'QATestCaseAssignment',
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
      aiTips: [],
      qualityScore: null,
      qualityFeedback: '',
      selectedSavedId: null,
      aiFieldLoading: '',
      fieldSuggestion: { open: false, path: '', label: '', options: [] },
    };
  },
  mounted() {
    this.loadItems();
  },
  methods: {
    getByPath(path) {
      const parts = String(path || '').split('.');
      let cur = this.form;
      for (const p of parts) {
        if (cur == null) return '';
        cur = cur[p];
      }
      return cur == null ? '' : String(cur);
    },
    setByPath(path, value) {
      const parts = String(path || '').split('.');
      let cur = this.form;
      for (let i = 0; i < parts.length - 1; i++) {
        cur = cur[parts[i]];
        if (cur == null) return;
      }
      cur[parts[parts.length - 1]] = value;
    },
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
        const { data } = await axios.post('/api/qa-test-docs/case/ai-help', {
          prompt: 'Помоги сформировать шаги тест-кейса для GrowBoard',
          form: this.form,
        }, this.authConfig());
        this.aiTips = data.tips || [];
        if (data.test_description && !this.form.test_description) this.form.test_description = data.test_description;
        if (Array.isArray(data.steps) && data.steps.length) {
          this.form.steps = makeSteps().map((s, idx) => ({ ...s, ...(data.steps[idx] || {}) }));
        }
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка AI-запроса';
      } finally {
        this.aiLoading = false;
      }
    },
    async askAiForField(fieldPath, label) {
      this.aiFieldLoading = fieldPath;
      this.error = '';
      try {
        const { data } = await axios.post('/api/qa-test-docs/case/ai-help', {
          target_field: fieldPath,
          target_label: label,
          current_value: this.getByPath(fieldPath),
          prompt: `Сформулируй качественный текст для поля "${label}"`,
          form: this.form,
        }, this.authConfig());
        const options = Array.isArray(data.suggestions) ? data.suggestions.filter(Boolean) : (data.suggested_text ? [data.suggested_text] : []);
        this.fieldSuggestion = { open: !!options.length, path: fieldPath, label, options };
      } catch (e) {
        if (e.response?.status === 401) this.error = this.$t('qa.docAuthRequired');
        else this.error = e.response?.data?.error || 'Ошибка AI-запроса';
      } finally {
        this.aiFieldLoading = '';
      }
    },
    applyFieldSuggestion(text) {
      if (!this.fieldSuggestion.path) return;
      this.setByPath(this.fieldSuggestion.path, text);
      this.fieldSuggestion.open = false;
    },
    loadExample() {
      this.editingId = null;
      this.form = exampleForm();
      this.qualityScore = null;
      this.qualityFeedback = '';
      this.aiTips = [];
    },
    async evaluate() {
      this.evaluateLoading = true;
      this.error = '';
      try {
        const { data } = await axios.post('/api/qa-test-docs/case/evaluate', { payload: this.form }, this.authConfig());
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
        if (this.editingId) await axios.put(`/api/qa-test-docs/case/submissions/${this.editingId}`, payload, this.authConfig());
        else await axios.post('/api/qa-test-docs/case/submit', payload, this.authConfig());
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
      const token = this.getAuthToken();
      if (!token) {
        this.items = [];
        this.loadingList = false;
        return;
      }
      try {
        const { data } = await axios.get('/api/qa-test-docs/case/submissions', this.authConfig());
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
      if (!Array.isArray(this.form.steps)) this.form.steps = makeSteps();
      if (this.form.steps.length < 18) {
        const extra = makeSteps().slice(this.form.steps.length);
        this.form.steps = [...this.form.steps, ...extra];
      }
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
      this.aiTips = [];
    },
    addRow() {
      this.form.steps.push(makeStepByIndex(this.form.steps.length));
    },
    removeLastRow() {
      if (this.form.steps.length <= 1) return;
      this.form.steps.pop();
    },
    async removeItem(item) {
      if (!confirm(this.$t('qa.userStoryDeleteConfirm'))) return;
      this.error = '';
      try {
        await axios.delete(`/api/qa-test-docs/case/submissions/${item.id}`, this.authConfig());
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
        pdf.save(`test-case-${Date.now()}.pdf`);
      } finally {
        this.exporting = false;
      }
    },
  },
};
</script>

<style scoped>
.qa-doc-page { max-width: 1080px; margin: 0 auto; padding: 24px 16px; }
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
.field-suggest-box { margin-top: 10px; border: 1px solid #bfdbfe; background: #eff6ff; border-radius: 10px; padding: 10px; }
.field-suggest-head { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.field-suggest-list { display: grid; gap: 8px; }
.field-suggest-item { border: 1px solid #dbeafe; border-radius: 8px; background: #fff; padding: 8px; }
.field-suggest-item p { margin: 0 0 8px; white-space: pre-wrap; }
.doc-form-wrap { display: grid; gap: 10px; margin-top: 12px; }
.doc-section { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; background: #fff; }
.doc-section input, .doc-section textarea { width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; box-sizing: border-box; font-size: 13px; }
.field-with-ai { display: grid; grid-template-columns: 1fr auto; gap: 6px; align-items: start; }
.mini-ai-btn { border: 1px solid #cbd5e1; background: #f8fafc; color: #334155; border-radius: 8px; min-width: 36px; height: 36px; padding: 0 8px; cursor: pointer; font-size: 12px; }
.grid-two { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }
.steps-actions { display: flex; gap: 8px; align-items: center; margin-bottom: 10px; }
.steps-count { color: #64748b; font-size: 12px; margin-left: auto; }
.steps-table-wrap { width: 100%; overflow-x: auto; border: 1px solid #e5e7eb; border-radius: 10px; }
.steps-table { width: 100%; min-width: 980px; border-collapse: collapse; table-layout: fixed; }
.steps-table th, .steps-table td { border: 1px solid #e5e7eb; padding: 8px; vertical-align: top; background: #fff; }
.steps-table th { background: #f8fafc; font-weight: 700; font-size: 12px; color: #334155; text-align: left; }
.steps-table .col-id { width: 70px; }
.steps-table .col-desc { width: 25%; }
.steps-table .col-expected { width: 25%; }
.steps-table .col-actual { width: 25%; }
.steps-table .col-passfail { width: 80px; }
.steps-table .col-notes { width: 140px; }
.steps-table textarea { min-height: 64px; resize: vertical; line-height: 1.35; }
.steps-table input { min-height: 36px; }
.cell-with-ai { display: grid; grid-template-columns: 1fr auto; gap: 6px; align-items: start; }
.cell-ai-btn { border: 1px solid #cbd5e1; background: #f8fafc; color: #334155; border-radius: 8px; min-width: 34px; height: 34px; cursor: pointer; font-size: 11px; }
.steps-table tbody tr:nth-child(even) td { background: #fcfcfd; }
.doc-list { margin-top: 24px; }
.doc-list-grid { display: grid; gap: 10px; }
.doc-item { border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; display: grid; gap: 6px; }
.doc-item-actions { display: flex; gap: 8px; }
</style>
