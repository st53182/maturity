<template>
  <div class="sql-page">
    <button type="button" class="sql-back" @click="$router.push('/qa')">
      ← {{ $t('qa.backToList') }}
    </button>

    <header class="sql-header">
      <h1>{{ $t('qa.sqlPageTitle') }}</h1>
      <p class="sql-lead">{{ $t('qa.sqlPageLead') }}</p>
      <p class="sql-note">{{ $t('qa.sqlBrowserOnly') }}</p>
      <p class="sql-note sql-note--soft">{{ $t('qa.sqlTasksHint') }}</p>
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
              :class="{ active: activeLesson === idx, done: isLessonComplete(idx) }"
              :style="{ '--sql-lesson-hue': String((idx * 23) % 360) }"
              :aria-current="activeLesson === idx ? 'true' : undefined"
              @click="selectLesson(idx)"
            >
              <span class="sql-lesson-tab-num">{{ idx + 1 }}.</span>
              {{ lesson.title }}
              <span v-if="isLessonComplete(idx)" class="sql-lesson-done" aria-hidden="true">✓</span>
            </button>
          </li>
        </ul>
        <div v-if="currentLesson" class="sql-lesson-body">
          <h3>{{ currentLesson.title }}</h3>
          <p class="sql-theory">{{ currentLesson.theory }}</p>
          <p class="sql-task-progress">
            {{ $t('qa.sqlTaskProgress', { current: activeTaskIndex + 1, total: currentLesson.tasks.length }) }}
          </p>
          <ol class="sql-task-chips">
            <li
              v-for="(t, ti) in currentLesson.tasks"
              :key="t.id"
              class="sql-task-chip"
              :class="{
                current: ti === activeTaskIndex,
                done: completedTasks[t.id],
                pending: !completedTasks[t.id] && ti !== activeTaskIndex,
              }"
            >
              <button type="button" class="sql-task-chip-btn" @click="activeTaskIndex = ti">
                {{ ti + 1 }}
                <span v-if="completedTasks[t.id]" class="sql-chip-check">✓</span>
              </button>
            </li>
          </ol>
          <template v-if="currentTask">
            <p class="sql-hint-label">{{ $t('qa.sqlHintLabel') }}</p>
            <p class="sql-hint">{{ currentTask.hint }}</p>
            <button type="button" class="sql-btn-secondary" @click="showHintSql = !showHintSql">
              {{ showHintSql ? $t('qa.sqlHideExample') : $t('qa.sqlShowExample') }}
            </button>
            <pre v-if="showHintSql" class="sql-example">{{ currentTask.exampleSql }}</pre>
            <button type="button" class="sql-btn-secondary sql-use-example" @click="useExample">
              {{ $t('qa.sqlInsertExample') }}
            </button>
          </template>
        </div>
      </aside>

      <main class="sql-main">
        <div v-if="successFlash" class="sql-banner sql-banner--success" role="status">
          {{ $t('qa.sqlCorrect') }}
        </div>

        <section class="sql-tables" aria-label="Демо-таблицы">
          <h2>{{ $t('qa.sqlDemoTablesTitle') }}</h2>
          <p class="sql-muted">{{ $t('qa.sqlDemoTablesHint') }}</p>
          <div class="sql-tables-grid sql-tables-grid--4">
            <div v-for="prev in tablePreviews" :key="prev.name" class="sql-table-card">
              <h3>
                {{ prev.name }}
                <span class="sql-badge">{{ prev.badge }}</span>
              </h3>
              <div class="sql-table-scroll">
                <table class="sql-data-table">
                  <thead>
                    <tr>
                      <th v-for="c in prev.grid.columns" :key="c">{{ c }}</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, ri) in prev.grid.rows" :key="prev.name + ri">
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
          <div
            v-if="currentLesson && currentTask"
            class="sql-editor-task-above"
          >
            <p class="sql-editor-task-progress">
              {{ $t('qa.sqlTaskProgress', { current: activeTaskIndex + 1, total: currentLesson.tasks.length }) }}
            </p>
            <p class="sql-editor-task-kicker">{{ $t('qa.sqlHintLabel') }}</p>
            <p
              :id="`sql-task-prompt-${currentTask.id}`"
              class="sql-editor-task-body"
            >
              {{ currentTask.hint }}
            </p>
          </div>
          <p class="sql-muted">{{ $t('qa.sqlEditorHint') }}</p>
          <p class="sql-muted sql-auto-hint">{{ $t('qa.sqlAutoRunHint') }}</p>
          <textarea
            v-model="editorSql"
            class="sql-textarea"
            spellcheck="false"
            rows="10"
            :aria-label="$t('qa.sqlEditorTitle')"
            :aria-describedby="currentTask ? `sql-task-prompt-${currentTask.id}` : undefined"
          />
          <div class="sql-actions">
            <button type="button" class="sql-btn-secondary sql-btn-run-now" :disabled="!db" @click="runSqlNow">
              {{ $t('qa.sqlRunNow') }}
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

    <div
      v-if="lessonCompleteOpen"
      class="sql-modal-backdrop"
      role="dialog"
      aria-modal="true"
      :aria-label="$t('qa.sqlLessonDoneTitle')"
      @click.self="lessonCompleteOpen = false"
    >
      <div class="sql-modal">
        <h2 class="sql-modal-title">
          {{ isLastLesson ? $t('qa.sqlCourseCompleteTitle') : $t('qa.sqlLessonDoneTitle') }}
        </h2>
        <p class="sql-modal-text">
          {{ isLastLesson ? $t('qa.sqlCourseCompleteBody') : $t('qa.sqlLessonDoneBody') }}
        </p>
        <div class="sql-modal-actions">
          <button
            v-if="!isLastLesson"
            type="button"
            class="sql-btn-primary"
            @click="goNextLesson"
          >
            {{ $t('qa.sqlNextLesson') }}
          </button>
          <button type="button" class="sql-btn-secondary" @click="lessonCompleteOpen = false">
            {{ isLastLesson ? $t('qa.sqlClose') : $t('qa.sqlStayHere') }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getSeedSQL,
  SQL_LESSONS,
  validateTaskWithCtor,
  SQL_PROGRESS_STORAGE_KEY,
} from '@/qa/sqlSandbox.js';

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
      sqlFactory: null,
      seedBytes: null,
      lessons: SQL_LESSONS,
      activeLesson: 0,
      activeTaskIndex: 0,
      completedTasks: {},
      showHintSql: false,
      editorSql: '',
      previewCustomers: { columns: [], rows: [] },
      previewProducts: { columns: [], rows: [] },
      previewOrders: { columns: [], rows: [] },
      previewOrderItems: { columns: [], rows: [] },
      runError: null,
      resultMessage: '',
      resultColumns: [],
      resultRows: [],
      successFlash: false,
      lessonCompleteOpen: false,
      advanceTimer: null,
      debounceTimer: null,
      suppressAutoRun: false,
    };
  },
  computed: {
    currentLesson() {
      return this.lessons[this.activeLesson] || null;
    },
    currentTask() {
      const L = this.currentLesson;
      if (!L || !L.tasks) return null;
      return L.tasks[this.activeTaskIndex] || null;
    },
    tablePreviews() {
      const fmt = (name, grid) => {
        const r = grid.rows?.length ?? 0;
        const c = grid.columns?.length ?? 0;
        return { name, grid, badge: `${r} × ${c}` };
      };
      return [
        fmt('customers', this.previewCustomers),
        fmt('products', this.previewProducts),
        fmt('orders', this.previewOrders),
        fmt('order_items', this.previewOrderItems),
      ];
    },
    isLastLesson() {
      return this.activeLesson >= this.lessons.length - 1;
    },
  },
  watch: {
    activeLesson() {
      this.showHintSql = false;
      this.syncEditorForTask();
    },
    activeTaskIndex() {
      this.showHintSql = false;
      this.syncEditorForTask();
    },
    editorSql() {
      if (this.suppressAutoRun || this.loading || !this.db) return;
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = null;
      }
      this.debounceTimer = setTimeout(() => {
        this.debounceTimer = null;
        this.runSqlCore({ manual: false });
      }, 480);
    },
  },
  mounted() {
    this.loadProgress();
    this.syncFirstIncompleteInLesson();
    this.syncEditorForTask();
    this.initDb();
  },
  beforeUnmount() {
    if (this.advanceTimer) {
      clearTimeout(this.advanceTimer);
      this.advanceTimer = null;
    }
    if (this.debounceTimer) {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = null;
    }
  },
  methods: {
    loadProgress() {
      try {
        const raw = localStorage.getItem(SQL_PROGRESS_STORAGE_KEY);
        if (!raw) return;
        const data = JSON.parse(raw);
        if (data && typeof data.completed === 'object') {
          this.completedTasks = { ...data.completed };
        }
      } catch (_) {
        /* ignore */
      }
    },
    saveProgress() {
      try {
        localStorage.setItem(
          SQL_PROGRESS_STORAGE_KEY,
          JSON.stringify({ completed: this.completedTasks }),
        );
      } catch (_) {
        /* ignore */
      }
    },
    isLessonComplete(lessonIdx) {
      const L = this.lessons[lessonIdx];
      if (!L) return false;
      return L.tasks.every((t) => this.completedTasks[t.id]);
    },
    selectLesson(idx) {
      this.activeLesson = idx;
      this.lessonCompleteOpen = false;
      this.firstIncompleteInCurrentLesson();
    },
    firstIncompleteInCurrentLesson() {
      const L = this.currentLesson;
      if (!L) return;
      const i = L.tasks.findIndex((t) => !this.completedTasks[t.id]);
      this.activeTaskIndex = i === -1 ? 0 : i;
    },
    syncFirstIncompleteInLesson() {
      this.firstIncompleteInCurrentLesson();
    },
    syncEditorForTask() {
      this.suppressAutoRun = true;
      this.editorSql = '';
      this.$nextTick(() => {
        this.suppressAutoRun = false;
      });
    },
    async initDb() {
      this.loading = true;
      this.loadError = null;
      try {
        if (this.db) {
          try {
            this.db.close();
          } catch (_) {
            /* ignore */
          }
          this.db = null;
        }
        const initSqlJs = (await import('sql.js')).default;
        const baseNorm = (process.env.BASE_URL || '/').replace(/\/?$/, '/');
        const localWasmUrl = new URL('sql-wasm.wasm', window.location.origin + baseNorm).href;
        const sqlJsCdnBase = 'https://cdn.jsdelivr.net/npm/sql.js@1.14.1/dist/';

        const looksLikeWasm = (buf) => {
          if (!buf || buf.byteLength < 4) return false;
          const u = new Uint8Array(buf);
          return u[0] === 0x00 && u[1] === 0x61 && u[2] === 0x73 && u[3] === 0x6d;
        };

        let SQL;
        const localResp = await fetch(localWasmUrl);
        if (localResp.ok) {
          const wasmBuf = await localResp.arrayBuffer();
          if (looksLikeWasm(wasmBuf)) {
            SQL = await initSqlJs({ wasmBinary: wasmBuf });
          }
        }
        if (!SQL) {
          SQL = await initSqlJs({
            locateFile: (file) => `${sqlJsCdnBase}${file}`,
          });
        }
        this.sqlFactory = SQL;

        const database = new SQL.Database();
        database.run(getSeedSQL());
        this.seedBytes = database.export();
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
    restoreDbFromSeed() {
      if (!this.sqlFactory || !this.seedBytes) return;
      try {
        if (this.db) {
          try {
            this.db.close();
          } catch (_) {
            /* ignore */
          }
        }
        this.db = new this.sqlFactory.Database(new Uint8Array(this.seedBytes));
        this.refreshPreviews();
      } catch (e) {
        this.runError = e.message || String(e);
      }
    },
    refreshPreviews() {
      if (!this.db) return;
      this.previewCustomers = execToGrid(this.db, 'SELECT * FROM customers ORDER BY id');
      this.previewProducts = execToGrid(this.db, 'SELECT * FROM products ORDER BY id');
      this.previewOrders = execToGrid(this.db, 'SELECT * FROM orders ORDER BY id');
      this.previewOrderItems = execToGrid(this.db, 'SELECT * FROM order_items ORDER BY id');
    },
    async resetDb() {
      await this.initDb();
    },
    runSqlNow() {
      if (this.debounceTimer) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = null;
      }
      this.runSqlCore({ manual: true });
    },
    /** @param {{ manual: boolean }} opts manual: кнопка «сейчас»; иначе автозапуск после паузы */
    runSqlCore(opts) {
      const manual = opts && opts.manual;
      this.runError = null;
      this.resultMessage = '';
      this.resultColumns = [];
      this.resultRows = [];
      this.successFlash = false;
      if (this.advanceTimer) {
        clearTimeout(this.advanceTimer);
        this.advanceTimer = null;
      }

      const sql = (this.editorSql || '').trim();
      if (!sql) {
        if (manual) {
          this.runError = this.$t('qa.sqlEmptyQuery');
        } else {
          this.runError = null;
          this.resultMessage = '';
          this.resultColumns = [];
          this.resultRows = [];
        }
        return;
      }
      if (!this.db || !this.sqlFactory || !this.seedBytes) return;

      const task = this.currentTask;
      const taskGraded = task && task.checkSql && !this.completedTasks[task.id];

      if (task && task.checkSql && this.completedTasks[task.id]) {
        this.runExploratorySql(sql);
        return;
      }

      if (taskGraded) {
        const v = validateTaskWithCtor(this.sqlFactory, this.seedBytes, sql, task.checkSql);
        if (!v.ok) {
          if (v.userError) {
            this.runError = v.userError;
            return;
          }
          if (v.messageKey) {
            this.runError = this.$t(v.messageKey);
            return;
          }
          this.runError = this.$t('qa.sqlWrongResult');
          return;
        }

        this.completedTasks = { ...this.completedTasks, [task.id]: true };
        this.saveProgress();
        this.successFlash = true;
        setTimeout(() => {
          this.successFlash = false;
        }, 1200);

        this.restoreDbFromSeed();
        try {
          const results = this.db.exec(sql);
          if (results && results.length) {
            let last = null;
            for (let i = results.length - 1; i >= 0; i--) {
              const block = results[i];
              if (block.columns && block.columns.length) {
                last = block;
                break;
              }
            }
            if (last) {
              this.resultColumns = last.columns;
              this.resultRows = last.values || [];
            } else {
              this.resultMessage = this.$t('qa.sqlNoSelectResult');
            }
          } else {
            this.resultMessage = this.$t('qa.sqlNoSelectResult');
          }
        } catch (e) {
          this.runError = e.message || String(e);
          return;
        }

        const L = this.currentLesson;
        const lastIdx = L ? L.tasks.length - 1 : 0;
        if (this.activeTaskIndex >= lastIdx) {
          this.lessonCompleteOpen = true;
        } else {
          this.advanceTimer = setTimeout(() => {
            this.activeTaskIndex += 1;
            this.advanceTimer = null;
          }, 750);
        }
        return;
      }

      this.runExploratorySql(sql);
    },
    runExploratorySql(sql) {
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
    goNextLesson() {
      this.lessonCompleteOpen = false;
      if (this.activeLesson < this.lessons.length - 1) {
        this.activeLesson += 1;
        this.firstIncompleteInCurrentLesson();
      }
    },
    useExample() {
      if (this.currentTask && this.currentTask.exampleSql) {
        this.editorSql = this.currentTask.exampleSql.trim();
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

.sql-note--soft {
  margin-top: 0.35rem;
  font-size: 0.85rem;
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

.sql-banner--success {
  background: #ecfdf5;
  color: #047857;
  font-weight: 600;
}

.sql-layout {
  display: grid;
  grid-template-columns: minmax(280px, 320px) 1fr;
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
  padding: 0.55rem 0.65rem;
  margin-bottom: 0.35rem;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.82rem;
  line-height: 1.35;
  color: #f8fafc;
  display: flex;
  align-items: flex-start;
  gap: 0.35rem;
  --h: var(--sql-lesson-hue, 250);
  background: linear-gradient(
    145deg,
    hsl(var(--h), 40%, 38%),
    hsl(calc(var(--h) + 16), 44%, 26%)
  );
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.2);
  transition:
    transform 0.15s ease,
    box-shadow 0.15s ease,
    filter 0.15s ease,
    border-color 0.15s ease;
}

.sql-lesson-tab-num {
  flex-shrink: 0;
  font-weight: 700;
  opacity: 0.95;
}

.sql-lesson-done {
  margin-left: auto;
  color: #86efac;
  font-weight: 700;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.25);
}

.sql-lesson-tab:hover:not(.active) {
  filter: brightness(1.09);
  border-color: rgba(255, 255, 255, 0.28);
}

.sql-lesson-tab:focus-visible {
  outline: 2px solid #fbbf24;
  outline-offset: 2px;
}

/* Текущий урок: контрастный «якорь», не зависит от --sql-lesson-hue */
.sql-lesson-tab.active {
  color: #1c1917;
  border-color: rgba(180, 83, 9, 0.55);
  font-weight: 800;
  background: linear-gradient(145deg, #fde68a, #f59e0b);
  box-shadow:
    0 0 0 3px rgba(251, 191, 36, 0.65),
    0 10px 24px rgba(245, 158, 11, 0.35);
  transform: translateX(5px);
}

.sql-lesson-tab.active .sql-lesson-done {
  color: #047857;
  text-shadow: none;
}

.sql-lesson-tab.done:not(.active) {
  box-shadow:
    inset 3px 0 0 0 #34d399,
    0 2px 8px rgba(15, 23, 42, 0.2);
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

.sql-task-progress {
  font-size: 0.8rem;
  font-weight: 600;
  color: #5b21b6;
  margin: 0.5rem 0 0.35rem;
}

.sql-task-chips {
  list-style: none;
  margin: 0 0 0.75rem;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}

.sql-task-chip-btn {
  width: 2.15rem;
  height: 2.15rem;
  border-radius: 10px;
  border: 2px solid #cbd5e1;
  background: #f1f5f9 !important;
  color: #475569 !important;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  transition:
    background 0.15s ease,
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    color 0.15s ease;
}

.sql-task-chip.pending .sql-task-chip-btn:hover {
  border-color: #94a3b8;
  background: #e2e8f0 !important;
}

/* Текущее задание: фиолетовый акцент */
.sql-task-chip.current .sql-task-chip-btn {
  border-color: #7c3aed !important;
  background: linear-gradient(145deg, #ede9fe, #ddd6fe) !important;
  color: #5b21b6 !important;
  font-weight: 800;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.35);
}

/* Выполнено: зелёный, явно отличается от ожидающих */
.sql-task-chip.done .sql-task-chip-btn {
  border-color: #059669 !important;
  background: linear-gradient(145deg, #34d399, #059669) !important;
  color: #fff !important;
  font-weight: 800;
}

/* Вернулись на уже сделанный шаг: зелёный + фиолетовое кольцо «вы здесь» */
.sql-task-chip.done.current .sql-task-chip-btn {
  background: linear-gradient(145deg, #10b981, #047857) !important;
  color: #fff !important;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.55);
}

.sql-chip-check {
  position: absolute;
  top: -0.35rem;
  right: -0.35rem;
  font-size: 0.6rem;
  line-height: 1;
  padding: 0.1rem 0.2rem;
  border-radius: 4px;
  background: #fff;
  color: #047857;
  font-weight: 800;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.12);
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

.sql-auto-hint {
  margin-top: -0.35rem;
  font-size: 0.8rem;
  color: #7c3aed;
}

.sql-btn-run-now {
  font-weight: 600;
}

.sql-tables-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 700px) {
  .sql-tables-grid--4 {
    grid-template-columns: 1fr 1fr;
  }
}

@media (min-width: 1100px) {
  .sql-tables-grid--4 {
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
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
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
  max-height: 220px;
  overflow-y: auto;
}

.sql-data-table {
  border-collapse: collapse;
  font-size: 0.68rem;
  min-width: 100%;
}

.sql-data-table th,
.sql-data-table td {
  border: 1px solid #e2e8f0;
  padding: 0.2rem 0.35rem;
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

.sql-editor-task-above {
  margin: 0.75rem 0 1rem;
  padding: 0.85rem 1rem;
  border-radius: 10px;
  border: 1px solid #c4b5fd;
  background: linear-gradient(180deg, #f5f3ff 0%, #ede9fe 100%);
}

.sql-editor-task-above .sql-editor-task-progress {
  margin: 0 0 0.35rem;
  font-size: 0.82rem;
  font-weight: 700;
  color: #6d28d9;
}

.sql-editor-task-kicker {
  margin: 0 0 0.25rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #7c3aed;
}

.sql-editor-task-body {
  margin: 0;
  font-size: 0.95rem;
  line-height: 1.5;
  color: #1e1b4b;
  font-weight: 500;
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
  font-size: 0.78rem;
}

.sql-footer-link {
  margin-top: 1.5rem;
  font-size: 0.85rem;
}

.sql-footer-link a {
  color: #5b21b6;
}

.sql-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 1rem;
}

.sql-modal {
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
}

.sql-modal-title {
  margin: 0 0 0.75rem;
  font-size: 1.2rem;
  color: #1e1b4b;
}

.sql-modal-text {
  margin: 0 0 1.25rem;
  font-size: 0.95rem;
  color: #475569;
  line-height: 1.5;
}

.sql-modal-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
</style>
