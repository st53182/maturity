<template>
  <div class="is-results">
    <header class="is-results__head">
      <router-link to="/new/interview-simulator" class="is-a">← Home</router-link>
      <h1>Interview results</h1>
      <p v-if="store.role" class="is-results__meta">{{ store.role }} · {{ store.level }}</p>
    </header>

    <div v-if="!store.finalReport && store.error" class="is-results__empty">
      <p>{{ store.error }}</p>
      <router-link to="/new/interview-simulator/setup" class="is-btn">Try again</router-link>
    </div>

    <div v-else-if="!store.finalReport" class="is-results__empty">
      <p>No report yet. Complete an interview first.</p>
      <router-link to="/new/interview-simulator/setup" class="is-btn">Start setup</router-link>
    </div>

    <template v-else>
      <FeedbackCard :report="store.finalReport" />
      <ScoreBreakdown :scores="store.finalReport.category_scores" />
      <div class="is-results__actions">
        <button type="button" class="is-btn is-btn--primary" @click="newInterview">New interview</button>
        <router-link to="/new/interview-simulator" class="is-btn is-btn--ghost">Simulator home</router-link>
      </div>
    </template>
  </div>
</template>

<script>
import { mapStores } from 'pinia';
import { useInterviewSimulatorStore } from '@/stores/interviewSimulator';
import FeedbackCard from '@/features/interviewSimulator/components/FeedbackCard.vue';
import ScoreBreakdown from '@/features/interviewSimulator/components/ScoreBreakdown.vue';

export default {
  name: 'InterviewSimulatorResults',
  components: { FeedbackCard, ScoreBreakdown },
  computed: {
    ...mapStores(useInterviewSimulatorStore),
    store() {
      return this.interviewSimulatorStore;
    },
  },
  methods: {
    newInterview() {
      this.interviewSimulatorStore.reset();
      this.$router.push('/new/interview-simulator/setup');
    },
  },
};
</script>

<style scoped>
.is-results {
  max-width: 720px;
  margin: 0 auto;
  padding: 28px 20px 48px;
  text-align: left;
}
.is-results__head h1 {
  margin: 12px 0 6px;
  font-size: 1.5rem;
  color: var(--vl-text, #0d1733);
}
.is-results__meta {
  margin: 0 0 20px;
  font-size: 0.9rem;
  color: var(--vl-muted, #5d6b8a);
}
.is-a {
  color: #2754c7;
  text-decoration: none;
  font-size: 0.9rem;
}
.is-results__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 28px;
}
.is-btn {
  display: inline-block;
  border: none;
  border-radius: 12px;
  padding: 12px 22px;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  text-decoration: none;
  text-align: center;
}
.is-btn--primary {
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
}
.is-btn--ghost {
  background: #fff;
  border: 1px solid var(--vl-border, #d8e0f0);
  color: var(--vl-text, #0d1733);
}
.is-results__empty {
  padding: 32px 0;
  color: var(--vl-muted, #5d6b8a);
}
.is-results__empty .is-btn {
  margin-top: 16px;
  background: #2754c7;
  color: #fff;
}
</style>
