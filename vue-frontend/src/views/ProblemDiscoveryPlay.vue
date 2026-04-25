<template>
  <div class="pd-play">
    <div class="pd-play__toolbar">
      <router-link to="/agile-training" class="pd-play__back">← {{ $t('agileTraining.hub.backHome') }}</router-link>
      <div class="pd-lang" role="group" :aria-label="$t('agileTraining.common.language')">
        <button type="button" class="pd-lang__btn" :class="{ 'pd-lang__btn--active': locale === 'ru' }" @click="setLocale('ru')">RU</button>
        <button type="button" class="pd-lang__btn" :class="{ 'pd-lang__btn--active': locale === 'en' }" @click="setLocale('en')">EN</button>
      </div>
    </div>

    <header class="pd-play__head">
      <h1>{{ $t('agileTraining.problemDiscovery.title') }}</h1>
      <p class="pd-play__lead">{{ $t('agileTraining.problemDiscovery.lead') }}</p>
      <p v-if="serverMock" class="pd-play__mock">{{ $t('agileTraining.problemDiscovery.mockHint') }}</p>
    </header>

    <div v-if="!started" class="pd-play__start">
      <p class="pd-play__hint">{{ $t('agileTraining.problemDiscovery.startHint') }}</p>
      <button type="button" class="pd-play__btn pd-play__btn--primary" :disabled="loading" @click="beginInterview">
        {{ loading ? $t('agileTraining.common.loading') : $t('agileTraining.problemDiscovery.start') }}
      </button>
      <p v-if="error" class="pd-play__err">{{ error }}</p>
    </div>

    <template v-else>
      <div class="pd-play__layout">
        <div class="pd-play__main">
          <QuestionCard
            :question="lastAssistantText"
            :is-follow-up="false"
            :hide-follow-up-badge="true"
            :kicker-key="'agileTraining.problemDiscovery.currentReplyKicker'"
          />
          <InterviewControls
            :disabled="loading || dialogueComplete"
            :submit-label="$t('agileTraining.problemDiscovery.sendQuestion')"
            @submit="onSubmitQuestion"
          />
          <p v-if="error" class="pd-play__err">{{ error }}</p>
          <p v-if="loading" class="pd-play__loading">{{ $t('agileTraining.problemDiscovery.thinking') }}</p>
          <p v-if="dialogueComplete" class="pd-play__done">{{ $t('agileTraining.problemDiscovery.dialogueComplete') }}</p>

          <div class="pd-play__actions">
            <button type="button" class="pd-play__btn pd-play__btn--ghost" :disabled="loading || !messages.length" @click="resetAll">
              {{ $t('agileTraining.problemDiscovery.reset') }}
            </button>
            <button
              type="button"
              class="pd-play__btn pd-play__btn--primary"
              :disabled="loading || synthesizing || !messages.length"
              @click="runSynthesis"
            >
              {{ synthesizing ? $t('agileTraining.problemDiscovery.synthesizing') : $t('agileTraining.problemDiscovery.synthesize') }}
            </button>
          </div>

          <section v-if="synthesis" class="pd-play__synth">
            <h2>{{ $t('agileTraining.problemDiscovery.synthesisTitle') }}</h2>
            <p class="pd-play__summary">{{ synthesis.summary }}</p>
            <div v-if="(synthesis.facts || []).length" class="pd-play__block">
              <h3>{{ $t('agileTraining.problemDiscovery.facts') }}</h3>
              <ul>
                <li v-for="(f, i) in synthesis.facts" :key="'f' + i">{{ f }}</li>
              </ul>
            </div>
            <div v-if="(synthesis.pain_points || []).length" class="pd-play__block">
              <h3>{{ $t('agileTraining.problemDiscovery.pains') }}</h3>
              <ul>
                <li v-for="(p, i) in synthesis.pain_points" :key="'p' + i">{{ p }}</li>
              </ul>
            </div>
            <div v-if="(synthesis.constraints || []).length" class="pd-play__block">
              <h3>{{ $t('agileTraining.problemDiscovery.constraints') }}</h3>
              <ul>
                <li v-for="(c, i) in synthesis.constraints" :key="'c' + i">{{ c }}</li>
              </ul>
            </div>
            <div v-if="(synthesis.open_questions || []).length" class="pd-play__block">
              <h3>{{ $t('agileTraining.problemDiscovery.openQuestions') }}</h3>
              <ul>
                <li v-for="(q, i) in synthesis.open_questions" :key="'q' + i">{{ q }}</li>
              </ul>
            </div>
          </section>
        </div>
        <TranscriptPanel
          :messages="messages"
          :user-label="$t('agileTraining.problemDiscovery.labelYou')"
          :assistant-label="$t('agileTraining.problemDiscovery.labelUser')"
        />
      </div>
    </template>
  </div>
</template>

<script>
import axios from 'axios';
import QuestionCard from '@/features/interviewSimulator/components/QuestionCard.vue';
import TranscriptPanel from '@/features/interviewSimulator/components/TranscriptPanel.vue';
import InterviewControls from '@/features/interviewSimulator/components/InterviewControls.vue';

export default {
  name: 'ProblemDiscoveryPlay',
  components: { QuestionCard, TranscriptPanel, InterviewControls },
  data() {
    return {
      locale: 'ru',
      started: false,
      loading: false,
      synthesizing: false,
      error: null,
      serverMock: false,
      messages: [],
      dialogueComplete: false,
      synthesis: null,
    };
  },
  computed: {
    lastAssistantText() {
      for (let i = this.messages.length - 1; i >= 0; i -= 1) {
        if (this.messages[i].role === 'assistant') return this.messages[i].content || '';
      }
      return '';
    },
  },
  mounted() {
    this.initLocale();
    this.checkHealth();
  },
  methods: {
    initLocale() {
      try {
        const s = localStorage.getItem('language');
        if (s === 'en' || s === 'ru') this.locale = s;
      } catch (_e) {
        /* ignore */
      }
    },
    setLocale(lang) {
      this.locale = lang;
      this.$i18n.locale = lang;
      try {
        localStorage.setItem('language', lang);
      } catch (_e) {
        /* ignore */
      }
    },
    async checkHealth() {
      try {
        const { data } = await axios.get('/api/problem-discovery/health');
        this.serverMock = !!data.mock;
      } catch {
        this.serverMock = false;
      }
    },
    async beginInterview() {
      this.error = null;
      this.loading = true;
      this.synthesis = null;
      try {
        await this.checkHealth();
        const { data } = await axios.post('/api/problem-discovery/reply', {
          messages: [],
          locale: this.locale,
        });
        if (!data.success) throw new Error(data.error || 'reply failed');
        this.messages = [{ role: 'assistant', content: data.reply }];
        this.dialogueComplete = !!data.dialogue_complete;
        this.started = true;
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
      } finally {
        this.loading = false;
      }
    },
    async onSubmitQuestion(text) {
      if (!text.trim() || this.dialogueComplete) return;
      this.error = null;
      this.messages = [...this.messages, { role: 'user', content: text.trim() }];
      this.loading = true;
      this.synthesis = null;
      try {
        const { data } = await axios.post('/api/problem-discovery/reply', {
          messages: this.messages,
          locale: this.locale,
        });
        if (!data.success) throw new Error(data.error || 'reply failed');
        this.messages = [...this.messages, { role: 'assistant', content: data.reply }];
        this.dialogueComplete = !!data.dialogue_complete;
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
        if (this.messages.length && this.messages[this.messages.length - 1].role === 'user') {
          this.messages = this.messages.slice(0, -1);
        }
      } finally {
        this.loading = false;
      }
    },
    async runSynthesis() {
      this.error = null;
      this.synthesizing = true;
      try {
        const { data } = await axios.post('/api/problem-discovery/synthesize', {
          messages: this.messages,
          locale: this.locale,
        });
        if (!data.success) throw new Error(data.error || 'synthesize failed');
        this.synthesis = data.synthesis || null;
      } catch (e) {
        this.error = e instanceof Error ? e.message : String(e);
      } finally {
        this.synthesizing = false;
      }
    },
    resetAll() {
      if (this.messages.length && !window.confirm(this.$t('agileTraining.problemDiscovery.confirmReset'))) return;
      this.started = false;
      this.messages = [];
      this.dialogueComplete = false;
      this.synthesis = null;
      this.error = null;
    },
  },
};
</script>

<style scoped>
.pd-play {
  max-width: 980px;
  margin: 0 auto;
  padding: 20px 16px 48px;
}
.pd-play__toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.pd-play__back {
  color: #2754c7;
  text-decoration: none;
  font-size: 0.9rem;
}
.pd-lang {
  display: flex;
  gap: 6px;
}
.pd-lang__btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid #d8e0f0;
  background: #fff;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.8rem;
}
.pd-lang__btn--active {
  background: #142b66;
  color: #fff;
  border-color: #142b66;
}
.pd-play__head h1 {
  margin: 0 0 8px;
  font-size: 1.45rem;
  color: #0d1733;
}
.pd-play__lead {
  margin: 0;
  color: #5d6b8a;
  line-height: 1.5;
  max-width: 52rem;
}
.pd-play__mock {
  margin-top: 12px;
  padding: 10px 14px;
  background: #fff8e6;
  border: 1px solid #f0d78c;
  border-radius: 10px;
  font-size: 0.88rem;
  color: #6a5a1e;
}
.pd-play__start {
  margin-top: 28px;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #d8e0f0;
  background: #fafbff;
}
.pd-play__hint {
  margin: 0 0 16px;
  color: #5d6b8a;
}
.pd-play__btn {
  padding: 10px 20px;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  font-size: 0.9rem;
}
.pd-play__btn--primary {
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
}
.pd-play__btn--primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pd-play__btn--ghost {
  background: #eff3fb;
  color: #5d6b8a;
  border: 1px solid #d8e0f0;
}
.pd-play__btn--ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pd-play__err {
  color: #c0392b;
  margin-top: 12px;
  font-size: 0.9rem;
}
.pd-play__layout {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 20px;
  margin-top: 20px;
}
@media (max-width: 800px) {
  .pd-play__layout {
    grid-template-columns: 1fr;
  }
}
.pd-play__loading {
  font-size: 0.85rem;
  color: #5d6b8a;
  margin-top: 8px;
}
.pd-play__done {
  margin-top: 12px;
  padding: 10px 14px;
  background: #eef7ee;
  border: 1px solid #b8d4b8;
  border-radius: 10px;
  font-size: 0.88rem;
  color: #2d5a2d;
}
.pd-play__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 20px;
}
.pd-play__synth {
  margin-top: 28px;
  padding: 20px 22px;
  border-radius: 16px;
  border: 1px solid #d8e0f0;
  background: #fff;
}
.pd-play__synth h2 {
  margin: 0 0 12px;
  font-size: 1.1rem;
}
.pd-play__summary {
  margin: 0 0 16px;
  line-height: 1.5;
  color: #0d1733;
}
.pd-play__block {
  margin-top: 14px;
}
.pd-play__block h3 {
  margin: 0 0 8px;
  font-size: 0.95rem;
  color: #2754c7;
}
.pd-play__block ul {
  margin: 0;
  padding-left: 1.2rem;
  color: #0d1733;
  line-height: 1.45;
}
</style>
