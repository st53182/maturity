<template>
  <div class="is-session">
    <div v-if="reportFailed" class="is-session__empty is-session__empty--err">
      <p>{{ store.error || $t('interviewSimulator.sessionReportFailed') }}</p>
      <button type="button" class="is-retry" :disabled="store.loading" @click="retryReport">
        {{ store.loading ? $t('interviewSimulator.loading') : $t('interviewSimulator.retryReport') }}
      </button>
      <router-link to="/new/interview-simulator/setup" class="is-a is-a--block">{{ $t('interviewSimulator.backToSetup') }}</router-link>
    </div>

    <div v-else-if="!hasQuestion" class="is-session__empty">
      <p>{{ $t('interviewSimulator.noActiveInterview') }}</p>
      <router-link to="/new/interview-simulator/setup" class="is-a">{{ $t('interviewSimulator.goToSetup') }}</router-link>
    </div>

    <template v-else>
      <header class="is-session__bar">
        <router-link to="/new/interview-simulator/setup" class="is-a" @click.prevent="confirmLeave">{{ $t('interviewSimulator.exit') }}</router-link>
        <span class="is-session__meta">{{ roleLabel }} · {{ levelLabel }}</span>
      </header>

      <ProgressIndicator :completed="store.interviewerTurnsCount" :max="store.maxQuestions" />

      <div class="is-session__layout">
        <div class="is-session__main">
          <QuestionCard :question="store.currentQuestion" :isFollowUp="store.lastQuestionIsFollowUp" />
          <InterviewControls
            :disabled="store.loading || store.interviewComplete"
            :submit-label="$t('interviewSimulator.submitAnswer')"
            @submit="onSubmit"
          />
          <p v-if="store.error" class="is-err">{{ store.error }}</p>
          <p v-if="store.loading" class="is-loading">{{ $t('interviewSimulator.working') }}</p>
        </div>
        <TranscriptPanel :messages="store.transcript" />
      </div>
    </template>
  </div>
</template>

<script>
import { mapStores } from 'pinia';
import { useInterviewSimulatorStore } from '@/stores/interviewSimulator';
import QuestionCard from '@/features/interviewSimulator/components/QuestionCard.vue';
import TranscriptPanel from '@/features/interviewSimulator/components/TranscriptPanel.vue';
import InterviewControls from '@/features/interviewSimulator/components/InterviewControls.vue';
import ProgressIndicator from '@/features/interviewSimulator/components/ProgressIndicator.vue';

export default {
  name: 'InterviewSimulatorSession',
  components: {
    QuestionCard,
    TranscriptPanel,
    InterviewControls,
    ProgressIndicator,
  },
  computed: {
    ...mapStores(useInterviewSimulatorStore),
    store() {
      return this.interviewSimulatorStore;
    },
    reportFailed() {
      return this.store.interviewComplete && !this.store.finalReport && !!this.store.error;
    },
    hasQuestion() {
      if (this.reportFailed) return false;
      return !!(this.store.currentQuestion || this.store.loading);
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
  },
  methods: {
    async onSubmit(text) {
      const res = await this.store.submitAnswer(text);
      if (res && res.done && !res.error) {
        this.$router.push({ name: 'InterviewSimulatorResults' });
      }
    },
    async retryReport() {
      await this.store.loadFinalReport();
      if (this.store.finalReport && !this.store.error) {
        this.$router.push({ name: 'InterviewSimulatorResults' });
      }
    },
    confirmLeave() {
      if (this.store.rounds.length && !this.store.interviewComplete) {
        if (!window.confirm(this.$t('interviewSimulator.confirmLeave'))) return;
      }
      this.store.reset();
      this.$router.push('/new/interview-simulator/setup');
    },
  },
};
</script>

<style scoped>
.is-session {
  max-width: 960px;
  margin: 0 auto;
  padding: 20px 16px 40px;
}
.is-session__bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.is-session__meta {
  font-size: 0.85rem;
  color: var(--vl-muted, #5d6b8a);
}
.is-a {
  color: #2754c7;
  font-size: 0.9rem;
  text-decoration: none;
}
.is-session__layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  margin-top: 20px;
}
@media (max-width: 800px) {
  .is-session__layout {
    grid-template-columns: 1fr;
  }
}
.is-err {
  color: #c0392b;
  font-size: 0.9rem;
  margin-top: 12px;
}
.is-loading {
  font-size: 0.85rem;
  color: var(--vl-muted, #5d6b8a);
  margin-top: 8px;
}
.is-session__empty {
  text-align: center;
  padding: 48px 16px;
  color: var(--vl-muted, #5d6b8a);
}
.is-session__empty--err {
  color: var(--vl-text, #0d1733);
}
.is-retry {
  margin-top: 16px;
  padding: 10px 20px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}
.is-retry:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.is-a--block {
  display: inline-block;
  margin-top: 16px;
}
</style>
