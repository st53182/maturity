<template>
  <div class="prep-page">
    <div class="prep-container">
      <h1>{{ $t('backlogPrep.title') }}</h1>
      <p class="subtitle">{{ $t('backlogPrep.subtitle') }}</p>
      <p v-if="aiUsageRemaining !== null" class="ai-usage-line">
        {{ $t('backlogPrep.aiUsageLeft', { n: aiUsageRemaining }) }}
      </p>

      <section class="prep-intro" aria-labelledby="bp-intro-title">
        <h2 id="bp-intro-title" class="prep-intro__title">{{ $t('backlogPrep.introTitle') }}</h2>
        <p class="prep-intro__lead">{{ $t('backlogPrep.introLead') }}</p>
        <button type="button" class="prep-intro__toggle" @click="introExpanded = !introExpanded">
          {{ introExpanded ? $t('backlogPrep.introCollapse') : $t('backlogPrep.introExpand') }}
        </button>
        <div v-show="introExpanded" class="prep-intro__body">
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">1</span> {{ $t('backlogPrep.introStep1Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep1Body') }}</p>
          </article>
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">2</span> {{ $t('backlogPrep.introStep2Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep2Body') }}</p>
          </article>
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">3</span> {{ $t('backlogPrep.introStep3Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep3Body') }}</p>
          </article>
        </div>
      </section>

      <section class="ai-assist-card" aria-label="AI">
        <h2 class="ai-assist-card__title">✨ {{ $t('backlogPrep.assistTitle') }}</h2>
        <p class="ai-assist-card__hint">{{ $t('backlogPrep.assistHint') }}</p>
        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">💡</span>
          <textarea
            v-model="assistHint"
            rows="3"
            class="modern-input modern-textarea"
            :class="{ 'has-value': assistHint }"
          />
          <label class="floating-label">{{ $t('backlogPrep.assistHintLabel') }}</label>
        </div>
        <div class="ai-assist-card__actions">
          <button type="button" class="secondary-btn" :disabled="assistLoading" @click="runAssist">
            {{ assistLoading ? $t('backlogPrep.assistLoading') : $t('backlogPrep.assistRun') }}
          </button>
        </div>
        <p v-if="assistError" class="assist-error">{{ assistError }}</p>
      </section>

      <div class="modern-form">
        <div class="form-grid">
          <div class="field-block">
            <div class="input-wrapper">
              <span class="input-icon">📋</span>
              <select
                v-model="form.workType"
                class="modern-input modern-select"
                :class="{ 'has-value': form.workType }"
              >
                <option value=""></option>
                <option value="story">{{ $t('backlogPrep.story') }}</option>
                <option value="epic">{{ $t('backlogPrep.epic') }}</option>
              </select>
              <label class="floating-label">{{ $t('backlogPrep.workType') }}</label>
            </div>
            <p class="field-hint">{{ $t('backlogPrep.hintWorkType') }}</p>
          </div>

          <div class="field-block">
            <div class="input-wrapper">
              <span class="input-icon">🌐</span>
              <select
                v-model="form.language"
                class="modern-input modern-select"
                :class="{ 'has-value': form.language }"
              >
                <option value=""></option>
                <option value="ru">Русский</option>
                <option value="en">English</option>
              </select>
              <label class="floating-label">{{ $t('backlogPrep.language') }}</label>
            </div>
            <p class="field-hint">{{ $t('backlogPrep.hintLanguage') }}</p>
          </div>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">📝</span>
            <textarea
              v-model="form.text"
              rows="7"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.text }"
            />
            <label class="floating-label">{{ $t('backlogPrep.description') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintDescription') }}</p>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">🎯</span>
            <textarea
              v-model="form.context"
              rows="4"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.context }"
            />
            <label class="floating-label">{{ $t('backlogPrep.context') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintContext') }}</p>
        </div>
      </div>

      <div class="actions">
        <button class="primary" :disabled="loading" @click="analyze">
          {{ loading ? $t('common.loading') : $t('backlogPrep.run') }}
        </button>
        <span v-if="error" class="error">{{ error }}</span>
      </div>

      <div v-if="result" class="results">
        <section v-if="result.missing_fields?.length">
          <h3>🧩 {{ $t('backlogPrep.missingFields') }}</h3>
          <ul>
            <li v-for="item in result.missing_fields" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section v-if="result.questions?.length">
          <h3>❓ {{ $t('backlogPrep.questions') }}</h3>
          <ul>
            <li v-for="item in result.questions" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section v-if="result.suggestions?.length">
          <h3>💡 {{ $t('backlogPrep.suggestions') }}</h3>
          <ul>
            <li v-for="item in result.suggestions" :key="item">{{ item }}</li>
          </ul>
        </section>

        <section v-if="result.improved_example">
          <h3>📝 {{ $t('backlogPrep.improvedExample') }}</h3>
          <div class="example">{{ result.improved_example }}</div>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "BacklogPrep",
  data() {
    return {
      loading: false,
      error: "",
      result: null,
      introExpanded: false,
      assistHint: "",
      assistLoading: false,
      assistError: "",
      aiUsageRemaining: null,
      form: {
        text: "",
        context: "",
        workType: "story",
        language: "ru",
      },
    };
  },
  mounted() {
    this.fetchAiUsage();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem("token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    async fetchAiUsage() {
      try {
        const { data } = await axios.get("/api/ai-usage", { headers: this.authHeaders() });
        this.aiUsageRemaining = data?.remaining ?? null;
      } catch {
        this.aiUsageRemaining = null;
      }
    },
    async runAssist() {
      this.assistError = "";
      const hint = (this.assistHint || "").trim();
      if (!hint && !(this.form.text || "").trim()) {
        this.assistError = this.$t("backlogPrep.assistNeedHint");
        return;
      }
      this.assistLoading = true;
      try {
        const { data } = await axios.post(
          "/api/backlog/prep/assist",
          {
            hint,
            work_type: this.form.workType,
            language: this.form.language,
            existing_text: this.form.text,
            existing_context: this.form.context,
          },
          { headers: { ...this.authHeaders(), "Content-Type": "application/json" } }
        );
        if (data.suggested_text) this.form.text = data.suggested_text;
        if (data.suggested_context) this.form.context = data.suggested_context;
        await this.fetchAiUsage();
      } catch (err) {
        this.assistError =
          err?.response?.data?.error || err?.message || this.$t("common.error");
      } finally {
        this.assistLoading = false;
      }
    },
    async analyze() {
      this.error = "";
      this.result = null;

      if (!this.form.text.trim()) {
        this.error = this.$t("backlogPrep.validation");
        return;
      }

      this.loading = true;
      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.post(
          "/api/backlog/prep",
          {
            text: this.form.text,
            context: this.form.context,
            work_type: this.form.workType,
            language: this.form.language,
          },
          token
            ? { headers: { Authorization: `Bearer ${token}` } }
            : undefined
        );
        this.result = data;
        await this.fetchAiUsage();
      } catch (err) {
        this.error =
          err?.response?.data?.error ||
          err?.message ||
          this.$t("common.error");
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.prep-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.prep-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  border: 1px solid #bae6fd;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 16px;
  font-size: 16px;
  line-height: 1.6;
}

.ai-usage-line {
  margin: 0 0 20px;
  font-size: 14px;
  color: #475569;
}

.prep-intro {
  margin-bottom: 28px;
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.prep-intro__title {
  font-size: 1.2rem;
  margin: 0 0 12px;
  color: #0c4a6e;
}

.prep-intro__lead {
  margin: 0 0 16px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.prep-intro__toggle {
  background: #fff;
  border: 2px solid #0ea5e9;
  color: #0369a1;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.prep-intro__body {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prep-intro__card {
  background: #fff;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.prep-intro__card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.prep-intro__card p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.prep-intro__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #0ea5e9;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.ai-assist-card {
  margin-bottom: 28px;
  padding: 20px 22px;
  background: linear-gradient(145deg, #faf5ff 0%, #eef2ff 100%);
  border-radius: 16px;
  border: 1px solid #c7d2fe;
}

.ai-assist-card__title {
  margin: 0 0 8px;
  font-size: 1.05rem;
  color: #312e81;
}

.ai-assist-card__hint {
  margin: 0 0 14px;
  font-size: 13px;
  color: #5b21b6;
  line-height: 1.45;
}

.ai-assist-card__actions {
  margin-top: 12px;
}

.secondary-btn {
  border: 2px solid #6366f1;
  background: #fff;
  color: #4338ca;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  font-family: inherit;
}

.secondary-btn:hover:not(:disabled) {
  background: #eef2ff;
}

.secondary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.assist-error {
  margin-top: 10px;
  color: #dc2626;
  font-size: 14px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-hint {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
  padding-left: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
  margin-top: 0;
}

.input-wrapper.textarea-wrapper {
  margin-top: 0;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.textarea-wrapper .input-icon {
  top: 24px;
  transform: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.modern-textarea {
  padding-top: 32px;
  min-height: 120px;
  resize: vertical;
  line-height: 1.6;
}

.modern-select {
  padding-right: 52px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%236b7280' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
  z-index: 1;
}

.textarea-wrapper .floating-label {
  top: 32px;
  transform: none;
}

.modern-input:focus,
.modern-input.has-value {
  padding-top: 20px;
  padding-bottom: 8px;
  border-color: #0ea5e9;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f9ff 100%);
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.12);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #0284c7;
  font-weight: 600;
  transform: none;
}

.textarea-wrapper .modern-input:focus + .floating-label,
.textarea-wrapper .modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
}

.modern-input:focus {
  outline: none;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0 32px;
}

.primary {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #fff;
  border: none;
  padding: 14px 28px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
}

.primary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
}

.results {
  display: grid;
  gap: 24px;
  margin-top: 32px;
}

section {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 24px;
  border-left: 4px solid #0ea5e9;
}

section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

h3 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
}

ul {
  margin: 0;
  padding-left: 24px;
  color: #4b5563;
  line-height: 1.8;
}

.example {
  white-space: pre-wrap;
  color: #374151;
  line-height: 1.7;
  background: #f0f9ff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #bae6fd;
  font-size: 14px;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .prep-container {
    padding: 24px 20px;
  }

  h1 {
    font-size: 24px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary {
    width: 100%;
  }
}
</style>
