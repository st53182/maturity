<template>
  <div class="pws pws-ps" :class="'pws-ps--s' + form.step">
    <div v-if="loading" class="pws__load">{{ $t('common.loading') }}…</div>
    <template v-else>
      <div class="pws__bar">
        <div class="pws__brand">📘 {{ $t('agileTraining.workshops.productStories.title') }}</div>
        <div class="pws__steps">
          <span v-for="n in 10" :key="n" class="pws__dot" :class="{ isOn: form.step === n, isDone: form.step > n }" />
        </div>
        <div class="pws__lang">
          <button type="button" :class="{ on: locale === 'ru' }" @click="setLoc('ru')">RU</button>
          <button type="button" :class="{ on: locale === 'en' }" @click="setLoc('en')">EN</button>
        </div>
      </div>

      <section v-if="form.step === 1" class="pws__card">
        <h1>{{ $t('agileTraining.workshops.productStories.s1Title') }}</h1>
        <p class="pws__case">{{ content.intro && content.intro.contextCase }}</p>
        <p class="pws__warn">{{ content.intro && content.intro.instability }}</p>
        <div class="pws__actions">
          <button class="pws__btn" @click="form.step = 2">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 2" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s2Title') }}</h2>
        <div class="pws__ex">
          <h4>User Story</h4>
          <p>{{ ex.us }}</p>
          <h4>Job Story</h4>
          <p>{{ ex.js }}</p>
          <p class="pws__hint">{{ ex.diff }}</p>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 1">←</button>
          <button class="pws__btn" @click="form.step = 3">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 3" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s3Title') }}</h2>
        <p class="pws__hint">«{{ $t('agileTraining.workshops.productStories.formatUs') }}»</p>
        <textarea v-model="form.user_story" rows="4" class="pws__ta" :placeholder="$t('agileTraining.workshops.yourText')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiHelp('user_story', 'user_story', form.user_story)">
            👉 {{ $t('agileTraining.workshops.aiHelp') }}
          </button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 2">←</button>
          <button class="pws__btn" @click="go(4)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 4" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s4Title') }}</h2>
        <div v-for="(r, i) in form.requests" :key="i" class="pws__req">
          <input v-model="r.type" :placeholder="$t('agileTraining.workshops.productStories.reqType')" />
          <input v-model="r.source" :placeholder="$t('agileTraining.workshops.productStories.reqSource')" />
          <input v-model="r.frequency" :placeholder="$t('agileTraining.workshops.productStories.reqFreq')" />
          <input v-model="r.expectations" :placeholder="$t('agileTraining.workshops.productStories.reqExp')" />
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="addReq">+</button>
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiHelp('request analysis', 'requests', JSON.stringify(form.requests))">
            👉 {{ $t('agileTraining.workshops.aiHelp') }}
          </button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 3">←</button>
          <button class="pws__btn" @click="go(5)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 5" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s5Title') }}</h2>
        <p class="pws__hint">«{{ $t('agileTraining.workshops.productStories.formatJs') }}»</p>
        <textarea v-model="form.job_story" rows="4" class="pws__ta" :placeholder="$t('agileTraining.workshops.yourText')" />
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiHelp('job story', 'job_story', form.job_story)">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 4">←</button>
          <button class="pws__btn" @click="go(6)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 6" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s6Title') }}</h2>
        <div class="pws__row2">
          <div><h4>User Story</h4><p class="pws__out">{{ form.user_story || '—' }}</p></div>
          <div><h4>Job Story</h4><p class="pws__out">{{ form.job_story || '—' }}</p></div>
        </div>
        <p class="pws__hint-title">{{ $t('agileTraining.workshops.notice') }}</p>
        <ul class="pws__ul"><li v-for="(q, i) in intro.discussionQ" :key="i">{{ q }}</li></ul>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 5">←</button>
          <button class="pws__btn" @click="form.step = 7">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 7" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s7Title') }}</h2>
        <p class="pws__ex-list"><span v-for="(x, i) in decompEx" :key="i" class="pws__pill">{{ x }}</span></p>
        <h3 class="pws__h3">{{ $t('agileTraining.workshops.productStories.yourDecomp') }}</h3>
        <div v-for="(t, i) in form.decomposition" :key="i" class="pws__line">
          <input v-model="t.text" :placeholder="$t('agileTraining.workshops.productStories.taskPh')" />
          <button type="button" class="pws__x" @click="form.decomposition.splice(i, 1)">✕</button>
        </div>
        <button type="button" class="pws__btn pws__btn--ghost" @click="form.decomposition.push({ text: '' })">+</button>
        <div class="pws__row">
          <button type="button" class="pws__ai" :disabled="aiLoad" @click="aiHelp('decomposition', 'decomp', form.decomposition.map(d => d.text).join(' | '))">👉 {{ $t('agileTraining.workshops.aiHelp') }}</button>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 6">←</button>
          <button class="pws__btn" @click="go(8)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 8" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s8Title') }}</h2>
        <label class="pws__lab"><input v-model="form.tool" type="radio" value="spidr" /> SPIDR</label>
        <label class="pws__lab"><input v-model="form.tool" type="radio" value="seven_dim" /> 7 dimensions</label>
        <textarea v-model="form.tool_notes" rows="3" class="pws__ta" :placeholder="$t('agileTraining.workshops.notesPlaceholder')" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 7">←</button>
          <button class="pws__btn" @click="go(9)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else-if="form.step === 9" class="pws__card">
        <h2>{{ $t('agileTraining.workshops.productStories.s9Title') }}</h2>
        <ul class="pws__ul"><li v-for="(q, i) in discQ" :key="i">{{ q }}</li></ul>
        <textarea v-model="form.discussion" rows="3" class="pws__ta" />
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 8">←</button>
          <button class="pws__btn" @click="go(10)">{{ $t('agileTraining.workshops.next') }} →</button>
        </div>
      </section>

      <section v-else class="pws__card">
        <h2>{{ $t('agileTraining.workshops.final') }}</h2>
        <div ref="pdfRoot" class="pws__pdf">
          <p><b>{{ $t('agileTraining.workshops.name') }}:</b> {{ displayName || '—' }}</p>
          <h4>User Story</h4><p>{{ form.user_story }}</p>
          <h4>Job Story</h4><p>{{ form.job_story }}</p>
          <h4>{{ $t('agileTraining.workshops.decomposition') }}</h4>
          <ul><li v-for="(t, i) in form.decomposition" :key="i">{{ t.text }}</li></ul>
        </div>
        <div class="pws__actions">
          <button class="pws__btn pws__btn--ghost" @click="form.step = 9">←</button>
          <button class="pws__btn" :disabled="pdfIng" @click="pdf">{{ pdfIng ? '…' : $t('agileTraining.common.downloadPdf') }}</button>
        </div>
      </section>
    </template>

    <div v-if="aiOpen" class="pws__modal" @click.self="aiOpen = false">
      <div class="pws__modal-box">
        <h3>AI</h3>
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

const emptyForm = () => ({
  step: 1,
  user_story: '',
  job_story: '',
  requests: [{ type: '', source: '', frequency: '', expectations: '' }],
  decomposition: [{ text: '' }],
  tool: 'spidr',
  tool_notes: '',
  discussion: '',
});

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
    intro() { return this.content.intro || { discussionQ: [] }; },
    ex() { return (this.content.intro && this.content.intro.example) || { us: '', js: '', diff: '' }; },
    decompEx() { return (this.content.intro && this.content.intro.decompExample) || []; },
    discQ() { return (this.content.intro && this.content.intro.discussionQ) || []; },
  },
  watch: {
    'form': {
      deep: true,
      handler() { this.debouncedSave(); },
    },
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
          this.form = { ...emptyForm(), ...st.data, requests: (st.data.requests && st.data.requests.length) ? st.data.requests : emptyForm().requests, decomposition: (st.data.decomposition && st.data.decomposition.length) ? st.data.decomposition : [{ text: '' }] };
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
        const payload = { ...this.form, step: this.form.step };
        await saveWorkshopData(EX, this.slug, this.participantToken, payload);
      } catch (e) { /* ignore */ }
    },
    async go(s) { await this.saveNow(); this.form.step = s; },
    addReq() { this.form.requests.push({ type: '', source: '', frequency: '', expectations: '' }); },
    async aiHelp(stepLabel, k, text) {
      this.aiLoad = true;
      try {
        const r = await callWorkshopCopilot({
          exerciseKey: EX,
          step: stepLabel,
          userText: text,
          locale: this.locale,
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
.pws__steps { display: flex; gap: 4px; }
.pws__dot { width: 8px; height: 8px; border-radius: 50%; background: #e2e8f0; }
.pws__dot.isOn { background: #7c3aed; }
.pws__dot.isDone { background: #a78bfa; }
.pws__lang button { border: 1px solid #e2e8f0; background: #fff; border-radius: 8px; padding: 4px 10px; font-weight: 700; cursor: pointer; }
.pws__lang button.on { background: #ede9fe; border-color: #7c3aed; }
.pws__card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; }
.pws h1, .pws h2 { margin-top: 0; }
.pws__case { font-size: 17px; font-weight: 600; }
.pws__warn { color: #b45309; }
.pws__ex { background: #f8fafc; border-radius: 12px; padding: 12px; }
.pws__hint, .pws__hint-title { color: #64748b; font-size: 14px; }
.pws__ta { width: 100%; border-radius: 10px; border: 1px solid #cbd5e1; padding: 10px; font-size: 14px; }
.pws__actions { display: flex; justify-content: space-between; margin-top: 16px; flex-wrap: wrap; gap: 8px; }
.pws__btn { background: #7c3aed; color: #fff; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__btn--ghost { background: #f1f5f9; color: #0f172a; }
.pws__ai { background: #fff; border: 1px dashed #a78bfa; color: #5b21b6; padding: 8px 14px; border-radius: 10px; font-weight: 700; cursor: pointer; }
.pws__row { margin-top: 8px; }
.pws__req { display: grid; gap: 6px; margin-bottom: 8px; }
.pws__req input { border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; }
.pws__row2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.pws__out { background: #f8fafc; padding: 8px; border-radius: 8px; min-height: 3em; }
.pws__ul { margin: 8px 0; padding-left: 18px; }
.pws__ex-list { display: flex; flex-wrap: wrap; gap: 6px; }
.pws__pill { background: #ecfeff; border: 1px solid #a5f3fc; border-radius: 8px; padding: 4px 8px; font-size: 13px; }
.pws__line { display: flex; gap: 6px; margin-bottom: 6px; }
.pws__line input { flex: 1; border: 1px solid #e2e8f0; border-radius: 8px; padding: 6px; }
.pws__x { border: none; background: #fee2e2; color: #991b1b; border-radius: 6px; width: 28px; cursor: pointer; }
.pws__lab { display: block; margin: 6px 0; }
.pws__h3 { font-size: 15px; }
.pws__modal { position: fixed; inset: 0; background: rgba(15, 23, 42, 0.45); z-index: 200; display: flex; align-items: center; justify-content: center; padding: 20px; }
.pws__modal-box { background: #fff; border-radius: 14px; padding: 16px; max-width: 520px; max-height: 80vh; overflow: auto; }
.pws__ai-out { white-space: pre-wrap; font-size: 14px; line-height: 1.5; }
.pws__pdf { background: #fafafa; border: 1px solid #e5e5e5; padding: 12px; border-radius: 10px; }
</style>
