<template>
  <div class="survey-container">
    <h1>📊 Оценка зрелости команды</h1>

    <!-- 🔹 Выбор команды -->
    <div v-if="!selectedTeam" class="team-selection">
      <div class="team-buttons">
        <button
          v-for="team in teams"
          :key="team.id"
          class="team-btn"
          :class="{ active: selectedTeam === team.id }"
          @click="selectTeam(team.id, team.name)"
        >
          {{ team.name }}
        </button>
      </div>
      <div class="create-btn-container">
  <button class="modern-button purple" @click="showTeamModal = true">
    ➕ Создать команду
  </button>
</div>
    </div>

    <!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay">
      <div class="modal">
        <h2>Создать новую команду</h2>
        <input
          v-model="newTeamName"
          placeholder="Введите название команды"
          class="team-input"
        />
        <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ Создать</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ Отмена</button>
        </div>
      </div>
    </div>

    <!-- 🔹 Опросник -->
    <div v-else>
      <h2 class="team-name">🛠 Команда: {{ selectedTeamName }}</h2>
      <p class="disclaimer">
  🧠 <strong>Важно:</strong> Варианты ответов расположены от менее зрелых (1) к более зрелым (5).
  Выбирая более высокий уровень, предполагается, что предыдущие практики уже реализованы.
</p>

      <!-- 🔹 Прогресс-бар -->
      <div class="progress-bar">
        <div class="progress" :style="{ width: progress + '%' }"></div>
        <span class="progress-text">{{ Math.round(progress) }}% | ~{{ remainingTime }} мин</span>
      </div>
      <div class="question-tracker">
  <span
    v-for="(q, index) in questions"
    :key="q.id"
    class="tracker-dot"
    :class="{
      answered: answers[q.id],
      active: currentQuestionIndex === index
    }"
    @click="currentQuestionIndex = index"
  ></span>
</div>

      <!-- 🔹 Вопрос -->
      <div v-if="currentQuestion" class="question-card">
        <button v-if="currentQuestionIndex > 0" class="back-btn" @click="prevQuestion">⬅</button>
        <h2 class="question-text"> {{ currentQuestion.question }}</h2>

        <div class="answer-options">
          <button
            v-for="(desc, level) in currentQuestion.levels"
            :key="level"
            :class="{ selected: answers[currentQuestion.id] === level }"
            @click="answerQuestion(level)"
          >
            {{ desc }}
          </button>
        </div>
      </div>

      <!-- 🔹 Кнопка отправки -->
      <div style="text-align: center; margin-top: 30px;">
        <button
  v-if="allAnswered && currentQuestionIndex === questions.length - 1"
  class="modern-button purple"
  @click="submitAssessment"
>
  📩 Отправить результаты
</button>
      </div>
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

        const res = await axios.get("/user_teams", {
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
        const res = await axios.get("/questions");
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
          "/create_team",
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
      "/submit_assessment",
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
/* 🔷 Общий контейнер */
.survey-container {
  max-width: 900px;
  margin: auto;
  padding: 30px;
  text-align: center;
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.08);
  animation: fadeInUp 0.6s ease;
}

/* 🔷 Заголовок */
h1 {
  font-size: 28px;
  font-weight: 800;
  color: #2c3e50;
  margin-bottom: 20px;
}

/* 🔹 Прогресс бар */
.progress-bar {
  position: relative;
  width: 100%;
  height: 10px;
  background: #e0e0e0;
  border-radius: 5px;
  overflow: hidden;
  margin: 20px 0;
}
.progress {
  height: 100%;
  background: linear-gradient(90deg, #00c6ff, #0072ff);
  transition: width 0.4s ease-in-out;
}
.progress-text {
  position: absolute;
  top: -22px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 14px;
  font-weight: 600;
  color: #555;
}

/* 🔹 Вопрос */
.question-text {
  font-size: 22px;
  font-weight: bold;
  margin-bottom: 20px;
  line-height: 1.4;
}

/* 🔹 Ответы */
.answer-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: stretch;
}
.answer-options button {
  padding: 14px 20px;
  border-radius: 30px;
  background: #f0f0f0;
  color: #333;
  font-size: 16px;
  font-weight: 500;
  border: none;
  cursor: pointer;
  transition: all 0.25s ease;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}
.answer-options button:hover {
  background: #4caf50;
  color: #000000;
  transform: scale(1.03);
}
.answer-options button.selected {
  background: #4caf50;
  color: white;
  font-weight: bold;
}

/* 🔹 Кнопка отправки */
.send-button {
  margin-top: 25px;
  background: #8e44ad;
  color: white;
  padding: 14px 28px;
  border-radius: 12px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: 0.3s ease;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.send-button:hover {
  background: #732d91;
  transform: scale(1.03);
}

/* 🔹 Анимация появления */
.fade-in {
  opacity: 0;
  transform: translateY(12px);
  animation: fadeInUp 0.6s ease forwards;
}
@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 🔹 Плавная смена вопросов */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.4s ease;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(10px);
}

/* 🔹 Выбор команды */
.team-selection {
  margin-bottom: 20px;
}
.team-buttons {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 15px;
  margin-top: 10px;
}
.team-btn {
  background: #3498db;
  border: none;
  padding: 12px 22px;
  font-size: 16px;
  font-weight: bold;
  color: white;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}
.team-btn:hover {
  background: #2980b9;
  transform: scale(1.05);
}
.team-btn.active {
  background: #2ecc71;
}

/* 🔹 Кнопка "Создать команду" */
.create-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #8e44ad;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  margin-top: 10px;
  transition: color 0.2s ease;
}
.create-btn:hover {
  color: #732d91;
}

/* 🔹 Modal */
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
  z-index: 1000;
}
.modal {
  background: white;
  padding: 30px;
  border-radius: 16px;
  width: 100%;
  max-width: 400px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
  text-align: center;
}
.modal h2 {
  font-size: 22px;
  margin-bottom: 15px;
}
.team-input {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  border-radius: 10px;
  border: 2px solid #ccc;
  transition: border-color 0.3s ease;
}
.team-input:focus {
  border-color: #8e44ad;
  outline: none;
}
.modal-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 20px;
}
.confirm-btn,
.cancel-btn {
  flex: 1;
  margin: 0 5px;
  padding: 12px;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
  border: none;
  font-size: 16px;
}
.confirm-btn {
  background: #2ecc71;
  color: white;
}
.confirm-btn:hover {
  background: #27ae60;
}
.cancel-btn {
  background: #e74c3c;
  color: white;
}
.cancel-btn:hover {
  background: #c0392b;
}

.disclaimer {
  background: #f0f8ff;
  padding: 12px 16px;
  border-left: 5px solid #3498db;
  border-radius: 8px;
  margin-bottom: 20px;
  font-size: 15px;
  color: #2c3e50;
  text-align: left;
}

.answer-options button {
  transition: 0.3s;
}
.answer-options button:nth-child(1) { background-color: rgba(231, 104, 124, 0.6); }
.answer-options button:nth-child(2) { background-color: rgba(231, 211, 104, 0.6); }
.answer-options button:nth-child(3) { background-color: rgba(104, 124, 231, 0.6); }
.answer-options button:nth-child(4) { background-color: rgba(104, 188, 231, 0.6); }
.answer-options button:nth-child(5) { background-color: rgba(124, 231, 104, 0.6); }

.question-tracker {
  display: flex;
  justify-content: center;
  gap: 6px;
  margin-bottom: 18px;
}

.tracker-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #ccc;
  cursor: pointer;
  transition: background 0.3s ease;
}
.tracker-dot.answered {
  background: #2ecc71;
}
.tracker-dot.active {
  border: 2px solid #3498db;
  background: white;
}
</style>
