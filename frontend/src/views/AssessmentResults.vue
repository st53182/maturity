<template>
  <div class="results-container">
    <h1>📊 Результаты оценки команды</h1>

    <!-- 🔹 Если пользователь не авторизован, показываем предложение зарегистрироваться -->
    <div v-if="!isAuthenticated" class="auth-notice">
      <p>Ваши результаты не сохранены. Зарегистрируйтесь, чтобы сохранить их!</p>
      <button @click="goToRegister">🔐 Зарегистрироваться</button>
    </div>

    <!-- 🔹 Общая оценка -->
    <div class="team-score-card">
      <h2>Средняя оценка</h2>
      <p class="score">{{ averageScore.toFixed(2) }}</p>
    </div>

    <!-- 🔹 Загрузка / Ошибка -->
    <div v-if="loading" class="loading">⏳ Загрузка данных...</div>
<div v-else-if="error" class="error">❌ {{ error }}</div>

<!-- 🔹 Графики по категориям -->
<div v-else class="charts-container">
  <RadarChart
  v-for="(data, category) in filteredRadarData"
  :key="category"
  :chartData="data"
  :title="category"
  class="radar-chart"
/>
</div>
   <div class="recommendations-block">
  <button @click="fetchOpenAIRecommendations" class="submit-btn">
    🤖 Получить персональные рекомендации
  </button>
     <button
    v-if="recommendationsHtml"
    @click="saveRecommendations"
    class="submit-btn"
  >
    💾 Сохранить рекомендации
  </button>

  <div v-if="loadingDetailedRecs">⏳ Анализируем ответы...</div>

  <div v-if="recommendationsHtml" v-html="recommendationsHtml" class="recommendation-html"></div>
</div>
  </div>
</template>

<script>
import axios from "axios";
import RadarChart from "@/components/RadarChart.vue";

export default {
  components: { RadarChart },
  props: ["team_id", "assessment_id"],

  data() {
    return {
      results: {},
      radarData: {},
      loading: true,
      error: null,
      averageScore: 0,
      isAuthenticated: false, // Проверка авторизации
      recommendationsDetailed: [],
      loadingDetailedRecs: false,
      recommendationsHtml: "",
      chartInstance: null,
      isUnmounted: false, // 🔒 добавляем
    };
  },

  methods: {
    async fetchOpenAIRecommendations() {
  this.loadingDetailedRecs = true;
  try {
    const response = await axios.post("http://127.0.0.1:5000/openai_recommend", {
      answer_text: this.prepareFullAnswerSummary(),
      assessment_id: this.assessmentId
    });

    console.log("🔍 Ответ от OpenAI:", response.data.content);

    // Обернём текст в HTML (например, заменим \n на <br>)
    const htmlFormatted = response.data.content

    this.recommendationsHtml = `<p>${htmlFormatted}</p>`;
  } catch (error) {
    console.error("❌ Ошибка при получении рекомендаций:", error.response?.data || error);
    alert("Ошибка при запросе рекомендаций.");
  } finally {
    this.loadingDetailedRecs = false;
  }
},
    async saveRecommendations() {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      console.warn("🚫 Нет токена авторизации.");
      alert("Вы не авторизованы!");
      return;
    }

    await axios.post(
      `http://127.0.0.1:5000/assessment/${this.assessment_id}/recommendations`,
      {
        recommendations: this.recommendationsHtml,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    alert("✅ Рекомендации успешно сохранены!");
  } catch (error) {
    console.error("❌ Ошибка сохранения:", error.response?.data || error);
    alert("❌ Не удалось сохранить рекомендации.");
  }
},

    async fetchSavedRecommendations() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.warn("🚫 Нет токена авторизации.");
      return;
    }

    const res = await axios.get(
      `http://127.0.0.1:5000/assessment/${this.assessment_id}/recommendations`,
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );

    if (res.data && res.data.recommendations) {
      this.recommendationsHtml = `<p>${res.data.recommendations}</p>`;
      console.log("📥 Подгружены сохранённые рекомендации");
    } else {
      console.log("ℹ️ Нет сохранённых рекомендаций");
    }
  } catch (error) {
    console.error("❌ Ошибка при загрузке рекомендаций:", error.response?.data || error);
  }
},
async fetchResultsHistory() {
  try {
    const token = localStorage.getItem("token");

    const res = await axios.get(
      `http://127.0.0.1:5000/team_results_history/${this.team_id}`,
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

    async fetchResults() {
      try {
        console.log(`📡 Загружаем результаты для команды ID ${this.team_id}`);
        const token = localStorage.getItem("token");

        if (token) {
          this.isAuthenticated = true; // Пользователь залогинен
        } else {
          this.isAuthenticated = false; // Гость
        }

        // Если пользователь не авторизован, загружаем временные данные
        const endpoint = token
          ? `http://127.0.0.1:5000/team_results/${this.team_id}`
          : `http://127.0.0.1:5000/temp_results/${this.team_id}`;

        const res = await axios.get(endpoint, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        console.log("✅ Данные загружены:", res.data);
        this.results = res.data;
        this.prepareRadarData();
      } catch (error) {
        console.error("❌ Ошибка загрузки данных:", error.response?.data || error);
        this.error = "Ошибка загрузки данных.";
      } finally {
        this.loading = false;
      }
    },

   isChartDataValid(chartData) {
  return (
    chartData &&
    Array.isArray(chartData.labels) &&
    chartData.labels.length > 0 &&
    Array.isArray(chartData.datasets) &&
    chartData.datasets.length > 0
  );
},

calculateAverageFromLatestSession(history) {
  const sortedDates = Object.keys(history).sort().reverse();
  const latestSession = history[sortedDates[0]];

  if (!latestSession) {
    console.warn("⚠️ Нет данных для последней сессии.");
    this.averageScore = 0;
    return;
  }

  let total = 0;
  let count = 0;

  for (const categoryData of Object.values(latestSession)) {
    for (const score of Object.values(categoryData)) {
      total += score;
      count++;
    }
  }

  this.averageScore = count > 0 ? total / count : 0;
},
    processHistoryRadarData(history) {
  const sortedDates = Object.keys(history).sort().reverse(); // Последняя оценка — первая

  if (sortedDates.length === 0) return;

  const allLabels = new Set();
  const datasets = [];

  sortedDates.slice(0, 2).forEach((date, index) => {
    const session = history[date];
    const dataMap = {};

    for (const [category, subcats] of Object.entries(session)) {
      for (const [subcategory, score] of Object.entries(subcats)) {
        const label = `${category} - ${subcategory}`;
        dataMap[label] = score;
        allLabels.add(label);
      }
    }

    const dataset = {
      label: index === 0 ? "🟢 Последняя оценка" : "🟡 Предыдущая оценка",
      data: [],
      backgroundColor: index === 0 ? "rgba(75, 192, 192, 0.2)" : "rgba(255, 206, 86, 0.2)",
      borderColor: index === 0 ? "rgba(75, 192, 192, 1)" : "rgba(255, 206, 86, 1)",
      borderWidth: 2,
    };

    allLabels.forEach(label => {
      dataset.data.push(dataMap[label] || 0); // если подкатегория отсутствует в этой сессии — 0
    });

    datasets.push(dataset);
  });

  this.radarData = {
    labels: Array.from(allLabels),
    datasets,
  };
},
    buildCombinedRadarData(latestResults, history) {
  const sortedDates = Object.keys(history).sort().reverse(); // самые свежие сначала
  const allLabels = new Set();
  const labelToScoreMap = {};

  // 🔹 Обрабатываем последние 2 измерения (в том числе текущее)
  sortedDates.slice(0, 2).forEach(date => {
  const session = history[date];
  const dataMap = {};

  for (const [category, subcats] of Object.entries(session)) {
    for (const [subcategory, score] of Object.entries(subcats)) {
      const label = `${category} - ${subcategory}`;
      dataMap[label] = score;
      allLabels.add(label);
    }
  }

  labelToScoreMap[date] = dataMap;
});

  const labels = Array.from(allLabels);
  const datasets = [];

  sortedDates.slice(0, 2).forEach((date, index) => {
    const dataMap = labelToScoreMap[date];
    const dataset = {
      label: index === 0 ? "🟢 Последняя оценка" : "🟡 Предыдущая оценка",
      data: labels.map(label => dataMap[label] || 0),
      backgroundColor: index === 0 ? "rgba(75, 192, 192, 0.2)" : "rgba(255, 206, 86, 0.2)",
      borderColor: index === 0 ? "rgba(75, 192, 192, 1)" : "rgba(255, 206, 86, 1)",
      borderWidth: 2,
    };
    datasets.push(dataset);
  });

  this.radarData = { labels, datasets };
},
buildCombinedRadarDataByCategory(history) {
  const sortedDates = Object.keys(history).sort().reverse();
  if (sortedDates.length === 0) {
    this.error = "Недостаточно данных для отображения прогресса. Пройдите хотя бы одну оценку.";
    return;
  }

  const latestSession = history[sortedDates[0]];
  const previousSession = sortedDates[1] ? history[sortedDates[1]] : null;

  const radarDataByCategory = {};

  // Проходим по категориям последней оценки
  for (const [category, subcats] of Object.entries(latestSession)) {
    const labels = Object.keys(subcats);

    const latestData = labels.map(label => latestSession[category][label] || 0);
    const previousData = labels.map(label => previousSession?.[category]?.[label] || 0);

    radarDataByCategory[category] = {
      labels,
      datasets: [
        {
          label: "🟢 Последняя оценка",
          data: latestData,
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 2
        },
        {
          label: "🟡 Предыдущая оценка",
          data: previousData,
          backgroundColor: "rgba(255, 206, 86, 0.2)",
          borderColor: "rgba(255, 206, 86, 1)",
          borderWidth: 2
        }
      ]
    };
  }

  this.radarData = radarDataByCategory;
},


    prepareRadarData() {
      let totalScore = 0;
      let categoryCount = 0;

      this.radarData = Object.entries(this.results).reduce((acc, [category, scores]) => {
        if (!scores || Object.keys(scores).length === 0) {
          console.warn(`⚠️ Категория "${category}" пуста, пропускаем.`);
          return acc;
        }

        console.log(`📌 Формируем данные для категории: ${category}`);

        const scoresArray = Object.values(scores).map(value => parseFloat(value) || 0);
        const categoryAverage = scoresArray.reduce((sum, val) => sum + val, 0) / scoresArray.length;

        totalScore += categoryAverage;
        categoryCount++;

        acc[category] = {
          labels: Object.keys(scores),
          datasets: [
            {
              label: category,
              data: scoresArray,
              backgroundColor: "rgba(75, 192, 192, 0.2)",
              borderColor: "rgba(75, 192, 192, 1)",
              borderWidth: 2
            }
          ]
        };
        return acc;
      }, {});

      this.averageScore = categoryCount > 0 ? totalScore / categoryCount : 0;

      console.log("📊 Итоговые данные для диаграмм:", JSON.stringify(this.radarData, null, 2));
    },
    prepareFullAnswerSummary() {
  let summary = "";
  for (const [category, questions] of Object.entries(this.results)) {
    summary += `📌 Категория: ${category}\n`;
    for (const [question, answer] of Object.entries(questions)) {
      summary += ` - ${question}: ${answer}\n`;
    }
    summary += "\n";
  }
  return summary;
  },

    goToRegister() {
      this.$router.push({ name: "Register" });
    }
  },

  mounted() {
    this.fetchResults();
    this.fetchSavedRecommendations();
    this.fetchResultsHistory();



  },
  computed: {
  filteredRadarData() {
    return Object.entries(this.radarData).reduce((acc, [category, chartData]) => {
      if (this.isChartDataValid(chartData)) {
        acc[category] = chartData;
      }
      return acc;
    }, {});
  }
},
};
</script>

<style scoped>
/* 🔹 Общий контейнер */
.results-container {
  max-width: 1300px;
  margin: auto;
  text-align: center;
  padding: 30px;
  background: #f4f6f9;
  font-family: 'Arial', sans-serif;
}

/* 🔹 Заголовок */
h1 {
  font-size: 30px;
  color: #2c3e50;
  font-weight: bold;
}

/* 🔹 Переключатель команд */
.team-switcher {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
}

.switch-btn {
  font-size: 22px;
  padding: 8px 12px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin: 0 10px;
  transition: 0.2s;
}

.switch-btn:hover {
  background: #2980b9;
}

.team-name-container h2 {
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
}

/* 🔹 Карточка общей оценки */
.team-score-card {
  background: linear-gradient(135deg, #33469e, #fad0c4);
  padding: 5px;
  border-radius: 5px;
  color: white;
  text-align: center;
  margin-bottom: 5px;
}

.team-score-card h2 {
  font-size: 22px;
}

.team-score-card .score {
  font-size: 36px;
  font-weight: bold;
  margin-top: 10px;
}

/* 🔹 Графики */
.charts-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 30px;
  justify-content: center;
  padding: 20px;
}

.radar-chart {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 380px;
  height: 430px;
  background: white;
  border-radius: 15px;
  padding: 15px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
}
.recommendations-block {
  margin-top: 30px;
  background: #f0f9ff;
  border: 2px solid #4caf50;
  padding: 20px;
  border-radius: 12px;
}

.recommendations-block ul {
  text-align: left;
  padding-left: 20px;
}

.recommendations-block li {
  margin-bottom: 10px;
  font-size: 16px;
}

@media (max-width: 992px) {
  .charts-container {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
}
</style>

