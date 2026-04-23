<template>
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
import AgilePrinciplesPlay from '@/views/AgilePrinciplesPlay.vue';
import AgileCynefinPlay from '@/views/AgileCynefinPlay.vue';
import AgileIcebergPlay from '@/views/AgileIcebergPlay.vue';
import AgileMvpPlay from '@/views/AgileMvpPlay.vue';
import AgileDorDodPlay from '@/views/AgileDorDodPlay.vue';
import AgileWsjfPlay from '@/views/AgileWsjfPlay.vue';
import AgileScrumEventsPlay from '@/views/AgileScrumEventsPlay.vue';
import AgileScrumRolesPlay from '@/views/AgileScrumRolesPlay.vue';

const REMOVED_WORKSHOP_KEYS = new Set(['product_stories', 'user_story_map', 'kanban_system']);

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
  },
  data() {
    return {
      loading: true,
      error: '',
      session: null,
    };
  },
  computed: {
    slug() { return this.$route.params.slug; },
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
      }
    } catch (e) {
      this.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
    } finally {
      this.loading = false;
    }
  },
};
</script>

<style scoped>
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
