<template>
  <div class="is-controls">
    <label class="is-sr-only" for="answer-box">{{ $t('interviewSimulator.placeholderAnswer') }}</label>
    <textarea
      id="answer-box"
      v-model="local"
      class="is-controls__input"
      rows="4"
      :disabled="disabled"
      :placeholder="$t('interviewSimulator.placeholderAnswer')"
      @keydown.ctrl.enter="submit"
      @keydown.meta.enter="submit"
    />
    <p v-if="voiceError" class="is-voice-err">{{ voiceErrorMessage }}</p>
    <div class="is-controls__row">
      <button
        v-if="voiceSupported"
        type="button"
        class="is-btn is-btn--ghost is-btn--voice"
        :class="{ 'is-btn--voice-active': listening }"
        :disabled="disabled"
        :aria-pressed="listening"
        :title="listening ? $t('interviewSimulator.voiceListening') : $t('interviewSimulator.voiceAnswer')"
        @click="toggleListen"
      >
        {{ listening ? $t('interviewSimulator.voiceStop') : $t('interviewSimulator.voiceAnswer') }}
      </button>
      <button
        v-else
        type="button"
        class="is-btn is-btn--ghost is-btn--ghost--muted"
        disabled
        :title="$t('interviewSimulator.voiceUnsupported')"
      >
        {{ $t('interviewSimulator.voiceAnswer') }}
      </button>
      <button
        type="button"
        class="is-btn is-btn--primary"
        :disabled="disabled || !local.trim()"
        @click="submit"
      >
        {{ submitLabel }}
      </button>
    </div>
    <p class="is-tip">{{ $t('interviewSimulator.keyboardTip') }}</p>
  </div>
</template>

<script>
export default {
  name: 'InterviewControls',
  props: {
    modelValue: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    submitLabel: { type: String, default: 'Send answer' },
  },
  emits: ['update:modelValue', 'submit'],
  data() {
    return {
      local: this.modelValue,
      listening: false,
      recognition: null,
      voiceError: null,
    };
  },
  computed: {
    voiceSupported() {
      if (typeof window === 'undefined') return false;
      return !!(window.SpeechRecognition || window.webkitSpeechRecognition);
    },
    speechLang() {
      const raw = this.$i18n?.locale;
      const loc = typeof raw === 'string' ? raw : raw?.value;
      const s = String(loc || 'ru').toLowerCase();
      return s.startsWith('en') ? 'en-US' : 'ru-RU';
    },
    voiceErrorMessage() {
      if (this.voiceError === 'not-allowed') return this.$t('interviewSimulator.voiceMicDenied');
      return this.$t('interviewSimulator.voiceErrorGeneric');
    },
  },
  watch: {
    modelValue(v) {
      if (v !== this.local) this.local = v;
    },
  },
  beforeUnmount() {
    this.stopRecognition();
  },
  methods: {
    stopRecognition() {
      this.listening = false;
      const rec = this.recognition;
      this.recognition = null;
      if (rec) {
        try {
          rec.stop();
        } catch (_e) {
          /* ignore */
        }
      }
    },
    buildRecognition() {
      const SR = typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition);
      if (!SR) return null;
      const r = new SR();
      r.lang = this.speechLang;
      r.interimResults = false;
      r.continuous = true;
      r.onresult = (event) => {
        let chunk = '';
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          if (event.results[i].isFinal) {
            chunk += event.results[i][0].transcript;
          }
        }
        const t = chunk.trim();
        if (t) {
          this.local = this.local ? `${this.local} ${t}` : t;
        }
      };
      r.onerror = (e) => {
        this.voiceError = e.error || 'generic';
        this.stopRecognition();
      };
      r.onend = () => {
        if (!this.listening || this.recognition !== r) return;
        setTimeout(() => {
          if (!this.listening || this.recognition !== r) return;
          try {
            r.start();
          } catch (_err) {
            this.listening = false;
            this.recognition = null;
          }
        }, 100);
      };
      return r;
    },
    toggleListen() {
      if (this.disabled) return;
      this.voiceError = null;
      if (this.listening) {
        this.stopRecognition();
        return;
      }
      const r = this.buildRecognition();
      if (!r) return;
      this.recognition = r;
      this.listening = true;
      try {
        r.start();
      } catch (_e) {
        this.listening = false;
        this.recognition = null;
        this.voiceError = 'generic';
      }
    },
    submit() {
      if (this.disabled || !this.local.trim()) return;
      this.$emit('update:modelValue', this.local);
      this.$emit('submit', this.local.trim());
      this.local = '';
    },
  },
};
</script>

<style scoped>
.is-controls__input {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  padding: 12px 14px;
  font-size: 0.9rem;
  font-family: inherit;
  margin-bottom: 12px;
  background: #fff;
  color: var(--vl-text, #0d1733);
}
.is-controls__input:disabled {
  opacity: 0.6;
}
.is-controls__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.is-btn {
  border-radius: 12px;
  padding: 10px 20px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  border: none;
}
.is-btn--primary {
  background: linear-gradient(135deg, #142b66, #2754c7);
  color: #fff;
}
.is-btn--primary:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
.is-btn--ghost {
  background: #eff3fb;
  color: var(--vl-muted, #5d6b8a);
  border: 1px solid var(--vl-border, #d8e0f0);
}
.is-btn--ghost:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.is-btn--ghost--muted {
  cursor: not-allowed;
}
.is-btn--voice:not(:disabled) {
  cursor: pointer;
}
.is-btn--voice-active {
  background: rgba(192, 57, 43, 0.12);
  border-color: rgba(192, 57, 43, 0.35);
  color: #922b21;
}
.is-voice-err {
  font-size: 0.8rem;
  color: #c0392b;
  margin: 0 0 8px;
}
.is-tip {
  margin: 8px 0 0;
  font-size: 0.75rem;
  color: var(--vl-muted, #5d6b8a);
}
.is-sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}
</style>
