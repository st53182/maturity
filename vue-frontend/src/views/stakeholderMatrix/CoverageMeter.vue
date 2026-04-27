<template>
  <div class="cv">
    <div class="cv__head">
      <strong>{{ $t('agileTraining.stakeholderMatrix.screens.matrix.coverageTitle') }}</strong>
      <span class="cv__score">{{ $t('agileTraining.stakeholderMatrix.coverage.score') }}: {{ score }}%</span>
    </div>
    <div class="cv__bars">
      <div v-for="b in bars" :key="b.key" class="cv__bar" :class="'cv__bar--' + b.key">
        <span class="cv__label">{{ $t('agileTraining.stakeholderMatrix.coverage.' + b.key) }}</span>
        <span class="cv__fill" :style="{ width: b.percent + '%' }" />
        <span class="cv__count">{{ b.count }}</span>
      </div>
    </div>
    <p class="cv__hint">{{ $t('agileTraining.stakeholderMatrix.screens.matrix.coverageHint') }}</p>
  </div>
</template>

<script>
import { bucketCounts, coverageScore } from './content.js';

export default {
  name: 'CoverageMeter',
  props: {
    placements: { type: Object, required: true },
    locale: { type: String, default: 'ru' },
  },
  computed: {
    counts() { return bucketCounts(this.placements); },
    total() {
      const c = this.counts;
      return Math.max(1, c.minimal + c.informed + c.satisfied + c.close);
    },
    score() { return coverageScore(this.placements); },
    bars() {
      const c = this.counts;
      const t = this.total;
      return [
        { key: 'minimal', count: c.minimal, percent: (c.minimal / t) * 100 },
        { key: 'informed', count: c.informed, percent: (c.informed / t) * 100 },
        { key: 'satisfied', count: c.satisfied, percent: (c.satisfied / t) * 100 },
        { key: 'close', count: c.close, percent: (c.close / t) * 100 },
      ];
    },
  },
};
</script>

<style scoped>
.cv { margin-top: 12px; padding: 10px 12px; border: 1px solid rgba(15,23,42,0.08); border-radius: 10px; background: #f8fafc; }
.cv__head { display: flex; justify-content: space-between; gap: 8px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
.cv__score { background: #1d4ed8; color: #fff; padding: 2px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; }
.cv__bars { display: flex; flex-direction: column; gap: 6px; }
.cv__bar { position: relative; display: grid; grid-template-columns: 110px 1fr 28px; gap: 8px; align-items: center; height: 22px; }
.cv__label { font-size: 12px; font-weight: 600; color: #334155; }
.cv__fill { display: block; height: 12px; border-radius: 6px; background: #cbd5e1; transition: width .25s ease; }
.cv__bar--minimal .cv__fill { background: #e5e7eb; }
.cv__bar--informed .cv__fill { background: #93c5fd; }
.cv__bar--satisfied .cv__fill { background: #6366f1; }
.cv__bar--close .cv__fill { background: #1d4ed8; }
.cv__count { font-size: 12px; font-weight: 700; color: #1f2937; text-align: right; }
.cv__hint { color: #64748b; font-size: 11.5px; margin: 8px 0 0; line-height: 1.4; }
</style>
