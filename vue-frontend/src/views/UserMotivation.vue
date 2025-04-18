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
          <h4 class="employee-name">{{ employee.name }}</h4>
          <button class="delete-btn" @click.stop="deleteEmployee(employee.id)">🗑</button>

        </div>
        <p class="team-name">🏢 Команда: <strong>{{ getTeamName(employee.team_id) || '—' }}</strong></p>
        <p class="disc-type-full">🧠 Тип DISC: <strong>{{ extractDISCFullType(employee.ai_analysis) }}</strong></p>
        <div class="employee-card-footer">
    <button class="update-btn" @click="handleEmployeeClick(employee)">
      🔄 Обновить рекомендации
    </button>
  </div>

        <div v-if="employee.ai_analysis" class="factors">
          <div class="column">
            <h5>⬆️ Мотиваторы</h5>
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

    <div v-if="employee.ai_analysis" class="manager-tips-block" v-html="extractManagerTips(employee.ai_analysis)"></div>

<div class="form-footer">

</div>

      </div>

      <div class="employee-card add-card" @click="resetForm">
        <span>➕</span>
        <p>Создать</p>
      </div>
    </div>

    <!-- 🔹 Форма -->


    <!-- 🔹 Результат -->

  </div>
  <div v-if="showModal" class="modal-overlay">
  <div class="modal-content">
     <button class="modal-close" @click="showModal = false">✖</button>

    <form @submit.prevent="submitMotivation" class="form-group">
      <h2 style="text-align: center;">📝 Информация о сотруднике</h2>

      <label>Имя сотрудника:</label>
      <input v-model="form.name" required />

      <label>Должность:</label>
      <input v-model="form.role" required />

      <label>Команда (необязательно):</label>
<select v-model="form.team_id">
  <option value="">— Без команды —</option>
  <option v-for="team in teams" :key="team.id" :value="team.id">
    {{ team.name }}
  </option>
</select>

      <label>1. Поведение в стрессовой ситуации</label>
      <textarea v-model="form.stress" required></textarea>

      <label>2. Взаимодействие с другими</label>
      <textarea v-model="form.communication" required></textarea>

      <label>3. Особенности в работе</label>
      <textarea v-model="form.behavior" required></textarea>

      <label>4. Реакции на критику и изменения</label>
      <textarea v-model="form.feedback" required></textarea>

      <button
  @click="submitMotivation(false)"
  :disabled="loading"
>
  💾 Сохранить
</button>

<!-- Сохранить и сгенерировать -->
<button
  @click="submitMotivation(true)"
  :disabled="loading"
>
  <span v-if="loading">⏳ Генерация...</span>
  <span v-else>💬 Получить рекомендации</span>
</button>

    </form>
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
      loading: false,
      showModal: false,
      avatar: "default.png"
    };
  },

  async mounted() {
    const token = localStorage.getItem("token");

    try {
      // Получение команд
      const teamRes = await fetch("/user_teams", {
        headers: { Authorization: `Bearer ${token}` }
      });
      this.teams = await teamRes.json();

      // Получение сотрудников
      const empRes = await fetch("/employees", {
        headers: { Authorization: `Bearer ${token}` }
      });

      const rawEmployees = await empRes.json();

      if (!Array.isArray(rawEmployees)) {
        console.error("Сотрудники не получены:", rawEmployees);
        return;
      }

      this.employees = rawEmployees.map(e => ({
        ...e,
        motivators: this.extractFactors(e.ai_analysis, "Мотивирующие"),
        demotivators: this.extractFactors(e.ai_analysis, "Демотиваторы"),
        managerTips: this.extractManagerTips(e.ai_analysis)
      }));
    } catch (err) {
      console.error("Ошибка при загрузке:", err);
    }
  },

  methods: {
    async submitMotivation(generate = false) {
  this.loading = true;
  const token = localStorage.getItem("token");

  const url = generate ? "/motivation" : "/employees";
  const method = "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        ...this.form,
        id: this.form.id, // всегда передаём id
        team_id: this.form.team_id || null // избегаем ошибки "" в integer
      })
    });

    const data = await res.json();

    if (res.ok) {
      this.result = data.analysis || data.message;
      this.form.id = data.employee_id || data.id;

      const updated = {
        ...this.form,
        id: this.form.id,
        ai_analysis: data.analysis || "",
        motivators: this.extractFactors(data.analysis, "Мотивирующие"),
        demotivators: this.extractFactors(data.analysis, "Демотиваторы"),
        managerTips: this.extractManagerTips(data.analysis)
      };

      const index = this.employees.findIndex(e => e.id === this.form.id);
      if (index !== -1) {
        this.employees.splice(index, 1, updated);
      } else {
        this.employees.push(updated);
        await this.fetchEmployees();

      }

      this.showModal = false;
      setTimeout(() => {
    location.reload();
  }, 300);
    } else {
      alert(data.error || "Ошибка сохранения");
    }
  } catch (err) {
    console.error(err);
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
      this.showModal = true;
    },

    async deleteEmployee(id) {
      const token = localStorage.getItem("token");
      if (!confirm("Удалить сотрудника?")) return;

      try {
        await fetch(`/employee/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        this.employees = this.employees.filter(e => e.id !== id);
      } catch (e) {
        console.error("Ошибка удаления", e);
      }
    },

    handleEmployeeClick(employee) {
      this.selectEmployee(employee);
      this.showModal = true;
    },

    selectEmployee(employee) {
      this.form = { ...employee };
      this.result = employee.ai_analysis;
    },

    extractDISCFullType(aiText) {
      if (!aiText) return "Неизвестно";
      const match = aiText.match(/Тип DISC[:-]?\s*<\/?strong>?[\s"]*([A-ZА-Я]\s*\([^)]+?\))/i)
                 || aiText.match(/Тип DISC[:-]?\s*([A-ZА-Я]\s*\([^)]+?\))/i);
      return match ? match[1].trim() : "Неизвестно";
    },

    extractFactors(html, sectionTitle) {
      if (!html) return [];

      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;

      const headers = Array.from(tempDiv.querySelectorAll('h3, h4, strong'));
      const header = headers.find(h =>
        h.textContent.toLowerCase().includes(sectionTitle.toLowerCase())
      );

      if (!header) return [];

      const ul = header.nextElementSibling;
      if (!ul || ul.tagName !== 'UL') return [];

      return Array.from(ul.querySelectorAll('li')).map(li => li.textContent.trim());
    },

    extractDISCType(aiText) {
      if (!aiText) return "Неизвестно";

      const match =
        aiText.match(/Тип DISC[:-]?\s*<\/?strong>?[\s"]*([A-ZА-Я][^)<\n:]*\([A-ZА-Я]\))/i) ||
        aiText.match(/тип\s+[A-ZА-Я]\s*\([^)]+\)/i) ||
        aiText.match(/тип\s+["«]?(.)["»]?/i);

      return match ? match[1].trim() : "Неизвестно";
    },

    extractManagerTips(text) {
      if (!text) return '';
      const match = text.match(/<h3>Рекомендации для руководителя:.*?<\/ul>/is);
      return match ? match[0] : '';
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





<style scoped>
.motivation-container {
  max-width: 1200px;
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
  max-width: 650px;
  margin: 1rem auto;
  padding: 1.5rem 2rem;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  gap: 16px;
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
  background: #677be5;
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
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.employee-card {
  /* Убери width */
  min-height: 100px;
  padding: 1rem;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 0 10px rgba(0, 0, 0, 0.04);
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

.employee-card .employee-name {
  text-align: center;
  font-size: 18px;
  font-weight: bold;
}

.employee-card .team-name,
.employee-card .disc-type-full {
  text-align: center;
  font-size: 14px;
  color: #444;
  margin: 0;
}

.disc-type-full strong {
  color: #2c3e50;
}

.employee-card .delete-btn {
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
  min-height: 240px;
  background: #f3f3f3;
  justify-content: center;
  align-items: center;
  text-align: center;
  font-size: 18px;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border-radius: 14px;
  padding: 1rem;
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
  overflow: visible;
  max-height: none;
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

.manager-tips-block {
  margin-top: 10px;
  background: #f9f9f9;
  padding: 12px;
  border-radius: 8px;
  font-size: 13px;
}

.manager-tips-block ul {
  padding-left: 1.2rem;
  list-style-type: disc;
}

.manager-tips-block li {
  margin-bottom: 6px;
}

.manager-tips-block h3 {
  margin-bottom: 10px;
  font-size: 15px;
  color: #222;
}

.employee-card-footer {
  margin-top: 1rem;
  display: flex;
  justify-content: center;
}

.update-btn {
  padding: 10px 20px;
  background-color: #677be5;
  color: #fff;
  font-weight: bold;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.update-btn:hover {
  background-color: #2c80c0;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
  display: flex;
  align-items: center;
  justify-content: center;
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

.modal-close {
  position: absolute;
  top: 10px;
  right: 14px;
  background: none;
  border: none;
  font-size: 22px;
  color: #999;
  cursor: pointer;
  transition: 0.2s;
}

.modal-close:hover {
  color: #000;
}

.modal-content h2 {
  font-size: 22px;
  margin-bottom: 24px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-content label {
  display: block;
  margin-top: 16px;
  font-weight: bold;
  color: #2c3e50;
  font-size: 14px;
}

.modal-content input,
.modal-content select,
.modal-content textarea {
  width: 100%;
  margin-top: 6px;
  padding: 10px 12px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 14px;
  resize: vertical;
}

.modal-actions {
  margin-top: 30px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.modal-actions button {
  padding: 12px 20px;
  font-weight: bold;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 15px;
  transition: 0.3s ease;
}

.modal-actions button:first-child {
  background-color: #4a90e2;
  color: white;
}

.modal-actions button:first-child:hover {
  background-color: #337acc;
}

.modal-actions button:last-child {
  background-color: #1d71b8;
  color: white;
}

.modal-actions button:last-child:hover {
  background-color: #155a94;
}

</style>

