<template>
  <div class="test-runner-page">
    <h1>{{ $t('tests.title') }}</h1>
    <p class="test-runner-hint">{{ $t('tests.hint') }}</p>

    <div class="test-runner-toolbar">
      <button
        type="button"
        class="test-runner__run-btn"
        :disabled="running"
        @click="runTests(null)"
      >
        {{ running ? $t('tests.running') : $t('tests.runAll') }}
      </button>

      <div class="test-runner__chips">
        <button
          v-for="cat in categories"
          :key="cat"
          type="button"
          class="test-runner__chip"
          :class="{ 'test-runner__chip--active': selectedCategory === cat }"
          @click="toggleCategory(cat)"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <div v-if="running" class="test-runner-progress">
      <div class="test-runner-progress__bar">
        <div
          class="test-runner-progress__fill"
          :style="{ width: progressPct + '%' }"
        />
      </div>
      <span class="test-runner-progress__text">{{ $t('tests.progressText', { pct: progressPct }) }}</span>
    </div>

    <div v-if="results.length" class="test-runner-summary">
      <span class="test-runner-summary__total">{{ $t('tests.total') }}: {{ results.length }}</span>
      <span class="test-runner-summary__passed">{{ $t('tests.passed') }}: {{ passedCount }}</span>
      <span class="test-runner-summary__failed">{{ $t('tests.failed') }}: {{ failedCount }}</span>
      <span class="test-runner-summary__duration">{{ totalDuration }}ms</span>
    </div>

    <div v-if="failedCount > 0" class="test-runner-actions">
      <button
        type="button"
        class="test-runner__copy-btn"
        @click="copyFailedReport"
      >
        {{ copied ? $t('tests.copied') : $t('tests.copyFailed') }}
      </button>
    </div>

    <div v-if="results.length" class="test-runner-results">
      <div
        v-for="cat in resultCategories"
        :key="cat"
        class="test-runner-cat"
      >
        <h3 class="test-runner-cat__title">
          <span class="test-runner-cat__icon">{{ catIcon(cat) }}</span>
          {{ cat }}
          <span class="test-runner-cat__count">
            {{ catPassed(cat) }}/{{ catResults(cat).length }}
          </span>
        </h3>

        <div class="test-runner-cat__list">
          <div
            v-for="(t, i) in catResults(cat)"
            :key="i"
            class="test-runner-item"
            :class="{ 'test-runner-item--fail': !t.passed }"
            @click="toggleExpand(t)"
          >
            <span class="test-runner-item__status">{{ t.passed ? '✅' : '❌' }}</span>
            <span class="test-runner-item__name">{{ t.name }}</span>
            <span class="test-runner-item__ms">{{ t.duration_ms }}ms</span>

            <div v-if="t._expanded && t.detail" class="test-runner-item__detail">
              <pre>{{ t.detail }}</pre>
              <pre v-if="t.traceback" class="test-runner-item__traceback">{{ t.traceback }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="error" class="test-runner-error">
      {{ error }}
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "TestRunner",
  data() {
    return {
      categories: [],
      selectedCategory: null,
      results: [],
      running: false,
      progressPct: 0,
      error: "",
      copied: false,
    };
  },
  computed: {
    passedCount() {
      return this.results.filter((r) => r.passed).length;
    },
    failedCount() {
      return this.results.filter((r) => !r.passed).length;
    },
    totalDuration() {
      return this.results.reduce((s, r) => s + (r.duration_ms || 0), 0);
    },
    resultCategories() {
      const cats = [];
      for (const r of this.results) {
        if (!cats.includes(r.category)) cats.push(r.category);
      }
      return cats;
    },
  },
  async mounted() {
    await this.loadCategories();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem("token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },

    async loadCategories() {
      try {
        const { data } = await axios.get("/api/tests/list", {
          headers: this.authHeaders(),
        });
        this.categories = Object.keys(data.categories || {}).sort();
      } catch (e) {
        this.error = e.response?.data?.error || e.message;
      }
    },

    toggleCategory(cat) {
      this.selectedCategory = this.selectedCategory === cat ? null : cat;
    },

    async runTests(category) {
      this.running = true;
      this.error = "";
      this.results = [];
      this.progressPct = 0;
      this.copied = false;

      const cat = category || this.selectedCategory;
      const url = cat ? `/api/tests/run/${cat}` : "/api/tests/run";

      const fakeProgress = setInterval(() => {
        if (this.progressPct < 90) this.progressPct += 2;
      }, 300);

      try {
        const { data } = await axios.post(url, cat ? undefined : {}, {
          headers: this.authHeaders(),
        });
        this.results = (data.results || []).map((r) => ({
          ...r,
          _expanded: false,
        }));
        this.progressPct = 100;
      } catch (e) {
        this.error = e.response?.data?.error || e.message;
      } finally {
        clearInterval(fakeProgress);
        this.running = false;
      }
    },

    catResults(cat) {
      return this.results.filter((r) => r.category === cat);
    },
    catPassed(cat) {
      return this.catResults(cat).filter((r) => r.passed).length;
    },
    catIcon(cat) {
      const allPassed = this.catResults(cat).every((r) => r.passed);
      return allPassed ? "🟢" : "🔴";
    },
    toggleExpand(t) {
      t._expanded = !t._expanded;
    },

    copyFailedReport() {
      const failed = this.results.filter((r) => !r.passed);
      if (!failed.length) return;

      const now = new Date().toISOString().slice(0, 10);
      let md = `## Failed Tests Report (${now})\n\n`;

      const grouped = {};
      for (const f of failed) {
        if (!grouped[f.category]) grouped[f.category] = [];
        grouped[f.category].push(f);
      }

      for (const [cat, tests] of Object.entries(grouped)) {
        md += `### Category: ${cat}\n`;
        for (const t of tests) {
          md += `- **FAIL**: ${t.name}\n`;
          if (t.detail) md += `  - Detail: ${t.detail}\n`;
          if (t.traceback) md += `  - Traceback:\n\`\`\`\n${t.traceback}\n\`\`\`\n`;
        }
        md += "\n";
      }

      navigator.clipboard.writeText(md).then(() => {
        this.copied = true;
        setTimeout(() => { this.copied = false; }, 3000);
      });
    },
  },
};
</script>

<style scoped>
.test-runner-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 20px 60px;
  font-family: 'Inter', 'SF Pro Display', system-ui, -apple-system, sans-serif;
}

.test-runner-page h1 {
  font-size: 28px;
  font-weight: 700;
  color: rgba(10, 20, 45, 0.9);
  margin: 0 0 6px;
}

.test-runner-hint {
  font-size: 14px;
  color: rgba(10, 20, 45, 0.5);
  margin: 0 0 24px;
  line-height: 1.5;
}

/* Toolbar */
.test-runner-toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
}

.test-runner__run-btn {
  padding: 10px 28px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(145deg, #205aff, #00c2ff);
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s, transform 0.2s;
  flex-shrink: 0;
}

.test-runner__run-btn:hover:not(:disabled) {
  opacity: 0.9;
  transform: translateY(-1px);
}

.test-runner__run-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.test-runner__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.test-runner__chip {
  padding: 5px 14px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.85);
  color: rgba(10, 20, 45, 0.7);
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.15s ease;
}

.test-runner__chip:hover {
  border-color: rgba(32, 90, 255, 0.3);
  background: rgba(32, 90, 255, 0.06);
}

.test-runner__chip--active {
  border-color: rgba(32, 90, 255, 0.5);
  background: rgba(32, 90, 255, 0.1);
  color: #205aff;
  font-weight: 600;
}

/* Progress */
.test-runner-progress {
  margin-bottom: 20px;
}

.test-runner-progress__bar {
  height: 6px;
  background: rgba(10, 20, 45, 0.08);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 6px;
}

.test-runner-progress__fill {
  height: 100%;
  background: linear-gradient(90deg, #205aff, #00c2ff);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.test-runner-progress__text {
  font-size: 12px;
  color: rgba(10, 20, 45, 0.5);
}

/* Summary */
.test-runner-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: center;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 14px;
  margin-bottom: 16px;
  font-size: 14px;
  font-weight: 500;
  color: rgba(10, 20, 45, 0.7);
}

.test-runner-summary__passed {
  color: #16a34a;
}

.test-runner-summary__failed {
  color: #ef4444;
}

.test-runner-summary__duration {
  margin-left: auto;
  font-size: 12px;
  color: rgba(10, 20, 45, 0.4);
}

/* Actions */
.test-runner-actions {
  margin-bottom: 20px;
}

.test-runner__copy-btn {
  padding: 8px 22px;
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.06);
  color: #ef4444;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.test-runner__copy-btn:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.5);
}

/* Results */
.test-runner-cat {
  margin-bottom: 24px;
}

.test-runner-cat__title {
  font-size: 16px;
  font-weight: 600;
  color: rgba(10, 20, 45, 0.85);
  margin: 0 0 10px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.test-runner-cat__count {
  font-size: 13px;
  font-weight: 500;
  color: rgba(10, 20, 45, 0.45);
  margin-left: auto;
}

.test-runner-cat__list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.test-runner-item {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(10, 20, 45, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s ease;
}

.test-runner-item:hover {
  background: rgba(255, 255, 255, 1);
}

.test-runner-item--fail {
  border-color: rgba(239, 68, 68, 0.18);
  background: rgba(239, 68, 68, 0.03);
}

.test-runner-item--fail:hover {
  background: rgba(239, 68, 68, 0.06);
}

.test-runner-item__status {
  flex-shrink: 0;
  font-size: 16px;
  line-height: 1;
}

.test-runner-item__name {
  font-size: 14px;
  color: rgba(10, 20, 45, 0.8);
  flex: 1;
  min-width: 0;
}

.test-runner-item__ms {
  font-size: 12px;
  color: rgba(10, 20, 45, 0.35);
  flex-shrink: 0;
}

.test-runner-item__detail {
  width: 100%;
  margin-top: 8px;
  padding: 10px 12px;
  background: rgba(10, 20, 45, 0.04);
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.5;
  overflow-x: auto;
}

.test-runner-item__detail pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  color: rgba(10, 20, 45, 0.7);
}

.test-runner-item__traceback {
  margin-top: 8px !important;
  color: #ef4444 !important;
  font-size: 11px;
}

/* Error */
.test-runner-error {
  padding: 14px 18px;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.18);
  border-radius: 12px;
  color: #ef4444;
  font-size: 14px;
}

@media (max-width: 768px) {
  .test-runner-page {
    padding: 20px 14px 40px;
  }
  .test-runner-page h1 {
    font-size: 22px;
  }
  .test-runner-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .test-runner__run-btn {
    width: 100%;
  }
  .test-runner-summary {
    flex-direction: column;
    gap: 6px;
  }
  .test-runner-summary__duration {
    margin-left: 0;
  }
}
</style>
