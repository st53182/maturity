<template>
  <div class="is-field">
    <label class="is-label">{{ label }}</label>
    <div class="is-seg">
      <button
        v-for="lv in levels"
        :key="lv.id"
        type="button"
        class="is-seg__btn"
        :class="{ 'is-seg__btn--active': modelValue === lv.id }"
        @click="$emit('update:modelValue', lv.id)"
      >
        {{ lv.label }}
      </button>
    </div>
  </div>
</template>

<script>
import { INTERVIEW_LEVELS } from '../types';

export default {
  name: 'LevelSelector',
  props: {
    modelValue: { type: String, required: true },
    label: { type: String, default: 'Level' },
  },
  emits: ['update:modelValue'],
  data() {
    return { levels: INTERVIEW_LEVELS };
  },
};
</script>

<style scoped>
.is-label {
  display: block;
  font-size: 0.85rem;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
  margin-bottom: 8px;
}
.is-seg {
  display: inline-flex;
  border-radius: 12px;
  border: 1px solid var(--vl-border, #d8e0f0);
  overflow: hidden;
  background: #f6f9ff;
}
.is-seg__btn {
  border: none;
  background: transparent;
  padding: 10px 18px;
  font-size: 0.9rem;
  cursor: pointer;
  color: var(--vl-muted, #5d6b8a);
}
.is-seg__btn--active {
  background: #fff;
  color: var(--vl-text, #0d1733);
  font-weight: 600;
  box-shadow: 0 1px 0 rgba(10, 20, 45, 0.06);
}
</style>
