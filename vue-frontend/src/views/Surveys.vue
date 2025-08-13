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
        
        <div class="deadline-field">
          <label for="deadline" class="deadline-label">{{ $t('surveys.deadlineLabel') }}</label>
          <input v-model="deadline" 
                 id="deadline"
                 type="datetime-local" 
                 class="survey-input" />
          <small class="deadline-help">{{ $t('surveys.deadlineHelp') }}</small>
        </div>
        
        <textarea v-model="emailList" 
                  :placeholder="$t('surveys.emailPlaceholder')"
                  class="survey-textarea"
                  rows="3"></textarea>
        
        <button @click="previewSurvey" 
                :disabled="!canPreviewSurvey"
                class="preview-survey-btn">
          {{ $t('surveys.previewSurvey') }}
        </button>
        
        <button @click="createAndSendSurvey" 
                :disabled="!canPreviewSurvey"
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
    
    <!-- Survey Preview Modal -->
    <div v-if="showPreview" class="preview-modal">
      <div class="preview-content">
        <div class="preview-header">
          <h2>{{ $t('surveys.previewTitle') }}: {{ surveyTitle }}</h2>
          <button @click="closePreview" class="close-btn">✕</button>
        </div>
        
        <div class="preview-body">
          <div class="survey-info">
            <p><strong>{{ $t('surveys.surveyType') }}:</strong> {{ selectedType.toUpperCase() }}</p>
            <p v-if="selectedType === 'enps'"><strong>{{ $t('surveys.team') }}:</strong> {{ getTeamName(selectedTeamId) }}</p>
            <p v-if="selectedType === '360'"><strong>{{ $t('surveys.employee') }}:</strong> {{ getEmployeeName(selectedEmployeeId) }}</p>
            <p v-if="deadline"><strong>{{ $t('surveys.deadlineLabel') }}:</strong> {{ formatDeadline(deadline) }}</p>
          </div>
          
          <div class="questions-preview">
            <h3>{{ $t('surveys.questionsPreview') }}</h3>
            <div v-for="(question, index) in currentQuestions" :key="question.id" class="question-preview">
              <div class="question-header">
                <span class="question-number">{{ index + 1 }}.</span>
                <span class="question-text">{{ question.question }}</span>
                <span v-if="question.required" class="required-mark">*</span>
                <button @click="editQuestion(index)" class="edit-question-btn">✏️</button>
              </div>
              
              <div class="question-type-info">
                <span class="question-type">{{ $t(`surveys.questionTypes.${question.type}`) }}</span>
                <span v-if="question.options" class="options-count">
                  ({{ question.options.length }} {{ $t('surveys.options') }})
                </span>
                <span v-if="question.scale" class="scale-info">
                  ({{ $t('surveys.scale') }}: {{ question.scale[0] }}-{{ question.scale[question.scale.length - 1] }})
                </span>
                <span v-if="question.rows" class="matrix-info">
                  ({{ question.rows.length }} {{ $t('surveys.competencies') }})
                </span>
              </div>
            </div>
          </div>
          
          <div class="email-preview">
            <h3>{{ $t('surveys.recipientsPreview') }}</h3>
            <div class="email-list">
              <span v-for="email in emailArray" :key="email" class="email-tag">{{ email }}</span>
            </div>
            <p class="recipient-count">{{ $t('surveys.totalRecipients') }}: {{ emailArray.length }}</p>
          </div>
        </div>
        
        <div class="preview-actions">
          <button @click="editSurvey" class="edit-btn">{{ $t('surveys.editSurvey') }}</button>
          <button @click="createAndSendSurvey" class="send-btn">{{ $t('surveys.createAndSend') }}</button>
        </div>
      </div>
    </div>
    
    <!-- Question Edit Modal -->
    <div v-if="showQuestionEdit" class="question-edit-modal">
      <div class="question-edit-content">
        <div class="edit-header">
          <h3>{{ $t('surveys.editQuestion') }}</h3>
          <button @click="closeQuestionEdit" class="close-btn">✕</button>
        </div>
        
        <div class="edit-body">
          <div class="form-group">
            <label>{{ $t('surveys.questionText') }}</label>
            <textarea v-model="editingQuestion.question" class="question-input" rows="3"></textarea>
          </div>
          
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="editingQuestion.required" />
              {{ $t('surveys.requiredQuestion') }}
            </label>
          </div>
          
          <div v-if="editingQuestion.type === 'radio'" class="form-group">
            <label>{{ $t('surveys.options') }}</label>
            <div v-for="(option, index) in editingQuestion.options" :key="index" class="option-input">
              <input v-model="editingQuestion.options[index]" class="option-field" />
              <button @click="removeOption(index)" class="remove-option-btn">✕</button>
            </div>
            <button @click="addOption" class="add-option-btn">{{ $t('surveys.addOption') }}</button>
          </div>
          
          <div v-if="editingQuestion.type === 'scale'" class="form-group">
            <label>{{ $t('surveys.scaleRange') }}</label>
            <div class="scale-inputs">
              <input v-model.number="scaleMin" type="number" min="1" max="10" />
              <span>-</span>
              <input v-model.number="scaleMax" type="number" min="1" max="10" />
            </div>
          </div>
        </div>
        
        <div class="edit-actions">
          <button @click="saveQuestion" class="save-btn">{{ $t('surveys.saveQuestion') }}</button>
          <button @click="closeQuestionEdit" class="cancel-btn">{{ $t('surveys.cancel') }}</button>
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
      loading: false,
      showPreview: false,
      showQuestionEdit: false,
      currentQuestions: [],
      editingQuestion: null,
      editingQuestionIndex: -1,
      scaleMin: 1,
      scaleMax: 5
    }
  },
  
  computed: {
    canPreviewSurvey() {
      return this.surveyTitle && 
             ((this.selectedType === 'enps' && this.selectedTeamId) ||
              (this.selectedType === '360' && this.selectedEmployeeId)) &&
             this.emailList
    },
    
    emailArray() {
      return this.emailList.split(',').map(email => email.trim()).filter(email => email)
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
    
    previewSurvey() {
      // Load template questions based on survey type
      if (this.selectedType === 'enps') {
        this.currentQuestions = this.getEnpsTemplate()
      } else if (this.selectedType === '360') {
        this.currentQuestions = this.get360Template()
      }
      
      this.showPreview = true
    },
    
    closePreview() {
      this.showPreview = false
    },
    
    editSurvey() {
      this.showPreview = false
    },
    
    async createAndSendSurvey() {
      try {
        const token = localStorage.getItem('token')
        const emails = this.emailArray
        
        const surveyData = {
          survey_type: this.selectedType,
          title: this.surveyTitle,
          team_id: this.selectedTeamId || null,
          target_employee_id: this.selectedEmployeeId || null,
          deadline: this.deadline || null,
          questions: this.currentQuestions
        }
        
        const createResponse = await axios.post('/api/surveys', surveyData, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        const surveyId = createResponse.data.id
        
        await axios.post(`/api/surveys/${surveyId}/send`, { emails }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        alert(this.$t('surveys.surveyCreated'))
        
        this.resetForm()
        this.showPreview = false
        await this.fetchSurveys()
        
      } catch (error) {
        console.error('Error creating survey:', error)
        alert('Ошибка создания опросника')
      }
    },
    
    resetForm() {
      this.selectedType = ''
      this.surveyTitle = ''
      this.selectedTeamId = ''
      this.selectedEmployeeId = ''
      this.deadline = ''
      this.emailList = ''
      this.currentQuestions = []
    },
    
    editQuestion(index) {
      this.editingQuestionIndex = index
      this.editingQuestion = JSON.parse(JSON.stringify(this.currentQuestions[index]))
      
      if (this.editingQuestion.type === 'scale' && this.editingQuestion.scale) {
        this.scaleMin = this.editingQuestion.scale[0]
        this.scaleMax = this.editingQuestion.scale[this.editingQuestion.scale.length - 1]
      }
      
      this.showQuestionEdit = true
    },
    
    closeQuestionEdit() {
      this.showQuestionEdit = false
      this.editingQuestion = null
      this.editingQuestionIndex = -1
    },
    
    saveQuestion() {
      if (this.editingQuestion.type === 'scale') {
        this.editingQuestion.scale = []
        for (let i = this.scaleMin; i <= this.scaleMax; i++) {
          this.editingQuestion.scale.push(i)
        }
      }
      
      this.currentQuestions[this.editingQuestionIndex] = this.editingQuestion
      this.closeQuestionEdit()
    },
    
    addOption() {
      if (!this.editingQuestion.options) {
        this.editingQuestion.options = []
      }
      this.editingQuestion.options.push('')
    },
    
    removeOption(index) {
      this.editingQuestion.options.splice(index, 1)
    },
    
    getTeamName(teamId) {
      const team = this.teams.find(t => t.id == teamId)
      return team ? team.name : ''
    },
    
    getEmployeeName(employeeId) {
      const employee = this.employees.find(e => e.id == employeeId)
      return employee ? employee.name : ''
    },
    
    formatDeadline(deadline) {
      return new Date(deadline).toLocaleString('ru-RU')
    },
    
    getEnpsTemplate() {
      return [
        {"id": 1, "type": "radio", "question": "Укажите ваш формат работы:", "options": ["Офисный", "Удаленный", "Гибридный"], "required": true},
        {"id": 2, "type": "textarea", "question": "Какие шаги, по вашему мнению, компания могла бы предпринять для улучшения вашего опыта работы?", "required": false},
        {"id": 3, "type": "scale", "question": "Насколько вы удовлетворены своим опытом работы в компании?", "scale": [1,2,3,4,5], "required": true},
        {"id": 4, "type": "textarea", "question": "Какие меры, на ваш взгляд, компания могла бы принять, чтобы вы охотнее рекомендовали ее своим друзьям как место для работы?", "required": false},
        {"id": 5, "type": "scale", "question": "Порекомендовали бы вы работать здесь своим друзьям?", "scale": [1,2,3,4,5], "required": true},
        {"id": 6, "type": "scale", "question": "Чувствуете ли вы, что у вас есть возможность расти в этой компании?", "scale": [1,2,3,4,5], "required": true},
        {"id": 7, "type": "textarea", "question": "Какие изменения, по вашему мнению, руководство могло бы внести для улучшения качества рабочих условий сотрудников?", "required": true},
        {"id": 8, "type": "scale", "question": "Считаете ли вы, что у вас есть все ресурсы и инструменты, необходимые для выполнения вашей работы эффективно?", "scale": [1,2,3,4,5], "required": true},
        {"id": 9, "type": "scale", "question": "В какой степени вы чувствуете, что растете внутри компании как эксперт в своей области?", "scale": [1,2,3,4,5], "required": true}
      ]
    },
    
    get360Template() {
      return [
        {"id": 1, "type": "text", "question": "Имя", "required": true},
        {"id": 2, "type": "textarea", "question": "В чем заключаются ключевые личные, профессиональные и лидерские (если применимо) таланты сотрудника?", "required": false},
        {"id": 3, "type": "textarea", "question": "Каковы области личного, профессионального и лидерского (если применимо) совершенствования и развития сотрудника?", "required": false},
        {"id": 4, "type": "textarea", "question": "На основе ваших наблюдений приведите примеры того, как сотрудник развивается личностно, профессионально и как лидер (если применимо).", "required": false},
        {"id": 5, "type": "textarea", "question": "Другие комментарии", "required": false},
        {"id": 6, "type": "matrix", "question": "Оцените", "required": true, "rows": [
          "Межличностные: Предоставление обратной связи",
          "Межличностные: Лидерство (если применимо)", 
          "Социальное: Эффективное общение",
          "Решение проблем: Достижение результатов",
          "Решение проблем: Движущая сила инноваций",
          "Социальное: Сотрудничество (отношение к командной работе)",
          "Профессионал: Ответственность и подотчетность",
          "Профессионал: Профессиональная компетентность",
          "Профессионал: Продуктивность и организация труда",
          "Межличностные: Взаимное уважение"
        ], "scale": ["Требует срочной корректировки", "Требует улучшения", "Соответствует занимаемой должности", "Превосходит ожидания", "Выдающийся результат"]}
      ]
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

.deadline-field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.deadline-label {
  font-weight: bold;
  color: #2c3e50;
}

.deadline-help {
  color: #7f8c8d;
  font-size: 12px;
}

.preview-survey-btn {
  background: #3498db;
  color: white;
  padding: 15px 30px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s ease;
}

.preview-survey-btn:hover:not(:disabled) {
  background: #2980b9;
}

.preview-survey-btn:disabled {
  background: #bdc3c7;
  cursor: not-allowed;
}

.preview-modal, .question-edit-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.preview-content, .question-edit-content {
  background: white;
  border-radius: 12px;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.preview-header, .edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.close-btn:hover {
  color: #e74c3c;
}

.preview-body, .edit-body {
  padding: 20px;
}

.survey-info {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.survey-info p {
  margin: 5px 0;
}

.questions-preview {
  margin-bottom: 20px;
}

.question-preview {
  border: 1px solid #eee;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
}

.question-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.question-number {
  font-weight: bold;
  color: #3498db;
}

.question-text {
  flex: 1;
  font-weight: 500;
}

.required-mark {
  color: #e74c3c;
  font-weight: bold;
}

.edit-question-btn {
  background: #f39c12;
  border: none;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  font-size: 14px;
}

.edit-question-btn:hover {
  background: #e67e22;
}

.question-type-info {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #7f8c8d;
}

.question-type {
  background: #ecf0f1;
  padding: 2px 6px;
  border-radius: 4px;
}

.email-preview {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.email-list {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 10px 0;
}

.email-tag {
  background: #3498db;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
}

.recipient-count {
  font-weight: bold;
  color: #2c3e50;
}

.preview-actions, .edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.edit-btn, .send-btn, .save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: background 0.3s ease;
}

.edit-btn {
  background: #95a5a6;
  color: white;
}

.send-btn, .save-btn {
  background: #2ecc71;
  color: white;
}

.cancel-btn {
  background: #e74c3c;
  color: white;
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
}

.edit-btn:hover {
  background: #7f8c8d;
}

.send-btn:hover, .save-btn:hover {
  background: #27ae60;
}

.cancel-btn:hover {
  background: #c0392b;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
  color: #2c3e50;
}

.question-input {
  width: 100%;
  padding: 10px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
}

.option-input {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
  align-items: center;
}

.option-field {
  flex: 1;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.remove-option-btn {
  background: #e74c3c;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 12px;
  cursor: pointer;
}

.add-option-btn {
  background: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  padding: 8px 16px;
  cursor: pointer;
}

.scale-inputs {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scale-inputs input {
  width: 60px;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  text-align: center;
}
</style>
