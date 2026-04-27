<template>
  <article class="rep" :id="domId" v-if="ready">
    <header class="rep__head">
      <h1 class="rep__title">{{ $t('agileTraining.stakeholderMatrix.report.title') }}</h1>
      <p class="rep__sub">
        <span v-if="groupName">{{ groupName }}</span>
        <span v-if="participantName"> · {{ participantName }}</span>
        <span class="rep__date">· {{ formattedDate }}</span>
      </p>
      <p v-if="activeCase" class="rep__case">
        <span class="rep__case-emoji">{{ activeCase.emoji }}</span>
        <strong>{{ activeCase.title }}</strong>
        — {{ activeCase.lead }}
        <br /><em>{{ $t('agileTraining.stakeholderMatrix.screens.context.goalLabel') }}:</em> {{ activeCase.goal }}
      </p>
    </header>

    <section class="rep__sec">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.report.matrixR1') }}</h2>
      <div class="rep__matrix">
        <div class="rep__y-axis">{{ axisY }}</div>
        <div class="rep__grid">
          <div v-for="infl in [2, 1, 0]" :key="'r1' + infl" class="rep__row">
            <div class="rep__y-tick">{{ levelLabels[infl] }}</div>
            <div
              v-for="intv in [0, 1, 2]"
              :key="'r1' + infl + '-' + intv"
              class="rep__cell"
              :class="cellClass(infl, intv)"
            >
              <div class="rep__cell-tag">{{ cellStrategyLabel(infl, intv) }}</div>
              <div class="rep__cell-items">
                <div
                  v-for="rid in rolesInCell(placementsR1, infl, intv)"
                  :key="'r1c-' + rid"
                  class="rep__chip"
                >
                  <span class="rep__chip-emoji">{{ personaEmoji(rid) }}</span>
                  <span>{{ personaName(rid) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="rep__x-ticks">
            <span v-for="(lb, j) in levelLabelsX" :key="'rx1-' + j">{{ lb }}</span>
          </div>
          <div class="rep__x-axis">{{ axisX }}</div>
        </div>
      </div>
    </section>

    <section class="rep__sec" v-if="hasR2">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.report.matrixR2') }}</h2>
      <p v-if="activeEvent" class="rep__event">
        <strong>{{ $t('agileTraining.stakeholderMatrix.report.eventLabel') }}:</strong>
        {{ activeEvent.emoji }} {{ activeEvent.title }} — {{ activeEvent.lead }}
      </p>
      <div class="rep__matrix">
        <div class="rep__y-axis">{{ axisY }}</div>
        <div class="rep__grid">
          <div v-for="infl in [2, 1, 0]" :key="'r2' + infl" class="rep__row">
            <div class="rep__y-tick">{{ levelLabels[infl] }}</div>
            <div
              v-for="intv in [0, 1, 2]"
              :key="'r2' + infl + '-' + intv"
              class="rep__cell"
              :class="cellClass(infl, intv)"
            >
              <div class="rep__cell-tag">{{ cellStrategyLabel(infl, intv) }}</div>
              <div class="rep__cell-items">
                <div
                  v-for="rid in rolesInCell(placementsR2, infl, intv)"
                  :key="'r2c-' + rid"
                  class="rep__chip"
                >
                  <span class="rep__chip-emoji">{{ personaEmoji(rid) }}</span>
                  <span>{{ personaName(rid) }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="rep__x-ticks">
            <span v-for="(lb, j) in levelLabelsX" :key="'rx2-' + j">{{ lb }}</span>
          </div>
          <div class="rep__x-axis">{{ axisX }}</div>
        </div>
      </div>
    </section>

    <section class="rep__sec" v-if="diff && diff.length">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.screens.final.diffTitle') }}</h2>
      <ul class="rep__diff">
        <li v-for="d in diff" :key="'rdiff-' + d.rid" :class="'rep__diff-item rep__diff-item--' + d.kind">
          <span class="rep__chip-emoji">{{ d.persona.emoji }}</span>
          <strong>{{ d.persona.name }}</strong>
          <span class="rep__muted">· {{ d.persona.role }}</span>
          <span class="rep__diff-arrow">{{ diffArrow(d.kind) }}</span>
          <span>{{ $t('agileTraining.stakeholderMatrix.diff.' + d.kind) }}</span>
          <span v-if="d.from && d.to" class="rep__muted">
            ({{ levelLabels[d.from.infl] }} / {{ levelLabelsX[d.from.int] }}
            → {{ levelLabels[d.to.infl] }} / {{ levelLabelsX[d.to.int] }})
          </span>
        </li>
      </ul>
    </section>

    <section class="rep__sec" v-if="filledDiscussion.length">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.report.discussion') }}</h2>
      <div v-for="d in filledDiscussion" :key="'rd-' + d.rid" class="rep__discuss">
        <h3 class="rep__h3">
          <span class="rep__chip-emoji">{{ personaEmoji(d.rid) }}</span>
          {{ personaName(d.rid) }}
          <span class="rep__muted">· {{ personaRole(d.rid) }}</span>
        </h3>
        <p v-if="d.why_power"><strong>{{ $t('agileTraining.stakeholderMatrix.discussion.q1') }}</strong> {{ d.why_power }}</p>
        <p v-if="d.why_interest"><strong>{{ $t('agileTraining.stakeholderMatrix.discussion.q2') }}</strong> {{ d.why_interest }}</p>
        <p v-if="d.if_ignore"><strong>{{ $t('agileTraining.stakeholderMatrix.discussion.q3') }}</strong> {{ d.if_ignore }}</p>
      </div>
    </section>

    <section class="rep__sec" v-if="hasStrategy">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.report.strategy') }}</h2>
      <div v-for="qk in ['hh','hl','lh','ll']" :key="'rs-' + qk">
        <template v-if="strategyQuadrant[qk]">
          <h3 class="rep__h3">{{ strategyHints[qk] }}</h3>
          <p class="rep__pre">{{ strategyQuadrant[qk] }}</p>
        </template>
      </div>
    </section>

    <section class="rep__sec" v-if="reactions && reactions.length">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.screens.consequences.reactionsTitle') }}</h2>
      <div class="rep__reactions">
        <div v-for="r in reactions" :key="'rr-' + r.rid" class="rep__reaction" :class="'rep__reaction--' + r.bucket">
          <p class="rep__reaction-h">
            <span class="rep__chip-emoji">{{ r.persona.emoji }}</span>
            <strong>{{ r.persona.name }}</strong>
            <span class="rep__muted">· {{ r.persona.role }}</span>
          </p>
          <p class="rep__reaction-q">{{ r.quote }}</p>
        </div>
      </div>
    </section>

    <section class="rep__sec" v-if="consequencesR1.length || consequencesR2.length || strengthsR1.length || strengthsR2.length">
      <h2 class="rep__h2">{{ $t('agileTraining.stakeholderMatrix.report.consequences') }}</h2>
      <div class="rep__cons-grid">
        <div v-if="consequencesR1.length || strengthsR1.length">
          <h3 class="rep__h3">{{ $t('agileTraining.stakeholderMatrix.screens.final.round1') }}</h3>
          <ul class="rep__bullets" v-if="consequencesR1.length">
            <li v-for="(line, i) in consequencesR1" :key="'rc1-' + i">{{ line }}</li>
          </ul>
          <ul class="rep__bullets rep__bullets--pos" v-if="strengthsR1.length">
            <li v-for="(line, i) in strengthsR1" :key="'rs1-' + i">{{ line }}</li>
          </ul>
        </div>
        <div v-if="consequencesR2.length || strengthsR2.length">
          <h3 class="rep__h3">{{ $t('agileTraining.stakeholderMatrix.screens.final.round2') }}</h3>
          <ul class="rep__bullets" v-if="consequencesR2.length">
            <li v-for="(line, i) in consequencesR2" :key="'rc2-' + i">{{ line }}</li>
          </ul>
          <ul class="rep__bullets rep__bullets--pos" v-if="strengthsR2.length">
            <li v-for="(line, i) in strengthsR2" :key="'rs2-' + i">{{ line }}</li>
          </ul>
        </div>
      </div>
    </section>

    <footer class="rep__foot">
      {{ $t('agileTraining.stakeholderMatrix.report.footer') }}
    </footer>
  </article>
</template>

<script>
import { cellBucket } from './logic.js';

export default {
  name: 'SummaryReport',
  props: {
    domId: { type: String, default: 'sh-report' },
    groupName: { type: String, default: '' },
    participantName: { type: String, default: '' },
    locale: { type: String, default: 'ru' },
    activeCase: { type: Object, default: null },
    activeEvent: { type: Object, default: null },
    placementsR1: { type: Object, default: () => ({}) },
    placementsR2: { type: Object, default: () => ({}) },
    discussion: { type: Object, default: () => ({}) },
    strategyQuadrant: { type: Object, default: () => ({}) },
    strategyHints: { type: Object, default: () => ({}) },
    reactions: { type: Array, default: () => [] },
    diff: { type: Array, default: () => [] },
    consequencesR1: { type: Array, default: () => [] },
    consequencesR2: { type: Array, default: () => [] },
    strengthsR1: { type: Array, default: () => [] },
    strengthsR2: { type: Array, default: () => [] },
    personas: { type: Object, default: () => ({}) },
    levelLabels: { type: Array, default: () => [] },
    levelLabelsX: { type: Array, default: () => [] },
    cellStrategy: { type: Object, default: () => ({}) },
    axisX: { type: String, default: '' },
    axisY: { type: String, default: '' },
  },
  computed: {
    ready() {
      return Boolean(this.levelLabels && this.levelLabels.length);
    },
    hasR2() {
      return Object.values(this.placementsR2 || {}).some((p) => p);
    },
    hasStrategy() {
      return ['hh', 'hl', 'lh', 'll'].some((k) => (this.strategyQuadrant[k] || '').trim());
    },
    filledDiscussion() {
      const out = [];
      Object.keys(this.discussion || {}).forEach((rid) => {
        const d = this.discussion[rid] || {};
        if ((d.why_power || '').trim() || (d.why_interest || '').trim() || (d.if_ignore || '').trim()) {
          out.push({ rid, ...d });
        }
      });
      return out;
    },
    formattedDate() {
      try {
        return new Date().toLocaleString(this.locale === 'en' ? 'en-GB' : 'ru-RU', {
          year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit',
        });
      } catch (_) {
        return '';
      }
    },
  },
  methods: {
    personaEmoji(rid) { return (this.personas[rid] && this.personas[rid].emoji) || '👤'; },
    personaName(rid) { return (this.personas[rid] && this.personas[rid].name) || rid; },
    personaRole(rid) { return (this.personas[rid] && this.personas[rid].role) || ''; },
    cellClass(infl, int) { return 'rep__cell--' + cellBucket(infl, int); },
    cellStrategyLabel(infl, int) {
      const b = cellBucket(infl, int);
      return this.cellStrategy[b] || b;
    },
    rolesInCell(map, infl, int) {
      return Object.keys(map || {}).filter((rid) => {
        const p = map[rid];
        return p && p.infl === infl && p.int === int;
      });
    },
    diffArrow(kind) {
      switch (kind) {
        case 'up': return '⬆';
        case 'down': return '⬇';
        case 'placed': return '＋';
        case 'removed': return '✕';
        default: return '↔';
      }
    },
  },
};
</script>

<style scoped>
.rep { font-family: var(--vl-font, "Segoe UI", system-ui, sans-serif); color: #0f172a; background: #fff; padding: 24px; border-radius: 12px; border: 1px solid rgba(15,23,42,0.1); margin-top: 16px; }
.rep__head { border-bottom: 2px solid #1d4ed8; padding-bottom: 10px; margin-bottom: 14px; }
.rep__title { margin: 0 0 4px; font-size: 22px; color: #1d4ed8; }
.rep__sub { margin: 0 0 8px; color: #64748b; font-size: 13px; }
.rep__date { color: #94a3b8; }
.rep__case { margin: 4px 0 0; line-height: 1.5; font-size: 13.5px; color: #1f2937; }
.rep__case-emoji { font-size: 22px; vertical-align: middle; margin-right: 4px; }
.rep__sec { margin-top: 18px; page-break-inside: avoid; break-inside: avoid; }
.rep__h2 { margin: 0 0 8px; font-size: 16px; color: #0f172a; border-left: 4px solid #1d4ed8; padding-left: 8px; }
.rep__h3 { margin: 8px 0 4px; font-size: 14px; }
.rep__muted { color: #64748b; font-weight: 400; font-size: 12.5px; }
.rep__event { margin: 0 0 8px; font-size: 13px; color: #1f2937; padding: 8px 10px; background: #fef3c7; border-radius: 8px; line-height: 1.5; }

.rep__matrix { display: grid; grid-template-columns: 28px 1fr; gap: 4px; align-items: stretch; }
.rep__y-axis { writing-mode: vertical-rl; transform: rotate(180deg); font-size: 11px; font-weight: 700; color: #64748b; line-height: 1.2; padding: 4px 0; }
.rep__grid { min-width: 0; }
.rep__row { display: grid; grid-template-columns: 70px 1fr 1fr 1fr; gap: 2px; align-items: stretch; }
.rep__y-tick { font-size: 10px; font-weight: 700; color: #475569; display: flex; align-items: center; justify-content: center; line-height: 1.1; }
.rep__cell { min-height: 90px; border: 1px solid #94a3b8; padding: 4px; font-size: 11px; display: flex; flex-direction: column; }
.rep__cell--minimal { background: #fff; }
.rep__cell--informed { background: #eef2ff; }
.rep__cell--satisfied { background: #c7d2fe; }
.rep__cell--close { background: #1e3a8a; color: #f8fafc; }
.rep__cell-tag { font-size: 9px; font-weight: 700; margin-bottom: 4px; opacity: 0.95; line-height: 1.1; text-transform: uppercase; letter-spacing: .04em; }
.rep__cell-items { flex: 1; display: flex; flex-direction: column; gap: 3px; }
.rep__chip { display: inline-flex; gap: 4px; align-items: center; background: #fff; color: #1f2937; font-size: 11px; font-weight: 600; padding: 2px 6px; border-radius: 6px; border: 1px solid rgba(15,23,42,0.12); }
.rep__cell--close .rep__chip { color: #1e3a8a; }
.rep__chip-emoji { font-size: 13px; }
.rep__x-ticks { display: grid; grid-template-columns: 1fr 1fr 1fr; text-align: center; font-size: 10px; font-weight: 600; color: #64748b; padding-left: 70px; margin-top: 2px; }
.rep__x-axis { text-align: center; font-size: 11px; font-weight: 700; color: #475569; padding-left: 70px; margin-top: 2px; }

.rep__diff { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 4px; }
.rep__diff-item { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; padding: 6px 8px; border-radius: 8px; background: #f8fafc; font-size: 13px; border: 1px solid rgba(15,23,42,0.08); }
.rep__diff-item--up { background: #ecfdf5; border-color: #bbf7d0; }
.rep__diff-item--down { background: #fef2f2; border-color: #fecaca; }
.rep__diff-item--placed { background: #eef2ff; border-color: #c7d2fe; }
.rep__diff-item--removed { background: #f5f5f4; border-color: #e7e5e4; }
.rep__diff-arrow { color: #1d4ed8; font-weight: 700; font-size: 15px; }

.rep__discuss { padding: 8px 0; border-top: 1px solid #e2e8f0; }
.rep__discuss:first-of-type { border-top: none; }
.rep__discuss p { margin: 4px 0; font-size: 13px; line-height: 1.45; }

.rep__pre { white-space: pre-wrap; font-size: 13.5px; line-height: 1.5; margin: 4px 0 8px; padding: 8px 10px; background: #f8fafc; border-radius: 8px; border-left: 3px solid #1d4ed8; }

.rep__reactions { display: grid; gap: 8px; grid-template-columns: 1fr 1fr; }
.rep__reaction { padding: 8px 10px; border-radius: 8px; border: 1px solid rgba(15,23,42,0.1); background: #fff; }
.rep__reaction--close { background: #eef2ff; border-color: #c7d2fe; }
.rep__reaction--minimal { background: #fefce8; border-color: #fde68a; }
.rep__reaction--satisfied { background: #f1f5f9; }
.rep__reaction-h { margin: 0 0 4px; font-size: 13px; }
.rep__reaction-q { margin: 0; font-size: 13px; line-height: 1.45; color: #1f2937; }

.rep__cons-grid { display: grid; gap: 12px; grid-template-columns: 1fr 1fr; }
.rep__bullets { margin: 4px 0; padding-left: 18px; font-size: 13px; line-height: 1.5; }
.rep__bullets--pos { color: #14532d; }

.rep__foot { margin-top: 18px; padding-top: 8px; border-top: 1px solid #e2e8f0; color: #94a3b8; font-size: 11px; text-align: center; }

@media (max-width: 700px) {
  .rep__cons-grid, .rep__reactions { grid-template-columns: 1fr; }
}
</style>
