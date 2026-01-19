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
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.subtitle {
  color: #5f6b7a;
  margin-bottom: 16px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

label {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-weight: 600;
  color: #2d3748;
}

label select,
textarea {
  padding: 10px 12px;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
}

.block {
  margin-bottom: 12px;
}

.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 12px 0 20px;
}

.primary {
  background: #3b82f6;
  color: #fff;
  border: none;
  padding: 12px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #c0392b;
}

.results {
  display: grid;
  gap: 16px;
}

section {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 14px 16px;
}

h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #1f2933;
}

ul {
  margin: 0;
  padding-left: 18px;
  color: #334e68;
}

.example {
  white-space: pre-wrap;
  color: #334e68;
  line-height: 1.5;
}
</style>
