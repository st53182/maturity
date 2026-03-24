<template>
  <div class="roadmap-list-container">
    <header class="list-header">
      <div class="list-header__text">
        <h1>Дорожные карты</h1>
        <p class="list-lead">
          Эпики и истории на временной сетке, связи между работами и совместное редактирование.
        </p>
      </div>
      <button type="button" class="rm-btn rm-btn--primary" @click="showCreateModal = true">Новая карта</button>
    </header>

    <div v-if="loading" class="loading">Загрузка…</div>
    <div v-else-if="roadmaps.length === 0" class="empty-state">
      <p class="empty-title">Пока нет карт</p>
      <p class="empty-hint">Создайте первую дорожную карту для команды или продукта.</p>
      <button type="button" class="rm-btn rm-btn--primary" @click="showCreateModal = true">Создать карту</button>
    </div>
    <div v-else class="roadmaps-grid">
      <article
        v-for="roadmap in roadmaps"
        :key="roadmap.id"
        class="roadmap-card"
        tabindex="0"
        role="button"
        @click="openRoadmap(roadmap.id)"
        @keydown.enter.prevent="openRoadmap(roadmap.id)"
      >
        <h3>{{ roadmap.name }}</h3>
        <dl class="card-meta">
          <div>
            <dt>Элементов</dt>
            <dd>{{ roadmap.item_count }}</dd>
          </div>
          <div>
            <dt>Обновлено</dt>
            <dd>{{ formatDate(roadmap.updated_at) }}</dd>
          </div>
        </dl>
        <div class="card-actions">
          <button type="button" class="rm-btn rm-btn--secondary rm-btn--sm" @click.stop="openRoadmap(roadmap.id)">
            Открыть
          </button>
          <button
            type="button"
            class="rm-btn rm-btn--danger rm-btn--sm"
            title="Удалить карту"
            @click.stop="deleteRoadmap(roadmap.id)"
          >
            Удалить
          </button>
        </div>
      </article>
    </div>

    <!-- Модальное окно создания карты -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content">
        <button class="modal-close-top" @click="showCreateModal = false" aria-label="Close">✕</button>
        <h2>Создать дорожную карту</h2>
        <div class="modern-form">
          <div class="input-wrapper">
            <span class="input-icon">📋</span>
            <input v-model="newRoadmapName" class="modern-input" :class="{ 'has-value': newRoadmapName }" />
            <label class="floating-label">Название карты</label>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="rm-btn rm-btn--primary" @click="createRoadmap">Создать</button>
          <button type="button" class="rm-btn rm-btn--quiet" @click="showCreateModal = false">Отмена</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "RoadmapList",
  data() {
    return {
      roadmaps: [],
      loading: true,
      showCreateModal: false,
      newRoadmapName: ""
    };
  },
  async mounted() {
    await this.loadRoadmaps();
  },
  methods: {
    async loadRoadmaps() {
      try {
        this.loading = true;
        const token = localStorage.getItem("token");
        const { data } = await axios.get("/api/roadmap", {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.roadmaps = data;
      } catch (error) {
        console.error("Ошибка загрузки карт:", error);
        alert("Ошибка загрузки дорожных карт");
      } finally {
        this.loading = false;
      }
    },
    async createRoadmap() {
      if (!this.newRoadmapName.trim()) {
        alert("Введите название карты");
        return;
      }

      try {
        const token = localStorage.getItem("token");
        const { data } = await axios.post("/api/roadmap", {
          name: this.newRoadmapName
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.showCreateModal = false;
        this.newRoadmapName = "";
        await this.loadRoadmaps();
        this.$router.push(`/roadmap/${data.id}`);
      } catch (error) {
        console.error("Ошибка создания карты:", error);
        alert("Ошибка создания дорожной карты");
      }
    },
    openRoadmap(id) {
      this.$router.push(`/roadmap/${id}`);
    },
    async deleteRoadmap(id) {
      if (!confirm("Вы уверены, что хотите удалить эту дорожную карту?")) {
        return;
      }

      try {
        const token = localStorage.getItem("token");
        await axios.delete(`/api/roadmap/${id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        await this.loadRoadmaps();
      } catch (error) {
        console.error("Ошибка удаления карты:", error);
        alert("Ошибка удаления дорожной карты");
      }
    },
    formatDate(dateString) {
      if (!dateString) return "";
      const date = new Date(dateString);
      return date.toLocaleDateString("ru-RU");
    }
  }
};
</script>

<style scoped>
.roadmap-list-container {
  max-width: 1120px;
  margin: 0 auto;
  padding: 1.5rem 1rem 2.5rem;
  box-sizing: border-box;
}

.list-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem 1.25rem;
  margin-bottom: 1.75rem;
}

.list-header__text {
  min-width: 0;
}

.list-header h1 {
  margin: 0 0 0.35rem;
  font-size: 1.65rem;
  font-weight: 700;
  color: var(--vl-text, #0d1733);
  letter-spacing: -0.02em;
}

.list-lead {
  margin: 0;
  max-width: 36rem;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--vl-muted, #5d6b8a);
}

.rm-btn {
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.55rem 1rem;
  line-height: 1.25;
  transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease, border-color 0.15s ease;
}

.rm-btn--sm {
  padding: 0.4rem 0.75rem;
  font-size: 0.8125rem;
}

.rm-btn--primary {
  color: #fff;
  background: linear-gradient(135deg, var(--vl-primary-start, #142b66), var(--vl-primary-end, #2754c7));
  box-shadow: 0 2px 10px rgba(20, 43, 102, 0.22);
}

.rm-btn--primary:hover {
  background: linear-gradient(135deg, var(--vl-primary-hover-start, #102457), var(--vl-primary-hover-end, #1f46ae));
}

.rm-btn--secondary {
  flex: 1;
  color: var(--vl-text, #0d1733);
  background: var(--vl-surface, #fff);
  border: 1px solid var(--vl-border, #d8e0f0);
}

.rm-btn--secondary:hover {
  border-color: rgba(39, 84, 199, 0.35);
  background: var(--vl-surface-soft, #f6f9ff);
}

.rm-btn--quiet {
  color: var(--vl-muted, #5d6b8a);
  background: transparent;
  border: 1px solid transparent;
}

.rm-btn--quiet:hover {
  background: rgba(10, 20, 45, 0.06);
  color: var(--vl-text, #0d1733);
}

.rm-btn--danger {
  color: var(--vl-danger, #d43b50);
  background: rgba(212, 59, 80, 0.08);
  border: 1px solid rgba(212, 59, 80, 0.22);
}

.rm-btn--danger:hover {
  background: rgba(212, 59, 80, 0.12);
  border-color: rgba(212, 59, 80, 0.35);
}

.loading {
  text-align: center;
  padding: 3rem 1rem;
  color: var(--vl-muted, #5d6b8a);
  font-size: 0.9375rem;
}

.empty-state {
  text-align: center;
  padding: 3rem 1.5rem;
  background: var(--vl-surface, #fff);
  border: 1px dashed var(--vl-border, #d8e0f0);
  border-radius: 14px;
  max-width: 28rem;
  margin: 0 auto;
}

.empty-title {
  margin: 0 0 0.35rem;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--vl-text, #0d1733);
}

.empty-hint {
  margin: 0 0 1.25rem;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--vl-muted, #5d6b8a);
}

.roadmaps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.25rem;
}

.roadmap-card {
  background: var(--vl-surface, #fff);
  border-radius: 14px;
  padding: 1.25rem 1.35rem;
  border: 1px solid var(--vl-border, #d8e0f0);
  box-shadow: 0 2px 12px rgba(10, 20, 45, 0.06);
  cursor: pointer;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.roadmap-card:hover,
.roadmap-card:focus-visible {
  outline: none;
  border-color: rgba(39, 84, 199, 0.28);
  box-shadow: 0 8px 28px rgba(10, 20, 45, 0.1);
  transform: translateY(-2px);
}

.roadmap-card h3 {
  margin: 0 0 1rem;
  font-size: 1.05rem;
  font-weight: 700;
  color: var(--vl-text, #0d1733);
  line-height: 1.35;
}

.card-meta {
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
}

.card-meta dt {
  margin: 0;
  font-size: 0.6875rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--vl-muted, #5d6b8a);
}

.card-meta dd {
  margin: 0.2rem 0 0;
  font-size: 0.875rem;
  color: var(--vl-text, #0d1733);
}

.card-actions {
  margin-top: 1.15rem;
  display: flex;
  gap: 0.5rem;
  align-items: stretch;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  padding: 32px;
  border-radius: 12px;
  max-width: 500px;
  width: 90%;
  position: relative;
  border: 1px solid rgba(10, 20, 45, 0.12);
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.24);
}

.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.84);
  cursor: pointer;
  font-size: 18px;
}

.modal-actions {
  margin-top: 1.25rem;
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  flex-wrap: wrap;
}

/* Modern form styles */
.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  box-sizing: border-box;
  color: #111827;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 1;
}

.modern-input:focus,
.modern-input.has-value {
  padding-top: 20px;
  padding-bottom: 8px;
  border-color: #3b82f6;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f7ff 100%);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 4px 12px rgba(59, 130, 246, 0.15);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
  transform: none;
}
</style>
