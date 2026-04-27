<template>
  <div class="sh-ai">
    <button type="button" class="sh-ai__toggle" @click="open = !open">
      {{ title }}
    </button>
    <div v-if="open" class="sh-ai__panel">
      <textarea v-model="text" class="sh-ai__ta" rows="3" :placeholder="placeholder" :disabled="disabled" />
      <button
        type="button"
        class="sh-btn sh-btn--primary"
        :disabled="disabled || !text.trim() || remaining <= 0"
        @click="submit"
      >{{ $t('agileTraining.stakeholderMatrix.askAi') }} ({{ remaining }})</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AiBlock',
  props: {
    title: { type: String, default: 'AI' },
    remaining: { type: Number, default: 0 },
    disabled: { type: Boolean, default: false },
    placeholder: { type: String, default: '' },
  },
  data() { return { open: false, text: '' }; },
  methods: {
    submit() {
      this.$emit('ask', this.text);
      this.text = '';
    },
  },
};
</script>

<style scoped>
.sh-ai { margin-top: 12px; border-top: 1px solid #e2e8f0; padding-top: 10px; }
.sh-ai__toggle { border: none; background: none; color: #1d4ed8; font-weight: 600; cursor: pointer; padding: 0; font-size: 14px; }
.sh-ai__panel { margin-top: 8px; }
.sh-ai__ta { width: 100%; box-sizing: border-box; border-radius: 8px; border: 1px solid rgba(15, 23, 42, 0.12); padding: 8px; font: inherit; margin-bottom: 6px; }
.sh-btn { display: inline-flex; align-items: center; padding: 6px 12px; border-radius: 8px; border: 1px solid #1d4ed8; background: #1d4ed8; color: #fff; font-weight: 600; cursor: pointer; font-size: 13px; }
.sh-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
