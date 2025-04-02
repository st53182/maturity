<template>
  <div class="motivation-container">
    <h1>🎯 Мотивация сотрудника</h1>

    <!-- 🔹 Список сотрудников -->
    <div class="employee-list">
      <div
        v-for="employee in employees"
        :key="employee.id"
        class="employee-card"
        @click="selectEmployee(employee)"
      >
        <img
          class="avatar"
          :src="getAvatarUrl(employee.ai_analysis)"
          alt="avatar"
        />
        <h4>{{ employee.name }}</h4>
        <p class="team-name">{{ getTeamName(employee.team_id) }}</p>
        <span class="disc-type">{{ extractDISCType(employee.ai_analysis) }}</span>
        <button @click.stop="deleteEmployee(employee.id)">🗑</button>
      </div>
    </div>

    <!-- 🔹 Форма -->
    <form @submit.prevent="submitMotivation">
      <div class="form-group">
        <label>Имя сотрудника:</label>
        <input v-model="form.name" placeholder="Например: Иван Иванов" required />

        <label>Должность:</label>
        <input v-model="form.role" placeholder="Например: Аналитик, Разработчик..." required />

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
        <textarea
          v-model="form.stress"
          placeholder="Как он реагирует на давление, конфликты..."
          required
        ></textarea>

        <label>2. Взаимодействие с другими</label>
        <textarea
          v-model="form.communication"
          placeholder="Открытый, сдержанный, любит работать в команде или один..."
          required
        ></textarea>

        <label>3. Особенности в работе</label>
        <textarea
          v-model="form.behavior"
          placeholder="Привычки, подход, структура, планирование..."
          required
        ></textarea>

        <label>4. Реакции на критику и изменения</label>
        <textarea
          v-model="form.feedback"
          placeholder="Как принимает фидбек, открыт к переменам..."
          required
        ></textarea>
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? "Сохраняем и анализируем..." : "Сохранить и получить рекомендации" }}
      </button>
    </form>

    <!-- 🔹 Результат -->
    <div v-if="result" class="result-block">
      <h2>📋 Рекомендации</h2>
      <div v-html="result"></div>
      <button @click="resetForm">Новый сотрудник</button>
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
      teams: [],
      employees: [],
      discProfiles: [],
      result: "",
      loading: false
    };
  },
  async mounted() {
    const token = localStorage.getItem("token");

    const teamRes = await fetch("/user_teams", {
      headers: { Authorization: `Bearer ${token}` }
    });
    this.teams = await teamRes.json();

    const empRes = await fetch("/employees");
    this.employees = await empRes.json();

    const discRes = await fetch("/static/disc_profiles_for_frontend.json");
    this.discProfiles = await discRes.json();
  },
  methods: {
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
          this.employees.push({ ...this.form, ai_analysis: data.analysis });
        } else {
          alert(data.error || "Ошибка");
        }
      } catch (err) {
        alert("Ошибка при сохранении");
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.form = {
        name: "",
        role: "",
        team_id: "",
        stress: "",
        communication: "",
        behavior: "",
        feedback: ""
      };
      this.result = "";
    },
    async deleteEmployee(id) {
      if (!confirm("Удалить сотрудника?")) return;
      await fetch(`/employee/${id}`, { method: "DELETE" });
      this.employees = this.employees.filter(e => e.id !== id);
    },
    selectEmployee(emp) {
      this.form = {
        name: emp.name,
        role: emp.role,
        team_id: emp.team_id,
        stress: emp.stress,
        communication: emp.communication,
        behavior: emp.behavior,
        feedback: emp.feedback
      };
      this.result = emp.ai_analysis;
    },
    extractDISCType(text) {
      const match = text?.match(/\*\*Тип DISC:\*\*\s*(.+)/i);
      return match ? match[1].split("\n")[0].trim() : "Неизвестно";
    },
    getTeamName(teamId) {
      const team = this.teams.find(t => t.id === teamId);
      return team ? team.name : "—";
    },
    getAvatarUrl(aiText) {
      const type = this.extractDISCType(aiText);
      const key = type?.toLowerCase().split(" ")[0].replace(/[^\w]/g, "");
      return `/avatars/${key || "default"}.png`;
    }
  }
};
</script>

<style scoped>
.motivation-container {
  max-width: 900px;
  margin: auto;
  background: #fff;
  padding: 25px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  font-family: "Arial", sans-serif;
}
form {
  margin-top: 20px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
input,
textarea,
select {
  padding: 10px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid #ccc;
}
button {
  background: #3498db;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin-top: 15px;
  font-weight: bold;
}
.result-block {
  background: #f4f9ff;
  margin-top: 30px;
  padding: 20px;
  border-radius: 10px;
}

.employee-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 30px;
}

.employee-card {
  background: #fefefe;
  border-radius: 12px;
  padding: 12px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  width: 200px;
  cursor: pointer;
  position: relative;
  text-align: center;
}
.employee-card:hover {
  transform: translateY(-2px);
}
.employee-card .avatar {
  width: 60px;
  height: 60px;
  object-fit: contain;
}
.employee-card .disc-type {
  font-size: 14px;
  font-weight: bold;
  color: #555;
}
.employee-card button {
  position: absolute;
  top: 6px;
  right: 8px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #e74c3c;
}
.team-name {
  font-size: 13px;
  color: #888;
}
</style>


