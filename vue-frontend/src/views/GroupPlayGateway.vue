<template>
  <div class="at-gateway-lang" v-if="!isAuthenticated">
    <button
      type="button"
      class="at-gateway-lang__btn"
      :class="{ 'at-gateway-lang__btn--active': $i18n.locale === 'ru' }"
      :aria-pressed="$i18n.locale === 'ru'"
      @click="switchLanguage('ru')"
    >RU</button>
    <button
      type="button"
      class="at-gateway-lang__btn"
      :class="{ 'at-gateway-lang__btn--active': $i18n.locale === 'en' }"
      :aria-pressed="$i18n.locale === 'en'"
      @click="switchLanguage('en')"
    >EN</button>
  </div>

  <div class="at-gateway" v-if="loading">
    <div class="at-gateway__spinner" />
    <div class="at-gateway__hint">{{ $t('common.loading') }}…</div>
  </div>
  <div class="at-gateway at-gateway--error" v-else-if="error">
    <h1>{{ $t('agileTraining.play.loadError') || 'Не удалось загрузить тренинг' }}</h1>
    <p>{{ error }}</p>
    <router-link to="/agile-training" class="at-gateway__btn">
      {{ $t('agileTraining.hub.backHome') }}
    </router-link>
  </div>

  <component
    v-else
    :is="playComponent"
    :slug="slug"
    :prefetched-session="session"
  />
</template>

<script>
/**
 * Диспетчер публичной страницы `/g/:slug`.
 * Загружает информацию о группе и выбирает компонент геймплея по
 * `session.exercise_key` — чтобы одна ссылка могла вести и на тренинг
 * принципов Agile, и на упражнение Cynefin.
 */
import axios from 'axios';
import { syncI18nFallback } from '@/i18n';
import AgilePrinciplesPlay from '@/views/AgilePrinciplesPlay.vue';
import AgileCynefinPlay from '@/views/AgileCynefinPlay.vue';
import AgileIcebergPlay from '@/views/AgileIcebergPlay.vue';
import AgileMvpPlay from '@/views/AgileMvpPlay.vue';
import AgileDorDodPlay from '@/views/AgileDorDodPlay.vue';
import AgileWsjfPlay from '@/views/AgileWsjfPlay.vue';
import AgileScrumEventsPlay from '@/views/AgileScrumEventsPlay.vue';
import AgileScrumRolesPlay from '@/views/AgileScrumRolesPlay.vue';
import AgileProductThinkingPlay from '@/views/AgileProductThinkingPlay.vue';
import AgileKanbanPlay from '@/views/AgileKanbanPlay.vue';
import AgileScrumSimPlay from '@/views/AgileScrumSimPlay.vue';
import AgilePoPathPlay from '@/views/AgilePoPathPlay.vue';
import AgilePmSimPlay from '@/views/AgilePmSimPlay.vue';

const REMOVED_WORKSHOP_KEYS = new Set(['product_stories', 'user_story_map']);

export default {
  name: 'GroupPlayGateway',
  components: {
    AgilePrinciplesPlay,
    AgileCynefinPlay,
    AgileIcebergPlay,
    AgileMvpPlay,
    AgileDorDodPlay,
    AgileWsjfPlay,
    AgileScrumEventsPlay,
    AgileScrumRolesPlay,
    AgileProductThinkingPlay,
    AgileKanbanPlay,
    AgileScrumSimPlay,
    AgilePoPathPlay,
    AgilePmSimPlay,
  },
  computed: {
    slug() { return this.$route.params.slug; },
    isAuthenticated() {
      try { return !!localStorage.getItem('access_token'); } catch (_) { return false; }
    },
    exerciseKey() {
      return (this.session && this.session.exercise_key) || 'agile_principles';
    },
    playComponent() {
      if (this.exerciseKey === 'cynefin') return 'AgileCynefinPlay';
      if (this.exerciseKey === 'iceberg') return 'AgileIcebergPlay';
      if (this.exerciseKey === 'mvp') return 'AgileMvpPlay';
      if (this.exerciseKey === 'dor_dod') return 'AgileDorDodPlay';
      if (this.exerciseKey === 'wsjf') return 'AgileWsjfPlay';
      if (this.exerciseKey === 'scrum_events') return 'AgileScrumEventsPlay';
      if (this.exerciseKey === 'scrum_roles') return 'AgileScrumRolesPlay';
      if (this.exerciseKey === 'product_thinking') return 'AgileProductThinkingPlay';
      if (this.exerciseKey === 'kanban_system') return 'AgileKanbanPlay';
      if (this.exerciseKey === 'scrum_simulator') return 'AgileScrumSimPlay';
      if (this.exerciseKey === 'po_path') return 'AgilePoPathPlay';
      if (this.exerciseKey === 'pm_sim') return 'AgilePmSimPlay';
      return 'AgilePrinciplesPlay';
    },
  },
  async mounted() {
    try {
      const res = await axios.get(`/api/agile-training/g/${this.slug}`);
      this.session = res.data.session || null;
      const ex = (this.session && this.session.exercise_key) || '';
      if (REMOVED_WORKSHOP_KEYS.has(ex)) {
        this.error = this.$t('agileTraining.play.workshopRemoved');
        this.session = null;
      } else if (this.session && !this.userPickedLocale && (this.session.locale === 'ru' || this.session.locale === 'en')) {
        if (this.$i18n.locale !== this.session.locale) {
          this.$i18n.locale = this.session.locale;
          syncI18nFallback();
        }
      }
    } catch (e) {
      this.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
    } finally {
      this.loading = false;
    }
  },
  methods: {
    switchLanguage(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      syncI18nFallback();
      try {
        localStorage.setItem('language', lang);
        localStorage.setItem('language_user_pick', '1');
      } catch (_) { /* noop */ }
    },
  },
  data() {
    const userPickedLocale = (() => {
      try { return localStorage.getItem('language_user_pick') === '1'; } catch (_) { return false; }
    })();
    return {
      loading: true,
      error: '',
      session: null,
      userPickedLocale,
    };
  },
};
</script>

<style scoped>
.at-gateway-lang {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 1000;
  display: inline-flex;
  gap: 4px;
  background: rgba(255,255,255,0.94);
  padding: 4px;
  border-radius: 999px;
  box-shadow: 0 6px 18px rgba(15,23,42,0.10);
  border: 1px solid #e5e7eb;
}
.at-gateway-lang__btn {
  border: none;
  background: transparent;
  color: #475569;
  font-weight: 700;
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 999px;
  cursor: pointer;
  letter-spacing: 0.4px;
  line-height: 1.1;
}
.at-gateway-lang__btn--active {
  background: #0f172a;
  color: #fff;
}
.at-gateway-lang__btn:hover:not(.at-gateway-lang__btn--active) {
  color: #0f172a;
}
@media print {
  .at-gateway-lang { display: none !important; }
}

.at-gateway {
  min-height: 70vh;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 40px 20px;
  color: #111;
}
.at-gateway__spinner {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 3px solid #eee;
  border-top-color: #111;
  animation: at-spin 0.9s linear infinite;
}
@keyframes at-spin { to { transform: rotate(360deg); } }
.at-gateway--error h1 { font-size: 22px; margin: 0 0 6px; }
.at-gateway--error p { color: #555; max-width: 520px; text-align: center; }
.at-gateway__btn {
  margin-top: 12px; padding: 10px 18px; border-radius: 999px;
  background: #111; color: #fff; text-decoration: none; font-weight: 600;
}
</style>
