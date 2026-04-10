<template>
  <div class="is-field">
    <label class="is-label">{{ label }}</label>
    <div class="is-chip-grid">
      <button
        v-for="r in roles"
        :key="r.id"
        type="button"
        class="is-chip"
        :class="{ 'is-chip--active': modelValue === r.id }"
        @click="$emit('update:modelValue', r.id)"
      >
        {{ r.label }}
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
    label: { type: String, default: 'Role' },
  },
  emits: ['update:modelValue'],
  data() {
    return { roles: INTERVIEW_ROLES };
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
  border-color: rgba(39, 84, 199, 0.55);
  background: rgba(39, 84, 199, 0.08);
  font-weight: 600;
}
</style>
