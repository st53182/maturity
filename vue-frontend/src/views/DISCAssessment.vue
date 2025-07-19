<template>
  <div class="disc-assessment">
    <div class="container">
      <div v-if="!showResults" class="assessment-container">
        <div class="header">
          <h1>{{ $t('disc.title') }}</h1>
          <p class="subtitle">{{ $t('disc.description') }}</p>
        </div>

        <div v-if="!assessmentStarted" class="intro">
          <div class="intro-content">
            <h2>{{ $t('disc.about') }}</h2>
            <p>{{ $t('disc.description') }}:</p>
            <ul>
              <li v-for="benefit in $t('disc.benefits')" :key="benefit">{{ benefit }}</li>
            </ul>
            <p><strong>{{ $t('disc.duration') }}</strong></p>
            <p><strong>{{ $t('disc.questionCount') }}</strong></p>
          </div>
          <button @click="startAssessment" class="btn btn-primary btn-large">
            {{ $t('disc.startAssessment') }}
          </button>
        </div>

        <div v-else class="question-container">
          <div class="progress-bar">
            <div class="progress" :style="{ width: progressPercentage + '%' }"></div>
          </div>
          <div class="progress-text">
            {{ $t('disc.question') }} {{ currentQuestionIndex + 1 }} {{ $t('disc.of') }} {{ questions.length }}
          </div>

          <div class="question-card">
            <h3>{{ currentQuestion.question }}</h3>
            <div class="options">
              <div 
                v-for="(option, index) in currentQuestion.options" 
                :key="index"
                class="option"
                :class="{ 'selected': selectedAnswer === option.text }"
                @click="selectAnswer(option.text)"
              >
                <div class="option-content">
                  <div class="radio">
                    <div v-if="selectedAnswer === option.text" class="radio-selected"></div>
                  </div>
                  <span>{{ option.text }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="navigation">
            <button 
              @click="previousQuestion" 
              :disabled="currentQuestionIndex === 0"
              class="btn btn-secondary"
            >
              {{ $t('common.cancel') }}
            </button>
            <button 
              @click="nextQuestion" 
              :disabled="!selectedAnswer"
              class="btn btn-primary"
            >
              {{ currentQuestionIndex === questions.length - 1 ? $t('disc.finish') : $t('disc.next') }}
            </button>
          </div>
        </div>
      </div>

      <div v-else class="results-container">
        <div class="results-header">
          <h1>{{ $t('disc.results') }}</h1>
          <div class="personality-type">
            <h2>{{ $t('disc.personalityType') }}: <span class="type-badge">{{ results.personality_type }}</span></h2>
          </div>
        </div>

        <div class="scores-section">
          <h3>{{ $t('disc.results') }}</h3>
          <div class="scores-grid">
            <div class="score-item">
              <div class="score-label">{{ $t('disc.dominance') }} (D)</div>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (results.dominance_score / 36 * 100) + '%' }"></div>
              </div>
              <div class="score-value">{{ results.dominance_score }}/36</div>
            </div>
            <div class="score-item">
              <div class="score-label">{{ $t('disc.influence') }} (I)</div>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (results.influence_score / 36 * 100) + '%' }"></div>
              </div>
              <div class="score-value">{{ results.influence_score }}/36</div>
            </div>
            <div class="score-item">
              <div class="score-label">{{ $t('disc.steadiness') }} (S)</div>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (results.steadiness_score / 36 * 100) + '%' }"></div>
              </div>
              <div class="score-value">{{ results.steadiness_score }}/36</div>
            </div>
            <div class="score-item">
              <div class="score-label">{{ $t('disc.conscientiousness') }} (C)</div>
              <div class="score-bar">
                <div class="score-fill" :style="{ width: (results.conscientiousness_score / 36 * 100) + '%' }"></div>
              </div>
              <div class="score-value">{{ results.conscientiousness_score }}/36</div>
            </div>
          </div>
        </div>

        <div class="recommendations-section">
          <h3>{{ $t('disc.recommendations') }}</h3>
          <div class="recommendations-content" v-html="formattedRecommendations"></div>
        </div>

        <div class="actions">
          <button @click="retakeAssessment" class="btn btn-secondary">
            {{ $t('disc.startAssessment') }}
          </button>
          <router-link to="/profile" class="btn btn-primary">
            {{ $t('nav.dashboard') }}
          </router-link>
        </div>
      </div>

      <div v-if="loading" class="loading-overlay">
        <div class="loading-spinner"></div>
        <p>{{ $t('common.loading') }}</p>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'DISCAssessment',
  data() {
    return {
      assessmentStarted: false,
      questions: [],
      currentQuestionIndex: 0,
      answers: {},
      selectedAnswer: null,
      showResults: false,
      results: null,
      loading: false
    }
  },
  computed: {
    currentQuestion() {
      return this.questions[this.currentQuestionIndex] || {}
    },
    progressPercentage() {
      return ((this.currentQuestionIndex + 1) / this.questions.length) * 100
    },
    formattedRecommendations() {
      if (!this.results?.recommendations) return ''
      return this.results.recommendations.replace(/\n/g, '<br>')
    }
  },
  async mounted() {
    await this.loadQuestions()
  },
  methods: {
    async loadQuestions() {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/disc/questions', {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        if (response.data.success) {
          this.questions = response.data.questions
        } else {
          this.$toast.error('Ошибка при загрузке вопросов')
        }
      } catch (error) {
        console.error('Error loading questions:', error)
        this.$toast.error('Ошибка при загрузке вопросов')
      }
    },
    startAssessment() {
      this.assessmentStarted = true
      this.currentQuestionIndex = 0
      this.answers = {}
      this.selectedAnswer = this.answers[this.currentQuestion.id] || null
    },
    selectAnswer(answer) {
      this.selectedAnswer = answer
    },
    nextQuestion() {
      if (!this.selectedAnswer) return
      
      this.answers[this.currentQuestion.id] = this.selectedAnswer
      
      if (this.currentQuestionIndex === this.questions.length - 1) {
        this.submitAssessment()
      } else {
        this.currentQuestionIndex++
        this.selectedAnswer = this.answers[this.currentQuestion.id] || null
      }
    },
    previousQuestion() {
      if (this.currentQuestionIndex > 0) {
        this.currentQuestionIndex--
        this.selectedAnswer = this.answers[this.currentQuestion.id] || null
      }
    },
    async submitAssessment() {
      this.loading = true
      try {
        const token = localStorage.getItem('token')
        const response = await axios.post('/api/disc/submit', {
          answers: this.answers
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        if (response.data.success) {
          this.results = response.data.assessment
          this.showResults = true
          if (this.$toast) {
            this.$toast.success('Оценка успешно завершена!')
          }
        } else {
          if (this.$toast) {
            this.$toast.error('Ошибка при сохранении результатов')
          }
        }
      } catch (error) {
        console.error('Error submitting assessment:', error)
        this.$toast.error('Ошибка при сохранении результатов')
      } finally {
        this.loading = false
      }
    },
    retakeAssessment() {
      this.assessmentStarted = false
      this.showResults = false
      this.answers = {}
      this.selectedAnswer = null
      this.currentQuestionIndex = 0
      this.results = null
    }
  }
}
</script>

<style scoped>
.disc-assessment {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px 0;
}

.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 0 20px;
}

.assessment-container, .results-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  text-align: center;
}

.header h1 {
  margin: 0 0 10px 0;
  font-size: 2.5rem;
  font-weight: 700;
}

.subtitle {
  margin: 0;
  font-size: 1.2rem;
  opacity: 0.9;
}

.intro {
  padding: 40px;
  text-align: center;
}

.intro-content {
  margin-bottom: 30px;
}

.intro-content h2 {
  color: #333;
  margin-bottom: 20px;
}

.intro-content ul {
  text-align: left;
  max-width: 500px;
  margin: 20px auto;
}

.intro-content li {
  margin-bottom: 8px;
  color: #666;
}

.question-container {
  padding: 40px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  margin-bottom: 10px;
  overflow: hidden;
}

.progress {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #666;
  margin-bottom: 30px;
  font-weight: 500;
}

.question-card {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 30px;
  margin-bottom: 30px;
}

.question-card h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 1.3rem;
  line-height: 1.5;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.option {
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.option:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.option.selected {
  border-color: #667eea;
  background: #f0f4ff;
}

.option-content {
  display: flex;
  align-items: center;
  gap: 15px;
}

.radio {
  width: 20px;
  height: 20px;
  border: 2px solid #ddd;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.option.selected .radio {
  border-color: #667eea;
}

.radio-selected {
  width: 10px;
  height: 10px;
  background: #667eea;
  border-radius: 50%;
}

.navigation {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.results-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 40px;
  text-align: center;
}

.results-header h1 {
  margin: 0 0 20px 0;
  font-size: 2.2rem;
}

.personality-type h2 {
  margin: 0;
  font-size: 1.5rem;
}

.type-badge {
  background: rgba(255, 255, 255, 0.2);
  padding: 8px 16px;
  border-radius: 20px;
  font-weight: 700;
}

.scores-section, .recommendations-section {
  padding: 40px;
  border-bottom: 1px solid #eee;
}

.scores-section h3, .recommendations-section h3 {
  color: #333;
  margin-bottom: 25px;
  font-size: 1.4rem;
}

.scores-grid {
  display: grid;
  gap: 20px;
}

.score-item {
  display: grid;
  grid-template-columns: 150px 1fr 80px;
  align-items: center;
  gap: 15px;
}

.score-label {
  font-weight: 600;
  color: #333;
}

.score-bar {
  height: 12px;
  background: #e0e0e0;
  border-radius: 6px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  transition: width 0.5s ease;
}

.score-value {
  font-weight: 600;
  color: #667eea;
  text-align: right;
}

.recommendations-content {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 8px;
  line-height: 1.6;
  color: #333;
}

.actions {
  padding: 40px;
  display: flex;
  gap: 20px;
  justify-content: center;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-2px);
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-large {
  padding: 16px 32px;
  font-size: 1.1rem;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  color: white;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.3);
  border-top: 4px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .container {
    padding: 0 15px;
  }
  
  .header {
    padding: 30px 20px;
  }
  
  .header h1 {
    font-size: 2rem;
  }
  
  .question-container, .intro, .scores-section, .recommendations-section, .actions {
    padding: 30px 20px;
  }
  
  .score-item {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  
  .actions {
    flex-direction: column;
  }
  
  .navigation {
    flex-direction: column;
  }
}
</style>
