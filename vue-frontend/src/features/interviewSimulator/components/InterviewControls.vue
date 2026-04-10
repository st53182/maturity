<template>
  <div class="is-controls">
    <label class="is-sr-only" for="answer-box">Your answer</label>
    <textarea
      id="answer-box"
      v-model="local"
      class="is-controls__input"
      rows="4"
      :disabled="disabled"
      placeholder="Type your answer…"
      @keydown.ctrl.enter="submit"
      @keydown.meta.enter="submit"
    />
    <div class="is-controls__row">
      <button
        type="button"
        class="is-btn is-btn--ghost"
        disabled
        title="Voice input (planned)"
      >
        Voice (soon)
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
    <p class="is-tip">Tip: Ctrl+Enter / Cmd+Enter to send</p>
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
    return { local: this.modelValue };
  },
  watch: {
    modelValue(v) {
      if (v !== this.local) this.local = v;
    },
  },
  methods: {
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
  cursor: not-allowed;
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
