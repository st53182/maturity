<template>
  <div class="is-field">
    <label class="is-label" for="jd-input">{{ effectiveLabel }}</label>
    <p class="is-hint">{{ effectiveHint }}</p>
    <textarea
      id="jd-input"
      class="is-textarea"
      :rows="rows"
      :placeholder="effectivePlaceholder"
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
    />
  </div>
</template>

<script>
export default {
  name: 'JobDescriptionInput',
  props: {
    modelValue: { type: String, default: '' },
    label: { type: String, default: '' },
    hint: { type: String, default: '' },
    placeholder: { type: String, default: '' },
    rows: { type: Number, default: 8 },
  },
  emits: ['update:modelValue'],
  computed: {
    effectiveLabel() {
      return this.label || this.$t('interviewSimulator.jdLabel');
    },
    effectiveHint() {
      return this.hint || this.$t('interviewSimulator.jdHint');
    },
    effectivePlaceholder() {
      return this.placeholder || this.$t('interviewSimulator.jdPlaceholder');
    },
  },
};
</script>

<style scoped>
.is-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
  margin-bottom: 6px;
}
.is-hint {
  margin: 0 0 10px;
  font-size: 0.8rem;
  color: var(--vl-muted, #5d6b8a);
  line-height: 1.45;
}
.is-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  padding: 12px 14px;
  font-size: 0.9rem;
  font-family: inherit;
  resize: vertical;
  min-height: 140px;
  background: var(--vl-surface-soft, #f6f9ff);
  color: var(--vl-text, #0d1733);
}
.is-textarea:focus {
  outline: none;
  border-color: rgba(39, 84, 199, 0.45);
  box-shadow: 0 0 0 3px rgba(39, 84, 199, 0.1);
}
</style>
