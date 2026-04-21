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

      <div class="sb-industry">
        <label class="sb-field__label" for="sb-industry">{{ $t('strategyBuilder.industryLabel') }}</label>
        <input id="sb-industry" v-model="industry" class="sb-input" :placeholder="$t('strategyBuilder.industryPlaceholder')" />
      </div>

      <p v-if="aiError" class="sb-error">{{ aiError }}</p>

      <section class="sb-grid">
        <article class="sb-summary" @click="openEditor('vision')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.vision.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <p v-if="form.vision" class="sb-summary__body">{{ form.vision }}</p>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.vision.hint') }}</p>
        </article>

        <article class="sb-summary" @click="openEditor('mission')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.mission.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <p v-if="form.mission" class="sb-summary__body">{{ form.mission }}</p>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.mission.hint') }}</p>
        </article>

        <article class="sb-summary" @click="openEditor('purpose')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.purpose.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <p v-if="form.purpose" class="sb-summary__body">{{ form.purpose }}</p>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.purpose.hint') }}</p>
        </article>

        <article class="sb-summary" @click="openEditor('values')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.values.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <div v-if="valuesFilled.length" class="sb-summary__chips">
            <span v-for="(v, i) in valuesFilled" :key="`v-${i}`" class="sb-summary__chip">{{ v }}</span>
          </div>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.values.hint') }}</p>
        </article>

        <article class="sb-summary sb-summary--wide" @click="openEditor('strategy')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.strategy.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <p v-if="strategyPreview" class="sb-summary__body">{{ strategyPreview }}</p>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.strategy.hint') }}</p>
        </article>

        <article class="sb-summary sb-summary--wide" @click="openEditor('okrs')">
          <header class="sb-summary__head">
            <h3 class="sb-summary__h">{{ $t('strategyBuilder.okrs.title') }}</h3>
            <span class="sb-summary__edit">{{ $t('strategyBuilder.edit') }}</span>
          </header>
          <p v-if="okrsPreview" class="sb-summary__body">{{ okrsPreview }}</p>
          <p v-else class="sb-summary__empty">{{ $t('strategyBuilder.okrs.hint') }}</p>
        </article>
      </section>

      <div v-if="openSection" class="sb-modal-overlay" @click.self="closeEditor">
        <div class="sb-modal" role="dialog" aria-modal="true">
          <header class="sb-modal__head">
            <h2 class="sb-modal__h">{{ modalTitle }}</h2>
            <button type="button" class="sb-modal__close" :aria-label="$t('strategyBuilder.close')" @click="closeEditor">×</button>
          </header>

          <div class="sb-modal__body">
            <p class="sb-modal__hint">{{ modalHint }}</p>

            <!-- Vision / Mission / Purpose: single textarea -->
            <template v-if="['vision', 'mission', 'purpose'].includes(openSection)">
              <textarea
                v-model="form[openSection]"
                class="sb-textarea"
                rows="4"
                :placeholder="$t(`strategyBuilder.${openSection}.placeholder`)"
              />
            </template>

            <!-- Values: chips list -->
            <template v-else-if="openSection === 'values'">
              <div class="sb-chips">
                <span v-for="(val, idx) in form.values" :key="`vm-${idx}`" class="sb-chip">
                  <input
                    v-model="form.values[idx]"
                    class="sb-chip__input"
                    :placeholder="$t('strategyBuilder.values.placeholder')"
                  />
                  <button type="button" class="sb-chip__x" @click="removeValue(idx)" aria-label="remove">×</button>
                </span>
                <button type="button" class="sb-chip--add" @click="addValue">
                  + {{ $t('strategyBuilder.values.add') }}
                </button>
              </div>
            </template>

            <!-- Strategy: horizon + pillars + bets + metrics -->
            <template v-else-if="openSection === 'strategy'">
              <label class="sb-field__label">{{ $t('strategyBuilder.strategy.horizon') }}</label>
              <input v-model="form.strategy.horizon" class="sb-input" :placeholder="$t('strategyBuilder.strategy.horizonPlaceholder')" />

              <div class="sb-subhead">
                <h4>{{ $t('strategyBuilder.strategy.pillars') }}</h4>
                <button type="button" class="sb-link-btn" @click="addPillar">+ {{ $t('strategyBuilder.add') }}</button>
              </div>
              <div v-for="(p, idx) in form.strategy.pillars" :key="`pm-${idx}`" class="sb-editor-row sb-editor-row--split">
                <div class="sb-editor-row__fields">
                  <input v-model="p.name" class="sb-input" :placeholder="$t('strategyBuilder.strategy.pillarName')" />
                  <textarea v-model="p.description" class="sb-textarea sb-textarea--tight" rows="2" :placeholder="$t('strategyBuilder.strategy.pillarDesc')" />
                </div>
                <button type="button" class="sb-row-x" @click="removePillar(idx)" aria-label="remove">×</button>
              </div>

              <div class="sb-subhead">
                <h4>{{ $t('strategyBuilder.strategy.bets') }}</h4>
                <button type="button" class="sb-link-btn" @click="form.strategy.bets.push('')">+ {{ $t('strategyBuilder.add') }}</button>
              </div>
              <div v-for="(b, idx) in form.strategy.bets" :key="`bm-${idx}`" class="sb-editor-row">
                <input v-model="form.strategy.bets[idx]" class="sb-input" :placeholder="$t('strategyBuilder.strategy.betPlaceholder')" />
                <button type="button" class="sb-row-x" @click="form.strategy.bets.splice(idx, 1)">×</button>
              </div>

              <div class="sb-subhead">
                <h4>{{ $t('strategyBuilder.strategy.metrics') }}</h4>
                <button type="button" class="sb-link-btn" @click="form.strategy.metrics.push('')">+ {{ $t('strategyBuilder.add') }}</button>
              </div>
              <div v-for="(m, idx) in form.strategy.metrics" :key="`mm-${idx}`" class="sb-editor-row">
                <input v-model="form.strategy.metrics[idx]" class="sb-input" :placeholder="$t('strategyBuilder.strategy.metricPlaceholder')" />
                <button type="button" class="sb-row-x" @click="form.strategy.metrics.splice(idx, 1)">×</button>
              </div>
            </template>

            <!-- OKRs: objectives + key results -->
            <template v-else-if="openSection === 'okrs'">
              <div v-for="(o, idx) in form.okrs" :key="`om-${idx}`" class="sb-okr">
                <input v-model="o.objective" class="sb-input" :placeholder="$t('strategyBuilder.okrs.objectivePlaceholder')" />
                <div v-for="(kr, krIdx) in o.key_results" :key="`kr-${idx}-${krIdx}`" class="sb-editor-row">
                  <input v-model="o.key_results[krIdx]" class="sb-input sb-input--kr" :placeholder="$t('strategyBuilder.okrs.krPlaceholder')" />
                  <button type="button" class="sb-row-x" @click="o.key_results.splice(krIdx, 1)">×</button>
                </div>
                <div class="sb-okr__actions">
                  <button type="button" class="sb-link-btn" @click="o.key_results.push('')">+ {{ $t('strategyBuilder.okrs.addKr') }}</button>
                  <button type="button" class="sb-link-btn sb-link-btn--danger" @click="form.okrs.splice(idx, 1)">{{ $t('strategyBuilder.okrs.removeObjective') }}</button>
                </div>
              </div>
              <button type="button" class="sb-btn sb-btn--ghost sb-btn--block" @click="addObjective">+ {{ $t('strategyBuilder.okrs.addObjective') }}</button>
            </template>
          </div>

          <footer class="sb-modal__foot">
            <button type="button" class="sb-btn sb-btn--ghost" :disabled="aiLoading[openSection]" @click="runAi(openSection)">
              <span v-if="!aiLoading[openSection]">{{ $t('strategyBuilder.aiHelp') }}</span>
              <span v-else>{{ $t('strategyBuilder.aiThinking') }}</span>
            </button>
            <button type="button" class="sb-btn sb-btn--primary" @click="closeEditor">
              {{ $t('strategyBuilder.done') }}
            </button>
          </footer>
        </div>
      </div>
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
      openSection: null,
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
    valuesFilled() {
      return (this.form.values || []).map((v) => String(v || '').trim()).filter(Boolean);
    },
    strategyPreview() {
      const s = this.form.strategy || {};
      const parts = [];
      if (s.horizon) parts.push(s.horizon);
      const pillars = (s.pillars || []).filter((p) => p && (p.name || p.description));
      if (pillars.length) parts.push(this.$t('strategyBuilder.preview.pillars', { n: pillars.length }));
      const bets = (s.bets || []).filter(Boolean);
      if (bets.length) parts.push(this.$t('strategyBuilder.preview.bets', { n: bets.length }));
      const metrics = (s.metrics || []).filter(Boolean);
      if (metrics.length) parts.push(this.$t('strategyBuilder.preview.metrics', { n: metrics.length }));
      return parts.join(' · ');
    },
    okrsPreview() {
      const list = (this.form.okrs || []).filter((o) => o && (o.objective || (o.key_results || []).some(Boolean)));
      if (!list.length) return '';
      const krs = list.reduce((acc, o) => acc + (o.key_results || []).filter(Boolean).length, 0);
      return this.$t('strategyBuilder.preview.okrs', { o: list.length, k: krs });
    },
    modalTitle() {
      if (!this.openSection) return '';
      return this.$t(`strategyBuilder.${this.openSection}.title`);
    },
    modalHint() {
      if (!this.openSection) return '';
      return this.$t(`strategyBuilder.${this.openSection}.hint`);
    },
  },
  watch: {
    openSection(val) {
      if (typeof document !== 'undefined') {
        document.body.style.overflow = val ? 'hidden' : '';
      }
    },
  },
  beforeUnmount() {
    if (typeof document !== 'undefined') document.body.style.overflow = '';
  },
  methods: {
    openEditor(section) {
      this.openSection = section;
      this.aiError = '';
    },
    closeEditor() {
      this.openSection = null;
    },
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
.sb-page { position: relative; min-height: calc(100vh - 40px); }
.sb-page__bg { position: absolute; inset: 0; pointer-events: none; overflow: hidden; z-index: 0; }
.sb-page__orb { position: absolute; width: 540px; height: 540px; border-radius: 50%; filter: blur(60px); opacity: 0.55; }
.sb-page__orb--1 { top: -220px; left: -210px; background: radial-gradient(circle at 30% 30%, rgba(120, 119, 255, 0.4), transparent 65%); }
.sb-page__orb--2 { bottom: -220px; right: -160px; background: radial-gradient(circle at 70% 70%, rgba(0, 194, 255, 0.35), transparent 65%); }

.sb-intro,
.sb-toolbar,
.sb-industry,
.sb-summary,
.sb-modal-overlay { position: relative; z-index: 1; }

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
  margin: 18px 0 10px;
}
.sb-scope { min-width: 260px; }
.sb-scope__tabs {
  display: inline-flex;
  border: 1px solid rgba(10, 20, 45, 0.12);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.92);
}
.sb-actions { display: flex; gap: 10px; flex-wrap: wrap; }

.sb-industry {
  margin-bottom: 18px;
  background: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 14px;
  padding: 12px 16px;
}

.sb-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px;
}

.sb-summary {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 18px;
  padding: 16px 18px;
  box-shadow: 0 18px 42px rgba(10, 20, 45, 0.08);
  cursor: pointer;
  transition: 0.18s ease;
  min-height: 120px;
}
.sb-summary:hover {
  transform: translateY(-2px);
  border-color: rgba(32, 90, 255, 0.35);
  box-shadow: 0 22px 50px rgba(10, 20, 45, 0.12);
}
.sb-summary--wide { grid-column: 1 / -1; }

.sb-summary__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.sb-summary__h { margin: 0; font-size: 15px; font-weight: 700; }
.sb-summary__edit {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(32, 90, 255, 0.9);
}
.sb-summary__body { margin: 0; font-size: 14px; line-height: 1.55; color: rgba(10, 20, 45, 0.88); }
.sb-summary__empty { margin: 0; font-size: 13px; color: rgba(10, 20, 45, 0.55); font-style: italic; line-height: 1.5; }
.sb-summary__chips { display: flex; flex-wrap: wrap; gap: 6px; }
.sb-summary__chip {
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(32, 90, 255, 0.1);
  color: rgba(32, 90, 255, 0.95);
  font-size: 12px;
  font-weight: 600;
}

.sb-field__label { display: block; font-size: 13px; font-weight: 600; margin: 8px 0 6px; color: rgba(10, 20, 45, 0.78); }

.sb-input {
  width: 100%;
  padding: 9px 12px;
  border-radius: 10px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  font-size: 14px;
  background: #fff;
  box-sizing: border-box;
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
  box-sizing: border-box;
}
.sb-textarea:focus { outline: none; border-color: rgba(32, 90, 255, 0.5); box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.12); }
.sb-textarea--tight { min-height: 60px; }

.sb-chips { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 4px; }
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

.sb-subhead {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 14px 0 6px;
}
.sb-subhead h4 { margin: 0; font-size: 12px; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(10, 20, 45, 0.6); font-weight: 700; }

.sb-editor-row {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 8px;
}
.sb-editor-row--split {
  align-items: flex-start;
}
.sb-editor-row__fields {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr;
  gap: 6px;
}

.sb-okr {
  border: 1px solid rgba(10, 20, 45, 0.08);
  border-radius: 12px;
  padding: 12px 14px;
  background: rgba(246, 249, 255, 0.6);
  margin-bottom: 10px;
}
.sb-okr > .sb-input:first-child { margin-bottom: 8px; }
.sb-okr__actions {
  display: flex;
  gap: 10px;
  justify-content: space-between;
  margin-top: 6px;
}

.sb-error { color: #b00020; font-size: 13px; margin: 10px 0; }

/* Modal */
.sb-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(10, 20, 45, 0.55);
  backdrop-filter: blur(4px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 60;
  padding: 20px;
  animation: sbFadeIn 0.18s ease-out;
}
.sb-modal {
  width: min(640px, 100%);
  max-height: min(90vh, 860px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 40px 100px rgba(10, 20, 45, 0.3);
  overflow: hidden;
  animation: sbSlideUp 0.22s ease-out;
}
.sb-modal__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 22px;
  border-bottom: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(160deg, rgba(246, 249, 255, 0.9), rgba(255, 255, 255, 1));
}
.sb-modal__h { margin: 0; font-size: 18px; font-weight: 700; }
.sb-modal__close {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  border: none;
  background: rgba(10, 20, 45, 0.06);
  color: rgba(10, 20, 45, 0.7);
  font-size: 20px;
  cursor: pointer;
  line-height: 1;
  padding: 0;
}
.sb-modal__close:hover { background: rgba(10, 20, 45, 0.12); color: rgba(10, 20, 45, 0.95); }

.sb-modal__body {
  padding: 18px 22px;
  overflow-y: auto;
  flex: 1;
}
.sb-modal__hint { margin: 0 0 12px; color: rgba(10, 20, 45, 0.65); font-size: 13px; line-height: 1.55; }

.sb-modal__foot {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(246, 249, 255, 0.6);
  flex-wrap: wrap;
}

@keyframes sbFadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes sbSlideUp {
  from { opacity: 0; transform: translateY(14px); }
  to { opacity: 1; transform: translateY(0); }
}

@media (max-width: 600px) {
  .sb-modal { border-radius: 16px; }
  .sb-modal__head, .sb-modal__body, .sb-modal__foot { padding-left: 16px; padding-right: 16px; }
}
</style>
