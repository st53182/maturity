<template>
  <div class="survey-results-container">
    <div v-if="loading" class="loading">⏳ Загрузка результатов...</div>
    
    <div v-else-if="error" class="error">❌ {{ error }}</div>
    
    <div v-else class="results-content">
      <div class="results-header">
        <h1>📊 {{ survey.title }}</h1>
        <div class="survey-meta">
          <span class="survey-type">{{ survey.survey_type.toUpperCase() }}</span>
          <span class="response-count">{{ $t('surveys.responses') }}: {{ survey.response_count }}</span>
        </div>
      </div>
      
      <div v-if="survey.survey_type === 'enps'" class="enps-results">
        <div class="metrics-grid">
          <div class="metric-card nps-score">
            <h3>{{ $t('surveys.npsScore') }}</h3>
            <div class="metric-value">{{ analytics.nps_score?.toFixed(1) || 0 }}</div>
          </div>
          
          <div class="metric-card response-count">
            <h3>{{ $t('surveys.responseCount') }}</h3>
            <div class="metric-value">{{ analytics.response_count || 0 }}</div>
          </div>
        </div>
        
        <div class="question-analytics">
          <h3>Средние оценки по вопросам</h3>
          <div v-for="(data, questionKey) in analytics.averages" :key="questionKey" class="question-result">
            <div class="question-header">
              <span class="question-number">Вопрос {{ questionKey.replace('question_', '') }}</span>
              <span class="average-score">{{ data.average.toFixed(2) }}</span>
            </div>
            
            <div class="score-distribution">
              <div v-for="(count, score) in data.distribution" :key="score" 
                   class="distribution-bar"
                   :style="{ width: (count / data.count * 100) + '%' }">
                <span class="score-label">{{ score }}: {{ count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="survey.survey_type === '360'" class="feedback-360-results">
        <div class="competency-results">
          <h3>{{ $t('surveys.competencyRatings') }}</h3>
          
          <div v-for="(data, competency) in analytics.competency_averages" :key="competency" 
               class="competency-item">
            <div class="competency-header">
              <span class="competency-name">{{ competency }}</span>
              <span class="competency-score">{{ data.average.toFixed(2) }}</span>
            </div>
            
            <div class="competency-bar">
              <div class="bar-fill" :style="{ width: (data.average / 5 * 100) + '%' }"></div>
            </div>
            
            <span class="response-count">{{ data.count }} {{ data.count === 1 ? 'ответ' : 'ответов' }}</span>
          </div>
        </div>
        
        <div v-if="analytics.detailed_responses" class="detailed-responses">
          <h3>{{ $t('surveys.detailedView') }}</h3>
          <div class="toggle-anonymous">
            <label>
              <input type="checkbox" v-model="showDetailedNames" />
              Показать имена респондентов (только для создателя)
            </label>
          </div>
          
          <div v-for="(response, index) in analytics.detailed_responses" :key="index" 
               class="response-card">
            <div class="response-header">
              <span v-if="showDetailedNames" class="respondent-name">
                {{ response.respondent_name || 'Анонимный' }}
              </span>
              <span v-else class="respondent-anonymous">Респондент {{ index + 1 }}</span>
              <span class="response-date">{{ formatDate(response.submitted_at) }}</span>
            </div>
            
            <div class="response-content">
              <div v-for="(answer, questionId) in response.answers" :key="questionId" 
                   class="answer-item">
                <strong>{{ getQuestionText(questionId) }}:</strong>
                <div v-if="typeof answer === 'object'" class="matrix-answer">
                  <div v-for="(rating, competency) in answer" :key="competency" 
                       class="matrix-item">
                    {{ competency }}: {{ rating }}
                  </div>
                </div>
                <div v-else class="text-answer">{{ answer }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="export-section">
        <button @click="exportResults" class="export-btn">
          📄 {{ $t('surveys.exportResults') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SurveyAnalytics',
  data() {
    return {
      survey: null,
      analytics: {},
      loading: true,
      error: null,
      showDetailedNames: false
    }
  },
  
  async mounted() {
    await this.loadResults()
  },
  
  methods: {
    async loadResults() {
      try {
        const surveyId = this.$route.params.surveyId
        const token = localStorage.getItem('token')
        
        const response = await axios.get(`/api/surveys/${surveyId}/results`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        this.survey = response.data.survey
        this.analytics = response.data.analytics
        
      } catch (error) {
        console.error('Error loading results:', error)
        this.error = error.response?.data?.error || 'Ошибка загрузки результатов'
      } finally {
        this.loading = false
      }
    },
    
    getQuestionText(questionId) {
      const questionMap = {
        '1': 'Имя',
        '2': 'Ключевые таланты',
        '3': 'Области развития',
        '4': 'Примеры развития',
        '5': 'Другие комментарии',
        '6': 'Оценки компетенций'
      }
      return questionMap[questionId] || `Вопрос ${questionId}`
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    
    exportResults() {
      const csvContent = this.generateCSV()
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `${this.survey.title}_results.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    
    generateCSV() {
      let csv = 'Survey Results\n'
      csv += `Title: ${this.survey.title}\n`
      csv += `Type: ${this.survey.survey_type}\n`
      csv += `Responses: ${this.survey.response_count}\n\n`
      
      if (this.survey.survey_type === 'enps') {
        csv += 'Question,Average Score,Response Count\n'
        Object.entries(this.analytics.averages || {}).forEach(([key, data]) => {
          csv += `${key},${data.average.toFixed(2)},${data.count}\n`
        })
      }
      
      return csv
    }
  }
}
</script>

<style scoped>
.survey-results-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.results-header {
  text-align: center;
  margin-bottom: 40px;
}

.survey-meta {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.survey-type {
  background: #3498db;
  color: white;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 14px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.metric-card {
  background: white;
  padding: 20px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  text-align: center;
}

.metric-value {
  font-size: 36px;
  font-weight: bold;
  color: #2ecc71;
  margin-top: 10px;
}

.question-analytics, .competency-results {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.question-result, .competency-item {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.question-header, .competency-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.average-score, .competency-score {
  font-size: 18px;
  font-weight: bold;
  color: #3498db;
}

.score-distribution {
  display: flex;
  gap: 5px;
  height: 30px;
}

.distribution-bar {
  background: #3498db;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  min-width: 40px;
}

.competency-bar {
  width: 100%;
  height: 20px;
  background: #ecf0f1;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 5px;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #e74c3c, #f39c12, #f1c40f, #2ecc71, #27ae60);
  transition: width 0.3s ease;
}

.detailed-responses {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.response-card {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
}

.response-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 15px;
  font-weight: bold;
}

.answer-item {
  margin-bottom: 15px;
}

.matrix-answer {
  margin-top: 5px;
  padding-left: 20px;
}

.matrix-item {
  margin-bottom: 5px;
  font-size: 14px;
}

.text-answer {
  margin-top: 5px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.export-section {
  text-align: center;
}

.export-btn {
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

.export-btn:hover {
  background: #27ae60;
}

.loading, .error {
  text-align: center;
  padding: 50px;
  font-size: 18px;
}

.error {
  color: #e74c3c;
}
</style>
