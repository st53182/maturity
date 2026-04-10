<template>
  <div class="is-field">
    <label class="is-label">{{ effectiveLabel }}</label>
    <div class="is-chip-grid">
      <button
        v-for="r in roles"
        :key="r.id"
        type="button"
        class="is-chip"
        :class="{ 'is-chip--active': modelValue === r.id }"
        @click="$emit('update:modelValue', r.id)"
      >
        {{ $t(`interviewSimulator.roles.${r.id}`) }}
      </button>
    </div>
  </div>
</template>

<script>
import { INTERVIEW_ROLES } from '../types';

export default {
  name: 'RoleSelector',
  props: {
    modelValue: { type: String, required: true },
    label: { type: String, default: '' },
  },
  emits: ['update:modelValue'],
  data() {
    return { roles: INTERVIEW_ROLES };
  },
  computed: {
    effectiveLabel() {
      return this.label || this.$t('interviewSimulator.labelRole');
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
.is-chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.is-chip {
  border: 1px solid var(--vl-border, #d8e0f0);
  background: #fff;
  color: var(--vl-text, #0d1733);
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}
.is-chip:hover {
  border-color: rgba(39, 84, 199, 0.45);
}
.is-chip--active {
  border-color: #2754c7;
  background: linear-gradient(180deg, rgba(39, 84, 199, 0.18), rgba(39, 84, 199, 0.1));
  color: #142b66;
  font-weight: 700;
  box-shadow: 0 0 0 2px rgba(39, 84, 199, 0.35);
}
</style>
