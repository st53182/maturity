<template>
  <div class="conflict-container">
    <h1>🧠 Разрешение конфликта</h1>

    <div v-if="!aiResponse">
      <div class="step">
        <label>1. Опиши контекст конфликта:</label>
        <textarea
          v-model="context"
          rows="3"
          placeholder="Что произошло? Где и когда случилось? В чём суть конфликта? Какие события предшествовали?"
        />
      </div>

      <div class="step">
        <label>2. Опиши участников конфликта (их поведение, эмоции, реакции):</label>
        <textarea
          v-model="participants"
          rows="3"
          placeholder="Кто участвовал? Как себя вели? Какие эмоции проявляли? Как реагировали друг на друга?"
        />
      </div>

      <div class="step">
        <label>3. Какие действия уже были предприняты и с каким результатом?</label>
        <textarea
          v-model="attempts"
          rows="3"
          placeholder="Что уже пробовали? Кто инициировал? Какие шаги были предприняты? Каков был результат?"
        />
      </div>

      <div class="step">
        <label>4. Какова цель — чего ты хочешь достичь?</label>
        <textarea
          v-model="goal"
          rows="2"
          placeholder="Какой желаемый результат? Чего ты хочешь достичь? Как выглядит идеальное решение?"
        />
      </div>

      <button @click="submitConflict" :disabled="loading">
        {{ loading ? "Обработка..." : "Получить рекомендации" }}
      </button>
    </div>

    <div v-if="aiResponse" class="response-block">
      <h2>📝 Рекомендации</h2>
      <div v-html="aiResponse"></div>
      <button @click="resetForm">Новый запрос</button>
    </div>
  </div>
</template>


<script>
export default {
  data() {
    return {
      context: "",
      participants: "",
      attempts: "",
      goal: "",
      aiResponse: "",
      loading: false
    };
  },
  methods: {
    async submitConflict() {
      this.loading = true;
      try {
        const response = await fetch("/api/conflict/resolve", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            context: this.context,
            participants: this.participants,
            attempts: this.attempts,
            goal: this.goal
          })
        });

        const data = await response.json();
        this.aiResponse = data.response || "Не удалось получить ответ.";
      } catch (error) {
        console.error("❌ Ошибка:", error);
        this.aiResponse = "Произошла ошибка при получении ответа от AI.";
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.context = "";
      this.participants = "";
      this.attempts = "";
      this.goal = "";
      this.aiResponse = "";
    }
  }
};
</script>

<style scoped>
.conflict-container {
  max-width: 800px;
  margin: auto;
  padding: 20px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 0 12px rgba(0,0,0,0.08);
}

.step {
  margin-bottom: 20px;
}

textarea {
  width: 100%;
  padding: 10px;
  border-radius: 8px;
  border: 1px solid #ddd;
  font-size: 14px;
  resize: vertical;
}

button {
  background: #7e57c2;
  color: white;
  padding: 12px 24px;
  border: none;
  font-weight: bold;
  border-radius: 8px;
  cursor: pointer;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.response-block {
  background: #f9f9f9;
  padding: 20px;
  border-radius: 12px;
}
</style>
