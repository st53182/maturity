<template>
  <section class="is-card" aria-live="polite">
    <div class="is-card__kicker">Current question</div>
    <h2 class="is-card__title">{{ question || '—' }}</h2>
    <div v-if="isFollowUp" class="is-badge">Follow-up</div>
  </section>
</template>

<script>
export default {
  name: 'QuestionCard',
  props: {
    question: { type: String, default: '' },
    isFollowUp: { type: Boolean, default: false },
  },
};
</script>

<style scoped>
.is-card {
  background: linear-gradient(180deg, #fff 0%, #f7f9ff 100%);
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 16px;
  padding: 22px 24px;
  box-shadow: 0 12px 40px rgba(20, 43, 102, 0.08);
}
.is-card__kicker {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--vl-muted, #5d6b8a);
  margin-bottom: 8px;
}
.is-card__title {
  margin: 0;
  font-size: 1.15rem;
  line-height: 1.45;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
}
.is-badge {
  display: inline-block;
  margin-top: 12px;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(39, 84, 199, 0.1);
  color: #2754c7;
  font-weight: 600;
}
</style>
