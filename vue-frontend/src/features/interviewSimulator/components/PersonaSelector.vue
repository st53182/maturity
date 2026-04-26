<template>
  <div class="is-persona">
    <div class="is-persona__label">{{ displayLabel }}</div>
    <div class="is-persona__grid" role="radiogroup" :aria-label="displayLabel">
      <label v-for="id in ids" :key="id" class="is-persona__opt">
        <input v-model="local" type="radio" name="is-persona" :value="id" />
        <span>{{ $t(`interviewSimulator.personas.${id}`) }}</span>
      </label>
    </div>
  </div>
</template>

<script>
const IDS = ['tech_employee', 'retiree', 'middle_class_messenger', 'regional_smb'];

export default {
  name: 'PersonaSelector',
  props: {
    modelValue: { type: String, default: 'tech_employee' },
    label: { type: String, default: '' },
  },
  computed: {
    ids() {
      return IDS;
    },
    local: {
      get() {
        return this.modelValue;
      },
      set(v) {
        this.$emit('update:modelValue', v);
      },
    },
    displayLabel() {
      return this.label || this.$t('interviewSimulator.labelPersona');
    },
  },
};
</script>

<style scoped>
.is-persona {
  text-align: left;
}
.is-persona__label {
  display: block;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
  margin-bottom: 10px;
}
.is-persona__grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.is-persona__opt {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  background: #fff;
  cursor: pointer;
  font-size: 0.9rem;
  line-height: 1.35;
  color: var(--vl-text, #0d1733);
}
.is-persona__opt:has(:checked) {
  border-color: rgba(39, 84, 199, 0.45);
  background: #f4f6ff;
}
.is-persona__opt input {
  margin-top: 3px;
  accent-color: #2754c7;
  flex-shrink: 0;
}
</style>
