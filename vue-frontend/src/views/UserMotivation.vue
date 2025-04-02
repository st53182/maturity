<template>
  <div class="motivation-container">
    <h1>🎯 Мотивация сотрудника</h1>

    <form @submit.prevent="submitMotivation">
      <div class="form-group">
        <label>Имя сотрудника:</label>
        <input v-model="form.name" placeholder="Например: Иван Иванов" required />

        <label>Должность:</label>
        <input v-model="form.role" placeholder="Например: Аналитик, Разработчик..." required />

        <label>Команда:</label>
        <select v-model="form.team_id">
          <option disabled value="">-- Не выбрано --</option>
          <option v-for="team in teams" :key="team.id" :value="team.id">
            {{ team.name }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label>1. Поведение в стрессовой ситуации</label>
        <textarea v-model="form.stress" placeholder="Как он реагирует на давление, конфликты..." required></textarea>

        <label>2. Взаимодействие с другими</label>
        <textarea v-model="form.communication" placeholder="Открытый, сдержанный, любит работать в команде или один..." required></textarea>

        <label>3. Особенности в работе</label>
        <textarea v-model="form.behavior" placeholder="Привычки, подход, структура, планирование..." required></textarea>

        <label>4. Реакции на критику и изменения</label>
        <textarea v-model="form.feedback" placeholder="Как принимает фидбек, открыт к переменам..." required></textarea>
      </div>

      <button type="submit" :disabled="loading">
        {{ loading ? "Сохраняем и анализируем..." : "Сохранить и получить рекомендации" }}
      </button>
    </form>

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
      result: "",
      loading: false
    };
  },
  async mounted() {
  const token = localStorage.getItem("token");
  if (!token) {
    console.warn("⛔ Нет токена авторизации!");
    return;
  }

  try {
    const response = await fetch("/user_teams", {
      headers: {
        "Authorization": `Bearer ${token}`
      }
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("⛔ Ошибка при получении команд:", errorText);
      return;
    }

    const data = await response.json();
    console.log("✅ Команды загружены:", data);
    this.teams = data;

  } catch (err) {
    console.error("❌ Ошибка запроса:", err);
  }
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
        } else {
          alert(data.error || "Ошибка анализа");
        }
      } catch (err) {
        console.error("❌ Ошибка запроса:", err);
        alert("Не удалось получить рекомендации.");
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
    }
  }
};
</script>


<style scoped>
.motivation-container {
  max-width: 800px;
  margin: auto;
  padding: 30px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
}
.form-group {
  margin-bottom: 20px;
}
textarea,
input,
select {
  width: 100%;
  padding: 10px;
  margin-top: 6px;
  margin-bottom: 12px;
  border-radius: 6px;
  border: 1px solid #ccc;
}
button {
  background: #4caf50;
  color: white;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s;
}
button:hover {
  background: #3b8d3f;
}
.result-block {
  margin-top: 30px;
  background: #f8f8f8;
  padding: 20px;
  border-radius: 10px;
}
</style>
