<template>
  <div class="iceberg-container">
    <h1>🧊 Айсберг системного мышления</h1>

    <!-- Список существующих айсбергов -->
    <div class="iceberg-list-section">
      <div class="filter-bar">
        <button @click="showCreateForm = true" class="add-btn">➕ Создать новый айсберг</button>
      </div>

      <div class="iceberg-list">
        <div
          v-for="iceberg in icebergs"
          :key="iceberg.id"
          class="iceberg-card"
          @click="openIceberg(iceberg)"
        >
          <h3>🧊 Айсберг #{{ iceberg.id }}</h3>
          <p><strong>Событие:</strong> {{ (iceberg.event || 'Не указано').slice(0, 100) }}{{ iceberg.event && iceberg.event.length > 100 ? '...' : '' }}</p>
          <p><strong>Текущий уровень:</strong> {{ getLevelName(iceberg.current_level) }}</p>
          <div v-if="iceberg.solutions" class="solutions-badge">✅ Решения готовы</div>
          <button class="delete-btn" @click.stop="deleteIceberg(iceberg.id)">🗑</button>
        </div>
      </div>
    </div>

    <!-- Форма создания нового айсберга -->
    <div class="modal-overlay" v-if="showCreateForm">
      <div class="modal-content">
        <h2>Создать новый айсберг</h2>
        <div class="modern-form">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">📝</span>
            <textarea
              v-model="newEvent"
              rows="4"
              class="modern-input modern-textarea"
              :class="{ 'has-value': newEvent }"
              placeholder="Опишите событие или проблему..."
            ></textarea>
            <label class="floating-label">Событие</label>
          </div>
        </div>
        <div class="modal-actions">
          <button class="save-btn" @click="createIceberg" :disabled="!newEvent.trim() || creating">
            {{ creating ? 'Создание...' : 'Создать' }}
          </button>
          <button class="modal-close" @click="showCreateForm = false">✖</button>
        </div>
      </div>
    </div>

    <!-- Работа с айсбергом -->
    <div class="modal-overlay" v-if="showIcebergModal && currentIceberg">
      <div class="modal-content iceberg-modal">
        <h2>🧊 Айсберг системного мышления</h2>

        <!-- Визуализация уровней -->
        <div class="iceberg-visualization">
          <div class="iceberg-level" :class="{ active: currentIceberg.current_level === 'event', completed: currentIceberg.event }">
            <div class="level-header">
              <span class="level-number">1</span>
              <span class="level-title">Событие</span>
            </div>
            <div class="level-content" v-if="currentIceberg.event">
              {{ currentIceberg.event }}
            </div>
          </div>

          <div class="iceberg-level" :class="{ active: currentIceberg.current_level === 'pattern', completed: currentIceberg.pattern }">
            <div class="level-header">
              <span class="level-number">2</span>
              <span class="level-title">Паттерн поведения</span>
            </div>
            <div class="level-content" v-if="currentIceberg.pattern">
              {{ currentIceberg.pattern }}
            </div>
          </div>

          <div class="iceberg-level" :class="{ active: currentIceberg.current_level === 'system_structure', completed: currentIceberg.system_structure }">
            <div class="level-header">
              <span class="level-number">3</span>
              <span class="level-title">Системная структура</span>
            </div>
            <div class="level-content" v-if="currentIceberg.system_structure">
              {{ currentIceberg.system_structure }}
            </div>
          </div>

          <div class="iceberg-level" :class="{ active: currentIceberg.current_level === 'mental_model', completed: currentIceberg.mental_model }">
            <div class="level-header">
              <span class="level-number">4</span>
              <span class="level-title">Ментальная модель</span>
            </div>
            <div class="level-content" v-if="currentIceberg.mental_model">
              {{ currentIceberg.mental_model }}
            </div>
          </div>

          <div class="iceberg-level" :class="{ active: currentIceberg.current_level === 'experience', completed: currentIceberg.experience }">
            <div class="level-header">
              <span class="level-number">5</span>
              <span class="level-title">Опыт</span>
            </div>
            <div class="level-content" v-if="currentIceberg.experience">
              {{ currentIceberg.experience }}
            </div>
          </div>
        </div>

        <!-- Текущий вопрос -->
        <div v-if="currentQuestion && currentIceberg.current_level !== 'completed'" class="question-block">
          <div class="question-text">{{ currentQuestion }}</div>
          
          <div v-if="suggestions.length > 0" class="suggestions-block">
            <p class="suggestions-title">💡 Предложения:</p>
            <div class="suggestions-list">
              <button
                v-for="(suggestion, index) in suggestions"
                :key="index"
                class="suggestion-btn"
                @click="selectSuggestion(suggestion)"
              >
                {{ suggestion }}
              </button>
            </div>
          </div>

          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">✍️</span>
            <textarea
              v-model="currentAnswer"
              rows="3"
              class="modern-input modern-textarea"
              :class="{ 'has-value': currentAnswer }"
              placeholder="Введите ваш ответ или напишите 'не знаю' для получения предложений..."
            ></textarea>
            <label class="floating-label">Ваш ответ</label>
          </div>

          <div class="modal-actions">
            <button class="generate-btn" @click="submitAnswer" :disabled="!currentAnswer.trim() || loading">
              {{ loading ? 'Обработка...' : 'Ответить' }}
            </button>
            <button class="modal-close" @click="showIcebergModal = false">✖</button>
          </div>
        </div>

        <!-- Решения -->
        <div v-if="currentIceberg.solutions && currentIceberg.solutions.length > 0" class="solutions-block">
          <h3>💡 Решения</h3>
          <div
            v-for="(solution, index) in currentIceberg.solutions"
            :key="index"
            class="solution-card"
          >
            <h4>{{ solution.title }}</h4>
            <p>{{ solution.text }}</p>
          </div>
        </div>

        <!-- Кнопка генерации решений если все заполнено -->
        <div v-if="currentIceberg.current_level === 'experience' && !currentIceberg.solutions" class="generate-solutions-block">
          <button class="generate-btn" @click="generateSolutions" :disabled="generatingSolutions">
            {{ generatingSolutions ? 'Генерация решений...' : 'Сгенерировать решения' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      icebergs: [],
      showCreateForm: false,
      showIcebergModal: false,
      currentIceberg: null,
      newEvent: "",
      creating: false,
      currentQuestion: "",
      currentAnswer: "",
      suggestions: [],
      loading: false,
      generatingSolutions: false
    };
  },

  methods: {
    async fetchIcebergs() {
      const token = localStorage.getItem("token");
      try {
        const res = await fetch("/api/system-thinking", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        if (res.ok) {
          this.icebergs = await res.json();
        }
      } catch (err) {
        console.error("Ошибка загрузки айсбергов:", err);
      }
    },

    async createIceberg() {
      if (!this.newEvent.trim()) return;
      
      this.creating = true;
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch("/api/system-thinking", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ event: this.newEvent })
        });

        if (res.ok) {
          const iceberg = await res.json();
          this.showCreateForm = false;
          this.newEvent = "";
          await this.fetchIcebergs();
          this.openIceberg(iceberg);
        } else {
          alert("Ошибка при создании айсберга");
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка соединения");
      } finally {
        this.creating = false;
      }
    },

    async openIceberg(iceberg) {
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch(`/api/system-thinking/${iceberg.id}`, {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (res.ok) {
          this.currentIceberg = await res.json();
          this.showIcebergModal = true;
          
          // Если айсберг не завершен, получаем текущий вопрос
          if (this.currentIceberg.current_level !== 'completed') {
            await this.getCurrentQuestion();
          }
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка загрузки айсберга");
      }
    },

    async getCurrentQuestion() {
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch(`/api/system-thinking/${this.currentIceberg.id}/ask-question`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ response: "" })
        });

        if (res.ok) {
          const data = await res.json();
          this.currentQuestion = data.question || data.next_question;
          this.suggestions = data.suggestions || [];
          
          // Если получен следующий вопрос, обновляем айсберг
          if (data.iceberg) {
            this.currentIceberg = data.iceberg;
          }
        }
      } catch (err) {
        console.error(err);
      }
    },

    async submitAnswer() {
      if (!this.currentAnswer.trim()) return;
      
      this.loading = true;
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch(`/api/system-thinking/${this.currentIceberg.id}/ask-question`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({ response: this.currentAnswer })
        });

        if (res.ok) {
          const data = await res.json();
          
          // Если получены решения, значит айсберг завершен
          if (data.solutions) {
            this.currentIceberg.solutions = data.solutions;
            this.currentIceberg.current_level = "completed";
            this.currentQuestion = "";
          } else {
            // Обновляем текущий вопрос
            this.currentQuestion = data.next_question || data.question;
            this.suggestions = data.suggestions || [];
            this.currentAnswer = "";
            
            // Обновляем айсберг
            if (data.iceberg) {
              this.currentIceberg = data.iceberg;
            } else {
              await this.openIceberg({ id: this.currentIceberg.id });
            }
          }
        } else {
          const error = await res.json();
          alert(error.error || "Ошибка при сохранении ответа");
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка соединения");
      } finally {
        this.loading = false;
      }
    },

    selectSuggestion(suggestion) {
      this.currentAnswer = suggestion;
    },

    async generateSolutions() {
      this.generatingSolutions = true;
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch(`/api/system-thinking/${this.currentIceberg.id}/generate-solutions`, {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (res.ok) {
          const data = await res.json();
          this.currentIceberg.solutions = data.solutions;
          this.currentIceberg.current_level = "completed";
        } else {
          const error = await res.json();
          alert(error.error || "Ошибка генерации решений");
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка соединения");
      } finally {
        this.generatingSolutions = false;
      }
    },

    async deleteIceberg(id) {
      if (!confirm("Удалить этот айсберг?")) return;
      
      const token = localStorage.getItem("token");
      
      try {
        const res = await fetch(`/api/system-thinking/${id}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        if (res.ok) {
          await this.fetchIcebergs();
          if (this.currentIceberg && this.currentIceberg.id === id) {
            this.showIcebergModal = false;
            this.currentIceberg = null;
          }
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка удаления");
      }
    },

    getLevelName(level) {
      const names = {
        event: "Событие",
        pattern: "Паттерн поведения",
        system_structure: "Системная структура",
        mental_model: "Ментальная модель",
        experience: "Опыт",
        completed: "Завершен"
      };
      return names[level] || level;
    }
  },

  async mounted() {
    await this.fetchIcebergs();
  }
};
</script>

<style scoped>
.iceberg-container {
  max-width: 1280px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #1a1a1a;
}

.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.add-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.iceberg-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.iceberg-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.iceberg-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.iceberg-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #111827;
}

.iceberg-card p {
  font-size: 14px;
  color: #6b7280;
  margin: 8px 0;
  line-height: 1.6;
}

.solutions-badge {
  display: inline-block;
  background: #10b981;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 12px;
}

.delete-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
}

.delete-btn:hover {
  background: #dc2626;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #ffffff;
  padding: 40px;
  border-radius: 20px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.iceberg-modal {
  max-width: 900px;
}

.iceberg-visualization {
  margin: 32px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.iceberg-level {
  padding: 20px;
  border-radius: 12px;
  border: 2px solid #e5e7eb;
  background: #f9fafb;
  transition: all 0.3s ease;
}

.iceberg-level.active {
  border-color: #3b82f6;
  background: #eff6ff;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
}

.iceberg-level.completed {
  border-color: #10b981;
  background: #f0fdf4;
}

.level-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.level-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  font-weight: 600;
  font-size: 14px;
}

.iceberg-level.completed .level-number {
  background: #10b981;
}

.level-title {
  font-weight: 600;
  font-size: 16px;
  color: #111827;
}

.level-content {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  padding-left: 44px;
}

.question-block {
  margin-top: 32px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 12px;
}

.question-text {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
}

.suggestions-block {
  margin-bottom: 24px;
}

.suggestions-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-btn {
  background: white;
  border: 2px solid #e5e7eb;
  padding: 12px 16px;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #374151;
}

.suggestion-btn:hover {
  border-color: #3b82f6;
  background: #eff6ff;
  transform: translateX(4px);
}

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
  top: 24px;
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
  font-family: inherit;
  transition: all 0.3s ease;
  background: white;
  box-sizing: border-box;
}

.modern-textarea {
  padding-top: 32px;
  min-height: 100px;
  resize: vertical;
  line-height: 1.6;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 32px;
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s ease;
  background: transparent;
  z-index: 1;
}

.modern-input:focus,
.modern-input.has-value {
  border-color: #3b82f6;
  outline: none;
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
}

.modal-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.modal-actions button {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.generate-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.modal-close {
  background: #f3f4f6;
  color: #374151;
  font-size: 20px;
  padding: 10px 16px;
  min-width: 44px;
}

.modal-close:hover {
  background: #e5e7eb;
}

.solutions-block {
  margin-top: 32px;
  padding: 24px;
  background: #f0fdf4;
  border-radius: 12px;
  border: 2px solid #10b981;
}

.solutions-block h3 {
  font-size: 20px;
  font-weight: 700;
  color: #059669;
  margin-bottom: 20px;
}

.solution-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
  border-left: 4px solid #10b981;
}

.solution-card h4 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.solution-card p {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.generate-solutions-block {
  margin-top: 32px;
  text-align: center;
}

@media (max-width: 768px) {
  .iceberg-container {
    margin: 20px 10px;
    padding: 20px;
  }

  .iceberg-list {
    grid-template-columns: 1fr;
  }

  .modal-content {
    padding: 24px 20px;
    max-width: 100%;
  }
}
</style>
