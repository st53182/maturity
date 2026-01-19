<template>
  <div class="prep-container">
    <h1>{{ $t('backlogPrep.title') }}</h1>
    <p class="subtitle">{{ $t('backlogPrep.subtitle') }}</p>

    <div class="form-grid">
      <label>
        {{ $t('backlogPrep.workType') }}
        <select v-model="form.workType">
          <option value="story">{{ $t('backlogPrep.story') }}</option>
          <option value="epic">{{ $t('backlogPrep.epic') }}</option>
        </select>
      </label>

      <label>
        {{ $t('backlogPrep.language') }}
        <select v-model="form.language">
          <option value="ru">Русский</option>
          <option value="en">English</option>
        </select>
      </label>
    </div>

    <label class="block">
      {{ $t('backlogPrep.description') }}
      <textarea
        v-model="form.text"
        rows="7"
        :placeholder="$t('backlogPrep.descriptionPlaceholder')"
      ></textarea>
    </label>

    <label class="block">
      {{ $t('backlogPrep.context') }}
      <textarea
        v-model="form.context"
        rows="4"
        :placeholder="$t('backlogPrep.contextPlaceholder')"
      ></textarea>
    </label>

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

label {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

label select,
textarea {
  padding: 12px 16px;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 14px;
  resize: vertical;
  font-family: inherit;
  transition: all 0.2s ease;
  background: #ffffff;
}

label select:focus,
textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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
