<template>
  <div class="meeting-design-container iceberg-tool">
    <h1>{{ $t('meetingDesign.title') }}</h1>
    <p v-if="aiUsageRemaining !== null" class="ai-usage-line">
      {{ $t('meetingDesign.aiUsageLeft', { n: aiUsageRemaining }) }}
    </p>

    <section class="iceberg-intro" aria-labelledby="md-intro-title">
      <h2 id="md-intro-title" class="iceberg-intro__title">{{ $t('meetingDesign.icebergIntro.title') }}</h2>
      <p class="iceberg-intro__lead">{{ $t('meetingDesign.icebergIntro.lead') }}</p>
      <button type="button" class="iceberg-intro__toggle" @click="introExpanded = !introExpanded">
        {{ introExpanded ? $t('meetingDesign.icebergIntro.collapse') : $t('meetingDesign.icebergIntro.expand') }}
      </button>
      <div v-show="introExpanded" class="iceberg-intro__levels">
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">1</span> {{ $t('meetingDesign.icebergIntro.step1Title') }}</h3>
          <p>{{ $t('meetingDesign.icebergIntro.step1Body') }}</p>
        </article>
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">2</span> {{ $t('meetingDesign.icebergIntro.step2Title') }}</h3>
          <p>{{ $t('meetingDesign.icebergIntro.step2Body') }}</p>
        </article>
        <article class="iceberg-intro__level-card">
          <h3><span class="iceberg-intro__badge">3</span> {{ $t('meetingDesign.icebergIntro.step3Title') }}</h3>
          <p>{{ $t('meetingDesign.icebergIntro.step3Body') }}</p>
        </article>
      </div>
    </section>

    <div v-if="loading" class="loading">⏳ {{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">❌ {{ error }}</div>

    <template v-else>
    <button
      v-if="!topicPanelOpen && !showCreateModal && !showViewModal && !showEditModal"
      type="button"
      class="ai-fab"
      :title="$t('meetingDesign.ai.fabTitle')"
      :aria-label="$t('meetingDesign.ai.fabTitle')"
      @click="openTopicPanel"
    >
      <span class="ai-fab__glyph" aria-hidden="true">✨</span>
      <span class="ai-fab__label">{{ $t('meetingDesign.ai.fabTitle') }}</span>
    </button>

    <div
      v-if="topicPanelOpen"
      class="topic-panel-overlay"
      role="dialog"
      aria-modal="true"
      :aria-label="$t('meetingDesign.ai.panelTitle')"
      @click.self="minimizeTopicPanel"
    >
      <div class="topic-panel" @click.stop>
        <div class="topic-panel__head">
          <h2>{{ $t('meetingDesign.ai.panelTitle') }}</h2>
          <div class="topic-panel__head-actions">
            <button type="button" class="topic-panel__icon-btn" :title="$t('meetingDesign.ai.minimize')" @click="minimizeTopicPanel">▁</button>
          </div>
        </div>
        <p class="topic-panel__lead">{{ $t('meetingDesign.ai.panelSubtitle') }}</p>

        <div class="form-group">
          <label>{{ $t('meetingDesign.ai.responseLang') }}</label>
          <select v-model="aiLocale" class="form-select">
            <option value="">{{ $t('meetingDesign.ai.responseLang') }} ({{ $i18n.locale }})</option>
            <option value="ru">Русский</option>
            <option value="en">English</option>
            <option value="uk">Українська</option>
            <option value="de">Deutsch</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="pl">Polski</option>
            <option value="kk">Қазақша</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.ai.topicContextType') }}</label>
          <select v-model="topicMeetingType" class="form-select">
            <option value="retrospective">{{ $t('meetingDesign.types.retrospective') }}</option>
            <option value="planning">{{ $t('meetingDesign.types.planning') }}</option>
            <option value="brainstorm">{{ $t('meetingDesign.types.brainstorm') }}</option>
            <option value="workshop">{{ $t('meetingDesign.types.workshop') }}</option>
            <option value="standup">{{ $t('meetingDesign.types.standup') }}</option>
            <option value="review">{{ $t('meetingDesign.types.review') }}</option>
            <option value="kickoff">{{ $t('meetingDesign.types.kickoff') }}</option>
            <option value="training">{{ $t('meetingDesign.types.training') }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.ai.themeLabel') }}</label>
          <textarea
            v-model="topicTheme"
            class="form-textarea"
            rows="3"
            :placeholder="$t('meetingDesign.ai.themePlaceholder')"
          />
        </div>

        <div class="topic-panel__actions">
          <button type="button" class="confirm-btn" :disabled="topicLoading || !topicTheme.trim()" @click="fetchConversationTopics">
            {{ topicLoading ? $t('meetingDesign.ai.topicsLoading') : $t('meetingDesign.ai.getTopics') }}
          </button>
        </div>

        <p v-if="topicError" class="topic-panel__error" role="alert">{{ topicError }}</p>

        <p v-if="topicLoading" class="topic-panel__status">{{ $t('meetingDesign.ai.topicsLoading') }}</p>

        <ul v-if="topicTopics.length" class="topic-list">
          <li v-for="(t, idx) in topicTopics" :key="idx" class="topic-list__item">
            <span class="topic-list__text">{{ t }}</span>
            <button type="button" class="topic-list__apply" @click="applyTopicToGoal(t)">{{ $t('meetingDesign.ai.applyToGoal') }}</button>
          </li>
        </ul>
        <p v-else-if="!topicLoading && topicRequestedOnce && !topicError && !topicTopics.length" class="topic-panel__empty">{{ $t('meetingDesign.ai.noTopics') }}</p>
      </div>
    </div>

      <div class="action-buttons">
        <button type="button" class="create-btn" @click="openCreateModal">
          ➕ {{ $t('meetingDesign.createNew') }}
        </button>
      </div>

      <div v-if="designs.length === 0" class="no-designs">
        <p>{{ $t('meetingDesign.noDesigns') }}</p>
      </div>

      <div v-else class="designs-grid">
        <div v-for="design in designs" :key="design.id" class="design-card">
          <h3>{{ design.title }}</h3>
          <p><strong>{{ $t('meetingDesign.meetingType') }}:</strong> {{ design.meeting_type }}</p>
          <p><strong>{{ $t('meetingDesign.duration') }}:</strong> {{ design.duration_minutes }} {{ $t('meetingDesign.minutes') }}</p>
          <p><strong>{{ $t('meetingDesign.goal') }}:</strong> {{ goalPreview(design.goal) }}</p>
          
          <div class="design-actions">
            <button class="view-btn" @click="viewDesign(design)">👁️ Просмотр</button>
            <button class="delete-btn" @click="deleteDesign(design.id)">🗑️ {{ $t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </template>

    <!-- Create Meeting Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal create-modal">
        <button class="close-btn" @click="closeCreateModal" aria-label="Close">✕</button>
        <h2>{{ $t('meetingDesign.createNew') }}</h2>

        <div class="form-assist-iceberg">
          <p class="form-assist-iceberg__lead">{{ $t('meetingDesign.formAssist.lead') }}</p>
          <textarea
            v-model="formAssistBrief"
            class="form-textarea"
            rows="2"
            :placeholder="$t('meetingDesign.formAssist.placeholder')"
          />
          <div class="form-assist-iceberg__actions">
            <button
              type="button"
              class="secondary-ice-btn"
              :disabled="formAssistLoading || !formAssistBrief.trim()"
              @click="runFormAssist"
            >
              {{ formAssistLoading ? '…' : $t('meetingDesign.formAssist.run') }}
            </button>
          </div>
          <p v-if="formAssistError" class="form-assist-iceberg__err">{{ formAssistError }}</p>
        </div>
        
        <div class="form-group">
          <label>{{ $t('meetingDesign.meetingTitle') }}</label>
          <input v-model="newDesign.title" type="text" class="form-input" />
          <p class="field-hint">{{ $t('meetingDesign.fieldHints.title') }}</p>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.meetingType') }}</label>
          <select v-model="newDesign.meeting_type" class="form-select">
            <option value="retrospective">{{ $t('meetingDesign.types.retrospective') }}</option>
            <option value="planning">{{ $t('meetingDesign.types.planning') }}</option>
            <option value="brainstorm">{{ $t('meetingDesign.types.brainstorm') }}</option>
            <option value="workshop">{{ $t('meetingDesign.types.workshop') }}</option>
            <option value="standup">{{ $t('meetingDesign.types.standup') }}</option>
            <option value="review">{{ $t('meetingDesign.types.review') }}</option>
            <option value="kickoff">{{ $t('meetingDesign.types.kickoff') }}</option>
            <option value="training">{{ $t('meetingDesign.types.training') }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.goal') }}</label>
          <textarea v-model="newDesign.goal" class="form-textarea" rows="3"></textarea>
          <p class="field-hint">{{ $t('meetingDesign.fieldHints.goal') }}</p>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.duration') }}</label>
          <select v-model="newDesign.duration_minutes" class="form-select">
            <option value="15">15 {{ $t('meetingDesign.minutes') }}</option>
            <option value="30">30 {{ $t('meetingDesign.minutes') }}</option>
            <option value="45">45 {{ $t('meetingDesign.minutes') }}</option>
            <option value="60">1 {{ $t('meetingDesign.hours') }}</option>
            <option value="90">1.5 {{ $t('meetingDesign.hours') }}</option>
            <option value="120">2 {{ $t('meetingDesign.hours') }}</option>
            <option value="180">3 {{ $t('meetingDesign.hours') }}</option>
            <option value="240">4 {{ $t('meetingDesign.hours') }}</option>
            <option value="300">5 {{ $t('meetingDesign.hours') }}</option>
            <option value="360">6 {{ $t('meetingDesign.hours') }}</option>
            <option value="420">7 {{ $t('meetingDesign.hours') }}</option>
            <option value="480">8 {{ $t('meetingDesign.hours') }}</option>
            <option value="960">16 {{ $t('meetingDesign.hours') }}</option>
          </select>
          <p class="field-hint">{{ $t('meetingDesign.fieldHints.duration') }}</p>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.selectTeam') }}</label>
          <select v-model="newDesign.team_id" class="form-select">
            <option value="">Без команды</option>
            <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.ai.responseLang') }}</label>
          <select v-model="aiLocale" class="form-select">
            <option value="">{{ $t('meetingDesign.ai.responseLang') }} ({{ $i18n.locale }})</option>
            <option value="ru">Русский</option>
            <option value="en">English</option>
            <option value="uk">Українська</option>
            <option value="de">Deutsch</option>
            <option value="es">Español</option>
            <option value="fr">Français</option>
            <option value="pl">Polski</option>
            <option value="kk">Қазақша</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.constraints') }}</label>
          <p class="field-hint">{{ $t('meetingDesign.fieldHints.constraints') }}</p>
          <div class="constraint-labels">
            <div v-for="(label, key) in constraintLabels" :key="key" class="constraint-row">
              <input
                :id="'meeting-constraint-' + key"
                v-model="selectedConstraints"
                type="checkbox"
                class="constraint-checkbox"
                :value="key"
              />
              <label :for="'meeting-constraint-' + key" class="constraint-label">{{ label }}</label>
            </div>
          </div>
          <textarea v-model="newDesign.constraints" class="form-textarea" rows="2" placeholder="Дополнительные ограничения..."></textarea>
        </div>

        <p class="create-modal__ai-row">
          <button type="button" class="create-modal__ai-link" @click="openTopicPanelFromCreate">
            <span aria-hidden="true">✨</span> {{ $t('meetingDesign.ai.fabTitle') }}
          </button>
        </p>

        <div class="modal-buttons">
          <button class="confirm-btn" @click="generateDesign" :disabled="generating">
            {{ generating ? $t('meetingDesign.creating') : $t('meetingDesign.generate') }}
          </button>
          <button class="cancel-btn" @click="closeCreateModal">{{ $t('common.cancel') }}</button>
        </div>
      </div>
    </div>

    <!-- View Design Modal -->
    <div v-if="showViewModal && currentDesign" class="modal-overlay" @click.self="closeViewModal">
      <div class="modal view-modal">
        <div class="modal-header">
          <h2>{{ currentDesign.title }}</h2>
          <div class="modal-header__tools">
            <button
              type="button"
              class="view-ai-fab"
              :title="$t('meetingDesign.ai.viewAiTitle')"
              :aria-expanded="viewAiOpen"
              @click="viewAiOpen = !viewAiOpen"
            >
              <span aria-hidden="true">✨</span>
            </button>
            <button class="close-btn" @click="closeViewModal">✕</button>
          </div>
        </div>

        <div v-show="viewAiOpen" class="view-ai-box">
          <p class="view-ai-box__hint">{{ $t('meetingDesign.ai.viewAiHint') }}</p>
          <div class="form-group">
            <label>{{ $t('meetingDesign.ai.responseLang') }}</label>
            <select v-model="viewAiLocale" class="form-select">
              <option value="">{{ $t('meetingDesign.ai.responseLang') }} ({{ $i18n.locale }})</option>
              <option value="ru">Русский</option>
              <option value="en">English</option>
              <option value="uk">Українська</option>
              <option value="de">Deutsch</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="pl">Polski</option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ $t('meetingDesign.ai.selectBlock') }}</label>
            <select v-model="viewAiContext" class="form-select">
              <option value="whole">{{ $t('meetingDesign.ai.contextWhole') }}</option>
              <option v-for="(b, i) in (currentDesign.blocks || [])" :key="'b-' + i" :value="String(i)">
                {{ i + 1 }}. {{ b.title }} ({{ b.time }})
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>{{ $t('meetingDesign.ai.yourQuestion') }}</label>
            <textarea
              v-model="viewAiQuestion"
              class="form-textarea"
              rows="2"
              :placeholder="$t('meetingDesign.ai.questionPlaceholder')"
            />
          </div>
          <div class="view-ai-box__actions">
            <button type="button" class="confirm-btn" :disabled="viewAiLoading" @click="fetchFacilitatorHelp(false)">
              {{ viewAiLoading ? $t('meetingDesign.ai.helpLoading') : $t('meetingDesign.ai.quickHelp') }}
            </button>
            <button
              type="button"
              class="cancel-btn"
              :disabled="viewAiLoading || !viewAiQuestion.trim()"
              @click="fetchFacilitatorHelp(true)"
            >
              {{ viewAiLoading ? $t('meetingDesign.ai.helpLoading') : $t('meetingDesign.ai.getHelp') }}
            </button>
          </div>
          <div v-if="viewAiLoading" class="view-ai-box__loading" role="status">{{ $t('meetingDesign.ai.helpLoading') }}</div>
          <p v-if="viewAiError" class="view-ai-box__error">{{ viewAiError }}</p>
          <div v-if="viewAiAnswer" class="view-ai-box__answer">{{ viewAiAnswer }}</div>
        </div>

        <div class="design-info">
          <p><strong>{{ $t('meetingDesign.meetingType') }}:</strong> {{ currentDesign.meeting_type }}</p>
          <p><strong>{{ $t('meetingDesign.goal') }}:</strong> {{ currentDesign.goal }}</p>
          <p><strong>{{ $t('meetingDesign.duration') }}:</strong> {{ currentDesign.duration_minutes }} {{ $t('meetingDesign.minutes') }}</p>
          <p v-if="currentDesign.constraints"><strong>{{ $t('meetingDesign.constraints') }}:</strong> {{ currentDesign.constraints }}</p>
        </div>

        <div class="blocks-container">
          <h3>{{ $t('meetingDesign.blocks') }}</h3>
          <div v-for="(block, index) in (currentDesign.blocks || [])" :key="index" class="block-card">
            <div class="block-header">
              <div class="block-time">
                <strong>{{ block.time }}</strong> - {{ block.title }}
                <span class="block-duration">({{ block.duration }} мин)</span>
              </div>
              <div class="block-actions">
                <button class="regenerate-btn" @click="regenerateBlock(index)" :disabled="regenerating === index">
                  {{ regenerating === index ? $t('meetingDesign.regenerating') : '🔄' }}
                </button>
                <button class="edit-btn" @click="editBlock(index)">✏️</button>
              </div>
            </div>
            <div class="block-content">
              <p>{{ block.description }}</p>
            </div>
          </div>
        </div>

        <div class="modal-buttons">
          <button class="save-btn" @click="saveDesign" :disabled="saving">
            {{ saving ? $t('meetingDesign.saving') : $t('meetingDesign.save') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Edit Block Modal -->
    <div v-if="showEditModal && editingBlock" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal edit-modal">
        <button class="close-btn" @click="showEditModal = false" aria-label="Close">✕</button>
        <h2>Редактировать блок</h2>
        
        <div class="form-group">
          <label>Название</label>
          <input v-model="editingBlock.title" type="text" class="form-input" />
        </div>

        <div class="form-group">
          <label>Время</label>
          <input v-model="editingBlock.time" type="text" class="form-input" />
        </div>

        <div class="form-group">
          <label>Продолжительность (минуты)</label>
          <input v-model="editingBlock.duration" type="number" class="form-input" />
        </div>

        <div class="form-group">
          <label>Описание</label>
          <textarea v-model="editingBlock.description" class="form-textarea" rows="4"></textarea>
        </div>

        <div class="modal-buttons">
          <button class="confirm-btn" @click="saveBlockEdit">{{ $t('common.save') }}</button>
          <button class="cancel-btn" @click="showEditModal = false">{{ $t('common.cancel') }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'MeetingDesign',
  data() {
    return {
      designs: [],
      teams: [],
      loading: true,
      error: null,
      showCreateModal: false,
      showViewModal: false,
      showEditModal: false,
      generating: false,
      saving: false,
      regenerating: null,
      currentDesign: null,
      editingBlock: null,
      editingBlockIndex: null,
      selectedConstraints: [],
      newDesign: {
        title: '',
        meeting_type: 'retrospective',
        goal: '',
        duration_minutes: 60,
        team_id: '',
        constraints: ''
      },
      constraintLabels: {},
      topicPanelOpen: false,
      topicTheme: '',
      topicTopics: [],
      topicLoading: false,
      topicRequestedOnce: false,
      topicError: '',
      aiLocale: '',
      topicMeetingType: 'retrospective',
      viewAiOpen: false,
      viewAiLocale: '',
      viewAiContext: 'whole',
      viewAiQuestion: '',
      viewAiAnswer: '',
      viewAiLoading: false,
      viewAiError: '',
      introExpanded: false,
      formAssistBrief: '',
      formAssistLoading: false,
      formAssistError: '',
      aiUsageRemaining: null
    };
  },
  computed: {
    effectiveLocale() {
      const l = (this.aiLocale || this.$i18n.locale || 'ru').toString();
      return l.split('-')[0].slice(0, 12);
    },
    viewEffectiveLocale() {
      const l = (this.viewAiLocale || this.$i18n.locale || 'ru').toString();
      return l.split('-')[0].slice(0, 12);
    }
  },
  async mounted() {
    this.constraintLabels = {
      remote: this.$t('meetingDesign.constraintLabels.remote'),
      inPerson: this.$t('meetingDesign.constraintLabels.inPerson'),
      hybrid: this.$t('meetingDesign.constraintLabels.hybrid'),
      largeGroup: this.$t('meetingDesign.constraintLabels.largeGroup'),
      smallGroup: this.$t('meetingDesign.constraintLabels.smallGroup'),
      timeboxed: this.$t('meetingDesign.constraintLabels.timeboxed'),
      interactive: this.$t('meetingDesign.constraintLabels.interactive'),
      presentation: this.$t('meetingDesign.constraintLabels.presentation')
    };
    await this.loadDesigns();
    await this.loadTeams();
    await this.fetchAiUsage();
  },
  methods: {
    async fetchAiUsage() {
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.get('/api/ai-usage', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.aiUsageRemaining = data?.remaining ?? null;
      } catch {
        this.aiUsageRemaining = null;
      }
    },
    async runFormAssist() {
      const brief = (this.formAssistBrief || '').trim();
      if (!brief) return;
      this.formAssistLoading = true;
      this.formAssistError = '';
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post(
          '/api/meeting-design/form-assist',
          {
            brief_note: brief,
            meeting_type: this.newDesign.meeting_type,
            duration_minutes: this.newDesign.duration_minutes,
            locale: this.effectiveLocale,
            existing_title: this.newDesign.title,
            existing_goal: this.newDesign.goal
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (data.title) this.newDesign.title = data.title;
        if (data.goal) this.newDesign.goal = data.goal;
        const keys = Array.isArray(data.constraint_keys) ? data.constraint_keys : [];
        const allowed = new Set(Object.keys(this.constraintLabels));
        this.selectedConstraints = keys.filter((k) => allowed.has(k));
        const notes = (data.constraints_notes || '').trim();
        if (notes) {
          this.newDesign.constraints = this.newDesign.constraints
            ? `${this.newDesign.constraints.trim()}\n\n${notes}`
            : notes;
        }
        await this.fetchAiUsage();
      } catch (error) {
        this.formAssistError =
          (error.response && error.response.data && error.response.data.error) ||
          this.$t('meetingDesign.errorGenerating');
      } finally {
        this.formAssistLoading = false;
      }
    },
    async loadDesigns() {
      try {
        this.loading = true;
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/meeting-design', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.designs = response.data;
      } catch (error) {
        console.error('Error loading designs:', error);
        this.error = this.$t('meetingDesign.errorLoading');
      } finally {
        this.loading = false;
      }
    },

    async loadTeams() {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get('/api/teams', {
          headers: { Authorization: `Bearer ${token}` }
        });
        this.teams = response.data;
      } catch (error) {
        console.error('Error loading teams:', error);
      }
    },

    async generateDesign() {
      try {
        this.generating = true;
        const token = localStorage.getItem('token');
        
        const constraints = this.selectedConstraints.length > 0 
          ? this.selectedConstraints.map(key => this.constraintLabels[key]).join(', ') + 
            (this.newDesign.constraints ? '. ' + this.newDesign.constraints : '')
          : this.newDesign.constraints;

        const payload = {
          ...this.newDesign,
          constraints,
          team_id: this.newDesign.team_id || null
        };

        const response = await axios.post('/api/meeting-design/generate', payload, {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.designs.unshift(response.data);
        this.closeCreateModal();
        await this.fetchAiUsage();
        this.viewDesign(response.data);
      } catch (error) {
        console.error('Error generating design:', error);
        this.error = this.$t('meetingDesign.errorGenerating');
      } finally {
        this.generating = false;
      }
    },

    async regenerateBlock(blockIndex) {
      try {
        this.regenerating = blockIndex;
        const token = localStorage.getItem('token');
        
        const response = await axios.post('/api/meeting-design/regenerate-block', {
          design_id: this.currentDesign.id,
          block_index: blockIndex,
          locale: this.viewEffectiveLocale
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.currentDesign.blocks[blockIndex] = response.data.block;
        
        const designIndex = this.designs.findIndex(d => d.id === this.currentDesign.id);
        if (designIndex !== -1) {
          this.designs[designIndex] = response.data.design;
        }
      } catch (error) {
        console.error('Error regenerating block:', error);
        this.error = this.$t('meetingDesign.errorRegenerating');
      } finally {
        this.regenerating = null;
      }
    },

    async saveDesign() {
      try {
        this.saving = true;
        const token = localStorage.getItem('token');
        
        await axios.put(`/api/meeting-design/${this.currentDesign.id}`, {
          title: this.currentDesign.title,
          goal: this.currentDesign.goal,
          constraints: this.currentDesign.constraints,
          blocks: this.currentDesign.blocks
        }, {
          headers: { Authorization: `Bearer ${token}` }
        });

        alert(this.$t('meetingDesign.designSaved'));
      } catch (error) {
        console.error('Error saving design:', error);
        this.error = this.$t('meetingDesign.errorSaving');
      } finally {
        this.saving = false;
      }
    },

    async deleteDesign(designId) {
      if (!confirm(this.$t('meetingDesign.confirmDelete'))) {
        return;
      }

      try {
        const token = localStorage.getItem('token');
        await axios.delete(`/api/meeting-design/${designId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });

        this.designs = this.designs.filter(d => d.id !== designId);
        alert(this.$t('meetingDesign.designDeleted'));
      } catch (error) {
        console.error('Error deleting design:', error);
        this.error = this.$t('meetingDesign.errorSaving');
      }
    },

    async exportPdf(designId) {
      try {
        const token = localStorage.getItem('token');
        const response = await axios.get(`/api/meeting-design/${designId}/pdf`, {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob'
        });

        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `meeting-design-${designId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
      } catch (error) {
        console.error('Error exporting PDF:', error);
        this.error = 'Ошибка экспорта PDF';
      }
    },

    goalPreview(goal) {
      if (!goal || typeof goal !== 'string') {
        return '';
      }
      return goal.length > 100 ? `${goal.slice(0, 100)}…` : goal;
    },

    openCreateModal() {
      this.topicMeetingType = this.newDesign.meeting_type || 'retrospective';
      this.formAssistBrief = '';
      this.formAssistError = '';
      this.showCreateModal = true;
    },

    openTopicPanel() {
      this.topicPanelOpen = true;
    },

    minimizeTopicPanel() {
      this.topicPanelOpen = false;
    },

    async fetchConversationTopics() {
      const theme = (this.topicTheme || '').trim();
      if (!theme) {
        return;
      }
      const token = localStorage.getItem('token');
      if (!token) {
        this.topicError = this.$t('meetingDesign.ai.loginRequired');
        return;
      }
      this.topicLoading = true;
      this.topicRequestedOnce = true;
      this.topicError = '';
      try {
        const { data } = await axios.post(
          '/api/meeting-design/ai-conversation-topics',
          {
            theme,
            meeting_type: this.topicMeetingType,
            locale: this.effectiveLocale
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        this.topicTopics = Array.isArray(data.topics) ? data.topics : [];
      } catch (error) {
        console.error('ai-conversation-topics:', error);
        this.topicTopics = [];
        const status = error.response && error.response.status;
        const d = error.response && error.response.data;
        const fromBody =
          typeof d === 'string'
            ? d
            : d && (d.error || d.msg || d.message);
        let msg = fromBody;
        if (!msg && status === 401) {
          msg = this.$t('meetingDesign.ai.loginRequired');
        }
        if (!msg) {
          msg = this.$t('meetingDesign.errorGenerating');
        }
        this.topicError = msg;
      } finally {
        this.topicLoading = false;
      }
    },

    applyTopicToGoal(t) {
      const line = (t || '').trim();
      if (!line) {
        return;
      }
      this.newDesign.goal = this.newDesign.goal
        ? `${this.newDesign.goal.trim()}\n\n${line}`
        : line;
      this.topicPanelOpen = false;
      this.showCreateModal = true;
    },

    async fetchFacilitatorHelp(useQuestion) {
      if (!this.currentDesign || !this.currentDesign.id) {
        return;
      }
      if (useQuestion && !(this.viewAiQuestion || '').trim()) {
        return;
      }
      this.viewAiLoading = true;
      this.viewAiError = '';
      this.viewAiAnswer = '';
      try {
        const token = localStorage.getItem('token');
        const block_index =
          this.viewAiContext === 'whole' ? null : parseInt(this.viewAiContext, 10);
        const question = useQuestion ? (this.viewAiQuestion || '').trim() : '';
        const { data } = await axios.post(
          '/api/meeting-design/ai-facilitator-help',
          {
            design_id: this.currentDesign.id,
            block_index,
            question,
            locale: this.viewEffectiveLocale
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        this.viewAiAnswer = (data && data.answer) ? String(data.answer) : '';
      } catch (error) {
        console.error('ai-facilitator-help:', error);
        const msg =
          (error.response && error.response.data && error.response.data.error) ||
          this.$t('meetingDesign.errorGenerating');
        this.viewAiError = msg;
      } finally {
        this.viewAiLoading = false;
      }
    },

    viewDesign(design) {
      this.currentDesign = JSON.parse(JSON.stringify(design));
      this.viewAiOpen = false;
      this.viewAiLocale = '';
      this.viewAiContext = 'whole';
      this.viewAiQuestion = '';
      this.viewAiAnswer = '';
      this.viewAiError = '';
      this.viewAiLoading = false;
      this.showViewModal = true;
    },

    closeViewModal() {
      this.showViewModal = false;
      this.currentDesign = null;
    },

    editBlock(blockIndex) {
      this.editingBlock = { ...this.currentDesign.blocks[blockIndex] };
      this.editingBlockIndex = blockIndex;
      this.showEditModal = true;
    },

    saveBlockEdit() {
      this.currentDesign.blocks[this.editingBlockIndex] = { ...this.editingBlock };
      this.showEditModal = false;
      this.editingBlock = null;
      this.editingBlockIndex = null;
    },

    closeCreateModal() {
      this.showCreateModal = false;
      this.formAssistBrief = '';
      this.formAssistError = '';
      this.newDesign = {
        title: '',
        meeting_type: 'retrospective',
        goal: '',
        duration_minutes: 60,
        team_id: '',
        constraints: ''
      };
      this.selectedConstraints = [];
    }
  }
};
</script>

<style scoped>
.meeting-design-container.iceberg-tool {
  margin-left: auto;
  margin-right: auto;
  padding: 32px;
  width: 100%;
  max-width: 1280px;
  box-sizing: border-box;
  background: #ffffff;
  border-radius: 20px;
  border: 1px solid #bae6fd;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

.ai-usage-line {
  margin: -16px 0 20px;
  font-size: 14px;
  color: #475569;
}

.iceberg-intro {
  margin-bottom: 28px;
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.iceberg-intro__title {
  font-size: 1.2rem;
  margin: 0 0 12px;
  color: #0c4a6e;
}

.iceberg-intro__lead {
  margin: 0 0 16px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.iceberg-intro__toggle {
  background: #fff;
  border: 2px solid #0ea5e9;
  color: #0369a1;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.iceberg-intro__levels {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.iceberg-intro__level-card {
  background: #fff;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.iceberg-intro__level-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.iceberg-intro__level-card p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.iceberg-intro__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #0ea5e9;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.field-hint {
  margin: 6px 0 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
}

.form-assist-iceberg {
  margin-bottom: 22px;
  padding: 16px 18px;
  background: linear-gradient(145deg, #faf5ff 0%, #eef2ff 100%);
  border-radius: 14px;
  border: 1px solid #c7d2fe;
}

.form-assist-iceberg__lead {
  margin: 0 0 10px;
  font-size: 13px;
  color: #5b21b6;
  line-height: 1.45;
}

.form-assist-iceberg__actions {
  margin-top: 10px;
}

.form-assist-iceberg__err {
  margin: 10px 0 0;
  font-size: 13px;
  color: #dc2626;
}

.secondary-ice-btn {
  border: 2px solid #6366f1;
  background: #fff;
  color: #4338ca;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  font-family: inherit;
}

.secondary-ice-btn:hover:not(:disabled) {
  background: #eef2ff;
}

.secondary-ice-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

h1 {
  font-size: 32px;
  color: #1a1a1a;
  font-weight: 700;
  margin-bottom: 32px;
  letter-spacing: -0.5px;
}

.action-buttons {
  margin-bottom: 32px;
}

.create-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: white;
  padding: 14px 28px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.create-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.no-designs {
  text-align: center;
  padding: 60px 20px;
  color: #7f8c8d;
  font-size: 18px;
}

.designs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 20px;
}

.design-card {
  background: white;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.design-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: #d1d5db;
}

.design-card h3 {
  color: #111827;
  margin-bottom: 16px;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.3px;
}

.design-card p {
  margin: 10px 0;
  color: #6b7280;
  line-height: 1.6;
  font-size: 14px;
}

.design-actions {
  display: flex;
  gap: 10px;
  margin-top: 15px;
}

.view-btn, .pdf-btn, .delete-btn {
  padding: 10px 16px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
  font-family: inherit;
}

.view-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.view-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.pdf-btn {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(245, 158, 11, 0.3);
}

.pdf-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.4);
}

.delete-btn {
  background: #ef4444;
  color: white;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.delete-btn:hover {
  background: #dc2626;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 20px;
  padding: 40px;
  max-width: 90%;
  max-height: 90%;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.create-modal {
  width: 600px;
}

.create-modal__ai-row {
  margin: 0 0 16px;
  text-align: center;
}

.create-modal__ai-link {
  background: none;
  border: none;
  padding: 8px 12px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  color: #6366f1;
  text-decoration: underline;
  text-underline-offset: 3px;
  font-family: inherit;
}

.create-modal__ai-link:hover {
  color: #4f46e5;
}

.view-modal {
  width: 800px;
}

.edit-modal {
  width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
}

.close-btn:hover {
  color: #2c3e50;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 10px;
  font-weight: 600;
  color: #1f2937;
  font-size: 15px;
  letter-spacing: -0.2px;
}

.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  background: #ffffff;
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
}

.form-input::placeholder,
.form-textarea::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

.form-input:hover, .form-select:hover, .form-textarea:hover {
  border-color: #cbd5e1;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #0ea5e9;
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.12), 0 2px 8px rgba(14, 165, 233, 0.08);
  background: #f0f9ff;
}

.form-select {
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%236b7280' d='M6 9L1 4h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 16px center;
  padding-right: 44px;
}

.form-textarea {
  min-height: 100px;
  line-height: 1.6;
}

.constraint-labels {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.constraint-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  min-width: 0;
}

.constraint-checkbox {
  margin: 2px 0 0;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  cursor: pointer;
  accent-color: #3b82f6;
  vertical-align: top;
}

.constraint-checkbox:focus {
  outline: none;
}

.constraint-checkbox:focus-visible {
  outline: 2px solid rgba(59, 130, 246, 0.45);
  outline-offset: 2px;
}

.form-group .constraint-labels .constraint-label {
  margin-bottom: 0;
}

.constraint-label {
  display: block;
  font-weight: 500;
  font-size: 14px;
  line-height: 1.4;
  color: #374151;
  cursor: pointer;
  margin: 0;
  user-select: none;
  text-decoration: none;
}

.design-info {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.design-info p {
  margin: 10px 0;
}

.blocks-container h3 {
  color: #2c3e50;
  margin-bottom: 15px;
}

.block-card {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  border-left: 4px solid #0ea5e9;
  border: 1px solid #e5e7eb;
  border-left-width: 4px;
  transition: all 0.2s ease;
}

.block-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
}

.block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.block-time {
  font-weight: bold;
  color: #2c3e50;
}

.block-duration {
  color: #7f8c8d;
  font-weight: normal;
  margin-left: 10px;
}

.block-actions {
  display: flex;
  gap: 8px;
}

.regenerate-btn, .edit-btn {
  background: none;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 4px 8px;
  cursor: pointer;
  transition: 0.3s;
}

.regenerate-btn:hover, .edit-btn:hover {
  background: #f0f0f0;
}

.regenerate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.block-content p {
  line-height: 1.6;
  color: #555;
}

.modal-buttons {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
}

.confirm-btn, .cancel-btn, .save-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.2s ease;
  font-family: inherit;
}

.confirm-btn, .save-btn {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
}

.confirm-btn:hover:not(:disabled), .save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(14, 165, 233, 0.45);
}

.confirm-btn:disabled, .save-btn:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  opacity: 0.6;
  transform: none;
}

.cancel-btn {
  background: #f3f4f6;
  color: #374151;
}

.cancel-btn:hover {
  background: #e5e7eb;
  color: #111827;
}

.loading, .error {
  text-align: center;
  padding: 40px;
  font-size: 18px;
}

.error {
  color: #e74c3c;
  font-weight: bold;
}

.modal-header__tools {
  display: flex;
  align-items: center;
  gap: 8px;
}

.view-ai-fab {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: linear-gradient(145deg, #faf5ff 0%, #eef2ff 100%);
  cursor: pointer;
  font-size: 20px;
  line-height: 1;
  transition: box-shadow 0.2s ease, transform 0.15s ease;
}

.view-ai-fab:hover {
  box-shadow: 0 4px 14px rgba(99, 102, 241, 0.25);
  transform: translateY(-1px);
}

.view-ai-box {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 16px 18px;
  margin-bottom: 20px;
}

.view-ai-box__hint {
  margin: 0 0 12px;
  font-size: 14px;
  color: #4b5563;
  line-height: 1.5;
}

.view-ai-box__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 8px;
}

.view-ai-box__loading {
  font-size: 14px;
  color: #6366f1;
  margin: 8px 0 0;
}

.view-ai-box__error {
  color: #dc2626;
  font-size: 14px;
  margin: 8px 0 0;
}

.view-ai-box__answer {
  margin-top: 12px;
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  white-space: pre-wrap;
  line-height: 1.55;
  color: #1f2937;
  font-size: 14px;
}

.ai-fab {
  position: fixed;
  right: 24px;
  bottom: 24px;
  z-index: 1005;
  width: auto;
  min-height: 52px;
  height: auto;
  padding: 12px 18px;
  border-radius: 999px;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
  color: #fff;
  box-shadow: 0 8px 24px rgba(37, 99, 235, 0.4);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  max-width: min(calc(100vw - 32px), 340px);
  text-align: left;
}

.ai-fab:hover {
  transform: scale(1.02);
  box-shadow: 0 10px 28px rgba(37, 99, 235, 0.48);
}

.ai-fab__glyph {
  font-size: 22px;
  line-height: 1;
  flex-shrink: 0;
}

.ai-fab__label {
  font-size: 14px;
  font-weight: 700;
  line-height: 1.25;
  text-decoration: underline;
  text-underline-offset: 3px;
}

.topic-panel-overlay {
  position: fixed;
  inset: 0;
  z-index: 1100;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(3px);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 16px;
}

@media (min-width: 640px) {
  .topic-panel-overlay {
    align-items: center;
  }
}

.topic-panel {
  width: 100%;
  max-width: 520px;
  max-height: min(90vh, 640px);
  overflow-y: auto;
  background: #fff;
  border-radius: 18px;
  padding: 20px 22px 24px;
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.2);
}

.topic-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.topic-panel__head h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #111827;
}

.topic-panel__head-actions {
  display: flex;
  gap: 6px;
}

.topic-panel__icon-btn {
  border: 1px solid #e5e7eb;
  background: #f9fafb;
  border-radius: 8px;
  width: 36px;
  height: 32px;
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
}

.topic-panel__icon-btn:hover {
  background: #f3f4f6;
}

.topic-panel__lead {
  font-size: 14px;
  color: #6b7280;
  margin: 0 0 16px;
  line-height: 1.5;
}

.topic-panel__actions {
  margin-bottom: 12px;
}

.topic-panel__status,
.topic-panel__error,
.topic-panel__empty {
  font-size: 14px;
  margin: 8px 0;
}

.topic-panel__error {
  color: #dc2626;
}

.topic-panel__empty {
  color: #9ca3af;
}

.topic-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.topic-list__item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
}

.topic-list__item:last-child {
  border-bottom: none;
}

.topic-list__text {
  flex: 1;
  font-size: 14px;
  color: #374151;
  line-height: 1.45;
}

.topic-list__apply {
  flex-shrink: 0;
  font-size: 13px;
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid #c7d2fe;
  background: #eef2ff;
  color: #4338ca;
  cursor: pointer;
  font-weight: 600;
}

.topic-list__apply:hover {
  background: #e0e7ff;
}

@media (max-width: 768px) {
  .meeting-design-container {
    margin-left: 0;
    width: 100%;
    padding: 15px;
  }
  
  .designs-grid {
    grid-template-columns: 1fr;
  }
  
  .modal {
    width: 95%;
    padding: 20px;
  }
  
  .constraint-labels {
    grid-template-columns: 1fr;
  }

  .ai-fab {
    right: 16px;
    bottom: 16px;
  }
}
</style>
