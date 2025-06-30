<template>
  <div class="p-4">
    <h1 class="text-2xl mb-4">Создать покер-сессию</h1>
    <button @click="createSession" class="px-4 py-2 bg-blue-600 text-white rounded">Создать</button>
    <div v-if="sessionLink" class="mt-4">
      Ссылка для входа: <a :href="sessionLink" class="text-blue-700 underline">{{ sessionLink }}</a>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      sessionLink: ""
    }
  },
  methods: {
    async createSession() {
      const response = await fetch('/dashboard/poker/create', {
        method: 'POST'
      })
      const data = await response.json()
      this.sessionLink = `${window.location.origin}/#/poker/${data.session_id}`
    }
  }
}
</script>
