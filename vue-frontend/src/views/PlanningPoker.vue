<template>
  <div class="poker-container">
    <h1 class="poker-title">🃏 Planning Poker — Комната {{ roomId }}</h1>

    <div v-if="!joined" class="join-form">
      <input v-model="name" placeholder="Ваше имя" class="form-input" />
      <select v-model="role" class="form-input">
        <option disabled value="">Выберите роль</option>
        <option>FE</option>
        <option>BE</option>
        <option>FullStack</option>
        <option>QA</option>
        <option>Analyst</option>
      </select>
      <button class="btn primary" @click="joinRoom">🚪 Присоединиться</button>
    </div>

    <div v-else>
      <div class="joined-info">
        👤 Вы вошли как <strong>{{ name }}</strong> ({{ role }})
      </div>

      <h2>📌 Оцените задачу</h2>
      <div class="sp-buttons">
        <button
          v-for="sp in storyPoints"
          :key="sp"
          @click="selectSP(sp)"
          :class="['sp-btn', { selected: selectedSP === sp }]"
        >
          {{ sp }}
        </button>
      </div>

      <div v-if="selectedSP" class="vote-section">
        <p>✅ Вы выбрали: <strong>{{ selectedSP }} SP</strong></p>
        <button class="btn secondary" @click="submitVote">📨 Отправить голос</button>

        <div v-if="hints.length" class="hints-box">
          <h3>💡 Подсказки по похожим историям:</h3>
          <ul>
            <li v-for="(hint, i) in hints" :key="i">— {{ hint.story }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      roomId: this.$route.params.roomId,
      name: "",
      role: "",
      joined: false,
      participantId: null,
      storyPoints: [1, 2, 3, 5, 8, 13, 21],
      selectedSP: null,
      hints: []
    };
  },
  methods: {
    async joinRoom() {
      if (!this.name || !this.role) {
        alert("Введите имя и роль");
        return;
      }

      const res = await fetch(`/api/planning-room/${this.roomId}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: this.name, role: this.role })
      });
      const data = await res.json();
      this.participantId = data.participant_id;
      this.joined = true;
    },
    selectSP(sp) {
      this.selectedSP = sp;
      this.fetchHints(sp);
    },
    async fetchHints(sp) {
      const res = await fetch(
        `/api/planning-room/${this.roomId}/hints?sp=${sp}&role=${this.role}`
      );
      const data = await res.json();
      this.hints = data.hints || [];
    },
    async submitVote() {
      await fetch(`/api/planning-room/${this.roomId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story: "История без названия",
          points: this.selectedSP,
          participant_id: this.participantId
        })
      });
      alert("Голос учтён!");
    }
  }
};
</script>

<style scoped>
.poker-container {
  max-width: 600px;
  margin: auto;
  padding: 20px;
}
.poker-title {
  text-align: center;
  margin-bottom: 20px;
}
.join-form {
  display: flex;
  flex-direction: column;
}
.form-input {
  padding: 10px;
  margin: 8px 0;
  font-size: 16px;
}
.btn {
  padding: 10px;
  margin-top: 10px;
  cursor: pointer;
}
.primary {
  background-color: #2e7d32;
  color: white;
}
.secondary {
  background-color: #1976d2;
  color: white;
}
.sp-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 16px 0;
}
.sp-btn {
  padding: 10px 16px;
  font-size: 16px;
  cursor: pointer;
}
.selected {
  background-color: #ffb300;
  color: #000;
}
.vote-section {
  margin-top: 20px;
}
.hints-box {
  margin-top: 15px;
  background: #f1f8e9;
  padding: 10px;
  border-left: 4px solid #8bc34a;
}
</style>
