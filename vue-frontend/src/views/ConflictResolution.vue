<template>
  <div class="conflict-container">
    <h1>{{ $t('conflicts.title') }}</h1>

    <!-- 🔹 Фильтр -->
    <div class="filter-bar">
      <button
        v-for="s in statuses"
        :key="s"
        :class="{ active: filterStatus === s }"
        @click="filterStatus = s"
      >
        {{ s }}
      </button>
      <button @click="openModal(null)" class="add-btn">➕ {{ $t('conflicts.addConflict') }}</button>
    </div>

    <!-- 🔹 Карточки -->
    <div class="conflict-list">
      <div
        v-for="conflict in filteredConflicts"
        :key="conflict.id"
        class="conflict-card"
      >
        <h3>🧠 {{ conflict.context.slice(0, 100) }}...</h3>
        <p>👥 Участники: {{ getParticipantNames(conflict.participants) }}</p>
        <p>🎯 Цель: {{ conflict.goal }}</p>
        <p>📌 Статус: <strong>{{ conflict.status }}</strong></p>
        <div v-if="conflict.ai_analysis" class="summary-block">
    <strong>📝 Рекомендации:</strong>
    <p v-html="shortenAnalysis(conflict.ai_analysis)"></p>
  </div>
        <button @click="openModal(conflict)">✏️ Открыть или редактировать </button>
        <button class="delete-btn" @click="deleteConflict(conflict.id)">🗑</button>
      </div>
    </div>

    <!-- 🔹 Модальное окно -->
    <div class="modal-overlay" v-if="showModal">

      <div class="modal-content">
        <div v-if="form.ai_response" class="ai-analysis" v-html="form.ai_response"></div>
        <h2>{{ form.id ? $t('conflicts.editConflict') : $t('conflicts.addConflict') }}</h2>
        <label>{{ $t('conflicts.context') }}</label>
        <textarea v-model="form.context" rows="3" placeholder="Опишите суть ситуации, как она возникла, чем детальнее тем лучше..."></textarea>

        <label>{{ $t('conflicts.participants') }}</label>
        <select v-model="form.participants" multiple>
          <option v-for="e in employees" :value="e.id" :key="e.id">{{ e.name }}</option>
        </select>

        <label>{{ $t('conflicts.actionsTaken') }}</label>
        <textarea v-model="form.actions_taken" rows="3" placeholder="Какие шаги уже были предприняты для разрешения?"></textarea>

        <label>{{ $t('conflicts.goal') }}</label>
        <textarea v-model="form.goal" rows="3" placeholder="Какого результата вы хотите достичь?"></textarea>

        <label>{{ $t('conflicts.status') }}</label>
        <select v-model="form.status">
          <option value="Активен">{{ $t('conflicts.active') }}</option>
          <option value="Закрыт">{{ $t('conflicts.resolved') }}</option>
          <option value="Обострение">{{ $t('conflicts.active') }}</option>
        </select>

        <div class="modal-actions">
  <button class="generate-btn" @click="submitConflict" :disabled="loading">
    💬 {{ loading ? $t('conflicts.analyzing') : $t('conflicts.analyze') }}
  </button>
  <button
  v-if="form.id"
  class="save-btn"
  @click="saveConflict"
  :disabled="saving"
>
  💾 {{ saving ? $t('common.loading') : $t('common.save') }}
</button>
  <button class="modal-close" @click="showModal = false">✖</button>
</div>

      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      conflicts: [],
      employees: [],
      showModal: false,
      saving: false,
      loading: false,

      filterStatus: "Все",
      statuses: ["Все", "Активен", "Закрыт", "Обострение"],

      form: {
        id: null,
        context: "",
        participants: [],
        actions_taken: "",
        goal: "",
        status: "Активен",
        ai_response: ""
      }
    };
  },

  computed: {
    filteredConflicts() {
      if (this.filterStatus === "Все") return this.conflicts;
      return this.conflicts.filter(c => c.status === this.filterStatus);
    }
  },

  methods: {
    async fetchConflicts() {
      const token = localStorage.getItem("token");

      try {
        const res = await fetch("/api/conflicts", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        const contentType = res.headers.get("content-type");
        if (!res.ok || !contentType?.includes("application/json")) {
          console.error("Ошибка получения конфликтов:", await res.text());
          return;
        }

        this.conflicts = await res.json();
      } catch (err) {
        console.error("Ошибка загрузки конфликтов:", err);
      }
    },

    async fetchEmployees() {
      const token = localStorage.getItem("token");

      try {
        const res = await fetch("/employees", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        const contentType = res.headers.get("content-type");
        if (!res.ok || !contentType?.includes("application/json")) {
          console.error("Ошибка при загрузке сотрудников:", await res.text());
          return;
        }

        this.employees = await res.json();
      } catch (err) {
        console.error("Ошибка загрузки сотрудников:", err);
      }
    },

    shortenAnalysis(html) {
      const stripped = html.replace(/<[^>]+>/g, '');
      return stripped.slice(0, 350) + "...";
    },

    getParticipantNames(ids) {
      try {
        const parsed = Array.isArray(ids) ? ids : JSON.parse(ids);
        return this.employees
          .filter(e => parsed.includes(e.id))
          .map(e => e.name)
          .join(", ");
      } catch (e) {
        return "—";
      }
    },

    openModal(conflict) {
      if (conflict) {
        this.form = { ...conflict };

        try {
          this.form.participants = JSON.parse(conflict.participants || "[]");
        } catch {
          this.form.participants = [];
        }

        this.form.ai_response = conflict.ai_analysis || "";
        this.form.actions_taken = conflict.attempts || "";
      } else {
        this.form = {
          id: null,
          context: "",
          participants: [],
          actions_taken: "",
          goal: "",
          status: "Активен",
          ai_response: ""
        };
      }

      this.showModal = true;
    },

    async deleteConflict(id) {
      const token = localStorage.getItem("token");

      try {
        await fetch(`/api/conflict/${id}`, {
          method: "DELETE",
          headers: {
            Authorization: `Bearer ${token}`
          }
        });

        await this.fetchConflicts();
      } catch (err) {
        alert("Ошибка удаления");
        console.error(err);
      }
    },

    async submitConflict() {
      this.loading = true;
      const token = localStorage.getItem("token");

      const payload = {
        ...this.form,
        participants: JSON.stringify(this.form.participants),
        attempts: this.form.actions_taken
      };

      delete payload.actions_taken;

      const isEditing = !!this.form.id;
      const url = isEditing
        ? `/api/conflict/${this.form.id}`
        : `/api/conflicts`;

      const method = isEditing ? "PUT" : "POST";

      try {
        const res = await fetch(url, {
          method,
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
          this.form.ai_response = data.analysis;
          await this.fetchConflicts();
        } else {
          alert(data.error || "Ошибка при сохранении конфликта");
        }
      } catch (err) {
        console.error(err);
        alert("Ошибка при подключении.");
      } finally {
        this.loading = false;
      }
    },

    async saveConflict() {
      this.saving = true;
      const token = localStorage.getItem("token");

      const payload = {
        ...this.form,
        participants: JSON.stringify(this.form.participants),
        attempts: this.form.actions_taken
      };

      delete payload.actions_taken;

      try {
        const res = await fetch("/api/conflicts/save", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(payload)
        });

        const data = await res.json();

        if (res.ok) {
          this.showModal = false;
          await this.fetchConflicts();
        } else {
          alert(data.error || "Ошибка при сохранении");
        }
      } catch (err) {
        alert("Ошибка соединения");
        console.error(err);
      } finally {
        this.saving = false;
      }
    },

    async waitForTokenAndInit() {
      let retries = 10;
      while (!localStorage.getItem("token") && retries > 0) {
        await new Promise(resolve => setTimeout(resolve, 300));
        retries--;
      }

      const token = localStorage.getItem("token");
      if (!token) {
        this.$router.push("/login");
        return;
      }

      await this.fetchConflicts();
      await this.fetchEmployees();
    }
  },

  mounted() {
    this.waitForTokenAndInit();
  }
};
</script>


<style scoped>
/* Контейнер всей страницы */
.conflict-container {
  max-width: 1280px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

/* Заголовок */
h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

/* Панель фильтров */
.filter-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 12px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.filter-bar button {
  background: #f3f4f6;
  border: none;
  padding: 10px 20px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  font-size: 14px;
  color: #4b5563;
  transition: all 0.2s ease;
  font-family: inherit;
}

.filter-bar button:hover {
  background: #e5e7eb;
  color: #1f2937;
}

.filter-bar button.active {
  background: #3b82f6;
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.add-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
  color: white !important;
  font-weight: 600 !important;
  padding: 12px 24px !important;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3) !important;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4) !important;
}

/* Карточки */
.conflict-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 24px;
}

.conflict-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
}

.conflict-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: #d1d5db;
}

.conflict-card h3 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
  line-height: 1.5;
}

.conflict-card p {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
  line-height: 1.6;
}

.conflict-card p strong {
  color: #374151;
  font-weight: 600;
}

/* Статус badge */
.conflict-card .status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Блок рекомендаций */
.summary-block {
  background: #f9fafb;
  border-left: 3px solid #3b82f6;
  padding: 16px;
  border-radius: 8px;
  margin-top: 8px;
}

.summary-block strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.summary-block p {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

/* Кнопки в карточке */
.conflict-card button {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  margin-top: 8px;
}

.conflict-card button:hover {
  background: #2563eb;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.conflict-card .delete-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #ef4444;
  padding: 8px 12px;
  margin: 0;
  font-size: 12px;
}

.conflict-card .delete-btn:hover {
  background: #dc2626;
}

/* Модальное окно */
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
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-content h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #111827;
  letter-spacing: -0.5px;
}

.modal-content label {
  display: block;
  margin-top: 24px;
  margin-bottom: 10px;
  font-weight: 600;
  color: #1f2937;
  font-size: 15px;
  letter-spacing: -0.2px;
}

.modal-content label:first-of-type {
  margin-top: 0;
}

.modal-content textarea,
.modal-content select {
  width: 100%;
  margin-top: 0;
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  resize: vertical;
  font-size: 15px;
  box-sizing: border-box;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  color: #111827;
  line-height: 1.5;
}

.modal-content textarea::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.modal-content textarea:hover,
.modal-content select:hover {
  border-color: #cbd5e1;
}

.modal-content textarea:focus,
.modal-content select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12), 0 2px 8px rgba(59, 130, 246, 0.08);
  background: #fafbff;
}

.modal-content select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  padding-right: 44px;
}

.modal-content textarea {
  min-height: 100px;
  line-height: 1.6;
}

.modal-content select[multiple] {
  background-image: none;
  padding-right: 18px;
  min-height: 120px;
}

/* Кнопки в модальном окне */
.modal-actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
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
  font-family: inherit;
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

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.modal-actions .modal-close {
  background: #f3f4f6;
  color: #374151;
  font-size: 20px;
  padding: 10px 16px;
  min-width: 44px;
}

.modal-actions .modal-close:hover {
  background: #e5e7eb;
  color: #111827;
}

/* AI Анализ */
.ai-analysis {
  margin-top: 24px;
  margin-bottom: 32px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  padding: 20px;
  border-radius: 12px;
  font-size: 14px;
  color: #1e40af;
  border: 1px solid #bae6fd;
  line-height: 1.7;
}

.ai-analysis ul {
  list-style: disc;
  padding-left: 24px;
  margin-top: 12px;
}

.ai-analysis li {
  margin-bottom: 8px;
}

@media (max-width: 768px) {
  .conflict-container {
    margin: 20px 10px !important;
    padding: 20px !important;
  }
  
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
  }
  
  .filter-bar {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .filter-bar button {
    width: 100%;
    text-align: center;
  }
  
  .conflict-list {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .conflict-card {
    padding: 20px;
  }
  
  .modal-content {
    width: 100% !important;
    max-width: 100% !important;
    padding: 24px 20px !important;
    margin: 0 !important;
    border-radius: 16px 16px 0 0;
  }
  
  .modal-content h2 {
    font-size: 22px;
    margin-bottom: 24px;
  }
  
  .modal-content textarea,
  .modal-content select {
    width: 100% !important;
    font-size: 16px !important;
  }
  
  .modal-actions {
    flex-direction: column !important;
    gap: 10px !important;
  }
  
  .modal-actions button {
    width: 100% !important;
  }
}
</style>
