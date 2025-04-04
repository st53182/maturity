<template>
  <div class="motivation-container">
    <h1>🎯 Мотивация сотрудника</h1>

    <!-- 🔹 Список сотрудников -->
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
        <li v-for="item in extractFactors(employee.ai_analysis, 'Мотивирующие')" :key="item">{{ item }}</li>
      </ul>
    </div>
    <div class="column">
      <h5>⬇️ Демотиваторы</h5>
      <ul>
        <li v-for="item in extractFactors(employee.ai_analysis, 'Демотиваторы')" :key="item">{{ item }}</li>
      </ul>
    </div>
  </div>
</div>
    </div>
 <div class="employee-card add-card" @click="resetForm">
        <span>➕</span>
        <p>Создать</p>
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
  <div class="ai-analysis" v-html="result"></div>
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
    const rawEmployees = await empRes.json();

    const discRes = await fetch("/static/disc_profiles_for_frontend.json");
    this.discProfiles = await discRes.json();

    // 💡 добавляем motivators и demotivators
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

          // 🔁 Обновление или добавление сотрудника
          const index = this.employees.findIndex(e => e.id === data.employee_id);
          const updated = {
            ...this.form,
            id: data.employee_id,
            ai_analysis: data.analysis,
            motivators: this.extractFactors(data.analysis, "Мотивирующие"),
            demotivators: this.extractFactors(data.analysis, "Демотиваторы")
          };

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
      this.form = {
        id: employee.id,
        name: employee.name,
        role: employee.role,
        team_id: employee.team_id,
        stress: employee.stress,
        communication: employee.communication,
        behavior: employee.behavior,
        feedback: employee.feedback
      };
      this.result = employee.ai_analysis;
    },

   extractFactors(text, sectionTitle) {
  if (!text) return [];

  const sectionRegex = new RegExp(`\\*\\*${sectionTitle} факторы:\\*\\*(.*?)(\\*\\*|\\n\\n|$)`, "s");
  const match = text.match(sectionRegex);
  if (!match) return [];

  return match[1]
    .split(/[-–•]/)
    .map(line => line.trim())
    .filter(line => line.length > 3);
},

    extractDISCType(aiText) {
      const match = aiText?.match(/\*\*Тип DISC:\*\*\s*(.*?)(\*\*|$)/);
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
    }
  }
};
</script>


<style>
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
  position: relative; /* ✅ добавили */
  width: 320px;
  padding: 1rem;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 0 6px rgba(0,0,0,0.05);
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 1rem;
}
.employee-card:hover {
  transform: translateY(-2px);
}
.employee-card .avatar {
  width: 60px;
  height: 60px;
  object-fit: contain;
}

.employee-card img.avatar {
  width: 70px;
  height: 70px;
  object-fit: contain;
  border-radius: 50%;
  margin: 0 auto;
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
.ai-analysis {
  background: #f7f7f7;
  padding: 1rem;
  border-radius: 12px;
  margin-top: 1.5rem;
}

.ai-analysis h4 {
  margin-top: 1rem;
  color: #333;
}

.ai-analysis h3 {
  font-size: 18px;
  margin-top: 1.2rem;
  color: #2c3e50;
  border-bottom: 1px solid #eee;
  padding-bottom: 0.4rem;
}

.columns {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.column {
  flex: 1;
  min-width: 200px;
}

.column ul {
  list-style: disc inside;
  padding-left: 1rem;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h4 {
  margin: 0;
  font-size: 1.1rem;
}

.factors {
  display: flex;
  gap: 12px;
  margin-top: 10px;
}

.factors .column {
  flex: 1;
  background: #f9f9f9;
  padding: 10px;
  border-radius: 8px;
}

.factors h5 {
  margin-bottom: 6px;
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
.employee-card .columns {
  display: flex;
  flex-direction: row;
  flex-wrap: wrap;
  gap: 1rem;
}

.employee-card .column {
  flex: 1;
  min-width: 200px;
  max-width: 48%;
  word-wrap: break-word;
}
.ai-analysis ul {
  margin-left: 1rem;
  padding-left: 1rem;
  list-style-type: disc;
}
</style>


