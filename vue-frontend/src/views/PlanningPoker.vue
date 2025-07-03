<template>
  <div class="poker-wrapper">
    <h1 class="poker-title">🃏 Planning Poker — Комната {{ roomId }}</h1>

    <div v-if="!joined" class="card poker-card">
      <input v-model="name" placeholder="Ваше имя" class="form-control" />
      <select v-model="role" class="form-control">
        <option disabled value="">Выберите роль</option>
        <option>FE</option>
        <option>BE</option>
        <option>FullStack</option>
        <option>QA</option>
        <option>Analyst</option>
      </select>
      <button class="btn btn-purple" @click="joinRoom">🚪 Присоединиться</button>
    </div>

    <div v-else class="card poker-card">
      <div class="joined-info">👤 <strong>{{ name }}</strong> ({{ role }})</div>

      <h2>📌 Выберите Story Point</h2>
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

      <div class="participants-box">
        <h3>👥 Участники</h3>
        <ul>
          <li v-for="p in participants" :key="p.id">
            <strong>{{ p.name }}</strong> ({{ p.role }}) —
            <span v-if="votesVisible">
              {{ p.voted ? p.points + ' SP' : '— ❌ Не голосовал' }}
            </span>
            <span v-else>
              {{ p.voted ? '🔒 Оценка скрыта' : '❌ Не голосовал' }}
            </span>
          </li>
        </ul>

        <button class="btn btn-purple" @click="votesVisible = true" v-if="!votesVisible">
          👁 Показать оценки
        </button>
      </div>

      <div class="hints-box" v-if="hints.length">
        <h3>💡 Подсказки:</h3>
        <ul>
          <li v-for="(hint, i) in hints" :key="i">— {{ hint.story }}</li>
        </ul>
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
      hints: [],
      participants: [],
      votesVisible: false,
      pollingInterval: null
    };
  },
  methods: {
    async joinRoom() {
      if (!this.name || !this.role) return alert("Заполните имя и роль");

      const res = await fetch(`/api/planning-room/${this.roomId}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: this.name, role: this.role })
      });
      const data = await res.json();
      this.participantId = data.participant_id;
      this.joined = true;
      this.startPolling();
    },
    async selectSP(sp) {
      this.selectedSP = sp;
      await fetch(`/api/planning-room/${this.roomId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story: "История без названия",
          points: sp,
          participant_id: this.participantId
        })
      });
      this.fetchParticipants();
      this.fetchHints(sp);
    },
    async fetchParticipants() {
      const res = await fetch(`/api/planning-room/${this.roomId}/participants`);
      const data = await res.json();
      this.participants = data.participants;
    },
    async fetchHints(sp) {
      const res = await fetch(`/api/planning-room/${this.roomId}/hints?sp=${sp}&role=${this.role}`);
      const data = await res.json();
      this.hints = data.hints || [];
    },
    startPolling() {
      this.pollingInterval = setInterval(this.fetchParticipants, 3000);
    },
    stopPolling() {
      clearInterval(this.pollingInterval);
    }
  },
  beforeUnmount() {
  this.stopPolling();
}
};
</script>


<style>

.participants-box {
  margin-top: 30px;
  background: #fefefe;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.poker-wrapper {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px;
}
.poker-title {
  text-align: center;
  color: #4b4f7c;
  margin-bottom: 16px;
}
.card.poker-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  padding: 20px;
}
.form-control {
  display: block;
  width: 100%;
  margin: 10px 0;
  padding: 10px 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 16px;
}
.btn {
  margin-top: 10px;
  padding: 10px 18px;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 15px;
  cursor: pointer;
}
.btn-purple {
  background-color: #6C63FF;
  color: white;
}
.btn-blue {
  background-color: #478eff;
  color: white;
}
.sp-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 16px 0;
}
.sp-btn {
  border: 1px solid #6C63FF;
  padding: 10px 18px;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-weight: bold;
  transition: 0.3s;
}
.sp-btn.selected {
  background: #6C63FF;
  color: white;
}
.hints-box {
  margin-top: 20px;
  background: #f0f4ff;
  border-left: 4px solid #6C63FF;
  padding: 12px;
  border-radius: 8px;
}
</style>
