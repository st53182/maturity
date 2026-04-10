<template>
  <div class="is-page">
    <header class="is-page__head">
      <router-link to="/new/interview-simulator" class="is-link">{{ $t('interviewSimulator.setupBack') }}</router-link>
      <h1>{{ $t('interviewSimulator.setupTitle') }}</h1>
    </header>

    <RoleSelector v-model="role" :label="$t('interviewSimulator.labelRole')" />
    <LevelSelector v-model="level" :label="$t('interviewSimulator.labelLevel')" class="is-spaced" />

    <JobDescriptionInput
      v-model="jobDescription"
      class="is-spaced"
      :label="$t('interviewSimulator.jdLabel')"
      :hint="$t('interviewSimulator.jdHint')"
      :placeholder="$t('interviewSimulator.jdPlaceholder')"
    />

    <p v-if="serverHint" class="is-hint">{{ serverHint }}</p>
    <p v-if="error" class="is-error">{{ error }}</p>

    <div class="is-actions">
      <button type="button" class="is-btn is-btn--primary" :disabled="starting" @click="start">
        {{ starting ? $t('interviewSimulator.starting') : $t('interviewSimulator.startInterview') }}
      </button>
    </div>
  </div>
</template>

<script>
import RoleSelector from '@/features/interviewSimulator/components/RoleSelector.vue';
import LevelSelector from '@/features/interviewSimulator/components/LevelSelector.vue';
import JobDescriptionInput from '@/features/interviewSimulator/components/JobDescriptionInput.vue';
import { useInterviewSimulatorStore } from '@/stores/interviewSimulator';
import { canStartSession } from '@/features/interviewSimulator/services/interviewEngine';

export default {
  name: 'InterviewSimulatorSetup',
  components: { RoleSelector, LevelSelector, JobDescriptionInput },
  data() {
    return {
      role: 'frontend',
      level: 'middle',
      jobDescription: '',
      starting: false,
      error: null,
    };
  },
  computed: {
    serverHint() {
      const s = useInterviewSimulatorStore();
      return s.serverMock ? this.$t('interviewSimulator.serverMockHint') : '';
    },
  },
  async mounted() {
    const s = useInterviewSimulatorStore();
    await s.checkHealth();
  },
  methods: {
    async start() {
      this.error = null;
      const loc =
        typeof this.$i18n.locale === 'string' ? this.$i18n.locale : this.$i18n.locale.value;
      const state = {
        role: this.role,
        level: this.level,
        jobDescription: this.jobDescription,
        locale: loc,
      };
      if (!canStartSession(state)) {
        this.error = this.$t('interviewSimulator.errSelectRoleLevel');
        return;
      }
      this.starting = true;
      const store = useInterviewSimulatorStore();
      store.reset();
      store.setConfig(state);
      await store.bootstrapFirstQuestion();
      this.starting = false;
      if (store.error) {
        this.error = store.error;
        return;
      }
      this.$router.push({ name: 'InterviewSimulatorSession' });
    },
  },
};
</script>

<style scoped>
.is-page {
  max-width: 640px;
  margin: 0 auto;
  padding: 28px 20px 48px;
  text-align: left;
}
.is-page__head h1 {
  margin: 10px 0 20px;
  font-size: 1.5rem;
}
.is-link {
  color: #2754c7;
  text-decoration: none;
  font-size: 0.9rem;
}
.is-spaced {
  margin-top: 22px;
}
.is-hint {
  margin-top: 16px;
  font-size: 0.85rem;
  color: #2754c7;
}
.is-error {
  margin-top: 12px;
  color: #c0392b;
  font-size: 0.9rem;
}
.is-actions {
  margin-top: 28px;
}
.is-btn {
  border: none;
  border-radius: 12px;
  padding: 12px 24px;
  font-weight: 600;
  cursor: pointer;
  font-size: 0.95rem;
}
.is-btn--primary {
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
}
.is-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
