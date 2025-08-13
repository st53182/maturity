<template>
  <div class="surveys-container">
    <h1>📋 {{ $t('surveys.title') }}</h1>
    
    <div class="create-survey-section">
      <h2>{{ $t('surveys.createSurvey') }}</h2>
      
      <div class="survey-type-selection">
        <div class="survey-type-card" 
             :class="{ active: selectedType === 'enps' }"
             @click="selectedType = 'enps'">
          <h3>📊 {{ $t('surveys.enpsTitle') }}</h3>
          <p>Собрать обратную связь от сотрудников о текущем состоянии в команде</p>
        </div>
        
        <div class="survey-type-card"
             :class="{ active: selectedType === '360' }"
             @click="selectedType = '360'">
          <h3>🔄 {{ $t('surveys.feedback360Title') }}</h3>
          <p>Собрать анонимную обратную связь о конкретном сотруднике от коллег</p>
        </div>
      </div>
      
      <div v-if="selectedType" class="survey-form">
        <input v-model="surveyTitle" 
               :placeholder="$t('surveys.surveyTitle')" 
               class="survey-input" />
        
        <select v-if="selectedType === 'enps'" 
                v-model="selectedTeamId" 
                class="survey-select">
          <option value="">{{ $t('surveys.selectTeam') }}</option>
          <option v-for="team in teams" :key="team.id" :value="team.id">
            {{ team.name }}
          </option>
        </select>
        
        <select v-if="selectedType === '360'" 
                v-model="selectedEmployeeId" 
                class="survey-select">
          <option value="">{{ $t('surveys.selectEmployee') }}</option>
          <option v-for="employee in employees" :key="employee.id" :value="employee.id">
            {{ employee.name }}
          </option>
        </select>
        
        <input v-model="deadline" 
               type="datetime-local" 
               :placeholder="$t('surveys.deadline')"
               class="survey-input" />
        
        <textarea v-model="emailList" 
                  :placeholder="$t('surveys.emailPlaceholder')"
                  class="survey-textarea"
                  rows="3"></textarea>
        
        <button @click="createSurvey" 
                :disabled="!canCreateSurvey"
                class="create-survey-btn">
          {{ $t('surveys.createAndSend') }}
        </button>
      </div>
    </div>
    
    <div class="existing-surveys">
      <h2>Мои опросники</h2>
      
      <div v-if="loading" class="loading">⏳ Загрузка...</div>
      
      <div v-else-if="surveys.length === 0" class="no-surveys">
        Нет созданных опросников
      </div>
      
      <div v-else class="surveys-grid">
        <div v-for="survey in surveys" :key="survey.id" class="survey-card">
          <div class="survey-header">
            <h3>{{ survey.title }}</h3>
            <span class="survey-type">{{ survey.survey_type.toUpperCase() }}</span>
          </div>
          
          <div class="survey-stats">
            <span>{{ $t('surveys.responses') }}: {{ survey.response_count }}</span>
            <span class="survey-status" :class="survey.status">
              {{ $t(`surveys.surveyStatus.${survey.status}`) }}
            </span>
          </div>
          
          <div class="survey-actions">
            <button @click="viewResults(survey.id)" class="view-results-btn">
              📊 {{ $t('surveys.analytics') }}
            </button>
            <button @click="copySurveyLink(survey)" class="copy-link-btn">
              🔗 {{ $t('surveys.copyLink') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SurveyList',
  data() {
    return {
      selectedType: '',
      surveyTitle: '',
      selectedTeamId: '',
      selectedEmployeeId: '',
      deadline: '',
      emailList: '',
      teams: [],
      employees: [],
      surveys: [],
      loading: false
    }
  },
  
  computed: {
    canCreateSurvey() {
      return this.surveyTitle && 
             ((this.selectedType === 'enps' && this.selectedTeamId) ||
              (this.selectedType === '360' && this.selectedEmployeeId)) &&
             this.emailList
    }
  },
  
  async mounted() {
    await this.fetchTeams()
    await this.fetchEmployees()
    await this.fetchSurveys()
  },
  
  methods: {
    async fetchTeams() {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/user_teams', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.teams = response.data
      } catch (error) {
        console.error('Error fetching teams:', error)
      }
    },
    
    async fetchEmployees() {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/employees', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.employees = response.data
      } catch (error) {
        console.error('Error fetching employees:', error)
      }
    },
    
    async fetchSurveys() {
      try {
        this.loading = true
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/surveys', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.surveys = response.data
      } catch (error) {
        console.error('Error fetching surveys:', error)
      } finally {
        this.loading = false
      }
    },
    
    async createSurvey() {
      try {
        const token = localStorage.getItem('token')
        const emails = this.emailList.split(',').map(email => email.trim()).filter(email => email)
        
        const surveyData = {
          survey_type: this.selectedType,
          title: this.surveyTitle,
          team_id: this.selectedTeamId || null,
          target_employee_id: this.selectedEmployeeId || null,
          deadline: this.deadline || null
        }
        
        const createResponse = await axios.post('/api/surveys', surveyData, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        const surveyId = createResponse.data.id
        
        await axios.post(`/api/surveys/${surveyId}/send`, { emails }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        alert(this.$t('surveys.surveyCreated'))
        
        this.selectedType = ''
        this.surveyTitle = ''
        this.selectedTeamId = ''
        this.selectedEmployeeId = ''
        this.deadline = ''
        this.emailList = ''
        
        await this.fetchSurveys()
        
      } catch (error) {
        console.error('Error creating survey:', error)
        alert('Ошибка создания опросника')
      }
    },
    
    viewResults(surveyId) {
      this.$router.push(`/survey/${surveyId}/results`)
    },
    
    async copySurveyLink(survey) {
      try {
        const link = `${window.location.origin}/survey/${survey.access_token}`
        
        await navigator.clipboard.writeText(link)
        alert('Ссылка скопирована в буфер обмена!')
      } catch (error) {
        console.error('Error copying link:', error)
      }
    }
  }
}
</script>

<style scoped>
.surveys-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.survey-type-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 30px;
}

.survey-type-card {
  border: 2px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.survey-type-card:hover {
  border-color: #3498db;
}

.survey-type-card.active {
  border-color: #2ecc71;
  background-color: #f8fff8;
}

.survey-form {
  display: flex;
  flex-direction: column;
  gap: 15px;
  max-width: 500px;
}

.survey-input, .survey-select, .survey-textarea {
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
}

.create-survey-btn {
  background: #2ecc71;
  color: white;
  padding: 15px 30px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s ease;
}

.create-survey-btn:hover:not(:disabled) {
  background: #27ae60;
}

.create-survey-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.surveys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.survey-card {
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  padding: 20px;
  background: white;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.survey-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.survey-type {
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.survey-stats {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-size: 14px;
  color: #666;
}

.survey-status.active {
  color: #2ecc71;
  font-weight: bold;
}

.survey-actions {
  display: flex;
  gap: 10px;
}

.view-results-btn, .copy-link-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

.view-results-btn {
  background: #3498db;
  color: white;
}

.copy-link-btn {
  background: #95a5a6;
  color: white;
}

.view-results-btn:hover {
  background: #2980b9;
}

.copy-link-btn:hover {
  background: #7f8c8d;
}
</style>
