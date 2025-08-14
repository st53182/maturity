<template>
  <div class="modal-overlay" v-if="show">
    <div class="modal question-preview">
      <h2>Предпросмотр вопросов: {{ surveyTitle }}</h2>
      
      <div class="questions-list">
        <div v-for="(question, index) in questions" :key="index" class="question-item">
          <div class="question-header">
            <span class="question-number">{{ index + 1 }}.</span>
            <span class="question-text">{{ question.question }}</span>
            <span class="question-type">{{ getQuestionTypeLabel(question.type) }}</span>
          </div>
          
          <div v-if="question.options" class="question-options">
            <span v-for="option in question.options" :key="option.value" class="option-tag">
              {{ option.text }}
            </span>
          </div>
          
          <div v-if="question.type === 'matrix'" class="matrix-preview">
            <div class="matrix-rows">
              <span v-for="row in question.rows" :key="row.value" class="row-tag">
                {{ row.text }}
              </span>
            </div>
          </div>
          
          <div v-if="question.type === 'scale'" class="scale-preview">
            <span class="scale-info">Шкала: {{ question.min || 1 }} - {{ question.max || 10 }}</span>
          </div>
        </div>
      </div>
      
      <div class="modal-buttons">
        <button @click="editQuestions" class="edit-btn">Редактировать вопросы</button>
        <button @click="confirmCreate" class="confirm-btn">Создать опросник</button>
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
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
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.question-preview {
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
}

.questions-list {
  margin: 20px 0;
}

.question-item {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 15px;
  background: #f9f9f9;
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
  min-width: 30px;
}

.question-text {
  flex: 1;
  font-weight: 500;
}

.question-type {
  background: #ecf0f1;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.question-options, .matrix-preview {
  margin-top: 10px;
}

.option-tag, .row-tag {
  display: inline-block;
  background: #f8f9fa;
  padding: 2px 6px;
  margin: 2px;
  border-radius: 3px;
  font-size: 12px;
  border: 1px solid #dee2e6;
}

.scale-preview {
  margin-top: 10px;
}

.scale-info {
  font-size: 12px;
  color: #666;
  background: #e9ecef;
  padding: 4px 8px;
  border-radius: 4px;
}

.modal-buttons {
  display: flex;
  gap: 15px;
  justify-content: flex-end;
  margin-top: 30px;
}

.edit-btn, .confirm-btn, .cancel-btn {
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.edit-btn {
  background: #6c757d;
  color: white;
}

.edit-btn:hover {
  background: #5a6268;
}

.confirm-btn {
  background: #2ecc71;
  color: white;
}

.confirm-btn:hover {
  background: #27ae60;
}

.cancel-btn {
  background: #95a5a6;
  color: white;
}

.cancel-btn:hover {
  background: #7f8c8d;
}
</style>
