<template>
  <section class="is-card" aria-live="polite">
    <div class="is-card__head">
      <div>
        <div class="is-card__kicker">{{ kickerLabel }}</div>
        <h2 class="is-card__title">{{ question || '—' }}</h2>
        <div v-if="isFollowUp && !hideFollowUpBadge" class="is-badge">{{ $t('interviewSimulator.followUpBadge') }}</div>
        <label v-if="readAloudSupported" class="is-card__auto">
          <input v-model="autoSpeakLocal" type="checkbox" @change="onAutoSpeakChange" />
          <span>{{ $t('interviewSimulator.readQuestionAuto') }}</span>
        </label>
        <p v-if="readAloudSupported" class="is-card__auto-hint">{{ $t('interviewSimulator.readQuestionAutoHint') }}</p>
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
const AUTO_SPEAK_KEY = 'interviewSimulator.autoSpeak';

function loadAutoSpeakPreference() {
  try {
    const v = localStorage.getItem(AUTO_SPEAK_KEY);
    if (v === '0' || v === 'false') return false;
    return true;
  } catch (_e) {
    return true;
  }
}

function saveAutoSpeakPreference(on) {
  try {
    localStorage.setItem(AUTO_SPEAK_KEY, on ? '1' : '0');
  } catch (_e) {
    /* ignore */
  }
}

/** Prefer clearer / neural-style voices when the browser exposes them */
function pickPreferredVoice(voices, langTag) {
  if (!voices || !voices.length) return null;
  const primary = (langTag || 'en-US').split('-')[0].toLowerCase();
  const matchLang = (v) => {
    const L = (v.lang || '').toLowerCase().replace('_', '-');
    return L === primary || L.startsWith(`${primary}-`);
  };
  let list = voices.filter(matchLang);
  if (!list.length) {
    list = voices.filter((v) => (v.lang || '').toLowerCase().startsWith(primary));
  }
  if (!list.length) return null;

  const score = (v) => {
    const n = `${v.name || ''} ${v.voiceURI || ''}`.toLowerCase();
    let s = 0;
    if (/neural|natural|premium|enhanced|online|google|microsoft|apple/i.test(n)) s += 40;
    if (v.localService) s += 25;
    if (v.default) s += 15;
    if (/compact|embedded|low quality/i.test(n)) s -= 30;
    return s;
  };
  list.sort((a, b) => score(b) - score(a));
  return list[0];
}

export default {
  name: 'QuestionCard',
  props: {
    question: { type: String, default: '' },
    isFollowUp: { type: Boolean, default: false },
    /** Parent can disable auto TTS (e.g. future setting page) */
    autoSpeak: { type: Boolean, default: true },
    /** If set, used as i18n key for the kicker instead of interviewSimulator.currentQuestion */
    kickerKey: { type: String, default: '' },
    hideFollowUpBadge: { type: Boolean, default: false },
  },
  data() {
    return {
      speaking: false,
      autoSpeakLocal: loadAutoSpeakPreference(),
      voices: [],
      autoSpeakTimerId: null,
    };
  },
  computed: {
    kickerLabel() {
      if (this.kickerKey) return this.$t(this.kickerKey);
      return this.$t('interviewSimulator.currentQuestion');
    },
    readAloudSupported() {
      return typeof window !== 'undefined' && !!window.speechSynthesis;
    },
    utteranceLang() {
      const raw = this.$i18n?.locale;
      const loc = typeof raw === 'string' ? raw : raw?.value;
      const s = String(loc || 'ru').toLowerCase();
      return s.startsWith('en') ? 'en-US' : 'ru-RU';
    },
    autoSpeakEffective() {
      return this.autoSpeak !== false && this.autoSpeakLocal;
    },
  },
  mounted() {
    if (!this.readAloudSupported) return;
    this.refreshVoices();
    window.speechSynthesis.addEventListener('voiceschanged', this.refreshVoices);
    window.speechSynthesis.getVoices();
  },
  beforeUnmount() {
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.removeEventListener('voiceschanged', this.refreshVoices);
      window.speechSynthesis.cancel();
    }
    if (this.autoSpeakTimerId) clearTimeout(this.autoSpeakTimerId);
  },
  watch: {
    question: {
      immediate: true,
      handler(newQ, oldQ) {
        this.stopSpeak();
        if (!newQ || !String(newQ).trim()) return;
        if (!this.autoSpeakEffective) return;
        if (oldQ !== undefined && newQ === oldQ) return;
        if (this.autoSpeakTimerId) clearTimeout(this.autoSpeakTimerId);
        this.autoSpeakTimerId = setTimeout(() => {
          this.autoSpeakTimerId = null;
          if ((this.question || '').trim() === String(newQ).trim()) {
            this.speakQuestion();
          }
        }, 100);
      },
    },
  },
  methods: {
    refreshVoices() {
      if (typeof window === 'undefined' || !window.speechSynthesis) return;
      this.voices = window.speechSynthesis.getVoices() || [];
    },
    onAutoSpeakChange() {
      saveAutoSpeakPreference(this.autoSpeakLocal);
      if (this.autoSpeakLocal && (this.question || '').trim()) {
        this.speakQuestion();
      } else {
        this.stopSpeak();
      }
    },
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
      this.speakQuestion(true);
    },
    speakQuestion() {
      const q = (this.question || '').trim();
      if (!q || typeof window === 'undefined' || !window.speechSynthesis) return;

      const synth = window.speechSynthesis;
      synth.cancel();
      this.refreshVoices();

      const lang = this.utteranceLang;
      const short = lang.split('-')[0].toLowerCase();

      const run = () => {
        const text = (this.question || '').trim();
        if (!text) return;
        synth.cancel();
        this.refreshVoices();
        const voiceList = this.voices.length ? this.voices : synth.getVoices() || [];
        const u = new SpeechSynthesisUtterance(text);
        u.lang = lang;
        u.volume = 1;
        u.pitch = 1;
        u.rate = short === 'ru' ? 0.93 : 0.96;

        const voice = pickPreferredVoice(voiceList, lang);
        if (voice) u.voice = voice;

        u.onend = () => {
          this.speaking = false;
        };
        u.onerror = () => {
          this.speaking = false;
        };
        this.speaking = true;
        synth.speak(u);
      };

      const voiceList = this.voices.length ? this.voices : synth.getVoices() || [];
      if (!voiceList.length) {
        let ran = false;
        const kick = () => {
          if (ran) return;
          ran = true;
          synth.removeEventListener('voiceschanged', kick);
          run();
        };
        synth.addEventListener('voiceschanged', kick);
        setTimeout(kick, 280);
        return;
      }

      run();
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
.is-card__auto {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 12px;
  font-size: 0.82rem;
  color: var(--vl-text, #0d1733);
  cursor: pointer;
  user-select: none;
}
.is-card__auto input {
  width: 16px;
  height: 16px;
  accent-color: #2754c7;
}
.is-card__auto-hint {
  margin: 6px 0 0;
  font-size: 0.72rem;
  line-height: 1.4;
  color: var(--vl-muted, #5d6b8a);
  max-width: 36rem;
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
