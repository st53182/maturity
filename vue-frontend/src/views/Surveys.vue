<template>
  <div class="surveys-shell">
    <div class="surveys-container">
    <section class="iceberg-intro surveys-landing-intro" aria-labelledby="surveys-landing-intro-title">
      <h2 id="surveys-landing-intro-title" class="iceberg-intro__title">{{ $t('surveys.wizard.introTitle') }}</h2>
      <p class="iceberg-intro__lead">{{ $t('surveys.wizard.introLead') }}</p>
      <button type="button" class="iceberg-intro__toggle" @click="surveyIntroExpanded = !surveyIntroExpanded">
        {{ surveyIntroExpanded ? $t('surveys.wizard.introCollapse') : $t('surveys.wizard.introExpand') }}
      </button>
      <div v-show="surveyIntroExpanded" class="iceberg-intro__levels">
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">1</span> {{ $t('surveys.wizard.introStep1Title') }}</h3>
          <p>{{ $t('surveys.wizard.introStep1Body') }}</p>
        </article>
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">2</span> {{ $t('surveys.wizard.introStep2Title') }}</h3>
          <p>{{ $t('surveys.wizard.introStep2Body') }}</p>
        </article>
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">3</span> {{ $t('surveys.wizard.introStep3Title') }}</h3>
          <p>{{ $t('surveys.wizard.introStep3Body') }}</p>
        </article>
      </div>

      <p class="surveys-landing-type-hint">{{ $t('surveys.wizard.landingTypeHint') }}</p>
      <div class="survey-type-selection survey-type-selection--landing">
        <button
          type="button"
          class="survey-type-card survey-type-card--landing"
          @click="openWizardFromTypeCard('enps')"
        >
          <h3>📊 {{ $t('surveys.enpsTitle') }}</h3>
          <p class="survey-type-card__lead">{{ $t('surveys.hr.enpsShort') }}</p>
          <ul class="survey-type-card__bullets">
            <li v-for="(b, i) in enpsWhenBullets" :key="'land-enps-' + i">{{ b }}</li>
          </ul>
        </button>
        <button
          type="button"
          class="survey-type-card survey-type-card--landing"
          @click="openWizardFromTypeCard('360')"
        >
          <h3>🔄 {{ $t('surveys.feedback360Title') }}</h3>
          <p class="survey-type-card__lead">{{ $t('surveys.hr.feedback360Short') }}</p>
          <ul class="survey-type-card__bullets">
            <li v-for="(b, i) in feedback360WhenBullets" :key="'land-360-' + i">{{ b }}</li>
          </ul>
        </button>
      </div>

      <div class="surveys-landing-cta">
        <button type="button" class="surveys-open-wizard-btn" @click="openCreateSurveyWizard">
          {{ $t('surveys.wizard.openWizardBtn') }}
        </button>
      </div>
    </section>

    <!-- Мастер создания (как модалка «создать айсберг») -->
    <div
      v-if="showCreateSurveyModal"
      class="modal-overlay survey-master-overlay"
      @click.self="closeCreateSurveyWizard"
    >
      <div class="modal-content survey-master-modal modal-content--wide">
        <button
          type="button"
          class="modal-close-top"
          :aria-label="$t('surveys.wizard.modalClose')"
          @click="closeCreateSurveyWizard"
        >✕</button>
        <h2 class="survey-master-modal__title">{{ $t('surveys.wizard.modalTitle') }}</h2>

        <div v-if="createFlowMode === 'choose' && !wizardEntryType" class="wizard-choose">
          <p class="wizard-choose__lead">{{ $t('surveys.wizard.chooseLead') }}</p>
          <div class="wizard-choose__grid">
            <button type="button" class="wizard-choice-card" @click="pickQuickFlow">
              <strong class="wizard-choice-card__title">{{ $t('surveys.wizard.quickTitle') }}</strong>
              <p class="wizard-choice-card__text">{{ $t('surveys.wizard.quickBody') }}</p>
              <span class="wizard-choice-card__cta">{{ $t('surveys.wizard.quickPick') }}</span>
            </button>
            <button type="button" class="wizard-choice-card" @click="pickCustomFlow">
              <strong class="wizard-choice-card__title">{{ $t('surveys.wizard.customTitle') }}</strong>
              <p class="wizard-choice-card__text">{{ $t('surveys.wizard.customBody') }}</p>
              <span class="wizard-choice-card__cta">{{ $t('surveys.wizard.customPick') }}</span>
            </button>
          </div>
        </div>

        <div v-else class="wizard-body">
          <button type="button" class="wizard-back-btn" @click="backToCreateChoice">
            {{ $t('surveys.wizard.backToChoice') }}
          </button>

          <div v-if="wizardEntryType" class="wizard-type-chip">
            <span class="wizard-type-chip__label">{{
              wizardEntryType === 'enps' ? $t('surveys.enpsTitle') : $t('surveys.feedback360Title')
            }}</span>
            <button type="button" class="wizard-type-chip__change" @click="clearWizardEntryType">
              {{ $t('surveys.wizard.changeType') }}
            </button>
          </div>

          <template v-if="!wizardEntryType">
            <p class="step-label step-label--outer">{{ $t('surveys.hr.step1Title') }}</p>
            <div class="survey-type-selection">
              <div
                class="survey-type-card"
                :class="{ active: selectedType === 'enps' }"
                @click="selectSurveyType('enps')"
              >
                <h3>📊 {{ $t('surveys.enpsTitle') }}</h3>
                <p class="survey-type-card__lead">{{ $t('surveys.hr.enpsShort') }}</p>
                <ul class="survey-type-card__bullets">
                  <li v-for="(b, i) in enpsWhenBullets" :key="'enps-' + i">{{ b }}</li>
                </ul>
              </div>

              <div
                class="survey-type-card"
                :class="{ active: selectedType === '360' }"
                @click="selectSurveyType('360')"
              >
                <h3>🔄 {{ $t('surveys.feedback360Title') }}</h3>
                <p class="survey-type-card__lead">{{ $t('surveys.hr.feedback360Short') }}</p>
                <ul class="survey-type-card__bullets">
                  <li v-for="(b, i) in feedback360WhenBullets" :key="'360-' + i">{{ b }}</li>
                </ul>
              </div>
            </div>
          </template>

          <div v-if="selectedType" class="survey-create-frame">
            <section class="survey-create-intro" aria-labelledby="survey-create-intro-title">
              <h3 id="survey-create-intro-title" class="survey-create-intro__title">{{ $t('surveys.hr.introTitle') }}</h3>
              <p class="survey-create-intro__lead">
                {{ $t('surveys.hr.introScenario') }}
              </p>
              <div v-if="createFlowMode === 'custom'" class="survey-create-intro__toolbar">
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

              <template v-if="createFlowMode === 'custom'">
                <p class="step-label step-label--in">{{ $t('surveys.hr.step3Title') }}</p>
                <div class="template-subcard">
                  <h4 class="template-subcard__title">{{ $t('surveys.hr.templateBlockTitle') }}</h4>
                  <p class="template-subcard__hint template-subcard__glossary">
                    {{ $t('surveys.hr.glossary') }}
                  </p>

                  <div v-if="hasUserTemplatesForSelectedType" class="template-source-block">
                    <p class="template-source-block__lead">{{ $t('surveys.wizard.templateSourceLead') }}</p>
                    <label class="template-source-row">
                      <input v-model="templateSourceMode" type="radio" value="standard" />
                      <span>{{ $t('surveys.wizard.templateSourceStandard') }}</span>
                    </label>
                    <label class="template-source-row">
                      <input v-model="templateSourceMode" type="radio" value="saved" />
                      <span>{{ $t('surveys.wizard.templateSourceSaved') }}</span>
                    </label>
                    <label
                      v-if="templateSourceMode === 'saved'"
                      class="stacked-field-label"
                      for="survey-template-select-saved"
                    >{{ $t('surveys.wizard.templateSourcePickSaved') }}</label>
                    <select
                      v-if="templateSourceMode === 'saved'"
                      id="survey-template-select-saved"
                      v-model="selectedTemplateId"
                      class="survey-select"
                    >
                      <option
                        v-for="template in userTemplatesForType"
                        :key="template.id"
                        :value="String(template.id)"
                      >
                        {{ template.name }}
                      </option>
                    </select>
                  </div>
                  <div v-else>
                    <label class="stacked-field-label" for="survey-template-select">{{ $t('surveys.hr.selectTemplateLabel') }}</label>
                    <select id="survey-template-select" v-model="selectedTemplateId" class="survey-select">
                      <option value="">{{ $t('surveys.hr.standardTemplate') }}</option>
                      <option v-for="template in availableTemplates" :key="template.id" :value="String(template.id)">
                        {{ template.name }}
                      </option>
                    </select>
                  </div>

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
              </template>

              <p v-else class="quick-flow-hint">
                {{ $t('surveys.wizard.quickTemplateHint') }}
                <button type="button" class="quick-flow-hint__link" @click="switchToCustomFlow">
                  {{ $t('surveys.wizard.switchToCustom') }}
                </button>
              </p>

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
      </div>
    </div>

    <!-- Модальное окно: черновик вопросов с ИИ (поверх мастера) -->
    <div v-if="showAiDraftModal" class="modal-overlay survey-ai-modal-overlay" @click.self="closeAiDraftModal">
      <div class="modal-content survey-ai-modal">
        <button type="button" class="modal-close-top" :aria-label="$t('common.close')" @click="closeAiDraftModal">✕</button>
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

    <section v-if="createdLink" class="invite-card" :aria-label="$t('surveys.inviteReadyTitle')">
      <h2 class="invite-title">{{ $t('surveys.inviteReadyTitle') }}</h2>
      <div class="invite-grid">
        <div class="invite-field">
          <label class="invite-label">{{ $t('surveys.inviteLinkLabel') }}</label>
          <div class="invite-row">
            <input class="survey-input mono" :value="createdLink" readonly />
            <button type="button" class="copy-btn" @click="copyText(createdLink)">{{ $t('surveys.inviteCopy') }}</button>
          </div>
        </div>
        <div class="invite-field">
          <label class="invite-label">{{ $t('surveys.inviteEmailBodyLabel') }}</label>
          <textarea class="survey-textarea" rows="6" :value="createdEmailText" readonly />
          <div class="invite-row">
            <button type="button" class="copy-btn" @click="copyText(createdEmailText)">{{ $t('surveys.inviteCopyText') }}</button>
            <span v-if="copiedMsg" class="copied-msg">{{ copiedMsg }}</span>
          </div>
        </div>
      </div>
      <p class="invite-hint">{{ $t('surveys.invitePasteHint') }}</p>
    </section>
    
    <div class="existing-surveys">
      <div class="surveys-header">
        <h2>{{ $t('surveys.listTitle') }}</h2>
        <div class="filter-controls">
          <select v-model="statusFilter" class="status-filter">
            <option value="">{{ $t('surveys.allStatuses') }}</option>
            <option value="draft">{{ $t('surveys.surveyStatus.draft') }}</option>
            <option value="active">{{ $t('surveys.surveyStatus.active') }}</option>
            <option value="closed">{{ $t('surveys.surveyStatus.closed') }}</option>
          </select>
        </div>
      </div>
      
      <div v-if="loading" class="loading">⏳ {{ $t('surveys.loadingList') }}</div>
      
      <div v-else-if="filteredSurveys.length === 0" class="no-surveys">
        {{ $t('surveys.noSurveysYet') }}
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
              ✏️ {{ $t('surveys.editSurveyBtn') }}
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
        <button class="modal-close-top" @click="closeEditModal" :aria-label="$t('common.close')">✕</button>
        <h2>{{ $t('surveys.editSurveyModalTitle') }}</h2>
        <div class="edit-form">
          <div class="form-group">
            <label>{{ $t('surveys.fieldTitle') }}:</label>
            <input v-model="editingSurvey.title" class="survey-input" />
          </div>
          <div class="form-group">
            <label>{{ $t('surveys.fieldStatus') }}:</label>
            <select v-model="editingSurvey.status" class="survey-select">
              <option value="draft">{{ $t('surveys.surveyStatus.draft') }}</option>
              <option value="active">{{ $t('surveys.surveyStatus.active') }}</option>
              <option value="closed">{{ $t('surveys.surveyStatus.closed') }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ $t('surveys.deadlineOptional') }}:</label>
            <input 
              type="datetime-local" 
              v-model="editingSurvey.deadline" 
              class="survey-input"
              :value="editingSurvey.deadline ? new Date(editingSurvey.deadline).toISOString().slice(0, 16) : ''"
            />
          </div>
        </div>
        <div class="modal-actions">
          <button @click="saveSurveyChanges" class="save-btn">{{ $t('common.save') }}</button>
          <button @click="closeEditModal" class="cancel-btn">{{ $t('common.cancel') }}</button>
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
      selectedTemplateId: '',
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
      aiDraftError: '',
      surveyIntroExpanded: false,
      showCreateSurveyModal: false,
      createFlowMode: 'choose',
      wizardEntryType: null,
      templateSourceMode: 'standard'
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
      return !!this.surveyTitle?.trim()
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
    },

    userTemplatesForType() {
      if (!this.selectedType || !this.availableTemplates?.length) return []
      return this.availableTemplates.filter(t => t.is_default === false)
    },

    hasUserTemplatesForSelectedType() {
      return this.createFlowMode === 'custom' && this.userTemplatesForType.length > 0
    }
  },

  watch: {
    templateSourceMode(val) {
      if (val === 'standard') {
        this.selectedTemplateId = ''
      } else if (val === 'saved' && this.userTemplatesForType.length) {
        const first = this.userTemplatesForType[0]
        this.selectedTemplateId = String(first.id)
      }
    }
  },
  
  async mounted() {
    await this.fetchSurveys()
  },
  
  methods: {
    openCreateSurveyWizard() {
      this.wizardEntryType = null
      this.createFlowMode = 'choose'
      this.showCreateSurveyModal = true
    },

    async openWizardFromTypeCard(type) {
      this.wizardEntryType = type
      this.selectedType = type
      this.createFlowMode = 'quick'
      this.templateSourceMode = 'standard'
      this.selectedTemplateId = ''
      this.surveyTitle = ''
      this.showCreateSurveyModal = true
      await this.fetchTemplates()
    },

    clearWizardEntryType() {
      this.wizardEntryType = null
      this.selectedType = ''
      this.createFlowMode = 'choose'
      this.surveyTitle = ''
      this.selectedTemplateId = ''
    },

    closeCreateSurveyWizard() {
      if (this.aiDraftLoading) return
      this.resetForm()
    },

    pickQuickFlow() {
      this.createFlowMode = 'quick'
      this.selectedTemplateId = ''
      this.templateSourceMode = 'standard'
    },

    pickCustomFlow() {
      this.createFlowMode = 'custom'
      this.templateSourceMode = 'standard'
    },

    backToCreateChoice() {
      this.wizardEntryType = null
      this.createFlowMode = 'choose'
      this.selectedType = ''
      this.surveyTitle = ''
      this.selectedTemplateId = ''
    },

    switchToCustomFlow() {
      this.createFlowMode = 'custom'
      this.templateSourceMode = 'standard'
      if (this.selectedType) {
        this.fetchTemplates()
      }
    },

    selectSurveyType(type) {
      this.selectedType = type
      this.selectedTemplateId = ''
      this.templateSourceMode = 'standard'
      this.fetchTemplates()
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
  const ok = window.confirm(this.$t('surveys.confirmDeleteTemplateNamed', { name: tpl.name }))
  if (!ok) return

  try {
    const token = localStorage.getItem('token')
    await axios.delete(`/api/survey-templates/${tpl.id}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    // сбрасываем выбор и обновляем список шаблонов
    this.selectedTemplateId = ''
    await this.fetchTemplates()
    alert(this.$t('surveys.templateDeletedOk'))
  } catch (e) {
    const status = e?.response?.status
    const msg = e?.response?.data?.error || this.$t('surveys.errorDeleteTemplate')
    if (status === 400 && /Default/i.test(msg)) {
      alert(this.$t('surveys.templateDeleteDefaultForbidden'))
    } else if (status === 404) {
      alert(this.$t('surveys.templateDeleteNotFound'))
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
      const kind =
        type === '360' ? this.$t('surveys.inviteEmailKind360') : this.$t('surveys.inviteEmailKindEnps');
      const dline = deadline
        ? this.$t('surveys.inviteEmailDeadlineLine', { date: this.formatDate(deadline) })
        : '';
      const t = (title || '').trim();
      const titleLine = t ? this.$t('surveys.inviteEmailSurveyLine', { title: t }) : '';
      const opening = this.$t('surveys.inviteEmailOpening', { kind });
      const linkSection = this.$t('surveys.inviteEmailLinkSection', { link });
      return `${titleLine}${opening}${dline}${linkSection}`;
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
      const baseName = this.currentTemplate
        ? this.currentTemplate.name
        : this.$t('surveys.standardTemplateName');
      const name = window.prompt(
        this.$t('surveys.templatePromptName'),
        this.$t('surveys.templateDefaultCopyName', { name: baseName })
      );
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
        alert(this.$t('surveys.templateCreated'));
      } catch (e) {
        alert(e?.response?.data?.error || this.$t('surveys.errorCreateTemplate'));
      }
    },

    async confirmCreateSurvey() {
      try {
        const token = localStorage.getItem('token')
        
        const surveyData = {
          survey_type: this.selectedType,
          title: this.surveyTitle,
          team_id: null,
          target_employee_id: null,
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
          this.copiedMsg = this.$t('surveys.linkCopiedShort')
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
        
        alert(this.$t('surveys.surveyDeletedSuccess'))
        await this.fetchSurveys()
      } catch (error) {
        console.error('Error deleting survey:', error)
        alert(this.$t('surveys.errorDeleteSurvey'))
      }
    },
    
    resetForm() {
      this.selectedType = ''
      this.surveyTitle = ''
      this.selectedTemplateId = ''
      this.previewQuestions = []
      this.showCreateSurveyModal = false
      this.createFlowMode = 'choose'
      this.wizardEntryType = null
      this.templateSourceMode = 'standard'
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
        name: this.$t('surveys.customTemplateName', { type: this.selectedType.toUpperCase() }),
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
        alert(this.$t('surveys.surveyUpdatedSuccess'))
      } catch (error) {
        console.error('Error updating survey:', error)
        alert(this.$t('surveys.errorUpdateSurvey'))
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
        alert(newStatus === 'active' ? this.$t('surveys.statusActivated') : this.$t('surveys.statusPaused'))
      } catch (error) {
        console.error('Error toggling survey status:', error)
        alert(this.$t('surveys.errorStatusChange'))
      }
    },
    
    getStatusLabel(status) {
      const key = `surveys.surveyStatus.${status}`;
      return this.$te(key) ? this.$t(key) : status;
    },
    
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      const loc = this.$i18n.locale === 'ru' ? 'ru-RU' : 'en-US';
      return date.toLocaleDateString(loc, {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
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

.surveys-landing-intro.iceberg-intro {
  margin-bottom: 28px;
  padding: 22px 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.iceberg-intro__title {
  font-size: 1.2rem;
  margin: 0 0 10px;
  color: #0c4a6e;
  font-weight: 700;
}

.iceberg-intro__lead {
  margin: 0 0 12px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.iceberg-intro__toggle {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 999px;
  border: 1px solid #7dd3fc;
  background: #fff;
  color: #0369a1;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  margin-bottom: 12px;
}

.iceberg-intro__toggle:hover {
  background: #f0f9ff;
}

.iceberg-intro__levels {
  display: grid;
  gap: 12px;
  margin-bottom: 8px;
}

.iceberg-intro__level-card {
  padding: 14px 16px;
  border-radius: 12px;
  background: #fff;
  border: 1px solid #e0f2fe;
}

.iceberg-intro__level-card h3 {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 8px;
}

.iceberg-intro__level-card p {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.iceberg-intro__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 26px;
  height: 26px;
  border-radius: 8px;
  background: linear-gradient(135deg, #0ea5e9, #2563eb);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.surveys-landing-cta {
  margin-top: 8px;
}

.surveys-open-wizard-btn {
  padding: 14px 28px;
  border-radius: 14px;
  border: none;
  cursor: pointer;
  font-family: inherit;
  font-size: 16px;
  font-weight: 700;
  color: #fff;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.95), rgba(0, 194, 255, 0.85));
  box-shadow: 0 10px 28px rgba(32, 90, 255, 0.28);
}

.surveys-open-wizard-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 34px rgba(32, 90, 255, 0.35);
}

.surveys-landing-type-hint {
  margin: 0 0 14px;
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

.survey-type-selection--landing {
  margin-bottom: 22px;
}

.survey-type-card--landing {
  display: block;
  width: 100%;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  border: 2px solid #e5e7eb;
}

.survey-type-card--landing:focus-visible {
  outline: 3px solid rgba(32, 90, 255, 0.45);
  outline-offset: 2px;
}

.wizard-type-chip {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
}

.wizard-type-chip__label {
  font-size: 14px;
  font-weight: 700;
  color: #14532d;
}

.wizard-type-chip__change {
  padding: 6px 12px;
  border-radius: 10px;
  border: 1px solid #86efac;
  background: #fff;
  color: #166534;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
}

.wizard-type-chip__change:hover {
  background: #f0fdf4;
}

.template-source-block {
  margin-bottom: 16px;
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #f8fafc;
}

.template-source-block__lead {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: 700;
  color: #0f172a;
}

.template-source-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 8px;
  font-size: 14px;
  color: #334155;
  cursor: pointer;
}

.template-source-row input {
  margin-top: 3px;
}

.survey-master-modal.modal-content--wide {
  max-width: min(920px, 96vw);
  width: 100%;
  max-height: calc(100vh - 64px);
  overflow-y: auto;
  margin: 0 auto;
  padding: 28px 26px 24px;
  position: relative;
  background: #fff;
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  box-shadow: 0 24px 80px rgba(15, 23, 42, 0.2);
}

.survey-master-modal__title {
  margin: 0 0 18px;
  font-size: 22px;
  font-weight: 700;
  color: #0f172a;
  padding-right: 36px;
}

.wizard-choose__lead {
  margin: 0 0 16px;
  font-size: 15px;
  color: #475569;
  line-height: 1.5;
}

.wizard-choose__grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.wizard-choice-card {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  text-align: left;
  padding: 20px 18px;
  border-radius: 16px;
  border: 2px solid #e2e8f0;
  background: linear-gradient(180deg, #f8fafc 0%, #fff 48%);
  cursor: pointer;
  font-family: inherit;
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.wizard-choice-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 8px 24px rgba(59, 130, 246, 0.12);
  transform: translateY(-2px);
}

.wizard-choice-card__title {
  display: block;
  font-size: 17px;
  color: #0f172a;
  margin-bottom: 8px;
}

.wizard-choice-card__text {
  margin: 0 0 14px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
  flex: 1;
}

.wizard-choice-card__cta {
  font-size: 14px;
  font-weight: 700;
  color: #2563eb;
}

.wizard-back-btn {
  display: inline-block;
  margin-bottom: 16px;
  padding: 6px 0;
  border: none;
  background: none;
  color: #2563eb;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.wizard-back-btn:hover {
  color: #1d4ed8;
}

.quick-flow-hint {
  margin: 16px 0 8px;
  font-size: 13px;
  color: #64748b;
  line-height: 1.5;
}

.quick-flow-hint__link {
  display: inline;
  margin-left: 6px;
  padding: 0;
  border: none;
  background: none;
  color: #2563eb;
  font-size: inherit;
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  text-decoration: underline;
  text-underline-offset: 2px;
}

@media (max-width: 640px) {
  .wizard-choose__grid {
    grid-template-columns: 1fr;
  }
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

/* Блок «Мои опросники»: явный отступ и строка заголовок + фильтр без налезания на сетку */
.existing-surveys {
  margin-top: 8px;
}

.surveys-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px 20px;
  margin-bottom: 22px;
  position: relative;
  z-index: 2;
}

.surveys-header h2 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.35;
}

.filter-controls {
  flex: 0 0 auto;
}

.status-select,
.status-filter {
  display: block;
  min-width: min(220px, 100%);
  padding: 10px 40px 10px 14px;
  font-size: 14px;
  line-height: 1.35;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #fff;
  color: #0f172a;
  cursor: pointer;
  box-sizing: border-box;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

.surveys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  position: relative;
  z-index: 1;
  padding-top: 4px;
}

.survey-card {
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 24px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1), border-color 0.3s ease, transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.survey-card:hover {
  transform: translateY(-2px);
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

.modal-overlay.survey-master-overlay {
  align-items: flex-start;
  padding-top: 28px;
  padding-bottom: 28px;
  overflow-y: auto;
}

.modal-overlay.survey-ai-modal-overlay {
  z-index: 1100;
  align-items: center;
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
