<template>
  <div class="pws pws-ps" :class="'pws-ps--s' + form.step">
    <div v-if="loading" class="pws__load">{{ $t('agileTraining.common.loading') }}…</div>
    <template v-else>
      <div class="pws__bar">
        <div class="pws__brand">📘 {{ $t('agileTraining.workshops.productStories.title') }}</div>
        <div class="pws__steps" :aria-label="$t('agileTraining.workshops.productStories.stepProgress')">
          <span v-for="n in 11" :key="n" class="pws__dot" :class="{ isOn: form.step === n, isDone: form.step > n }" />
        </div>
        <div class="pws__lang">
          <button type="button" :class="{ on: locale === 'ru' }" @click="setLoc('ru')">RU</button>
          <button type="button" :class="{ on: locale === 'en' }" @click="setLoc('en')">EN</button>
        </div>
      </div>

      <!-- 1 — контекст + имя -->
      <section v-if="form.step === 1" class="pws__card">
        <h1>{{ $t('agileTraining.workshops.productStories.s1Title') }}</h1>
        <p class="pws__case">{{ intro.contextCase }}</p>
        <p class="pws__warn">{{ intro.instability }}</p>
        <label class="pws__namelab">{{ $t('agileTraining.workshops.productStories.nameForPdf') }}</label>
        <input v-model="displayName" class="pws__name" :placeholder="$t('agileTraining.workshops.productStories.namePh')" @input="onNameInput" />
        <p class="pws__mini">{{ $t('agileTraining.workshops.productStories.nameHint') }}</p>
        <div class="pws__actions">
          <span />
          <button class="pws__btn" @click="go(2)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 2 — примеры -->
      <section v-else-if="form.step === 2" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s2Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s2Lede') }}</p>
        <div class="pws__ex">
          <h4 class="pws__h4">User Story</h4>
          <p>{{ ex.us }}</p>
          <h4 class="pws__h4">Job Story</h4>
          <p>{{ ex.js }}</p>
          <p class="pws__diff">{{ ex.diff }}</p>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 1">←</button>
          <button class="pws__btn" @click="go(3)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 3 — User Story -->
      <section v-else-if="form.step === 3" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s3Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s3Lede') }}</p>
        <ul class="pws__q">
          <li v-for="(q, i) in usPrompts" :key="'usq' + i">{{ q }}</li>
        </ul>
        <p class="pws__format">«{{ $t('agileTraining.workshops.productStories.formatUs') }}»</p>
        <textarea v-model="form.user_story" rows="4" class="pws__ta" :placeholder="$t('agileTraining.workshops.yourText')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiUs">👉 {{ $t('agileTraining.workshops.productStories.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 2">←</button>
          <button class="pws__btn" @click="go(4)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 4 — Job Story -->
      <section v-else-if="form.step === 4" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s4Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s4Lede') }}</p>
        <ul class="pws__q">
          <li v-for="(q, i) in jsPrompts" :key="'jsq' + i">{{ q }}</li>
        </ul>
        <p class="pws__format">«{{ $t('agileTraining.workshops.productStories.formatJs') }}»</p>
        <textarea v-model="form.job_story" rows="4" class="pws__ta" :placeholder="$t('agileTraining.workshops.yourText')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiJs">👉 {{ $t('agileTraining.workshops.productStories.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 3">←</button>
          <button class="pws__btn" @click="go(5)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 5 — сравнение -->
      <section v-else-if="form.step === 5" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s5Title') }}</h2>
        <p class="pws__note">{{ $t('agileTraining.workshops.productStories.noScoring') }}</p>
        <div class="pws__row2">
          <div class="pws__col">
            <h4 class="pws__h4">User Story</h4>
            <p class="pws__out">{{ form.user_story || '—' }}</p>
          </div>
          <div class="pws__col">
            <h4 class="pws__h4">Job Story</h4>
            <p class="pws__out">{{ form.job_story || '—' }}</p>
          </div>
        </div>
        <p class="pws__attn">{{ intro.compareLead }}</p>
        <ul class="pws__ul">
          <li v-for="(q, i) in intro.discussionQ" :key="i">{{ q }}</li>
        </ul>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 4">←</button>
          <button class="pws__btn" @click="go(6)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 6 — эпик -->
      <section v-else-if="form.step === 6" class="pws__card">
        <h2>{{ intro.epicTitle }}</h2>
        <p class="pws__prose">{{ intro.epicBody }}</p>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 5">←</button>
          <button class="pws__btn" @click="go(7)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 7 — пример декомпозиции -->
      <section v-else-if="form.step === 7" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s7Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s7Lede') }}</p>
        <ol class="pws__ol">
          <li v-for="(x, i) in decompEx" :key="i">{{ x }}</li>
        </ol>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 6">←</button>
          <button class="pws__btn" @click="go(8)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 8 — декомпозиция -->
      <section v-else-if="form.step === 8" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s8Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s8Lede') }}</p>
        <ul class="pws__q">
          <li v-for="(q, i) in decompGuidance" :key="'dg' + i">{{ q }}</li>
        </ul>
        <div v-for="(t, i) in form.tasks" :key="t.id" class="pws__line">
          <input v-model="t.text" :placeholder="$t('agileTraining.workshops.productStories.taskPh')" />
          <button type="button" class="pws__x" :aria-label="$t('agileTraining.workshops.productStories.removeRow')" @click="removeTask(i)">✕</button>
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="addTask">+ {{ $t('agileTraining.workshops.productStories.addTask') }}</button>
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiDecomp">👉 {{ $t('agileTraining.workshops.productStories.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 7">←</button>
          <button class="pws__btn" @click="go(9)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 9 — SPIDR / 7 dim -->
      <section v-else-if="form.step === 9" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s9Title') }}</h2>
        <p class="pws__lede">{{ $t('agileTraining.workshops.productStories.s9Lede') }}</p>
        <div class="pws__toolbox">
          <p class="pws__tooltxt"><label class="pws__lab"><input v-model="form.tool" type="radio" value="spidr" /> SPIDR</label></p>
          <p class="pws__hint2">{{ intro.toolSpidr }}</p>
          <p class="pws__tooltxt"><label class="pws__lab"><input v-model="form.tool" type="radio" value="seven_dim" /> 7 dimensions</label></p>
          <p class="pws__hint2">{{ intro.tool7d }}</p>
        </div>
        <textarea v-model="form.tool_notes" rows="4" class="pws__ta" :placeholder="$t('agileTraining.workshops.notesPlaceholder')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiTool">👉 {{ $t('agileTraining.workshops.productStories.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 8">←</button>
          <button class="pws__btn" @click="go(10)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 10 — улучшение -->
      <section v-else-if="form.step === 10" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s10Title') }}</h2>
        <p class="pws__prose">{{ intro.s10improvementLead }}</p>
        <div v-for="(t, i) in form.tasks" :key="t.id + 'r'" class="pws__line">
          <input v-model="t.text" :placeholder="$t('agileTraining.workshops.productStories.taskPh')" />
          <button type="button" class="pws__x" :aria-label="$t('agileTraining.workshops.productStories.removeRow')" @click="removeTask(i)">✕</button>
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="addTask">+ {{ $t('agileTraining.workshops.productStories.addTask') }}</button>
        <textarea v-model="form.refinement_notes" rows="3" class="pws__ta" :placeholder="$t('agileTraining.workshops.productNotes')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiRefine">👉 {{ $t('agileTraining.workshops.productStories.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 9">←</button>
          <button class="pws__btn" @click="go(11)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <!-- 11 — итог + PDF -->
      <section v-else class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s11Title') }}</h2>
        <p class="pws__note">{{ $t('agileTraining.workshops.productStories.s11Lede') }}</p>
        <div ref="pdfRoot" class="pws__pdf">
          <p class="pws__pdfmeta">{{ pdfDateLine }}</p>
          <p><b>{{ $t('agileTraining.workshops.productStories.nameForPdf') }}:</b> {{ displayName || '—' }}</p>
          <h4 class="pws__h4">{{ $t('agileTraining.workshops.productStories.pdfContext') }}</h4>
          <p>{{ intro.contextCase }}</p>
          <p class="pws__mini">{{ intro.instability }}</p>
          <h4 class="pws__h4">User Story</h4>
          <p>{{ form.user_story || '—' }}</p>
          <h4 class="pws__h4">Job Story</h4>
          <p>{{ form.job_story || '—' }}</p>
          <h4 class="pws__h4">{{ $t('agileTraining.workshops.decomposition') }}</h4>
          <ul>
            <li v-for="(t, i) in form.tasks" :key="i">{{ t.text || '—' }}</li>
          </ul>
          <h4 class="pws__h4">{{ $t('agileTraining.workshops.productStories.pdfTool') }}</h4>
          <p>{{ form.tool === 'seven_dim' ? '7 dimensions' : 'SPIDR' }}</p>
          <p class="pws__pre2">{{ form.tool_notes || '—' }}</p>
          <h4 v-if="form.refinement_notes" class="pws__h4">{{ $t('agileTraining.workshops.productStories.pdfRefine') }}</h4>
          <p v-if="form.refinement_notes" class="pws__pre2">{{ form.refinement_notes }}</p>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 10">←</button>
          <button class="pws__btn" :disabled="pdfIng" @click="pdf">{{ pdfIng ? '…' : $t('agileTraining.common.downloadPdf') }}</button>
        </div>
      </section>
    </template>

    <div v-if="aiOpen" class="pws__modal" @click.self="aiOpen = false">
      <div class="pws__modal-box">
        <h3 class="pws__modtit">{{ $t('agileTraining.workshops.productStories.aiModalTitle') }}</h3>
        <div class="pws__ai-out">{{ aiText }}</div>
        <button type="button" class="pws__btn" @click="aiOpen = false">OK</button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';
import { fetchWorkshopState, saveWorkshopData, callWorkshopCopilot } from '@/utils/workshopHelpers.js';

const EX = 'product_stories';

function uid() {
  return 't' + Date.now() + Math.random().toString(16).slice(2);
}

const emptyForm = () => ({
  step: 1,
  user_story: '',
  job_story: '',
  tasks: [{ id: uid(), text: '' }],
  tool: 'spidr',
  tool_notes: '',
  refinement_notes: '',
});

function migratePayload(d) {
  if (!d || typeof d !== 'object') return emptyForm();
  const out = { ...emptyForm(), ...d };
  if (d.decomposition && !d.tasks) {
    out.tasks = d.decomposition
      .map((x, i) => ({ id: uid() + i, text: (x && x.text) || '' }))
      .filter(t => t.text);
    if (!out.tasks.length) out.tasks = [{ id: uid(), text: '' }];
  }
  if (!out.tasks || !out.tasks.length) out.tasks = [{ id: uid(), text: '' }];
  if (d.discussion && !d.refinement_notes) out.refinement_notes = d.discussion;
  if (d.requests) {
    const o = d.step | 0;
    const map = { 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 6: 5, 7: 8, 8: 9, 9: 10, 10: 11 };
    out.step = map[o] || o;
  }
  let s = out.step | 0;
  if (s < 1) s = 1;
  if (s > 11) s = 11;
  out.step = s;
  delete out.decomposition;
  delete out.requests;
  return out;
}

export default {
  name: 'AgileProductStoriesPlay',
  props: { slug: { type: String, required: true } },
  data() {
    return {
      loading: true,
      locale: 'ru',
      group: null,
      content: { intro: {} },
      form: emptyForm(),
      displayName: '',
      participantToken: '',
      pdfIng: false,
      aiLoad: false,
      aiOpen: false,
      aiText: '',
    };
  },
  computed: {
    intro() {
      const base = {
        example: {},
        decompExample: [],
        discussionQ: [],
        usPrompts: [],
        jsPrompts: [],
        decompGuidanceQ: [],
        compareLead: '',
        epicTitle: this.$t('agileTraining.workshops.productStories.epicFallbackTitle'),
        epicBody: this.$t('agileTraining.workshops.productStories.epicFallbackBody'),
        s10improvementLead: '',
        toolSpidr: '',
        tool7d: '',
        contextCase: '',
        instability: '',
      };
      return { ...base, ...(this.content.intro || {}) };
    },
    ex() { return this.intro.example || { us: '', js: '', diff: '' }; },
    decompEx() { return this.intro.decompExample || []; },
    usPrompts() { return this.intro.usPrompts || []; },
    jsPrompts() { return this.intro.jsPrompts || []; },
    decompGuidance() { return this.intro.decompGuidanceQ || []; },
    pdfDateLine() {
      const loc = this.locale === 'en' ? 'en-US' : 'ru-RU';
      try {
        return this.$t('agileTraining.workshops.productStories.pdfDate', { d: new Date().toLocaleDateString(loc) });
      } catch (_) {
        return new Date().toLocaleDateString(loc);
      }
    },
  },
  watch: {
    form: { deep: true, handler() { this.debouncedSave(); } },
    displayName() { this.persistName(); this.debouncedSave(); },
  },
  created() {
    this._saveT = null;
  },
  async mounted() {
    this.locale = (localStorage.getItem('language') === 'en') ? 'en' : 'ru';
    this.participantToken = localStorage.getItem(`pws_ps_${this.slug}`) || '';
    this.displayName = localStorage.getItem(`pws_ps_name_${this.slug}`) || '';
    await this.boot();
  },
  methods: {
    setLoc(lc) {
      this.locale = lc;
      try { localStorage.setItem('language', lc); } catch (_err) { /* ignore */ }
      if (this.$i18n) this.$i18n.locale = lc;
      this.boot();
    },
    persistName() {
      try { localStorage.setItem(`pws_ps_name_${this.slug}`, this.displayName || ''); } catch (_err) { /* ignore */ }
    },
    onNameInput() { this.persistName(); },
    addTask() {
      this.form.tasks.push({ id: uid(), text: '' });
    },
    removeTask(i) {
      if (this.form.tasks.length <= 1) {
        this.form.tasks[0].text = '';
        return;
      }
      this.form.tasks.splice(i, 1);
    },
    async boot() {
      this.loading = true;
      try {
        if (!this.participantToken) {
          const r = await axios.post(
            `/api/agile-training/g/${this.slug}/participant`,
            { display_name: this.displayName || null },
          );
          this.participantToken = r.data.participant_token;
          localStorage.setItem(`pws_ps_${this.slug}`, this.participantToken);
        }
        const st = await fetchWorkshopState(EX, this.slug, this.participantToken, this.locale);
        this.group = st.group;
        this.content = { ...st.content, intro: (st.content && st.content.intro) || {} };
        if (st.data && typeof st.data === 'object') {
          this.form = migratePayload(st.data);
          if (st.data.display_name) this.displayName = st.data.display_name;
        }
      } catch (e) { console.error(e); }
      finally { this.loading = false; }
    },
    debouncedSave() {
      clearTimeout(this._saveT);
      this._saveT = setTimeout(() => this.saveNow(), 500);
    },
    async saveNow() {
      if (!this.participantToken) return;
      try {
        const payload = {
          ...this.form,
          step: this.form.step,
          display_name: this.displayName,
        };
        await saveWorkshopData(EX, this.slug, this.participantToken, payload);
      } catch (_err) { /* ignore */ }
    },
    async go(s) {
      this.persistName();
      await this.saveNow();
      this.form.step = s;
    },
    async aiUs() {
      const ctx = [
        this.$t('agileTraining.workshops.productStories.formatUs'),
        ...(this.usPrompts.length ? this.usPrompts : []),
      ].join('\n');
      await this.runAi('us_draft', this.form.user_story, ctx);
    },
    async aiJs() {
      const ctx = [
        this.$t('agileTraining.workshops.productStories.formatJs'),
        'User story draft:\n' + (this.form.user_story || '—'),
        ...(this.jsPrompts.length ? this.jsPrompts : []),
      ].join('\n');
      await this.runAi('js_draft', this.form.job_story, ctx);
    },
    async aiDecomp() {
      const list = (this.form.tasks || []).map(t => t.text).filter(Boolean).join(' | ') || '—';
      const ctx = (this.decompGuidance || []).join('\n');
      await this.runAi('decomposition', list, ctx);
    },
    async aiTool() {
      const ctx = (this.form.tool === 'seven_dim' ? (this.intro.tool7d || '') : (this.intro.toolSpidr || '')) + '\n' + (this.form.tasks || []).map(t => t.text).filter(Boolean).join(' | ');
      await this.runAi('tool_notes ' + this.form.tool, this.form.tool_notes, ctx);
    },
    async aiRefine() {
      const ctx = [
        (this.form.tasks || []).map((t, i) => `${i + 1}. ${t.text}`).join('\n'),
        'SPIDR/7d notes:\n' + (this.form.tool_notes || '—'),
      ].join('\n\n');
      await this.runAi('refine_tasks', this.form.refinement_notes, ctx);
    },
    async runAi(step, userText, context) {
      this.aiLoad = true;
      try {
        const r = await callWorkshopCopilot({
          exerciseKey: EX,
          step,
          userText: userText || '',
          locale: this.locale,
          context: context || '',
        });
        this.aiText = (r && r.reply) || '';
        this.aiOpen = true;
      } catch (e) {
        this.aiText = (e.response && e.response.data && e.response.data.error) || String(e);
        this.aiOpen = true;
      } finally { this.aiLoad = false; }
    },
    async pdf() {
      const el = this.$refs.pdfRoot;
      if (!el) return;
      this.pdfIng = true;
      try {
        const res = await exportElementToPdf(el, `product-stories-${this.slug}`);
        if (!res.ok) throw new Error(res.error);
      } catch (e) { console.error(e); }
      finally { this.pdfIng = false; }
    },
  },
};
</script>

<style scoped>
.pws { max-width: 720px; margin: 0 auto; padding: 16px; font-size: 15px; color: #0f172a; }
.pws__load { padding: 40px; text-align: center; color: #64748b; }
.pws__bar { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 10px; margin-bottom: 16px; }
.pws__brand { font-weight: 800; }
.pws__steps { display: flex; gap: 3px; flex-wrap: wrap; max-width: 220px; }
.pws__dot { width: 7px; height: 7px; border-radius: 50%; background: #e2e8f0; }
.pws__dot.isOn { background: #7c3aed; }
.pws__dot.isDone { background: #c4b5fd; }
.pws__lang button { border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 4px 10px; font-weight: 700; cursor: pointer; }
.pws__lang button.on { background: #ede9fe; border-color: #7c3aed; }
.pws__card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; }
.pws h1, .pws h2 { margin-top: 0; }
.pws__case { font-size: 17px; font-weight: 600; }
.pws__warn { color: #b45309; }
.pws__lede, .pws__note, .pws__mini { color: #64748b; font-size: 14px; line-height: 1.45; }
.pws__ex { background: #f8fafc; border-radius: 12px; padding: 12px; }
.pws__h4 { margin: 0 0 4px; font-size: 14px; }
.pws__diff { margin-top: 10px; font-size: 14px; color: #334155; border-top: 1px solid #e2e8f0; padding-top: 10px; }
.pws__q { margin: 8px 0; padding-left: 18px; color: #475569; }
.pws__format { font-size: 13px; color: #5b21b6; background: #f5f3ff; padding: 6px 10px; border-radius: 8px; }
.pws__ta { width: 100%; border-radius: 10px; border: 1px solid #cbd5e1; padding: 10px; font-size: 14px; }
.pws__actions { display: flex; justify-content: space-between; margin-top: 16px; flex-wrap: wrap; gap: 8px; }
.pws__btn { background: #7c3aed; color: #fff; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__btn--ghost { background: #f1f5f9; color: #0f172a; }
.pws__ai { background: #fff; border: 1px dashed #a78bfa; color: #5b21b6; padding: 8px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__row { margin-top: 10px; }
.pws__row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
@media (max-width: 600px) { .pws__row2 { grid-template-columns: 1fr; } }
.pws__col { min-width: 0; }
.pws__out { background: #f8fafc; padding: 8px; border-radius: 8px; min-height: 3em; white-space: pre-wrap; }
.pws__ul { margin: 8px 0; padding-left: 18px; }
.pws__attn { font-weight: 600; font-size: 14px; margin: 10px 0 4px; }
.pws__ol { margin: 8px 0; padding-left: 20px; }
.pws__prose { line-height: 1.55; color: #334155; }
.pws__line { display: flex; gap: 6px; margin-bottom: 6px; }
.pws__line input { flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; }
.pws__x { border: none; background: #fee2e2; color: #991b1b; border-radius: 6px; width: 28px; cursor: pointer; flex-shrink: 0; }
.pws__lab { display: block; margin: 4px 0; font-size: 14px; }
.pws__toolbox { background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 10px; padding: 8px 12px; margin-bottom: 8px; }
.pws__hint2 { font-size: 13px; color: #64748b; margin: 0 0 8px; }
.pws__tooltxt { margin: 0; }
.pws__namelab { display: block; font-size: 13px; font-weight: 600; margin: 12px 0 4px; }
.pws__name { width: 100%; border: 1px solid #cbd5e1; border-radius: 8px; padding: 8px; font-size: 15px; }
.pws__pdfmeta { font-size: 13px; color: #64748b; margin: 0 0 6px; }
.pws__pre2 { white-space: pre-wrap; margin: 0; font-size: 14px; }
.pws__modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px; }
.pws__modal-box { background: #fff; border-radius: 14px; padding: 16px; max-width: 520px; max-height: 80vh; overflow: auto; }
.pws__modtit { margin: 0 0 8px; }
.pws__ai-out { white-space: pre-wrap; font-size: 14px; line-height: 1.5; }
.pws__pdf { background: #fafafa; border: 1px solid #e5e5e5; padding: 12px; border-radius: 10px; }
</style>
