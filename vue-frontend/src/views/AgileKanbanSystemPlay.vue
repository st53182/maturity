<template>
  <div class="pws pws-kb">
    <div v-if="loading" class="pws__load">{{ $t('agileTraining.common.loading') }}…</div>
    <template v-else>
      <div class="pws__bar">
        <b>📶 {{ $t('agileTraining.workshops.kanbanSystem.bar') }}</b>
        <div class="pws__steps">
          <span v-for="n in 10" :key="n" class="pws__dot" :class="{ isOn: step === n, isDone: step > n }" />
        </div>
        <div class="pws__lang">
          <button type="button" :class="{ on: locale === 'ru' }" @click="setLoc('ru')">RU</button>
          <button type="button" :class="{ on: locale === 'en' }" @click="setLoc('en')">EN</button>
        </div>
      </div>

      <section v-if="step === 1" class="pws__card">
        <h1>{{ $t('agileTraining.workshops.kanbanSystem.s1') }}</h1>
        <p class="pws__case">{{ intro.context && intro.context.text }}</p>
        <p class="pws__warn">{{ intro.context && intro.context.unstable }}</p>
        <p class="pws__cos">{{ intro.cosConflict }}</p>
        <div class="pws__actions">
          <button class="pws__btn" @click="go(2)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 2" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s2') }}</h2>
        <p class="pws__hint">{{ $t('agileTraining.workshops.kanbanSystem.s2hint') }}</p>
        <div class="pws__ex2">
          <h4 class="pws__h4">{{ $t('agileTraining.workshops.kanbanSystem.staticExample') }}</h4>
          <ul class="pws__ul2">
            <li v-for="[k, lab] in staticKeyRows" :key="k">
              <b>{{ lab }}</b><br />
              <span class="pws__exv">{{ (staticEx && staticEx[k]) || '—' }}</span>
            </li>
          </ul>
        </div>
        <div v-for="[k, lab] in staticKeyRows" :key="'in-' + k" class="pws__field">
          <label>{{ lab }}</label>
          <textarea v-model="form.static[k]" rows="2" class="pws__ta" />
        </div>
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="askAi('STATIC profile', staticAiPayload)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 1">←</button>
          <button class="pws__btn" @click="go(3)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 3" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s3') }}</h2>
        <textarea v-model="form.flow" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.flowPh')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="askAi('value stream', form.flow)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 2">←</button>
          <button class="pws__btn" @click="go(4)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 4" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s4') }}</h2>
        <textarea v-model="form.serviceClasses" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.servicePh')" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 3">←</button>
          <button class="pws__btn" @click="go(5)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 5" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s5') }}</h2>
        <textarea v-model="form.policies" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.policiesPh')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="askAi('policies', form.policies)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 4">←</button>
          <button class="pws__btn" @click="go(6)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 6" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s6') }}</h2>
        <textarea v-model="form.cadence" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.cadencePh')" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 5">←</button>
          <button class="pws__btn" @click="go(7)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 7" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s7') }}</h2>
        <div class="pws__board2">
          <div v-for="col in form.boardCols" :key="col.id" class="pws__bcol2">
            <input v-model="col.name" class="pws__colname" />
            <div v-for="(it, idx) in col.items" :key="it.id" class="pws__bline">
              <input v-model="it.text" :placeholder="$t('agileTraining.workshops.kanbanSystem.addCard')" />
              <button type="button" class="pws__x" @click="col.items.splice(idx, 1)">×</button>
            </div>
            <button type="button" class="pws__btn pws__btn--ghost" @click="addCard(col)">+ {{ $t('agileTraining.workshops.kanbanSystem.addCard') }}</button>
          </div>
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="addColumn">+ {{ $t('agileTraining.workshops.kanbanSystem.addColumn') }}</button>
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="askAi('kanban board', boardAiPayload)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 6">←</button>
          <button class="pws__btn" @click="go(8)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 8" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s8') }}</h2>
        <textarea v-model="form.consequences" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.consPh')" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 7">←</button>
          <button class="pws__btn" @click="go(9)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="step === 9" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.kanbanSystem.s9') }}</h2>
        <textarea v-model="form.improve" rows="5" class="pws__ta" :placeholder="$t('agileTraining.workshops.kanbanSystem.improvePh')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="askAi('improvement experiments', form.improve)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 8">←</button>
          <button class="pws__btn" @click="go(10)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else class="pws__card">
        <h2>{{ $t('agileTraining.workshops.final') }}</h2>
        <div ref="pdfRoot" class="pws__pdf">
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s2') }}</h3>
          <ul class="pws__ul2">
            <li v-for="[k, lab] in staticKeyRows" :key="'p-' + k">
              <b>{{ lab }}</b> — {{ form.static[k] || '—' }}
            </li>
          </ul>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s3') }}</h3>
          <p class="pws__blk">{{ form.flow || '—' }}</p>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s4') }}</h3>
          <p class="pws__blk">{{ form.serviceClasses || '—' }}</p>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s5') }}</h3>
          <p class="pws__blk">{{ form.policies || '—' }}</p>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s6') }}</h3>
          <p class="pws__blk">{{ form.cadence || '—' }}</p>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s7') }}</h3>
          <div class="pws__board2 pws__board2--pdf">
            <div v-for="col in form.boardCols" :key="'pc-' + col.id" class="pws__bcol2">
              <div class="pws__bhead">{{ col.name }}</div>
              <ul>
                <li v-for="it in col.items" :key="it.id">{{ it.text || '—' }}</li>
              </ul>
            </div>
          </div>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s8') }}</h3>
          <p class="pws__blk">{{ form.consequences || '—' }}</p>
          <h3>{{ $t('agileTraining.workshops.kanbanSystem.s9') }}</h3>
          <p class="pws__blk">{{ form.improve || '—' }}</p>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 9">←</button>
          <button class="pws__btn" :disabled="pdfIng" @click="pdf">{{ pdfIng ? '…' : $t('agileTraining.common.downloadPdf') }}</button>
        </div>
      </section>
    </template>

    <div v-if="aiText" class="pws__modal" @click.self="aiText = ''">
      <div class="pws__modal-box">
        <pre class="pws__pre2">{{ aiText }}</pre>
        <button class="pws__btn" type="button" @click="aiText = ''">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';
import { fetchWorkshopState, saveWorkshopData, callWorkshopCopilot } from '@/utils/workshopHelpers.js';

const EX = 'kanban_system';

function uid() {
  return 'k' + Date.now() + Math.random().toString(16).slice(2);
}

const emptyStatic = () => ({
  satisfaction: '',
  types: '',
  arrival: '',
  team: '',
  inventory: '',
  kanban: '',
});

const emptyForm = () => ({
  static: emptyStatic(),
  flow: '',
  serviceClasses: '',
  policies: '',
  cadence: '',
  boardCols: [],
  consequences: '',
  improve: '',
});

export default {
  name: 'AgileKanbanSystemPlay',
  props: { slug: { type: String, required: true } },
  data() {
    return {
      loading: true,
      locale: 'ru',
      step: 1,
      form: emptyForm(),
      participantToken: '',
      content: { intro: {} },
      pdfIng: false,
      aiLoad: false,
      aiText: '',
    };
  },
  computed: {
    intro() {
      return this.content.intro || { context: {}, staticExample: {}, staticKeys: [] };
    },
    staticEx() {
      return this.intro.staticExample || {};
    },
    staticKeyRows() {
      const sk = this.intro.staticKeys;
      if (sk && sk.length) return sk.map((row) => (Array.isArray(row) ? row : [row, String(row)]));
      return [
        ['satisfaction', 'S'],
        ['types', 'T'],
        ['arrival', 'A'],
        ['team', 'T'],
        ['inventory', 'I'],
        ['kanban', 'K'],
      ];
    },
    staticAiPayload() {
      return this.staticKeyRows.map(([k, lab]) => `${lab}: ${(this.form.static[k] || '').trim()}`).join('\n');
    },
    boardAiPayload() {
      return (this.form.boardCols || [])
        .map(c => `${c.name}: ${(c.items || []).map(i => i.text).filter(Boolean).join(' | ')}`)
        .join('\n');
    },
  },
  watch: {
    form: { deep: true, handler() { this.dsave(); } },
  },
  async mounted() {
    this.locale = (localStorage.getItem('language') === 'en') ? 'en' : 'ru';
    this.participantToken = localStorage.getItem(`pws_kb_${this.slug}`) || '';
    await this.load();
  },
  methods: {
    async setLoc(lc) {
      this.locale = lc;
      try { localStorage.setItem('language', lc); } catch (_err) { /* ignore */ }
      if (this.$i18n) this.$i18n.locale = lc;
      await this.save();
      await this.load();
    },
    defaultBoardCols() {
      return [
        { id: uid(), name: this.$t('agileTraining.workshops.kanbanSystem.colA'), items: [{ id: uid(), text: '' }] },
        { id: uid(), name: this.$t('agileTraining.workshops.kanbanSystem.colB'), items: [{ id: uid(), text: '' }] },
        { id: uid(), name: this.$t('agileTraining.workshops.kanbanSystem.colC'), items: [{ id: uid(), text: '' }] },
      ];
    },
    ensureBoard() {
      if (!this.form.boardCols || !this.form.boardCols.length) {
        this.form.boardCols = this.defaultBoardCols();
      } else {
        this.form.boardCols.forEach(c => {
          if (!c.items || !c.items.length) c.items = [{ id: uid(), text: '' }];
        });
      }
    },
    addColumn() {
      this.ensureBoard();
      this.form.boardCols.push({ id: uid(), name: '', items: [{ id: uid(), text: '' }] });
    },
    addCard(col) {
      if (!col.items) col.items = [];
      col.items.push({ id: uid(), text: '' });
    },
    async load() {
      this.loading = true;
      try {
        if (!this.participantToken) {
          const r = await axios.post(`/api/agile-training/g/${this.slug}/participant`, {});
          this.participantToken = r.data.participant_token;
          localStorage.setItem(`pws_kb_${this.slug}`, this.participantToken);
        }
        const st = await fetchWorkshopState(EX, this.slug, this.participantToken, this.locale);
        this.content = { ...st.content, intro: (st.content && st.content.intro) || {} };
        if (st.data && typeof st.data === 'object') {
          this.form = { ...emptyForm(), ...st.data, static: { ...emptyStatic(), ...((st.data && st.data.static) || {}) } };
        }
        this.ensureBoard();
        if (st.data && st.data.step) this.step = st.data.step;
      } catch (e) { console.error(e); }
      finally { this.loading = false; }
    },
    dsave() {
      clearTimeout(this._t);
      this._t = setTimeout(this.save, 400);
    },
    async save() {
      if (!this.participantToken) return;
      try {
        await saveWorkshopData(EX, this.slug, this.participantToken, { ...this.form, step: this.step });
      } catch (_err) { /* ignore */ }
    },
    async go(s) {
      if (s === 7) this.ensureBoard();
      await this.save();
      this.step = s;
      await this.save();
    },
    async askAi(stepLabel, text) {
      this.aiLoad = true;
      try {
        const r = await callWorkshopCopilot({ exerciseKey: EX, step: stepLabel, userText: text || '', locale: this.locale });
        this.aiText = (r && r.reply) || '';
      } catch (e) {
        this.aiText = String(e);
      } finally { this.aiLoad = false; }
    },
    async pdf() {
      this.pdfIng = true;
      try {
        const el = this.$refs.pdfRoot;
        if (el) await exportElementToPdf(el, `kanban-system-${this.slug}`);
      } catch (e) { console.error(e); }
      finally { this.pdfIng = false; }
    },
  },
};
</script>

<style scoped>
.pws-kb { max-width: 800px; margin: 0 auto; padding: 16px; font-size: 15px; color: #0f172a; }
.pws__load { text-align: center; padding: 40px; color: #64748b; }
.pws__bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 16px; }
.pws__steps { display: flex; gap: 4px; }
.pws__dot { width: 8px; height: 8px; border-radius: 50%; background: #e2e8f0; }
.pws__dot.isOn { background: #0ea5e9; }
.pws__dot.isDone { background: #7dd3fc; }
.pws__lang button { border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 4px 10px; font-weight: 700; cursor: pointer; }
.pws__lang button.on { background: #e0f2fe; border-color: #0ea5e9; }
.pws__card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; }
.pws h1, .pws h2, .pws h3 { margin-top: 0; }
.pws__case { font-size: 16px; font-weight: 600; }
.pws__warn { color: #b45309; }
.pws__cos { font-style: italic; color: #64748b; }
.pws__hint { color: #64748b; font-size: 14px; }
.pws__ex2 { background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 12px; padding: 12px; margin-bottom: 12px; }
.pws__h4 { margin: 0 0 8px; font-size: 14px; }
.pws__ul2 { margin: 0; padding-left: 18px; font-size: 14px; }
.pws__exv { color: #334155; }
.pws__field { margin-bottom: 10px; }
.pws__field label { display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; }
.pws__ta { width: 100%; border-radius: 10px; border: 1px solid #cbd5e1; padding: 10px; font-size: 14px; }
.pws__row { margin-top: 8px; }
.pws__ai { background: #fff; border: 1px dashed #0ea5e9; color: #0369a1; padding: 8px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__actions { display: flex; justify-content: space-between; margin-top: 16px; flex-wrap: wrap; gap: 8px; }
.pws__btn { background: #0ea5e9; color: #fff; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__btn--ghost { background: #f1f5f9; color: #0f172a; }
.pws__board2 { display: flex; gap: 10px; flex-wrap: wrap; margin: 12px 0; }
.pws__bcol2 { flex: 1; min-width: 140px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 8px; }
.pws__colname { width: 100%; font-weight: 700; border: 1px solid #cbd5e1; border-radius: 6px; padding: 6px; margin-bottom: 6px; }
.pws__bline { display: flex; gap: 4px; margin-bottom: 4px; }
.pws__bline input { flex: 1; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px; font-size: 13px; }
.pws__x { border: none; background: #fee2e2; color: #991b1b; border-radius: 6px; width: 28px; cursor: pointer; }
.pws__board2--pdf { page-break-inside: avoid; }
.pws__bhead { font-weight: 800; font-size: 13px; margin-bottom: 4px; }
.pws__blk { white-space: pre-wrap; }
.pws__pdf { background: #fafafa; border: 1px solid #e5e5e5; padding: 12px; border-radius: 10px; }
.pws__modal { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 200; display: flex; align-items: center; justify-content: center; }
.pws__modal-box { background: #fff; padding: 16px; border-radius: 12px; max-width: 90vw; }
.pws__pre2 { white-space: pre-wrap; max-height: 60vh; overflow: auto; font-size: 14px; }
</style>
