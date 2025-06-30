<template>
  <div class="p-6">
    <div v-if="!hasJoined">
      <h2 class="text-xl mb-2">Введите имя и выберите роль</h2>
      <input v-model="name" placeholder="Ваше имя" class="border p-2 mb-2 w-full" />
      <select v-model="role" class="border p-2 w-full mb-2">
        <option disabled value="">Выберите роль</option>
        <option>FE</option>
        <option>BE</option>
        <option>DB</option>
        <option>Analyst</option>
        <option>FullStack</option>
      </select>
      <button @click="join" class="bg-green-500 text-white px-4 py-2">Присоединиться</button>
    </div>

    <div v-else>
      <h2 class="text-xl mb-4">Сессия: {{ sessionId }}</h2>
      <p>Вы вошли как: <strong>{{ name }} ({{ role }})</strong></p>

      <div class="mt-4">
        <h3 class="text-lg mb-2">Участники:</h3>
        <ul>
          <li v-for="p in participants" :key="p.id">
            {{ p.name }} ({{ p.role }})
            <span v-if="revealed">
              — оценка:
              {{ getEstimate(p.id) !== null ? getEstimate(p.id) : '—' }}
            </span>
          </li>
        </ul>
      </div>

      <div class="mt-6">
        <h3 class="text-lg mb-2">Оценка</h3>
        <button
          v-for="n in [1, 2, 3, 5, 8, 13]"
          :key="n"
          @click="vote(n)"
          class="border px-3 py-1 mr-2 mb-2"
          :disabled="hasVoted || revealed"
        >
          {{ n }}
        </button>
      </div>

      <div class="mt-4">
        <button @click="reveal" class="bg-red-500 text-white px-4 py-2" :disabled="revealed">
          Открыть оценки
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { v4 as uuidv4 } from 'uuid'

export default {
  data() {
    return {
      name: '',
      role: '',
      sessionId: this.$route.params.session_id,
      participantId: localStorage.getItem('poker_participant_id') || uuidv4(),
      hasJoined: false,
      hasVoted: false,
      participants: [],
      estimates: [],
      revealed: false
    }
  },
  sockets: {
    connect() {
      console.log("Connected to socket.io")
    },
    user_joined(data) {
      console.log("Присоединился:", data)
    },
    update_participants(data) {
      this.participants = data
    },
    vote_submitted(data) {
      // можно отследить, кто проголосовал
      console.log("Оценка отправлена от:", data.participant_id)
    },
    estimates_revealed() {
      this.revealed = true
      this.hasVoted = false
      this.fetchEstimates()
    }
  },
  methods: {
    join() {
      this.hasJoined = true
      localStorage.setItem('poker_participant_id', this.participantId)

      this.$socket.emit('join_session', {
        session_id: this.sessionId,
        name: this.name,
        role: this.role
      })
    },
    vote(value) {
      this.$socket.emit('submit_estimate', {
        session_id: this.sessionId,
        story_id: 1, // пока захардкожено
        participant_id: this.participantId,
        value,
        estimate_type: 'points'
      })
      this.hasVoted = true
    },
    reveal() {
      this.$socket.emit('reveal_estimates', {
        session_id: this.sessionId,
        story_id: 1
      })
    },
    async fetchEstimates() {
      const res = await fetch(`/dashboard/poker/1/estimates`) // заменишь 1 на текущий story_id позже
      const data = await res.json()
      this.estimates = data
    },
    getEstimate(participantId) {
      const match = this.estimates.find(e => e.participant_id === participantId)
      return match ? match.value : null
    }
  }
}
</script>

