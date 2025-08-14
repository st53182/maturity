<template>
  <div class="surveys-container">
    <h1>📋 {{ $t('surveys.title') }}</h1>
    
    <div class="create-survey-section">
      <h2>{{ $t('surveys.createSurvey') }}</h2>
      
      <div class="survey-type-selection">
        <div class="survey-type-card" 
             :class="{ active: selectedType === 'enps' }"
             @click="selectSurveyType('enps')">
          <h3>📊 {{ $t('surveys.enpsTitle') }}</h3>
          <p>Собрать обратную связь от сотрудников о текущем состоянии в команде</p>
        </div>
        
        <div class="survey-type-card"
             :class="{ active: selectedType === '360' }"
             @click="selectSurveyType('360')">
          <h3>🔄 {{ $t('surveys.feedback360Title') }}</h3>
          <p>Собрать анонимную обратную связь о конкретном сотруднике от коллег</p>
        </div>
      </div>
      
      <div v-if="selectedType" class="survey-form">
        <input v-model="surveyTitle" 
               :placeholder="$t('surveys.surveyTitle')" 
               class="survey-input" />
        
        <!-- Template Selection -->
        <div class="template-selection">
          <label>Выберите шаблон:</label>
          <select v-model="selectedTemplateId" class="survey-select">
            <option value="">Стандартный шаблон</option>
            <option v-for="template in availableTemplates" :key="template.id" :value="template.id">
              {{ template.name }}
            </option>
          </select>
          <button @click="editTemplate" class="edit-template-btn">
            {{ selectedTemplateId ? 'Редактировать' : 'Создать свой' }}
          </button>
        </div>
        
        <!-- Optional Team Selection -->
        <div class="optional-selection">
          <label>
            <input type="checkbox" v-model="useTeamSelection" />
            Привязать к команде
          </label>
          <select v-if="useTeamSelection && selectedType === 'enps'" 
                  v-model="selectedTeamId" 
                  class="survey-select">
            <option value="">{{ $t('surveys.selectTeam') }}</option>
            <option v-for="team in teams" :key="team.id" :value="team.id">
              {{ team.name }}
            </option>
          </select>
        </div>
        
        <!-- Optional Employee Selection -->
        <div class="optional-selection">
          <label>
            <input type="checkbox" v-model="useEmployeeSelection" />
            Привязать к сотруднику
          </label>
          <select v-if="useEmployeeSelection && selectedType === '360'" 
                  v-model="selectedEmployeeId" 
                  class="survey-select">
            <option value="">{{ $t('surveys.selectEmployee') }}</option>
            <option v-for="employee in employees" :key="employee.id" :value="employee.id">
              {{ employee.name }}
            </option>
          </select>
        </div>
        
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
            <button @click="confirmDeleteSurvey(survey)" class="delete-survey-btn">
              🗑️ Удалить
            </button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Template Editor Modal -->
    <TemplateEditor 
      :show="showTemplateEditor"
      :template="editingTemplate"
      :survey-type="selectedType"
      @close="closeTemplateEditor"
      @saved="onTemplateSaved"
    />
    
    <QuestionPreview 
      :show="showQuestionPreview"
      :questions="previewQuestions"
      :survey-title="surveyTitle"
      :survey-type="selectedType"
      @close="showQuestionPreview = false"
      @edit-questions="openTemplateEditor"
      @confirm-create="confirmCreateSurvey" />
  </div>
</template>

<script>
import axios from 'axios'
import TemplateEditor from '@/components/TemplateEditor.vue'
import QuestionPreview from '@/components/QuestionPreview.vue'

export default {
  name: 'SurveyList',
  components: {
    TemplateEditor,
    QuestionPreview
  },
  data() {
    return {
      selectedType: '',
      surveyTitle: '',
      selectedTeamId: '',
      selectedEmployeeId: '',
      selectedTemplateId: '',
      useTeamSelection: false,
      useEmployeeSelection: false,
      teams: [],
      employees: [],
      surveys: [],
      availableTemplates: [],
      loading: false,
      showTemplateEditor: false,
      editingTemplate: null,
      showQuestionPreview: false,
      previewQuestions: []
    }
  },
  
  computed: {
    canCreateSurvey() {
      return this.surveyTitle && 
             (!this.useTeamSelection || this.selectedTeamId) &&
             (!this.useEmployeeSelection || this.selectedEmployeeId)
    }
  },
  
  async mounted() {
    await this.fetchTeams()
    await this.fetchEmployees()
    await this.fetchSurveys()
  },
  
  methods: {
    selectSurveyType(type) {
      this.selectedType = type
      this.selectedTeamId = ''
      this.selectedEmployeeId = ''
      this.selectedTemplateId = ''
      this.useTeamSelection = false
      this.useEmployeeSelection = false
      
      this.fetchTemplates()
      
      if (type === 'enps') {
        this.fetchTeams()
      } else if (type === '360') {
        this.fetchEmployees()
      }
    },

    async fetchTemplates() {
      try {
        const token = localStorage.getItem('token')
        const response = await axios.get('/api/survey-templates', {
          headers: { Authorization: `Bearer ${token}` }
        })
        this.availableTemplates = response.data.filter(t => 
          t.survey_type === this.selectedType
        )
      } catch (error) {
        console.error('Error fetching templates:', error)
      }
    },
    
    editTemplate() {
      console.log('editTemplate called with selectedTemplateId:', this.selectedTemplateId)
      console.log('availableTemplates:', this.availableTemplates)
      
      if (this.selectedTemplateId) {
        this.editingTemplate = this.availableTemplates.find(t => t.id == this.selectedTemplateId)
        console.log('Found template for editing:', this.editingTemplate)
      } else {
        this.editingTemplate = null
        console.log('No template selected, creating new template')
      }
      this.showTemplateEditor = true
    },
    
    closeTemplateEditor() {
      this.showTemplateEditor = false
      this.editingTemplate = null
    },
    
    async onTemplateSaved() {
      await this.fetchTemplates()
    },

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
      let questions = null
      if (this.selectedTemplateId) {
        const template = this.availableTemplates.find(t => t.id === this.selectedTemplateId)
        questions = template.questions
      } else {
        questions = this.selectedType === 'enps' ? this.getDefaultEnpsQuestions() : this.getDefault360Questions()
      }
      
      this.previewQuestions = questions
      this.showQuestionPreview = true
    },

    async confirmCreateSurvey() {
      try {
        const token = localStorage.getItem('token')
        
        const surveyData = {
          survey_type: this.selectedType,
          title: this.surveyTitle,
          team_id: this.useTeamSelection ? this.selectedTeamId : null,
          target_employee_id: this.useEmployeeSelection ? this.selectedEmployeeId : null,
          questions: this.previewQuestions
        }
        
        const createResponse = await axios.post('/api/surveys', surveyData, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        const surveyToken = createResponse.data.access_token
        const link = `${window.location.origin}/survey/${surveyToken}`
        
        try {
          await navigator.clipboard.writeText(link)
          alert(`${this.$t('surveys.surveyCreated')}\n\nСсылка скопирована в буфер обмена!`)
        } catch (clipboardError) {
          console.error('Clipboard error:', clipboardError)
          alert(`${this.$t('surveys.surveyCreated')}\n\nСсылка: ${link}`)
        }
        
        this.resetForm()
        this.showQuestionPreview = false
        await this.fetchSurveys()
        
      } catch (error) {
        console.error('Error creating survey:', error)
        alert('Ошибка создания опросника')
      }
    },
    
    confirmDeleteSurvey(survey) {
      if (confirm(`Вы уверены, что хотите удалить опросник "${survey.title}"?`)) {
        this.deleteSurvey(survey.id)
      }
    },
    
    async deleteSurvey(surveyId) {
      try {
        const token = localStorage.getItem('token')
        await axios.delete(`/api/surveys/${surveyId}`, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        alert('Опросник удален!')
        await this.fetchSurveys()
      } catch (error) {
        console.error('Error deleting survey:', error)
        alert('Ошибка удаления опросника')
      }
    },
    
    resetForm() {
      this.selectedType = ''
      this.surveyTitle = ''
      this.selectedTeamId = ''
      this.selectedEmployeeId = ''
      this.selectedTemplateId = ''
      this.useTeamSelection = false
      this.useEmployeeSelection = false
      this.previewQuestions = []
    },

    getDefaultEnpsQuestions() {
      return [
        {
          "id": 1,
          "type": "radio",
          "question": "В каком формате вы работаете?",
          "required": true,
          "options": [
            {"text": "Удаленно", "value": "remote"},
            {"text": "В офисе", "value": "office"},
            {"text": "Гибридно", "value": "hybrid"}
          ]
        },
        {
          "id": 2,
          "type": "scale",
          "question": "Насколько вы удовлетворены своей работой?",
          "required": true,
          "min": 1,
          "max": 10
        },
        {
          "id": 3,
          "type": "scale",
          "question": "Насколько вероятно, что вы порекомендуете нашу компанию как место работы друзьям или коллегам?",
          "required": true,
          "min": 0,
          "max": 10
        },
        {
          "id": 4,
          "type": "scale",
          "question": "Насколько вы удовлетворены балансом работы и личной жизни?",
          "required": true,
          "min": 1,
          "max": 10
        },
        {
          "id": 5,
          "type": "scale",
          "question": "Насколько вы удовлетворены возможностями профессионального развития?",
          "required": true,
          "min": 1,
          "max": 10
        },
        {
          "id": 6,
          "type": "scale",
          "question": "Насколько вы удовлетворены отношениями с коллегами?",
          "required": true,
          "min": 1,
          "max": 10
        },
        {
          "id": 7,
          "type": "scale",
          "question": "Насколько вы удовлетворены управлением и руководством?",
          "required": true,
          "min": 1,
          "max": 10
        },
        {
          "id": 8,
          "type": "textarea",
          "question": "Что вам больше всего нравится в работе в нашей компании?",
          "required": false
        },
        {
          "id": 9,
          "type": "textarea",
          "question": "Что бы вы хотели улучшить в нашей компании?",
          "required": false
        }
      ]
    },

    getDefault360Questions() {
      return [
        {
          "id": 1,
          "type": "text",
          "question": "Ваше имя (необязательно)",
          "required": false
        },
        {
          "id": 2,
          "type": "text",
          "question": "Ваша роль/должность",
          "required": false
        },
        {
          "id": 3,
          "type": "radio",
          "question": "Ваши отношения с оцениваемым сотрудником",
          "required": true,
          "options": [
            {"text": "Руководитель", "value": "manager"},
            {"text": "Коллега", "value": "peer"},
            {"text": "Подчиненный", "value": "subordinate"},
            {"text": "Клиент/Партнер", "value": "external"}
          ]
        },
        {
          "id": 4,
          "type": "matrix",
          "question": "Оцените компетенции сотрудника по шкале от 1 до 5",
          "required": true,
          "rows": [
            {"text": "Профессиональные навыки", "value": "professional_skills"},
            {"text": "Коммуникация", "value": "communication"},
            {"text": "Лидерство", "value": "leadership"},
            {"text": "Работа в команде", "value": "teamwork"},
            {"text": "Решение проблем", "value": "problem_solving"},
            {"text": "Адаптивность", "value": "adaptability"}
          ],
          "columns": [
            {"text": "1 - Неудовлетворительно", "value": "1"},
            {"text": "2 - Ниже ожиданий", "value": "2"},
            {"text": "3 - Соответствует ожиданиям", "value": "3"},
            {"text": "4 - Превышает ожидания", "value": "4"},
            {"text": "5 - Выдающийся результат", "value": "5"}
          ]
        },
        {
          "id": 5,
          "type": "textarea",
          "question": "Что является главными сильными сторонами этого сотрудника?",
          "required": false
        },
        {
          "id": 6,
          "type": "textarea",
          "question": "В каких областях сотрудник мог бы улучшиться?",
          "required": false
        }
      ]
    },

    openTemplateEditor() {
      this.showQuestionPreview = false
      this.editingTemplate = {
        name: `Кастомный ${this.selectedType.toUpperCase()} шаблон`,
        survey_type: this.selectedType,
        questions: this.previewQuestions
      }
      this.showTemplateEditor = true
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

.view-results-btn, .copy-link-btn, .delete-survey-btn {
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

.delete-survey-btn {
  background: #dc3545;
  color: white;
}

.view-results-btn:hover {
  background: #2980b9;
}

.copy-link-btn:hover {
  background: #7f8c8d;
}

.delete-survey-btn:hover {
  background: #c82333;
}

.template-selection {
  margin-bottom: 1rem;
}

.template-selection label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: bold;
}

.edit-template-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-left: 0.5rem;
}

.edit-template-btn:hover {
  background: #5a6268;
}

.optional-selection {
  margin-bottom: 1rem;
}

.optional-selection label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.optional-selection input[type="checkbox"] {
  margin: 0;
}
</style>
