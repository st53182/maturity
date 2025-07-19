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
      console.error(this.$t('console.loadingError'), e);
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
        console.error(this.$t('console.saveError'), e);
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
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.05);
  font-family: "Segoe UI", sans-serif;
}

.profile-page h1 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 30px;
  color: #2c3e50;
  font-weight: 800;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  padding: 10px 20px;
  border-left: 4px solid #8e44ad;
  background: #fafafa;
  border-radius: 8px;
}

.form-section h2 {
  font-size: 20px;
  color: #2c3e50;
  margin-bottom: 20px;
}

label {
  font-weight: 600;
  margin-top: 12px;
  display: block;
  color: #34495e;
}

input {
  width: 100%;
  padding: 12px;
  margin-top: 6px;
  margin-bottom: 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #8e44ad;
  box-shadow: 0 0 0 2px rgba(142, 68, 173, 0.2);
}

hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 30px 0;
}

.modern-button {
  display: inline-block;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}

.modern-button.purple {
  background: linear-gradient(90deg, #8e44ad, #9b59b6);
  color: white;
  box-shadow: 0 4px 14px rgba(142, 68, 173, 0.2);
}

.modern-button.purple:hover {
  background: linear-gradient(90deg, #732d91, #884ea0);
  transform: scale(1.03);
}

.disc-section {
  margin-top: 40px;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 16px;
  border-left: 4px solid #667eea;
}

.disc-section h2 {
  font-size: 20px;
  color: #2c3e50;
  margin-bottom: 15px;
}

.disc-section p {
  color: #666;
  margin-bottom: 25px;
  line-height: 1.6;
}

.disc-actions {
  display: flex;
  gap: 15px;
  margin-bottom: 25px;
  flex-wrap: wrap;
}

.modern-button.secondary {
  background: linear-gradient(90deg, #6c757d, #5a6268);
  color: white;
  box-shadow: 0 4px 14px rgba(108, 117, 125, 0.2);
}

.modern-button.secondary:hover {
  background: linear-gradient(90deg, #5a6268, #495057);
  transform: scale(1.03);
}

.latest-result {
  background: white;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #e0e0e0;
}

.latest-result h3 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.result-summary {
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}

.personality-badge {
  background: linear-gradient(90deg, #667eea, #764ba2);
  color: white;
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 600;
  font-size: 14px;
}

.scores {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.scores span {
  background: #f0f4ff;
  color: #667eea;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
}

.assessment-date {
  color: #666;
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
  margin-top: 20px;
}

.history-summary h4 {
  margin: 0 0 15px 0;
  color: #333;
  font-size: 16px;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.history-item {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  padding: 12px;
  background: white;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.history-type {
  font-weight: 600;
  color: #667eea;
}

.history-date {
  font-size: 12px;
  color: #666;
}

.toggle-btn {
  background: none;
  border: none;
  color: #667eea;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.toggle-btn:hover {
  background-color: #f0f4ff;
}

.recommendations-preview {
  margin-top: 12px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 3px solid #667eea;
}

.recommendations-content {
  color: #333;
  line-height: 1.6;
  font-size: 14px;
}
</style>
