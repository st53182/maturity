<template>
  <div class="dashboard-container">


    <div v-if="loading" class="loading">⏳ Загружаем данные...</div>
    <div v-else-if="error" class="error">❌ Ошибка: {{ error }}</div>

    <!-- 🔹 Список команд -->
    <div v-else class="teams-container">
      <div v-for="team in teams" :key="team.id" class="team-card">
        <h2 class="team-name">{{ team.name }}</h2>

        <!-- 🔹 Средняя оценка команды -->
        <div class="team-score-card">
          <h3>Средняя оценка</h3>
          <p class="score">{{ team.averageScore.toFixed(2) }}</p>
        </div>

        <!-- 🔹 Радар-график -->
        <RadarChart v-if="team.chartData" :chartData="team.chartData" class="radar-chart" />

        <!-- 🔹 Кнопки действий -->
        <div class="buttons">
          <button class="evaluate-btn" @click="goToSurvey(team.id)">📝 Оценить команду</button>
          <button class="view-results-btn" @click="goToResults(team.id, team.latest_assessment_id)">📊 Смотреть результаты</button>
          <button class="delete-btn" @click="deleteTeam(team.id)">🗑 Удалить</button>
        </div>


      </div>
      <div class="team-card create-team-card" @click="showTeamModal = true">
        <div class="plus-icon">+</div>
        <p>Создать команду</p>
      </div>

    </div>


    </div>

    <!-- 🔹 Pop-up для создания команды -->
<!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
      <div class="modal">
        <h2>Создать новую команду</h2>
        <p class="modal-subtitle"></p>

        <input
          v-model="newTeamName"
          placeholder="Название команды"
          class="team-input"
          @keyup.enter="createTeam"
        />

        <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ Создать</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ Отмена</button>
        </div>

      </div>

    </div>

</template>

<script>
import { useAuthStore } from "@/stores/auth"; // Импортируем хранилище аутентификации
import {onMounted} from "vue";
import axios from "axios";
import RadarChart from "@/components/RadarChart.vue";
 /* eslint-disable */
export default {
  components: { RadarChart },
  props: ["team_id"],

  setup() {
    const authStore = useAuthStore(); // Подключаем Pinia


    // Вычисляемое свойство для проверки авторизации
      onMounted(() => {
      authStore.checkAuth(); // ✅ Проверяем токен при загрузке
    });

    return { authStore };
  },

  data() {
    return {
      results: {},
      radarData: {},
      loading: true,
      error: null,
      showTeamModal: false,
      averageScore: 0,
      newTeamName: "",
    };

  },

  methods: {
    async fetchTeams() {
      try {
        console.log("📡 Загружаем список команд...");
        const token = localStorage.getItem("token");

        if (!token) {
          console.error("❌ Нет токена авторизации!");
          alert("🚫 Вы не авторизованы!");
          return;
        }

        const res = await axios.get("/user_teams", {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.teams = await Promise.all(
          res.data.map(async team => {
            const rawResults = await this.fetchResults(team.id);
            console.log("👉 rawResults для", team.name, rawResults);
            const chartData = rawResults ? this.generateRadarData(rawResults) : null;
            const averageScore = rawResults ? this.calculateAverageFromResults(rawResults) : 0;
            return {
              ...team,
              chartData,
              averageScore
            };
          })
        );

        console.log("✅ Команды загружены:", this.teams);
      } catch (error) {
        console.error("❌ Ошибка загрузки команд:", error.response?.data || error);
        this.error = "Ошибка загрузки команд.";
      } finally {
        this.loading = false;
      }
    },



    async fetchResults(teamId) {
  try {
    console.log(`📡 Загружаем результаты для команды ID ${teamId}`);
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("❌ Нет токена авторизации!");
      return null;
    }

    const res = await axios.get(`/team_results/${teamId}`, {
      headers: { Authorization: `Bearer ${token}` }
    });

    return res.data.results; // 👈 просто отдаём сырые данные
  } catch (error) {
    console.error("❌ Ошибка загрузки результатов:", error.response?.data || error);
    return null;
  }
},

    async fetchResultsHistory() {
  try {
    const token = localStorage.getItem("token");

    const res = await axios.get(
      `/team_results_history/${this.team_id}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );

    const history = res.data;
    console.log("📜 История оценок:", history);

    const sortedDates = Object.keys(history).sort().reverse();

    if (sortedDates.length >= 2) {
      // ✅ Показываем два последних измерения по категориям
      this.buildCombinedRadarDataByCategory(history);
      this.calculateAverageFromLatestSession(history); // <-- заменили функцию
    } else if (sortedDates.length === 1) {
      // ✅ Только одно измерение — используем обычную отрисовку
      this.prepareRadarData();
    } else {
      // ❌ Нет данных вообще
      this.error = "Пожалуйста, пройдите опрос для вашей команды.";
    }

  } catch (error) {
    console.error("❌ Ошибка при получении истории:", error.response?.data || error);
    this.error = "Ошибка при получении истории команды.";
  }
},



    async deleteTeam(teamId) {
  if (!confirm("Вы уверены, что хотите удалить эту команду? Это действие необратимо!")) {
    return;
  }

  try {
    console.log(`🗑 Удаляем команду ID: ${teamId}`);
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("❌ Нет токена авторизации!");
      alert("🚫 Вы не авторизованы!");
      return;
    }

    await axios.delete(`/dashboard/delete_team/${teamId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    console.log("✅ Команда успешно удалена!");
    alert("✅ Команда удалена!");

    // 🔄 Обновляем список команд после удаления
    await this.fetchTeams();
    window.location.reload();

  } catch (error) {
    console.error("❌ Ошибка удаления команды:", error.response?.data || error);
    alert("❌ Ошибка удаления команды.");
  }
},

    async createTeam() {
  if (!this.newTeamName.trim()) {
    alert("Введите название команды!");
    return;
  }

  try {
    console.log("📤 Создание команды...");
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("❌ Нет токена авторизации!");
      alert("🚫 Вы не авторизованы!");
      return;
    }

    const res = await axios.post(
      "/create_team",
      { team_name: this.newTeamName },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    console.log("✅ Команда успешно создана:", res.data);
    alert("🎉 Команда создана!");

    // 🔄 Обновляем список команд
    await this.fetchTeams();

    // ✅ Очищаем поле и закрываем pop-up
    this.newTeamName = "";
    this.showTeamModal = false;

    // 🔄 Перезагружаем страницу
    window.location.reload();

  } catch (error) {
    console.error("❌ Ошибка создания команды:", error.response?.data || error);
    alert("❌ Ошибка создания команды. Убедись не занято ли имя команды.");
  }
},


    generateRadarData(results) {
      if (!results) return { labels: [], datasets: [] };

      const categories = Object.keys(results);
      const scores = categories.map(category => {
        const values = Object.values(results[category]).map(val => parseFloat(val) || 0);
        return values.length ? values.reduce((sum, val) => sum + val, 0) / values.length : 0;
      });

      return {
        labels: categories,
        datasets: [
          {
            label: "Средняя оценка",
            data: scores,
            backgroundColor: "rgba(75, 192, 192, 0.2)",
            borderColor: "rgba(75, 192, 192, 1)",
            borderWidth: 2
          }
        ]
      };
    },

    calculateAverage(chartData) {
      if (!chartData || !chartData.datasets.length) return 0;
      const total = chartData.datasets[0].data.reduce((sum, val) => sum + val, 0);
      return total / chartData.datasets[0].data.length;
    },

    calculateAverageFromResults(results) {
  let total = 0;
  let count = 0;

  for (const category of Object.values(results)) {
    for (const score of Object.values(category)) {
      total += parseFloat(score);
      count++;
    }
  }

  return count > 0 ? total / count : 0;
},
    // eslint-disable-next-line no-undef
    goToResults(teamId,latest_assessment_id) {
      this.$router.push({ name: "AssessmentResults", params: { team_id: teamId,  assessment_id: latest_assessment_id } });
    },

    goToSurvey(teamId) {
      this.$router.push({ name: "UserSurvey", params: { team_id: teamId } });
    }
  },


  async mounted() {
    const token = localStorage.getItem("token");
    if (!token) {
      console.warn("🚫 Пользователь не авторизован. Перенаправляем на страницу входа...");
      this.$router.push("/login"); // 🔄 Перенаправляем на страницу логина
      return; // ⛔ Прерываем дальнейшее выполнение кода
    }

    await this.fetchTeams();
  }
};
</script>

<style scoped>
/* 🔹 Основной контейнер */
.dashboard-container {
  margin-left: 70px; /* чтобы не пересекаться с sidebar */
  padding: 30px;
  width: calc(100% - 70px);
  box-sizing: border-box;
  background: #f4f6f9;
}

/* 🔹 Заголовок */
h1 {
  font-size: 30px;
  color: #2c3e50;
  font-weight: bold;
}

/* 🔹 Контейнер команд */
.teams-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  width: 100%;
}

/* 🔹 Карточка команды */
.team-card {
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
}

.team-card:hover {
  transform: scale(1.03);
}

/* 🔹 Название команды */
.team-name {
  font-size: 22px;
  font-weight: bold;
  color: #2c3e50;
}

/* 🔹 Карточка средней оценки */
.team-score-card {
  background: linear-gradient(135deg, rgba(110, 143, 204, 0.56), #b3c5ea);
  padding-top: 20px;
  padding-bottom: 1px;
  border-radius: 5px;
  color: white;
  text-align: center;
  margin-bottom: 1px;
}

.team-score-card h3 {
  margin: 0;
  font-size: 18px;
}

.team-score-card .score {
  font-size: 32px;
  font-weight: bold;
  margin-top: 5px;
}

/* 🔹 График */
.radar-chart {
  width: 100%;
  max-width: 350px;
  height: 350px;
  margin: auto;
}

/* 🔹 Кнопки */
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 15px;
}

.evaluate-btn,
.view-results-btn {
  background: #687ce7;
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
}

.evaluate-btn:hover {
  background: #687ce7;
}

.view-results-btn {
  background: #7ce768;
}

.view-results-btn:hover {
  background: #7ce768;
}

/* 🔹 Ошибки и загрузка */
.loading, .error {
  font-size: 18px;
  color: #555;
}
.error {
  color: #e74c3c;
  font-weight: bold;
}
/* 🔹 Кнопка "Создать команду" */
.create-team-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 22px;
  color: #2ecc71;
  cursor: pointer;
}

.plus-icon {
  font-size: 50px;
  font-weight: bold;
}

/* 🔹 Pop-up */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  text-align: center;
}
.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  width: 350px; /* Ширина Pop-up */
  max-width: 90%; /* Адаптация к мобильным экранам */
}
.delete-btn {
  background: #e7687c;
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  cursor: pointer;
  font-weight: bold;
  transition: 0.3s;
}

.team-input {
  width: 90%;
  padding: 14px;
  border: 3px solid #3498db;
  border-radius: 10px;
  font-size: 18px;
  text-align: center;
  transition: 0.3s;
  margin-top: 5px;
}

.modal-buttons {
  display: flex;
  justify-content: space-evenly; /* Равномерное распределение */
  align-items: center;
  margin-top: 25px;
  gap: 15px;
}

.confirm-btn,
.cancel-btn {
  flex: 1; /* Одинаковая ширина */
  background: #2ecc71;
  color: white;
  padding: 15px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  border: none;
  transition: 0.3s;
  text-align: center;
  max-width: 160px; /* Максимальная ширина кнопки */
  max-height: 100px;
}

.confirm-btn:hover {
  background: #27ae60;
}

.cancel-btn {
  background: #e74c3c;
}

.cancel-btn:hover {
  background: #c0392b;
}

.team-input:focus {
  border-color: #2ecc71;
  outline: none;
}

.delete-btn:hover {
  background: #c0392b;
}
</style>
