<template>
  <div class="qa-practice">
    <header class="qa-header">
      <h1>🔍 {{ $t('qa.title') }}</h1>
      <p class="qa-subtitle">{{ $t('qa.subtitle') }}</p>
      <p class="qa-hint">{{ $t('qa.linkHint') }} <code>{{ qaLink }}</code></p>
    </header>

    <div class="tasks-list">
      <section
        v-for="(task, index) in tasks"
        :key="task.id"
        class="task-card"
        :class="{ done: isTaskDone(task.id), open: openedTaskId === task.id }"
      >
        <div class="task-head" @click="toggleTask(task.id)">
          <span class="task-num">{{ index + 1 }}</span>
          <h2>{{ $t(task.titleKey) }}</h2>
          <span class="task-done-badge" v-if="isTaskDone(task.id)">✅</span>
          <span class="task-chevron">{{ openedTaskId === task.id ? '▼' : '▶' }}</span>
        </div>

        <div v-show="openedTaskId === task.id" class="task-body">
          <p class="task-desc">{{ $t(task.descKey) }}</p>

          <!-- Задание 1: Найди баг (опечатка) -->
          <div v-if="task.id === 'find-bug'" class="task-content">
            <p>{{ $t('qa.findBugInstruction') }}</p>
            <div class="find-bug-text">
              {{ $t('qa.findBugTextBefore') }}<span class="bug-word" :class="{ found: bugFound }" @click="bugFound = true">{{ $t('qa.findBugTypo') }}</span>{{ $t('qa.findBugTextAfter') }}
            </div>
            <p v-if="bugFound" class="success-msg">🎉 {{ $t('qa.findBugSuccess') }}</p>
            <button v-if="bugFound && !isTaskDone('find-bug')" class="mark-done-btn" @click="markDone('find-bug')">{{ $t('qa.markDone') }}</button>
          </div>

          <!-- Задание 2: Чек-лист -->
          <div v-if="task.id === 'checklist'" class="task-content">
            <p>{{ $t('qa.checklistInstruction') }}</p>
            <ul class="qa-checklist">
              <li v-for="item in checklistItems" :key="item.id">
                <label>
                  <input type="checkbox" v-model="item.checked" />
                  {{ $t(item.textKey) }}
                </label>
              </li>
            </ul>
            <p class="hint">{{ $t('qa.checklistHint') }}</p>
            <button v-if="checklistDone && !isTaskDone('checklist')" class="mark-done-btn" @click="markDone('checklist')">{{ $t('qa.markDone') }}</button>
          </div>

          <!-- Задание 3: Лучший баг-репорт -->
          <div v-if="task.id === 'bug-report'" class="task-content">
            <p>{{ $t('qa.bugReportInstruction') }}</p>
            <div class="options-list">
              <label
                v-for="opt in bugReportOptions"
                :key="opt.id"
                class="option-item"
                :class="{ selected: selectedBugReport === opt.id, correct: bugReportAnswered && opt.correct }"
              >
                <input type="radio" :value="opt.id" v-model="selectedBugReport" @change="onBugReportSelect" />
                <span>{{ $t(opt.textKey) }}</span>
              </label>
            </div>
            <p v-if="bugReportAnswered" class="success-msg" :class="{ wrong: selectedBugReport !== 'b' }">
              {{ selectedBugReport === 'b' ? '🎉 ' + $t('qa.bugReportSuccess') : $t('qa.bugReportHintWrong') }}
            </p>
            <button v-if="bugReportAnswered && selectedBugReport === 'b' && !isTaskDone('bug-report')" class="mark-done-btn" @click="markDone('bug-report')">{{ $t('qa.markDone') }}</button>
          </div>

          <!-- Задание 4: Приоритет проверок -->
          <div v-if="task.id === 'priority'" class="task-content">
            <p>{{ $t('qa.priorityInstruction') }}</p>
            <div class="options-list">
              <label
                v-for="opt in priorityOptions"
                :key="opt.id"
                class="option-item"
                :class="{ selected: selectedPriority === opt.id }"
              >
                <input type="radio" :value="opt.id" v-model="selectedPriority" />
                <span>{{ $t(opt.textKey) }}</span>
              </label>
            </div>
            <p class="hint">{{ $t('qa.priorityHint') }}</p>
            <button v-if="selectedPriority && !isTaskDone('priority')" class="mark-done-btn" @click="markDone('priority')">{{ $t('qa.markDone') }}</button>
          </div>

          <!-- Задание 5: Мини-викторина -->
          <div v-if="task.id === 'quiz'" class="task-content">
            <p>{{ $t('qa.quizQuestion') }}</p>
            <div class="options-list">
              <label
                v-for="opt in quizOptions"
                :key="opt.id"
                class="option-item"
                :class="{ selected: selectedQuiz === opt.id, correct: quizAnswered && opt.correct }"
              >
                <input type="radio" :value="opt.id" v-model="selectedQuiz" @change="quizAnswered = true" />
                <span>{{ $t(opt.textKey) }}</span>
              </label>
            </div>
            <p v-if="quizAnswered && selectedQuiz === 'b'" class="success-msg">🎉 {{ $t('qa.quizSuccess') }}</p>
            <button v-if="quizAnswered && selectedQuiz === 'b' && !isTaskDone('quiz')" class="mark-done-btn" @click="markDone('quiz')">{{ $t('qa.markDone') }}</button>
          </div>
        </div>
      </section>
    </div>

    <div class="qa-footer">
      <p>{{ $t('qa.footer') }} 🚀</p>
    </div>
  </div>
</template>

<script>
const STORAGE_KEY = 'qa_practice_done';
const TASKS = [
  { id: 'find-bug', titleKey: 'qa.task1Title', descKey: 'qa.task1Desc' },
  { id: 'checklist', titleKey: 'qa.task2Title', descKey: 'qa.task2Desc' },
  { id: 'bug-report', titleKey: 'qa.task3Title', descKey: 'qa.task3Desc' },
  { id: 'priority', titleKey: 'qa.task4Title', descKey: 'qa.task4Desc' },
  { id: 'quiz', titleKey: 'qa.task5Title', descKey: 'qa.task5Desc' },
];

export default {
  name: 'QAPractice',
  data() {
    return {
      tasks: TASKS,
      openedTaskId: TASKS[0]?.id || null,
      doneIds: this.loadDoneIds(),
      bugFound: false,
      checklistItems: [
        { id: 1, textKey: 'qa.checklist1', checked: false },
        { id: 2, textKey: 'qa.checklist2', checked: false },
        { id: 3, textKey: 'qa.checklist3', checked: false },
        { id: 4, textKey: 'qa.checklist4', checked: false },
      ],
      selectedBugReport: null,
      bugReportAnswered: false,
      bugReportOptions: [
        { id: 'a', textKey: 'qa.bugReportA', correct: false },
        { id: 'b', textKey: 'qa.bugReportB', correct: true },
        { id: 'c', textKey: 'qa.bugReportC', correct: false },
      ],
      selectedPriority: null,
      priorityOptions: [
        { id: 'a', textKey: 'qa.priorityA' },
        { id: 'b', textKey: 'qa.priorityB' },
        { id: 'c', textKey: 'qa.priorityC' },
      ],
      selectedQuiz: null,
      quizAnswered: false,
      quizOptions: [
        { id: 'a', textKey: 'qa.quizA', correct: false },
        { id: 'b', textKey: 'qa.quizB', correct: true },
        { id: 'c', textKey: 'qa.quizC', correct: false },
      ],
    };
  },
  computed: {
    qaLink() {
      return typeof window !== 'undefined' ? window.location.origin + '/qa' : '/qa';
    },
    checklistDone() {
      return this.checklistItems.some((i) => i.checked);
    },
  },
  methods: {
    loadDoneIds() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
      } catch {
        return [];
      }
    },
    saveDoneIds() {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(this.doneIds));
    },
    isTaskDone(id) {
      return this.doneIds.includes(id);
    },
    markDone(id) {
      if (!this.doneIds.includes(id)) {
        this.doneIds = [...this.doneIds, id];
        this.saveDoneIds();
      }
    },
    toggleTask(id) {
      this.openedTaskId = this.openedTaskId === id ? null : id;
    },
    onBugReportSelect() {
      this.bugReportAnswered = true;
    },
  },
};
</script>

<style scoped>
.qa-practice {
  max-width: 700px;
  margin: 0 auto;
  padding: 24px 16px;
}

.qa-header {
  text-align: center;
  margin-bottom: 32px;
}

.qa-header h1 {
  font-size: 1.75rem;
  color: #333;
  margin-bottom: 8px;
}

.qa-subtitle {
  color: #555;
  font-size: 1.05rem;
  margin-bottom: 12px;
}

.qa-hint {
  font-size: 0.9rem;
  color: #666;
}

.qa-hint code {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 6px;
  word-break: break-all;
}

.tasks-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  background: #fff;
  border: 1px solid #e0e0e0;
  border-radius: 12px;
  overflow: hidden;
  transition: box-shadow 0.2s ease;
}

.task-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

.task-card.done {
  border-color: #a8e6cf;
  background: linear-gradient(to bottom, #f0fff4 0%, #fff 30%);
}

.task-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  cursor: pointer;
  user-select: none;
}

.task-num {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  flex-shrink: 0;
}

.task-head h2 {
  flex: 1;
  margin: 0;
  font-size: 1.1rem;
  color: #333;
}

.task-done-badge {
  font-size: 1.2rem;
}

.task-chevron {
  color: #888;
  font-size: 0.9rem;
}

.task-body {
  padding: 0 20px 20px;
  border-top: 1px solid #eee;
  padding-top: 16px;
}

.task-desc {
  color: #555;
  margin-bottom: 16px;
  font-size: 0.95rem;
}

.task-content {
  margin-top: 8px;
}

.find-bug-text {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  margin: 12px 0;
  line-height: 1.6;
  cursor: default;
}

.find-bug-text .bug-word {
  text-decoration: underline;
  text-decoration-style: dotted;
  cursor: pointer;
  color: #c0392b;
}

.find-bug-text .bug-word.found {
  background: #a8e6cf;
  color: #1e7e34;
  border-radius: 4px;
}

.qa-checklist {
  list-style: none;
  padding: 0;
  margin: 12px 0;
}

.qa-checklist li {
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.qa-checklist label {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin: 12px 0;
}

.option-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}

.option-item:hover,
.option-item.selected {
  border-color: #667eea;
  background: #f5f3ff;
}

.option-item.correct {
  border-color: #27ae60;
  background: #e8f8f0;
}

.option-item input {
  margin-top: 2px;
}

.success-msg {
  color: #1e7e34;
  font-weight: 500;
  margin-top: 12px;
}

.success-msg.wrong {
  color: #b8860b;
}

.hint {
  color: #666;
  font-size: 0.9rem;
  margin-top: 12px;
}

.mark-done-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s;
}

.mark-done-btn:hover {
  transform: scale(1.02);
}

.qa-footer {
  text-align: center;
  margin-top: 40px;
  padding: 24px;
  background: #f8f9fa;
  border-radius: 12px;
  color: #555;
}
</style>
