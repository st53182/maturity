<template>
  <div class="is-prog">
    <div class="is-prog__labels">
      <span>{{ $t('interviewSimulator.progressLabel') }}</span>
      <span>{{ $t('interviewSimulator.progressTurns', { done: completed, max }) }}</span>
    </div>
    <div class="is-prog__track" role="progressbar" :aria-valuenow="completed" :aria-valuemax="max">
      <div class="is-prog__fill" :style="{ width: pct + '%' }" />
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProgressIndicator',
  props: {
    completed: { type: Number, default: 0 },
    max: { type: Number, default: 13 },
  },
  computed: {
    pct() {
      if (!this.max) return 0;
      return Math.min(100, Math.round((this.completed / this.max) * 100));
    },
  },
};
</script>

<style scoped>
.is-prog__labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.8rem;
  color: var(--vl-muted, #5d6b8a);
  margin-bottom: 6px;
}
.is-prog__track {
  height: 8px;
  background: #e8ecf5;
  border-radius: 999px;
  overflow: hidden;
}
.is-prog__fill {
  height: 100%;
  background: linear-gradient(90deg, #142b66, #2754c7);
  border-radius: 999px;
  transition: width 0.25s ease;
}
</style>
