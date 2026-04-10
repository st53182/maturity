<template>
  <div class="is-field">
    <label class="is-label">{{ effectiveLabel }}</label>
    <div class="is-seg">
      <button
        v-for="lv in levels"
        :key="lv.id"
        type="button"
        class="is-seg__btn"
        :class="{ 'is-seg__btn--active': modelValue === lv.id }"
        @click="$emit('update:modelValue', lv.id)"
      >
        {{ $t(`interviewSimulator.levels.${lv.id}`) }}
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
    label: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  data() {
    return { levels: INTERVIEW_LEVELS };
  },
  computed: {
    effectiveLabel() {
      return this.label || this.$t('interviewSimulator.labelLevel');
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
  color: #142b66;
  font-weight: 700;
  box-shadow: inset 0 0 0 2px rgba(39, 84, 199, 0.55), 0 2px 8px rgba(20, 43, 102, 0.12);
}
</style>
