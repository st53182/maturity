<template>
  <div class="dashboard-container" :class="{ 'dashboard--new': variant === 'new' }">


    <div v-if="loading" class="loading">⏳ {{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">❌ {{ $t('common.error') }}: {{ error }}</div>

    <!-- 🔹 Список команд -->
    <div v-else class="teams-container">
      <div v-for="team in teams" :key="team.id" class="team-card">
        <h2 class="team-name">{{ team.name }}</h2>

        <!-- 🔹 Средняя оценка команды -->
        <div class="team-score-card">
          <h3>{{ $t('results.overallScore') }}</h3>
          <p class="score">{{ team.averageScore.toFixed(2) }}</p>
        </div>

        <!-- 🔹 Радар-график -->
        <RadarChart v-if="team.chartData" :chartData="team.chartData" class="radar-chart" />

        <!-- 🔹 Кнопки действий -->
        <div class="buttons">
          <button class="evaluate-btn" @click="goToSurvey(team.id)">📝 {{ $t('dashboard.takeAssessment') }}</button>
          <button class="view-results-btn" @click="goToResults(team.id, team.latest_assessment_id)">📊 {{ $t('dashboard.viewResults') }}</button>
          <button class="delete-btn" @click="deleteTeam(team.id)">🗑 {{ $t('common.delete') }}</button>
        </div>


      </div>
      <div class="team-card create-team-card" @click="showTeamModal = true">
        <div class="plus-icon">+</div>
        <p>{{ $t('dashboard.createTeam') }}</p>
      </div>

    </div>


    </div>

    <!-- 🔹 Pop-up для создания команды -->
<!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
      <div class="modal">
        <button class="modal-close-top" :aria-label="$t('common.close')" @click="showTeamModal = false">✕</button>
        <h2>{{ $t('survey.createNewTeam') }}</h2>
        <p class="modal-subtitle"></p>

        <input
          v-model="newTeamName"
          :placeholder="$t('survey.teamName')"
          class="team-input"
          @keyup.enter="createTeam"
        />

        <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ {{ $t('survey.create') }}</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ {{ $t('survey.cancel') }}</button>
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
  props: {
    team_id: { type: [String, Number], default: null },
    variant: { type: String, default: "legacy" },
  },

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
      if (this.variant === "new") {
        this.$router.push({ path: "/new/survey", query: { team_id: String(teamId) } });
      } else {
        this.$router.push({ name: "UserSurvey", query: { team_id: String(teamId) } });
      }
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
  margin-left: 0;
  padding: 30px;
  width: 100%;
  max-width: 100%;
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
  text-align: center;
  display: flex;
  justify-content: center;



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
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
  font-weight: bold;
}

.evaluate-btn:hover {
  background: #2980B9FF;
}

.view-results-btn {
  background: #7ce768;
}

.view-results-btn:hover {
  background: #27AE60FF;
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
  position: relative;
  border: 1px solid rgba(10, 20, 45, 0.1);
  box-shadow: 0 22px 60px rgba(10, 20, 45, 0.24);
}
.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.82);
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.delete-btn {
  background: #e7687c;
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  border: none;
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

@media (max-width: 768px) {
  .dashboard-container {
    margin-left: 0 !important;
    width: 100% !important;
    padding: 15px !important;
  }
  
  .teams-container {
    grid-template-columns: 1fr;
    gap: 15px;
  }
  
  .team-card {
    padding: 15px;
  }
  
  .radar-chart {
    max-width: 280px;
    height: 280px;
  }
  
  .modal {
    width: 95% !important;
    max-width: 95% !important;
    padding: 15px !important;
  }
  
  .team-input {
    width: 100% !important;
    font-size: 16px !important;
    box-sizing: border-box !important;
  }
  
  .modal-buttons {
    flex-direction: column !important;
    gap: 10px !important;
  }
  
  .confirm-btn,
  .cancel-btn {
    max-width: 100% !important;
    width: 100% !important;
  }
}

@media (max-width: 480px) {
  .teams-container {
    gap: 10px;
  }
  
  .radar-chart {
    max-width: 250px;
    height: 250px;
  }
}

/* —— New UI (только variant="new", /new/dashboard) —— */
.dashboard-container.dashboard--new {
  margin-left: 0;
  width: 100%;
  padding: 0;
  background: transparent;
}

.dashboard--new .teams-container {
  gap: 18px;
}

.dashboard--new .team-card {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 18px 50px rgba(10, 20, 45, 0.08);
  background: rgba(255, 255, 255, 0.92);
}

.dashboard--new .team-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 22px 60px rgba(32, 90, 255, 0.12);
}

.dashboard--new .team-score-card {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.88), rgba(0, 194, 255, 0.75));
  border-radius: 14px;
  padding: 16px 12px 20px;
  margin-bottom: 12px;
}

.dashboard--new .evaluate-btn,
.dashboard--new .view-results-btn,
.dashboard--new .delete-btn {
  border-radius: 12px;
  padding: 12px 16px;
  font-weight: 650;
  border: 1px solid transparent;
  box-shadow: 0 6px 18px rgba(10, 20, 45, 0.08);
  transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
}

.dashboard--new .evaluate-btn {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
  color: #fff;
}

.dashboard--new .evaluate-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(32, 90, 255, 0.28);
}

.dashboard--new .view-results-btn {
  background: linear-gradient(135deg, rgba(72, 187, 120, 0.95), rgba(34, 197, 94, 0.85));
  color: #fff;
}

.dashboard--new .view-results-btn:hover {
  filter: brightness(1.05);
  transform: translateY(-1px);
  box-shadow: 0 10px 26px rgba(34, 197, 94, 0.25);
}

.dashboard--new .delete-btn {
  background: rgba(255, 255, 255, 0.95);
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.35);
}

.dashboard--new .delete-btn:hover {
  background: #fef2f2;
  border-color: rgba(220, 38, 38, 0.55);
  transform: translateY(-1px);
  box-shadow: 0 8px 22px rgba(220, 38, 38, 0.15);
}

.dashboard--new .create-team-card {
  border: 2px dashed rgba(32, 90, 255, 0.28);
  background: rgba(255, 255, 255, 0.65);
  color: rgba(32, 90, 255, 0.9);
  border-radius: 18px;
}

.dashboard--new .create-team-card:hover {
  border-color: rgba(32, 90, 255, 0.45);
  background: rgba(32, 90, 255, 0.06);
  transform: translateY(-2px);
}

.dashboard--new .plus-icon {
  color: rgba(32, 90, 255, 0.85);
}

.dashboard--new .modal {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.14);
}

.dashboard--new .confirm-btn:hover,
.dashboard--new .cancel-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
}

.dashboard--new .team-card,
.dashboard--new .create-team-card,
.dashboard--new .modal {
  position: relative;
  overflow: hidden;
}

.dashboard--new .team-card::before,
.dashboard--new .create-team-card::before,
.dashboard--new .modal::before {
  content: "";
  position: absolute;
  top: -120%;
  left: -35%;
  width: 42%;
  height: 320%;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.38), transparent);
  transform: rotate(16deg);
  pointer-events: none;
  animation: premiumShine 9s linear infinite;
}

.dashboard--new .team-card:nth-child(2n)::before {
  animation-delay: 1.4s;
}

.dashboard--new .team-card:nth-child(3n)::before {
  animation-delay: 2.6s;
}

.dashboard--new .team-score-card {
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.42), 0 14px 32px rgba(32, 90, 255, 0.22);
}

.dashboard--new .team-input {
  border-color: rgba(32, 90, 255, 0.38);
  background: rgba(248, 250, 255, 0.95);
}

.dashboard--new .team-input:focus {
  border-color: rgba(32, 90, 255, 0.6);
  box-shadow: 0 0 0 5px rgba(32, 90, 255, 0.12);
}

@keyframes premiumShine {
  0% {
    transform: translateX(-220px) rotate(16deg);
  }
  45%,
  100% {
    transform: translateX(940px) rotate(16deg);
  }
}
</style>
