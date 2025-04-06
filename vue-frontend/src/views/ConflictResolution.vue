<template>
  <div class="conflict-container">
    <h1>🔥 Конфликты в командах</h1>

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
        <button @click="openModal(conflict)">✏️ Редактировать</button>
        <button class="delete-btn" @click="deleteConflict(conflict.id)">🗑</button>
      </div>
    </div>

    <!-- 🔹 Модальное окно -->
    <div class="modal-overlay" v-if="showModal">
      <div class="modal-content">
        <h2>{{ form.id ? 'Редактировать' : 'Новый конфликт' }}</h2>
        <label>Контекст конфликта</label>
        <textarea v-model="form.context" rows="3" />

        <label>Участники</label>
        <select v-model="form.participants" multiple>
          <option v-for="e in employees" :value="e.id" :key="e.id">{{ e.name }}</option>
        </select>

        <label>Что предпринималось?</label>
        <textarea v-model="form.actions_taken" rows="2" />

        <label>Цель разрешения</label>
        <textarea v-model="form.goal" rows="2" />

        <label>Статус</label>
        <select v-model="form.status">
          <option value="Активен">Активен</option>
          <option value="Закрыт">Закрыт</option>
          <option value="Обострение">Обострение</option>
        </select>

        <div class="modal-actions">
          <button @click="submitConflict">💬 Получить рекомендации</button>
          <button class="modal-close" @click="showModal = false">✖</button>
        </div>

        <div v-if="form.ai_response" class="ai-analysis" v-html="form.ai_response"></div>
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
  const token = localStorage.getItem("token"); // 👈 добавлено
  const res = await fetch("/conflicts", {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  this.conflicts = await res.json();
},

async fetchEmployees() {
  const token = localStorage.getItem("token"); // 👈 добавлено
  const res = await fetch("/employees", {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
  this.employees = await res.json();
},
    getParticipantNames(ids) {
      if (!ids) return "—";
      const parsed = Array.isArray(ids) ? ids : JSON.parse(ids);
      return this.employees
        .filter(e => parsed.includes(e.id))
        .map(e => e.name)
        .join(", ");
    },
    openModal(conflict) {
      if (conflict) {
        this.form = { ...conflict };
        this.form.participants = JSON.parse(conflict.participants || "[]");
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
  await fetch(`/conflict/${id}`, {
    method: "DELETE",
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });
await this.fetchConflicts();
},
    async submitConflict() {
  const token = localStorage.getItem("token");
  const payload = { ...this.form };

  payload.participants = JSON.stringify(payload.participants);
  payload.attempts = payload.actions_taken;
  delete payload.actions_taken;

  const res = await fetch("/conflicts", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
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
}
},

  mounted() {
    this.fetchConflicts();
    this.fetchEmployees();
  }
};
</script>
<style scoped>
.conflict-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 20px;
  background: #fff;
  border-radius: 14px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  font-family: "Segoe UI", sans-serif;
}

h1 {
  font-size: 26px;
  margin-bottom: 20px;
  color: #2c3e50;
}

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
  position: relative;
}

.conflict-card h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.conflict-card p {
  font-size: 14px;
  color: #555;
  margin: 0;
}

.conflict-card button {
  align-self: flex-start;
  background: #3498db;
  color: white;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.conflict-card .delete-btn {
  background: #e74c3c;
  margin-top: 6px;
}

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
  border-radius: 14px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

.modal-content h2 {
  font-size: 20px;
  margin-bottom: 20px;
}

.modal-content label {
  display: block;
  margin-top: 14px;
  font-weight: bold;
  color: #2c3e50;
}

.modal-content textarea,
.modal-content select {
  width: 100%;
  margin-top: 6px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  resize: vertical;
  font-size: 14px;
}

.modal-actions {
  margin-top: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-actions button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: bold;
  cursor: pointer;
}

.modal-actions .modal-close {
  background: transparent;
  color: #888;
  font-size: 20px;
}

.modal-actions .modal-close:hover {
  color: #000;
}

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
</style>
