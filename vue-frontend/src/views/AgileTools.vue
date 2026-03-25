<template>
  <div class="agile-tools">
    <header class="agile-tools__hero">
      <h1 class="agile-tools__title">{{ $t('agileTools.title') }}</h1>
      <p class="agile-tools__lead">{{ $t('agileTools.lead') }}</p>
      <div class="agile-tools__search-wrap">
        <label for="agile-tools-search" class="agile-tools__sr-only">{{ $t('agileTools.search') }}</label>
        <input
          id="agile-tools-search"
          v-model.trim="query"
          type="search"
          class="agile-tools__search"
          :placeholder="$t('agileTools.searchPh')"
          autocomplete="off"
        />
      </div>
      <p v-if="query && !totalVisible" class="agile-tools__empty">{{ $t('agileTools.noResults') }}</p>
    </header>

    <div class="agile-tools__layout">
      <section
        v-for="(cat, idx) in filteredCategories"
        :key="cat.title + idx"
        class="agile-tools__category"
      >
        <button
          type="button"
          class="agile-tools__cat-head"
          :aria-expanded="openCats[idx]"
          @click="toggleCat(idx)"
        >
          <span class="agile-tools__cat-title">{{ cat.title }}</span>
          <span class="agile-tools__cat-chevron" :class="{ 'is-open': openCats[idx] }" aria-hidden="true">▶</span>
        </button>
        <div v-show="openCats[idx]" class="agile-tools__cat-body">
          <article
            v-for="(p, pi) in cat.practices"
            :key="p.name + '-' + pi"
            class="agile-tools__card"
          >
            <h3 class="agile-tools__name">{{ p.name }}</h3>
            <p v-if="p.subtitle" class="agile-tools__subtitle">{{ p.subtitle }}</p>
            <p class="agile-tools__block">
              <span class="agile-tools__label">{{ $t('agileTools.summaryLabel') }}</span>
              {{ p.summary }}
            </p>
            <p class="agile-tools__block">
              <span class="agile-tools__label">{{ $t('agileTools.benefitLabel') }}</span>
              {{ p.benefit }}
            </p>
            <p v-if="p.detail" class="agile-tools__block agile-tools__detail">
              <span class="agile-tools__label">{{ $t('agileTools.detailLabel') }}</span>
              {{ p.detail }}
            </p>
            <div class="agile-tools__ai">
              <div class="agile-tools__ai-row">
                <button
                  type="button"
                  class="agile-tools__ai-btn"
                  :disabled="aiSession(cat, p).loading"
                  @click="fetchAiExplanation(cat, p, false)"
                >
                  {{
                    aiSession(cat, p).loading && !aiSession(cat, p).followUpPending
                      ? $t('agileTools.aiThinking')
                      : aiSession(cat, p).reply
                        ? $t('agileTools.askAiAgain')
                        : $t('agileTools.askAi')
                  }}
                </button>
                <button
                  v-if="aiSession(cat, p).reply"
                  type="button"
                  class="agile-tools__ai-toggle"
                  @click="toggleAiFollowUp(cat, p)"
                >
                  {{ $t('agileTools.aiFollowUp') }}
                </button>
              </div>
              <p class="agile-tools__ai-disclaimer">{{ $t('agileTools.aiDisclaimer') }}</p>
              <div v-if="aiSession(cat, p).showFollowUp" class="agile-tools__ai-follow">
                <textarea
                  v-model="aiSession(cat, p).question"
                  class="agile-tools__ai-textarea"
                  rows="2"
                  :placeholder="$t('agileTools.aiFollowPh')"
                />
                <button
                  type="button"
                  class="agile-tools__ai-send"
                  :disabled="aiSession(cat, p).loading || !aiSession(cat, p).question.trim()"
                  @click="fetchAiExplanation(cat, p, true)"
                >
                  {{ aiSession(cat, p).loading && aiSession(cat, p).followUpPending ? $t('agileTools.aiThinking') : $t('agileTools.aiSendQuestion') }}
                </button>
              </div>
              <p v-if="aiSession(cat, p).error" class="agile-tools__ai-error" role="alert">
                {{ aiSession(cat, p).error }}
              </p>
              <div v-if="aiSession(cat, p).reply" class="agile-tools__ai-reply">
                <span class="agile-tools__label">{{ $t('agileTools.aiReplyTitle') }}</span>
                <div
                  class="agile-tools__ai-reply-body agile-tools__md"
                  v-html="renderAiMarkdown(aiSession(cat, p).reply)"
                ></div>
              </div>
            </div>
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import DOMPurify from 'dompurify';
import { marked } from 'marked';
import { agilePracticeCategories } from '@/data/agilePractices.js';

marked.use({
  gfm: true,
  breaks: true,
});

export default {
  name: 'AgileTools',
  data() {
    return {
      query: '',
      openCats: [],
      aiByKey: {},
    };
  },
  computed: {
    filteredCategories() {
      const q = (this.query || '').toLowerCase();
      if (!q) {
        return agilePracticeCategories;
      }
      return agilePracticeCategories
        .map((cat) => ({
          ...cat,
          practices: cat.practices.filter((p) => {
            const hay = [p.name, p.subtitle, p.summary, p.benefit, p.detail].join(' ').toLowerCase();
            return hay.includes(q);
          }),
        }))
        .filter((c) => c.practices.length > 0);
    },
    totalVisible() {
      return this.filteredCategories.reduce((n, c) => n + c.practices.length, 0);
    },
  },
  watch: {
    filteredCategories: {
      handler(cats) {
        const q = (this.query || '').trim();
        if (this.openCats.length !== cats.length) {
          this.openCats = cats.map(() => !!q);
        }
      },
      immediate: true,
    },
    query(q) {
      const cats = this.filteredCategories;
      if ((q || '').trim()) {
        this.openCats = cats.map(() => true);
      } else {
        this.openCats = cats.map(() => false);
      }
    },
  },
  methods: {
    renderAiMarkdown(text) {
      if (!text || typeof text !== 'string') {
        return '';
      }
      try {
        const html = marked.parse(text.trimEnd());
        return DOMPurify.sanitize(html);
      } catch {
        return DOMPurify.sanitize(`<p>${text.replace(/</g, '&lt;').replace(/>/g, '&gt;')}</p>`);
      }
    },
    practiceAiKey(cat, p) {
      return `${cat.title}::${p.name}`;
    },
    aiSession(cat, p) {
      const k = this.practiceAiKey(cat, p);
      if (!this.aiByKey[k]) {
        this.aiByKey[k] = {
          loading: false,
          reply: '',
          error: '',
          question: '',
          showFollowUp: false,
          followUpPending: false,
        };
      }
      return this.aiByKey[k];
    },
    toggleAiFollowUp(cat, p) {
      const s = this.aiSession(cat, p);
      s.showFollowUp = !s.showFollowUp;
    },
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    async fetchAiExplanation(cat, p, isFollowUp) {
      const s = this.aiSession(cat, p);
      if (isFollowUp && !s.question.trim()) {
        return;
      }
      s.loading = true;
      s.followUpPending = !!isFollowUp;
      s.error = '';
      try {
        const locale = (this.$i18n.locale || 'ru').toString();
        const { data } = await axios.post(
          '/api/agile-tools/ask',
          {
            locale,
            categoryTitle: cat.title,
            name: p.name,
            subtitle: p.subtitle || '',
            summary: p.summary || '',
            benefit: p.benefit || '',
            detail: p.detail || '',
            user_question: isFollowUp ? s.question.trim() : '',
          },
          { headers: this.authHeaders() }
        );
        s.reply = data.reply || '';
        if (isFollowUp) {
          s.question = '';
          s.showFollowUp = false;
        }
      } catch (e) {
        if (e.response?.status === 401) {
          s.error = this.$t('agileTools.aiNeedAuth');
        } else {
          s.error = e.response?.data?.error || this.$t('agileTools.aiErrorGeneric');
        }
      } finally {
        s.loading = false;
        s.followUpPending = false;
      }
    },
    toggleCat(i) {
      const next = [...this.openCats];
      next[i] = !next[i];
      this.openCats = next;
    },
  },
};
</script>

<style scoped>
.agile-tools {
  max-width: 960px;
  margin: 0 auto;
  padding: 28px 20px 56px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
  color: #0f172a;
}

.agile-tools__hero {
  margin-bottom: 28px;
}

.agile-tools__title {
  margin: 0 0 10px;
  font-size: 1.85rem;
  font-weight: 800;
  letter-spacing: -0.03em;
}

.agile-tools__lead {
  margin: 0 0 20px;
  color: #64748b;
  line-height: 1.55;
  font-size: 15px;
  max-width: 720px;
}

.agile-tools__search-wrap {
  max-width: 420px;
}

.agile-tools__search {
  width: 100%;
  padding: 12px 16px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  font-size: 15px;
  box-sizing: border-box;
}

.agile-tools__search:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
}

.agile-tools__empty {
  margin-top: 12px;
  color: #94a3b8;
  font-size: 14px;
}

.agile-tools__category {
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  overflow: hidden;
  background: #fff;
  box-shadow: 0 1px 3px rgba(15, 23, 42, 0.06);
}

.agile-tools__cat-head {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  border: none;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  cursor: pointer;
  text-align: left;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
  font-family: inherit;
}

.agile-tools__cat-head:hover {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.agile-tools__cat-chevron {
  font-size: 12px;
  color: #64748b;
  transition: transform 0.2s ease;
}

.agile-tools__cat-chevron.is-open {
  transform: rotate(90deg);
}

.agile-tools__cat-body {
  padding: 8px 12px 16px;
  border-top: 1px solid #e5e7eb;
}

.agile-tools__card {
  padding: 16px 14px;
  margin-bottom: 8px;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  background: #fafafa;
}

.agile-tools__card:last-child {
  margin-bottom: 0;
}

.agile-tools__name {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
}

.agile-tools__subtitle {
  margin: 0 0 10px;
  font-size: 13px;
  color: #6366f1;
  font-weight: 600;
}

.agile-tools__block {
  margin: 0 0 8px;
  font-size: 14px;
  line-height: 1.55;
  color: #334155;
}

.agile-tools__block:last-child {
  margin-bottom: 0;
}

.agile-tools__detail {
  margin-top: 10px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}

.agile-tools__label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #94a3b8;
  margin-bottom: 4px;
}

.agile-tools__sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  border: 0;
}

.agile-tools__ai {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #e2e8f0;
}

.agile-tools__ai-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.agile-tools__ai-btn {
  padding: 10px 16px;
  border-radius: 10px;
  border: 2px solid #6366f1;
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #3730a3;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  font-family: inherit;
}

.agile-tools__ai-btn:hover:not(:disabled) {
  border-color: #4f46e5;
  background: #e0e7ff;
}

.agile-tools__ai-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.agile-tools__ai-toggle {
  padding: 8px 12px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  background: #fff;
  color: #475569;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.agile-tools__ai-toggle:hover {
  border-color: #cbd5e1;
  background: #f8fafc;
}

.agile-tools__ai-disclaimer {
  margin: 8px 0 0;
  font-size: 11px;
  line-height: 1.4;
  color: #94a3b8;
}

.agile-tools__ai-follow {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.agile-tools__ai-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border-radius: 10px;
  border: 2px solid #e5e7eb;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 52px;
}

.agile-tools__ai-textarea:focus {
  outline: none;
  border-color: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.agile-tools__ai-send {
  align-self: flex-start;
  padding: 8px 14px;
  border-radius: 10px;
  border: 2px solid #0f172a;
  background: #0f172a;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.agile-tools__ai-send:hover:not(:disabled) {
  background: #1e293b;
}

.agile-tools__ai-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.agile-tools__ai-error {
  margin: 10px 0 0;
  font-size: 13px;
  color: #b91c1c;
}

.agile-tools__ai-reply {
  margin-top: 14px;
}

.agile-tools__ai-reply-body {
  margin-top: 6px;
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  font-size: 14px;
  line-height: 1.6;
  color: #334155;
}

.agile-tools__md :deep(h1),
.agile-tools__md :deep(h2),
.agile-tools__md :deep(h3) {
  margin: 1em 0 0.45em;
  font-weight: 750;
  color: #0f172a;
  line-height: 1.3;
}

.agile-tools__md :deep(h1) {
  font-size: 1.2rem;
  margin-top: 0;
}

.agile-tools__md :deep(h2) {
  font-size: 1.08rem;
}

.agile-tools__md :deep(h3) {
  font-size: 1rem;
}

.agile-tools__md :deep(p) {
  margin: 0.55em 0;
}

.agile-tools__md :deep(p:first-child) {
  margin-top: 0;
}

.agile-tools__md :deep(p:last-child) {
  margin-bottom: 0;
}

.agile-tools__md :deep(ul),
.agile-tools__md :deep(ol) {
  margin: 0.5em 0;
  padding-left: 1.35rem;
}

.agile-tools__md :deep(li) {
  margin: 0.25em 0;
}

.agile-tools__md :deep(strong) {
  font-weight: 700;
  color: #1e293b;
}

.agile-tools__md :deep(code) {
  font-size: 0.9em;
  padding: 0.12em 0.35em;
  border-radius: 6px;
  background: #f1f5f9;
  color: #0f172a;
}

.agile-tools__md :deep(pre) {
  margin: 0.75em 0;
  padding: 12px;
  overflow-x: auto;
  border-radius: 10px;
  background: #1e293b;
  color: #e2e8f0;
  font-size: 13px;
}

.agile-tools__md :deep(pre code) {
  background: transparent;
  color: inherit;
  padding: 0;
}

.agile-tools__md :deep(blockquote) {
  margin: 0.65em 0;
  padding: 8px 12px;
  border-left: 4px solid #c7d2fe;
  background: #f8fafc;
  color: #475569;
}

.agile-tools__md :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
  text-underline-offset: 2px;
}
</style>
