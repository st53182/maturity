<template>
  <div class="disc-page">
    <div class="disc-page__bg" aria-hidden="true">
      <div class="disc-page__orb disc-page__orb--1" />
      <div class="disc-page__orb disc-page__orb--2" />
    </div>
    <NewToolShell :title="$t('disc.title')" :subtitle="$t('disc.description')">
      <div v-if="!showResults" class="disc-body">
        <div v-if="!assessmentStarted" class="disc-card disc-card--intro">
          <h2 class="disc-card__h">{{ $t('disc.introTitle') }}</h2>
          <p class="disc-card__lead">{{ $t('disc.introLead') }}</p>
          <ul class="disc-list">
            <li>{{ $t('disc.introBullet1') }}</li>
            <li>{{ $t('disc.introBullet2') }}</li>
            <li>{{ $t('disc.introBullet3') }}</li>
            <li>{{ $t('disc.introBullet4') }}</li>
          </ul>
          <p class="disc-meta">
            <strong>{{ $t('disc.timeLabel') }}</strong> {{ $t('disc.timeValue') }}
          </p>
          <p class="disc-meta">
            <strong>{{ $t('disc.questionsLabel') }}</strong> {{ $t('disc.questionsValue') }}
          </p>
          <div class="disc-actions">
            <button type="button" class="disc-btn disc-btn--primary" @click="startAssessment">
              {{ $t('disc.startAssessment') }}
            </button>
          </div>
        </div>

        <div v-else class="disc-card disc-card--quiz">
          <div class="disc-progress">
            <div class="disc-progress__bar" :style="{ width: progressPercentage + '%' }" />
          </div>
          <p class="disc-progress__text">
            {{ $t('disc.question') }} {{ currentQuestionIndex + 1 }} {{ $t('disc.of') }} {{ questions.length }}
          </p>

          <div class="disc-question">
            <h3 class="disc-question__title">{{ currentQuestion.question }}</h3>
            <div class="disc-options">
              <button
                v-for="(option, index) in currentQuestion.options"
                :key="index"
                type="button"
                class="disc-option"
                :class="{ 'disc-option--selected': selectedAnswer === option.type }"
                @click="selectAnswer(option)"
              >
                <span class="disc-option__radio" :class="{ 'disc-option__radio--on': selectedAnswer === option.type }" />
                <span class="disc-option__text">{{ option.text }}</span>
              </button>
            </div>
          </div>

          <div class="disc-nav">
            <button type="button" class="disc-btn disc-btn--ghost" :disabled="currentQuestionIndex === 0" @click="previousQuestion">
              {{ $t('disc.previous') }}
            </button>
            <button type="button" class="disc-btn disc-btn--primary" :disabled="!selectedAnswer" @click="nextQuestion">
              {{ currentQuestionIndex === questions.length - 1 ? $t('disc.finish') : $t('disc.next') }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="disc-body">
        <div class="disc-card disc-card--results">
          <h2 class="disc-results__title">{{ $t('disc.results') }}</h2>
          <div class="disc-results__type">
            {{ $t('disc.personalityType') }}:
            <span class="disc-results__badge">{{ results.personality_type }}</span>
          </div>

          <h3 class="disc-results__h">{{ $t('disc.scoresTitle') }}</h3>
          <div class="disc-scores">
            <div v-for="row in scoreRows" :key="row.key" class="disc-score-row">
              <div class="disc-score-row__label">{{ row.label }} ({{ row.letter }})</div>
              <div class="disc-score-row__bar">
                <div class="disc-score-row__fill" :style="{ width: row.pct + '%' }" />
              </div>
              <div class="disc-score-row__val">{{ row.val }}/36</div>
            </div>
          </div>

          <h3 class="disc-results__h">{{ $t('disc.recommendations') }}</h3>
          <div class="disc-rec" v-html="formattedRecommendations" />

          <div class="disc-actions disc-actions--footer">
            <button type="button" class="disc-btn disc-btn--ghost" @click="retakeAssessment">
              {{ $t('disc.startAssessment') }}
            </button>
            <router-link to="/new/profile" class="disc-btn disc-btn--primary disc-btn--link">{{ $t('disc.backProfile') }}</router-link>
          </div>
        </div>
      </div>

      <div v-if="loading" class="disc-loading">
        <div class="disc-loading__spinner" />
        <p>{{ $t('common.loading') }}</p>
      </div>
    </NewToolShell>
  </div>
</template>

<script>
import axios from 'axios';
import NewToolShell from '@/views/NewToolShell.vue';

export default {
  name: 'DISCAssessment',
  components: { NewToolShell },
  data() {
    return {
      assessmentStarted: false,
      questions: [],
      currentQuestionIndex: 0,
      answers: {},
      selectedAnswer: null,
      showResults: false,
      results: null,
      loading: false,
    };
  },
  computed: {
    discApiLang() {
      const loc = this.$i18n.locale;
      const s = typeof loc === 'string' ? loc : loc?.value || 'ru';
      return String(s).toLowerCase().startsWith('en') ? 'en' : 'ru';
    },
    currentQuestion() {
      return this.questions[this.currentQuestionIndex] || {};
    },
    progressPercentage() {
      if (!this.questions.length) return 0;
      return ((this.currentQuestionIndex + 1) / this.questions.length) * 100;
    },
    formattedRecommendations() {
      if (!this.results?.recommendations) return '';
      return this.results.recommendations.replace(/\n/g, '<br>');
    },
    scoreRows() {
      if (!this.results) return [];
      const r = this.results;
      const mk = (key, letter, labelKey) => {
        const val = r[`${key}_score`] ?? 0;
        return {
          key,
          letter,
          label: this.$t(labelKey),
          val,
          pct: Math.min(100, (val / 36) * 100),
        };
      };
      return [
        mk('dominance', 'D', 'disc.dominance'),
        mk('influence', 'I', 'disc.influence'),
        mk('steadiness', 'S', 'disc.steadiness'),
        mk('conscientiousness', 'C', 'disc.conscientiousness'),
      ];
    },
  },
  watch: {
    discApiLang() {
      if (!this.assessmentStarted && !this.showResults) {
        this.loadQuestions();
      }
    },
  },
  async mounted() {
    await this.loadQuestions();
  },
  methods: {
    async loadQuestions() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/disc/questions', {
          params: { lang: this.discApiLang },
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.data.success) {
          this.questions = response.data.questions;
        } else if (this.$toast) {
          this.$toast.error(this.$t('disc.errorLoading'));
        }
      } catch (error) {
        console.error('Error loading questions:', error);
        if (this.$toast) {
          this.$toast.error(this.$t('disc.errorLoading'));
        }
      }
    },
    startAssessment() {
      this.assessmentStarted = true;
      this.currentQuestionIndex = 0;
      this.answers = {};
      this.selectedAnswer = this.answers[this.currentQuestion.id] || null;
    },
    selectAnswer(option) {
      this.selectedAnswer = option.type;
    },
    nextQuestion() {
      if (!this.selectedAnswer) return;

      this.answers[this.currentQuestion.id] = this.selectedAnswer;

      if (this.currentQuestionIndex === this.questions.length - 1) {
        this.submitAssessment();
      } else {
        this.currentQuestionIndex++;
        this.selectedAnswer = this.answers[this.currentQuestion.id] || null;
      }
    },
    previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--;
        this.selectedAnswer = this.answers[this.currentQuestion.id] || null;
      }
    },
    async submitAssessment() {
      this.loading = true;
      try {
        const token = localStorage.getItem('token');
        const response = await axios.post(
          '/api/disc/submit',
          {
            answers: this.answers,
            lang: this.discApiLang,
          },
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        if (response.data.success) {
          this.results = response.data.assessment;
          this.showResults = true;
          if (this.$toast) {
            this.$toast.success(this.$t('disc.submitSuccess'));
          }
        } else if (this.$toast) {
          this.$toast.error(this.$t('disc.errorSubmitting'));
        }
      } catch (error) {
        console.error('Error submitting assessment:', error);
        if (this.$toast) {
          this.$toast.error(this.$t('disc.errorSubmitting'));
        }
      } finally {
        this.loading = false;
      }
    },
    retakeAssessment() {
      this.assessmentStarted = false;
      this.showResults = false;
      this.answers = {};
      this.selectedAnswer = null;
      this.currentQuestionIndex = 0;
      this.results = null;
    },
  },
};
</script>

<style scoped>
.disc-page {
  position: relative;
  min-height: calc(100vh - 24px);
  color: rgba(10, 20, 45, 0.92);
}

.disc-page__bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
  z-index: 0;
}

.disc-page__orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(48px);
  opacity: 0.55;
}

.disc-page__orb--1 {
  width: 420px;
  height: 420px;
  left: -120px;
  top: -80px;
  background: radial-gradient(circle at 30% 30%, rgba(98, 70, 255, 0.35), transparent 62%);
}

.disc-page__orb--2 {
  width: 380px;
  height: 380px;
  right: -100px;
  top: 40px;
  background: radial-gradient(circle at 35% 35%, rgba(0, 194, 255, 0.28), transparent 60%);
}

.disc-page :deep(.new-tool-shell) {
  position: relative;
  z-index: 1;
}

.disc-body {
  margin-top: 4px;
}

.disc-card {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(175deg, rgba(255, 255, 255, 0.96), rgba(246, 249, 255, 0.88));
  box-shadow: 0 22px 70px rgba(10, 20, 45, 0.1);
  padding: 22px 20px 24px;
}

.disc-card--intro {
  text-align: center;
}

.disc-card__h {
  margin: 0 0 10px;
  font-size: 1.15rem;
  font-weight: 700;
  color: rgba(10, 20, 45, 0.94);
}

.disc-card__lead {
  margin: 0;
  color: rgba(10, 20, 45, 0.68);
  font-size: 15px;
}

.disc-list {
  text-align: left;
  max-width: 520px;
  margin: 16px auto;
  padding-left: 1.2rem;
  color: rgba(10, 20, 45, 0.78);
  line-height: 1.5;
  font-size: 14px;
}

.disc-meta {
  margin: 8px 0;
  font-size: 14px;
  color: rgba(10, 20, 45, 0.72);
}

.disc-actions {
  margin-top: 20px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.disc-actions--footer {
  justify-content: center;
}

.disc-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 12px 18px;
  border-radius: 14px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: 1px solid rgba(10, 20, 45, 0.12);
  background: rgba(255, 255, 255, 0.9);
  color: rgba(10, 20, 45, 0.9);
  text-decoration: none;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.disc-btn:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.disc-btn--primary {
  border-color: rgba(32, 90, 255, 0.55);
  color: #fff;
  background: linear-gradient(135deg, #365cff 0%, #2a7dff 55%, #14b8ff 100%);
  box-shadow: 0 12px 28px rgba(41, 84, 255, 0.22);
}

.disc-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 16px 34px rgba(41, 84, 255, 0.28);
}

.disc-btn--ghost:hover:not(:disabled) {
  border-color: rgba(32, 90, 255, 0.28);
  background: rgba(255, 255, 255, 0.98);
}

.disc-btn--link {
  box-sizing: border-box;
}

.disc-progress {
  height: 8px;
  background: rgba(10, 20, 45, 0.08);
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 10px;
}

.disc-progress__bar {
  height: 100%;
  background: linear-gradient(90deg, #365cff, #14b8ff);
  transition: width 0.3s ease;
}

.disc-progress__text {
  text-align: center;
  color: rgba(10, 20, 45, 0.58);
  font-size: 13px;
  font-weight: 600;
  margin: 0 0 18px;
}

.disc-question__title {
  margin: 0 0 16px;
  font-size: 1.05rem;
  line-height: 1.45;
  color: rgba(10, 20, 45, 0.92);
}

.disc-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.disc-option {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  text-align: left;
  width: 100%;
  padding: 14px 14px;
  border-radius: 14px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(255, 255, 255, 0.88);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, background 0.2s ease;
  color: inherit;
  font: inherit;
}

.disc-option:hover {
  border-color: rgba(32, 90, 255, 0.28);
}

.disc-option--selected {
  border-color: rgba(32, 90, 255, 0.45);
  background: rgba(239, 246, 255, 0.95);
  box-shadow: 0 8px 24px rgba(32, 90, 255, 0.12);
}

.disc-option__radio {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid rgba(10, 20, 45, 0.2);
  margin-top: 2px;
  flex-shrink: 0;
  position: relative;
}

.disc-option__radio--on {
  border-color: rgba(32, 90, 255, 0.75);
}

.disc-option__radio--on::after {
  content: '';
  position: absolute;
  inset: 3px;
  border-radius: 50%;
  background: linear-gradient(135deg, #365cff, #14b8ff);
}

.disc-option__text {
  font-size: 14px;
  line-height: 1.45;
  color: rgba(10, 20, 45, 0.88);
}

.disc-nav {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-top: 22px;
}

.disc-results__title {
  margin: 0 0 12px;
  font-size: 1.2rem;
}

.disc-results__type {
  font-size: 1rem;
  margin-bottom: 18px;
  color: rgba(10, 20, 45, 0.78);
}

.disc-results__badge {
  display: inline-block;
  margin-left: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 800;
  background: rgba(32, 90, 255, 0.12);
  color: #1d4ed8;
}

.disc-results__h {
  margin: 18px 0 12px;
  font-size: 1.05rem;
}

.disc-scores {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 8px;
}

.disc-score-row {
  display: grid;
  grid-template-columns: minmax(100px, 140px) 1fr 52px;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}

.disc-score-row__label {
  font-weight: 600;
  color: rgba(10, 20, 45, 0.82);
}

.disc-score-row__bar {
  height: 10px;
  background: rgba(10, 20, 45, 0.08);
  border-radius: 999px;
  overflow: hidden;
}

.disc-score-row__fill {
  height: 100%;
  background: linear-gradient(90deg, #365cff, #14b8ff);
  border-radius: 999px;
  transition: width 0.5s ease;
}

.disc-score-row__val {
  text-align: right;
  font-weight: 700;
  color: #2563eb;
}

.disc-rec {
  padding: 16px;
  border-radius: 12px;
  background: rgba(10, 20, 45, 0.04);
  line-height: 1.55;
  font-size: 14px;
  color: rgba(10, 20, 45, 0.85);
}

.disc-loading {
  position: fixed;
  inset: 0;
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(10, 20, 45, 0.35);
  color: #fff;
}

.disc-loading__spinner {
  width: 44px;
  height: 44px;
  border: 3px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: disc-spin 0.9s linear infinite;
  margin-bottom: 12px;
}

@keyframes disc-spin {
  to {
    transform: rotate(360deg);
  }
}

@media (max-width: 640px) {
  .disc-score-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
  .disc-score-row__val {
    text-align: left;
  }
  .disc-nav {
    flex-direction: column;
  }
}
</style>
