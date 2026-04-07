<template>
  <div class="sql-page">
    <button type="button" class="sql-back" @click="$router.push('/qa')">
      ← {{ $t('qa.backToList') }}
    </button>

    <header class="sql-header">
      <h1>{{ $t('qa.sqlPageTitle') }}</h1>
      <p class="sql-lead">{{ $t('qa.sqlPageLead') }}</p>
      <p class="sql-note">{{ $t('qa.sqlBrowserOnly') }}</p>
    </header>

    <div v-if="loadError" class="sql-banner sql-banner--error">{{ loadError }}</div>
    <div v-else-if="loading" class="sql-banner">{{ $t('qa.sqlLoading') }}</div>

    <div v-else class="sql-layout">
      <aside class="sql-lessons" aria-label="Уроки">
        <h2 class="sql-aside-title">{{ $t('qa.sqlLessonsTitle') }}</h2>
        <ul class="sql-lesson-list">
          <li v-for="(lesson, idx) in lessons" :key="lesson.id">
            <button
              type="button"
              class="sql-lesson-tab"
              :class="{ active: activeLesson === idx }"
              @click="activeLesson = idx"
            >
              {{ idx + 1 }}. {{ lesson.title }}
            </button>
          </li>
        </ul>
        <div v-if="currentLesson" class="sql-lesson-body">
          <h3>{{ currentLesson.title }}</h3>
          <p class="sql-theory">{{ currentLesson.theory }}</p>
          <p class="sql-hint-label">{{ $t('qa.sqlHintLabel') }}</p>
          <p class="sql-hint">{{ currentLesson.hint }}</p>
          <button type="button" class="sql-btn-secondary" @click="showHintSql = !showHintSql">
            {{ showHintSql ? $t('qa.sqlHideExample') : $t('qa.sqlShowExample') }}
          </button>
          <pre v-if="showHintSql" class="sql-example">{{ currentLesson.exampleSql }}</pre>
          <button type="button" class="sql-btn-secondary sql-use-example" @click="useExample">
            {{ $t('qa.sqlInsertExample') }}
          </button>
        </div>
      </aside>

      <main class="sql-main">
        <section class="sql-tables" aria-label="Демо-таблицы">
          <h2>{{ $t('qa.sqlDemoTablesTitle') }}</h2>
          <p class="sql-muted">{{ $t('qa.sqlDemoTablesHint') }}</p>
          <div class="sql-tables-grid">
            <div class="sql-table-card">
              <h3>defects <span class="sql-badge">24 × 8</span></h3>
              <div class="sql-table-scroll">
                <table class="sql-data-table">
                  <thead>
                    <tr>
                      <th v-for="c in previewDefects.columns" :key="c">{{ c }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in previewDefects.rows" :key="'d' + ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div class="sql-table-card">
              <h3>test_runs <span class="sql-badge">24 × 8</span></h3>
              <div class="sql-table-scroll">
                <table class="sql-data-table">
                  <thead>
                    <tr>
                      <th v-for="c in previewRuns.columns" :key="c">{{ c }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in previewRuns.rows" :key="'r' + ri">
                      <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        </section>

        <section class="sql-editor-block" aria-label="Редактор SQL">
          <h2>{{ $t('qa.sqlEditorTitle') }}</h2>
          <p class="sql-muted">{{ $t('qa.sqlEditorHint') }}</p>
          <textarea
            v-model="editorSql"
            class="sql-textarea"
            spellcheck="false"
            rows="10"
            :aria-label="$t('qa.sqlEditorTitle')"
          />
          <div class="sql-actions">
            <button type="button" class="sql-btn-primary" :disabled="!db" @click="runSql">
              {{ $t('qa.sqlRun') }}
            </button>
            <button type="button" class="sql-btn-secondary" :disabled="!db" @click="resetDb">
              {{ $t('qa.sqlResetDb') }}
            </button>
          </div>
          <p v-if="runError" class="sql-error">{{ runError }}</p>
          <p v-if="resultMessage && !runError" class="sql-info">{{ resultMessage }}</p>
        </section>

        <section class="sql-result-block" aria-label="Результат">
          <h2>{{ $t('qa.sqlResultTitle') }}</h2>
          <div v-if="resultColumns.length" class="sql-table-scroll">
            <table class="sql-data-table sql-result-table">
              <thead>
                <tr>
                  <th v-for="c in resultColumns" :key="c">{{ c }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(row, ri) in resultRows" :key="'res' + ri">
                  <td v-for="(cell, ci) in row" :key="ci">{{ cell }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <p v-else-if="!resultMessage && !runError" class="sql-muted">{{ $t('qa.sqlResultEmpty') }}</p>
        </section>

        <p class="sql-footer-link">
          <a href="https://sqlbolt.com/" target="_blank" rel="noopener noreferrer">
            {{ $t('qa.sqlExternalBolt') }}
          </a>
        </p>
      </main>
    </div>
  </div>
</template>

<script>
import { getSeedSQL, SQL_LESSONS, DEFAULT_EDITOR_SQL } from '@/qa/sqlSandbox.js';

function execToGrid(db, sql) {
  const results = db.exec(sql);
  if (!results || !results.length) {
    return { columns: [], rows: [] };
  }
  const first = results[0];
  return {
    columns: first.columns || [],
    rows: first.values || [],
  };
}

export default {
  name: 'QASqlPractice',
  data() {
    return {
      loading: true,
      loadError: null,
      db: null,
      lessons: SQL_LESSONS,
      activeLesson: 0,
      showHintSql: false,
      editorSql: DEFAULT_EDITOR_SQL,
      previewDefects: { columns: [], rows: [] },
      previewRuns: { columns: [], rows: [] },
      runError: null,
      resultMessage: '',
      resultColumns: [],
      resultRows: [],
    };
  },
  computed: {
    currentLesson() {
      return this.lessons[this.activeLesson] || null;
    },
  },
  async mounted() {
    await this.initDb();
  },
  methods: {
    async initDb() {
      this.loading = true;
      this.loadError = null;
      this.db = null;
      try {
        const base = process.env.BASE_URL || '/';
        const initSqlJs = (await import('sql.js')).default;
        const SQL = await initSqlJs({
          locateFile: (file) => `${base}${file}`,
        });
        const database = new SQL.Database();
        database.run(getSeedSQL());
        this.db = database;
        this.refreshPreviews();
        this.runError = null;
        this.resultMessage = '';
        this.resultColumns = [];
        this.resultRows = [];
      } catch (e) {
        this.loadError = e.message || String(e);
      } finally {
        this.loading = false;
      }
    },
    refreshPreviews() {
      if (!this.db) return;
      this.previewDefects = execToGrid(this.db, 'SELECT * FROM defects ORDER BY id');
      this.previewRuns = execToGrid(this.db, 'SELECT * FROM test_runs ORDER BY id');
    },
    async resetDb() {
      if (this.db) {
        try {
          this.db.close();
        } catch (_) {
          /* ignore */
        }
        this.db = null;
      }
      await this.initDb();
    },
    runSql() {
      this.runError = null;
      this.resultMessage = '';
      this.resultColumns = [];
      this.resultRows = [];
      const sql = (this.editorSql || '').trim();
      if (!sql) {
        this.runError = this.$t('qa.sqlEmptyQuery');
        return;
      }
      if (!this.db) return;
      try {
        const results = this.db.exec(sql);
        if (!results || results.length === 0) {
          this.resultMessage = this.$t('qa.sqlNoSelectResult');
          this.refreshPreviews();
          return;
        }
        let last = null;
        for (let i = results.length - 1; i >= 0; i--) {
          const block = results[i];
          if (block.columns && block.columns.length) {
            last = block;
            break;
          }
        }
        if (!last) {
          this.resultMessage = this.$t('qa.sqlNoSelectResult');
        } else {
          this.resultColumns = last.columns;
          this.resultRows = last.values || [];
        }
        this.refreshPreviews();
      } catch (e) {
        this.runError = e.message || String(e);
      }
    },
    useExample() {
      if (this.currentLesson && this.currentLesson.exampleSql) {
        this.editorSql = this.currentLesson.exampleSql.trim();
        this.showHintSql = true;
      }
    },
  },
};
</script>

<style scoped>
.sql-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 1.25rem 1rem 3rem;
  color: #1e1b4b;
}

.sql-back {
  margin-bottom: 1rem;
  padding: 0.35rem 0.75rem;
  border: none;
  background: transparent;
  color: #5b21b6;
  cursor: pointer;
  font-size: 0.95rem;
}

.sql-back:hover {
  text-decoration: underline;
}

.sql-header h1 {
  margin: 0 0 0.5rem;
  font-size: 1.65rem;
}

.sql-lead {
  margin: 0 0 0.5rem;
  color: #4338ca;
  max-width: 52rem;
}

.sql-note {
  margin: 0;
  font-size: 0.9rem;
  color: #64748b;
}

.sql-banner {
  padding: 0.75rem 1rem;
  border-radius: 8px;
  background: #eef2ff;
  margin: 1rem 0;
}

.sql-banner--error {
  background: #fef2f2;
  color: #b91c1c;
}

.sql-layout {
  display: grid;
  grid-template-columns: minmax(260px, 300px) 1fr;
  gap: 1.5rem;
  margin-top: 1.25rem;
  align-items: start;
}

@media (max-width: 960px) {
  .sql-layout {
    grid-template-columns: 1fr;
  }
}

.sql-lessons {
  position: sticky;
  top: 0.5rem;
  background: #fafafa;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 1rem;
}

.sql-aside-title {
  margin: 0 0 0.75rem;
  font-size: 1rem;
}

.sql-lesson-list {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
}

.sql-lesson-tab {
  width: 100%;
  text-align: left;
  padding: 0.45rem 0.5rem;
  margin-bottom: 0.25rem;
  border: 1px solid transparent;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
  font-size: 0.85rem;
  color: #334155;
}

.sql-lesson-tab:hover {
  border-color: #c4b5fd;
}

.sql-lesson-tab.active {
  background: #ede9fe;
  border-color: #8b5cf6;
  font-weight: 600;
}

.sql-lesson-body h3 {
  margin: 0 0 0.5rem;
  font-size: 1rem;
}

.sql-theory,
.sql-hint {
  font-size: 0.88rem;
  line-height: 1.45;
  margin: 0 0 0.5rem;
  color: #475569;
}

.sql-hint-label {
  margin: 0.5rem 0 0.15rem;
  font-size: 0.8rem;
  font-weight: 600;
  color: #7c3aed;
}

.sql-example {
  margin: 0.5rem 0;
  padding: 0.65rem;
  background: #1e293b;
  color: #e2e8f0;
  border-radius: 8px;
  font-size: 0.78rem;
  overflow-x: auto;
  white-space: pre-wrap;
}

.sql-btn-primary,
.sql-btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 8px;
  font-size: 0.9rem;
  cursor: pointer;
  border: none;
  margin-right: 0.5rem;
  margin-top: 0.35rem;
}

.sql-btn-primary {
  background: linear-gradient(135deg, #7c3aed, #5b21b6);
  color: #fff;
}

.sql-btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.sql-btn-secondary {
  background: #fff;
  border: 1px solid #cbd5e1;
  color: #475569;
}

.sql-use-example {
  margin-top: 0.5rem;
}

.sql-main h2 {
  margin: 0 0 0.35rem;
  font-size: 1.15rem;
}

.sql-muted {
  font-size: 0.85rem;
  color: #64748b;
  margin: 0 0 0.75rem;
}

.sql-tables-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 900px) {
  .sql-tables-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.sql-table-card {
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.75rem;
  background: #fff;
}

.sql-table-card h3 {
  margin: 0 0 0.5rem;
  font-size: 0.95rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.sql-badge {
  font-size: 0.7rem;
  font-weight: 600;
  background: #ede9fe;
  color: #5b21b6;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
}

.sql-table-scroll {
  overflow-x: auto;
  max-height: 320px;
  overflow-y: auto;
}

.sql-data-table {
  border-collapse: collapse;
  font-size: 0.72rem;
  min-width: 100%;
}

.sql-data-table th,
.sql-data-table td {
  border: 1px solid #e2e8f0;
  padding: 0.25rem 0.4rem;
  text-align: left;
  white-space: nowrap;
}

.sql-data-table th {
  background: #f1f5f9;
  position: sticky;
  top: 0;
  z-index: 1;
}

.sql-editor-block {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  background: #fafafa;
}

.sql-textarea {
  width: 100%;
  box-sizing: border-box;
  font-family: ui-monospace, Consolas, monospace;
  font-size: 0.85rem;
  padding: 0.75rem;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  resize: vertical;
}

.sql-actions {
  margin-top: 0.5rem;
}

.sql-error {
  color: #b91c1c;
  font-size: 0.88rem;
  margin: 0.5rem 0 0;
}

.sql-info {
  color: #0369a1;
  font-size: 0.88rem;
  margin: 0.5rem 0 0;
}

.sql-result-block {
  margin-top: 1.5rem;
  padding: 1rem;
  border: 1px solid #c4b5fd;
  border-radius: 12px;
  background: #faf5ff;
}

.sql-result-table {
  font-size: 0.8rem;
}

.sql-footer-link {
  margin-top: 1.5rem;
  font-size: 0.85rem;
}

.sql-footer-link a {
  color: #5b21b6;
}
</style>
