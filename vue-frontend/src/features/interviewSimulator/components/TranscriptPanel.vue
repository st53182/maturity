<template>
  <aside class="is-transcript">
    <h3 class="is-transcript__title">Transcript</h3>
    <div ref="scroll" class="is-transcript__body">
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="is-msg"
        :class="m.role === 'assistant' ? 'is-msg--ai' : 'is-msg--user'"
      >
        <span class="is-msg__who">{{ m.role === 'assistant' ? 'Interviewer' : 'You' }}</span>
        <p class="is-msg__text">{{ m.content }}</p>
      </div>
      <p v-if="!messages.length" class="is-empty">The conversation will appear here.</p>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'TranscriptPanel',
  props: {
    messages: { type: Array, default: () => [] },
  },
  watch: {
    messages: {
      deep: true,
      handler() {
        this.$nextTick(() => {
          const el = this.$refs.scroll;
          if (el) el.scrollTop = el.scrollHeight;
        });
      },
    },
  },
};
</script>

<style scoped>
.is-transcript {
  border: 1px solid var(--vl-border, #d8e0f0);
  border-radius: 16px;
  background: #fff;
  display: flex;
  flex-direction: column;
  max-height: 420px;
}
.is-transcript__title {
  margin: 0;
  padding: 14px 16px 8px;
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--vl-text, #0d1733);
}
.is-transcript__body {
  padding: 8px 12px 14px;
  overflow-y: auto;
  flex: 1;
}
.is-msg {
  margin-bottom: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  font-size: 0.88rem;
  line-height: 1.45;
}
.is-msg--ai {
  background: #f0f4ff;
  border: 1px solid rgba(39, 84, 199, 0.12);
}
.is-msg--user {
  background: #f6f9ff;
  border: 1px solid var(--vl-border, #d8e0f0);
}
.is-msg__who {
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--vl-muted, #5d6b8a);
  margin-bottom: 4px;
}
.is-msg__text {
  margin: 0;
  color: var(--vl-text, #0d1733);
  white-space: pre-wrap;
}
.is-empty {
  margin: 12px;
  font-size: 0.85rem;
  color: var(--vl-muted, #5d6b8a);
}
</style>
