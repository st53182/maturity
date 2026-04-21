<template>
  <div class="sb-page">
    <div class="sb-page__bg" aria-hidden="true">
      <div class="sb-page__orb sb-page__orb--1" />
      <div class="sb-page__orb sb-page__orb--2" />
    </div>

    <NewToolShell :title="$t('strategyBuilder.title')" :subtitle="$t('strategyBuilder.subtitle')">
      <section class="sb-intro">
        <p class="sb-intro__lead">{{ $t('strategyBuilder.lead') }}</p>
        <ul class="sb-intro__bullets">
          <li>{{ $t('strategyBuilder.bullet1') }}</li>
          <li>{{ $t('strategyBuilder.bullet2') }}</li>
          <li>{{ $t('strategyBuilder.bullet3') }}</li>
        </ul>
      </section>

      <section class="sb-toolbar">
        <div class="sb-scope">
          <label class="sb-field__label">{{ $t('strategyBuilder.scopeLabel') }}</label>
          <div class="sb-scope__tabs">
            <button
              v-for="s in scopeOptions"
              :key="s.id"
              type="button"
              class="sb-scope__tab"
              :class="{ 'sb-scope__tab--on': scope === s.id }"
              @click="scope = s.id"
            >
              {{ s.label }}
            </button>
          </div>
        </div>
        <div class="sb-actions">
          <button type="button" class="sb-btn sb-btn--ghost" @click="loadExample">
            {{ $t('strategyBuilder.loadExample') }}
          </button>
          <button type="button" class="sb-btn sb-btn--primary" :disabled="aiLoading.all" @click="runAi('all')">
            <span v-if="!aiLoading.all">{{ $t('strategyBuilder.aiAll') }}</span>
            <span v-else>{{ $t('strategyBuilder.aiThinking') }}</span>
          </button>
        </div>
      </section>

      <p v-if="aiError" class="sb-error">{{ aiError }}</p>

      <section class="sb-grid">
        <article class="sb-card">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.vision.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.vision" @click="runAi('vision')">
              <span v-if="!aiLoading.vision">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.vision.hint') }}</p>
          <textarea v-model="form.vision" class="sb-textarea" rows="3" :placeholder="$t('strategyBuilder.vision.placeholder')" />
        </article>

        <article class="sb-card">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.mission.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.mission" @click="runAi('mission')">
              <span v-if="!aiLoading.mission">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.mission.hint') }}</p>
          <textarea v-model="form.mission" class="sb-textarea" rows="3" :placeholder="$t('strategyBuilder.mission.placeholder')" />
        </article>

        <article class="sb-card">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.purpose.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.purpose" @click="runAi('purpose')">
              <span v-if="!aiLoading.purpose">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.purpose.hint') }}</p>
          <textarea v-model="form.purpose" class="sb-textarea" rows="3" :placeholder="$t('strategyBuilder.purpose.placeholder')" />
        </article>

        <article class="sb-card">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.values.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.values" @click="runAi('values')">
              <span v-if="!aiLoading.values">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.values.hint') }}</p>
          <div class="sb-chips">
            <span v-for="(v, idx) in form.values" :key="`v-${idx}`" class="sb-chip">
              <input v-model="form.values[idx]" class="sb-chip__input" :placeholder="$t('strategyBuilder.values.placeholder')" />
              <button type="button" class="sb-chip__x" @click="removeValue(idx)" aria-label="remove">×</button>
            </span>
            <button type="button" class="sb-chip sb-chip--add" @click="addValue">
              + {{ $t('strategyBuilder.values.add') }}
            </button>
          </div>
        </article>

        <article class="sb-card sb-card--wide">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.strategy.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.strategy" @click="runAi('strategy')">
              <span v-if="!aiLoading.strategy">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.strategy.hint') }}</p>

          <label class="sb-field__label">{{ $t('strategyBuilder.strategy.horizon') }}</label>
          <input v-model="form.strategy.horizon" class="sb-input" :placeholder="$t('strategyBuilder.strategy.horizonPlaceholder')" />

          <div class="sb-subhead">
            <h4>{{ $t('strategyBuilder.strategy.pillars') }}</h4>
            <button type="button" class="sb-link-btn" @click="addPillar">+ {{ $t('strategyBuilder.add') }}</button>
          </div>
          <div v-for="(p, idx) in form.strategy.pillars" :key="`p-${idx}`" class="sb-pillar">
            <input v-model="p.name" class="sb-input" :placeholder="$t('strategyBuilder.strategy.pillarName')" />
            <textarea v-model="p.description" class="sb-textarea sb-textarea--tight" rows="2" :placeholder="$t('strategyBuilder.strategy.pillarDesc')" />
            <button type="button" class="sb-row-x" @click="removePillar(idx)" aria-label="remove">×</button>
          </div>

          <div class="sb-subhead">
            <h4>{{ $t('strategyBuilder.strategy.bets') }}</h4>
            <button type="button" class="sb-link-btn" @click="form.strategy.bets.push('')">+ {{ $t('strategyBuilder.add') }}</button>
          </div>
          <div v-for="(b, idx) in form.strategy.bets" :key="`b-${idx}`" class="sb-row">
            <input v-model="form.strategy.bets[idx]" class="sb-input" :placeholder="$t('strategyBuilder.strategy.betPlaceholder')" />
            <button type="button" class="sb-row-x" @click="form.strategy.bets.splice(idx, 1)">×</button>
          </div>

          <div class="sb-subhead">
            <h4>{{ $t('strategyBuilder.strategy.metrics') }}</h4>
            <button type="button" class="sb-link-btn" @click="form.strategy.metrics.push('')">+ {{ $t('strategyBuilder.add') }}</button>
          </div>
          <div v-for="(m, idx) in form.strategy.metrics" :key="`m-${idx}`" class="sb-row">
            <input v-model="form.strategy.metrics[idx]" class="sb-input" :placeholder="$t('strategyBuilder.strategy.metricPlaceholder')" />
            <button type="button" class="sb-row-x" @click="form.strategy.metrics.splice(idx, 1)">×</button>
          </div>
        </article>

        <article class="sb-card sb-card--wide">
          <header class="sb-card__head">
            <h3 class="sb-card__h">{{ $t('strategyBuilder.okrs.title') }}</h3>
            <button class="sb-ai-btn" :disabled="aiLoading.okrs" @click="runAi('okrs')">
              <span v-if="!aiLoading.okrs">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>…</span>
            </button>
          </header>
          <p class="sb-card__hint">{{ $t('strategyBuilder.okrs.hint') }}</p>
          <div v-for="(o, idx) in form.okrs" :key="`o-${idx}`" class="sb-okr">
            <input v-model="o.objective" class="sb-input" :placeholder="$t('strategyBuilder.okrs.objectivePlaceholder')" />
            <div v-for="(kr, krIdx) in o.key_results" :key="`kr-${idx}-${krIdx}`" class="sb-row">
              <input v-model="o.key_results[krIdx]" class="sb-input sb-input--kr" :placeholder="$t('strategyBuilder.okrs.krPlaceholder')" />
              <button type="button" class="sb-row-x" @click="o.key_results.splice(krIdx, 1)">×</button>
            </div>
            <div class="sb-okr__actions">
              <button type="button" class="sb-link-btn" @click="o.key_results.push('')">+ {{ $t('strategyBuilder.okrs.addKr') }}</button>
              <button type="button" class="sb-link-btn sb-link-btn--danger" @click="form.okrs.splice(idx, 1)">{{ $t('strategyBuilder.okrs.removeObjective') }}</button>
            </div>
          </div>
          <button type="button" class="sb-btn sb-btn--ghost" @click="addObjective">+ {{ $t('strategyBuilder.okrs.addObjective') }}</button>
        </article>
      </section>

      <section class="sb-bottom">
        <label class="sb-field__label">{{ $t('strategyBuilder.industryLabel') }}</label>
        <input v-model="industry" class="sb-input" :placeholder="$t('strategyBuilder.industryPlaceholder')" />
      </section>
    </NewToolShell>
  </div>
</template>

<script>
import axios from 'axios';
import NewToolShell from '@/views/NewToolShell.vue';
import { getStrategyExampleRu, getStrategyExampleEn } from '@/data/strategyBuilderExamples.js';

function emptyForm() {
  return {
    vision: '',
    mission: '',
    purpose: '',
    values: ['', '', ''],
    strategy: {
      horizon: '',
      pillars: [{ name: '', description: '' }],
      bets: [''],
      metrics: [''],
    },
    okrs: [{ objective: '', key_results: [''] }],
  };
}

export default {
  name: 'StrategyBuilder',
  components: { NewToolShell },
  data() {
    return {
      scope: 'company',
      industry: '',
      form: emptyForm(),
      aiLoading: { all: false, vision: false, mission: false, purpose: false, values: false, strategy: false, okrs: false },
      aiError: '',
    };
  },
  computed: {
    locale() {
      const loc = this.$i18n.locale;
      const s = typeof loc === 'string' ? loc : loc?.value || 'ru';
      return String(s).toLowerCase().startsWith('en') ? 'en' : 'ru';
    },
    scopeOptions() {
      return [
        { id: 'company', label: this.$t('strategyBuilder.scope.company') },
        { id: 'department', label: this.$t('strategyBuilder.scope.department') },
        { id: 'team', label: this.$t('strategyBuilder.scope.team') },
      ];
    },
  },
  methods: {
    addValue() {
      this.form.values.push('');
    },
    removeValue(i) {
      this.form.values.splice(i, 1);
    },
    addPillar() {
      this.form.strategy.pillars.push({ name: '', description: '' });
    },
    removePillar(i) {
      this.form.strategy.pillars.splice(i, 1);
    },
    addObjective() {
      this.form.okrs.push({ objective: '', key_results: [''] });
    },
    loadExample() {
      const data = this.locale === 'en' ? getStrategyExampleEn(this.scope) : getStrategyExampleRu(this.scope);
      this.industry = data.industry || '';
      this.form.vision = data.vision || '';
      this.form.mission = data.mission || '';
      this.form.purpose = data.purpose || '';
      this.form.values = Array.isArray(data.values) && data.values.length ? [...data.values] : [''];
      this.form.strategy = {
        horizon: data.strategy?.horizon || '',
        pillars: (data.strategy?.pillars || []).map((p) => ({ name: p.name || '', description: p.description || '' })),
        bets: [...(data.strategy?.bets || [])],
        metrics: [...(data.strategy?.metrics || [])],
      };
      if (!this.form.strategy.pillars.length) this.form.strategy.pillars = [{ name: '', description: '' }];
      if (!this.form.strategy.bets.length) this.form.strategy.bets = [''];
      if (!this.form.strategy.metrics.length) this.form.strategy.metrics = [''];
      this.form.okrs = (data.okrs || []).map((o) => ({
        objective: o.objective || '',
        key_results: [...(o.key_results || [''])],
      }));
      if (!this.form.okrs.length) this.form.okrs = [{ objective: '', key_results: [''] }];
    },
    async runAi(section) {
      this.aiError = '';
      this.aiLoading[section] = true;
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post(
          '/api/strategy-builder/ai-suggest',
          {
            section,
            scope: this.scope,
            locale: this.locale,
            industry: this.industry,
            form: this.form,
          },
          { headers: token ? { Authorization: `Bearer ${token}` } : {} },
        );
        this.applyAi(section, data?.data || {});
      } catch (e) {
        this.aiError = e?.response?.data?.error || this.$t('strategyBuilder.aiFailed');
      } finally {
        this.aiLoading[section] = false;
      }
    },
    applyAi(section, data) {
      if (!data || typeof data !== 'object') return;
      if (section === 'all') {
        if (typeof data.vision === 'string') this.form.vision = data.vision;
        if (typeof data.mission === 'string') this.form.mission = data.mission;
        if (typeof data.purpose === 'string') this.form.purpose = data.purpose;
        if (Array.isArray(data.values)) this.form.values = data.values.slice(0, 8);
        if (data.strategy && typeof data.strategy === 'object') this.applyStrategy(data.strategy);
        if (Array.isArray(data.okrs)) this.applyOkrs(data.okrs);
        return;
      }
      if (section === 'vision' && typeof data.vision === 'string') this.form.vision = data.vision;
      if (section === 'mission' && typeof data.mission === 'string') this.form.mission = data.mission;
      if (section === 'purpose' && typeof data.purpose === 'string') this.form.purpose = data.purpose;
      if (section === 'values' && Array.isArray(data.values)) this.form.values = data.values.slice(0, 8);
      if (section === 'strategy' && data.strategy) this.applyStrategy(data.strategy);
      if (section === 'okrs' && Array.isArray(data.okrs)) this.applyOkrs(data.okrs);
    },
    applyStrategy(s) {
      this.form.strategy = {
        horizon: s.horizon || this.form.strategy.horizon || '',
        pillars: (Array.isArray(s.pillars) ? s.pillars : []).map((p) => ({
          name: String(p?.name || ''),
          description: String(p?.description || ''),
        })),
        bets: (Array.isArray(s.bets) ? s.bets : []).map((x) => String(x || '')),
        metrics: (Array.isArray(s.metrics) ? s.metrics : []).map((x) => String(x || '')),
      };
      if (!this.form.strategy.pillars.length) this.form.strategy.pillars = [{ name: '', description: '' }];
      if (!this.form.strategy.bets.length) this.form.strategy.bets = [''];
      if (!this.form.strategy.metrics.length) this.form.strategy.metrics = [''];
    },
    applyOkrs(list) {
      this.form.okrs = list.map((o) => ({
        objective: String(o?.objective || ''),
        key_results: (Array.isArray(o?.key_results) ? o.key_results : []).map((kr) => String(kr || '')),
      }));
      if (!this.form.okrs.length) this.form.okrs = [{ objective: '', key_results: [''] }];
    },
  },
};
</script>

<style scoped>
.sb-page {
  position: relative;
  min-height: calc(100vh - 40px);
}
.sb-page__bg { position: absolute; inset: 0; pointer-events: none; overflow: hidden; z-index: 0; }
.sb-page__orb { position: absolute; width: 540px; height: 540px; border-radius: 50%; filter: blur(60px); opacity: 0.55; }
.sb-page__orb--1 {
  top: -220px; left: -210px;
  background: radial-gradient(circle at 30% 30%, rgba(120, 119, 255, 0.4), transparent 65%);
}
.sb-page__orb--2 {
  bottom: -220px; right: -160px;
  background: radial-gradient(circle at 70% 70%, rgba(0, 194, 255, 0.35), transparent 65%);
}

.sb-intro,
.sb-toolbar,
.sb-card,
.sb-bottom {
  position: relative;
  z-index: 1;
}

.sb-intro {
  background: linear-gradient(160deg, rgba(255, 255, 255, 0.92), rgba(246, 249, 255, 0.78));
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 18px;
  padding: 20px 22px;
  box-shadow: 0 18px 42px rgba(10, 20, 45, 0.08);
}
.sb-intro__lead { margin: 0 0 10px; color: rgba(10, 20, 45, 0.9); line-height: 1.55; }
.sb-intro__bullets { margin: 0; padding-left: 20px; color: rgba(10, 20, 45, 0.78); line-height: 1.55; }

.sb-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-end;
  justify-content: space-between;
  margin: 18px 0;
}
.sb-scope { min-width: 260px; }
.sb-scope__tabs {
  display: inline-flex;
  border: 1px solid rgba(10, 20, 45, 0.12);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.9);
}
.sb-scope__tab {
  padding: 8px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: rgba(10, 20, 45, 0.7);
  transition: 0.18s ease;
}
.sb-scope__tab + .sb-scope__tab { border-left: 1px solid rgba(10, 20, 45, 0.08); }
.sb-scope__tab:hover { background: rgba(32, 90, 255, 0.06); }
.sb-scope__tab--on {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.96), rgba(0, 194, 255, 0.88));
  color: #fff;
}

.sb-actions { display: flex; gap: 10px; flex-wrap: wrap; }
.sb-btn {
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.92);
  color: rgba(10, 20, 45, 0.92);
  transition: 0.18s ease;
}
.sb-btn:hover:not(:disabled) { transform: translateY(-1px); border-color: rgba(32, 90, 255, 0.35); }
.sb-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.sb-btn--primary {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.96), rgba(0, 194, 255, 0.88));
  border-color: transparent;
  color: #fff;
  box-shadow: 0 6px 16px rgba(32, 90, 255, 0.35);
}

.sb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 14px;
}
.sb-card {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 18px;
  padding: 18px 20px;
  box-shadow: 0 20px 50px rgba(10, 20, 45, 0.08);
}
.sb-card--wide { grid-column: 1 / -1; }

.sb-card__head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.sb-card__h { margin: 0; font-size: 16px; font-weight: 700; }
.sb-card__hint { margin: 6px 0 10px; color: rgba(10, 20, 45, 0.65); font-size: 13px; line-height: 1.5; }

.sb-ai-btn {
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid rgba(32, 90, 255, 0.3);
  background: rgba(32, 90, 255, 0.08);
  color: rgba(32, 90, 255, 0.9);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.18s ease;
}
.sb-ai-btn:hover:not(:disabled) { background: rgba(32, 90, 255, 0.16); }
.sb-ai-btn:disabled { opacity: 0.55; cursor: wait; }

.sb-field__label { display: block; font-size: 13px; font-weight: 600; margin: 8px 0 6px; color: rgba(10, 20, 45, 0.78); }

.sb-input {
  width: 100%;
  padding: 9px 12px;
  border-radius: 10px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  font-size: 14px;
  background: #fff;
}
.sb-input:focus { outline: none; border-color: rgba(32, 90, 255, 0.5); box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.12); }
.sb-input--kr { font-size: 13px; }

.sb-textarea {
  width: 100%;
  border: 1px solid rgba(10, 20, 45, 0.14);
  border-radius: 12px;
  padding: 10px 12px;
  font-size: 14px;
  line-height: 1.5;
  font-family: inherit;
  background: #fff;
  resize: vertical;
}
.sb-textarea:focus { outline: none; border-color: rgba(32, 90, 255, 0.5); box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.12); }
.sb-textarea--tight { min-height: 60px; }

.sb-chips { display: flex; flex-wrap: wrap; gap: 8px; }
.sb-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 6px 4px 10px;
  border-radius: 999px;
  background: rgba(32, 90, 255, 0.08);
  border: 1px solid rgba(32, 90, 255, 0.2);
  font-size: 13px;
}
.sb-chip__input {
  border: none;
  background: transparent;
  min-width: 80px;
  max-width: 180px;
  font-size: 13px;
  color: rgba(10, 20, 45, 0.9);
}
.sb-chip__input:focus { outline: none; }
.sb-chip__x {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: none;
  background: rgba(10, 20, 45, 0.1);
  color: rgba(10, 20, 45, 0.7);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}
.sb-chip--add {
  background: transparent;
  border-style: dashed;
  cursor: pointer;
  color: rgba(32, 90, 255, 0.9);
  padding: 6px 12px;
}

.sb-subhead {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0 6px;
}
.sb-subhead h4 { margin: 0; font-size: 13px; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(10, 20, 45, 0.6); font-weight: 700; }
.sb-link-btn {
  background: none;
  border: none;
  color: rgba(32, 90, 255, 0.9);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
}
.sb-link-btn:hover { background: rgba(32, 90, 255, 0.08); }
.sb-link-btn--danger { color: rgba(239, 68, 68, 0.9); }
.sb-link-btn--danger:hover { background: rgba(239, 68, 68, 0.08); }

.sb-pillar {
  display: grid;
  grid-template-columns: 1fr 2fr auto;
  gap: 8px;
  align-items: start;
  margin-bottom: 8px;
}
.sb-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 6px;
}
.sb-row-x {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  background: #fff;
  color: rgba(10, 20, 45, 0.7);
  cursor: pointer;
  font-size: 16px;
  line-height: 1;
  flex-shrink: 0;
}
.sb-row-x:hover { background: rgba(239, 68, 68, 0.08); border-color: rgba(239, 68, 68, 0.3); color: rgba(239, 68, 68, 0.9); }

.sb-okr {
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 12px;
  padding: 10px 12px;
  background: rgba(246, 249, 255, 0.5);
  margin-bottom: 10px;
}
.sb-okr__actions {
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-top: 6px;
}

.sb-bottom {
  margin-top: 18px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 14px;
  padding: 14px 18px;
}

.sb-error {
  color: #b00020;
  font-size: 13px;
  margin: 10px 0;
}

@media (max-width: 600px) {
  .sb-pillar { grid-template-columns: 1fr; }
}
</style>
