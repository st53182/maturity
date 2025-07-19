<template>
  <div class="poker-wrapper">
    <h1 class="poker-title">🃏 {{ $t('poker.title') }} — {{ $t('poker.room') }} {{ roomId }}</h1>

    <!-- 🔹 Вход -->
    <div v-if="!joined" class="card poker-card">
      <input v-model="name" :placeholder="$t('poker.yourName')" class="form-control" />
      <select v-model="role" class="form-control">
        <option disabled value="">{{ $t('poker.selectRole') }}</option>
        <option>FE</option>
        <option>BE</option>
        <option>FullStack</option>
        <option>QA</option>
        <option>Analyst</option>
      </select>
      <button class="btn btn-purple" @click="joinRoom">🚪 {{ $t('poker.join') }}</button>
    </div>

    <!-- 🔹 Комната -->
    <div v-else class="card poker-card">
      <div class="joined-info">👤 <strong>{{ name }}</strong> ({{ role }})</div>

      <!-- 📄 Список задач -->
      <h3>📋 {{ $t('poker.tasks') }}</h3>
      <ul class="story-list">
        <li
          v-for="story in stories"
          :key="story.id"
          :class="{ active: selectedStory && selectedStory.id === story.id }"
          @click="selectStory(story)"
        >
          {{ story.title }}
        </li>
      </ul>

      <!-- ➕ Добавить задачу -->
      <div class="add-story">
        <input
          v-model="newStoryTitle"
          :placeholder="$t('poker.newTaskTitle')"
          class="form-control"
        />
        <textarea
          v-model="newStoryDescription"
          :placeholder="$t('poker.descriptionOptional')"
          class="form-control"
        ></textarea>
        <button class="btn btn-blue" @click="addStory">➕ {{ $t('poker.addTask') }}</button>
      </div>

      <hr />

      <!-- 🃏 Story Points -->
      <div v-if="selectedStory">
        <h2>📌 {{ $t('poker.votingFor') }}: {{ selectedStory.title }}</h2>
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
      </div>

      <!-- 👥 Участники -->
      <div class="participants-box">
        <h3>👥 {{ $t('poker.participants') }}</h3>
        <ul>
          <li v-for="p in participants" :key="p.id">
            <strong>{{ p.name }}</strong> ({{ p.role }}) —
            <span v-if="votesVisible">
              {{ p.voted ? p.points + ' SP' : '— ❌ ' + $t('poker.didNotVote') }}
            </span>
            <span v-else>
              {{ p.voted ? '🔒 ' + $t('poker.voteHidden') : '❌ ' + $t('poker.didNotVote') }}
            </span>
          </li>
        </ul>
        <button
          class="btn btn-purple"
          @click="showVotes"
          v-if="!votesVisible"
        >
          👁 {{ $t('poker.showVotes') }}
        </button>
      </div>
<button class="btn btn-red" @click="leaveRoom">🚪 {{ $t('poker.leaveRoom') }}</button>

      <!-- 💡 Подсказки -->
      <div class="hints-box" v-if="hints.length">
        <h3>💡 {{ $t('poker.hints') }} ({{ $t('poker.rating') }} {{ selectedSP }} SP):</h3>
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
      participants: [],
      votesVisible: false,
      pollingInterval: null,
      // Tasks
      stories: [],
      selectedStory: null,
      newStoryTitle: "",
      newStoryDescription: "",
      hints: []
    };
  },
  mounted() {
  const savedId = localStorage.getItem("planningPokerParticipantId");
  if (savedId) {
    this.participantId = savedId;
    this.joined = true;

    // Load participants and current task
    this.fetchParticipants();
    this.fetchCurrentStory();

    // Start periodic polling
    this.startPolling();
  }
},
  methods: {
    async joinRoom() {
      const res = await fetch(`/api/planning-room/${this.roomId}/join`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: this.name, role: this.role })
      });
      const data = await res.json();
      this.participantId = data.participant_id;
      localStorage.setItem("planningPokerParticipantId", this.participantId);
      this.joined = true;
      this.startPolling();
    },
    async fetchParticipants() {
      const res = await fetch(`/api/planning-room/${this.roomId}/participants`);
      const data = await res.json();
      this.participants = data.participants;
      this.votesVisible = data.show_votes;
    },
    async fetchStories() {
      const res = await fetch(`/api/planning-room/${this.roomId}/stories`);
      const data = await res.json();
      this.stories = data.stories;
    },
    async leaveRoom() {
  if (!confirm(this.$t('poker.confirmLeave'))) return;

  await fetch(`/api/planning-room/${this.roomId}/leave/${this.participantId}`, {
    method: "POST"
  });

  localStorage.removeItem("planningPokerParticipantId");
  this.joined = false;
  this.participantId = null;
  this.selectedStory = null;
  this.participants = [];
  this.stories = [];
  this.stopPolling();
},
    async addStory() {
      if (!this.newStoryTitle) return alert(this.$t('poker.enterTaskTitle'));
      const res = await fetch(`/api/planning-room/${this.roomId}/add-story`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: this.newStoryTitle,
          description: this.newStoryDescription
        })
      });
      const data = await res.json();
      this.stories.push(data);
      this.newStoryTitle = "";
      this.newStoryDescription = "";
    },
    async selectStory(story) {
  this.selectedStory = story;

  // Send current task to server
  await fetch(`/api/planning-room/${this.roomId}/current-story`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ story_id: story.id })
  });
},

    async selectSP(sp) {
      this.selectedSP = sp;
      await fetch(`/api/planning-room/${this.roomId}/vote`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          story_id: this.selectedStory.id,
          story_title: this.selectedStory.title,
          points: this.selectedSP,
          participant_id: this.participantId
        })
      });
      this.fetchParticipants();
      this.fetchHints(sp);
    },
    async fetchHints(sp) {
      const res = await fetch(
        `/api/planning-room/${this.roomId}/hints?sp=${sp}&role=${this.role}`
      );
      const data = await res.json();
      this.hints = data.hints || [];
    },
    async fetchCurrentStory() {
  const res = await fetch(`/api/planning-room/${this.roomId}`);
  if (res.ok) {
    const data = await res.json();
    this.selectedStory = data.current_story; // Update local state
  }
},
    async showVotes() {
      await fetch(`/api/planning-room/${this.roomId}/show-votes`, {
        method: "POST"
      });
    },
    startPolling() {
  this.polling = setInterval(() => {
    this.fetchParticipants();
    this.fetchStories();
    this.fetchCurrentStory(); // Fetch current task
  }, 3000);
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
