<template>
  <div class="create-maturity" :class="{ 'create-maturity--new': isNewUi }">
    <h1>{{ $t('maturity.createLinkTitle') }}</h1>
    <div v-if="!createdUrl" class="form-block">
      <label>{{ $t('maturity.teamNameOptional') }}</label>
      <input v-model="teamName" type="text" class="team-input" :placeholder="$t('survey.teamName')" />
      <label>{{ $t('maturity.streamGroupOptional') }}</label>
      <input v-model="groupName" type="text" class="team-input" :placeholder="$t('maturity.streamGroupPlaceholder')" />
      <button type="button" class="btn-create" :disabled="creating" @click="createLink">
        {{ creating ? $t('maturity.creatingShort') : $t('maturity.create') }}
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
    isNewUi() {
      return (this.$route.path || '').startsWith('/new');
    },
  },
  data() {
    return {
      teamName: '',
      groupName: '',
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
        const res = await axios.post('/api/maturity-link', {
          team_name: this.teamName || null,
          group_name: this.groupName || null
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
        });
        this.token = res.data.token;
        const base = window.location.origin;
        this.createdUrl = `${base}${this.maturityPathPrefix}/${this.token}`;
      } catch (e) {
        alert(e.response?.data?.error || this.$t('maturity.linkCreateError'));
      } finally {
        this.creating = false;
      }
    },
    copyLink() {
      navigator.clipboard.writeText(this.createdUrl).then(() => {
        alert(this.$t('maturity.copyLink') + ' — ' + this.$t('maturity.copyLinkDone'));
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

/* Premium style for /new/maturity */
.create-maturity--new {
  max-width: 680px;
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.95), rgba(247, 250, 255, 0.9));
  box-shadow: 0 26px 70px rgba(10, 20, 45, 0.12);
  position: relative;
  overflow: hidden;
  animation: revealUp 420ms ease-out;
}

.create-maturity--new::before {
  content: "";
  position: absolute;
  top: -120%;
  left: -20%;
  width: 34%;
  height: 320%;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.38), transparent);
  transform: rotate(14deg);
  animation: shineTravel 8.5s linear infinite;
  pointer-events: none;
}

.create-maturity--new h1 {
  font-size: 1.75rem;
  letter-spacing: -0.02em;
  color: rgba(10, 20, 45, 0.94);
}

.create-maturity--new .team-input,
.create-maturity--new .url-input {
  border-radius: 12px;
  border-color: rgba(10, 20, 45, 0.14);
  background: rgba(248, 250, 255, 0.96);
}

.create-maturity--new .team-input:focus,
.create-maturity--new .url-input:focus {
  outline: none;
  border-color: rgba(32, 90, 255, 0.58);
  box-shadow: 0 0 0 5px rgba(32, 90, 255, 0.12);
}

.create-maturity--new .btn-create,
.create-maturity--new .btn-copy,
.create-maturity--new .btn-start {
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  box-shadow: 0 10px 26px rgba(10, 20, 45, 0.12);
}

.create-maturity--new .btn-create {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.94), rgba(0, 194, 255, 0.84));
}

.create-maturity--new .btn-start {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.94), rgba(16, 185, 129, 0.84));
}

.create-maturity--new .btn-copy {
  background: linear-gradient(135deg, rgba(71, 85, 105, 0.92), rgba(100, 116, 139, 0.85));
}

.create-maturity--new .btn-create::after,
.create-maturity--new .btn-copy::after,
.create-maturity--new .btn-start::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 20%, rgba(255, 255, 255, 0.34), transparent 80%);
  transform: translateX(-125%);
  transition: transform 0.6s ease;
}

.create-maturity--new .btn-create:hover::after,
.create-maturity--new .btn-copy:hover::after,
.create-maturity--new .btn-start:hover::after {
  transform: translateX(125%);
}

@keyframes revealUp {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes shineTravel {
  0% {
    transform: translateX(-240px) rotate(14deg);
  }
  45%,
  100% {
    transform: translateX(920px) rotate(14deg);
  }
}
</style>
