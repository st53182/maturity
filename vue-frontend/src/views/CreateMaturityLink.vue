<template>
  <div class="create-maturity">
    <h1>{{ $t('maturity.createLinkTitle') }}</h1>
    <div v-if="!createdUrl" class="form-block">
      <label>{{ $t('maturity.teamNameOptional') }}</label>
      <input v-model="teamName" type="text" class="team-input" :placeholder="$t('survey.teamName')" />
      <button type="button" class="btn-create" :disabled="creating" @click="createLink">
        {{ creating ? '...' : $t('maturity.create') }}
      </button>
    </div>
    <div v-else class="result-block">
      <p class="success-msg">{{ $t('maturity.linkCreated') }}</p>
      <div class="url-row">
        <input :value="createdUrl" readonly class="url-input" />
        <button type="button" class="btn-copy" @click="copyLink">{{ $t('maturity.copyLink') }}</button>
      </div>
      <router-link :to="`${maturityPathPrefix}/${token}`" class="btn-start">{{ $t('maturity.startAssessment') }}</router-link>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'CreateMaturityLink',
  computed: {
    maturityPathPrefix() {
      return (this.$route.path || '').startsWith('/new') ? '/new/maturity' : '/maturity';
    },
  },
  data() {
    return {
      teamName: '',
      creating: false,
      token: '',
      createdUrl: ''
    };
  },
  methods: {
    async createLink() {
      if (this.creating) return;
      this.creating = true;
      try {
        const res = await axios.post('/api/maturity-link', { team_name: this.teamName || null }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        this.token = res.data.token;
        const base = window.location.origin;
        this.createdUrl = `${base}${this.maturityPathPrefix}/${this.token}`;
      } catch (e) {
        alert(e.response?.data?.error || 'Ошибка создания ссылки');
      } finally {
        this.creating = false;
      }
    },
    copyLink() {
      navigator.clipboard.writeText(this.createdUrl).then(() => {
        alert(this.$t('maturity.copyLink') + ' — скопировано');
      }).catch(() => {});
    }
  }
};
</script>

<style scoped>
.create-maturity {
  max-width: 560px;
  margin: 2rem auto;
  padding: 1.5rem;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

.create-maturity h1 { font-size: 1.5rem; margin-bottom: 1.5rem; }

.form-block label { display: block; margin-bottom: 0.5rem; color: #374151; }
.team-input {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  margin-bottom: 1rem;
  box-sizing: border-box;
}
.btn-create {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}
.btn-create:disabled { opacity: 0.6; cursor: not-allowed; }

.result-block .success-msg { color: #059669; margin-bottom: 1rem; }
.url-row { display: flex; gap: 0.5rem; margin-bottom: 1rem; }
.url-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 0.9rem;
}
.btn-copy {
  padding: 0.75rem 1rem;
  background: #6b7280;
  color: #fff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
}
.btn-start {
  display: inline-block;
  padding: 0.75rem 1.5rem;
  background: #10b981;
  color: #fff;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
}
</style>
