<template>
  <div v-if="scores && Object.keys(scores).length" class="is-scores">
    <h3 class="is-scores__title">Scores by category</h3>
    <div v-for="(val, key) in scores" :key="key" class="is-scores__row">
      <span class="is-scores__label">{{ formatKey(key) }}</span>
      <div class="is-scores__bar">
        <div class="is-scores__fill" :style="{ width: val + '%' }" />
      </div>
      <span class="is-scores__num">{{ val }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ScoreBreakdown',
  props: {
    scores: { type: Object, default: null },
  },
  methods: {
    formatKey(k) {
      return String(k)
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());
    },
  },
};
</script>

<style scoped>
.is-scores {
  margin-top: 24px;
  padding: 20px;
  border-radius: 16px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background: #fff;
  text-align: left;
}
.is-scores__title {
  margin: 0 0 16px;
  font-size: 1rem;
}
.is-scores__row {
  display: grid;
  grid-template-columns: 140px 1fr 40px;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
  font-size: 0.85rem;
}
.is-scores__label {
  color: var(--vl-muted, #5d6b8a);
}
.is-scores__bar {
  height: 8px;
  background: #e8ecf5;
  border-radius: 999px;
  overflow: hidden;
}
.is-scores__fill {
  height: 100%;
  background: linear-gradient(90deg, #142b66, #2754c7);
  border-radius: 999px;
}
.is-scores__num {
  text-align: right;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
}
@media (max-width: 520px) {
  .is-scores__row {
    grid-template-columns: 1fr;
  }
  .is-scores__num {
    text-align: left;
  }
}
</style>
