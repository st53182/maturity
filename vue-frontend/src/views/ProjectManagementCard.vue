<template>
  <div class="project-card-page">
    <div class="page-actions">
      <button class="export-pdf-btn" @click="exportPdf" :disabled="exporting">
        {{ exporting ? 'Формируем PDF…' : '📄 Скачать PDF' }}
      </button>
    </div>

    <div ref="pdfContent" class="project-card-a3">
      <header class="card-header">
        <h1 class="card-title">Карта управления проектом</h1>
        <input v-model="form.projectName" class="card-project-name" placeholder="Название проекта (например: Открытие нового филиала)" />
      </header>

      <div class="card-grid">
        <!-- ① Активные задачи -->
        <section class="card-section section-tasks">
          <h2>① Активные задачи</h2>
          <p class="section-hint">Только текущие задачи (не более 10). Статусы: Готово, Риск, В работе, Ожидание.</p>
          <table class="tasks-table">
            <thead>
              <tr>
                <th>№</th>
                <th>Задача</th>
                <th>Статус</th>
                <th>Срок</th>
                <th>Кто</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(task, i) in form.tasks" :key="i">
                <td>{{ i + 1 }}</td>
                <td><input v-model="task.name" placeholder="Задача" /></td>
                <td>
                  <select v-model="task.status">
                    <option value="done">Готово</option>
                    <option value="risk">Риск</option>
                    <option value="progress">В работе</option>
                    <option value="waiting">Ожидание</option>
                  </select>
                </td>
                <td><input v-model="task.deadline" placeholder="10.04" class="input-sm" /></td>
                <td><input v-model="task.who" placeholder="Ответственный" class="input-sm" /></td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="add-row-btn" @click="addTask" :disabled="form.tasks.length >= 10">+ Добавить задачу</button>
        </section>

        <!-- ② Приоритеты -->
        <section class="card-section section-priorities">
          <h2>② Приоритеты</h2>
          <p class="section-hint">MUST — критично для запуска, SHOULD — важно, NICE — желательно.</p>
          <div class="priority-block">
            <h3>MUST (критично для запуска)</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesMust" :key="'m'+i">
                <input v-model="form.prioritiesMust[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesMust.push('')">+</button>
          </div>
          <div class="priority-block">
            <h3>SHOULD (важно, но не блокирует)</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesShould" :key="'s'+i">
                <input v-model="form.prioritiesShould[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesShould.push('')">+</button>
          </div>
          <div class="priority-block">
            <h3>NICE (желательно)</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesNice" :key="'n'+i">
                <input v-model="form.prioritiesNice[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesNice.push('')">+</button>
          </div>
        </section>

        <!-- ③ Зависимости -->
        <section class="card-section section-deps">
          <h2>③ Зависимости</h2>
          <p class="section-hint">Цепочки: что от чего зависит (например: Ремонт → Оборудование → Запуск).</p>
          <textarea v-model="form.dependencies" rows="4" placeholder="Опишите цепочки зависимостей по шагам или нарисуйте на флипчарте стрелками"></textarea>
        </section>

        <!-- ④ Узкое место -->
        <section class="card-section section-bottleneck">
          <h2>④ Узкое место</h2>
          <p class="section-hint">Элемент, который ограничивает общий ход. Выделите по имени.</p>
          <input v-model="form.bottleneckTitle" class="bottleneck-title" placeholder="Название узкого места (например: Подрядчик по ремонту)" />
          <textarea v-model="form.bottleneckDesc" rows="3" placeholder="Почему это узкое место: причины, отставание, влияние на следующие задачи"></textarea>
        </section>

        <!-- ⑤ Загрузка ключевых ролей -->
        <section class="card-section section-roles">
          <h2>⑤ Загрузка ключевых ролей</h2>
          <p class="section-hint">Кто перегружен — Норма, Средний, Высокий, Критический.</p>
          <table class="roles-table">
            <thead>
              <tr>
                <th>Роль</th>
                <th>Задач</th>
                <th>Риск перегруза</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(role, i) in form.roles" :key="i">
                <td><input v-model="role.name" placeholder="Роль" /></td>
                <td><input v-model.number="role.tasksCount" type="number" min="0" class="input-num" /></td>
                <td>
                  <select v-model="role.overloadRisk">
                    <option value="normal">Норма</option>
                    <option value="medium">Средний</option>
                    <option value="high">Высокий</option>
                    <option value="critical">Критический</option>
                  </select>
                </td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="add-row-btn" @click="addRole">+ Добавить роль</button>
        </section>

        <!-- ⑥ Решения -->
        <section class="card-section section-decisions">
          <h2>⑥ Что требует управленческого решения</h2>
          <p class="section-hint">Конкретные вопросы для руководства, не отчёт о статусе.</p>
          <div v-for="(item, i) in form.decisions" :key="i" class="decision-item">
            <input v-model="form.decisions[i].question" placeholder="Вопрос (например: Усиливать подрядчика?)" class="decision-q" />
            <textarea v-model="form.decisions[i].context" rows="2" placeholder="Контекст / варианты" class="decision-ctx"></textarea>
          </div>
          <button type="button" class="add-row-btn" @click="form.decisions.push({ question: '', context: '' })">+ Добавить вопрос</button>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

const defaultForm = () => ({
  projectName: '',
  tasks: [
    { name: '', status: 'progress', deadline: '', who: '' },
    { name: '', status: 'progress', deadline: '', who: '' },
  ],
  prioritiesMust: ['', ''],
  prioritiesShould: [''],
  prioritiesNice: [''],
  dependencies: '',
  bottleneckTitle: '',
  bottleneckDesc: '',
  roles: [
    { name: '', tasksCount: 0, overloadRisk: 'normal' },
    { name: '', tasksCount: 0, overloadRisk: 'normal' },
  ],
  decisions: [
    { question: '', context: '' },
  ],
});

export default {
  name: 'ProjectManagementCard',
  data() {
    return {
      form: defaultForm(),
      exporting: false,
    };
  },
  methods: {
    addTask() {
      if (this.form.tasks.length < 10) this.form.tasks.push({ name: '', status: 'progress', deadline: '', who: '' });
    },
    addRole() {
      this.form.roles.push({ name: '', tasksCount: 0, overloadRisk: 'normal' });
    },
    async exportPdf() {
      this.exporting = true;
      try {
        const el = this.$refs.pdfContent;
        if (!el) return;
        const canvas = await html2canvas(el, {
          scale: 2,
          useCORS: true,
          logging: false,
          backgroundColor: '#ffffff',
        });
        const imgData = canvas.toDataURL('image/jpeg', 0.92);
        const pdf = new jsPDF('p', 'mm', 'a4');
        const w = pdf.internal.pageSize.getWidth();
        const h = pdf.internal.pageSize.getHeight();
        const imgW = w;
        const imgH = (canvas.height * w) / canvas.width;
        let yOff = 0;
        while (yOff < imgH) {
          if (yOff > 0) pdf.addPage();
          pdf.addImage(imgData, 'JPEG', 0, -yOff, imgW, imgH);
          yOff += h;
        }
        const name = (this.form.projectName || 'project-card').replace(/[^\w\s-]/g, '').slice(0, 40);
        pdf.save(`карта-проекта-${name || 'project'}.pdf`);
      } catch (e) {
        console.error(e);
        alert('Ошибка при формировании PDF. Попробуйте ещё раз.');
      } finally {
        this.exporting = false;
      }
    },
  },
};
</script>

<style scoped>
.project-card-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.page-actions {
  margin-bottom: 16px;
}

.export-pdf-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.export-pdf-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.project-card-a3 {
  background: #fff;
  padding: 24px;
  border: 1px solid #ddd;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}

.card-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 2px solid #333;
}

.card-title {
  margin: 0 0 8px;
  font-size: 1.25rem;
  color: #333;
}

.card-project-name {
  width: 100%;
  max-width: 500px;
  padding: 8px 12px;
  font-size: 1rem;
  border: 1px solid #ccc;
  border-radius: 6px;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.card-section {
  background: #f9f9f9;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 14px;
}

.card-section h2 {
  margin: 0 0 6px;
  font-size: 1rem;
  color: #333;
}

.section-hint {
  margin: 0 0 10px;
  font-size: 0.8rem;
  color: #666;
  line-height: 1.3;
}

.section-tasks { grid-column: 1; }
.section-priorities { grid-column: 2; }
.section-deps { grid-column: 1; }
.section-bottleneck { grid-column: 2; }
.section-roles { grid-column: 1; }
.section-decisions { grid-column: 2; }

.tasks-table, .roles-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.tasks-table th, .tasks-table td,
.roles-table th, .roles-table td {
  border: 1px solid #ddd;
  padding: 6px 8px;
  text-align: left;
}

.tasks-table th, .roles-table th {
  background: #eee;
  font-weight: 600;
}

.tasks-table input, .roles-table input,
.tasks-table select, .roles-table select {
  width: 100%;
  padding: 4px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.85rem;
}

.input-sm { max-width: 80px; }
.input-num { max-width: 56px; }

.add-row-btn, .add-item-btn {
  margin-top: 8px;
  padding: 6px 12px;
  background: #e0e0e0;
  border: none;
  border-radius: 6px;
  font-size: 0.85rem;
  cursor: pointer;
}

.add-row-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.priority-block {
  margin-bottom: 12px;
}

.priority-block h3 {
  margin: 0 0 6px;
  font-size: 0.9rem;
  color: #555;
}

.priority-block ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.priority-block li {
  margin-bottom: 4px;
}

.priority-block input {
  width: 100%;
  padding: 4px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.85rem;
}

.add-item-btn {
  padding: 2px 10px;
  font-size: 0.9rem;
}

.section-deps textarea,
.section-bottleneck textarea,
.bottleneck-title {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.bottleneck-title {
  margin-bottom: 8px;
}

.section-bottleneck {
  border-left: 4px solid #c62828;
}

.decision-item {
  margin-bottom: 12px;
  padding: 8px;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.decision-q {
  width: 100%;
  padding: 6px 8px;
  margin-bottom: 6px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-weight: 600;
  box-sizing: border-box;
}

.decision-ctx {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.85rem;
  resize: vertical;
  box-sizing: border-box;
}

@media (max-width: 768px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
  .section-tasks, .section-priorities, .section-deps,
  .section-bottleneck, .section-roles, .section-decisions {
    grid-column: 1;
  }
}
</style>
