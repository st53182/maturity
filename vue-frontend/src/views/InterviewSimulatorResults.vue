<template>
  <div class="is-results">
    <header class="is-results__head">
      <router-link to="/new/interview-simulator" class="is-a">{{ $t('interviewSimulator.resultsBackHome') }}</router-link>
      <h1>{{ $t('interviewSimulator.resultsTitle') }}</h1>
      <p v-if="isProblem" class="is-results__meta">{{ personaLabel }}<span v-if="topicSnippet"> — {{ topicSnippet }}</span></p>
      <p v-else-if="store.role" class="is-results__meta">{{ roleLabel }} · {{ levelLabel }}</p>
    </header>

    <div v-if="!store.finalReport && store.error" class="is-results__empty">
      <p>{{ store.error }}</p>
      <router-link to="/new/interview-simulator/setup" class="is-btn">{{ $t('interviewSimulator.tryAgain') }}</router-link>
    </div>

    <div v-else-if="!store.finalReport" class="is-results__empty">
      <p>{{ $t('interviewSimulator.noReportYet') }}</p>
      <router-link to="/new/interview-simulator/setup" class="is-btn">{{ $t('interviewSimulator.startSetup') }}</router-link>
    </div>

    <template v-else>
      <FeedbackCard :report="store.finalReport" :is-problem-mode="isProblem" />
      <ScoreBreakdown :scores="store.finalReport.category_scores" :is-problem-mode="isProblem" />
      <div class="is-results__actions">
        <button type="button" class="is-btn is-btn--primary" @click="newInterview">{{ $t('interviewSimulator.newInterview') }}</button>
        <router-link to="/new/interview-simulator" class="is-btn is-btn--ghost">{{ $t('interviewSimulator.simulatorHome') }}</router-link>
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
    roleLabel() {
      const k = `interviewSimulator.roles.${this.store.role}`;
      const t = this.$t(k);
      return t !== k ? t : this.store.role;
    },
    levelLabel() {
      const k = `interviewSimulator.levels.${this.store.level}`;
      const t = this.$t(k);
      return t !== k ? t : this.store.level;
    },
    isProblem() {
      return this.store.interviewMode === 'problem_user';
    },
    personaLabel() {
      const k = `interviewSimulator.personas.${this.store.persona}`;
      const t = this.$t(k);
      return t !== k ? t : this.store.persona;
    },
    topicSnippet() {
      const j = (this.store.jobDescription || '').trim();
      if (!j) return '';
      return j.length > 80 ? `${j.slice(0, 80)}…` : j;
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
