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
          @error="setDefaultAvatar"
        />
        <div class="card-header">
          <h4>{{ employee.name }}</h4>
          <button @click.stop="deleteEmployee(employee.id)">🗑</button>
        </div>
        <p class="team-name">Команда: {{ getTeamName(employee.team_id) || '—' }}</p>
        <span class="disc-type">{{ extractDISCType(employee.ai_analysis) }}</span>

        <div v-if="employee.ai_analysis" class="factors">
          <div class="column">
            <h5>⬆️ Мотивирующие</h5>
            <ul>
              <li v-for="item in employee.motivators" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div class="column">
            <h5>⬇️ Демотиваторы</h5>
            <ul>
              <li v-for="item in employee.demotivators" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
      </div>

      <div class="employee-card add-card" @click="resetForm">
        <span>➕</span>
        <p>Создать</p>
      </div>
    </div>

    <!-- 🔹 Форма -->
    <form @submit.prevent="submitMotivation">
      <div class="form-group">
        <label>Имя сотрудника:</label>
        <input v-model="form.name" placeholder="Например: Иван Иванов" required />

        <label>Должность:</label>
        <input v-model="form.role" placeholder="Аналитик, Разработчик..." required />

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
        <textarea v-model="form.stress" placeholder="Как он реагирует на давление, конфликты..." required></textarea>

        <label>2. Взаимодействие с другими</label>
        <textarea v-model="form.communication" placeholder="Открытый, сдержанный, командный игрок?" required></textarea>

        <label>3. Особенности в работе</label>
        <textarea v-model="form.behavior" placeholder="Подход к задачам, ответственность..." required></textarea>

        <label>4. Реакции на критику и изменения</label>
        <textarea v-model="form.feedback" placeholder="Как принимает обратную связь..." required></textarea>
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? "Анализируем..." : "Сохранить и получить рекомендации" }}
      </button>
    </form>

    <!-- 🔹 Результат -->
    <div v-if="result" class="result-block">
      <h2>📋 Рекомендации</h2>
      <div class="ai-analysis" v-html="result"></div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        id: null,
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
    const rawEmployees = await empRes.json();

    this.employees = rawEmployees.map(e => ({
      ...e,
      motivators: this.extractFactors(e.ai_analysis, "Мотивирующие"),
      demotivators: this.extractFactors(e.ai_analysis, "Демотиваторы")
    }));
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
          this.form.id = data.employee_id;

          const updated = {
            ...this.form,
            id: data.employee_id,
            ai_analysis: data.analysis,
            motivators: this.extractFactors(data.analysis, "Мотивирующие"),
            demotivators: this.extractFactors(data.analysis, "Демотиваторы")
          };

          const index = this.employees.findIndex(e => e.id === data.employee_id);
          if (index !== -1) {
            this.employees.splice(index, 1, updated);
          } else {
            this.employees.push(updated);
          }
        } else {
          alert(data.error);
        }
      } catch (err) {
        alert("Ошибка подключения");
      } finally {
        this.loading = false;
      }
    },

    resetForm() {
      this.form = {
        id: null,
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

    selectEmployee(employee) {
      this.form = { ...employee };
      this.result = employee.ai_analysis;
    },

    extractFactors(text, sectionTitle) {
      if (!text) return [];
      const match = text.match(new RegExp(`${sectionTitle}.*?:`, 'i'));
      if (!match) return [];

      const start = text.indexOf(match[0]);
      const rest = text.slice(start);

      const stopRegex = /^(Мотивирующие|Демотиваторы|Рекомендации)/gmi;
      const stopMatch = [...rest.matchAll(stopRegex)];

      let end = rest.length;
      if (stopMatch.length > 1) end = stopMatch[1].index;

      const section = rest.slice(0, end);
      return section
        .split(/[-–•●]/)
        .map(s => s.trim())
        .filter(s => s.length > 5 && !s.startsWith(sectionTitle));
    },

    extractDISCType(text) {
      const match = text?.match(/\*\*Тип DISC:\*\*\s*(.*?)(\*\*|$)/);
      return match ? match[1].trim() : "Неизвестно";
    },

    getTeamName(teamId) {
      const team = this.teams.find(t => t.id === teamId);
      return team ? team.name : "—";
    },

    getAvatarUrl(aiText) {
      const type = this.extractDISCType(aiText);
      const key = type?.toLowerCase().split(" ")[0].replace(/[^\w]/g, "");
      return `/avatars/${key || "default"}.png`;
    },

    setDefaultAvatar(event) {
      event.target.src = "/avatars/default.png";
    }
  }
};
</script>




<style>
.motivation-container {
  max-width: 1000px;
  margin: 40px auto;
  background: #fff;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.07);
  font-family: "Segoe UI", sans-serif;
}

h1 {
  font-size: 28px;
  margin-bottom: 25px;
}

form {
  margin-top: 30px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
  margin-bottom: 20px;
}

input,
textarea,
select {
  padding: 10px 14px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid #ccc;
}

button {
  background: #2d8cff;
  color: white;
  padding: 12px 22px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin-top: 10px;
  font-weight: bold;
  transition: background 0.2s ease;
}
button:hover {
  background: #1c6edb;
}

.result-block {
  background: #f4f9ff;
  margin-top: 40px;
  padding: 25px;
  border-radius: 12px;
  border: 1px solid #e0eaff;
}

.employee-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 30px;
}

.employee-card {
  width: 340px;
  min-height: 100px;
  padding: 1rem;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 0 10px rgba(0,0,0,0.04);
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: relative;
}
.employee-card:hover {
  transform: translateY(-2px);
  transition: 0.2s ease;
}

.employee-card .avatar {
  width: 70px;
  height: 70px;
  object-fit: cover;
  border-radius: 50%;
  margin: 0 auto;
}

.employee-card .disc-type {
  font-size: 14px;
  font-weight: bold;
  color: #444;
  text-align: center;
}

.employee-card .team-name {
  font-size: 13px;
  color: #777;
  text-align: center;
}

.employee-card button {
  position: absolute;
  top: 6px;
  right: 10px;
  background: none;
  border: none;
  cursor: pointer;
  font-size: 16px;
  color: #e74c3c;
}

.employee-card.add-card {
  width: 160px;
  height: 160px;
  background: #f3f3f3;
  justify-content: center;
  align-items: center;
  text-align: center;
  font-size: 18px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
}

.factors {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

.factors .column {
  flex: 1;
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  max-height: 180px;
  overflow-y: auto;
}

.factors h5 {
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #ddd;
  padding-bottom: 4px;
}

.factors ul {
  padding-left: 1rem;
  margin: 0;
  font-size: 13px;
  color: #444;
  list-style: disc;
}

.factors li {
  margin-bottom: 6px;
}

.ai-analysis {
  padding: 1rem;
  border-radius: 12px;
  background: #fdfdfd;
  border: 1px solid #ddd;
  margin-top: 20px;
}

.ai-analysis h3,
.ai-analysis h4 {
  margin-top: 1rem;
  color: #2c3e50;
}

.ai-analysis ul {
  padding-left: 1.2rem;
  margin-bottom: 10px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
