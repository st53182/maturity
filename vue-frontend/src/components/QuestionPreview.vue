<template>
  <div class="modal-overlay" v-if="show" @click.self="$emit('close')">
    <div class="modal question-preview">
      <div class="modal-header">
        <h2>{{ $t('surveys.preview.title') }}</h2>
        <button type="button" @click="$emit('close')" class="close-btn" :aria-label="$t('surveys.preview.close')">✖</button>
      </div>
      
      <div class="survey-title-section">
        <h3>{{ surveyTitle }}</h3>
        <span class="survey-type-badge">{{ surveyType.toUpperCase() }}</span>
      </div>
      
      <div class="questions-list">
        <div v-for="(question, index) in questions" :key="index" class="question-item">
          <div class="question-header">
            <span class="question-number">{{ index + 1 }}.</span>
            <div class="question-content">
              <span class="question-text">{{ question.question }}</span>
              <span v-if="question.required" class="required-badge">{{ $t('surveys.preview.required') }}</span>
            </div>
            <span class="question-type">{{ getQuestionTypeLabel(question.type) }}</span>
          </div>
          
          <div v-if="question.options" class="question-options">
            <span v-for="option in question.options" :key="option.value || option" class="option-tag">
              {{ typeof option === 'object' ? option.text : option }}
            </span>
          </div>
          
          <div v-if="question.type === 'matrix'" class="matrix-preview">
            <div class="matrix-info">
              <div class="matrix-rows">
                <div v-for="(row, idx) in (question.rows || [])" :key="idx" class="row-item">
                  {{ typeof row === 'object' ? row.text : row }}
                </div>
              </div>
              <div class="matrix-scale">
                <span class="scale-label">{{ $t('surveys.preview.matrixScaleLabel') }}</span>
                <span v-for="(col, idx) in (question.columns || question.scale || [])" :key="idx" class="scale-item">
                  {{ typeof col === 'object' ? col.text : col }}
                </span>
              </div>
            </div>
          </div>
          
          <div v-if="question.type === 'scale'" class="scale-preview">
            <span class="scale-info">{{ $t('surveys.preview.scaleInfo', { min: question.min || 1, max: question.max || 10 }) }}</span>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <p class="preview-edit-hint">{{ $t('surveys.preview.editHint') }}</p>
        <div class="modal-footer__row">
          <div class="footer-info">
            <span>{{ $t('surveys.preview.totalQuestions', { count: questions.length }) }}</span>
          </div>
          <div class="modal-buttons qp-actions">
            <button type="button" class="qp-action-btn qp-action-btn--secondary" @click="editQuestions">
              ✏️ {{ $t('surveys.preview.editBtn') }}
            </button>
            <button type="button" class="qp-action-btn qp-action-btn--primary" @click="confirmCreate">
              ✅ {{ $t('surveys.preview.confirmBtn') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'QuestionPreview',
  props: {
    show: Boolean,
    questions: Array,
    surveyTitle: String,
    surveyType: String
  },
  methods: {
    getQuestionTypeLabel(type) {
      const keys = {
        text: 'surveys.preview.typeText',
        textarea: 'surveys.preview.typeTextarea',
        radio: 'surveys.preview.typeRadio',
        scale: 'surveys.preview.typeScale',
        matrix: 'surveys.preview.typeMatrix'
      }
      const key = keys[type]
      return key ? this.$t(key) : type
    },
    editQuestions() {
      this.$emit('edit-questions')
    },
    confirmCreate() {
      this.$emit('confirm-create')
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1120;
  padding: 20px;
}

.modal {
  background: white;
  border-radius: 20px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  max-height: 90vh;
}

.question-preview {
  max-width: 900px;
  width: 100%;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #111827;
}

.survey-title-section {
  padding: 20px 32px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.survey-title-section h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #111827;
}

.survey-type-badge {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 6px 16px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.questions-list {
  padding: 24px 32px;
  overflow-y: auto;
  flex: 1;
}

.question-item {
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  background: #ffffff;
  transition: all 0.2s ease;
}

.question-item:hover {
  border-color: #cbd5e1;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.question-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.question-number {
  font-weight: 700;
  color: #3b82f6;
  min-width: 32px;
  font-size: 16px;
}

.question-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.question-text {
  font-weight: 500;
  font-size: 15px;
  color: #111827;
  line-height: 1.5;
}

.required-badge {
  background: #fee2e2;
  color: #dc2626;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 600;
  align-self: flex-start;
}

.question-type {
  background: #f3f4f6;
  padding: 4px 12px;
  border-radius: 8px;
  font-size: 12px;
  color: #6b7280;
  font-weight: 500;
  white-space: nowrap;
}

.question-options {
  margin-top: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.option-tag {
  display: inline-block;
  background: #f0f9ff;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 13px;
  border: 1px solid #bae6fd;
  color: #0369a1;
}

.matrix-preview {
  margin-top: 12px;
}

.matrix-info {
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.matrix-rows {
  margin-bottom: 12px;
}

.row-item {
  padding: 8px 12px;
  background: white;
  border-radius: 6px;
  margin-bottom: 6px;
  font-size: 13px;
  color: #374151;
  border: 1px solid #e5e7eb;
}

.matrix-scale {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.scale-label {
  font-weight: 600;
  font-size: 12px;
  color: #6b7280;
  margin-right: 8px;
}

.scale-item {
  background: white;
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 11px;
  color: #4b5563;
  border: 1px solid #d1d5db;
}

.scale-preview {
  margin-top: 12px;
}

.scale-info {
  font-size: 13px;
  color: #4b5563;
  background: #f0f9ff;
  padding: 8px 12px;
  border-radius: 8px;
  border: 1px solid #bae6fd;
  display: inline-block;
}

.modal-footer {
  padding: 20px 32px;
  border-top: 1px solid #e5e7eb;
  background: #f9fafb;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 14px;
}

.preview-edit-hint {
  margin: 0;
  font-size: 13px;
  line-height: 1.5;
  color: #475569;
}

.modal-footer__row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  flex-wrap: wrap;
}

.footer-info {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.modal-buttons.qp-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: stretch;
  gap: 12px;
}

.qp-action-btn {
  flex: 1 1 220px;
  min-height: 48px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 12px 20px;
  border: none;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  line-height: 1.35;
  box-sizing: border-box;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  white-space: normal;
}

.qp-action-btn--secondary {
  background: linear-gradient(135deg, #64748b 0%, #475569 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(71, 85, 105, 0.35);
}

.qp-action-btn--secondary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(71, 85, 105, 0.45);
}

.qp-action-btn--primary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: #fff;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.qp-action-btn--primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

@media (max-width: 768px) {
  .modal {
    max-height: 95vh;
  }
  
  .modal-header, .survey-title-section, .questions-list, .modal-footer {
    padding: 16px 20px;
  }
  
  .modal-buttons {
    flex-direction: column;
    width: 100%;
  }
  
  .qp-action-btn {
    flex: 1 1 100%;
    width: 100%;
  }
  
  .modal-footer__row {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
