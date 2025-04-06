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
        <div v-if="conflict.ai_analysis" class="summary-block">
    <strong>📝 Рекомендации:</strong>
    <p v-html="shortenAnalysis(conflict.ai_analysis)"></p>
  </div>
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
  <button @click="submitConflict" :disabled="loading">
    💬 {{ loading ? "Генерация..." : "Получить рекомендации" }}
  </button>
  <button @click="saveConflict" :disabled="saving">
    💾 {{ saving ? "Сохранение..." : "Сохранить и закрыть" }}
  </button>
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
        ai_response: "",
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
      const res = await fetch("/api/conflicts", {
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      this.conflicts = await res.json();
    },

    async fetchEmployees() {
  const token = localStorage.getItem("token");
  const res = await fetch("/employees", {
    headers: {
      "Authorization": `Bearer ${token}`
    }
  });

  // 🧠 Проверим, что это точно JSON
  const contentType = res.headers.get("content-type");
  if (!res.ok || !contentType || !contentType.includes("application/json")) {
    const text = await res.text(); // получим содержимое
    console.error("Ошибка при загрузке сотрудников:", text);
    return;
  }

  this.employees = await res.json();
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
    } catch (e) {
      this.form.participants = [];
    }

    this.form.ai_response = conflict.ai_analysis || "";

    // ✅ вот это добавь
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
      await fetch(`/api/conflict/${id}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${token}`
        }
      });
      await this.fetchConflicts();
    },

    async submitConflict() {
  this.loading = true;
  const token = localStorage.getItem("token");
  const payload = { ...this.form };

  payload.participants = JSON.stringify(payload.participants);
  payload.attempts = this.form.actions_taken;
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
  } catch (err) {
    alert("Ошибка при подключении.");
    console.error(err);
  } finally {
    this.loading = false;
  }
},

async saveConflict() {
  this.saving = true;
  const token = localStorage.getItem("token");
  const payload = { ...this.form };

  payload.participants = JSON.stringify(payload.participants);
  payload.attempts = payload.actions_taken;
  delete payload.actions_taken;

  const res = await fetch("/api/conflicts/save", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Authorization": `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });

  const data = await res.json();

  this.saving = false;
  if (res.ok) {
    this.showModal = false;
    await this.fetchConflicts();
  } else {
    alert(data.error || "Ошибка при сохранении");
  }
}
,
    async waitForTokenAndInit() {
  let retries = 10;
  while (!localStorage.getItem("token") && retries > 0) {
    await new Promise(resolve => setTimeout(resolve, 300)); // ждём 300мс
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
/* ✅ Контейнер */
.conflict-container {
  max-width: 1200px;
  margin: 40px auto;
  padding: 24px;
  background: #fff;
  border-radius: 16px;
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.05);
  font-family: "Segoe UI", sans-serif;
}

/* ✅ Заголовок */
h1 {
  font-size: 28px;
  margin-bottom: 24px;
  font-weight: 700;
  color: #2c3e50;
}

/* ✅ Кнопки фильтра */
.filter-bar {
  display: flex;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.filter-bar button {
  background: #f0f4f8;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 500;
  color: #34495e;
  transition: 0.3s ease;
}

.filter-bar button.active,
.filter-bar button:hover {
  background: #3498db;
  color: #fff;
}

.add-btn {
  background-color: #27ae60 !important;
  color: white !important;
}

/* ✅ Сетка карточек */
.conflict-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}

/* ✅ Карточка конфликта */
.conflict-card {
  background: #fafafa;
  padding: 18px;
  border-radius: 14px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.06);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  cursor: pointer;
}

.conflict-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 18px rgba(0, 0, 0, 0.08);
}

.conflict-card h3 {
  font-size: 17px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.conflict-card p {
  font-size: 14px;
  color: #555;
  margin: 2px 0;
}

.conflict-card button {
  background: #3498db;
  color: #fff;
  border: none;
  padding: 8px 14px;
  border-radius: 8px;
  margin-top: 8px;
  font-size: 13px;
  transition: 0.3s ease;
}

.conflict-card .delete-btn {
  background: #e74c3c;
  margin-left: 8px;
}

/* ✅ Модалка */
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
  z-index: 100;
}

.modal-content {
  background: #fff;
  padding: 30px;
  border-radius: 16px;
  width: 95%;
  max-width: 750px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
}

.modal-content h2 {
  font-size: 22px;
  margin-bottom: 24px;
  color: #2c3e50;
  font-weight: bold;
}

.modal-content label {
  display: block;
  margin-top: 18px;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.modal-content textarea,
.modal-content select {
  width: 100%;
  margin-top: 6px;
  padding: 12px 14px;
  border: 1px solid #dcdfe6;
  border-radius: 10px;
  font-size: 14px;
  background: #fff;
  transition: border 0.2s;
}

.modal-content textarea:focus,
.modal-content select:focus {
  outline: none;
  border-color: #3498db;
}

/* ✅ Кнопки в модалке */
.modal-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 30px;
  gap: 12px;
  flex-wrap: wrap;
}

.modal-actions button {
  flex: 1;
  padding: 12px 20px;
  font-weight: bold;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.modal-actions button:disabled {
  background-color: #ccc !important;
  cursor: not-allowed;
}

.modal-actions .modal-close {
  background: transparent;
  color: #aaa;
  font-size: 22px;
}

.modal-actions .modal-close:hover {
  color: #333;
}

.modal-actions .save-btn {
  background-color: #8e44ad;
  color: #fff;
}

.modal-actions .generate-btn {
  background-color: #3498db;
  color: #fff;
}

/* ✅ AI блок */
.ai-analysis {
  margin-top: 28px;
  background: #f3f6f9;
  padding: 18px;
  border-radius: 12px;
  font-size: 14px;
  line-height: 1.6;
  color: #2c3e50;
  border-left: 4px solid #3498db;
}

.ai-analysis ul {
  padding-left: 20px;
  list-style: disc;
}
</style>
