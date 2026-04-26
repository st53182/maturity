<template>
  <div class="pmchart">
    <div class="pmchart__head">
      <span class="pmchart__label">{{ label }}</span>
      <span class="pmchart__value" v-if="last !== null">{{ formattedLast }}</span>
    </div>
    <svg :viewBox="`0 0 ${vbW} ${vbH}`" class="pmchart__svg" preserveAspectRatio="none">
      <line x1="0" :y1="vbH-1" :x2="vbW" :y2="vbH-1" stroke="#e2e8f0" stroke-width="1" />
      <line :x1="0" :y1="vbH/2" :x2="vbW" :y2="vbH/2" stroke="#f1f5f9" stroke-width="1" />
      <polyline
        v-if="points.length > 1"
        :points="polyline"
        :stroke="color"
        stroke-width="2"
        fill="none"
      />
      <circle
        v-for="(pt, i) in points"
        :key="i"
        :cx="pt.x" :cy="pt.y" r="2.5"
        :fill="color"
      />
    </svg>
  </div>
</template>

<script>
export default {
  name: 'PmSimChart',
  props: {
    data: { type: Array, default: () => [] },
    field: { type: String, required: true },
    label: { type: String, default: '' },
    color: { type: String, default: '#6366f1' },
    totalWeeks: { type: Number, default: 20 },
    max: { type: Number, default: 0 },
  },
  data() { return { vbW: 280, vbH: 80 }; },
  computed: {
    series() {
      return (this.data || []).map((d) => ({
        week: Number(d.week) || 0,
        v: Number(d[this.field]) || 0,
      }));
    },
    last() {
      if (!this.series.length) return null;
      return this.series[this.series.length - 1].v;
    },
    formattedLast() {
      const v = this.last;
      if (v === null) return '';
      if (Math.abs(v) >= 1000) return (v / 1000).toFixed(v >= 10000 ? 0 : 1) + 'k';
      return Math.round(v);
    },
    yMax() {
      if (this.max) return this.max;
      const m = Math.max(...this.series.map((p) => p.v), 1);
      return Math.ceil(m * 1.1);
    },
    points() {
      const w = this.vbW;
      const h = this.vbH;
      const total = Math.max(this.totalWeeks, 1);
      return this.series.map((p) => ({
        x: (p.week / total) * w,
        y: h - (Math.min(p.v, this.yMax) / this.yMax) * (h - 4) - 2,
      }));
    },
    polyline() {
      return this.points.map((p) => `${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    },
  },
};
</script>

<style scoped>
.pmchart { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 8px 10px; }
.pmchart__head { display: flex; justify-content: space-between; font-size: 12px; color: #475569; margin-bottom: 4px; }
.pmchart__value { font-weight: 700; color: #0f172a; }
.pmchart__svg { width: 100%; height: 70px; display: block; }
</style>
