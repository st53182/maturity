<template>
  <div>
    <h1>Planning Poker</h1>
    <div v-if="!joined">
      <input v-model="name" placeholder="Ваше имя" />
      <select v-model="role">
        <option>FE</option>
        <option>BE</option>
        <option>FullStack</option>
        <option>QA</option>
        <option>Analyst</option>
      </select>
      <button @click="joinRoom">Присоединиться</button>
    </div>
    <div v-else>
      <!-- Компонент оценивания задач -->
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      name: '',
      role: '',
      joined: false
    };
  },
  methods: {
    joinRoom() {
      fetch(`/api/planning-room/${this.$route.params.roomId}/join`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ name: this.name, role: this.role })
      }).then(() => this.joined = true);
    }
  }
};
</script>
