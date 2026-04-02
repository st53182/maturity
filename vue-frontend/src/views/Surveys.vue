<template>
  <div class="surveys-shell">
    <div class="surveys-container">
    <header class="page-head">
      <div>
        <h1 class="page-title">{{ $t('surveys.title') }}</h1>
        <p class="page-sub">{{ $t('surveys.hr.pageLead') }}</p>
      </div>
    </header>
    
    <div class="create-survey-section">
      <h2 class="create-section-title">{{ $t('surveys.createSurvey') }}</h2>
      
      <p class="step-label step-label--outer">{{ $t('surveys.hr.step1Title') }}</p>
      <div class="survey-type-selection">
        <div class="survey-type-card" 
             :class="{ active: selectedType === 'enps' }"
             @click="selectSurveyType('enps')">
          <h3>📊 {{ $t('surveys.enpsTitle') }}</h3>
          <p class="survey-type-card__lead">{{ $t('surveys.hr.enpsShort') }}</p>
          <ul class="survey-type-card__bullets">
            <li v-for="(b, i) in enpsWhenBullets" :key="'enps-' + i">{{ b }}</li>
          </ul>
        </div>
        
        <div class="survey-type-card"
             :class="{ active: selectedType === '360' }"
             @click="selectSurveyType('360')">
          <h3>🔄 {{ $t('surveys.feedback360Title') }}</h3>
          <p class="survey-type-card__lead">{{ $t('surveys.hr.feedback360Short') }}</p>
          <ul class="survey-type-card__bullets">
            <li v-for="(b, i) in feedback360WhenBullets" :key="'360-' + i">{{ b }}</li>
          </ul>
        </div>
      </div>
      
      <div v-if="selectedType" class="survey-create-frame">
        <section class="survey-create-intro" aria-labelledby="survey-create-intro-title">
          <h3 id="survey-create-intro-title" class="survey-create-intro__title">{{ $t('surveys.hr.introTitle') }}</h3>
          <p class="survey-create-intro__lead">
            {{ $t('surveys.hr.introScenario') }}
          </p>
          <div class="survey-create-intro__toolbar">
            <div
              class="ai-assistant-badge"
              tabindex="0"
              @mouseenter="showSurveyAiPopover = true"
              @mouseleave="showSurveyAiPopover = false"
              @focusin="showSurveyAiPopover = true"
              @focusout="showSurveyAiPopover = false"
            >
              <span class="ai-assistant-badge__icon" aria-hidden="true">✨</span>
              <span>{{ $t('surveys.hr.aiBadgeLabel') }}</span>
              <div v-show="showSurveyAiPopover" class="ai-popover-survey" role="tooltip">
                <p>{{ $t('surveys.hr.aiPopover1') }}</p>
                <p>{{ $t('surveys.hr.aiPopover2') }}</p>
              </div>
            </div>
          </div>
        </section>

        <div class="survey-form survey-form--framed">
          <p class="step-label step-label--in">{{ $t('surveys.hr.step2Title') }}</p>
          <div class="stacked-field">
            <label class="stacked-field-label" for="survey-title-input">{{ $t('surveys.hr.surveyNameLabel') }}</label>
            <input
              id="survey-title-input"
              v-model="surveyTitle"
              :placeholder="$t('surveys.surveyTitle')"
              class="survey-input"
            />
          </div>

          <div class="optional-block">
            <h4 class="optional-block__title">{{ $t('surveys.hr.optionalBlockTitle') }}</h4>
            <p class="optional-block__lead">{{ $t('surveys.hr.optionalBlockLead') }}</p>
            <div class="optional-selection">
              <label>
                <input type="checkbox" v-model="useTeamSelection" />
                {{ $t('surveys.hr.linkTeam') }}
              </label>
              <p v-if="selectedType === 'enps'" class="optional-hint">{{ $t('surveys.hr.teamLinkHint') }}</p>
              <select v-if="useTeamSelection && selectedType === 'enps'" 
                      v-model="selectedTeamId" 
                      class="survey-select">
                <option value="">{{ $t('surveys.selectTeam') }}</option>
                <option v-for="team in teams" :key="team.id" :value="team.id">
                  {{ team.name }}
                </option>
              </select>
            </div>
            <div class="optional-selection">
              <label>
                <input type="checkbox" v-model="useEmployeeSelection" />
                {{ $t('surveys.hr.linkEmployee') }}
              </label>
              <p v-if="selectedType === '360'" class="optional-hint">{{ $t('surveys.hr.employeeLinkHint') }}</p>
              <select v-if="useEmployeeSelection && selectedType === '360'" 
                      v-model="selectedEmployeeId" 
                      class="survey-select">
                <option value="">{{ $t('surveys.selectEmployee') }}</option>
                <option v-for="employee in employees" :key="employee.id" :value="employee.id">
                  {{ employee.name }}
                </option>
              </select>
            </div>
          </div>

          <p class="step-label step-label--in">{{ $t('surveys.hr.step3Title') }}</p>
          <div class="template-subcard">
            <h4 class="template-subcard__title">{{ $t('surveys.hr.templateBlockTitle') }}</h4>
            <p class="template-subcard__hint template-subcard__glossary">
              {{ $t('surveys.hr.glossary') }}
            </p>
            <label class="stacked-field-label" for="survey-template-select">{{ $t('surveys.hr.selectTemplateLabel') }}</label>
            <select id="survey-template-select" v-model="selectedTemplateId" class="survey-select">
              <option value="">{{ $t('surveys.hr.standardTemplate') }}</option>
              <option v-for="template in availableTemplates" :key="template.id" :value="template.id">
                {{ template.name }}
              </option>
            </select>

            <div class="template-action-grid">
              <div class="template-action-card">
                <div class="template-action-card__head">
                  <span class="template-action-card__badge">1</span>
                  <strong>{{ $t('surveys.hr.cardEditorTitle') }}</strong>
                </div>
                <p class="template-action-card__text">
                  {{ $t('surveys.hr.cardEditorBody') }}
                </p>
                <button type="button" class="template-action-card__btn primary" @click="editTemplate">
                  {{ $t('surveys.hr.cardEditorBtn') }}
                </button>
              </div>

              <div class="template-action-card">
                <div class="template-action-card__head">
                  <span class="template-action-card__badge">2</span>
                  <strong>{{ $t('surveys.hr.cardCopyTitle') }}</strong>
                </div>
                <p class="template-action-card__text">
                  {{ $t('surveys.hr.cardCopyBody') }}
                </p>
                <button
                  type="button"
                  class="template-action-card__btn secondary"
                  :disabled="!selectedType"
                  @click="createTemplateFromBase"
                >
                  {{ $t('surveys.hr.cardCopyBtn') }}
                </button>
              </div>

              <div class="template-action-card template-action-card--ai">
                <div class="template-action-card__head">
                  <span class="template-action-card__badge template-action-card__badge--ai">✨</span>
                  <strong>{{ $t('surveys.hr.cardAiTitle') }}</strong>
                </div>
                <p class="template-action-card__text">
                  {{ $t('surveys.hr.cardAiBody') }}
                </p>
                <button type="button" class="template-action-card__btn ai" @click="openAiDraftModal">
                  {{ $t('surveys.hr.cardAiBtn') }}
                </button>
              </div>
            </div>

            <div v-if="canDeleteSelectedTemplate" class="template-delete-row">
              <button
                type="button"
                class="delete-template-btn"
                :title="$t('surveys.hr.deleteTemplateBtn')"
                @click="deleteSelectedTemplate"
              >
                {{ $t('surveys.hr.deleteTemplateBtn') }}
              </button>
            </div>
          </div>

          <button
            type="button"
            @click="createSurvey"
            :disabled="!canCreateSurvey"
            class="create-survey-btn create-survey-btn--wide"
          >
            {{ $t('surveys.hr.createSurveyBtn') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Модальное окно: черновик вопросов с ИИ -->
    <div v-if="showAiDraftModal" class="modal-overlay" @click.self="closeAiDraftModal">
      <div class="modal-content survey-ai-modal">
        <button type="button" class="modal-close-top" aria-label="Закрыть" @click="closeAiDraftModal">✕</button>
        <h2>{{ $t('surveys.hr.aiModalTitle') }}</h2>
        <p class="survey-ai-lead">
          {{ $t('surveys.hr.aiModalLead') }}
        </p>
        <div class="modern-form-block">
          <label for="ai-brief" class="stacked-field-label">{{ $t('surveys.hr.aiBriefLabel') }}</label>
          <textarea
            id="ai-brief"
            v-model="aiDraftBrief"
            class="survey-textarea survey-ai-textarea"
            rows="6"
            :placeholder="$t('surveys.hr.aiBriefPlaceholder')"
          />
        </div>
        <p v-if="aiDraftError" class="survey-ai-error">{{ aiDraftError }}</p>
        <div class="modal-actions survey-ai-actions">
          <button type="button" class="cancel-btn" :disabled="aiDraftLoading" @click="closeAiDraftModal">{{ $t('surveys.hr.aiCancel') }}</button>
          <button type="button" class="save-btn" :disabled="aiDraftLoading || (aiDraftBrief || '').trim().length < 20" @click="generateAiDraft">
            {{ aiDraftLoading ? $t('surveys.hr.aiGenerating') : $t('surveys.hr.aiGenerate') }}
          </button>
        </div>
      </div>
    </div>

    <section v-if="createdLink" class="invite-card" aria-label="invite">
      <h2 class="invite-title">Готово: ссылка и текст для email</h2>
      <div class="invite-grid">
        <div class="invite-field">
          <label class="invite-label">Ссылка</label>
          <div class="invite-row">
            <input class="survey-input mono" :value="createdLink" readonly />
            <button type="button" class="copy-btn" @click="copyText(createdLink)">Копировать</button>
          </div>
        </div>
        <div class="invite-field">
          <label class="invite-label">Текст письма</label>
          <textarea class="survey-textarea" rows="6" :value="createdEmailText" readonly />
          <div class="invite-row">
            <button type="button" class="copy-btn" @click="copyText(createdEmailText)">Копировать текст</button>
            <span v-if="copiedMsg" class="copied-msg">{{ copiedMsg }}</span>
          </div>
        </div>
      </div>
      <p class="invite-hint">Вставьте текст в email/мессенджер и отправьте участникам.</p>
    </section>
    
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
        <button class="modal-close-top" @click="closeEditModal" aria-label="Close">✕</button>
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
      showEditModal: false,
      createdLink: '',
      createdEmailText: '',
      copiedMsg: '',
      showSurveyAiPopover: false,
      showAiDraftModal: false,
      aiDraftBrief: '',
      aiDraftLoading: false,
      aiDraftError: ''
    }
  },
  
  computed: {
    enpsWhenBullets() {
      const m = this.$tm('surveys.hr.enpsWhenBullets')
      return Array.isArray(m) ? m : []
    },
    feedback360WhenBullets() {
      const m = this.$tm('surveys.hr.feedback360WhenBullets')
      return Array.isArray(m) ? m : []
    },
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
      if (this.selectedTemplateId) {
        this.editingTemplate = this.availableTemplates.find(t => t.id == this.selectedTemplateId)
      } else {
        const q =
          this.selectedType === 'enps'
            ? this.getDefaultEnpsQuestions()
            : this.getDefault360Questions()
        this.editingTemplate = {
          name: '',
          survey_type: this.selectedType,
          questions: JSON.parse(JSON.stringify(q))
        }
      }
      this.showTemplateEditor = true
    },

    openAiDraftModal() {
      this.aiDraftError = ''
      this.aiDraftBrief = ''
      this.showAiDraftModal = true
    },

    closeAiDraftModal() {
      if (this.aiDraftLoading) return
      this.showAiDraftModal = false
      this.aiDraftError = ''
    },

    async generateAiDraft() {
      const brief = (this.aiDraftBrief || '').trim()
      if (brief.length < 20) {
        this.aiDraftError = 'Нужно не менее 20 символов описания.'
        return
      }
      this.aiDraftLoading = true
      this.aiDraftError = ''
      try {
        const token = localStorage.getItem('token')
        const { data } = await axios.post(
          '/api/survey-templates/ai-draft',
          { survey_type: this.selectedType, brief },
          { headers: { Authorization: `Bearer ${token}` } }
        )
        const questions = data?.questions
        if (!Array.isArray(questions) || !questions.length) {
          this.aiDraftError = 'Не удалось получить вопросы. Попробуйте ещё раз.'
          return
        }
        const stamp = new Date().toLocaleDateString('ru-RU')
        this.editingTemplate = {
          name: `Черновик ИИ — ${stamp}`,
          survey_type: this.selectedType,
          questions
        }
        this.showAiDraftModal = false
        this.showTemplateEditor = true
      } catch (e) {
        const msg = e?.response?.data?.error || e?.message || 'Ошибка запроса'
        this.aiDraftError = msg
        if (e?.response?.status === 429) {
          this.aiDraftError = 'Лимит AI-запросов на месяц исчерпан. Попробуйте позже.'
        }
      } finally {
        this.aiDraftLoading = false
      }
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

    buildInviteEmailText({ link, type, title, deadline }) {
      const kind = type === '360' ? '360° обратная связь' : 'eNPS';
      const dline = deadline ? `\nДедлайн: ${this.formatDate(deadline)}` : '';
      const t = (title || '').trim();
      const titleLine = t ? `Опрос: ${t}\n` : '';
      return (
        `${titleLine}Коллеги, пожалуйста, пройдите опрос (${kind}).` +
        `${dline}\n\nСсылка:\n${link}\n\nСпасибо!`
      );
    },

    async copyText(text) {
      try {
        await navigator.clipboard.writeText(String(text || ''));
        this.copiedMsg = 'Скопировано';
        window.setTimeout(() => (this.copiedMsg = ''), 2000);
      } catch {
        this.copiedMsg = 'Не удалось скопировать';
        window.setTimeout(() => (this.copiedMsg = ''), 2000);
      }
    },

    async createTemplateFromBase() {
      if (!this.selectedType) return;
      const token = localStorage.getItem('token');
      const base =
        (this.currentTemplate && this.currentTemplate.questions) ||
        (this.selectedType === 'enps' ? this.getDefaultEnpsQuestions() : this.getDefault360Questions());
      const baseName = this.currentTemplate ? this.currentTemplate.name : 'Стандартный шаблон';
      const name = window.prompt('Название нового шаблона', `Мой шаблон (копия: ${baseName})`);
      if (!name) return;
      try {
        const resp = await axios.post(
          '/api/survey-templates',
          { name, survey_type: this.selectedType, questions: base },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        await this.fetchTemplates();
        const newId = resp?.data?.id;
        if (newId != null) this.selectedTemplateId = String(newId);
        alert('Шаблон создан');
      } catch (e) {
        alert(e?.response?.data?.error || 'Ошибка создания шаблона');
      }
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
        this.createdLink = link
        this.createdEmailText = this.buildInviteEmailText({
          link,
          type: this.selectedType,
          title: this.surveyTitle,
          deadline: null
        })
        
        try {
          await navigator.clipboard.writeText(link)
          this.copiedMsg = 'Ссылка скопирована'
          window.setTimeout(() => (this.copiedMsg = ''), 2000)
        } catch (clipboardError) {
          console.error('Clipboard error:', clipboardError)
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
.surveys-shell {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px 48px;
  background: linear-gradient(180deg, rgba(247, 249, 255, 0.95) 0%, rgba(255, 255, 255, 0.45) 50%);
}

.surveys-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 28px;
  background: rgba(255, 255, 255, 0.96);
  border-radius: 20px;
  border: 1px solid rgba(10, 20, 45, 0.06);
  box-shadow: 0 20px 60px rgba(10, 20, 45, 0.08);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-title {
  font-size: 28px;
  font-weight: 750;
  margin: 0 0 6px 0;
  color: rgba(10, 20, 45, 0.92);
  letter-spacing: -0.02em;
}

.page-sub {
  margin: 0;
  color: #64748b;
  font-size: 14px;
  line-height: 1.5;
}

.create-section-title {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 20px;
  color: #0f172a;
  letter-spacing: -0.02em;
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

.step-label {
  font-size: 13px;
  font-weight: 700;
  margin: 0 0 12px;
  color: #0f172a;
  letter-spacing: 0.02em;
}

.step-label--outer {
  margin-top: 8px;
}

.step-label--in {
  margin-top: 8px;
}

.survey-type-card__lead {
  margin: 0 0 10px;
  font-size: 14px;
  color: #475569;
  line-height: 1.55;
}

.survey-type-card__bullets {
  margin: 0;
  padding-left: 1.15rem;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.survey-type-card__bullets li {
  margin-bottom: 6px;
}

.optional-block__lead {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.optional-hint {
  margin: 6px 0 10px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.45;
}

.template-subcard__glossary {
  font-size: 13px;
  color: #475569;
  line-height: 1.55;
}

.survey-create-frame {
  margin-top: 8px;
}

.survey-create-intro {
  margin-bottom: 20px;
  padding: 22px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.survey-create-intro__title {
  font-size: 1.15rem;
  margin: 0 0 10px;
  color: #0c4a6e;
  font-weight: 700;
}

.survey-create-intro__lead {
  margin: 0 0 14px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.survey-create-intro__toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.ai-assistant-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: #fff;
  border: 1px solid #7dd3fc;
  color: #0369a1;
  font-size: 13px;
  font-weight: 600;
  cursor: default;
}

.ai-assistant-badge__icon {
  font-size: 15px;
}

.ai-popover-survey {
  position: absolute;
  z-index: 20;
  left: 0;
  top: calc(100% + 8px);
  min-width: 260px;
  max-width: 320px;
  padding: 12px 14px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 12px 40px rgba(15, 23, 42, 0.12);
  font-size: 13px;
  color: #475569;
  line-height: 1.5;
}

.ai-popover-survey p {
  margin: 0 0 8px;
}

.ai-popover-survey p:last-child {
  margin-bottom: 0;
}

.survey-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
  max-width: 720px;
  margin-bottom: 32px;
}

.survey-form--framed {
  padding: 24px 22px 26px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fff;
  box-shadow: 0 10px 40px rgba(15, 23, 42, 0.06);
}

.stacked-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stacked-field-label {
  font-size: 13px;
  font-weight: 650;
  color: #334155;
}

.template-subcard {
  padding: 18px 18px 8px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #fff 48%);
}

.template-subcard__title {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.template-subcard__hint {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.template-action-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 14px;
  margin-top: 8px;
}

.template-action-card {
  display: flex;
  flex-direction: column;
  padding: 14px 14px 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  min-height: 100%;
}

.template-action-card--ai {
  border-color: #c4b5fd;
  background: linear-gradient(135deg, #faf5ff 0%, #fff 70%);
}

.template-action-card__head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #0f172a;
}

.template-action-card__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #0ea5e9;
  color: #fff;
  font-size: 12px;
  font-weight: 800;
}

.template-action-card__badge--ai {
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  font-size: 14px;
}

.template-action-card__text {
  flex: 1;
  margin: 0 0 12px;
  font-size: 12px;
  color: #64748b;
  line-height: 1.55;
}

.template-action-card__text em {
  color: #475569;
  font-style: normal;
  font-weight: 600;
}

.template-action-card__btn {
  margin-top: auto;
  padding: 10px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 650;
  cursor: pointer;
  border: none;
  font-family: inherit;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.template-action-card__btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.template-action-card__btn.primary {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(14, 165, 233, 0.35);
}

.template-action-card__btn.primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(14, 165, 233, 0.45);
}

.template-action-card__btn.secondary {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
  color: #0f172a;
  border: 1px solid #cbd5e1;
}

.template-action-card__btn.secondary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.template-action-card__btn.ai {
  background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
  color: #fff;
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
}

.template-action-card__btn.ai:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 18px rgba(99, 102, 241, 0.45);
}

.template-delete-row {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px dashed #e2e8f0;
}

.delete-template-btn {
  background: transparent;
  color: #b91c1c;
  border: 1px solid #fecaca;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.delete-template-btn:hover {
  background: #fef2f2;
}

.optional-block {
  padding: 16px 16px 4px;
  border-radius: 12px;
  border: 1px dashed #cbd5e1;
  background: #f8fafc;
}

.optional-block__title {
  margin: 0 0 12px;
  font-size: 14px;
  font-weight: 700;
  color: #334155;
}

.create-survey-btn--wide {
  width: 100%;
  max-width: none;
  padding: 16px 24px;
  font-size: 16px;
}

.survey-ai-modal {
  max-width: 560px;
  width: 100%;
  background: #fff;
  padding: 28px 26px 22px;
  border-radius: 18px;
  position: relative;
  border: 1px solid rgba(10, 20, 45, 0.1);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.2);
}

.survey-ai-modal h2 {
  margin-top: 0;
  margin-bottom: 10px;
  font-size: 22px;
  color: #0f172a;
}

.survey-ai-lead {
  margin: 0 0 16px;
  font-size: 14px;
  color: #475569;
  line-height: 1.55;
}

.modern-form-block {
  margin-bottom: 12px;
}

.survey-ai-textarea {
  width: 100%;
  box-sizing: border-box;
}

.survey-ai-error {
  color: #b91c1c;
  font-size: 13px;
  margin: 0 0 8px;
  font-weight: 600;
}

.survey-ai-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
}

@media (max-width: 640px) {
  .template-action-grid {
    grid-template-columns: 1fr;
  }
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

.template-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 10px;
}

.edit-template-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  border: none;
  padding: 10px 18px;
  border-radius: 10px;
  cursor: pointer;
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

.edit-template-btn.ghost {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.12), rgba(0, 194, 255, 0.1));
  color: #0b4a6f;
}

.invite-card {
  margin: 18px 0 28px;
  padding: 18px 18px 14px;
  border-radius: 16px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.10), rgba(59, 130, 246, 0.08));
}

.invite-title {
  margin: 0 0 12px 0;
  font-size: 18px;
}

.invite-grid {
  display: grid;
  gap: 12px;
}

.invite-field {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.invite-label {
  font-size: 12px;
  color: #334155;
  font-weight: 650;
}

.invite-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
}

.copy-btn {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
  color: #fff;
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 650;
  cursor: pointer;
}

.copied-msg {
  font-size: 13px;
  color: #0f766e;
  font-weight: 600;
}

.invite-hint {
  margin: 10px 0 0 0;
  color: #64748b;
  font-size: 13px;
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
  position: relative;
  border: 1px solid rgba(10, 20, 45, 0.12);
}

.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.84);
  cursor: pointer;
  font-size: 18px;
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
