<template>
  <div class="atp-page">
    <!-- Переключатель языка в правом верхнем углу, доступен всегда -->
    <div v-if="!loading" class="atp-lang" role="group" :aria-label="$t('agileTraining.common.language')">
      <button
        type="button"
        class="atp-lang__btn"
        :class="{ 'atp-lang__btn--active': $i18n.locale === 'ru' }"
        @click="switchLang('ru')"
      >RU</button>
      <button
        type="button"
        class="atp-lang__btn"
        :class="{ 'atp-lang__btn--active': $i18n.locale === 'en' }"
        @click="switchLang('en')"
      >EN</button>
    </div>

    <!-- Загрузка / ошибка -->
    <div v-if="loading" class="atp-state">
      <p>{{ $t('agileTraining.common.loading') }}…</p>
    </div>
    <div v-else-if="error" class="atp-state atp-state--error">
      <h2>😕 {{ $t('agileTraining.play.error.title') }}</h2>
      <p>{{ error }}</p>
    </div>

    <!-- Экран 1: старт -->
    <section v-else-if="stage === 'start'" class="atp-start">
      <div class="atp-start__kicker">{{ session.title }}</div>
      <h1>👥 {{ group.name }}</h1>
      <p class="atp-start__lead">{{ $t('agileTraining.play.start.lead', { n: principlesTotal }) }}</p>

      <ul class="atp-start__steps">
        <li>{{ $t('agileTraining.play.start.step1') }}</li>
        <li>{{ $t('agileTraining.play.start.step2') }}</li>
        <li>{{ $t('agileTraining.play.start.step3') }}</li>
      </ul>

      <input
        v-model="displayName"
        class="atp-start__input"
        type="text"
        :placeholder="$t('agileTraining.play.start.namePlaceholder')"
        maxlength="60"
      />

      <button class="atp-start__btn" :disabled="starting" @click="startSession">
        {{ starting ? $t('agileTraining.common.loading') : $t('agileTraining.play.start.cta') }}
      </button>

      <p v-if="answeredCount > 0" class="atp-start__resume">
        {{ $t('agileTraining.play.start.resume', { n: answeredCount, total: principlesTotal }) }}
      </p>
    </section>

    <!-- Экран 2: swipe -->
    <section v-else-if="stage === 'swipe'" class="atp-swipe">
      <header class="atp-swipe__bar">
        <div class="atp-swipe__group">👥 {{ group.name }}</div>
        <div class="atp-swipe__progress">
          {{ currentIndex + 1 }} / {{ principlesTotal }}
        </div>
      </header>

      <div class="atp-swipe__track" v-if="currentPrinciple && !showingResult">
        <div
          ref="cardEl"
          class="atp-card"
          :style="cardStyle"
          @pointerdown="onPointerDown"
          @pointermove="onPointerMove"
          @pointerup="onPointerUp"
          @pointercancel="onPointerUp"
        >
          <div class="atp-card__idx">#{{ currentIndex + 1 }}</div>
          <h2 class="atp-card__title">{{ currentPrinciple.short }}</h2>
          <p class="atp-card__text">{{ currentPrinciple.text }}</p>

          <div class="atp-card__hint atp-card__hint--left" :style="{ opacity: hintOpacity('left') }">
            ← {{ $t('agileTraining.play.swipe.outdated') }}
          </div>
          <div class="atp-card__hint atp-card__hint--right" :style="{ opacity: hintOpacity('right') }">
            {{ $t('agileTraining.play.swipe.relevant') }} →
          </div>
        </div>
      </div>

      <!-- fallback кнопки -->
      <div v-if="currentPrinciple && !showingResult" class="atp-swipe__buttons">
        <button class="atp-bigbtn atp-bigbtn--left" @click="submit('outdated')" :disabled="submitting">
          ✖ {{ $t('agileTraining.play.swipe.outdated') }}
        </button>
        <button class="atp-bigbtn atp-bigbtn--right" @click="submit('relevant')" :disabled="submitting">
          ✓ {{ $t('agileTraining.play.swipe.relevant') }}
        </button>
      </div>

      <!-- результат после ответа -->
      <div v-if="showingResult && lastResult" class="atp-result">
        <h3>{{ $t('agileTraining.play.result.title') }}</h3>
        <div class="atp-bars">
          <div class="atp-bar atp-bar--relevant">
            <span class="atp-bar__label">{{ $t('agileTraining.common.relevant') }}</span>
            <div class="atp-bar__track">
              <div class="atp-bar__fill atp-bar__fill--green" :style="{ width: lastResult.stats.relevant_pct + '%' }"></div>
            </div>
            <span class="atp-bar__pct">{{ lastResult.stats.relevant_pct }}%</span>
          </div>
          <div class="atp-bar atp-bar--outdated">
            <span class="atp-bar__label">{{ $t('agileTraining.common.outdated') }}</span>
            <div class="atp-bar__track">
              <div class="atp-bar__fill atp-bar__fill--red" :style="{ width: lastResult.stats.outdated_pct + '%' }"></div>
            </div>
            <span class="atp-bar__pct">{{ lastResult.stats.outdated_pct }}%</span>
          </div>
        </div>
        <p class="atp-result__total">
          {{ $t('agileTraining.play.result.based', { n: lastResult.stats.total }) }}
        </p>
        <blockquote v-if="lastResult.provocation" class="atp-result__quote">
          💭 {{ lastResult.provocation }}
        </blockquote>

        <details class="atp-rewrite">
          <summary>✍ {{ $t('agileTraining.play.rewrite.title') }}</summary>
          <textarea
            v-model="rewriteDraft"
            rows="3"
            :placeholder="$t('agileTraining.play.rewrite.placeholder')"
          ></textarea>
          <button class="atp-bigbtn atp-bigbtn--ghost" :disabled="savingRewrite" @click="saveRewrite">
            {{ savingRewrite ? $t('agileTraining.common.loading') : $t('agileTraining.play.rewrite.save') }}
          </button>
        </details>

        <button class="atp-bigbtn atp-bigbtn--primary" @click="nextCard">
          {{ currentIndex + 1 >= principlesTotal ? $t('agileTraining.play.result.finish') : $t('agileTraining.play.result.next') }} →
        </button>
      </div>
    </section>

    <!-- Экран 3: результаты -->
    <section v-else-if="stage === 'results'" class="atp-results">
      <header class="atp-results__head">
        <h1>🎉 {{ $t('agileTraining.play.resultsScreen.title') }}</h1>
        <p class="atp-muted">{{ $t('agileTraining.play.resultsScreen.group', { name: group.name }) }}</p>
      </header>

      <div v-if="!resultsData">
        <p>{{ $t('agileTraining.common.loading') }}…</p>
      </div>
      <div v-else>
        <section class="atp-block">
          <h2>🔥 {{ $t('agileTraining.play.resultsScreen.topControversial') }}</h2>
          <p class="atp-muted">{{ $t('agileTraining.play.resultsScreen.controversialHint') }}</p>
          <ul class="atp-listbars">
            <li v-for="row in resultsData.top_controversial" :key="'c-'+row.key">
              <div class="atp-listbars__name">{{ row.short }}</div>
              <div class="atp-listbars__track">
                <div class="atp-listbars__fill atp-listbars__fill--mix" :style="{ width: row.relevant_pct + '%' }"></div>
              </div>
              <div class="atp-listbars__pct">{{ row.relevant_pct }}% / {{ 100 - row.relevant_pct }}%</div>
            </li>
            <li v-if="!resultsData.top_controversial.length" class="atp-muted">{{ $t('agileTraining.common.notEnoughData') }}</li>
          </ul>
        </section>

        <section class="atp-block">
          <h2>🎯 {{ $t('agileTraining.play.resultsScreen.topObvious') }}</h2>
          <p class="atp-muted">{{ $t('agileTraining.play.resultsScreen.obviousHint') }}</p>
          <ul class="atp-listbars">
            <li v-for="row in resultsData.top_obvious" :key="'o-'+row.key">
              <div class="atp-listbars__name">{{ row.short }}</div>
              <div class="atp-listbars__track">
                <div class="atp-listbars__fill" :style="{ width: row.relevant_pct + '%' }"></div>
              </div>
              <div class="atp-listbars__pct">{{ row.relevant_pct }}%</div>
            </li>
            <li v-if="!resultsData.top_obvious.length" class="atp-muted">{{ $t('agileTraining.common.notEnoughData') }}</li>
          </ul>
        </section>

        <section class="atp-block">
          <h2>🆚 {{ $t('agileTraining.play.resultsScreen.compare') }}</h2>
          <p v-if="!resultsData.compare.has_others" class="atp-muted">
            {{ $t('agileTraining.play.resultsScreen.compareSolo') }}
          </p>
          <ul v-else class="atp-compare">
            <li v-for="row in resultsData.compare.differences_top" :key="'d-'+row.key">
              <div class="atp-compare__name">{{ row.short }}</div>
              <div class="atp-compare__row">
                <span>{{ $t('agileTraining.play.resultsScreen.we') }}: <b>{{ row.this_group_pct }}%</b></span>
                <span>{{ $t('agileTraining.play.resultsScreen.others') }}: <b>{{ row.other_groups_pct }}%</b></span>
                <span :class="row.diff >= 0 ? 'atp-diff atp-diff--up' : 'atp-diff atp-diff--down'">
                  {{ row.diff >= 0 ? '+' : '' }}{{ row.diff }} {{ $t('agileTraining.common.pp') }}
                </span>
              </div>
            </li>
            <li v-if="!resultsData.compare.differences_top.length" class="atp-muted">
              {{ $t('agileTraining.play.resultsScreen.compareNoDiff') }}
            </li>
          </ul>
        </section>

        <details class="atp-block atp-all">
          <summary>📋 {{ $t('agileTraining.play.resultsScreen.all') }}</summary>
          <ul class="atp-listbars">
            <li v-for="row in resultsData.per_principle" :key="'all-'+row.key">
              <div class="atp-listbars__name">{{ row.short }}</div>
              <div class="atp-listbars__track">
                <div class="atp-listbars__fill" :style="{ width: row.relevant_pct + '%' }"></div>
              </div>
              <div class="atp-listbars__pct">{{ row.relevant_pct }}%</div>
            </li>
          </ul>
        </details>

        <div class="atp-results__actions">
          <button class="atp-bigbtn atp-bigbtn--ghost" @click="restart">
            ↺ {{ $t('agileTraining.play.resultsScreen.replay') }}
          </button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

const STORAGE_KEY_PREFIX = 'agile_training_participant_';
const ANSWER_SEEN_PREFIX = 'agile_training_seen_';

export default {
  name: 'AgilePrinciplesPlay',
  data() {
    return {
      loading: true,
      error: '',
      stage: 'start', // 'start' | 'swipe' | 'results'
      group: { name: '', slug: '' },
      session: { title: '' },
      principles: [],
      principlesTotal: 0,
      displayName: '',
      participantToken: '',
      starting: false,
      submitting: false,
      currentIndex: 0,
      answeredKeys: [],
      showingResult: false,
      lastResult: null,
      rewriteDraft: '',
      savingRewrite: false,
      resultsData: null,
      drag: { active: false, startX: 0, dx: 0 }
    };
  },
  computed: {
    slug() {
      return this.$route.params.slug;
    },
    storageKey() {
      return STORAGE_KEY_PREFIX + this.slug;
    },
    seenKey() {
      return ANSWER_SEEN_PREFIX + this.slug;
    },
    currentPrinciple() {
      return this.principles[this.currentIndex] || null;
    },
    answeredCount() {
      return this.answeredKeys.length;
    },
    cardStyle() {
      const dx = this.drag.dx;
      const rotate = Math.max(-18, Math.min(18, dx * 0.08));
      return {
        transform: `translateX(${dx}px) rotate(${rotate}deg)`,
        transition: this.drag.active ? 'none' : 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
      };
    }
  },
  async mounted() {
    await this.loadGroup();
  },
  methods: {
    hintOpacity(side) {
      const dx = this.drag.dx;
      if (side === 'right' && dx > 0) return Math.min(1, dx / 120);
      if (side === 'left' && dx < 0) return Math.min(1, -dx / 120);
      return 0;
    },

    async loadGroup() {
      // Если пользователь ещё не выбирал язык сам — применим язык из сессии фасилитатора.
      // Если выбирал — уважаем его выбор (не трогаем i18n.locale).
      const hadExplicitLanguage = (() => {
        try { return !!localStorage.getItem('language'); } catch (_) { return false; }
      })();

      try {
        const [groupRes, principlesRes] = await Promise.all([
          axios.get(`/api/agile-training/g/${this.slug}`),
          axios.get('/api/agile-training/content/principles')
        ]);
        this.group = groupRes.data.group;
        this.session = groupRes.data.session;
        this.principlesTotal = groupRes.data.principles_total || 12;
        this.principles = principlesRes.data.principles || [];

        const sessionLocale = this.session?.locale;
        if (!hadExplicitLanguage && (sessionLocale === 'ru' || sessionLocale === 'en')) {
          this.$i18n.locale = sessionLocale;
          // В localStorage не пишем — это подсказка от организатора, а не явный выбор пользователя.
          // Так при возвращении на главную сайта автодетект продолжит работать.
        }

        this.participantToken = localStorage.getItem(this.storageKey) || '';
        try {
          const rawSeen = localStorage.getItem(this.seenKey);
          this.answeredKeys = rawSeen ? JSON.parse(rawSeen) : [];
        } catch (e) {
          this.answeredKeys = [];
        }
      } catch (e) {
        this.error = e.response?.data?.error || this.$t('agileTraining.play.error.notFound');
      } finally {
        this.loading = false;
      }
    },

    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* ignore */ }
    },

    async startSession() {
      this.starting = true;
      try {
        const payload = { display_name: this.displayName.trim() };
        if (this.participantToken) payload.participant_token = this.participantToken;
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, payload);
        this.participantToken = res.data.participant_token;
        localStorage.setItem(this.storageKey, this.participantToken);

        this.currentIndex = this.findNextUnansweredIndex(0);
        if (this.currentIndex >= this.principlesTotal) {
          await this.goToResults();
        } else {
          this.stage = 'swipe';
          this.resetDrag();
        }
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to start');
      } finally {
        this.starting = false;
      }
    },

    findNextUnansweredIndex(from = 0) {
      for (let i = from; i < this.principles.length; i++) {
        if (!this.answeredKeys.includes(this.principles[i].key)) return i;
      }
      return this.principles.length;
    },

    onPointerDown(e) {
      if (this.submitting || this.showingResult) return;
      this.drag.active = true;
      this.drag.startX = e.clientX;
      this.drag.dx = 0;
      e.currentTarget.setPointerCapture?.(e.pointerId);
    },
    onPointerMove(e) {
      if (!this.drag.active) return;
      this.drag.dx = e.clientX - this.drag.startX;
    },
    onPointerUp() {
      if (!this.drag.active) return;
      const dx = this.drag.dx;
      this.drag.active = false;
      const threshold = 120;
      if (dx > threshold) {
        this.submit('relevant');
      } else if (dx < -threshold) {
        this.submit('outdated');
      } else {
        this.resetDrag();
      }
    },
    resetDrag() { this.drag = { active: false, startX: 0, dx: 0 }; },

    async submit(value) {
      if (!this.currentPrinciple || this.submitting) return;
      this.submitting = true;
      const principle = this.currentPrinciple;
      this.drag.dx = value === 'relevant' ? 500 : -500;
      try {
        const res = await axios.post(`/api/agile-training/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          principle_key: principle.key,
          value
        });
        this.lastResult = res.data;
        if (!this.answeredKeys.includes(principle.key)) {
          this.answeredKeys.push(principle.key);
          localStorage.setItem(this.seenKey, JSON.stringify(this.answeredKeys));
        }
        setTimeout(() => {
          this.showingResult = true;
          this.rewriteDraft = '';
        }, 260);
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to submit');
        this.resetDrag();
      } finally {
        this.submitting = false;
      }
    },

    async saveRewrite() {
      const text = this.rewriteDraft.trim();
      if (!text || !this.currentPrinciple || !this.lastResult) return;
      this.savingRewrite = true;
      try {
        await axios.post(`/api/agile-training/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          principle_key: this.currentPrinciple.key,
          value: this.stageLastValue(),
          rewrite: text
        });
        this.rewriteDraft = '';
        alert(this.$t('agileTraining.play.rewrite.saved'));
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save rewrite');
      } finally {
        this.savingRewrite = false;
      }
    },
    stageLastValue() {
      const pct = this.lastResult?.stats?.relevant_pct || 0;
      return pct >= 50 ? 'relevant' : 'outdated';
    },

    async nextCard() {
      this.showingResult = false;
      this.lastResult = null;
      this.resetDrag();
      const next = this.findNextUnansweredIndex(this.currentIndex + 1);
      if (next >= this.principlesTotal) {
        await this.goToResults();
      } else {
        this.currentIndex = next;
      }
    },

    async goToResults() {
      this.stage = 'results';
      this.resultsData = null;
      try {
        const res = await axios.get(`/api/agile-training/g/${this.slug}/results`);
        this.resultsData = res.data;
      } catch (e) {
        this.error = e.response?.data?.error || 'Failed to load results';
      }
    },

    async restart() {
      localStorage.removeItem(this.seenKey);
      this.answeredKeys = [];
      this.currentIndex = 0;
      this.lastResult = null;
      this.showingResult = false;
      this.stage = 'swipe';
      this.resetDrag();
    }
  }
};
</script>

<style scoped>
.atp-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #faf5ff 0%, #eff6ff 100%);
  padding: 24px 16px 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
  color: #0f172a;
  position: relative;
}
.atp-lang {
  position: absolute;
  top: 18px;
  right: 18px;
  display: inline-flex;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.08);
  z-index: 10;
}
.atp-lang__btn {
  background: transparent;
  border: none;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  font-family: inherit;
  letter-spacing: 0.5px;
  transition: all 0.15s ease;
}
.atp-lang__btn:hover { color: #7c3aed; background: #faf5ff; }
.atp-lang__btn--active {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
}
.atp-lang__btn--active:hover { color: #fff; background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); }
.atp-state {
  max-width: 520px;
  margin: 120px auto;
  text-align: center;
  color: #475569;
}
.atp-state--error { color: #b91c1c; }

/* start screen */
.atp-start {
  max-width: 520px;
  margin: 60px auto;
  background: #fff;
  border-radius: 24px;
  padding: 36px 28px;
  text-align: center;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.08);
}
.atp-start__kicker {
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-size: 11px;
  color: #7c3aed;
  font-weight: 700;
  margin-bottom: 6px;
}
.atp-start h1 { margin: 0 0 14px; font-size: 32px; letter-spacing: -0.5px; }
.atp-start__lead { color: #475569; line-height: 1.6; margin: 0 0 18px; font-size: 16px; }
.atp-start__steps {
  text-align: left;
  background: #f8fafc;
  border-radius: 12px;
  padding: 14px 18px 14px 34px;
  margin: 0 0 20px;
  color: #334155;
  font-size: 14px;
  line-height: 1.7;
}
.atp-start__input {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 16px;
  margin-bottom: 16px;
  box-sizing: border-box;
  font-family: inherit;
}
.atp-start__input:focus { outline: none; border-color: #8b5cf6; box-shadow: 0 0 0 4px rgba(139,92,246,0.15); }
.atp-start__btn {
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
  border: none;
  padding: 16px;
  font-size: 17px;
  font-weight: 700;
  border-radius: 14px;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.35);
  font-family: inherit;
  transition: all 0.2s ease;
}
.atp-start__btn:hover { transform: translateY(-1px); box-shadow: 0 12px 26px rgba(139, 92, 246, 0.45); }
.atp-start__btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
.atp-start__resume { margin-top: 14px; color: #64748b; font-size: 13px; }

/* swipe screen */
.atp-swipe {
  max-width: 520px;
  margin: 0 auto;
}
.atp-swipe__bar {
  display: flex; justify-content: space-between; align-items: center;
  padding: 12px 6px; margin-bottom: 16px;
  color: #475569; font-weight: 600; font-size: 14px;
}
.atp-swipe__progress {
  background: #fff;
  padding: 6px 14px;
  border-radius: 999px;
  box-shadow: 0 4px 10px rgba(15, 23, 42, 0.08);
}

.atp-swipe__track {
  height: 420px;
  position: relative;
  margin-bottom: 20px;
}
.atp-card {
  position: absolute; inset: 0;
  background: #fff;
  border-radius: 22px;
  box-shadow: 0 20px 40px rgba(15, 23, 42, 0.12);
  padding: 28px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  cursor: grab;
  user-select: none;
  touch-action: none;
  overflow: hidden;
}
.atp-card:active { cursor: grabbing; }
.atp-card__idx {
  align-self: flex-start;
  background: #eef2ff; color: #4338ca;
  padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700;
}
.atp-card__title { margin: 0; font-size: 26px; line-height: 1.3; letter-spacing: -0.3px; }
.atp-card__text { margin: 0; color: #334155; font-size: 17px; line-height: 1.55; }
.atp-card__hint {
  position: absolute; top: 24px;
  padding: 6px 14px; border-radius: 10px;
  font-weight: 700; font-size: 18px; letter-spacing: 1px;
  text-transform: uppercase;
  pointer-events: none;
  transition: opacity 0.1s ease;
}
.atp-card__hint--left {
  left: 24px;
  color: #b91c1c; border: 3px solid #b91c1c;
  transform: rotate(-12deg);
}
.atp-card__hint--right {
  right: 24px;
  color: #15803d; border: 3px solid #15803d;
  transform: rotate(12deg);
}

.atp-swipe__buttons {
  display: flex; gap: 12px;
  margin-bottom: 20px;
}
.atp-bigbtn {
  flex: 1;
  padding: 16px;
  font-size: 16px;
  font-weight: 700;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  font-family: inherit;
  transition: all 0.2s ease;
}
.atp-bigbtn:disabled { opacity: 0.6; cursor: not-allowed; }
.atp-bigbtn--left { background: #fff; color: #b91c1c; border: 2px solid #fecaca; }
.atp-bigbtn--left:hover { background: #fef2f2; border-color: #f87171; }
.atp-bigbtn--right { background: #fff; color: #15803d; border: 2px solid #bbf7d0; }
.atp-bigbtn--right:hover { background: #f0fdf4; border-color: #4ade80; }
.atp-bigbtn--primary {
  width: 100%;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
  box-shadow: 0 8px 20px rgba(139, 92, 246, 0.35);
}
.atp-bigbtn--primary:hover { transform: translateY(-1px); box-shadow: 0 12px 26px rgba(139, 92, 246, 0.45); }
.atp-bigbtn--ghost {
  background: #fff; color: #334155;
  border: 1px solid #cbd5e1;
}
.atp-bigbtn--ghost:hover { background: #f1f5f9; border-color: #94a3b8; }

/* result */
.atp-result {
  background: #fff;
  border-radius: 20px;
  padding: 22px;
  box-shadow: 0 16px 32px rgba(15, 23, 42, 0.08);
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.atp-result h3 { margin: 0; font-size: 18px; }
.atp-bars { display: flex; flex-direction: column; gap: 10px; }
.atp-bar { display: grid; grid-template-columns: 110px 1fr auto; align-items: center; gap: 10px; font-size: 14px; }
.atp-bar__label { font-weight: 600; color: #334155; }
.atp-bar__track { height: 10px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.atp-bar__fill { height: 100%; transition: width 0.6s ease; }
.atp-bar__fill--green { background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); }
.atp-bar__fill--red { background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%); }
.atp-bar__pct { font-weight: 700; color: #0f172a; min-width: 44px; text-align: right; }
.atp-result__total { color: #64748b; margin: 0; font-size: 13px; }
.atp-result__quote {
  margin: 0;
  background: linear-gradient(135deg, #faf5ff 0%, #eff6ff 100%);
  border-left: 4px solid #8b5cf6;
  padding: 12px 16px;
  border-radius: 10px;
  color: #334155;
  line-height: 1.55;
  font-size: 14px;
}

.atp-rewrite summary { cursor: pointer; font-weight: 600; color: #7c3aed; }
.atp-rewrite textarea {
  width: 100%;
  margin-top: 10px;
  padding: 12px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-family: inherit;
  font-size: 14px;
  resize: vertical;
  box-sizing: border-box;
}
.atp-rewrite textarea:focus { outline: none; border-color: #8b5cf6; }

/* results screen */
.atp-results {
  max-width: 720px;
  margin: 0 auto;
}
.atp-results__head { text-align: center; margin-bottom: 22px; }
.atp-results__head h1 { margin: 0 0 6px; font-size: 30px; }
.atp-muted { color: #64748b; font-size: 13px; }
.atp-block {
  background: #fff;
  border-radius: 18px;
  padding: 20px 24px;
  margin-bottom: 16px;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}
.atp-block h2 { margin: 0 0 6px; font-size: 18px; }
.atp-listbars { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 10px; }
.atp-listbars li {
  display: grid; grid-template-columns: 1fr 1.4fr auto; gap: 12px; align-items: center;
  font-size: 13px;
}
.atp-listbars__name { font-weight: 600; color: #0f172a; }
.atp-listbars__track { height: 10px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.atp-listbars__fill { height: 100%; background: linear-gradient(90deg, #22c55e 0%, #16a34a 100%); }
.atp-listbars__fill--mix { background: linear-gradient(90deg, #22c55e 0%, #ef4444 100%); }
.atp-listbars__pct { text-align: right; font-weight: 600; color: #334155; min-width: 70px; }
.atp-compare { list-style: none; padding: 0; margin: 10px 0 0; display: grid; gap: 10px; }
.atp-compare__name { font-weight: 600; margin-bottom: 4px; color: #0f172a; }
.atp-compare__row { display: flex; gap: 14px; flex-wrap: wrap; color: #475569; font-size: 13px; }
.atp-diff { font-weight: 700; }
.atp-diff--up { color: #16a34a; }
.atp-diff--down { color: #b91c1c; }
.atp-all summary { cursor: pointer; font-weight: 700; color: #1f2937; }

.atp-results__actions {
  display: flex; justify-content: center; margin-top: 20px;
}
</style>
