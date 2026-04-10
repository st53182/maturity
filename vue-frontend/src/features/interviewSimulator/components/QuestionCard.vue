<template>
  <section class="is-card" aria-live="polite">
    <div class="is-card__head">
      <div>
        <div class="is-card__kicker">{{ $t('interviewSimulator.currentQuestion') }}</div>
        <h2 class="is-card__title">{{ question || '—' }}</h2>
        <div v-if="isFollowUp" class="is-badge">{{ $t('interviewSimulator.followUpBadge') }}</div>
      </div>
      <button
        v-if="readAloudSupported && question"
        type="button"
        class="is-card__speak"
        :class="{ 'is-card__speak--active': speaking }"
        :aria-pressed="speaking"
        :disabled="!question.trim()"
        @click="toggleSpeak"
      >
        {{ speaking ? $t('interviewSimulator.readQuestionStop') : $t('interviewSimulator.readQuestion') }}
      </button>
    </div>
  </section>
</template>

<script>
export default {
  name: 'QuestionCard',
  props: {
    question: { type: String, default: '' },
    isFollowUp: { type: Boolean, default: false },
  },
  data() {
    return { speaking: false };
  },
  computed: {
    readAloudSupported() {
      return typeof window !== 'undefined' && !!window.speechSynthesis;
    },
    utteranceLang() {
      const raw = this.$i18n?.locale;
      const loc = typeof raw === 'string' ? raw : raw?.value;
      const s = String(loc || 'ru').toLowerCase();
      return s.startsWith('en') ? 'en-US' : 'ru-RU';
    },
  },
  watch: {
    question() {
      this.stopSpeak();
    },
  },
  beforeUnmount() {
    this.stopSpeak();
  },
  methods: {
    stopSpeak() {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      this.speaking = false;
    },
    toggleSpeak() {
      if (this.speaking) {
        this.stopSpeak();
        return;
      }
      const q = (this.question || '').trim();
      if (!q || typeof window === 'undefined' || !window.speechSynthesis) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(q);
      u.lang = this.utteranceLang;
      u.onend = () => {
        this.speaking = false;
      };
      u.onerror = () => {
        this.speaking = false;
      };
      this.speaking = true;
      window.speechSynthesis.speak(u);
    },
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
.is-card__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
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
.is-card__speak {
  flex-shrink: 0;
  padding: 8px 14px;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 10px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background: #fff;
  color: #2754c7;
  cursor: pointer;
}
.is-card__speak:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.is-card__speak--active {
  background: rgba(39, 84, 199, 0.12);
  border-color: rgba(39, 84, 199, 0.4);
}
</style>
