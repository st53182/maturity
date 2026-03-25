<template>
  <div class="kata-page">
    <header class="kata-top">
      <div class="kata-top__main">
        <h1 class="kata-title">{{ $t('agileKata.pageTitle') }}</h1>
        <p class="kata-lead">{{ $t('agileKata.pageLead') }}</p>
      </div>
      <div class="kata-top__actions">
        <button type="button" class="kata-btn kata-btn--ghost" @click="learnOpen = !learnOpen">
          {{ learnOpen ? $t('agileKata.hideHelp') : $t('agileKata.showHelp') }}
        </button>
        <button type="button" class="kata-btn kata-btn--ghost" @click="aiOpen = !aiOpen">
          ✨ {{ $t('agileKata.ai.toggle') }}
        </button>
      </div>
    </header>

    <section v-show="learnOpen" class="kata-learn">
      <article class="kata-learn__card">
        <h2>{{ $t('agileKata.learn.whatTitle') }}</h2>
        <p>{{ $t('agileKata.learn.whatP1') }}</p>
        <p>{{ $t('agileKata.learn.whatP2') }}</p>
        <p>{{ $t('agileKata.learn.whatP3') }}</p>
        <p>{{ $t('agileKata.learn.whatP4') }}</p>
      </article>
      <article class="kata-learn__card">
        <h2>{{ $t('agileKata.learn.howTitle') }}</h2>
        <ol>
          <li v-for="n in 5" :key="n">{{ $t('agileKata.learn.step' + n) }}</li>
        </ol>
      </article>
    </section>

    <section class="kata-forms-panel" aria-labelledby="kata-forms-heading">
      <h2 id="kata-forms-heading" class="kata-forms-panel__title">{{ $t('agileKata.formsTitle') }}</h2>
      <p class="kata-forms-panel__hint">{{ $t('agileKata.formsHint') }}</p>
      <div class="kata-forms-grid">
        <button
          v-for="c in canvases"
          :key="c.id"
          type="button"
          class="kata-form-chip"
          :class="{ 'kata-form-chip--active': String(c.id) === selectedId }"
          @click="openCanvasForm(c.id)"
        >
          <span class="kata-form-chip__title">{{ c.title }}</span>
          <span class="kata-form-chip__meta">#{{ c.id }} · {{ formatCanvasDate(c.updated_at) }}</span>
        </button>
      </div>
      <p v-if="!canvases.length && !loading" class="kata-muted">{{ $t('agileKata.formsEmpty') }}</p>
    </section>

    <div class="kata-toolbar">
      <div class="kata-toolbar__row">
        <label class="kata-sr-only" for="kata-canvas-select">{{ $t('agileKata.selectCanvas') }}</label>
        <select
          id="kata-canvas-select"
          v-model="selectedId"
          class="kata-select"
          @change="loadCanvasBySelection"
        >
          <option value="">{{ $t('agileKata.newOrSelect') }}</option>
          <option v-for="c in canvases" :key="'sel-' + c.id" :value="String(c.id)">
            {{ c.title }} · #{{ c.id }}
          </option>
        </select>
        <button type="button" class="kata-btn kata-btn--primary" :disabled="loading" @click="createCanvas">
          {{ $t('agileKata.newCanvas') }}
        </button>
        <button type="button" class="kata-btn" :disabled="!selectedId || loading" @click="saveCanvas">
          {{ saveStatus === 'saving' ? $t('agileKata.saving') : $t('agileKata.save') }}
        </button>
        <button type="button" class="kata-btn kata-btn--danger" :disabled="!selectedId || loading" @click="removeCanvas">
          {{ $t('agileKata.delete') }}
        </button>
        <button type="button" class="kata-btn" :disabled="loading" @click="loadExample">
          {{ $t('agileKata.loadExample') }}
        </button>
      </div>
      <div v-if="selectedId" class="kata-toolbar__title">
        <label class="kata-field-label" for="kata-title-input">{{ $t('agileKata.canvasName') }}</label>
        <input
          id="kata-title-input"
          v-model="canvasTitle"
          type="text"
          class="kata-input kata-input--title"
          @input="scheduleSave"
        />
      </div>
      <p v-if="error" class="kata-error" role="alert">{{ error }}</p>
    </div>

    <div class="kata-layout" :class="{ 'kata-layout--ai': aiOpen }">
      <div class="kata-canvas-wrap">
        <div v-if="gapHint" class="kata-gap" role="status">
          <strong>{{ $t('agileKata.gapTitle') }}</strong>
          {{ gapHint }}
        </div>

        <section class="kata-card kata-card--challenge">
          <h2 class="kata-card__title">{{ $t('agileKata.challenge.title') }}</h2>
          <p class="kata-card__hint">{{ $t('agileKata.challenge.hint') }}</p>
          <label class="kata-field-label">{{ $t('agileKata.challenge.goal') }}</label>
          <textarea v-model="canvas.challenge.goal" class="kata-textarea" rows="2" @input="scheduleSave" />
          <label class="kata-field-label">{{ $t('agileKata.challenge.context') }}</label>
          <textarea v-model="canvas.challenge.businessContext" class="kata-textarea" rows="2" @input="scheduleSave" />
          <label class="kata-field-label">{{ $t('agileKata.challenge.metric') }}</label>
          <textarea v-model="canvas.challenge.metric" class="kata-textarea" rows="2" @input="scheduleSave" />
        </section>

        <div class="kata-columns">
          <section class="kata-card">
            <h2 class="kata-card__title">{{ $t('agileKata.target.title') }}</h2>
            <p class="kata-card__hint">{{ $t('agileKata.target.hint') }}</p>
            <label class="kata-field-label">{{ $t('agileKata.target.outcome') }}</label>
            <textarea v-model="canvas.target.outcome" class="kata-textarea" rows="3" @input="scheduleSave" />
            <label class="kata-field-label">{{ $t('agileKata.target.conditions') }}</label>
            <textarea v-model="canvas.target.conditions" class="kata-textarea" rows="3" @input="scheduleSave" />
          </section>

          <section class="kata-card">
            <h2 class="kata-card__title">{{ $t('agileKata.current.title') }}</h2>
            <p class="kata-card__hint">{{ $t('agileKata.current.hint') }}</p>
            <label class="kata-field-label">{{ $t('agileKata.current.measurable') }}</label>
            <textarea v-model="canvas.current.measurable" class="kata-textarea" rows="3" @input="scheduleSave" />
            <label class="kata-field-label">{{ $t('agileKata.current.facts') }}</label>
            <textarea v-model="canvas.current.facts" class="kata-textarea" rows="4" @input="scheduleSave" />
          </section>

          <section class="kata-card kata-card--experiments">
            <div class="kata-card__head">
              <h2 class="kata-card__title">{{ $t('agileKata.experiments.title') }}</h2>
              <button type="button" class="kata-btn kata-btn--small" @click="addExperiment">{{ $t('agileKata.experiments.add') }}</button>
            </div>
            <p class="kata-card__hint">{{ $t('agileKata.experiments.hint') }}</p>
            <div
              v-for="(exp, idx) in canvas.experiments"
              :key="'exp-' + idx"
              class="kata-experiment"
            >
              <div class="kata-experiment__bar">
                <span>{{ $t('agileKata.experiments.card') }} {{ idx + 1 }}</span>
                <button type="button" class="kata-icon-btn" :aria-label="$t('agileKata.experiments.remove')" @click="removeExperiment(idx)">✕</button>
              </div>
              <label class="kata-field-label">{{ $t('agileKata.experiments.step') }}</label>
              <textarea v-model="exp.step" class="kata-textarea" rows="2" @input="scheduleSave" />
              <label class="kata-field-label">{{ $t('agileKata.experiments.hypothesis') }}</label>
              <textarea v-model="exp.hypothesis" class="kata-textarea" rows="2" @input="scheduleSave" />
              <label class="kata-field-label">{{ $t('agileKata.experiments.result') }}</label>
              <textarea v-model="exp.result" class="kata-textarea" rows="2" @input="scheduleSave" />
              <label class="kata-field-label">{{ $t('agileKata.experiments.learning') }}</label>
              <textarea v-model="exp.learning" class="kata-textarea" rows="2" @input="scheduleSave" />
              <div class="kata-exp-reflect">
                <label class="kata-check">
                  <input
                    v-model="exp.impactedCurrent"
                    type="checkbox"
                    @change="scheduleSave"
                  />
                  <span>{{ $t('agileKata.experiments.impactedCurrent') }}</span>
                </label>
                <p class="kata-exp-reflect__hint">{{ $t('agileKata.experiments.impactedHint') }}</p>
                <span class="kata-field-label">{{ $t('agileKata.experiments.verdictLabel') }}</span>
                <div class="kata-verdict-row" role="group" :aria-label="$t('agileKata.experiments.verdictLabel')">
                  <button
                    type="button"
                    class="kata-verdict-btn"
                    :class="{ 'kata-verdict-btn--active': !exp.verdict }"
                    @click="setExperimentVerdict(idx, '')"
                  >
                    {{ $t('agileKata.experiments.verdictUnset') }}
                  </button>
                  <button
                    type="button"
                    class="kata-verdict-btn kata-verdict-btn--ok"
                    :class="{ 'kata-verdict-btn--active': exp.verdict === 'worked' }"
                    @click="setExperimentVerdict(idx, 'worked')"
                  >
                    {{ $t('agileKata.experiments.verdictWorked') }}
                  </button>
                  <button
                    type="button"
                    class="kata-verdict-btn kata-verdict-btn--no"
                    :class="{ 'kata-verdict-btn--active': exp.verdict === 'not_worked' }"
                    @click="setExperimentVerdict(idx, 'not_worked')"
                  >
                    {{ $t('agileKata.experiments.verdictFailed') }}
                  </button>
                </div>
              </div>
            </div>
            <p v-if="!canvas.experiments.length" class="kata-muted">{{ $t('agileKata.experiments.empty') }}</p>
          </section>
        </div>

        <section class="kata-card">
          <div class="kata-card__head">
            <h2 class="kata-card__title">{{ $t('agileKata.obstacles.title') }}</h2>
            <button type="button" class="kata-btn kata-btn--small" @click="addObstacle">{{ $t('agileKata.obstacles.add') }}</button>
          </div>
          <p class="kata-card__hint">{{ $t('agileKata.obstacles.hint') }}</p>
          <ul class="kata-obstacles">
            <li v-for="(obs, idx) in canvas.obstacles" :key="'obs-' + idx" class="kata-obstacle-row">
              <input
                v-model="canvas.selectedObstacleIndex"
                type="radio"
                class="kata-obstacle-radio"
                name="kata-current-obstacle"
                :value="idx"
                @change="scheduleSave"
              />
              <input v-model="canvas.obstacles[idx]" type="text" class="kata-input" @input="scheduleSave" />
              <button type="button" class="kata-icon-btn" @click="removeObstacle(idx)">✕</button>
            </li>
          </ul>
        </section>
      </div>

      <aside v-show="aiOpen" class="kata-ai" aria-label="AI mentor">
        <h2 class="kata-ai__title">{{ $t('agileKata.ai.title') }}</h2>
        <p class="kata-ai__lead">{{ $t('agileKata.ai.lead') }}</p>
        <div class="kata-ai-modes" role="tablist">
          <button
            v-for="m in aiModes"
            :key="m.id"
            type="button"
            class="kata-ai-mode"
            :class="{ 'kata-ai-mode--active': aiMode === m.id }"
            @click="aiMode = m.id"
          >
            {{ m.label }}
          </button>
        </div>
        <p class="kata-ai-mode-desc">{{ aiModeDescription }}</p>
        <label class="kata-field-label" for="kata-ai-msg">{{ $t('agileKata.ai.messageLabel') }}</label>
        <textarea
          id="kata-ai-msg"
          v-model="aiUserMessage"
          class="kata-textarea"
          rows="3"
          :placeholder="$t('agileKata.ai.messagePh')"
        />
        <button type="button" class="kata-btn kata-btn--primary kata-ai-run" :disabled="aiLoading" @click="runAi">
          {{ aiLoading ? $t('agileKata.ai.running') : $t('agileKata.ai.run') }}
        </button>
        <div v-if="aiReply" class="kata-ai-reply">
          <h3>{{ $t('agileKata.ai.replyTitle') }}</h3>
          <div class="kata-ai-reply__body">{{ aiReply }}</div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

function emptyCanvas() {
  return {
    challenge: { goal: '', businessContext: '', metric: '' },
    target: { outcome: '', conditions: '' },
    current: { measurable: '', facts: '' },
    experiments: [],
    obstacles: [],
    selectedObstacleIndex: null,
  };
}

export default {
  name: 'AgileKataCanvas',
  data() {
    return {
      loading: false,
      error: '',
      canvases: [],
      selectedId: '',
      canvasTitle: 'Agile Kata',
      canvas: emptyCanvas(),
      saveStatus: 'idle',
      saveTimer: null,
      learnOpen: true,
      aiOpen: true,
      aiMode: 'helper',
      aiUserMessage: '',
      aiReply: '',
      aiLoading: false,
    };
  },
  computed: {
    aiModes() {
      return [
        { id: 'helper', label: this.$t('agileKata.ai.modeHelper') },
        { id: 'mentor', label: this.$t('agileKata.ai.modeMentor') },
        { id: 'coach', label: this.$t('agileKata.ai.modeCoach') },
      ];
    },
    aiModeDescription() {
      const map = {
        helper: this.$t('agileKata.ai.descHelper'),
        mentor: this.$t('agileKata.ai.descMentor'),
        coach: this.$t('agileKata.ai.descCoach'),
      };
      return map[this.aiMode] || '';
    },
    gapHint() {
      const t = (this.canvas.target.outcome || '').trim();
      const c = (this.canvas.current.measurable || '').trim();
      if (t && c) {
        return this.$t('agileKata.gapBody', { target: t, current: c });
      }
      if (t && !c) {
        return this.$t('agileKata.gapNeedCurrent');
      }
      if (!t && c) {
        return this.$t('agileKata.gapNeedTarget');
      }
      return '';
    },
  },
  async mounted() {
    await this.refreshList();
  },
  beforeUnmount() {
    if (this.saveTimer) {
      clearTimeout(this.saveTimer);
    }
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem('token');
      return { Authorization: `Bearer ${token}` };
    },
    async refreshList() {
      this.loading = true;
      this.error = '';
      try {
        const { data } = await axios.get('/api/agile-kata', { headers: this.authHeaders() });
        this.canvases = data;
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorLoad');
      } finally {
        this.loading = false;
      }
    },
    applyCanvasState(state, title) {
      const base = emptyCanvas();
      if (!state || typeof state !== 'object') {
        this.canvas = base;
        return;
      }
      this.canvas = {
        challenge: { ...base.challenge, ...(state.challenge || {}) },
        target: { ...base.target, ...(state.target || {}) },
        current: { ...base.current, ...(state.current || {}) },
        experiments: Array.isArray(state.experiments)
          ? state.experiments.map((x) => ({
              step: x.step || '',
              hypothesis: x.hypothesis || '',
              result: x.result || '',
              learning: x.learning || '',
              impactedCurrent: !!x.impactedCurrent,
              verdict: ['worked', 'not_worked'].includes(x.verdict) ? x.verdict : '',
            }))
          : [],
        obstacles: Array.isArray(state.obstacles) ? [...state.obstacles] : [],
        selectedObstacleIndex:
          state.selectedObstacleIndex === null || state.selectedObstacleIndex === undefined
            ? null
            : Number(state.selectedObstacleIndex),
      };
      if (title) {
        this.canvasTitle = title;
      }
    },
    formatCanvasDate(iso) {
      if (!iso) {
        return '—';
      }
      try {
        const d = new Date(iso);
        if (Number.isNaN(d.getTime())) {
          return '—';
        }
        return d.toLocaleString(this.$i18n.locale === 'en' ? 'en-GB' : 'ru-RU', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        });
      } catch {
        return '—';
      }
    },
    openCanvasForm(id) {
      this.selectedId = String(id);
      this.loadCanvasBySelection();
    },
    async loadCanvasBySelection() {
      if (!this.selectedId) {
        this.applyCanvasState(emptyCanvas());
        this.canvasTitle = this.$t('agileKata.defaultTitle');
        return;
      }
      this.loading = true;
      this.error = '';
      try {
        const { data } = await axios.get(`/api/agile-kata/${this.selectedId}`, {
          headers: this.authHeaders(),
        });
        this.applyCanvasState(data.canvas_state, data.title);
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorLoad');
      } finally {
        this.loading = false;
      }
    },
    async createCanvas() {
      this.loading = true;
      this.error = '';
      try {
        const nextNum = (this.canvases && this.canvases.length) ? this.canvases.length + 1 : 1;
        const { data } = await axios.post(
          '/api/agile-kata',
          {
            title: this.$t('agileKata.newFormTitle', { n: nextNum }),
            canvas_state: emptyCanvas(),
          },
          { headers: this.authHeaders() }
        );
        await this.refreshList();
        this.selectedId = String(data.id);
        this.applyCanvasState(data.canvas_state, data.title);
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorSave');
      } finally {
        this.loading = false;
      }
    },
    scheduleSave() {
      if (!this.selectedId) {
        return;
      }
      if (this.saveTimer) {
        clearTimeout(this.saveTimer);
      }
      this.saveTimer = setTimeout(() => this.saveCanvas(), 800);
    },
    async saveCanvas() {
      if (!this.selectedId) {
        return;
      }
      this.saveStatus = 'saving';
      this.error = '';
      try {
        await axios.put(
          `/api/agile-kata/${this.selectedId}`,
          { title: this.canvasTitle, canvas_state: this.canvas },
          { headers: this.authHeaders() }
        );
        await this.refreshList();
        this.saveStatus = 'saved';
        setTimeout(() => {
          if (this.saveStatus === 'saved') {
            this.saveStatus = 'idle';
          }
        }, 1500);
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorSave');
        this.saveStatus = 'idle';
      }
    },
    async removeCanvas() {
      if (!this.selectedId || !confirm(this.$t('agileKata.confirmDelete'))) {
        return;
      }
      try {
        await axios.delete(`/api/agile-kata/${this.selectedId}`, { headers: this.authHeaders() });
        this.selectedId = '';
        this.applyCanvasState(emptyCanvas());
        await this.refreshList();
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorSave');
      }
    },
    async loadExample() {
      try {
        const { data } = await axios.get('/api/agile-kata/example');
        if (!this.selectedId) {
          await this.createCanvas();
        }
        if (!this.selectedId) {
          return;
        }
        this.applyCanvasState(data);
        this.canvasTitle = this.$t('agileKata.exampleTitle');
        await this.saveCanvas();
      } catch (e) {
        this.error = this.$t('agileKata.errorExample');
      }
    },
    addExperiment() {
      this.canvas.experiments.push({
        step: '',
        hypothesis: '',
        result: '',
        learning: '',
        impactedCurrent: false,
        verdict: '',
      });
      this.scheduleSave();
    },
    setExperimentVerdict(index, value) {
      const exp = this.canvas.experiments[index];
      if (!exp) {
        return;
      }
      exp.verdict = value;
      this.scheduleSave();
    },
    removeExperiment(i) {
      this.canvas.experiments.splice(i, 1);
      this.scheduleSave();
    },
    addObstacle() {
      this.canvas.obstacles.push('');
      this.scheduleSave();
    },
    removeObstacle(i) {
      this.canvas.obstacles.splice(i, 1);
      if (this.canvas.selectedObstacleIndex === i) {
        this.canvas.selectedObstacleIndex = null;
      } else if (this.canvas.selectedObstacleIndex > i) {
        this.canvas.selectedObstacleIndex -= 1;
      }
      this.scheduleSave();
    },
    async runAi() {
      this.aiLoading = true;
      this.aiReply = '';
      this.error = '';
      try {
        const locale = (this.$i18n.locale || 'ru').toString();
        const { data } = await axios.post(
          '/api/agile-kata/ai',
          {
            mode: this.aiMode,
            locale,
            canvas_state: this.canvas,
            user_message: this.aiUserMessage,
          },
          { headers: this.authHeaders() }
        );
        this.aiReply = data.reply || '';
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileKata.errorAi');
      } finally {
        this.aiLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.kata-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px 20px 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
  color: #0f172a;
}

.kata-top {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.kata-title {
  margin: 0 0 8px;
  font-size: 1.75rem;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.kata-lead {
  margin: 0;
  color: #64748b;
  max-width: 640px;
  line-height: 1.55;
  font-size: 15px;
}

.kata-forms-panel {
  margin-bottom: 24px;
  padding: 18px 20px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
}

.kata-forms-panel__title {
  margin: 0 0 8px;
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
}

.kata-forms-panel__hint {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
}

.kata-forms-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.kata-form-chip {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 4px;
  padding: 12px 14px;
  min-width: 160px;
  max-width: 280px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: border-color 0.15s ease, box-shadow 0.15s ease;
}

.kata-form-chip:hover {
  border-color: #c7d2fe;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.12);
}

.kata-form-chip--active {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  box-shadow: 0 2px 10px rgba(99, 102, 241, 0.2);
}

.kata-form-chip__title {
  font-size: 14px;
  font-weight: 700;
  color: #1e293b;
  overflow-wrap: anywhere;
}

.kata-form-chip__meta {
  font-size: 11px;
  color: #64748b;
}

.kata-check {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin: 12px 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: #334155;
  cursor: pointer;
}

.kata-check input {
  margin-top: 3px;
  width: 18px;
  height: 18px;
  accent-color: #6366f1;
  flex-shrink: 0;
}

.kata-exp-reflect {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #cbd5e1;
}

.kata-exp-reflect__hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.45;
}

.kata-verdict-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}

.kata-verdict-btn {
  padding: 8px 14px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  font-family: inherit;
}

.kata-verdict-btn:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.kata-verdict-btn--active {
  border-color: #6366f1;
  background: #eef2ff;
  color: #3730a3;
}

.kata-verdict-btn--ok.kata-verdict-btn--active {
  border-color: #22c55e;
  background: #ecfdf5;
  color: #166534;
}

.kata-verdict-btn--no.kata-verdict-btn--active {
  border-color: #f87171;
  background: #fef2f2;
  color: #991b1b;
}

.kata-top__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.kata-learn {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.kata-learn__card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 18px 20px;
  font-size: 14px;
  line-height: 1.55;
  color: #334155;
}

.kata-learn__card h2 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
}

.kata-learn__card ol {
  margin: 0;
  padding-left: 1.2rem;
}

.kata-toolbar {
  margin-bottom: 20px;
}

.kata-toolbar__row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.kata-toolbar__title {
  margin-top: 14px;
}

.kata-select {
  min-width: 200px;
  padding: 10px 14px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  font-size: 14px;
  background: #fff;
}

.kata-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  background: #fff;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  color: #334155;
}

.kata-btn:hover:not(:disabled) {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.kata-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.kata-btn--primary {
  border-color: #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #3730a3;
}

.kata-btn--ghost {
  background: transparent;
}

.kata-btn--danger {
  border-color: #fecaca;
  color: #b91c1c;
}

.kata-btn--small {
  padding: 6px 12px;
  font-size: 12px;
}

.kata-input {
  width: 100%;
  padding: 10px 12px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  font-size: 14px;
  box-sizing: border-box;
}

.kata-input--title {
  max-width: 420px;
}

.kata-input:focus,
.kata-textarea:focus,
.kata-select:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.kata-textarea {
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  box-sizing: border-box;
  font-family: inherit;
  margin-bottom: 12px;
}

.kata-field-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.kata-error {
  color: #dc2626;
  font-size: 14px;
  margin-top: 10px;
}

.kata-layout {
  display: grid;
  gap: 20px;
}

@media (min-width: 1100px) {
  .kata-layout--ai {
    grid-template-columns: 1fr minmax(300px, 360px);
    align-items: start;
  }
}

.kata-gap {
  background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%);
  border: 1px solid #fdba74;
  border-radius: 12px;
  padding: 12px 16px;
  font-size: 14px;
  color: #9a3412;
  margin-bottom: 16px;
  line-height: 1.5;
}

.kata-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px 22px;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
  margin-bottom: 16px;
}

.kata-card--challenge {
  border-top: 4px solid #6366f1;
}

.kata-card__title {
  margin: 0 0 6px;
  font-size: 17px;
  font-weight: 700;
  color: #0f172a;
}

.kata-card__hint {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
}

.kata-card__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}

.kata-columns {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.kata-experiment {
  border: 1px dashed #cbd5e1;
  border-radius: 12px;
  padding: 14px;
  margin-bottom: 12px;
  background: #fafafa;
}

.kata-experiment__bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
  margin-bottom: 10px;
}

.kata-icon-btn {
  border: none;
  background: #f1f5f9;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  cursor: pointer;
  color: #64748b;
  line-height: 1;
}

.kata-icon-btn:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.kata-muted {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.kata-obstacles {
  list-style: none;
  margin: 0;
  padding: 0;
}

.kata-obstacle-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.kata-obstacle-radio {
  flex-shrink: 0;
  width: 18px;
  height: 18px;
  accent-color: #6366f1;
  cursor: pointer;
}

.kata-ai {
  position: sticky;
  top: 16px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 18px;
  max-height: calc(100vh - 32px);
  overflow-y: auto;
}

.kata-ai__title {
  margin: 0 0 6px;
  font-size: 16px;
}

.kata-ai__lead {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
}

.kata-ai-modes {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 10px;
}

.kata-ai-mode {
  text-align: left;
  padding: 10px 12px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  background: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: #475569;
}

.kata-ai-mode--active {
  border-color: #818cf8;
  background: #eef2ff;
  color: #312e81;
}

.kata-ai-mode-desc {
  font-size: 12px;
  color: #64748b;
  line-height: 1.45;
  margin: 0 0 12px;
}

.kata-ai-run {
  width: 100%;
  margin-top: 8px;
}

.kata-ai-reply {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.kata-ai-reply h3 {
  margin: 0 0 8px;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #64748b;
}

.kata-ai-reply__body {
  font-size: 14px;
  line-height: 1.55;
  color: #1e293b;
  white-space: pre-wrap;
}

.kata-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
