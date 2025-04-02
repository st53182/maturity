<template>
  <div class="motivation-container">
    <h1>🎯 Мотивация сотрудника</h1>

    <!-- 🔹 Карточки сотрудников -->
    <div class="employee-cards">
      <div
        v-for="emp in employees"
        :key="emp.id"
        class="employee-card"
        @click="selectEmployee(emp)"
      >
        <img :src="getAvatar(emp.id)" class="avatar" />
        <div class="name">{{ emp.name }}</div>
        <div class="disc">{{ parseDisc(emp.ai_analysis) }}</div>
      </div>

      <div class="employee-card add-card" @click="resetForm">
        ➕
        <div style="font-size: 14px; margin-top: 5px;">Добавить</div>
      </div>
    </div>

    <!-- 🔹 Форма -->
    <form @submit.prevent="submitMotivation" v-if="!selectedEmployee || result === ''">
      <div class="form-group">
        <label>Имя сотрудника:</label>
        <input v-model="form.name" placeholder="Например: Иван Иванов" required />

        <label>Должность:</label>
        <input v-model="form.role" placeholder="Например: Аналитик..." required />

        <label>Команда:</label>
        <select v-model="form.team_id" required>
          <option disabled value="">Выберите команду</option>
          <option v-for="team in teams" :key="team.id" :value="team.id">
            {{ team.name }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>1. Поведение в стрессовой ситуации</label>
        <textarea v-model="form.stress" required placeholder="Как он реагирует на давление, конфликты..."></textarea>

        <label>2. Взаимодействие с другими</label>
        <textarea v-model="form.communication" required placeholder="Открытый, сдержанный, любит работать в команде или один..."></textarea>

        <label>3. Особенности в работе</label>
        <textarea v-model="form.behavior" required placeholder="Привычки, подход, структура, планирование..."></textarea>

        <label>4. Реакции на критику и изменения</label>
        <textarea v-model="form.feedback" required placeholder="Как принимает фидбек, открыт к переменам..."></textarea>
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? "Сохраняем и анализируем..." : "Сохранить и получить рекомендации" }}
      </button>
    </form>

    <!-- 🔹 Результаты -->
    <div v-if="result" class="result-block">
      <h2>📋 Рекомендации</h2>
      <div v-html="formatAnalysis(result)"></div>
      <button @click="resetForm">🔁 Новый сотрудник</button>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        name: "",
        role: "",
        team_id: "",
        stress: "",
        communication: "",
        behavior: "",
        feedback: ""
      },
      employees: [],
      selectedEmployee: null,
      teams: [],
      result: "",
      loading: false
    };
  },
  async mounted() {
    await this.fetchTeams();
    await this.fetchEmployees();
  },
  methods: {
    async fetchTeams() {
      try {
        const token = localStorage.getItem("token");
        const res = await fetch("/user_teams", {
          headers: {
            Authorization: `Bearer ${token}`
          }
        });
        const data = await res.json();
        this.teams = data;
      } catch (err) {
        alert("Ошибка загрузки команд");
      }
    },
    async fetchEmployees() {
      const res = await fetch("/employees");
      const data = await res.json();
      this.employees = data;
    },
    async submitMotivation() {
      this.loading = true;
      try {
        const res = await fetch("/motivation", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(this.form)
        });
        const data = await res.json();
        if (res.ok) {
          this.result = data.analysis;
          await this.fetchEmployees(); // обновляем список
        } else {
          alert(data.error);
        }
      } catch (err) {
        alert("Ошибка соединения");
      } finally {
        this.loading = false;
      }
    },
    selectEmployee(emp) {
      this.selectedEmployee = emp;
      this.result = emp.ai_analysis || "";
      this.form = {
        name: emp.name,
        role: emp.role,
        team_id: emp.team_id,
        stress: emp.stress,
        communication: emp.communication,
        behavior: emp.behavior,
        feedback: emp.feedback
      };
    },
    resetForm() {
      this.selectedEmployee = null;
      this.result = "";
      this.form = {
        name: "",
        role: "",
        team_id: "",
        stress: "",
        communication: "",
        behavior: "",
        feedback: ""
      };
    },
    getAvatar(id) {
      const index = (id % 12) + 1;
      return `/avatars/avatar${index}.png`; // Убедись, что картинки загружены в public/avatars
    },
    parseDisc(text) {
      const match = text?.match(/\*\*Тип DISC:\*\*\s*(.+)/);
      return match ? match[1].split("\n")[0].trim() : "–";
    },
    formatAnalysis(text) {
      return text
        .replace(/\*\*Тип DISC:\*\*/g, "<h3>Тип DISC</h3>")
        .replace(/\*\*Мотивирующие факторы:\*\*/g, "<h3>✅ Мотиваторы</h3>")
        .replace(/\*\*Демотиваторы:\*\*/g, "<h3>⚠️ Демотиваторы</h3>")
        .replace(/\*\*Рекомендации для руководителя:\*\*/g, "<h3>📋 Рекомендации</h3>")
        .replace(/\n/g, "<br>");
    }
  }
};
</script>

<style scoped>
.motivation-container {
  max-width: 1100px;
  margin: auto;
  padding: 30px;
  background: #fff;
  border-radius: 12px;
}

.employee-cards {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 30px;
}

.employee-card {
  width: 160px;
  background: #f1f1f1;
  padding: 10px;
  border-radius: 10px;
  text-align: center;
  cursor: pointer;
  transition: transform 0.2s;
}

.employee-card:hover {
  transform: scale(1.05);
}

.employee-card .avatar {
  width: 60px;
  height: 60px;
  border-radius: 50%;
}

.employee-card .name {
  font-weight: bold;
  margin-top: 8px;
}

.employee-card .disc {
  font-size: 13px;
  color: #555;
}

.add-card {
  background: #dfe6e9;
  display: flex;
  flex-direction: column;
  justify-content: center;
  font-size: 30px;
  color: #444;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

textarea,
input,
select {
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ccc;
  width: 100%;
  font-size: 15px;
}

button {
  padding: 12px 20px;
  font-size: 16px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin-top: 20px;
  transition: 0.3s;
}

button:hover {
  background: linear-gradient(135deg, #5865c1, #6e4ca6);
}

.result-block {
  margin-top: 30px;
  background: #f4f6fa;
  padding: 20px;
  border-radius: 12px;
}
</style>

