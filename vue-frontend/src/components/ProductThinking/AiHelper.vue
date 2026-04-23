<template>
  <div class="ai-helper">
    <div class="ai-helper__head">
      <div class="ai-helper__title">🤖 {{ $t('agileTraining.productThinking.aiHelperTitle') }}</div>
      <button
        type="button"
        class="ai-helper__cta"
        :disabled="loading || disabled || !callsRemaining"
        @click="handleAsk"
      >
        {{ loading ? $t('agileTraining.productThinking.aiHelperLoading') : (label || $t('agileTraining.productThinking.aiHelperCta')) }}
      </button>
    </div>

    <div v-if="disabled" class="ai-helper__hint ai-helper__hint--warn">
      {{ disabledHint }}
    </div>

    <div v-if="!callsRemaining && !disabled" class="ai-helper__hint ai-helper__hint--warn">
      {{ $t('agileTraining.productThinking.aiHelperLimit') }}
    </div>

    <p v-if="!reply && !loading && !error && !disabled" class="ai-helper__empty">
      {{ $t('agileTraining.productThinking.aiHelperEmpty') }}
    </p>

    <div v-if="error" class="ai-helper__error">{{ error }}</div>

    <div v-if="reply" class="ai-helper__reply" v-html="renderedReply"></div>

    <div v-if="history.length > 1" class="ai-helper__history">
      <div class="ai-helper__history-h">{{ $t('agileTraining.productThinking.aiHelperHistoryTitle') }}</div>
      <details v-for="(h, i) in historyPrev" :key="i">
        <summary>{{ h.inputShort || '…' }}</summary>
        <div class="ai-helper__history-reply" v-html="renderMd(h.reply)"></div>
      </details>
    </div>
  </div>
</template>

<script>
function escapeHtml(s) {
  return String(s || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
}
function tinyMd(text) {
  if (!text) return '';
  const lines = String(text).split(/\r?\n/);
  const out = [];
  let ul = false;
  const closeUl = () => { if (ul) { out.push('</ul>'); ul = false; } };
  for (const raw of lines) {
    const line = raw.trim();
    if (!line) { closeUl(); out.push(''); continue; }
    const bullet = line.match(/^[-*]\s+(.*)$/);
    if (bullet) {
      if (!ul) { out.push('<ul>'); ul = true; }
      out.push('<li>' + inline(bullet[1]) + '</li>');
      continue;
    }
    closeUl();
    const heading = line.match(/^(#{1,3})\s+(.*)$/);
    if (heading) {
      const level = Math.min(heading[1].length + 2, 6);
      out.push(`<h${level}>${inline(heading[2])}</h${level}>`);
      continue;
    }
    out.push('<p>' + inline(line) + '</p>');
  }
  closeUl();
  return out.join('\n');
}
function inline(text) {
  return escapeHtml(text)
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/_([^_]+)_/g, '<em>$1</em>');
}

export default {
  name: 'AiHelper',
  props: {
    locale: { type: String, default: 'ru' },
    mode: { type: String, required: true },
    label: { type: String, default: '' },
    callsRemaining: { type: Number, default: 0 },
    initialInput: { type: String, default: '' },
    disabled: { type: Boolean, default: false },
    disabledHint: { type: String, default: '' },
  },
  data() {
    return {
      loading: false,
      reply: '',
      error: '',
      history: [],
    };
  },
  computed: {
    renderedReply() { return tinyMd(this.reply); },
    historyPrev() {
      return this.history.slice(0, -1).map(h => ({
        inputShort: (h.input || '').slice(0, 80),
        reply: h.reply,
      })).reverse();
    },
  },
  methods: {
    renderMd(text) { return tinyMd(text); },
    handleAsk() {
      if (this.loading) return;
      const input = (this.initialInput || '').trim();
      this.error = '';
      this.loading = true;
      this.$emit('ask', {
        mode: this.mode,
        input,
        resolve: (result) => {
          this.loading = false;
          if (result && result.error) {
            this.error = result.error;
            return;
          }
          if (result && typeof result.reply === 'string') {
            this.reply = result.reply;
            this.history.push({ input, reply: result.reply });
          }
        },
      });
    },
  },
};
</script>

<style scoped>
.ai-helper {
  margin-top: 14px; background: #fef3ff;
  border: 1px solid #e9d5ff; border-radius: 14px;
  padding: 14px 16px;
}
.ai-helper__head {
  display: flex; justify-content: space-between; align-items: center; gap: 10px;
}
.ai-helper__title { font-weight: 700; color: #6d28d9; }
.ai-helper__cta {
  border: none; background: #7c3aed; color: #fff; font-weight: 600;
  border-radius: 999px; padding: 8px 16px; cursor: pointer;
  font-size: 13px; transition: all 0.15s ease;
}
.ai-helper__cta:hover:not(:disabled) { background: #6d28d9; }
.ai-helper__cta:disabled { opacity: 0.5; cursor: not-allowed; }
.ai-helper__hint {
  margin-top: 10px; font-size: 13px; color: #92400e;
}
.ai-helper__hint--warn {
  background: #fef3c7; padding: 8px 12px; border-radius: 8px;
}
.ai-helper__empty { margin: 10px 0 0; font-size: 13px; color: #7c3aed; }
.ai-helper__error {
  margin-top: 10px; padding: 8px 12px; background: #fee2e2;
  color: #b91c1c; border-radius: 8px; font-size: 13px;
}
.ai-helper__reply {
  margin-top: 12px; padding: 12px 14px; background: #fff;
  border-radius: 10px; border-left: 3px solid #7c3aed;
  color: #1e293b; line-height: 1.55; font-size: 14px;
}
.ai-helper__reply :deep(h3), .ai-helper__reply :deep(h4), .ai-helper__reply :deep(h5) {
  font-size: 14px; margin: 10px 0 4px;
}
.ai-helper__reply :deep(p) { margin: 6px 0; }
.ai-helper__reply :deep(ul) { margin: 6px 0; padding-left: 20px; }
.ai-helper__reply :deep(li) { margin: 2px 0; }
.ai-helper__reply :deep(strong) { color: #6d28d9; }
.ai-helper__reply :deep(em) { color: #334155; }
.ai-helper__reply :deep(code) {
  background: #faf5ff; padding: 1px 4px; border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, monospace; font-size: 12px;
}

.ai-helper__history {
  margin-top: 12px; padding-top: 12px; border-top: 1px dashed #e5e7eb;
}
.ai-helper__history-h {
  font-size: 12px; font-weight: 600; color: #64748b; margin-bottom: 6px;
  text-transform: uppercase; letter-spacing: 0.5px;
}
.ai-helper__history details {
  margin-top: 4px; font-size: 13px;
}
.ai-helper__history summary {
  cursor: pointer; color: #475569; padding: 4px 0;
}
.ai-helper__history-reply {
  margin-top: 4px; padding: 8px 10px; background: #faf5ff; border-radius: 8px;
  color: #334155; line-height: 1.5;
}
</style>
