<template>
  <div class="conflict-container">
    <h1>🔥 Конфликты и Проблемы</h1>

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
      <button @click="openModal(null)" class="add-btn">➕ Новый конфликт</button>
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
        <h2>{{ form.id ? 'Редактировать' : 'Новый конфликт' }}</h2>
        <label>Контекст</label>
        <textarea v-model="form.context" rows="3" placeholder="Опишите суть ситуации, как она возникла, чем детальнее тем лучше..."></textarea>

        <label>Участники (для выбора нескольких используйте ctrl) / Опционально </label>
        <select v-model="form.participants" multiple>
          <option v-for="e in employees" :value="e.id" :key="e.id">{{ e.name }}</option>
        </select>

        <label>Что предпринималось?</label>
        <textarea v-model="form.actions_taken" rows="3" placeholder="Какие шаги уже были предприняты для разрешения?"></textarea>

        <label>Цель разрешения</label>
        <textarea v-model="form.goal" rows="3" placeholder="Какого результата вы хотите достичь?"></textarea>

        <label>Статус</label>
        <select v-model="form.status">
          <option value="Активен">Активен</option>
          <option value="Закрыт">Закрыт</option>
          <option value="Обострение">Обострение</option>
        </select>

        <div class="modal-actions">
  <button class="generate-btn" @click="submitConflict" :disabled="loading">
    💬 {{ loading ? "Генерация..." : "Получить рекомендации" }}
  </button>
  <button
  v-if="form.id"
  class="save-btn"
  @click="saveConflict"
  :disabled="saving"
>
  💾 {{ saving ? "Сохранение..." : "Сохранить и закрыть" }}
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
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
  background: #f2f4f7;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  font-family: "Segoe UI", sans-serif;
}

/* Заголовок */
h1 {
  font-size: 26px;
  margin-bottom: 20px;
  color: #2c3e50;
}

/* Панель фильтров */
.filter-bar {
  display: flex;
  justify-content: space-between;
  margin-bottom: 20px;
  flex-wrap: wrap;
  gap: 10px;
}

.filter-bar button {
  background: #ecf0f1;
  border: none;
  padding: 10px 18px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: 500;
  color: #34495e;
  transition: 0.3s;
}

.filter-bar button.active,
.filter-bar button:hover {
  background: #3498db;
  color: white;
}

.add-btn {
  background-color: #2ecc71 !important;
  color: white !important;
  font-weight: bold;
}

/* Карточки */
.conflict-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

.conflict-card {
  background: #fdfdfd;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
  gap: 10px;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
}

.conflict-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.conflict-card h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.conflict-card p {
  font-size: 14px;
  color: #444;
  margin: 6px 0 10px;
  line-height: 1.6;
}

.conflict-card p + p {
  margin-top: 12px;
}

.conflict-card p strong {
  display: inline-block;
  margin-top: 4px;
}

/* Блок рекомендаций */
.recommendation-title {
  font-weight: bold;
  margin-top: 14px;
  color: #e74c3c;
  display: flex;
  align-items: center;
  gap: 6px;
}

.recommendation-text {
  background: #fcfcfc;
  border-left: 3px solid #e67e22;
  padding: 10px 12px;
  border-radius: 8px;
  margin-top: 8px;
  font-size: 14px;
  line-height: 1.5;
  color: #333;
}

/* Кнопки */
.conflict-card button {
  background: #3498db;
  color: white;
  border: none;
  padding: 9px 16px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: 0.3s;
}

.conflict-card button:hover {
  background: #2b7bbd;
}

.conflict-card .delete-btn {
  background: #e74c3c;
}

.conflict-card .delete-btn:hover {
  background: #c0392b;
}

/* Модальное окно */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 99;
}

.modal-content {
  background: #fff;
  padding: 30px;
  border-radius: 16px;
  width: 97%;
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
}

.modal-content h2 {
  font-size: 22px;
  margin-bottom: 20px;
  color: #2c3e50;
}

.modal-content label {
  display: block;
  margin-top: 16px;
  font-weight: bold;
  color: #34495e;
  font-size: 14px;
}

.modal-content textarea,
.modal-content select {
  width: 97%;
  margin-top: 6px;
  padding: 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  resize: vertical;
  font-size: 14px;
  box-sizing: border-box;

}

/* Кнопки в модальном окне */
.modal-actions {
  margin-top: 24px;
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.modal-actions button {
  flex: 1 1 auto;
  padding: 10px 18px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: 0.25s ease-in-out;
}

.modal-actions button:first-child {
  background: #2980b9;
  color: white;
}

.modal-actions button:first-child:hover {
  background: #2471a3;
}

.modal-actions button:nth-child(2) {
  background: #8e44ad;
  color: white;
}

.modal-actions button:nth-child(2):hover {
  background: #732d91;
}

.modal-actions .modal-close {
  background: #eee;
  color: #333;
  font-size: 18px;
  padding: 8px 14px;
}

.modal-actions .modal-close:hover {
  background: #ddd;
  color: #000;
}

/* AI Анализ */
.ai-analysis {
  margin-top: 20px;
  background: #f9f9f9;
  padding: 16px;
  border-radius: 10px;
  font-size: 14px;
  color: #333;
}

.ai-analysis ul {
  list-style: disc;
  padding-left: 20px;
}

@media (max-width: 768px) {
  .conflict-container {
    margin: 20px 10px;
    padding: 15px;
  }
  
  .filter-bar {
    flex-direction: column;
    gap: 10px;
  }
  
  .filter-bar button {
    width: 100%;
    text-align: center;
  }
  
  .conflict-list {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .conflict-card {
    padding: 15px;
  }
  
  .modal-content {
    width: 95%;
    max-width: 95%;
    padding: 20px 15px;
    margin: 10px;
  }
  
  .modal-content textarea,
  .modal-content select {
    width: 100%;
    font-size: 16px;
    box-sizing: border-box;
  }
  
  .modal-actions {
    flex-direction: column;
    gap: 10px;
  }
  
  .modal-actions button {
    width: 100%;
  }
}
</style>
