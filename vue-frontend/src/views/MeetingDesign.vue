<template>
  <div class="meeting-design-container">
    <h1>{{ $t('meetingDesign.title') }}</h1>

    <div v-if="loading" class="loading">⏳ {{ $t('common.loading') }}</div>
    <div v-else-if="error" class="error">❌ {{ error }}</div>

    <div v-else>
      <div class="action-buttons">
        <button class="create-btn" @click="showCreateModal = true">
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
          <p><strong>{{ $t('meetingDesign.goal') }}:</strong> {{ design.goal.substring(0, 100) }}...</p>
          
          <div class="design-actions">
            <button class="view-btn" @click="viewDesign(design)">👁️ Просмотр</button>
            <button class="delete-btn" @click="deleteDesign(design.id)">🗑️ {{ $t('common.delete') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Meeting Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal create-modal">
        <h2>{{ $t('meetingDesign.createNew') }}</h2>
        
        <div class="form-group">
          <label>{{ $t('meetingDesign.meetingTitle') }}</label>
          <input v-model="newDesign.title" type="text" class="form-input" />
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
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.selectTeam') }}</label>
          <select v-model="newDesign.team_id" class="form-select">
            <option value="">Без команды</option>
            <option v-for="team in teams" :key="team.id" :value="team.id">{{ team.name }}</option>
          </select>
        </div>

        <div class="form-group">
          <label>{{ $t('meetingDesign.constraints') }}</label>
          <div class="constraint-labels">
            <label v-for="(label, key) in constraintLabels" :key="key" class="constraint-label">
              <input type="checkbox" :value="key" v-model="selectedConstraints" />
              {{ label }}
            </label>
          </div>
          <textarea v-model="newDesign.constraints" class="form-textarea" rows="2" placeholder="Дополнительные ограничения..."></textarea>
        </div>

        <div class="modal-buttons">
          <button class="confirm-btn" @click="generateDesign" :disabled="generating">
            {{ generating ? $t('meetingDesign.creating') : $t('meetingDesign.generate') }}
          </button>
          <button class="cancel-btn" @click="closeCreateModal">{{ $t('common.cancel') }}</button>
        </div>
      </div>
    </div>

    <!-- View Design Modal -->
    <div v-if="showViewModal && currentDesign" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal view-modal">
        <div class="modal-header">
          <h2>{{ currentDesign.title }}</h2>
          <button class="close-btn" @click="showViewModal = false">✕</button>
        </div>

        <div class="design-info">
          <p><strong>{{ $t('meetingDesign.meetingType') }}:</strong> {{ currentDesign.meeting_type }}</p>
          <p><strong>{{ $t('meetingDesign.goal') }}:</strong> {{ currentDesign.goal }}</p>
          <p><strong>{{ $t('meetingDesign.duration') }}:</strong> {{ currentDesign.duration_minutes }} {{ $t('meetingDesign.minutes') }}</p>
          <p v-if="currentDesign.constraints"><strong>{{ $t('meetingDesign.constraints') }}:</strong> {{ currentDesign.constraints }}</p>
        </div>

        <div class="blocks-container">
          <h3>{{ $t('meetingDesign.blocks') }}</h3>
          <div v-for="(block, index) in currentDesign.blocks" :key="index" class="block-card">
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
      constraintLabels: {}
    };
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
  },
  methods: {
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
          block_index: blockIndex
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

    viewDesign(design) {
      this.currentDesign = { ...design };
      this.showViewModal = true;
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
.meeting-design-container {
  margin-left: 70px;
  padding: 32px;
  width: calc(100% - 70px);
  box-sizing: border-box;
  background: #ffffff;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
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
  margin-bottom: 8px;
  font-weight: 600;
  color: #374151;
  font-size: 14px;
}

.form-input, .form-select, .form-textarea {
  width: 100%;
  padding: 12px 16px;
  border: 1.5px solid #d1d5db;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease;
  font-family: inherit;
  background: #ffffff;
  box-sizing: border-box;
}

.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.constraint-labels {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.constraint-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: normal;
  cursor: pointer;
}

.constraint-label input[type="checkbox"] {
  width: auto;
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
  border-left: 4px solid #3b82f6;
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
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.confirm-btn:hover:not(:disabled), .save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
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
}
</style>
