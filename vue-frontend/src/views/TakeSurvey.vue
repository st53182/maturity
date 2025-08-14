<template>
  <div class="take-survey-container">
    <div v-if="loading" class="loading">⏳ Загрузка опросника...</div>
    
    <div v-else-if="error" class="error">❌ {{ error }}</div>
    
    <div v-else-if="submitted" class="success">
      <h2>✅ Спасибо за участие!</h2>
      <p>Ваши ответы успешно отправлены.</p>
    </div>
    
    <div v-else class="survey-form">
      <div class="survey-header">
        <h1>{{ survey.title }}</h1>
        <div class="survey-info">
          <span class="survey-type">{{ survey.survey_type.toUpperCase() }}</span>
          <span v-if="survey.deadline" class="deadline">
            Срок: {{ formatDate(survey.deadline) }}
          </span>
        </div>
      </div>
      
      <div class="progress-bar">
        <div class="progress" :style="{ width: progressPercent + '%' }"></div>
      </div>
      
      <div class="question-container">
        <div v-if="currentQuestion" class="question">
          <h3>{{ currentQuestion.question }}</h3>
          
          <input v-if="currentQuestion.type === 'text'" 
                 v-model="answers[currentQuestion.id]"
                 type="text"
                 class="text-input"
                 :required="currentQuestion.required" />
          
          <textarea v-if="currentQuestion.type === 'textarea'"
                    v-model="answers[currentQuestion.id]"
                    class="textarea-input"
                    rows="4"
                    :required="currentQuestion.required"></textarea>
          
          <div v-if="currentQuestion.type === 'radio'" class="radio-options">
            <label v-for="option in currentQuestion.options" :key="option" class="radio-label">
              <input type="radio" 
                     :value="option" 
                     v-model="answers[currentQuestion.id]"
                     :required="currentQuestion.required" />
              <span>{{ option }}</span>
            </label>
          </div>
          
          <div v-if="currentQuestion.type === 'scale'" class="scale-options">
            <div class="scale-labels">
              <span>1 (Низко)</span>
              <span>5 (Высоко)</span>
            </div>
            <div class="scale-buttons">
              <button v-for="value in currentQuestion.scale" 
                      :key="value"
                      :class="{ active: answers[currentQuestion.id] == value }"
                      @click="answers[currentQuestion.id] = value"
                      class="scale-btn">
                {{ value }}
              </button>
            </div>
          </div>
          
          <div v-if="currentQuestion.type === 'matrix'" class="matrix-rating">
            <div class="matrix-header">
              <div class="matrix-scale-labels">
                <span v-for="label in currentQuestion.scale" :key="label" class="scale-label">
                  {{ label }}
                </span>
              </div>
            </div>
            
            <div v-for="row in currentQuestion.rows" :key="row" class="matrix-row">
              <div class="row-label">{{ row }}</div>
              <div class="row-options">
                <label v-for="(label, index) in currentQuestion.scale" :key="index" class="matrix-option">
                  <input type="radio" 
                         :name="`matrix_${currentQuestion.id}_${row}`"
                         :value="label"
                         v-model="matrixAnswers[currentQuestion.id][row]" />
                  <span class="radio-custom"></span>
                </label>
              </div>
            </div>
          </div>
        </div>
        
        <div class="navigation-buttons">
          <button v-if="currentQuestionIndex > 0" 
                  @click="previousQuestion" 
                  class="nav-btn prev-btn">
            ← Назад
          </button>
          
          <button v-if="currentQuestionIndex < survey.questions.length - 1" 
                  @click="nextQuestion" 
                  class="nav-btn next-btn"
                  :disabled="!isCurrentQuestionAnswered">
            Далее →
          </button>
          
          <button v-if="currentQuestionIndex === survey.questions.length - 1" 
                  @click="submitSurvey" 
                  class="nav-btn submit-btn"
                  :disabled="!allRequiredAnswered">
            Отправить ответы
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SurveyTaker',
  data() {
    return {
      survey: null,
      loading: true,
      error: null,
      submitted: false,
      currentQuestionIndex: 0,
      answers: {},
      matrixAnswers: {}
    }
  },
  
  computed: {
    currentQuestion() {
      return this.survey?.questions[this.currentQuestionIndex]
    },
    
    progressPercent() {
      if (!this.survey) return 0
      return ((this.currentQuestionIndex + 1) / this.survey.questions.length) * 100
    },
    
    isCurrentQuestionAnswered() {
      const question = this.currentQuestion
      if (!question) return false
      
      if (question.type === 'matrix') {
        const matrixData = this.matrixAnswers[question.id] || {}
        return question.required ? 
          question.rows.every(row => matrixData[row]) : 
          true
      }
      
      return question.required ? 
        (this.answers[question.id] !== undefined && this.answers[question.id] !== '') : 
        true
    },
    
    allRequiredAnswered() {
      return this.survey?.questions.every(question => {
        if (!question.required) return true
        
        if (question.type === 'matrix') {
          const matrixData = this.matrixAnswers[question.id] || {}
          return question.rows.every(row => matrixData[row])
        }
        
        return this.answers[question.id] !== undefined && this.answers[question.id] !== ''
      })
    }
  },
  
  async mounted() {
    await this.loadSurvey()
  },
  
  methods: {
    async loadSurvey() {
      try {
        const token = this.$route.params.token
        const response = await axios.get(`/api/survey/${token}`)
        this.survey = response.data
        
        this.survey.questions.forEach(question => {
          if (question.type === 'matrix') {
            this.matrixAnswers[question.id] = {}
          }
        })
        
      } catch (error) {
        console.error('Error loading survey:', error)
        this.error = error.response?.data?.error || 'Ошибка загрузки опросника'
      } finally {
        this.loading = false
      }
    },
    
    nextQuestion() {
      if (this.currentQuestionIndex < this.survey.questions.length - 1) {
        this.currentQuestionIndex++
      }
    },
    
    previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--
      }
    },
    
    async submitSurvey() {
      try {
        const token = this.$route.params.token
        
        const allAnswers = { ...this.answers }
        Object.keys(this.matrixAnswers).forEach(questionId => {
          allAnswers[questionId] = this.matrixAnswers[questionId]
        })
        
        await axios.post(`/api/survey/${token}/submit`, {
          answers: allAnswers,
          respondent_name: this.answers[1]
        })
        
        this.submitted = true
        
      } catch (error) {
        console.error('Error submitting survey:', error)
        alert('Ошибка отправки ответов')
      }
    },
    
    formatDate(dateString) {
      return new Date(dateString).toLocaleDateString('ru-RU')
    }
  }
}
</script>

<style scoped>
.take-survey-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.survey-header {
  text-align: center;
  margin-bottom: 30px;
}

.survey-info {
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

.deadline {
  color: #e74c3c;
  font-weight: bold;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #ecf0f1;
  border-radius: 4px;
  margin-bottom: 30px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #3498db, #2ecc71);
  transition: width 0.3s ease;
}

.question {
  background: white;
  padding: 30px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  margin-bottom: 30px;
}

.text-input, .textarea-input {
  width: 100%;
  padding: 12px;
  border: 2px solid #ddd;
  border-radius: 8px;
  font-size: 16px;
  margin-top: 15px;
}

.radio-options {
  margin-top: 15px;
}

.radio-label {
  display: block;
  margin-bottom: 10px;
  cursor: pointer;
}

.radio-label input {
  margin-right: 10px;
}

.scale-options {
  margin-top: 15px;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
  color: #666;
}

.scale-buttons {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.scale-btn {
  width: 50px;
  height: 50px;
  border: 2px solid #ddd;
  border-radius: 50%;
  background: white;
  cursor: pointer;
  font-size: 18px;
  font-weight: bold;
  transition: all 0.3s ease;
}

.scale-btn:hover {
  border-color: #3498db;
}

.scale-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.matrix-rating {
  margin-top: 20px;
}

.matrix-header {
  margin-bottom: 15px;
}

.matrix-scale-labels {
  display: grid;
  grid-template-columns: 200px repeat(5, 1fr);
  gap: 10px;
  font-size: 12px;
  font-weight: bold;
  text-align: center;
}

.matrix-row {
  display: grid;
  grid-template-columns: 200px repeat(5, 1fr);
  gap: 10px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #eee;
}

.row-label {
  font-size: 14px;
  font-weight: 500;
}

.row-options {
  display: contents;
}

.matrix-option {
  display: flex;
  justify-content: center;
  cursor: pointer;
}

.radio-custom {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 50%;
  display: inline-block;
}

.matrix-option input:checked + .radio-custom {
  background: #3498db;
  border-color: #3498db;
}

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  gap: 15px;
}

.nav-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.prev-btn {
  background: #95a5a6;
  color: white;
}

.next-btn {
  background: #3498db;
  color: white;
}

.submit-btn {
  background: #2ecc71;
  color: white;
}

.nav-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.nav-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.success {
  text-align: center;
  padding: 50px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
