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
          <span class="agile-tools__cat-chevron" :class="{ 'is-open': openCats[idx] }">▼</span>
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
          </article>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { agilePracticeCategories } from '@/data/agilePractices.js';

export default {
  name: 'AgileTools',
  data() {
    return {
      query: '',
      openCats: [],
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
            const hay = [p.name, p.subtitle, p.summary, p.benefit].join(' ').toLowerCase();
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
        this.openCats = cats.map(() => true);
      },
      immediate: true,
    },
  },
  methods: {
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
  transform: rotate(-180deg);
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
</style>
