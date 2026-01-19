<template>
  <div class="prep-container">
    <h1>{{ $t('backlogPrep.title') }}</h1>
    <p class="subtitle">{{ $t('backlogPrep.subtitle') }}</p>

    <div class="modern-form">
      <div class="form-grid">
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
      </div>

      <div class="input-wrapper textarea-wrapper">
        <span class="input-icon">📝</span>
        <textarea
          v-model="form.text"
          rows="7"
          class="modern-input modern-textarea"
          :class="{ 'has-value': form.text }"
        ></textarea>
        <label class="floating-label">{{ $t('backlogPrep.description') }}</label>
      </div>

      <div class="input-wrapper textarea-wrapper">
        <span class="input-icon">🎯</span>
        <textarea
          v-model="form.context"
          rows="4"
          class="modern-input modern-textarea"
          :class="{ 'has-value': form.context }"
        ></textarea>
        <label class="floating-label">{{ $t('backlogPrep.context') }}</label>
      </div>
    </div>

    <div class="actions">
      <button class="primary" @click="analyze" :disabled="loading">
        {{ loading ? $t('common.loading') : $t('backlogPrep.run') }}
      </button>
      <span class="error" v-if="error">{{ error }}</span>
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
      form: {
        text: "",
        context: "",
        workType: "story",
        language: "ru",
      },
    };
  },
  methods: {
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
.prep-container {
  max-width: 1000px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
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
  margin-bottom: 32px;
  font-size: 16px;
  line-height: 1.6;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

/* Modern Form Styles with Floating Labels */
.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
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
  border-color: #3b82f6;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f7ff 100%);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 4px 12px rgba(59, 130, 246, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
  transform: none;
}

.textarea-wrapper .modern-input:focus + .floating-label,
.textarea-wrapper .modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
}

.modern-input:hover:not(:focus) {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.modern-input:focus {
  outline: none;
}

.modern-input:focus ~ .input-icon {
  transform: translateY(-50%) scale(1.1);
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
}

.textarea-wrapper .modern-input:focus ~ .input-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
}

.block {
  margin-bottom: 24px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0 32px;
}

.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: #fff;
  border: none;
  padding: 14px 28px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
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
  transition: all 0.2s ease;
}

section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

h3 {
  margin: 0 0 16px;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  letter-spacing: -0.3px;
}

ul {
  margin: 0;
  padding-left: 24px;
  color: #4b5563;
  line-height: 1.8;
}

ul li {
  margin-bottom: 8px;
}

.example {
  white-space: pre-wrap;
  color: #374151;
  line-height: 1.7;
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  margin-top: 12px;
}

@media (max-width: 768px) {
  .prep-container {
    margin: 20px 10px !important;
    padding: 24px 20px !important;
  }
  
  h1 {
    font-size: 24px;
  }
  
  .form-grid {
    grid-template-columns: 1fr;
    gap: 16px;
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
