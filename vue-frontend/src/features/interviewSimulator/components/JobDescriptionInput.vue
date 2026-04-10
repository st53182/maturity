<template>
  <div class="is-field">
    <label class="is-label" for="jd-input">{{ label }}</label>
    <p class="is-hint">{{ hint }}</p>
    <textarea
      id="jd-input"
      class="is-textarea"
      :rows="rows"
      :placeholder="placeholder"
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
    label: { type: String, default: 'Job description (optional)' },
    hint: {
      type: String,
      default:
        'Paste requirements, stack, and responsibilities. The AI will anchor questions and scoring to this text.',
    },
    placeholder: {
      type: String,
      default: 'Example: We need a Middle Frontend engineer with React, TypeScript, testing (Jest/RTL), REST…',
    },
    rows: { type: Number, default: 8 },
  },
  emits: ['update:modelValue'],
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
