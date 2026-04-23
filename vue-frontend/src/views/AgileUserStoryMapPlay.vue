<template>
  <div class="pws pws-usm">
    <div v-if="loading" class="pws__load">{{ $t('agileTraining.common.loading') }}…</div>
    <template v-else>
      <div class="pws__bar">
        <b>🗺️ USM</b>
        <div class="pws__lang">
          <button type="button" :class="{ on: locale === 'ru' }" @click="setLoc('ru')">RU</button>
          <button type="button" :class="{ on: locale === 'en' }" @click="setLoc('en')">EN</button>
        </div>
      </div>
      <section v-if="step === 1" class="pws__card">
        <h1>{{ $t('agileTraining.workshops.userStoryMap.s1') }}</h1>
        <button v-for="p in processOpts" :key="p.key" type="button" class="pws__chip" :class="{ on: form.processKey === p.key }" @click="form.processKey = p.key">
          {{ p.label }}
        </button>
        <input v-if="form.processKey === 'custom'" v-model="form.customProcess" class="pws__ta" :placeholder="$t('agileTraining.workshops.customPh')" />
        <div class="pws__actions"><button class="pws__btn" @click="step = 2">{{ $t('agileTraining.workshops.next') }} →</button></div>
      </section>
      <section v-else-if="step === 2" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.userStoryMap.s2') }}</h2>
        <div class="pws__map-preview">
          <p><b>{{ ex.role }}</b> → <b>{{ ex.goal }}</b></p>
          <div class="pws__cols">
            <div v-for="(s, i) in ex.steps" :key="i" class="pws__mcol">
              <div class="pws__mh">{{ s }}</div>
              <div class="pws__mcell">{{ ex.stories[i] }}</div>
            </div>
          </div>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 1">←</button>
          <button class="pws__btn" @click="step = 3">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else-if="step === 3" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.userStoryMap.s3') }}</h2>
        <input v-model="form.role" class="pws__ta" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 2">←</button>
          <button class="pws__btn" @click="go(4)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else-if="step === 4" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.userStoryMap.s4') }}</h2>
        <input v-model="form.goal" class="pws__ta" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 3">←</button>
          <button class="pws__btn" @click="go(5)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else-if="step === 5" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.userStoryMap.s5') }}</h2>
        <div v-for="(s, i) in form.steps" :key="s.id" class="pws__line">
          <input v-model="s.title" :placeholder="$t('agileTraining.workshops.userStoryMap.stepPh')" />
          <button type="button" @click="move(form.steps, i, -1)">↑</button>
          <button type="button" @click="move(form.steps, i, 1)">↓</button>
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="form.steps.push({ id: uid(), title: '' })">+</button>
        <div class="pws__row"><button class="pws__ai" type="button" :disabled="aiLoad" @click="askAi('backbone', form.steps.map(s => s.title).join(' | '))">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button></div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 4">←</button>
          <button class="pws__btn" @click="go(6)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else-if="step === 6" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.userStoryMap.s6') }}</h2>
        <div v-for="s in form.steps" :key="s.id" class="pws__blk">
          <b>{{ s.title || '—' }}</b>
          <div v-for="t in (tasks(s.id) || [])" :key="t.id" class="pws__line2">
            <input v-model="t.title" />
            <input
              class="pws__us"
              :value="form.stories[t.id] || ''"
              :placeholder="$t('agileTraining.workshops.userStoryMap.usPh')"
              @input="form.stories[t.id] = $event.target.value"
            />
          </div>
          <button type="button" class="pws__btn pws__btn--ghost" @click="addTask(s.id)">+ {{ $t('agileTraining.workshops.userStoryMap.addTask') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 5">←</button>
          <button class="pws__btn" @click="go(7)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else-if="step === 7" class="pws__card">
        <h2>MVP</h2>
        <label v-for="s in allStoryIds" :key="s.id" class="pws__lab">
          <input type="checkbox" :value="s.id" v-model="form.mvpIds" /> {{ s.label }}
        </label>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 6">←</button>
          <button class="pws__btn" @click="go(8)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>
      <section v-else class="pws__card">
        <h2>{{ $t('agileTraining.workshops.final') }}</h2>
        <div class="pws__board" ref="pdfRoot">
          <p><b>{{ form.role }}</b> — {{ form.goal }}</p>
          <div class="pws__cols2">
            <div v-for="s in form.steps" :key="s.id" class="pws__bcol">
              <div class="pws__bh">{{ s.title }}</div>
              <div v-for="t in (tasks(s.id) || [])" :key="t.id" class="pws__note">
                <div>{{ t.title }}</div>
                <small>{{ form.stories[t.id] || '' }}</small>
              </div>
            </div>
          </div>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="step = 7">←</button>
          <button class="pws__btn" :disabled="pdfIng" @click="pdf">{{ $t('agileTraining.common.downloadPdf') }}</button>
        </div>
      </section>
    </template>
    <div v-if="aiText" class="pws__modal" @click.self="aiText = ''"><div class="pws__modal-box"><pre>{{ aiText }}</pre><button class="pws__btn" @click="aiText = ''">OK</button></div></div>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';
import { fetchWorkshopState, saveWorkshopData, callWorkshopCopilot } from '@/utils/workshopHelpers.js';

const EX = 'user_story_map';

function uid() { return 'k' + Date.now() + Math.random().toString(16).slice(2); }
const defForm = () => ({
  processKey: 'ticket',
  customProcess: '',
  role: '',
  goal: '',
  steps: [{ id: uid(), title: '' }],
  taskByStep: {},
  stories: {},
  mvpIds: [],
});

export default {
  name: 'AgileUserStoryMapPlay',
  props: { slug: { type: String, required: true } },
  data() {
    return {
      loading: true, locale: 'ru', step: 1, form: defForm(), participantToken: '', aiLoad: false, aiText: '', pdfIng: false, content: { intro: {} },
    };
  },
  computed: {
    processOpts() { return (this.content.intro && this.content.intro.processes) || []; },
    ex() { return (this.content.intro && this.content.intro.example) || { role: '', goal: '', steps: [], stories: [] }; },
    allStoryIds() {
      const out = [];
      this.form.steps.forEach(s => {
        (this.tasks(s.id) || []).forEach(t => { out.push({ id: t.id, label: `${s.title} / ${t.title}` }); });
      });
      return out;
    },
  },
  watch: { form: { deep: true, handler() { this.dsave(); } } },
  async mounted() {
    this.locale = (localStorage.getItem('language') === 'en') ? 'en' : 'ru';
    this.participantToken = localStorage.getItem(`pws_usm_${this.slug}`) || '';
    await this.load();
  },
  methods: {
    setLoc(lc) { this.locale = lc; try { localStorage.setItem('language', lc); } catch (_err) { /* ignore */ } if (this.$i18n) this.$i18n.locale = lc; this.load(); },
    tasks(sid) { return this.form.taskByStep[sid] || []; },
    move(arr, i, d) {
      const j = i + d;
      if (j < 0 || j >= arr.length) return;
      [arr[i], arr[j]] = [arr[j], arr[i]];
    },
    addTask(sid) {
      if (!this.form.taskByStep[sid]) this.form.taskByStep[sid] = [];
      this.form.taskByStep[sid].push({ id: uid(), title: '' });
    },
    ensureTasks() {
      this.form.steps.forEach(s => {
        if (!this.form.taskByStep[s.id] || !this.form.taskByStep[s.id].length) {
          this.form.taskByStep[s.id] = [{ id: uid(), title: '' }];
        }
      });
    },
    async load() {
      this.loading = true;
      try {
        if (!this.participantToken) {
          const r = await axios.post(`/api/agile-training/g/${this.slug}/participant`, {});
          this.participantToken = r.data.participant_token;
          localStorage.setItem(`pws_usm_${this.slug}`, this.participantToken);
        }
        const st = await fetchWorkshopState(EX, this.slug, this.participantToken, this.locale);
        this.content = { ...st.content, intro: (st.content && st.content.intro) || {} };
        if (st.data) {
          this.form = { ...defForm(), ...st.data };
          if (!this.form.steps || !this.form.steps.length) this.form.steps = [{ id: uid(), title: '' }];
        }
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
      try { await saveWorkshopData(EX, this.slug, this.participantToken, { ...this.form, step: this.step }); } catch (_err) { /* ignore */ }
    },
    async go(s) {
      await this.save();
      if (s === 6) this.ensureTasks();
      this.step = s;
      await this.save();
    },
    async askAi(step, text) {
      this.aiLoad = true;
      try {
        const r = await callWorkshopCopilot({ exerciseKey: EX, step, userText: text, locale: this.locale });
        this.aiText = (r && r.reply) || '';
      } catch (e) { this.aiText = String(e); }
      finally { this.aiLoad = false; }
    },
    async pdf() {
      this.pdfIng = true;
      try { await exportElementToPdf(this.$refs.pdfRoot, `usm-${this.slug}`); } catch (e) { console.error(e); }
      finally { this.pdfIng = false; }
    },
  },
};
</script>

<style scoped>
.pws-usm { max-width: 900px; margin: 0 auto; padding: 16px; }
.pws__load { text-align: center; padding: 32px; }
.pws__bar { display: flex; justify-content: space-between; margin-bottom: 12px; }
.pws__lang button { border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 4px 10px; margin-left: 4px; cursor: pointer; }
.pws__lang button.on { background: #d1fae5; }
.pws__card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 18px; }
.pws__chip { display: block; width: 100%; text-align: left; margin: 6px 0; padding: 10px; border: 1px solid #e2e8f0; border-radius: 10px; background: #fff; cursor: pointer; }
.pws__chip.on { border-color: #059669; background: #ecfdf5; }
.pws__ta { width: 100%; border-radius: 8px; border: 1px solid #cbd5e1; padding: 8px; }
.pws__map-preview { background: #f8fafc; border-radius: 12px; padding: 10px; overflow: auto; }
.pws__cols { display: flex; gap: 8px; min-width: 400px; }
.pws__mcol { flex: 1; min-width: 100px; }
.pws__mh { background: #0ea5e9; color: #fff; padding: 6px; border-radius: 6px; font-size: 12px; }
.pws__mcell { background: #fff; border: 1px solid #e2e8f0; margin-top: 4px; padding: 4px; font-size: 11px; border-radius: 4px; }
.pws__line { display: flex; gap: 4px; margin-bottom: 6px; }
.pws__line input { flex: 1; border: 1px solid #e2e8f0; border-radius: 6px; padding: 6px; }
.pws__blk { border: 1px dashed #cbd5e1; border-radius: 10px; padding: 8px; margin-bottom: 10px; }
.pws__line2 { display: flex; flex-direction: column; gap: 4px; margin: 4px 0; }
.pws__us { font-size: 12px; }
.pws__cols2 { display: flex; gap: 8px; flex-wrap: wrap; }
.pws__bcol { background: #f0fdf4; border: 1px solid #86efac; border-radius: 8px; padding: 6px; min-width: 120px; flex: 1; }
.pws__bh { font-weight: 800; font-size: 12px; }
.pws__note { background: #fff; border: 1px solid #d1d5db; border-radius: 4px; padding: 4px; font-size: 11px; margin: 2px 0; }
.pws__actions { margin-top: 12px; display: flex; justify-content: space-between; }
.pws__btn { background: #059669; color: #fff; border: none; padding: 8px 16px; border-radius: 8px; font-weight: 700; cursor: pointer; }
.pws__btn--ghost { background: #f1f5f9; color: #0f172a; }
.pws__ai { background: #fff; border: 1px dashed #10b981; }
.pws__board { background: #fafafa; padding: 8px; border-radius: 8px; }
.pws__modal { position: fixed; inset: 0; background: rgba(0,0,0,0.4); z-index: 100; display: flex; align-items: center; justify-content: center; }
.pws__modal-box { background: #fff; padding: 16px; border-radius: 12px; max-width: 90vw; }
.pws__lab { display: block; font-size: 13px; margin: 4px 0; }
</style>
