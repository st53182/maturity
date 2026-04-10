<template>
  <div class="results-container">
  <!-- 🔹 Общая оценка -->
  <div class="team-info-card">
  <div class="info-block team">
    <h3>🏷️ {{ $t('assessmentResults.team') }}</h3>
    <p>{{ teamName || $t('assessmentResults.defaultTeam') }}</p>
  </div>
  <div class="info-block score" :class="scoreColor">
    <h3>📊 {{ $t('assessmentResults.score') }}</h3>
    <p>{{ averageScore.toFixed(2) }}</p>
  </div>
<div class="info-block level">
  <h3>
    🏅 {{ $t('assessmentResults.level') }}
    <span class="info-icon" @click="showLevelInfo = true" style="cursor: pointer;">ℹ️</span>
  </h3>
  <p>{{ teamLevel }}</p>
</div>

  <div class="info-block market">
  <h3>
    📈 {{ $t('assessmentResults.vsIndustry') }}
    <span class="info-icon" @click="showMarketModal = true">ℹ️</span>
  </h3>
  <p>
    <span :class="compareToMarket >= 0 ? 'better' : 'worse'">
      {{ compareToMarket >= 0 ? '+' : '' }}{{ compareToMarket.toFixed(2) }}%
    </span>
  </p>
  <small v-if="previousAverage !== null" class="previous-diff">
    {{ performanceChangeText }}
  </small>
</div>
</div>

<LevelInfoModal v-if="showLevelInfo" @close="showLevelInfo = false" />
<MarketInfoModal v-if="showMarketModal" @close="showMarketModal = false" />

<div v-if="timelineInfo" class="timeline-modern">
  <div class="timeline-track">
    <!-- 🔸 Заливка прогресса -->
    <div
      class="timeline-fill"
      :style="{ width: getTimelinePosition(todayDate) + '%' }"
    ></div>

    <!-- 📍 Прошлая точка -->
    <div
      class="timeline-dot"
      :style="{ left: getTimelinePosition(timelineInfo.lastDate) + '%' }"
    >
      <div class="tooltip always-visible">
        📍 {{ $t('assessmentResults.timelineLast', { date: timelineInfo.lastDate }) }}
      </div>
    </div>

    <!-- ➤ Сегодняшняя стрелка -->


    <!-- ⏭ Следующая точка -->
    <div
      class="timeline-dot"
      :style="{ left: getTimelinePosition(timelineInfo.nextDate) + '%' }"
    >
      <div class="tooltip always-visible">
        ⏭ {{ $t('assessmentResults.timelineNext', { date: timelineInfo.nextDate }) }}
      </div>
    </div>
  </div>

  <!-- 🧾 Подпись под шкалой -->
  <div class="timeline-days-left">
    ⏳ {{ $t('assessmentResults.daysUntil') }}
    <strong>{{ timelineInfo.daysLeft }} {{ pluralDays(timelineInfo.daysLeft) }}</strong>
  </div>
  <div v-if="previousAssessmentDates.length" class="timeline-previous-dates">
  📅 {{ $t('assessmentResults.previousAssessments') }}
  <strong>{{ previousAssessmentDates.join(', ') }}</strong>
</div>

</div>




    <!-- 🔹 Если пользователь не авторизован, показываем предложение зарегистрироваться -->
    <div v-if="!isAuthenticated" class="auth-notice">
      <p>{{ $t('assessmentResults.authNotice') }}</p>
      <button type="button" @click="goToRegister">🔐 {{ $t('assessmentResults.register') }}</button>
    </div>



    <!-- 🔹 Загрузка / Ошибка -->
    <div v-if="loading" class="loading">⏳ {{ $t('assessmentResults.loading') }}</div>
<div v-else-if="error" class="error">❌ {{ error }}</div>

<!-- 🔹 Графики по категориям -->
<div v-else class="charts-container">
  <RadarChart
  v-for="(data, category) in filteredRadarData"
  :key="`${category}-${currentUiLocale}`"
  :chartData="localizeChartData(data)"
  :title="radarCategoryTitle(category)"
  class="radar-chart"
/>


</div>
<div class="improvement-plan-block">

 <button
  type="button"
  @click="generateImprovementPlan"
  :disabled="loadingPlan"
  class="modern-button"
>
  🤖 {{ $t('assessmentResults.generatePlan') }}
</button>

  <div v-if="loadingPlan">⏳ {{ $t('assessmentResults.generatingPlan') }}</div>

  <div v-if="editablePlan.length" class="plan-editable">
    <ul>
      <li v-for="(item, index) in editablePlan" :key="index">
        <input type="checkbox" v-model="item.done" />
        <textarea
  v-model="item.text"
  class="editable-input"
  :class="{ completed: item.done }"
  rows="5"
  @input="autoResize($event)"
></textarea>
        <button @click="removeStep(index)">❌</button>
      </li>
    </ul>

<div class="plan-buttons">
  <button type="button" class="modern-button blue" @click="addStep">
    ➕ {{ $t('assessmentResults.addStep') }}
  </button>
  <button type="button" class="modern-button green" @click="saveImprovementPlan">
    ✔ {{ $t('assessmentResults.save') }}
  </button>
</div>
  </div>

  <div v-else-if="savedPlan.length">
  <ul class="plan-cards">
    <li
      v-for="(item, index) in savedPlan"
      :key="index"
      class="plan-card"
      @click="handleCardClick($event)"
    >
      <input
        type="checkbox"
        v-model="item.done"
        @change="saveImprovementPlan"
        @click.stop
      />
      <span :class="{ completed: item.done }">{{ item.text }}</span>
    </li>
  </ul>
</div>
</div>
   <div class="recommendations-block">
  <button @click="fetchOpenAIRecommendations" class="modern-button">
    🤖 {{ $t('assessmentResults.getRecommendations') }}
  </button>


  <div v-if="loadingDetailedRecs">⏳ {{ $t('assessmentResults.analyzing') }}</div>

  <div v-if="recommendationsHtml" v-html="recommendationsHtml" class="recommendation-html"></div>
     <button
    v-if="recommendationsHtml"
    @click="saveRecommendations"
    class="modern-button"
  >
    💾 {{ $t('assessmentResults.saveRecommendations') }}
  </button>
</div>
  </div>
</template>

<script>
import axios from "axios";
import RadarChart from "@/components/RadarChart.vue";
import LevelInfoModal from "@/components/LevelInfoModal.vue";
import MarketInfoModal from "@/components/MarketInfoModal.vue";
import enLocale from "@/i18n/locales/en.json";
import i18n from "@/i18n";



export default {
  components: { RadarChart, LevelInfoModal,MarketInfoModal},
  props: ["team_id", "assessment_id"],

  data() {
    return {
      showLevelInfo: false,
      showMarketModal: false,
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
      timelineInfo: null,
      resultsHistory: {},
      hoveredPoint: null,
      teamName: "", // можно получить через props или API
    previousAverage: null, // если сравниваем с прошлым
       loadingPlan: false,
    editablePlan: [],
    savedPlan: [],
    editing: false

    };
  },

  methods: {
  async fetchOpenAIRecommendations() {
  if (!this.savedPlan || this.savedPlan.length === 0) {
    alert(this.$t("assessmentResults.alertNeedPlan"));
    return;
  }

  this.loadingDetailedRecs = true;

  try {
    const response = await axios.post("/openai_recommend", {
      plan: this.savedPlan,
      assessment_id: this.assessmentId
    });

    console.log("📨 Ответ от OpenAI:", response.data.content);
    const htmlFormatted = response.data.content;
    this.recommendationsHtml = `<p>${htmlFormatted}</p>`;
  } catch (error) {
    console.error("❌ Ошибка при получении рекомендаций:", error.response?.data || error);
    alert(this.$t("assessmentResults.alertRecError"));
  } finally {
    this.loadingDetailedRecs = false;
  }
},
    async saveRecommendations() {
  try {
    const token = localStorage.getItem("token");

    if (!token) {
      console.warn("🚫 Нет токена авторизации.");
      alert(this.$t("assessmentResults.alertNotAuth"));
      return;
    }

    await axios.post(
      `/assessment/${this.assessment_id}/recommendations`,
      {
        recommendations: this.recommendationsHtml,
      },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );

    alert(this.$t("assessmentResults.alertRecSaved"));
  } catch (error) {
    console.error("❌ Ошибка сохранения:", error.response?.data || error);
    alert(this.$t("assessmentResults.alertRecSaveFail"));
  }
},

    async generateImprovementPlan() {
  this.loadingPlan = true;
  try {
    const res = await axios.post("/generate_plan", {
      assessment_id: this.assessment_id,
      answer_text: this.prepareFullAnswerSummary()
    });

    const rawSteps = res.data.steps || [];

    // 🔥 Вот здесь магия!
    this.editablePlan = rawSteps.map(step =>
      typeof step === "string" ? { text: step, done: false } : step
    );

    this.editing = true;
  } catch (err) {
    alert(this.$t("assessmentResults.alertPlanGenFail"));
    console.error(err);
  } finally {
    this.loadingPlan = false;
  }
},
  saveImprovementPlan() {
  const token = localStorage.getItem("token");

  const planToSave = this.editing ? this.editablePlan : this.savedPlan;

  axios
    .post(
      `/assessment/${this.assessment_id}/plan`,
      { plan: planToSave },
      { headers: { Authorization: `Bearer ${token}` } }
    )
    .then(() => {
      // 💾 Только в режиме редактирования обновляем savedPlan
      if (this.editing) {
        this.savedPlan = JSON.parse(JSON.stringify(this.editablePlan));
        this.editablePlan = [];
        this.editing = false;
      }

    })
    .catch((err) => {
      console.error("Ошибка сохранения плана", err);
      alert("❌ Не удалось сохранить план");
    });
}
,
  editPlan() {
    this.editablePlan = JSON.parse(JSON.stringify(this.savedPlan));
    this.editing = true;
  },
  addStep() {
    this.editablePlan.push({ text: "", done: false });
  },
  removeStep(index) {
    this.editablePlan.splice(index, 1);
  },
  async fetchSavedPlan() {
    const token = localStorage.getItem("token");
    const res = await axios.get(
      `/assessment/${this.assessment_id}/plan`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    this.savedPlan = res.data.plan || [];
  },

    async fetchSavedRecommendations() {
  try {
    const token = localStorage.getItem("token");
    if (!token) {
      console.warn("🚫 Нет токена авторизации.");
      return;
    }

    const res = await axios.get(
      `/assessment/${this.assessment_id}/recommendations`,
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
      `/team_results_history/${this.team_id}`,
      {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      }
    );

    const history = res.data;
    this.resultsHistory = history;
    console.log("📜 История оценок:", history);

    const sortedDates = Object.keys(history).sort().reverse();


    if (sortedDates.length > 0) {
  this.timelineInfo = this.getNextAssessmentInfo(sortedDates[0]); // <-- Добавь эту строчку
}

if (sortedDates.length >= 2) {
  this.buildCombinedRadarDataByCategory(history);
  this.calculateAverageFromLatestSession(history);
} else if (sortedDates.length === 1) {
  this.prepareRadarData();
} else {
  this.error = this.$t("assessmentResults.errPassFirst");
}

  } catch (error) {
    console.error("❌ Ошибка при получении истории:", error.response?.data || error);
    this.error = this.$t("assessmentResults.errHistory");
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
          ? `/team_results/${this.team_id}`
          : `/temp_results/${this.team_id}`;

        const res = await axios.get(endpoint, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        console.log("✅ Данные загружены:", res.data);
        this.teamName = res.data.team_name;
        this.results = res.data.results;
        this.prepareRadarData();
      } catch (error) {
        console.error("❌ Ошибка загрузки данных:", error.response?.data || error);
        this.error = this.$t("assessmentResults.errLoad");
      } finally {
        this.loading = false;
      }
    },
    autoResize(event) {
  const el = event.target;
  el.style.height = "auto";         // сброс высоты
  el.style.height = el.scrollHeight + "px"; // установить по содержимому
},
handleCardClick(event) {
  const isCheckbox = event.target.tagName === "INPUT";
  if (!isCheckbox) {
    this.editPlan();
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
    getTimelinePosition(date) {
  const start = new Date(this.timelineInfo.lastDate);
  const end = this.timelineInfo.nextDateObject;
  const current = new Date(date);

  const total = end - start;
  const elapsed = current - start;

  const raw = (elapsed / total) * 100;

  // 🔄 Сжимаем расстояние между точками: вместо 0-100% будет 30%-70%
  const compressed = 30 + (raw * 0.4);

  return Math.min(100, Math.max(0, compressed)).toFixed(1);
},

    getNextAssessmentInfo(lastDateStr) {
  const lastDate = new Date(lastDateStr);
  const today = new Date();

  // Добавляем 10 недель
  let nextDate = new Date(lastDate);
  nextDate.setDate(nextDate.getDate() + 70);

  // Если это выходной, переносим на ближайший будний
  while (nextDate.getDay() === 0 || nextDate.getDay() === 6) {
    nextDate.setDate(nextDate.getDate() + 1);
  }

  const daysLeft = Math.ceil((nextDate - today) / (1000 * 60 * 60 * 24));

  return {
    lastDate: lastDate.toLocaleDateString(),
    nextDate: nextDate.toLocaleDateString(),
    daysLeft,
    nextDateObject: nextDate,
  };
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
      label: index === 0 ? this.$t("assessmentResults.radarLatest") : this.$t("assessmentResults.radarPrevious"),
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
      label: index === 0 ? this.$t("assessmentResults.radarLatest") : this.$t("assessmentResults.radarPrevious"),
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
    this.error = this.$t("assessmentResults.errProgress");
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
          label: this.$t("assessmentResults.radarLatest"),
          data: latestData,
          backgroundColor: "rgba(75, 192, 192, 0.2)",
          borderColor: "rgba(75, 192, 192, 1)",
          borderWidth: 2
        },
        {
          label: this.$t("assessmentResults.radarPrevious"),
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

pluralDays(n) {
  const abs = Math.abs(n);
  const loc = typeof this.$i18n.locale === "string" ? this.$i18n.locale : this.$i18n.locale.value;
  if (loc === "en") return abs === 1 ? this.$t("assessmentResults.dayOne") : this.$t("assessmentResults.dayMany");
  if (abs % 10 === 1 && abs % 100 !== 11) return "день";
  if ([2, 3, 4].includes(abs % 10) && ![12, 13, 14].includes(abs % 100)) return "дня";
  return "дней";
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
    },

    isEnglishUI() {
      return String(this.currentUiLocale || "").toLowerCase().startsWith("en");
    },

    resolveRadarLabel(text) {
      if (text == null || text === "") return text;
      if (!this.isEnglishUI()) return text;
      const key = typeof text === "string" ? text.trim() : text;
      const map = this.enRadarLabelsMap;
      const mapped = map[key];
      return mapped !== undefined && mapped !== "" ? mapped : text;
    },

    radarCategoryTitle(category) {
      return this.resolveRadarLabel(category);
    },

    localizeChartData(data) {
      if (!data || !Array.isArray(data.labels)) return data;
      if (!this.isEnglishUI()) return data;
      const tr = (label) => this.resolveRadarLabel(label);
      return {
        ...data,
        labels: data.labels.map(tr),
        datasets: (data.datasets || []).map((ds) => ({
          ...ds,
          label: tr(ds.label),
        })),
      };
    },
  },

  mounted() {
    this.fetchResults();
    this.fetchSavedRecommendations();
    this.fetchResultsHistory();
    this.fetchSavedPlan();
  },
  computed: {
    currentUiLocale() {
      const g = i18n.global.locale;
      const fromGlobal = typeof g === "string" ? g : g?.value;
      if (fromGlobal && String(fromGlobal).length) {
        return String(fromGlobal);
      }
      let stored = null;
      try {
        stored = typeof localStorage !== "undefined" ? localStorage.getItem("language") : null;
      } catch (_e) {
        stored = null;
      }
      if (stored === "en" || stored === "ru") return stored;
      const l = this.$i18n?.locale;
      if (typeof l === "string") return l;
      if (l && typeof l === "object" && "value" in l && l.value) return String(l.value);
      return "ru";
    },
    enRadarLabelsMap() {
      return enLocale.assessmentResults?.radarLabels || {};
    },
    teamLevel() {
    const score = this.averageScore;

    if (score < 2) return this.$t("assessmentResults.levelBeginner");
    if (score < 3) return this.$t("assessmentResults.levelGrowing");
    if (score < 4) return this.$t("assessmentResults.levelProgressing");
    return this.$t("assessmentResults.levelHigh");
  },
    previousAssessmentDates() {
  const dates = Object.keys(this.resultsHistory).sort().reverse();
  return dates.slice(1); // убираем самую последнюю (она уже отображается в точке)
},
  compareToMarket() {
    const marketAvg = 3.75;
    return ((this.averageScore - marketAvg) / marketAvg) * 100;
  },
  performanceChangeText() {
    if (this.previousAverage === null) return "";
    const delta = this.averageScore - this.previousAverage;
    const percent = Math.abs((delta / this.previousAverage) * 100).toFixed(1);
    return delta >= 0
      ? this.$t("assessmentResults.perfUp", { percent })
      : this.$t("assessmentResults.perfDown", { percent });
  },
  scoreColor() {
    const s = this.averageScore;
    if (s < 2) return "danger";
    if (s < 3) return "warning";
    if (s < 4) return "info";
    return "success";
  },
  filteredRadarData() {
    return Object.entries(this.radarData).reduce((acc, [category, chartData]) => {
      if (this.isChartDataValid(chartData)) {
        acc[category] = chartData;
      }
      return acc;
    }, {});
  },
  lastAssessmentDate() {
    const keys = Object.keys(this.resultsHistory);
    if (keys.length === 0) return null;
    return new Date(keys.sort().reverse()[0]); // 🔙 Последняя дата (по ключу)
  },
  todayDate() {
    return new Date();
  },
  recommendedNextAssessmentDate() {
    if (!this.lastAssessmentDate) return null;
    const nextDate = new Date(this.lastAssessmentDate);
    nextDate.setDate(nextDate.getDate() + 14); // 📅 через 2 недели
    return nextDate;
  }
}
};
</script>

<style scoped>

.team-info-card {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  background: linear-gradient(135deg, #3f51b5, #caa6e8);
  border-radius: 12px;
  padding: 16px;
  color: #fff;
  text-align: center;
  gap: 8px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.info-block h3 {
  font-size: 14px;
  margin-bottom: 6px;
  font-weight: 500;
  opacity: 0.85;
}

.info-block p {
  font-size: 18px;
  font-weight: bold;
  margin: 0;
}

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
.team-info-card {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  background: linear-gradient(135deg, #3f51b5, #caa6e8);
  border-radius: 12px;
  padding: 16px;
  color: #fff;
  text-align: center;
  gap: 12px;
  margin-bottom: 20px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  animation: fadeIn 0.4s ease;
}

.info-block {
  padding: 8px;
  border-radius: 8px;
  background-color: rgba(175, 87, 87, 0.08);
  transition: transform 0.2s ease;
}

.info-block:hover {
  transform: scale(1.03);
}

.info-block h3 {
  font-size: 14px;
  margin-bottom: 4px;
  opacity: 0.85;
}

.info-block p {
  font-size: 20px;
  font-weight: bold;
  margin: 0;
}

/* Цвета для оценки */
.score.danger {
  background-color: rgba(220, 53, 69, 0.3);
}
.score.warning {
  background-color: rgba(255, 138, 0, 0.81);
}
.score.info {
  background-color: rgba(23, 162, 184, 0.3);
}
.score.success {
  background-color: rgba(40, 167, 69, 0.3);
}

/* Цвета сравнения с рынком */
.market .better {
  color: #28a745;
}
.market .worse {
  color: #dc3545;
}

.previous-diff {
  display: block;
  font-size: 12px;
  margin-top: 4px;
  opacity: 0.8;
}

.team-info-card .info-block.market h3 {
  color: rgba(13, 23, 51, 0.9);
  opacity: 1;
}

.team-info-card .info-block.market .previous-diff {
  color: rgba(13, 23, 51, 0.78);
  opacity: 1;
}

/* Анимация */
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
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
  background: #f7f8fa;
  border: 2px solid #6e5fbe;
  padding: 20px;
  border-radius: 12px;
}

.timeline-dot:hover .tooltip,
.tooltip:hover {
  transform: translateX(-50%) scale(1.1);
  opacity: 1;
}

.recommendations-block ul {
  text-align: left;
  padding-left: 20px;
}

.timeline-modern {
  position: relative;
  margin: 40px 0;
  height: 80px;
  padding-top: 30px;
}

.timeline-track {
  position: relative;
  background-color: #ddd;
  height: 10px;
  border-radius: 3px;
  top: 30px;
  overflow: visible;
}

.timeline-fill {
  position: absolute;
  height: 100%;
  background-color: #4abebe;
  top: 0;
  left: 0;
  border-radius: 1px;
  z-index: 0; /* самая задняя */
  transition: width 0.4s ease;
}

.timeline-dot {
  position: absolute;
  top: -3px;
  transform: translateX(-50%);
  width: 14px;
  height: 14px;
  background-color: #007bff;
  border-radius: 50%;
  z-index: 2;
}

.timeline-arrow.right {
  position: absolute;
  top: -8px;
  transform: translateX(-50%);
  z-index: 3;
}
.timeline-dot,
.timeline-arrow {
  z-index: 3;
}
.timeline-arrow .arrow {
  font-size: 18px;
  color: #31a35a;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.tooltip {
  position: absolute;
  bottom: 30px;
  left: 50%;
  transform: translateX(-50%) scale(1);
  background: #3497d9;
  color: white;
  padding: 6px 10px;
  border-radius: 6px;
  font-size: 13px;
  white-space: nowrap;
  z-index: 9999;
  transition: transform 0.2s ease, opacity 0.2s ease;
  opacity: 0.95;
}



.timeline-days-left {
  text-align: center;
  margin-top: 38px; /* было 16px — увеличим */
  font-size: 14px;
  color: #444;
  position: relative;
  z-index: 1;
}

.tooltip.always-visible {
  opacity: 1;
  visibility: visible;
}

.recommendations-block li {
  margin-bottom: 10px;
  font-size: 16px;
}

.editable-input {
  width: 100%;
  resize: vertical;
  font-size: 14px;
  padding: 6px 8px;
  border-radius: 5px;
  border: 1px solid #ccc;
  transition: all 0.2s ease;
  font-family: inherit;
  line-height: 1.4;
  background: #fff;
}
.editable-input:focus {
  outline: none;
  border-color: #6699ff;
  box-shadow: 0 0 4px rgba(102, 153, 255, 0.5);
}
.completed {
  text-decoration: line-through;
  opacity: 0.6;
}



.improvement-plan-block {
  margin-top: 20px;
  padding: 20px;
  background: #f9fafc;
  border-radius: 12px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.plan-editable ul,
.improvement-plan-block ul {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 0;
  list-style: none;
  justify-content: center;
}

.plan-editable li,
.improvement-plan-block li {
  flex: 0 0 calc(17% - 7px); /* теперь 5 поместятся */
  max-width: 240px;
  min-width: 140px;

  background: white;
  border-radius: 10px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 1px 6px rgba(0, 0, 0, 0.06);
  position: relative;
  transition: transform 0.2s ease, box-shadow 0.2s ease; /* 🔁 плавность */
}

.plan-editable li:hover,
.improvement-plan-block li:hover {
  transform: scale(1.03);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1;
}

.plan-editable textarea {
  resize: none;
  border: 1px solid #ccc;
  border-radius: 6px;
  padding: 8px;
  font-size: 14px;
  font-family: inherit;
  line-height: 1.4;
  width: 90%;
  overflow: hidden;
  min-height: 170px;
  transition: 0.2s ease;
}

.plan-editable textarea.completed {
  text-decoration: line-through;
  opacity: 0.6;
}

.plan-editable input[type="checkbox"] {
  align-self: flex-start;
  margin-bottom: 8px;
}

.plan-editable button {
  align-self: flex-end;
  background: transparent;
  border: none;
  color: #ffffff;
  font-size: 18px;
  cursor: pointer;
  padding: 4px;
  transition: 0.2s;
}



@media (max-width: 1200px) {
  .plan-editable li,
  .improvement-plan-block li {
    flex: 0 0 calc(33.333% - 16px) !important; /* 3 в ряд */
  }
}

@media (max-width: 800px) {
  .plan-editable li,
  .improvement-plan-block li {
    flex: 0 0 calc(50% - 16px) !important; /* 2 в ряд */
  }
}

@media (max-width: 768px) {
  .charts-container {
    grid-template-columns: 1fr !important;
    gap: 15px !important;
    padding: 15px 10px !important;
  }
  
  .radar-chart {
    width: 100% !important;
    max-width: 320px !important;
    height: 400px !important;
    margin: 0 auto 15px auto !important;
    padding: 12px !important;
  }
  
  .team-info-card {
    grid-template-columns: 1fr !important;
    gap: 15px !important;
    padding: 20px 15px !important;
  }
  
  .info-block {
    padding: 10px !important;
    font-size: 14px !important;
  }
  
  .info-block h3 {
    font-size: 16px !important;
    margin-bottom: 5px !important;
  }
  
  .timeline-modern {
    display: none !important;
  }
  
  .timeline-track {
    height: 8px !important;
    margin: 0 10px !important;
  }
  
  .timeline-dot {
    width: 12px !important;
    height: 12px !important;
  }
  
  .tooltip {
    font-size: 12px !important;
    padding: 4px 8px !important;
    max-width: 200px !important;
    white-space: normal !important;
    word-wrap: break-word !important;
  }
  
  .timeline-previous-dates {
    font-size: 16px !important;
    margin-top: 8px !important;
    line-height: 1.4 !important;
    padding: 0 10px !important;
  }
  
  .timeline-days-left {
    font-size: 16px !important;
    margin-top: 15px !important;
  }
  
  .recommendations-block {
    margin: 20px 10px !important;
    padding: 15px !important;
    width: calc(100% - 20px) !important;
    box-sizing: border-box !important;
    overflow-wrap: break-word !important;
  }
  
  .recommendations-block ul {
    padding-left: 15px !important;
    margin: 0 !important;
  }
  
  .recommendations-block li {
    font-size: 16px !important;
    line-height: 1.5 !important;
    margin-bottom: 12px !important;
    word-wrap: break-word !important;
  }
  
  .improvement-plan-block {
    margin: 20px 10px !important;
    padding: 15px !important;
    width: calc(100% - 20px) !important;
    box-sizing: border-box !important;
  }
  
  .plan-editable ul,
  .improvement-plan-block ul {
    width: 100% !important;
    padding: 0 !important;
    margin: 0 !important;
  }
  
  .plan-editable li,
  .improvement-plan-block li {
    flex: 1 1 100% !important; /* 1 в ряд на мобильных */
    max-width: 100% !important;
    min-width: auto !important;
    margin-bottom: 10px !important;
  }
  
  .plan-editable textarea {
    width: 100% !important;
    font-size: 16px !important;
    box-sizing: border-box !important;
    min-height: 120px !important;
  }
  
  .plan-buttons {
    flex-direction: column !important;
    gap: 10px !important;
    width: 100% !important;
  }
  
  .modern-button {
    width: 100% !important;
    min-width: auto !important;
    font-size: 16px !important;
    padding: 15px 20px !important;
  }
  
  .plan-cards {
    width: 100% !important;
    padding: 0 !important;
  }
  
  .plan-card {
    width: 100% !important;
    margin-bottom: 10px !important;
    padding: 15px !important;
    box-sizing: border-box !important;
  }
}

@media (max-width: 500px) {
  .plan-editable li,
  .improvement-plan-block li {
    flex: 1 1 100% !important; /* 1 в ряд */
  }
}

.modern-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  font-weight: 600;
  padding: 12px 20px;
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  font-size: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center; /* ✅ центрирование по горизонтали */
  text-align: center;       /* ✅ текст по центру */
  gap: 8px;
  width: 95%;
}

.modern-button:hover {
  transform: scale(1.04);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.15);
}

.modern-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.plan-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-top: 12px;
  flex-wrap: wrap;
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


/* 🎨 Цвета */
.modern-button.blue {
  background: linear-gradient(135deg, #3b82f6, #60a5fa);
}

.modern-button.green {
  background: linear-gradient(135deg, #10b981, #34d399);
}
.info-block.level {
  position: relative;
  cursor: help;
}

.level-header {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.level-title {
  display: flex;
  align-items: center;
  gap: 6px;
}

.level-tooltip-container {
  position: relative;
  cursor: help;
}

.level-tooltip-icon {
  font-size: 14px;
  color: #fff;
  background-color: #888;
  border-radius: 50%;
  padding: 2px 6px;
  font-weight: bold;
  line-height: 1;
}

.level-tooltip-text {
  display: none;
  position: absolute;
  top: 28px;
  right: 0;
  background-color: #fff;
  color: #333;
  border: 1px solid #ccc;
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  width: 260px;
  font-size: 13px;
  z-index: 99;
}

.level-tooltip-container:hover + .level-tooltip-text {
  display: block;
}
.info-icon {
  margin-left: 6px;
  cursor: pointer;
  font-size: 14px;
}
.timeline-previous-dates {
  text-align: center;
  margin-top: 4px;
  font-size: 13px;
  color: #555;
}
</style>

