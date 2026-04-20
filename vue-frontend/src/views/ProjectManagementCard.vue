<template>
  <div class="project-card-page">
    <div class="page-actions">
      <button type="button" class="pcard-load-example" @click="loadFullExample">
        {{ $t('projectCard.loadExample') }}
      </button>
      <button type="button" class="export-pdf-btn" @click="exportPdf" :disabled="exporting">
        {{ exporting ? $t('projectCard.downloadingPdf') : '📄 ' + $t('projectCard.downloadPdf') }}
      </button>
    </div>
    <p v-if="aiError" class="pcard-ai-error" role="alert">{{ aiError }}</p>

    <div ref="pdfContent" class="project-card-a3">
      <header class="card-header">
        <h1 class="card-title">{{ $t('projectCard.title') }}</h1>
        <input v-model="form.projectName" class="card-project-name" :placeholder="$t('projectCard.projectNamePh')" />
      </header>

      <div class="card-grid">
        <!-- ① -->
        <section class="card-section section-tasks">
          <div class="pcard-section-head">
            <h2><span class="section-num">①</span> {{ $t('projectCard.section1') }}</h2>
            <button
              type="button"
              class="pcard-ai-btn"
              :disabled="!!aiLoading"
              @click="runAi('tasks')"
            >
              {{ aiLoading === 'tasks' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section1Hint') }}</p>
          <div class="tasks-table-wrap">
            <table class="tasks-table">
              <thead>
                <tr>
                  <th class="col-num">{{ $t('projectCard.colNum') }}</th>
                  <th class="col-task">{{ $t('projectCard.colTask') }}</th>
                  <th class="col-status">{{ $t('projectCard.colStatus') }}</th>
                  <th class="col-deadline">{{ $t('projectCard.colDeadline') }}</th>
                  <th class="col-who">{{ $t('projectCard.colWho') }}</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(task, i) in form.tasks" :key="i">
                  <td class="col-num">{{ i + 1 }}</td>
                  <td class="col-task"><input v-model="task.name" :placeholder="$t('projectCard.taskPh')" /></td>
                  <td class="col-status">
                    <div class="traffic-light" :title="statusLabel(task.status)">
                      <button
                        type="button"
                        class="pcard-tl tl-green"
                        :class="{ 'pcard-tl--on': task.status === 'done' }"
                        :title="$t('projectCard.tlDone')"
                        @click="task.status = 'done'"
                      />
                      <button
                        type="button"
                        class="pcard-tl tl-yellow"
                        :class="{ 'pcard-tl--on': task.status === 'progress' }"
                        :title="$t('projectCard.tlProgress')"
                        @click="task.status = 'progress'"
                      />
                      <button
                        type="button"
                        class="pcard-tl tl-red"
                        :class="{ 'pcard-tl--on': task.status === 'risk' }"
                        :title="$t('projectCard.tlRisk')"
                        @click="task.status = 'risk'"
                      />
                      <button
                        type="button"
                        class="pcard-tl tl-gray"
                        :class="{ 'pcard-tl--on': task.status === 'waiting' }"
                        :title="$t('projectCard.tlWaiting')"
                        @click="task.status = 'waiting'"
                      />
                    </div>
                    <span class="status-label">{{ statusLabel(task.status) }}</span>
                  </td>
                  <td class="col-deadline"><input v-model="task.deadline" :placeholder="$t('projectCard.dateExample')" /></td>
                  <td class="col-who"><input v-model="task.who" :placeholder="$t('projectCard.ownerPh')" /></td>
                </tr>
              </tbody>
            </table>
          </div>
          <button type="button" class="add-row-btn" @click="addTask" :disabled="form.tasks.length >= 10">{{ $t('projectCard.addTask') }}</button>
        </section>

        <!-- ② -->
        <section class="card-section section-priorities">
          <div class="pcard-section-head">
            <h2><span class="section-num">②</span> {{ $t('projectCard.section2') }}</h2>
            <button type="button" class="pcard-ai-btn" :disabled="!!aiLoading" @click="runAi('priorities')">
              {{ aiLoading === 'priorities' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section2Hint') }}</p>
          <div class="priority-block must">
            <h3>MUST</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesMust" :key="'m'+i">
                <input v-model="form.prioritiesMust[i]" :placeholder="$t('projectCard.taskPh')" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesMust.push('')">+</button>
          </div>
          <div class="priority-block should">
            <h3>SHOULD</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesShould" :key="'s'+i">
                <input v-model="form.prioritiesShould[i]" :placeholder="$t('projectCard.taskPh')" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesShould.push('')">+</button>
          </div>
          <div class="priority-block nice">
            <h3>NICE</h3>
            <ul>
              <li v-for="(item, i) in form.prioritiesNice" :key="'n'+i">
                <input v-model="form.prioritiesNice[i]" :placeholder="$t('projectCard.taskPh')" />
              </li>
            </ul>
            <button type="button" class="add-item-btn" @click="form.prioritiesNice.push('')">+</button>
          </div>
        </section>

        <!-- ③ текстовые зависимости -->
        <section class="card-section section-deps">
          <div class="pcard-section-head">
            <h2><span class="section-num">③</span> {{ $t('projectCard.section3') }}</h2>
            <button type="button" class="pcard-ai-btn" :disabled="!!aiLoading" @click="runAi('dependencies')">
              {{ aiLoading === 'dependencies' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section3Hint') }}</p>
          <textarea
            v-model="form.dependenciesText"
            class="deps-textarea"
            rows="6"
            :placeholder="$t('projectCard.dependenciesPlaceholder')"
          />
        </section>

        <!-- ④ -->
        <section class="card-section section-bottleneck">
          <div class="pcard-section-head">
            <h2><span class="section-num">④</span> {{ $t('projectCard.section4') }}</h2>
            <button type="button" class="pcard-ai-btn" :disabled="!!aiLoading" @click="runAi('bottlenecks')">
              {{ aiLoading === 'bottlenecks' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section4Hint') }}</p>
          <div v-for="(b, i) in form.bottlenecks" :key="i" class="bottleneck-item">
            <input v-model="b.title" class="bottleneck-title" :placeholder="$t('projectCard.bottleneckTitlePh')" />
            <textarea v-model="b.desc" rows="2" :placeholder="$t('projectCard.bottleneckDescPh')" />
            <button type="button" class="chip-remove bottleneck-remove" @click="form.bottlenecks.splice(i, 1)" :title="$t('projectCard.deleteTitle')">×</button>
          </div>
          <button type="button" class="add-row-btn" @click="form.bottlenecks.push({ title: '', desc: '' })">{{ $t('projectCard.addBottleneck') }}</button>
        </section>

        <!-- ⑤ -->
        <section class="card-section section-roles">
          <div class="pcard-section-head">
            <h2><span class="section-num">⑤</span> {{ $t('projectCard.section5') }}</h2>
            <button type="button" class="pcard-ai-btn" :disabled="!!aiLoading" @click="runAi('roles')">
              {{ aiLoading === 'roles' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section5Hint') }}</p>
          <table class="roles-table">
            <thead>
              <tr>
                <th>{{ $t('projectCard.colRole') }}</th>
                <th>{{ $t('projectCard.colTasksCount') }}</th>
                <th>{{ $t('projectCard.colRiskHeader') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(role, i) in form.roles" :key="i">
                <td><input v-model="role.name" :placeholder="$t('projectCard.rolePh')" /></td>
                <td><input v-model.number="role.tasksCount" type="number" min="0" class="input-num" /></td>
                <td class="col-risk">
                  <div class="risk-dots">
                    <button
                      type="button"
                      class="pcard-risk pcard-risk--normal"
                      :class="{ 'pcard-risk--on': role.overloadRisk === 'normal' }"
                      :title="$t('projectCard.riskNormal')"
                      @click="role.overloadRisk = 'normal'"
                    />
                    <button
                      type="button"
                      class="pcard-risk pcard-risk--medium"
                      :class="{ 'pcard-risk--on': role.overloadRisk === 'medium' }"
                      :title="$t('projectCard.riskMedium')"
                      @click="role.overloadRisk = 'medium'"
                    />
                    <button
                      type="button"
                      class="pcard-risk pcard-risk--high"
                      :class="{ 'pcard-risk--on': role.overloadRisk === 'high' }"
                      :title="$t('projectCard.riskHigh')"
                      @click="role.overloadRisk = 'high'"
                    />
                    <button
                      type="button"
                      class="pcard-risk pcard-risk--critical"
                      :class="{ 'pcard-risk--on': role.overloadRisk === 'critical' }"
                      :title="$t('projectCard.riskCritical')"
                      @click="role.overloadRisk = 'critical'"
                    />
                  </div>
                  <span class="risk-label">{{ riskLabel(role.overloadRisk) }}</span>
                </td>
              </tr>
            </tbody>
          </table>
          <button type="button" class="add-row-btn" @click="addRole">{{ $t('projectCard.addRole') }}</button>
        </section>

        <!-- ⑥ -->
        <section class="card-section section-decisions">
          <div class="pcard-section-head">
            <h2><span class="section-num">⑥</span> {{ $t('projectCard.section6') }}</h2>
            <button type="button" class="pcard-ai-btn" :disabled="!!aiLoading" @click="runAi('decisions')">
              {{ aiLoading === 'decisions' ? $t('projectCard.aiThinking') : $t('projectCard.aiHelp') }}
            </button>
          </div>
          <p class="section-hint">{{ $t('projectCard.section6Hint') }}</p>
          <div v-for="(item, i) in form.decisions" :key="i" class="decision-item">
            <input v-model="form.decisions[i].question" :placeholder="$t('projectCard.decisionQPh')" class="decision-q" />
            <textarea v-model="form.decisions[i].context" rows="2" :placeholder="$t('projectCard.decisionCtxPh')" class="decision-ctx" />
          </div>
          <button type="button" class="add-row-btn" @click="form.decisions.push({ question: '', context: '' })">{{ $t('projectCard.addDecision') }}</button>
        </section>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import { getProjectCardExampleEn, getProjectCardExampleRu } from '@/data/projectCardExamples.js';

const defaultForm = () => ({
  projectName: '',
  tasks: [
    { name: '', status: 'progress', deadline: '', who: '' },
    { name: '', status: 'progress', deadline: '', who: '' },
  ],
  prioritiesMust: ['', ''],
  prioritiesShould: [''],
  prioritiesNice: [''],
  dependenciesText: '',
  bottlenecks: [{ title: '', desc: '' }],
  roles: [
    { name: '', tasksCount: 0, overloadRisk: 'normal' },
    { name: '', tasksCount: 0, overloadRisk: 'normal' },
  ],
  decisions: [{ question: '', context: '' }],
});

export default {
  name: 'ProjectManagementCard',
  data() {
    return {
      form: defaultForm(),
      exporting: false,
      aiLoading: null,
      aiError: '',
    };
  },
  methods: {
    localeCode() {
      const g = this.$i18n?.locale;
      const s = typeof g === 'string' ? g : g?.value || 'ru';
      return String(s).toLowerCase().startsWith('en') ? 'en' : 'ru';
    },
    snapshotForm() {
      return JSON.parse(JSON.stringify(this.form));
    },
    async runAi(section) {
      this.aiError = '';
      this.aiLoading = section;
      try {
        const token = localStorage.getItem('token');
        const { data } = await axios.post(
          '/api/project-card/ai-suggest',
          {
            section,
            locale: this.localeCode(),
            projectName: this.form.projectName,
            form: this.snapshotForm(),
          },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        if (!data.success || !data.data) {
          this.aiError = this.$t('projectCard.aiFailed');
          return;
        }
        this.applyAiPayload(section, data.data);
      } catch (e) {
        console.error(e);
        const msg = e.response?.data?.error;
        this.aiError = msg === 'OpenAI API is not configured' ? this.$t('projectCard.aiFailed') : this.$t('projectCard.aiFailed');
      } finally {
        this.aiLoading = null;
      }
    },
    applyAiPayload(section, payload) {
      if (section === 'tasks' && Array.isArray(payload.tasks)) {
        const rows = payload.tasks
          .filter((t) => t && String(t.name || '').trim())
          .slice(0, 10)
          .map((t) => ({
            name: String(t.name || '').slice(0, 500),
            status: ['done', 'progress', 'risk', 'waiting'].includes(t.status) ? t.status : 'progress',
            deadline: String(t.deadline || '').slice(0, 80),
            who: String(t.who || '').slice(0, 120),
          }));
        if (rows.length) this.form.tasks = rows;
      } else if (section === 'priorities') {
        const must = Array.isArray(payload.must) ? payload.must.map((x) => String(x || '').slice(0, 400)).filter(Boolean) : [];
        const should = Array.isArray(payload.should) ? payload.should.map((x) => String(x || '').slice(0, 400)).filter(Boolean) : [];
        const nice = Array.isArray(payload.nice) ? payload.nice.map((x) => String(x || '').slice(0, 400)).filter(Boolean) : [];
        if (must.length) this.form.prioritiesMust = must;
        if (should.length) this.form.prioritiesShould = should;
        if (nice.length) this.form.prioritiesNice = nice;
      } else if (section === 'dependencies' && typeof payload.text === 'string') {
        this.form.dependenciesText = payload.text.slice(0, 8000);
      } else if (section === 'bottlenecks' && Array.isArray(payload.items)) {
        const items = payload.items
          .filter((b) => b && (String(b.title || '').trim() || String(b.desc || '').trim()))
          .map((b) => ({
            title: String(b.title || '').slice(0, 300),
            desc: String(b.desc || '').slice(0, 2000),
          }));
        if (items.length) this.form.bottlenecks = items;
      } else if (section === 'roles' && Array.isArray(payload.roles)) {
        const roles = payload.roles
          .filter((r) => r && String(r.name || '').trim())
          .map((r) => ({
            name: String(r.name || '').slice(0, 200),
            tasksCount: Math.max(0, Math.min(999, parseInt(String(r.tasksCount ?? 0), 10) || 0)),
            overloadRisk: ['normal', 'medium', 'high', 'critical'].includes(r.overloadRisk) ? r.overloadRisk : 'normal',
          }));
        if (roles.length) this.form.roles = roles;
      } else if (section === 'decisions' && Array.isArray(payload.decisions)) {
        const dec = payload.decisions
          .filter((d) => d && (String(d.question || '').trim() || String(d.context || '').trim()))
          .map((d) => ({
            question: String(d.question || '').slice(0, 400),
            context: String(d.context || '').slice(0, 4000),
          }));
        if (dec.length) this.form.decisions = dec;
      }
    },
    loadFullExample() {
      const ex = this.localeCode() === 'en' ? getProjectCardExampleEn() : getProjectCardExampleRu();
      this.form = {
        projectName: ex.projectName,
        tasks: ex.tasks.map((t) => ({ ...t })),
        prioritiesMust: [...ex.prioritiesMust],
        prioritiesShould: [...ex.prioritiesShould],
        prioritiesNice: [...ex.prioritiesNice],
        dependenciesText: ex.dependenciesText,
        bottlenecks: ex.bottlenecks.map((b) => ({ ...b })),
        roles: ex.roles.map((r) => ({ ...r })),
        decisions: ex.decisions.map((d) => ({ ...d })),
      };
    },
    statusLabel(s) {
      const l = {
        done: this.$t('projectCard.tlDone'),
        progress: this.$t('projectCard.tlProgress'),
        risk: this.$t('projectCard.tlRisk'),
        waiting: this.$t('projectCard.tlWaiting'),
      };
      return l[s] || s;
    },
    riskLabel(r) {
      const l = {
        normal: this.$t('projectCard.riskNormal'),
        medium: this.$t('projectCard.riskMedium'),
        high: this.$t('projectCard.riskHigh'),
        critical: this.$t('projectCard.riskCritical'),
      };
      return l[r] || r;
    },
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
        const prefix = this.$t('projectCard.pdfFilePrefix');
        pdf.save(`${prefix}-${name || 'project'}.pdf`);
      } catch (e) {
        console.error(e);
        alert(this.$t('projectCard.exportPdfError'));
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
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.pcard-load-example {
  padding: 12px 24px;
  background: #f1f5f9;
  color: #0f172a;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
}

.pcard-load-example:hover {
  background: #e2e8f0;
}

.pcard-ai-error {
  color: #b91c1c;
  font-size: 0.9rem;
  margin: 0 0 12px;
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

.pcard-section-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 4px;
}

.pcard-section-head h2 {
  margin: 0;
}

.pcard-ai-btn {
  padding: 6px 12px;
  font-size: 0.8rem;
  font-weight: 600;
  border-radius: 8px;
  border: 1px solid rgba(37, 99, 235, 0.45);
  background: #eff6ff;
  color: #1d4ed8;
  cursor: pointer;
  white-space: nowrap;
}

.pcard-ai-btn:hover:not(:disabled) {
  background: #dbeafe;
}

.pcard-ai-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.project-card-a3 {
  background: linear-gradient(180deg, #fafbfc 0%, #fff 80px);
  padding: 28px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
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
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
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

.section-tasks {
  grid-column: 1;
}
.section-priorities {
  grid-column: 2;
}
.section-deps {
  grid-column: 1 / -1;
}
.section-bottleneck {
  grid-column: 1 / -1;
}
.section-roles {
  grid-column: 1;
}
.section-decisions {
  grid-column: 2;
}

.deps-textarea {
  width: 100%;
  box-sizing: border-box;
  padding: 12px 14px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 0.9rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 120px;
}

.tasks-table,
.roles-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85rem;
}

.tasks-table th,
.tasks-table td,
.roles-table th,
.roles-table td {
  border: 1px solid #e2e8f0;
  padding: 8px 10px;
  text-align: left;
}

.tasks-table th,
.roles-table th {
  background: #f1f5f9;
  font-weight: 600;
  color: #475569;
}

.tasks-table input,
.roles-table input,
.tasks-table select,
.roles-table select {
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

.col-num {
  width: 40px;
  min-width: 40px;
  text-align: center;
}
.col-task {
  min-width: 260px;
}
.col-status {
  width: 1%;
  white-space: nowrap;
  min-width: 140px;
}
.col-deadline {
  min-width: 100px;
}
.col-who {
  min-width: 160px;
}
.col-risk {
  white-space: nowrap;
}

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

.pcard-tl {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  cursor: pointer;
  padding: 0;
  flex-shrink: 0;
  background: #e2e8f0;
  box-sizing: border-box;
}

.pcard-tl:hover {
  filter: brightness(1.05);
}

.pcard-tl.tl-green.pcard-tl--on {
  background: #22c55e;
  border-color: #15803d;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.35);
}
.pcard-tl.tl-yellow.pcard-tl--on {
  background: #eab308;
  border-color: #a16207;
  box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.35);
}
.pcard-tl.tl-red.pcard-tl--on {
  background: #ef4444;
  border-color: #b91c1c;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.35);
}
.pcard-tl.tl-gray.pcard-tl--on {
  background: #64748b;
  border-color: #334155;
  box-shadow: 0 0 0 2px rgba(100, 116, 139, 0.35);
}

.status-label {
  margin-left: 8px;
  font-size: 0.8rem;
  color: #64748b;
}

.input-num {
  max-width: 56px;
}

.priority-block {
  margin-bottom: 14px;
  padding: 10px 12px;
  border-radius: 8px;
  border-left: 4px solid #cbd5e1;
}

.priority-block.must {
  border-left-color: #dc2626;
  background: #fef2f2;
}
.priority-block.should {
  border-left-color: #eab308;
  background: #fefce8;
}
.priority-block.nice {
  border-left-color: #22c55e;
  background: #f0fdf4;
}

.priority-block h3 {
  margin: 0 0 8px;
  font-size: 0.9rem;
  font-weight: 700;
  color: #334155;
}

.priority-block ul {
  list-style: none;
  padding: 0;
  margin: 0;
}
.priority-block li {
  margin-bottom: 6px;
}

.priority-block input {
  width: 100%;
  min-width: 0;
  padding: 6px 10px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 0.85rem;
  box-sizing: border-box;
}

.add-row-btn,
.add-item-btn {
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

.add-row-btn:hover:not(:disabled),
.add-item-btn:hover {
  background: #e2e8f0;
}

.add-row-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.add-item-btn {
  padding: 4px 12px;
  font-size: 0.9rem;
}

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

.risk-dots {
  display: inline-flex;
  gap: 5px;
  align-items: center;
}

.pcard-risk {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  padding: 0;
  cursor: pointer;
  flex-shrink: 0;
  background: #e2e8f0;
  box-sizing: border-box;
}

.pcard-risk:hover {
  filter: brightness(1.08);
}

.pcard-risk--normal.pcard-risk--on {
  background: #22c55e;
  border-color: #15803d;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.35);
}
.pcard-risk--medium.pcard-risk--on {
  background: #eab308;
  border-color: #a16207;
  box-shadow: 0 0 0 2px rgba(234, 179, 8, 0.35);
}
.pcard-risk--high.pcard-risk--on {
  background: #f97316;
  border-color: #c2410c;
  box-shadow: 0 0 0 2px rgba(249, 115, 22, 0.35);
}
.pcard-risk--critical.pcard-risk--on {
  background: #ef4444;
  border-color: #b91c1c;
  box-shadow: 0 0 0 2px rgba(239, 68, 68, 0.35);
}

.risk-label {
  margin-left: 8px;
  font-size: 0.8rem;
  color: #64748b;
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
  .section-tasks,
  .section-priorities,
  .section-deps,
  .section-bottleneck,
  .section-roles,
  .section-decisions {
    grid-column: 1;
  }
}

@media (max-width: 768px) {
  .project-card-page {
    padding: 16px;
  }
  .col-task {
    min-width: 180px;
  }
  .col-who {
    min-width: 120px;
  }
}
</style>
