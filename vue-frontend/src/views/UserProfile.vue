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

    <div class="disc-section">
      <h2>{{ $t('profile.discSection') }}</h2>
      <p>{{ $t('profile.discDescription') }}</p>
      
      <div class="disc-actions">
        <router-link to="/disc-assessment" class="modern-button purple">
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
  </div>
</template>
<script>
import axios from "axios";

export default {
  name: "UserProfile",
  data() {
    return {
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
      expandedAssessments: []
    };
  },
  async mounted() {
    try {
      const res = await axios.get("/api/user_profile", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      this.profile = res.data;
      await this.fetchAssessmentHistory();
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

    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
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
  margin-top: 16px;
  margin-bottom: 8px;
  display: block;
  color: #374151;
  font-size: 14px;
}

input {
  width: 100%;
  padding: 12px 16px;
  margin-top: 0;
  margin-bottom: 16px;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease;
  font-family: inherit;
  background: #ffffff;
  box-sizing: border-box;
}

input:focus {
  outline: none;
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

input[readonly] {
  background: #f9fafb;
  color: #6b7280;
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
</style>
