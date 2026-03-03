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
        <!-- ① Активные задачи + светофор -->
        <section class="card-section section-tasks">
          <h2><span class="section-num">①</span> Активные задачи</h2>
          <p class="section-hint">Не более 10 задач. Статус — клик по светофору.</p>
          <div class="tasks-table-wrap">
            <table class="tasks-table">
              <thead>
                <tr>
                  <th class="col-num">№</th>
                  <th class="col-task">Задача</th>
                  <th class="col-status">Статус</th>
                  <th class="col-deadline">Срок</th>
                  <th class="col-who">Кто</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(task, i) in form.tasks" :key="i">
                  <td class="col-num">{{ i + 1 }}</td>
                  <td class="col-task"><input v-model="task.name" placeholder="Задача" /></td>
                  <td class="col-status">
                    <div class="traffic-light" :title="statusLabel(task.status)">
                      <button type="button" class="tl-dot tl-green" :class="{ active: task.status === 'done' }" title="Готово" @click="task.status = 'done'" />
                      <button type="button" class="tl-dot tl-yellow" :class="{ active: task.status === 'progress' }" title="В работе" @click="task.status = 'progress'" />
                      <button type="button" class="tl-dot tl-red" :class="{ active: task.status === 'risk' }" title="Риск" @click="task.status = 'risk'" />
                      <button type="button" class="tl-dot tl-gray" :class="{ active: task.status === 'waiting' }" title="Ожидание" @click="task.status = 'waiting'" />
                    </div>
                    <span class="status-label">{{ statusLabel(task.status) }}</span>
                  </td>
                  <td class="col-deadline"><input v-model="task.deadline" placeholder="10.04" /></td>
                  <td class="col-who"><input v-model="task.who" placeholder="Ответственный" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="add-row-btn" @click="addTask" :disabled="form.tasks.length >= 10">+ Добавить задачу</button>
        </section>

        <!-- ② Приоритеты -->
        <section class="card-section section-priorities">
          <h2><span class="section-num">②</span> Приоритеты</h2>
          <p class="section-hint">MUST — критично, SHOULD — важно, NICE — желательно.</p>
          <div class="priority-block must">
            <h3>MUST</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesMust" :key="'m'+i">
                <input v-model="form.prioritiesMust[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesMust.push('')">+</button>
          </div>
          <div class="priority-block should">
            <h3>SHOULD</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesShould" :key="'s'+i">
                <input v-model="form.prioritiesShould[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesShould.push('')">+</button>
          </div>
          <div class="priority-block nice">
            <h3>NICE</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesNice" :key="'n'+i">
                <input v-model="form.prioritiesNice[i]" placeholder="Задача" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesNice.push('')">+</button>
          </div>
        </section>

        <!-- ③ Зависимости — рисуемая схема как в draw.io -->
        <section class="card-section section-deps">
          <h2><span class="section-num">③</span> Зависимости</h2>
          <p class="section-hint">Добавьте этапы, перетащите блоки на холсте. Связи: выберите «От» и «К» или кликните два этапа подряд для создания стрелки.</p>
          <div class="deps-toolbar">
            <button type="button" class="add-row-btn" @click="addDependencyNode">+ Добавить этап</button>
            <span class="deps-mode-hint" v-if="linkFromId">Кликните этап-цель для связи</span>
          </div>
          <div ref="depsDiagram" class="deps-diagram-canvas" @click.self="linkFromId = null">
            <svg class="deps-arrows-layer" :viewBox="depsSvgViewBox" preserveAspectRatio="none">
              <defs>
                <marker id="dep-arrowhead" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">
                  <polygon points="0 0, 10 4, 0 8" fill="#475569" />
                </marker>
              </defs>
              <path v-for="(path, i) in depsArrowPaths" :key="'p'+i" :d="path.d" stroke="#475569" stroke-width="2" fill="none" marker-end="url(#dep-arrowhead)" />
            </svg>
            <div
              v-for="(node, i) in form.dependencyNodes"
              :key="node.id"
              class="dep-node-box"
              :class="{ selected: linkFromId === node.id }"
              :style="nodeStyle(node)"
              @mousedown.prevent="onNodeMouseDown($event, node)"
              @dblclick.stop="editNodeLabel = node.id"
            >
              <span v-if="editNodeLabel !== node.id" class="dep-node-text">{{ node.label || 'Этап ' + (i + 1) }}</span>
              <input
                v-else
                ref="nodeLabelInput"
                v-model="node.label"
                class="dep-node-input"
                :placeholder="'Этап ' + (i + 1)"
                @blur="editNodeLabel = null"
                @keydown.enter="editNodeLabel = null"
              />
              <button type="button" class="dep-node-delete" @click.stop="removeNode(node.id)" title="Удалить">×</button>
            </div>
          </div>
          <div class="deps-links-editor">
            <label>Связи (или клик по двум этапам на схеме):</label>
            <div v-for="(link, idx) in form.dependencyLinks" :key="idx" class="link-row">
              <select v-model.number="link.fromId" class="link-select">
                <option v-for="n in form.dependencyNodes" :key="n.id" :value="n.id">{{ n.label || 'Этап ' + (nodeIndex(n.id) + 1) }}</option>
              </select>
              <span class="link-arrow">→</span>
              <select v-model.number="link.toId" class="link-select">
                <option v-for="n in form.dependencyNodes" :key="n.id" :value="n.id">{{ n.label || 'Этап ' + (nodeIndex(n.id) + 1) }}</option>
              </select>
              <button type="button" class="chip-remove" @click="form.dependencyLinks.splice(idx, 1)">×</button>
            </div>
            <button type="button" class="add-row-btn" @click="addDependencyLink" :disabled="form.dependencyNodes.length < 2">+ Добавить связь</button>
          </div>
        </section>

        <!-- ④ Узкие места (несколько) -->
        <section class="card-section section-bottleneck">
          <h2><span class="section-num">④</span> Узкие места</h2>
          <p class="section-hint">Элементы, ограничивающие общий ход. Можно указать несколько.</p>
          <div v-for="(b, i) in form.bottlenecks" :key="i" class="bottleneck-item">
            <input v-model="b.title" class="bottleneck-title" placeholder="Название (например: Подрядчик по ремонту)" />
            <textarea v-model="b.desc" rows="2" placeholder="Почему узкое место: причины, влияние"></textarea>
            <button type="button" class="chip-remove bottleneck-remove" @click="form.bottlenecks.splice(i, 1)" title="Удалить">×</button>
          </div>
          <button type="button" class="add-row-btn" @click="form.bottlenecks.push({ title: '', desc: '' })">+ Добавить узкое место</button>
        </section>

        <!-- ⑤ Загрузка ключевых ролей -->
        <section class="card-section section-roles">
          <h2><span class="section-num">⑤</span> Загрузка ключевых ролей</h2>
          <p class="section-hint">Риск перегруза: клик по индикатору.</p>
          <table class="roles-table">
            <thead>
              <tr>
                <th>Роль</th>
                <th>Задач</th>
                <th>Риск</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(role, i) in form.roles" :key="i">
                <td><input v-model="role.name" placeholder="Роль" /></td>
                <td><input v-model.number="role.tasksCount" type="number" min="0" class="input-num" /></td>
                <td class="col-risk">
                  <div class="risk-dots">
                    <button type="button" class="risk-dot" :class="{ active: role.overloadRisk === 'normal' }" title="Норма" @click="role.overloadRisk = 'normal'" />
                    <button type="button" class="risk-dot medium" :class="{ active: role.overloadRisk === 'medium' }" title="Средний" @click="role.overloadRisk = 'medium'" />
                    <button type="button" class="risk-dot high" :class="{ active: role.overloadRisk === 'high' }" title="Высокий" @click="role.overloadRisk = 'high'" />
                    <button type="button" class="risk-dot critical" :class="{ active: role.overloadRisk === 'critical' }" title="Критический" @click="role.overloadRisk = 'critical'" />
                  </div>
                  <span class="risk-label">{{ riskLabel(role.overloadRisk) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="add-row-btn" @click="addRole">+ Добавить роль</button>
        </section>

        <!-- ⑥ Решения -->
        <section class="card-section section-decisions">
          <h2><span class="section-num">⑥</span> Управленческие решения</h2>
          <p class="section-hint">Вопросы, требующие решения здесь и сейчас.</p>
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

let nextId = 1;
const NODE_W = 110;
const NODE_H = 40;
const DIAGRAM_W = 600;
const DIAGRAM_H = 280;

const defaultForm = () => {
  const nodes = [
    { id: nextId++, label: 'Планирование', x: 20, y: 30 },
    { id: nextId++, label: 'Работы', x: 150, y: 30 },
    { id: nextId++, label: 'Запуск', x: 280, y: 30 },
  ];
  return {
    projectName: '',
    tasks: [
      { name: '', status: 'progress', deadline: '', who: '' },
      { name: '', status: 'progress', deadline: '', who: '' },
    ],
    prioritiesMust: ['', ''],
    prioritiesShould: [''],
    prioritiesNice: [''],
    dependencyNodes: nodes,
    dependencyLinks: [
      { fromId: nodes[0].id, toId: nodes[1].id },
      { fromId: nodes[1].id, toId: nodes[2].id },
    ],
    bottlenecks: [
      { title: '', desc: '' },
    ],
    roles: [
      { name: '', tasksCount: 0, overloadRisk: 'normal' },
      { name: '', tasksCount: 0, overloadRisk: 'normal' },
    ],
    decisions: [
      { question: '', context: '' },
    ],
  };
};

export default {
  name: 'ProjectManagementCard',
  data() {
    return {
      form: defaultForm(),
      exporting: false,
      linkFromId: null,
      editNodeLabel: null,
      dragNode: null,
      dragStartX: 0,
      dragStartY: 0,
      dragStartNodeX: 0,
      dragStartNodeY: 0,
      dragMoved: false,
    };
  },
  computed: {
    firstNodeId() {
      const n = this.form.dependencyNodes[0];
      return n ? n.id : 0;
    },
    depsSvgViewBox() {
      return `0 0 ${DIAGRAM_W} ${DIAGRAM_H}`;
    },
    depsArrowPaths() {
      const nodes = this.form.dependencyNodes;
      const paths = [];
      this.form.dependencyLinks.forEach(link => {
        const from = nodes.find(n => n.id === link.fromId);
        const to = nodes.find(n => n.id === link.toId);
        if (!from || !to || from.id === to.id) return;
        const x1 = (from.x ?? 0) + NODE_W;
        const y1 = (from.y ?? 0) + NODE_H / 2;
        const x2 = to.x ?? 0;
        const y2 = (to.y ?? 0) + NODE_H / 2;
        const mid = (x1 + x2) / 2;
        const d = `M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`;
        paths.push({ d });
      });
      return paths;
    },
  },
  methods: {
    nodeStyle(node) {
      return {
        left: (node.x ?? 0) + 'px',
        top: (node.y ?? 0) + 'px',
        width: NODE_W + 'px',
        minHeight: NODE_H + 'px',
      };
    },
    nodeIndex(id) {
      return this.form.dependencyNodes.findIndex(n => n.id === id);
    },
    nodeLabel(id) {
      const n = this.form.dependencyNodes.find(x => x.id === id);
      const i = this.nodeIndex(id);
      return (n && n.label) ? n.label : ('Этап ' + (i + 1));
    },
    onNodeMouseDown(ev, node) {
      if (this.editNodeLabel === node.id) return;
      this.dragMoved = false;
      if (this.linkFromId !== null) {
        if (this.linkFromId === node.id) {
          this.linkFromId = null;
          return;
        }
        const from = this.form.dependencyNodes.find(n => n.id === this.linkFromId);
        if (from) {
          const exists = this.form.dependencyLinks.some(l => l.fromId === this.linkFromId && l.toId === node.id);
          if (!exists) this.form.dependencyLinks.push({ fromId: this.linkFromId, toId: node.id });
        }
        this.linkFromId = null;
        return;
      }
      this.dragNode = node;
      this.dragStartX = ev.clientX;
      this.dragStartY = ev.clientY;
      this.dragStartNodeX = node.x ?? 0;
      this.dragStartNodeY = node.y ?? 0;
      document.addEventListener('mousemove', this.onDiagramMouseMove);
      document.addEventListener('mouseup', this.onDiagramMouseUp);
    },
    onDiagramMouseMove(ev) {
      if (!this.dragNode) return;
      const dx = ev.clientX - this.dragStartX;
      const dy = ev.clientY - this.dragStartY;
      if (Math.abs(dx) > 4 || Math.abs(dy) > 4) this.dragMoved = true;
      this.dragNode.x = Math.max(0, Math.min(DIAGRAM_W - NODE_W, this.dragStartNodeX + dx));
      this.dragNode.y = Math.max(0, Math.min(DIAGRAM_H - NODE_H, this.dragStartNodeY + dy));
    },
    onDiagramMouseUp() {
      if (!this.dragMoved && this.dragNode && this.linkFromId === null) {
        this.linkFromId = this.dragNode.id;
      }
      this.dragNode = null;
      document.removeEventListener('mousemove', this.onDiagramMouseMove);
      document.removeEventListener('mouseup', this.onDiagramMouseUp);
    },
    statusLabel(s) {
      const l = { done: 'Готово', progress: 'В работе', risk: 'Риск', waiting: 'Ожидание' };
      return l[s] || s;
    },
    riskLabel(r) {
      const l = { normal: 'Норма', medium: 'Средний', high: 'Высокий', critical: 'Критический' };
      return l[r] || r;
    },
    addTask() {
      if (this.form.tasks.length < 10) this.form.tasks.push({ name: '', status: 'progress', deadline: '', who: '' });
    },
    addRole() {
      this.form.roles.push({ name: '', tasksCount: 0, overloadRisk: 'normal' });
    },
    addDependencyNode() {
      const nodes = this.form.dependencyNodes;
      const last = nodes[nodes.length - 1];
      const x = last ? (last.x + NODE_W + 30) : 20;
      const y = last ? last.y : 30;
      this.form.dependencyNodes.push({ id: nextId++, label: '', x, y });
    },
    removeNode(id) {
      this.form.dependencyNodes = this.form.dependencyNodes.filter(n => n.id !== id);
      this.form.dependencyLinks = this.form.dependencyLinks.filter(l => l.fromId !== id && l.toId !== id);
    },
    addDependencyLink() {
      const nodes = this.form.dependencyNodes;
      const a = nodes[0]?.id;
      const b = nodes[1]?.id ?? a;
      this.form.dependencyLinks.push({ fromId: a, toId: b });
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
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}

.page-actions {
  margin-bottom: 20px;
}

.export-pdf-btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.export-pdf-btn:hover:not(:disabled) {
  filter: brightness(1.05);
}

.export-pdf-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.project-card-a3 {
  background: linear-gradient(180deg, #fafbfc 0%, #fff 80px);
  padding: 28px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.06);
}

.card-header {
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 3px solid #1e293b;
}

.card-title {
  margin: 0 0 12px;
  font-size: 1.35rem;
  font-weight: 700;
  color: #0f172a;
}

.card-project-name {
  width: 100%;
  max-width: 520px;
  padding: 10px 14px;
  font-size: 1rem;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  background: #fff;
}

.card-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  min-width: 0;
}

.card-section {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  min-width: 0;
}

.card-section h2 {
  margin: 0 0 8px;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
  display: flex;
  align-items: center;
  gap: 6px;
}

.section-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  background: #1e293b;
  color: #fff;
  border-radius: 50%;
  font-size: 0.85rem;
}

.section-hint {
  margin: 0 0 14px;
  font-size: 0.8rem;
  color: #64748b;
  line-height: 1.4;
}

.section-tasks { grid-column: 1; }
.section-priorities { grid-column: 2; }
.section-deps { grid-column: 1 / -1; }
.section-bottleneck { grid-column: 1 / -1; }
.section-roles { grid-column: 1; }
.section-decisions { grid-column: 2; }

/* Таблица задач + светофор */
.tasks-table, .roles-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.tasks-table th, .tasks-table td,
.roles-table th, .roles-table td {
  border: 1px solid #e2e8f0;
  padding: 8px 10px;
  text-align: left;
}

.tasks-table th, .roles-table th {
  background: #f1f5f9;
  font-weight: 600;
  color: #475569;
}

.tasks-table input, .roles-table input,
.tasks-table select, .roles-table select {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
}

.tasks-table-wrap {
  overflow-x: auto;
  margin: 0 -4px;
}

.col-num { width: 40px; min-width: 40px; text-align: center; }
.col-task { min-width: 260px; }
.col-status { width: 1%; white-space: nowrap; min-width: 140px; }
.col-deadline { min-width: 100px; }
.col-who { min-width: 160px; }
.col-risk { white-space: nowrap; }

.tasks-table .col-task input,
.tasks-table .col-who input,
.tasks-table .col-deadline input {
  min-width: 0;
  width: 100%;
  box-sizing: border-box;
}

.traffic-light {
  display: inline-flex;
  gap: 4px;
  align-items: center;
  vertical-align: middle;
}

.tl-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
  cursor: pointer;
  padding: 0;
  transition: transform 0.15s, box-shadow 0.15s;
}

.tl-dot:hover {
  transform: scale(1.1);
}

.tl-green { background: #94a3b8; }
.tl-green.active { background: #22c55e; border-color: #16a34a; box-shadow: 0 0 0 2px #22c55e; }
.tl-yellow { background: #94a3b8; }
.tl-yellow.active { background: #eab308; border-color: #ca8a04; box-shadow: 0 0 0 2px #eab308; }
.tl-red { background: #94a3b8; }
.tl-red.active { background: #ef4444; border-color: #dc2626; box-shadow: 0 0 0 2px #ef4444; }
.tl-gray { background: #94a3b8; }
.tl-gray.active { background: #64748b; border-color: #475569; box-shadow: 0 0 0 2px #64748b; }

.status-label {
  margin-left: 8px;
  font-size: 0.8rem;
  color: #64748b;
}

.input-num { max-width: 56px; }

/* Приоритеты */
.priority-block {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 4px solid #cbd5e1;
}

.priority-block.must { border-left-color: #dc2626; background: #fef2f2; }
.priority-block.should { border-left-color: #eab308; background: #fefce8; }
.priority-block.nice { border-left-color: #22c55e; background: #f0fdf4; }

.priority-block h3 {
  margin: 0 0 8px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #334155;
}

.priority-block ul { list-style: none; padding: 0; margin: 0; }
.priority-block li { margin-bottom: 6px; }

.priority-block input {
  width: 100%;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  box-sizing: border-box;
}

.add-row-btn, .add-item-btn {
  margin-top: 10px;
  padding: 8px 14px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.85rem;
  cursor: pointer;
  color: #475569;
  font-weight: 500;
}

.add-row-btn:hover:not(:disabled), .add-item-btn:hover {
  background: #e2e8f0;
}

.add-row-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.add-item-btn { padding: 4px 12px; font-size: 0.9rem; }

/* Зависимости — рисуемый холст */
.deps-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.deps-mode-hint {
  font-size: 0.85rem;
  color: #64748b;
  font-style: italic;
}

.deps-diagram-canvas {
  position: relative;
  width: 600px;
  max-width: 100%;
  height: 280px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 8px;
  margin-bottom: 14px;
  overflow: hidden;
}

.deps-arrows-layer {
  position: absolute;
  left: 0;
  top: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.dep-node-box {
  position: absolute;
  padding: 8px 28px 8px 10px;
  background: #fff;
  border: 2px solid #334155;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e293b;
  cursor: move;
  box-shadow: 0 2px 6px rgba(0,0,0,0.08);
  display: flex;
  align-items: center;
  box-sizing: border-box;
}

.dep-node-box.selected {
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.3);
}

.dep-node-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dep-node-input {
  flex: 1;
  min-width: 0;
  padding: 2px 4px;
  border: 1px solid #94a3b8;
  border-radius: 4px;
  font-size: 0.85rem;
}

.dep-node-delete {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  padding: 0;
  border: none;
  background: #e2e8f0;
  color: #475569;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
}

.dep-node-delete:hover {
  background: #f87171;
  color: #fff;
}

.deps-links-editor {
  margin-top: 8px;
}

.deps-links-editor label {
  display: block;
  font-size: 0.8rem;
  font-weight: 600;
  color: #475569;
  margin-bottom: 6px;
}

.chip-remove {
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  background: #e2e8f0;
  color: #475569;
  border-radius: 50%;
  cursor: pointer;
  font-size: 1.1rem;
  line-height: 1;
}

.chip-remove:hover {
  background: #f87171;
  color: #fff;
}

.link-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.link-select {
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  min-width: 100px;
}

.link-arrow {
  color: #64748b;
  font-weight: 700;
}

/* Узкие места (несколько) */
.section-bottleneck {
  border-left: 4px solid #dc2626;
  background: #fef2f2;
}

.bottleneck-item {
  position: relative;
  margin-bottom: 14px;
  padding: 12px;
  background: #fff;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.bottleneck-title {
  width: 100%;
  padding: 8px 10px;
  margin-bottom: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  box-sizing: border-box;
}

.bottleneck-item textarea {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  resize: vertical;
  box-sizing: border-box;
}

.bottleneck-remove {
  position: absolute;
  top: 8px;
  right: 8px;
}

/* Роли — индикаторы риска */
.risk-dots {
  display: inline-flex;
  gap: 4px;
  align-items: center;
}

.risk-dot {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 2px solid #e2e8f0;
  padding: 0;
  cursor: pointer;
  background: #94a3b8;
  transition: transform 0.15s;
}

.risk-dot:hover { transform: scale(1.15); }
.risk-dot.active { box-shadow: 0 0 0 2px currentColor; }
.risk-dot.active { background: #22c55e; border-color: #16a34a; }
.risk-dot.medium.active { background: #eab308; border-color: #ca8a04; }
.risk-dot.high.active { background: #f97316; border-color: #ea580c; }
.risk-dot.critical.active { background: #ef4444; border-color: #dc2626; }

.risk-label {
  margin-left: 8px;
  font-size: 0.8rem;
  color: #64748b;
}

/* Решения */
.decision-item {
  margin-bottom: 14px;
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.decision-q {
  width: 100%;
  padding: 8px 10px;
  margin-bottom: 8px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.9rem;
  box-sizing: border-box;
}

.decision-ctx {
  width: 100%;
  padding: 8px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  resize: vertical;
  box-sizing: border-box;
}

@media (max-width: 1024px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
  .section-tasks, .section-priorities, .section-deps,
  .section-bottleneck, .section-roles, .section-decisions {
    grid-column: 1;
  }
  .deps-diagram-canvas { max-width: 100%; }
}

@media (max-width: 768px) {
  .project-card-page { padding: 16px; }
  .col-task { min-width: 180px; }
  .col-who { min-width: 120px; }
}
</style>
