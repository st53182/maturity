<template>
  <div class="survey-container">
    <h1>📊 Оценка зрелости команды</h1>

    <!-- 🔹 Выбор команды -->
    <div v-if="!selectedTeam" class="team-section">

      <div class="team-buttons">
        <button
          v-for="team in teams"
          :key="team.id"
          class="team-btn"
          :class="{ active: selectedTeam === team.id }"
          @click="selectTeam(team.id, team.name)">
          {{ team.name }}
        </button>
      </div>

      <!-- 🔹 Создание команды -->

    </div>


    <!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay">
      <div class="modal">
        <h2>Создать новую команду</h2>
        <input v-model="newTeamName" placeholder="Введите название команды" class="team-input" />
        <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">Создать</button>
          <button class="cancel-btn" @click="showTeamModal = false">Отмена</button>
        </div>
      </div>
    </div>


    <!-- 🔹 Опросник (оставил стиль нетронутым) -->
    <div v-else>
      <h2 class="team-name">🛠 Команда: {{ selectedTeamName }}</h2>

      <!-- 🔹 Прогресс-бар с временем -->
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ Math.round(progress) }}% | ~{{ remainingTime }} мин</span>
      </div>

      <!-- 🔹 Вопрос -->
      <div v-if="currentQuestion" class="question-card">
        <button v-if="currentQuestionIndex > 0" class="back-btn" @click="prevQuestion">⬅</button>
        <h2 class="question-text">❓ {{ currentQuestion.question }}</h2>

        <!-- 🔹 Варианты ответа -->
        <div class="answer-options">
          <button
            v-for="(desc, level) in currentQuestion.levels"
            :key="level"
            :class="{ selected: answers[currentQuestion.id] === level }"
            @click="answerQuestion(level)">
            {{ desc }}
          </button>
        </div>
      </div>

      <!-- 🔹 Отправка результатов -->
      <button v-if="allAnswered" class="submit-btn" @click="submitAssessment">
        📩 Отправить результаты
      </button>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      teams: [],
      selectedTeam: null,
      selectedTeamName: "",
      newTeamName: "",
      questions: [],
      answers: {},
      showTeamModal: false,
      currentQuestionIndex: 0,
      avgTimePerQuestion: 1.5, // Среднее время на один вопрос в минутах
    };
  },

  computed: {
    progress() {
      return this.questions.length ? (this.currentQuestionIndex / this.questions.length) * 100 : 0;
    },
    remainingTime() {
      return Math.max(0, Math.round((this.questions.length - this.currentQuestionIndex) * this.avgTimePerQuestion));
    },
    currentQuestion() {
      return this.questions[this.currentQuestionIndex] || null;
    },
    allAnswered() {
      return Object.keys(this.answers).length === this.questions.length;
    },
  },

  methods: {
    async fetchTeams() {
      try {
        console.log("📡 Загружаем список команд...");
        const token = localStorage.getItem("token");

        if (!token) {
          console.error("❌ Ошибка: Нет токена авторизации!");
          alert("🚫 Вы не авторизованы!");
          return;
        }

        const res = await axios.get("http://127.0.0.1:5000/user_teams", {
          headers: { Authorization: `Bearer ${token}` },
        });

        this.teams = res.data;
        console.log("✅ Команды загружены:", this.teams);
      } catch (error) {
        console.error("❌ Ошибка загрузки команд:", error.response?.data || error);
        alert("❌ Ошибка загрузки команд.");
      }
    },

    async fetchQuestions() {
      try {
        const res = await axios.get("http://127.0.0.1:5000/questions");
        this.questions = res.data;
      } catch (error) {
        console.error("❌ Ошибка загрузки вопросов:", error);
      }
    },

    selectTeam(teamId, teamName) {
      this.selectedTeam = teamId;
      this.selectedTeamName = teamName;
      this.fetchQuestions();
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
          console.error("❌ Ошибка: Нет токена авторизации!");
          alert("🚫 Вы не авторизованы!");
          return;
        }

        const res = await axios.post(
          "http://127.0.0.1:5000/create_team",
          { team_name: this.newTeamName },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        console.log("✅ Команда успешно создана:", res.data);

        await this.fetchTeams();
        this.selectTeam(res.data.id, res.data.name);
        this.showTeamModal = false; // Закрываем Pop-up
      } catch (error) {
        console.error("❌ Ошибка создания команды:", error.response?.data || error);
        alert("❌ Ошибка создания команды.");
      }
    },

    answerQuestion(level) {
      this.answers[this.currentQuestion.id] = level;
      if (this.currentQuestionIndex < this.questions.length - 1) {
        this.currentQuestionIndex++;
      }
    },

    prevQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--;
      }
    },

    async submitAssessment() {
  try {
    console.log("📤 Отправка результатов...");
    const token = localStorage.getItem("token");

    if (!token) {
      console.error("❌ Ошибка: Нет токена авторизации!");
      alert("🚫 Вы не авторизованы!");
      return;
    }

    const res = await axios.post(
      "http://127.0.0.1:5000/submit_assessment",
      {
        team_id: this.selectedTeam,
        answers: this.answers,
      },
      { headers: { Authorization: `Bearer ${token}` } }
    );

    const assessmentId = res.data.assessment_id; // ✅ берём ID созданной оценки

    alert("🎉 Результаты сохранены!");

    // 🔁 Переход с передачей assessment_id в параметры
    this.$router.push({
      name: "AssessmentResults",
      params: {
        team_id: this.selectedTeam,
        assessment_id: assessmentId,
      },
    });
  } catch (error) {
    console.error("❌ Ошибка отправки:", error.response?.data || error);
    alert("❌ Ошибка отправки результатов.");
  }
}
  },

  mounted() {
    this.fetchTeams();
  },
};
</script>

<style scoped>
/* Основные стили */
.survey-container {
  max-width: 800px;
  margin: auto;
  padding: 20px;
  text-align: center;
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}

/* Прогресс-бар */
.progress-bar {
  position: relative;
  width: 100%;
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  margin: 10px 0;
}
.progress {
  height: 100%;
  background: linear-gradient(to right, #4caf50, #8bc34a);
  transition: width 0.5s ease-in-out;
}
.progress-text {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 14px;
  font-weight: bold;
  color: #555;
}

/* Вопрос */
.question-text {
  font-size: 22px;
  font-weight: bold;
}

/* Варианты ответа */
.answer-options button {
  padding: 12px 20px;
  border-radius: 20px;
  cursor: pointer;
  background: #f0f0f0;
  transition: 0.3s;
  font-size: 16px;
}
.answer-options button:hover, .answer-options button.selected {
  background: #4caf50;
  color: white;
}
.team-selection {
  text-align: center;
  padding: 20px;
}
.team-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
  margin-bottom: 20px;
}
.team-btn {
  background: #3498db;
  border: none;
  padding: 12px 20px;
  font-size: 18px;
  color: white;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.3s;
}
.create-btn{
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  font-size: 22px;
  color: #f9fbfb;
  cursor: pointer;

}
.team-btn:hover {
  background: #2980b9;
}
.team-btn.active {
  background: #27ae60;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  text-align: center;
}
.modal-buttons {
  margin-top: 10px;
}
.confirm-btn {
  background: #4caf50;
  color: white;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
}
.cancel-btn {
  background: #e74c3c;
  color: white;
  padding: 10px;
  border-radius: 5px;
  cursor: pointer;
}
.team-card {
  background: #3497d9;
  border-radius: 5px;
  padding: 5px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  transition: transform 0.2s ease-in-out;
}
</style>
