<template>
  <div class="modal-overlay" v-if="show" @click.self="$emit('close')">
    <div class="modal question-preview">
      <div class="modal-header">
        <h2>Предпросмотр опросника</h2>
        <button @click="$emit('close')" class="close-btn">✖</button>
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
              <span v-if="question.required" class="required-badge">Обязательный</span>
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
                <span class="scale-label">Шкала оценки:</span>
                <span v-for="(col, idx) in (question.columns || question.scale || [])" :key="idx" class="scale-item">
                  {{ typeof col === 'object' ? col.text : col }}
                </span>
              </div>
            </div>
          </div>
          
          <div v-if="question.type === 'scale'" class="scale-preview">
            <span class="scale-info">Шкала: {{ question.min || 1 }} - {{ question.max || 10 }}</span>
          </div>
        </div>
      </div>
      
      <div class="modal-footer">
        <div class="footer-info">
          <span>Всего вопросов: {{ questions.length }}</span>
        </div>
        <div class="modal-buttons">
          <button @click="editQuestions" class="edit-btn">✏️ Редактировать вопросы</button>
          <button @click="confirmCreate" class="confirm-btn">✅ Создать опросник</button>
          <button @click="$emit('close')" class="cancel-btn">Отмена</button>
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
      const labels = {
        'text': 'Текст',
        'textarea': 'Длинный текст', 
        'radio': 'Выбор варианта',
        'scale': 'Шкала оценки',
        'matrix': 'Матрица оценок'
      }
      return labels[type] || type
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
  z-index: 1000;
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
  justify-content: space-between;
  align-items: center;
}

.footer-info {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.modal-buttons {
  display: flex;
  gap: 12px;
}

.edit-btn, .confirm-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  min-width: 140px;
}

.edit-btn {
  background: linear-gradient(135deg, #6b7280 0%, #4b5563 100%);
  color: white;
  box-shadow: 0 2px 8px rgba(107, 114, 128, 0.3);
}

.edit-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(107, 114, 128, 0.4);
}

.confirm-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.confirm-btn:hover {
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
  
  .edit-btn, .confirm-btn, .cancel-btn {
    width: 100%;
  }
  
  .modal-footer {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
}
</style>
