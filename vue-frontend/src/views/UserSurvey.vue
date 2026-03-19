<template>
  <div class="survey-container" :class="{ 'survey--new': variant === 'new' }">
    <h1>{{ $t('newSurvey.selectTeamForMaturity') }}</h1>

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

    </div>

    <!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay">
      <div class="modal">
        <h2>{{ $t('survey.createNewTeam') }}</h2>
        <input
          v-model="newTeamName"
          :placeholder="$t('survey.teamName')"
          class="team-input"
        />
        <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ {{ $t('survey.create') }}</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ {{ $t('survey.cancel') }}</button>
        </div>
      </div>
    </div>

    <!-- 🔹 Опросник -->
    <div v-else>
      <h2 class="team-name">{{ $t('newSurvey.teamPrefix') }}: {{ selectedTeamName }}</h2>
      <p class="disclaimer">
        {{ $t('newSurvey.disclaimer') }}
</p>

      <!-- 🔹 Прогресс-бар -->

      <div class="question-tracker">
  <button
    type="button"
    v-for="(q, index) in questions"
    :key="q.id"
    class="tracker-dot"
    :aria-label="`${$t('survey.question')} ${index + 1}`"
    :class="{
      answered: answers[q.id],
      active: currentQuestionIndex === index
    }"
    @click="currentQuestionIndex = index"
  ></button>
</div>

      <!-- 🔹 Вопрос -->
      <div v-if="currentQuestion" class="question-card">
        <button v-if="currentQuestionIndex > 0" class="back-btn" :aria-label="$t('maturity.prev')" @click="prevQuestion">⬅</button>
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
  {{ $t('newSurvey.submitResults') }}
</button>
      </div>
    </div>
  </div>
</template>


<script>
import axios from "axios";

export default {
  props: {
    variant: { type: String, default: "legacy" },
  },
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
        const lang = this.$i18n.locale;
        const res = await axios.get(`/questions?lang=${lang}`);
        this.questions = res.data;
      } catch (error) {
        console.error("❌ Ошибка загрузки вопросов:", error);
        this.$toast.error(this.$t('survey.errorLoadingQuestions'));
      }
    },

    selectTeam(teamId, teamName) {
      this.selectedTeam = teamId;
      this.selectedTeamName = teamName;
      this.fetchQuestions();
    },

    async createTeam() {
      if (!this.newTeamName.trim()) {
        alert(this.$t("newSurvey.enterTeamName"));
        return;
      }

      try {
        console.log("📤 Создание команды...");
        const token = localStorage.getItem("token");

        if (!token) {
          console.error("❌ Ошибка: Нет токена авторизации!");
          alert(this.$t("newSurvey.notAuthorized"));
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
        alert(this.$t("newSurvey.teamCreateError"));
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
      alert(this.$t("newSurvey.notAuthorized"));
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

    alert(this.$t("newSurvey.resultsSaved"));

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
    alert(this.$t("newSurvey.submitError"));
  }
}
  },

  async mounted() {
    await this.fetchTeams();
    const tid = this.$route.query.team_id;
    if (tid != null && tid !== "") {
      const team = this.teams.find((t) => String(t.id) === String(tid));
      if (team) {
        this.selectTeam(team.id, team.name);
      }
    }
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
  border: none;
  padding: 0;
}
.tracker-dot.answered {
  background: #2ecc71;
}
.tracker-dot.active {
  border: 2px solid #3498db;
  background: white;
}

.modern-button {
  font-weight: 600;
  padding: 12px 20px;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  gap: 8px;
  color: white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  min-width: 220px;
}

/* 🟣 Фиолетовый стиль */
.modern-button.purple {
  background: linear-gradient(135deg, #8e44ad, #9b59b6);
}

.modern-button.purple:hover {
  background: linear-gradient(135deg, #732d91, #8e44ad);
  transform: scale(1.04);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

/* —— New UI (/new/survey) —— */
.survey-container.survey--new {
  max-width: 880px;
  margin: 0 auto 40px;
  padding: 28px 22px 36px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 22px 70px rgba(10, 20, 45, 0.1);
}

.survey--new h1 {
  font-size: 1.65rem;
  letter-spacing: -0.02em;
  color: rgba(10, 20, 45, 0.92);
}

.survey--new .team-name {
  color: rgba(10, 20, 45, 0.75);
  font-weight: 650;
}

.survey--new .disclaimer {
  background: rgba(32, 90, 255, 0.06);
  border-left: 4px solid rgba(32, 90, 255, 0.55);
  border-radius: 12px;
}

.survey--new .question-card {
  position: relative;
  padding: 22px 18px 26px;
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.09);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.94), rgba(246, 249, 255, 0.9));
  box-shadow: 0 18px 48px rgba(10, 20, 45, 0.08);
}

.survey--new .question-text {
  color: rgba(10, 20, 45, 0.9);
}

.survey--new .answer-options button {
  border-radius: 13px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  font-weight: 560;
  text-align: left;
  line-height: 1.38;
  padding: 14px 16px;
  background: rgba(255, 255, 255, 0.94);
  color: rgba(16, 28, 58, 0.92);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.55), 0 8px 20px rgba(10, 20, 45, 0.06);
  animation: optionIn 340ms ease-out;
}

.survey--new .answer-options button:hover {
  transform: translateY(-1px) scale(1.004);
  box-shadow: 0 12px 26px rgba(32, 90, 255, 0.16);
  border-color: rgba(32, 90, 255, 0.35);
  filter: none;
}

.survey--new .answer-options button.selected {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.75)) !important;
  color: #fff !important;
  border-color: rgba(32, 90, 255, 0.45);
  font-weight: 700;
  box-shadow: 0 16px 34px rgba(32, 90, 255, 0.24);
}

.survey--new .answer-options button:nth-child(1) {
  background: linear-gradient(180deg, rgba(255, 239, 243, 0.96), rgba(255, 247, 249, 0.94));
}
.survey--new .answer-options button:nth-child(2) {
  background: linear-gradient(180deg, rgba(255, 248, 225, 0.96), rgba(255, 251, 236, 0.94));
}
.survey--new .answer-options button:nth-child(3) {
  background: linear-gradient(180deg, rgba(239, 244, 255, 0.96), rgba(246, 249, 255, 0.94));
}
.survey--new .answer-options button:nth-child(4) {
  background: linear-gradient(180deg, rgba(232, 246, 255, 0.96), rgba(241, 251, 255, 0.94));
}
.survey--new .answer-options button:nth-child(5) {
  background: linear-gradient(180deg, rgba(234, 252, 237, 0.96), rgba(241, 255, 244, 0.94));
}

.survey--new .tracker-dot.answered {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.85), rgba(0, 194, 255, 0.7));
}

.survey--new .tracker-dot.active {
  border: 2px solid rgba(32, 90, 255, 0.65);
  box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.15);
}

.survey--new .tracker-dot {
  width: 10px;
  height: 10px;
  background: rgba(10, 20, 45, 0.2);
}

.survey--new .team-btn {
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.88), rgba(0, 194, 255, 0.72));
  border: 1px solid rgba(32, 90, 255, 0.25);
  box-shadow: 0 8px 22px rgba(32, 90, 255, 0.18);
}

.survey--new .team-btn:hover {
  filter: brightness(1.06);
  transform: translateY(-2px);
}

.survey--new .team-btn.active {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.92), rgba(16, 185, 129, 0.78));
  border-color: rgba(34, 197, 94, 0.35);
}

.survey--new .modern-button.purple {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
  box-shadow: 0 12px 32px rgba(32, 90, 255, 0.22);
}

.survey--new .modern-button.purple:hover {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.98), rgba(0, 194, 255, 0.9));
  transform: translateY(-2px);
  box-shadow: 0 16px 40px rgba(32, 90, 255, 0.28);
}

.survey--new .modal {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.14);
}

.survey--new {
  position: relative;
  overflow: hidden;
}

.survey--new::before {
  content: "";
  position: absolute;
  inset: -40% -30% auto auto;
  width: 420px;
  height: 420px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(120, 119, 255, 0.18), rgba(0, 194, 255, 0));
  pointer-events: none;
  animation: premiumFloat 12s ease-in-out infinite;
}

.survey--new .question-card {
  animation: cardRise 380ms ease-out;
}

.survey--new .team-btn,
.survey--new .modern-button.purple,
.survey--new .confirm-btn,
.survey--new .cancel-btn,
.survey--new .back-btn {
  position: relative;
  overflow: hidden;
}

.survey--new .team-btn::after,
.survey--new .modern-button.purple::after,
.survey--new .confirm-btn::after,
.survey--new .cancel-btn::after,
.survey--new .back-btn::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 20%, rgba(255, 255, 255, 0.35), transparent 80%);
  transform: translateX(-130%);
  transition: transform 0.6s ease;
}

.survey--new .team-btn:hover::after,
.survey--new .modern-button.purple:hover::after,
.survey--new .confirm-btn:hover::after,
.survey--new .cancel-btn:hover::after,
.survey--new .back-btn:hover::after {
  transform: translateX(130%);
}

.survey--new .team-input {
  border: 1px solid rgba(10, 20, 45, 0.16);
  background: rgba(248, 250, 255, 0.95);
  border-radius: 12px;
}

.survey--new .team-input:focus {
  border-color: rgba(32, 90, 255, 0.55);
  box-shadow: 0 0 0 5px rgba(32, 90, 255, 0.12);
}

.survey--new .modal {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(245, 248, 255, 0.95));
}

.survey--new .back-btn {
  border-radius: 12px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.92);
  padding: 7px 10px;
  cursor: pointer;
  box-shadow: 0 6px 16px rgba(10, 20, 45, 0.08);
}

.survey--new .back-btn:hover {
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.35);
}

.survey--new .team-btn:focus-visible,
.survey--new .answer-options button:focus-visible,
.survey--new .modern-button:focus-visible,
.survey--new .back-btn:focus-visible,
.survey--new .tracker-dot:focus-visible,
.survey--new .team-input:focus-visible {
  outline: 3px solid rgba(32, 90, 255, 0.55);
  outline-offset: 2px;
}

@keyframes premiumFloat {
  0%,
  100% {
    transform: translate3d(0, 0, 0) scale(1);
  }
  50% {
    transform: translate3d(-10px, 12px, 0) scale(1.04);
  }
}

@keyframes cardRise {
  from {
    opacity: 0;
    transform: translateY(8px) scale(0.99);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

@keyframes optionIn {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

</style>
