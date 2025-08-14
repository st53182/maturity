<template>
  <div class="modal-overlay" v-if="show">
    <div class="modal template-editor">
      <h2>{{ isEditing ? 'Редактировать шаблон' : 'Создать шаблон' }}</h2>
      
      <input v-model="templateName" placeholder="Название шаблона" class="template-input" />
      
      <div class="questions-editor">
        <h3>Вопросы</h3>
        <div v-for="(question, index) in questions" :key="index" class="question-item">
          <div class="question-header">
            <input v-model="question.question" placeholder="Текст вопроса" class="question-text" />
            <select v-model="question.type" class="question-type">
              <option value="text">Текст</option>
              <option value="textarea">Длинный текст</option>
              <option value="radio">Выбор варианта</option>
              <option value="scale">Шкала оценки</option>
              <option value="matrix">Матрица оценок</option>
            </select>
            <button @click="removeQuestion(index)" class="remove-btn">Удалить</button>
          </div>
          
          <div v-if="question.type === 'radio'" class="options-editor">
            <h4>Варианты ответов:</h4>
            <div v-for="(option, optIndex) in question.options" :key="optIndex" class="option-item">
              <input v-model="option.text" placeholder="Текст варианта" />
              <button @click="removeOption(index, optIndex)" class="remove-option-btn">×</button>
            </div>
            <button @click="addOption(index)" class="add-option-btn">Добавить вариант</button>
          </div>
          
          <div v-if="question.type === 'scale'" class="scale-editor">
            <label>Минимум: <input v-model.number="question.min" type="number" /></label>
            <label>Максимум: <input v-model.number="question.max" type="number" /></label>
          </div>
          
          <div v-if="question.type === 'matrix'" class="matrix-editor">
            <h4>Строки матрицы:</h4>
            <div v-for="(row, rowIndex) in question.rows" :key="rowIndex" class="matrix-row">
              <input v-model="row.text" placeholder="Текст строки" />
              <button @click="removeMatrixRow(index, rowIndex)" class="remove-option-btn">×</button>
            </div>
            <button @click="addMatrixRow(index)" class="add-option-btn">Добавить строку</button>
            
            <h4>Колонки матрицы:</h4>
            <div v-for="(col, colIndex) in question.columns" :key="colIndex" class="matrix-col">
              <input v-model="col.text" placeholder="Текст колонки" />
              <button @click="removeMatrixCol(index, colIndex)" class="remove-option-btn">×</button>
            </div>
            <button @click="addMatrixCol(index)" class="add-option-btn">Добавить колонку</button>
          </div>
        </div>
        <button @click="addQuestion" class="add-question-btn">Добавить вопрос</button>
      </div>
      
      <div class="modal-buttons">
        <button @click="saveTemplate" class="confirm-btn">Сохранить</button>
        <button @click="$emit('close')" class="cancel-btn">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'TemplateEditor',
  props: {
    show: Boolean,
    template: Object,
    surveyType: String
  },
  data() {
    return {
      templateName: '',
      questions: []
    }
  },
  computed: {
    isEditing() {
      return !!this.template
    }
  },
  watch: {
    template: {
      handler(newTemplate) {
        if (newTemplate) {
          this.templateName = newTemplate.name
          this.questions = JSON.parse(JSON.stringify(newTemplate.questions))
        } else {
          this.resetForm()
        }
      },
      immediate: true
    }
  },
  methods: {
    resetForm() {
      this.templateName = ''
      this.questions = []
    },
    addQuestion() {
      this.questions.push({
        id: Date.now(),
        type: 'text',
        question: '',
        required: false
      })
    },
    removeQuestion(index) {
      this.questions.splice(index, 1)
    },
    addOption(questionIndex) {
      if (!this.questions[questionIndex].options) {
        this.questions[questionIndex].options = []
      }
      this.questions[questionIndex].options.push({ text: '', value: '' })
    },
    removeOption(questionIndex, optionIndex) {
      this.questions[questionIndex].options.splice(optionIndex, 1)
    },
    addMatrixRow(questionIndex) {
      if (!this.questions[questionIndex].rows) {
        this.questions[questionIndex].rows = []
      }
      this.questions[questionIndex].rows.push({ text: '', value: '' })
    },
    removeMatrixRow(questionIndex, rowIndex) {
      this.questions[questionIndex].rows.splice(rowIndex, 1)
    },
    addMatrixCol(questionIndex) {
      if (!this.questions[questionIndex].columns) {
        this.questions[questionIndex].columns = []
      }
      this.questions[questionIndex].columns.push({ text: '', value: '' })
    },
    removeMatrixCol(questionIndex, colIndex) {
      this.questions[questionIndex].columns.splice(colIndex, 1)
    },
    async saveTemplate() {
      try {
        const token = localStorage.getItem('token')
        const templateData = {
          name: this.templateName,
          survey_type: this.surveyType,
          questions: this.questions
        }
        
        if (this.isEditing) {
          await axios.put(`/api/survey-templates/${this.template.id}`, templateData, {
            headers: { Authorization: `Bearer ${token}` }
          })
        } else {
          await axios.post('/api/survey-templates', templateData, {
            headers: { Authorization: `Bearer ${token}` }
          })
        }
        
        this.$emit('saved')
        this.$emit('close')
      } catch (error) {
        console.error('Error saving template:', error)
        alert('Ошибка сохранения шаблона')
      }
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

.template-editor {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  max-width: 800px;
  max-height: 80vh;
  overflow-y: auto;
  width: 90%;
}

.template-input, .question-text {
  width: 100%;
  padding: 0.5rem;
  margin-bottom: 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.questions-editor {
  margin: 1rem 0;
}

.question-item {
  border: 1px solid #eee;
  padding: 1rem;
  margin-bottom: 1rem;
  border-radius: 4px;
}

.question-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.question-type {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.remove-btn, .remove-option-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
}

.add-question-btn, .add-option-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  margin-top: 0.5rem;
}

.options-editor, .scale-editor, .matrix-editor {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f8f9fa;
  border-radius: 4px;
}

.option-item, .matrix-row, .matrix-col {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.option-item input, .matrix-row input, .matrix-col input {
  flex: 1;
  padding: 0.25rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.scale-editor label {
  display: inline-block;
  margin-right: 1rem;
}

.scale-editor input {
  width: 80px;
  padding: 0.25rem;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.modal-buttons {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.confirm-btn {
  background: #007bff;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

.cancel-btn {
  background: #6c757d;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}
</style>
