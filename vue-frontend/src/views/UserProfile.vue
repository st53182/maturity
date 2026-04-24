<template>
  <div class="profile-page">
    <h1>{{ $t('profile.title') }}</h1>

    <form @submit.prevent="saveProfile" class="profile-form">
      <div class="form-section">
        <h2>{{ $t('profile.generalInfo') }}</h2>

        <label>{{ $t('profile.username') }}</label>
        <input v-model="profile.name" :placeholder="$t('profile.username')" />

        <label>{{ $t('motivation.role') }}</label>
        <input v-model="profile.position" :placeholder="$t('motivation.role')" />

        <label>{{ $t('common.company') }}</label>
        <input v-model="profile.company" :placeholder="$t('common.company')" />

        <label>{{ $t('disc.personalityType') }}</label>
        <input v-model="profile.personality_type" :placeholder="$t('disc.personalityType')" readonly />
        <small style="color: #666; font-size: 12px;">{{ $t('profile.autoDetected') }}</small>
      </div>

      <hr />

      <div class="form-section">
        <h2>{{ $t('profile.changeCredentials') }}</h2>

        <label>{{ $t('profile.email') }}</label>
        <input v-model="profile.email" type="email" />

        <label>{{ $t('profile.oldPassword') }}</label>
        <input v-model="oldPassword" type="password" />

        <label>{{ $t('profile.newPassword') }}</label>
        <input v-model="newPassword" type="password" />
      </div>

      <button type="submit" class="modern-button purple">{{ $t('profile.saveChanges') }}</button>
    </form>

    <div class="form-section jwt-section">
      <div class="jwt-head">
        <div>
          <h2>{{ $t('profile.jwtTitle') }}</h2>
          <p class="muted jwt-hint">{{ $t('profile.jwtHint') }}</p>
        </div>
        <div class="jwt-meta">
          <span v-if="jwtExpired" class="jwt-badge jwt-badge--danger">{{ $t('profile.jwtExpired') }}</span>
          <span v-else-if="jwtExpiresInDays !== null" class="jwt-badge">
            {{ $t('profile.jwtValidFor', { days: jwtExpiresInDays }) }}
          </span>
        </div>
      </div>

      <div v-if="jwtToken" class="jwt-box" :class="{ 'jwt-box--warn': jwtExpired }">
        <code class="jwt-value">{{ jwtVisible ? jwtToken : maskedJwt }}</code>
        <div class="jwt-actions">
          <button type="button" class="jwt-btn" @click="jwtVisible = !jwtVisible">
            {{ jwtVisible ? $t('profile.jwtHide') : $t('profile.jwtShow') }}
          </button>
          <button type="button" class="jwt-btn jwt-btn--primary" @click="copyJwt">
            {{ jwtCopied ? $t('profile.jwtCopied') : $t('profile.jwtCopy') }}
          </button>
        </div>
      </div>
      <p v-else class="muted">{{ $t('profile.jwtMissing') }}</p>

      <div v-if="jwtPayload" class="jwt-details">
        <div><span class="jwt-details__k">sub</span><span class="jwt-details__v">{{ jwtPayload.sub }}</span></div>
        <div v-if="jwtIssuedAt"><span class="jwt-details__k">iat</span><span class="jwt-details__v">{{ formatDateTime(jwtIssuedAt) }}</span></div>
        <div v-if="jwtExpiresAt"><span class="jwt-details__k">exp</span><span class="jwt-details__v">{{ formatDateTime(jwtExpiresAt) }}</span></div>
      </div>
    </div>

    <div class="form-section invite-section">
      <h2>Пригласить пользователя</h2>
      <label>Email приглашённого (необязательно; для кода на несколько человек оставьте пустым)</label>
      <input v-model="inviteeEmail" type="email" placeholder="name@company.com" />
      <label>Сколько раз можно использовать код (1 = один человек, до 100)</label>
      <input v-model.number="maxInviteUses" type="number" min="1" max="100" class="invite-max-uses" />
      <button type="button" class="modern-button purple" :disabled="inviteLoading" @click="createInvite">
        {{ inviteLoading ? 'Создание…' : 'Создать инвайт' }}
      </button>
      <p v-if="newInviteCode" class="invite-code"><strong>Код:</strong> {{ newInviteCode }}</p>
      <div v-if="myInvites.length" class="invite-list">
        <div v-for="inv in myInvites" :key="inv.id" class="invite-item">
          <div><strong>{{ inv.code }}</strong></div>
          <div class="muted">
            {{ inv.invitee_email || 'любой email' }} · {{ inv.status }}
            <span v-if="(inv.max_uses || 1) > 1">
              · использовано {{ inv.use_count || 0 }} / {{ inv.max_uses || 1 }}
              (осталось {{ inv.uses_remaining != null ? inv.uses_remaining : Math.max(0, (inv.max_uses || 1) - (inv.use_count || 0)) }})
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="disc-section">
      <h2>{{ $t('profile.discSection') }}</h2>
      <p>{{ $t('profile.discDescription') }}</p>
      
      <div class="disc-actions">
        <router-link to="/new/disc-assessment" class="modern-button purple">
          {{ profile.personality_type ? $t('profile.retakeAssessment') : $t('profile.takeAssessment') }}
        </router-link>
        <div v-if="assessmentHistory.length > 0" class="history-summary">
          <h4>{{ $t('profile.completionHistory') }} ({{ assessmentHistory.length }})</h4>
          <div class="history-list">
            <div v-for="assessment in assessmentHistory.slice(0, 5)" :key="assessment.id" class="history-item">
              <div class="history-header">
                <span class="history-type">{{ assessment.personality_type }}</span>
                <span class="history-date">{{ formatDate(assessment.completed_at) }}</span>
                <button @click="toggleRecommendations(assessment.id)" class="toggle-btn">
                  {{ expandedAssessments.includes(assessment.id) ? '▼' : '▶' }} {{ $t('profile.recommendations') }}
                </button>
              </div>
              <div v-if="expandedAssessments.includes(assessment.id)" class="recommendations-preview">
                <div class="recommendations-content" v-html="formatRecommendations(assessment.recommendations)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="latestAssessment" class="latest-result">
        <h3>{{ $t('profile.latestResult') }}</h3>
        <div class="result-summary">
          <div class="personality-badge">{{ latestAssessment.personality_type }}</div>
          <div class="scores">
            <span>D: {{ latestAssessment.dominance_score }}</span>
            <span>I: {{ latestAssessment.influence_score }}</span>
            <span>S: {{ latestAssessment.steadiness_score }}</span>
            <span>C: {{ latestAssessment.conscientiousness_score }}</span>
          </div>
          <div class="assessment-date">{{ formatDate(latestAssessment.completed_at) }}</div>
        </div>
      </div>
    </div>

    <p class="app-version">Growboard · {{ appVersion }}</p>
  </div>
</template>
<script>
import axios from "axios";

const APP_VERSION = '1.0';

export default {
  name: "UserProfile",
  data() {
    return {
      appVersion: APP_VERSION,
      profile: {
        name: "",
        position: "",
        company: "",
        personality_type: "",
        email: ""
      },
      oldPassword: "",
      newPassword: "",
      assessmentHistory: [],
      latestAssessment: null,
      expandedAssessments: [],
      inviteeEmail: '',
      maxInviteUses: 1,
      newInviteCode: '',
      myInvites: [],
      inviteLoading: false,
      jwtVisible: false,
      jwtCopied: false
    };
  },
  computed: {
    jwtToken() {
      if (typeof localStorage === 'undefined') return '';
      return localStorage.getItem('token') || '';
    },
    maskedJwt() {
      const t = this.jwtToken;
      if (!t) return '';
      if (t.length <= 24) return '•'.repeat(t.length);
      return `${t.slice(0, 12)}${'•'.repeat(24)}${t.slice(-8)}`;
    },
    jwtPayload() {
      const t = this.jwtToken;
      if (!t) return null;
      const parts = t.split('.');
      if (parts.length < 2) return null;
      try {
        const b64 = parts[1].replace(/-/g, '+').replace(/_/g, '/');
        const padded = b64 + '==='.slice((b64.length + 3) % 4);
        const json = decodeURIComponent(
          atob(padded)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join(''),
        );
        return JSON.parse(json);
      } catch (e) {
        return null;
      }
    },
    jwtIssuedAt() {
      const p = this.jwtPayload;
      return p && typeof p.iat === 'number' ? new Date(p.iat * 1000) : null;
    },
    jwtExpiresAt() {
      const p = this.jwtPayload;
      return p && typeof p.exp === 'number' ? new Date(p.exp * 1000) : null;
    },
    jwtExpired() {
      return this.jwtExpiresAt ? this.jwtExpiresAt.getTime() < Date.now() : false;
    },
    jwtExpiresInDays() {
      if (!this.jwtExpiresAt) return null;
      const diff = this.jwtExpiresAt.getTime() - Date.now();
      if (diff <= 0) return 0;
      return Math.ceil(diff / (24 * 3600 * 1000));
    }
  },
  async mounted() {
    try {
      const res = await axios.get("/api/user_profile", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      this.profile = res.data;
      await this.fetchAssessmentHistory();
      await this.fetchMyInvites();
    } catch (e) {
      console.error("Ошибка загрузки профиля:", e);
      alert(this.$t('profile.loadError'));
    }
  },
  methods: {
    async saveProfile() {
      try {
        await axios.post("/api/update_profile", {
          ...this.profile,
          old_password: this.oldPassword,
          new_password: this.newPassword
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });

        alert(this.$t('profile.profileUpdated'));
        this.oldPassword = "";
        this.newPassword = "";
      } catch (e) {
        console.error("Ошибка сохранения:", e);
        alert(this.$t('profile.updateError'));
      }
    },

    async fetchAssessmentHistory() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/disc/history', {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.success) {
          this.assessmentHistory = response.data.assessments;
          this.latestAssessment = this.assessmentHistory[0] || null;
        }
      } catch (error) {
        console.error('Error fetching assessment history:', error);
      }
    },
    async fetchMyInvites() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/invites/my', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.myInvites = response.data?.invites || [];
      } catch (error) {
        console.error('Error fetching invites:', error);
      }
    },
    async createInvite() {
      this.inviteLoading = true;
      this.newInviteCode = '';
      try {
        const token = localStorage.getItem('token');
        const maxUses = Math.min(100, Math.max(1, parseInt(this.maxInviteUses, 10) || 1));
        const response = await axios.post('/api/invites', {
          invitee_email: this.inviteeEmail || null,
          max_uses: maxUses
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.newInviteCode = response.data?.code || '';
        await this.fetchMyInvites();
      } catch (error) {
        alert(error.response?.data?.error || 'Не удалось создать инвайт');
      } finally {
        this.inviteLoading = false;
      }
    },

    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    },

    formatDateTime(date) {
      if (!date) return '';
      return date.toLocaleString(this.$i18n?.locale === 'en' ? 'en-US' : 'ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    async copyJwt() {
      const token = this.jwtToken;
      if (!token) return;
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(token);
        } else {
          const ta = document.createElement('textarea');
          ta.value = token;
          ta.style.position = 'fixed';
          ta.style.left = '-9999px';
          document.body.appendChild(ta);
          ta.select();
          document.execCommand('copy');
          document.body.removeChild(ta);
        }
        this.jwtCopied = true;
        setTimeout(() => { this.jwtCopied = false; }, 1600);
      } catch (e) {
        alert(this.$t('profile.jwtCopyFailed'));
      }
    },

    toggleRecommendations(assessmentId) {
      const index = this.expandedAssessments.indexOf(assessmentId);
      if (index > -1) {
        this.expandedAssessments.splice(index, 1);
      } else {
        this.expandedAssessments.push(assessmentId);
      }
    },

    formatRecommendations(recommendations) {
      if (!recommendations) return this.$t('profile.noRecommendations');
      return recommendations.replace(/\n/g, '<br>');
    }
  }
};
</script>
<style scoped>
.profile-page {
  max-width: 900px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

.profile-page h1 {
  text-align: center;
  font-size: 32px;
  margin-bottom: 32px;
  color: #1a1a1a;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.form-section {
  padding: 24px;
  border-left: 4px solid #8b5cf6;
  background: #ffffff;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.form-section:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.form-section h2 {
  font-size: 22px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 24px;
  letter-spacing: -0.3px;
}

label {
  font-weight: 600;
  margin-top: 20px;
  margin-bottom: 10px;
  display: block;
  color: #1f2937;
  font-size: 15px;
  letter-spacing: -0.2px;
}

label:first-of-type {
  margin-top: 0;
}

input {
  width: 100%;
  padding: 14px 18px;
  margin-top: 0;
  margin-bottom: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  background: #ffffff;
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
}

input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

input:hover {
  border-color: #cbd5e1;
}

input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.12), 0 2px 8px rgba(139, 92, 246, 0.08);
  background: #faf5ff;
}

input[readonly] {
  background: #f9fafb;
  color: #6b7280;
  cursor: not-allowed;
}

hr {
  border: none;
  border-top: 1px solid #e5e7eb;
  margin: 32px 0;
}

.modern-button {
  display: inline-block;
  padding: 12px 24px;
  font-size: 15px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.modern-button.purple {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.modern-button.purple:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
}

.disc-section {
  margin-top: 40px;
  padding: 32px;
  background: linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%);
  border-radius: 16px;
  border-left: 4px solid #8b5cf6;
  border: 1px solid #e9d5ff;
  border-left-width: 4px;
}

.disc-section h2 {
  font-size: 22px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
  letter-spacing: -0.3px;
}

.disc-section p {
  color: #6b7280;
  margin-bottom: 24px;
  line-height: 1.7;
  font-size: 14px;
}

.disc-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.modern-button.secondary {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.3);
}

.modern-button.secondary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(107, 114, 128, 0.4);
}

.latest-result {
  background: white;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  margin-top: 24px;
}

.latest-result h3 {
  margin: 0 0 16px 0;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.personality-badge {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 13px;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.scores {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.scores span {
  background: #f3e8ff;
  color: #7c3aed;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
}

.assessment-date {
  color: #6b7280;
  font-size: 12px;
  margin-left: auto;
}

@media (max-width: 768px) {
  .profile-page {
    margin: 20px 10px !important;
    padding: 20px 15px !important;
  }
  
  .form-section {
    padding: 15px !important;
  }
  
  input {
    font-size: 16px !important;
    width: 100% !important;
    box-sizing: border-box !important;
  }
  
  .history-header {
    flex-direction: column !important;
    align-items: flex-start !important;
    gap: 8px !important;
  }
  
  .toggle-btn {
    align-self: flex-end !important;
  }
  
  .form-group {
    margin-bottom: 15px !important;
  }
  
  .form-group label {
    display: block !important;
    margin-bottom: 5px !important;
  }
  
  .save-btn {
    width: 100% !important;
    margin-top: 10px !important;
  }
  
  .disc-actions {
    flex-direction: column;
  }
  
  .result-summary {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .assessment-date {
    margin-left: 0;
  }
}

.history-summary {
  margin-top: 24px;
}

.history-summary h4 {
  margin: 0 0 16px 0;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.history-item {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  padding: 16px;
  background: white;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  transition: all 0.2s ease;
}

.history-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
  flex-wrap: wrap;
  gap: 12px;
}

.history-type {
  font-weight: 600;
  color: #8b5cf6;
  font-size: 14px;
}

.history-date {
  font-size: 12px;
  color: #6b7280;
}

.toggle-btn {
  background: #f3e8ff;
  border: none;
  color: #8b5cf6;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
  font-family: inherit;
}

.toggle-btn:hover {
  background: #e9d5ff;
  transform: translateY(-1px);
}

.recommendations-preview {
  margin-top: 12px;
  padding: 16px;
  background: #faf5ff;
  border-radius: 10px;
  border-left: 3px solid #8b5cf6;
}

.recommendations-content {
  color: #374151;
  line-height: 1.7;
  font-size: 14px;
}

.app-version {
  margin-top: 2rem;
  margin-bottom: 0;
  font-size: 0.75rem;
  color: #9ca3af;
  font-weight: normal;
}
.invite-section .modern-button {
  margin-top: 8px;
}
.invite-section .invite-max-uses {
  width: 100%;
  max-width: 120px;
  padding: 10px 12px;
  margin: 8px 0;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  font-size: 15px;
}

.jwt-section {
  border-left-color: #0ea5e9;
}
.jwt-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.jwt-head h2 { margin: 0; }
.jwt-hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.55;
}
.jwt-meta { display: flex; gap: 8px; align-items: center; }
.jwt-badge {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 999px;
  background: #ecfeff;
  color: #0369a1;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid #bae6fd;
}
.jwt-badge--danger {
  background: #fef2f2;
  color: #b91c1c;
  border-color: #fecaca;
}
.jwt-box {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-top: 8px;
  flex-wrap: wrap;
}
.jwt-box--warn { border-color: #fecaca; background: #fef2f2; }
.jwt-value {
  flex: 1 1 260px;
  min-width: 0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 12px;
  color: #0f172a;
  word-break: break-all;
  background: transparent;
  padding: 2px 0;
  line-height: 1.5;
}
.jwt-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.jwt-btn {
  padding: 8px 14px;
  font-size: 13px;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #1f2937;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}
.jwt-btn:hover {
  border-color: #94a3b8;
  background: #f1f5f9;
}
.jwt-btn--primary {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #fff;
  border-color: transparent;
  box-shadow: 0 4px 10px rgba(14, 165, 233, 0.25);
}
.jwt-btn--primary:hover {
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  color: #fff;
  box-shadow: 0 6px 14px rgba(14, 165, 233, 0.35);
}
.jwt-details {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 6px 18px;
  margin-top: 12px;
  font-size: 12px;
  color: #475569;
}
.jwt-details__k {
  display: inline-block;
  width: 36px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  color: #0ea5e9;
  font-weight: 700;
  text-transform: uppercase;
}
.jwt-details__v {
  color: #0f172a;
}
.muted { color: #6b7280; font-size: 13px; }
.invite-code {
  margin-top: 10px;
  font-size: 0.95rem;
}
.invite-list {
  margin-top: 12px;
  display: grid;
  gap: 8px;
}
.invite-item {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
}
</style>
