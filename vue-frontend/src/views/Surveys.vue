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
            <button
    v-if="canDeleteSelectedTemplate"
    @click="deleteSelectedTemplate"
    class="delete-template-btn"
    title="Удалить выбранный шаблон"
  >
    Удалить шаблон
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
      <div class="surveys-header">
        <h2>Мои опросники</h2>
        <div class="filter-controls">
          <select v-model="statusFilter" class="status-filter">
            <option value="">Все статусы</option>
            <option value="draft">Черновик</option>
            <option value="active">Активные</option>
            <option value="closed">Закрытые</option>
          </select>
        </div>
      </div>
      
      <div v-if="loading" class="loading">⏳ Загрузка...</div>
      
      <div v-else-if="filteredSurveys.length === 0" class="no-surveys">
        Нет опросников
      </div>
      
      <div v-else class="surveys-grid">
        <div v-for="survey in filteredSurveys" :key="survey.id" class="survey-card">
          <div class="survey-header">
            <h3>{{ survey.title }}</h3>
            <div class="survey-badges">
              <span class="survey-type">{{ survey.survey_type.toUpperCase() }}</span>
              <span class="survey-status" :class="survey.status">
                {{ getStatusLabel(survey.status) }}
              </span>
            </div>
          </div>
          
          <div class="survey-info">
            <div class="survey-stats">
              <span>📊 {{ $t('surveys.responses') }}: <strong>{{ survey.response_count }}</strong></span>
              <span v-if="survey.created_at" class="survey-date">
                📅 Создан: {{ formatDate(survey.created_at) }}
              </span>
              <span v-if="survey.deadline" class="survey-deadline">
                ⏰ Дедлайн: {{ formatDate(survey.deadline) }}
              </span>
            </div>
          </div>
          
          <div class="survey-actions">
            <button @click="viewResults(survey.id)" class="view-results-btn" :disabled="survey.response_count === 0">
              📊 {{ $t('surveys.analytics') }}
            </button>
            <button @click="editSurvey(survey)" class="edit-survey-btn">
              ✏️ Редактировать
            </button>
            <button @click="copySurveyLink(survey)" class="copy-link-btn">
              🔗 {{ $t('surveys.copyLink') }}
            </button>
            <button @click="toggleSurveyStatus(survey)" class="toggle-status-btn" :class="survey.status">
              {{ survey.status === 'active' ? '⏸️ Остановить' : '▶️ Активировать' }}
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
    
    <!-- Edit Survey Modal -->
    <div v-if="showEditModal && editingSurvey" class="modal-overlay" @click.self="closeEditModal">
      <div class="modal-content edit-modal">
        <h2>Редактировать опросник</h2>
        <div class="edit-form">
          <div class="form-group">
            <label>Название:</label>
            <input v-model="editingSurvey.title" class="survey-input" />
          </div>
          <div class="form-group">
            <label>Статус:</label>
            <select v-model="editingSurvey.status" class="survey-select">
              <option value="draft">Черновик</option>
              <option value="active">Активен</option>
              <option value="closed">Закрыт</option>
            </select>
          </div>
          <div class="form-group">
            <label>Дедлайн (необязательно):</label>
            <input 
              type="datetime-local" 
              v-model="editingSurvey.deadline" 
              class="survey-input"
              :value="editingSurvey.deadline ? new Date(editingSurvey.deadline).toISOString().slice(0, 16) : ''"
            />
          </div>
        </div>
        <div class="modal-actions">
          <button @click="saveSurveyChanges" class="save-btn">Сохранить</button>
          <button @click="closeEditModal" class="cancel-btn">Отмена</button>
        </div>
      </div>
    </div>
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
      previewQuestions: [],
      statusFilter: '',
      editingSurvey: null,
      showEditModal: false
    }
  },
  
  computed: {
    canCreateSurvey() {
      return this.surveyTitle && 
             (!this.useTeamSelection || this.selectedTeamId) &&
             (!this.useEmployeeSelection || this.selectedEmployeeId)
    },
    currentTemplate() {
    if (!this.selectedTemplateId) return null
    return this.availableTemplates.find(t => t.id == this.selectedTemplateId) || null
  },

  // удобно для кнопки удаления
  canDeleteSelectedTemplate() {
    return !!(this.currentTemplate && !this.currentTemplate.is_default)
  },
    
    filteredSurveys() {
      if (!this.statusFilter) return this.surveys
      return this.surveys.filter(s => s.status === this.statusFilter)
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

    async deleteSelectedTemplate() {
  if (!this.canDeleteSelectedTemplate) return

  const tpl = this.currentTemplate
  const ok = window.confirm(`Удалить шаблон «${tpl.name}»? Это действие необратимо.`)
  if (!ok) return

  try {
    const token = localStorage.getItem('token')
    await axios.delete(`/api/survey-templates/${tpl.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // сбрасываем выбор и обновляем список шаблонов
    this.selectedTemplateId = ''
    await this.fetchTemplates()
    alert('Шаблон удалён')
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.error || 'Ошибка удаления'
    if (status === 400 && /Default/i.test(msg)) {
      alert('Дефолтные шаблоны удалять нельзя.')
    } else if (status === 404) {
      alert('Шаблон не найден или у вас нет прав.')
    } else {
      alert(msg)
    }
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
    },
    
    editSurvey(survey) {
      this.editingSurvey = { ...survey }
      this.showEditModal = true
    },
    
    async saveSurveyChanges() {
      try {
        const token = localStorage.getItem('token')
        await axios.put(`/api/surveys/${this.editingSurvey.id}`, {
          title: this.editingSurvey.title,
          status: this.editingSurvey.status,
          deadline: this.editingSurvey.deadline || null
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        await this.fetchSurveys()
        this.showEditModal = false
        this.editingSurvey = null
        alert('Опросник обновлен!')
      } catch (error) {
        console.error('Error updating survey:', error)
        alert('Ошибка обновления опросника')
      }
    },
    
    async toggleSurveyStatus(survey) {
      try {
        const token = localStorage.getItem('token')
        const newStatus = survey.status === 'active' ? 'closed' : 'active'
        
        await axios.put(`/api/surveys/${survey.id}`, {
          status: newStatus
        }, {
          headers: { Authorization: `Bearer ${token}` }
        })
        
        await this.fetchSurveys()
        alert(`Опросник ${newStatus === 'active' ? 'активирован' : 'остановлен'}!`)
      } catch (error) {
        console.error('Error toggling survey status:', error)
        alert('Ошибка изменения статуса')
      }
    },
    
    getStatusLabel(status) {
      const labels = {
        'draft': 'Черновик',
        'active': 'Активен',
        'closed': 'Закрыт'
      }
      return labels[status] || status
    },
    
    formatDate(dateString) {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleDateString('ru-RU', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      })
    },
    
    closeEditModal() {
      this.showEditModal = false
      this.editingSurvey = null
    }
  }
}
</script>

<style scoped>
.surveys-container {
  max-width: 1280px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

h2 {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 24px;
  color: #111827;
}

.survey-type-selection {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-bottom: 32px;
}

.survey-type-card {
  border: 2px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
}

.survey-type-card:hover {
  border-color: #3b82f6;
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.15);
}

.survey-type-card.active {
  border-color: #10b981;
  background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
}

.survey-type-card h3 {
  font-size: 20px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 8px;
}

.survey-type-card p {
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}

.survey-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 600px;
  margin-bottom: 32px;
}

.survey-input, .survey-select, .survey-textarea {
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  color: #111827;
  line-height: 1.5;
}

.survey-input::placeholder,
.survey-textarea::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.survey-input:hover, .survey-select:hover, .survey-textarea:hover {
  border-color: #cbd5e1;
}

.survey-input:focus, .survey-select:focus, .survey-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12), 0 2px 8px rgba(59, 130, 246, 0.08);
  background: #fafbff;
}

.survey-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  padding-right: 44px;
}

.survey-textarea {
  min-height: 100px;
  line-height: 1.6;
}

.create-survey-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.create-survey-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.create-survey-btn:disabled {
  background: linear-gradient(135deg, #9ca3af 0%, #6b7280 100%);
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
  box-shadow: none;
}

.surveys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
}

.survey-card {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.survey-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: #d1d5db;
}

.survey-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.survey-header h3 {
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.survey-type {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.survey-info {
  margin-bottom: 16px;
}

.survey-stats {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 13px;
  color: #6b7280;
}

.survey-date, .survey-deadline {
  font-size: 12px;
  color: #9ca3af;
}

.survey-status {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
}

.survey-status.draft {
  background: #f3f4f6;
  color: #6b7280;
}

.survey-status.active {
  background: #dcfce7;
  color: #16a34a;
}

.survey-status.closed {
  background: #fee2e2;
  color: #dc2626;
}

.survey-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.view-results-btn, .copy-link-btn, .delete-survey-btn {
  flex: 1;
  min-width: 100px;
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  font-family: inherit;
}

.view-results-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.copy-link-btn {
  background: #6b7280;
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.delete-survey-btn {
  background: #ef4444;
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.view-results-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.copy-link-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
}

.delete-survey-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.template-selection {
  margin-bottom: 20px;
}

.template-selection label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.edit-template-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
  margin-left: 12px;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.edit-template-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
}

.optional-selection {
  margin-bottom: 20px;
}

.optional-selection label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.optional-selection input[type="checkbox"] {
  margin: 0;
  width: 18px;
  height: 18px;
  cursor: pointer;
}

@media (max-width: 768px) {
  .surveys-container {
    margin: 20px 10px !important;
    padding: 24px 20px !important;
  }
  
  .survey-type-selection {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .surveys-grid {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .survey-actions {
    flex-direction: column;
  }
  
  .view-results-btn, .copy-link-btn, .delete-survey-btn, .edit-survey-btn, .toggle-status-btn {
    width: 100%;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.edit-modal {
  background: white;
  padding: 32px;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.edit-modal h2 {
  margin-top: 0;
  margin-bottom: 24px;
  font-size: 24px;
  color: #111827;
}

.edit-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-bottom: 24px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.save-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  min-width: 120px;
}

.save-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.save-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.cancel-btn {
  background: #ffffff;
  color: #374151;
  border: 2px solid #e5e7eb;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.cancel-btn:hover {
  background: #f9fafb;
  border-color: #d1d5db;
  transform: translateY(-1px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}
</style>
