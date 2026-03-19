<template>
  <div class="roadmap-list-container">
    <div class="list-header">
      <h1>Дорожные карты зависимостей</h1>
      <button @click="showCreateModal = true" class="create-btn">➕ Создать карту</button>
    </div>

    <div v-if="loading" class="loading">Загрузка...</div>
    <div v-else-if="roadmaps.length === 0" class="empty-state">
      <p>У вас пока нет дорожных карт</p>
      <button @click="showCreateModal = true" class="create-btn">Создать первую карту</button>
    </div>
    <div v-else class="roadmaps-grid">
      <div v-for="roadmap in roadmaps" :key="roadmap.id" class="roadmap-card" @click="openRoadmap(roadmap.id)">
        <h3>{{ roadmap.name }}</h3>
        <p class="meta">Элементов: {{ roadmap.item_count }}</p>
        <p class="meta">Обновлено: {{ formatDate(roadmap.updated_at) }}</p>
        <div class="card-actions">
          <button @click.stop="openRoadmap(roadmap.id)" class="open-btn">Открыть</button>
          <button @click.stop="deleteRoadmap(roadmap.id)" class="delete-btn">🗑</button>
        </div>
      </div>
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
          <button @click="createRoadmap" class="save-btn">Создать</button>
          <button @click="showCreateModal = false" class="cancel-btn">Отмена</button>
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
}

.list-header h1 {
  margin: 0;
  font-size: 32px;
  color: #333;
}

.create-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  box-shadow: 0 4px 12px rgba(33, 150, 243, 0.3);
  transition: all 0.2s;
}

.create-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(33, 150, 243, 0.4);
}

.loading {
  text-align: center;
  padding: 40px;
  color: #666;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #666;
}

.roadmaps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.roadmap-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.3s;
}

.roadmap-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.roadmap-card h3 {
  margin: 0 0 12px;
  font-size: 20px;
  color: #333;
}

.meta {
  margin: 8px 0;
  color: #666;
  font-size: 14px;
}

.card-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.open-btn {
  flex: 1;
  padding: 8px 16px;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
}

.delete-btn {
  padding: 8px 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
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
  margin-top: 24px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.save-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 600;
}

.save-btn {
  background: #4CAF50;
  color: white;
}

.cancel-btn {
  background: #f5f5f5;
  color: #333;
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
