<template>
  <div class="po-play modern-ui" v-if="loading">
    <div class="po-play__spinner"></div>
    <div class="po-play__hint">{{ $t('common.loading') }}…</div>
  </div>
  <div class="po-play po-play--error modern-ui" v-else-if="errorText">
    <p>{{ errorText }}</p>
  </div>
  <div class="po-play modern-ui" v-else>
    <header class="po-play__head">
      <div>
        <h1>🛣️ {{ content.title }}</h1>
        <p class="po-play__subtitle">{{ content.subtitle }}</p>
      </div>
      <div class="po-play__meta">
        <div class="po-play__group">{{ groupName }}</div>
        <div class="po-play__progress">{{ $t('agileTraining.poPath.play.progress', { done: stagesCompleted, total: 4 }) }}</div>
        <div class="po-play__sync" :class="{ 'po-play__sync--saving': syncing, 'po-play__sync--err': lastSaveError }">
          {{ syncing ? $t('agileTraining.poPath.play.saving') : lastSaveError ? $t('agileTraining.poPath.play.saveErr') : $t('agileTraining.poPath.play.saved') }}
        </div>
      </div>
    </header>

    <nav class="po-stepper">
      <button
        v-for="(st, idx) in stages"
        :key="'stp_' + st"
        class="po-step"
        :class="stepClass(st, idx)"
        :disabled="!canSelectStage(st, idx)"
        @click="goStage(st)"
      >
        <span class="po-step__num">{{ idx + 1 }}</span>
        <span class="po-step__label">{{ stageShort(st) }}</span>
        <span class="po-step__status">{{ statusEmoji(stageStatus(st)) }}</span>
      </button>
      <button class="po-step po-step--final" :class="{ 'po-step--active': activeStage === 'done' }" :disabled="!allApproved" @click="activeStage = 'done'">
        <span class="po-step__num">⭐</span>
        <span class="po-step__label">{{ $t('agileTraining.poPath.play.summaryShort') }}</span>
      </button>
    </nav>

    <!-- Welcome -->
    <section v-if="!hasName" class="po-card po-welcome">
      <h2>{{ $t('agileTraining.poPath.play.welcomeTitle') }}</h2>
      <p>{{ content.intro }}</p>
      <ul class="po-welcome__tips">
        <li v-for="(t, i) in content.tips" :key="'tip_' + i">💡 {{ t }}</li>
      </ul>
      <p class="po-welcome__lead">{{ $t('agileTraining.poPath.play.namePrompt') }}</p>
      <div class="po-welcome__row">
        <input v-model="displayNameInput" :placeholder="$t('agileTraining.poPath.play.namePlaceholder')" maxlength="60" />
        <button class="po-btn-primary" @click="startSession" :disabled="!displayNameInput.trim()">{{ $t('agileTraining.poPath.play.start') }} →</button>
      </div>
      <div class="po-welcome__examples">
        <div class="po-welcome__examples-h">{{ $t('agileTraining.poPath.play.ideaExamples') }}</div>
        <ul>
          <li v-for="(ex, i) in content.idea_examples" :key="'ex_' + i">{{ ex }}</li>
        </ul>
      </div>
    </section>

    <!-- Stage screens -->
    <section v-else-if="activeStage !== 'done'" class="po-card po-stage">
      <header class="po-stage__head">
        <div>
          <div class="po-stage__kicker">{{ $t('agileTraining.poPath.play.stageOf', { i: stageIdx + 1, total: 4 }) }}</div>
          <h2>{{ stageContent.title }}</h2>
          <p class="po-stage__context">{{ stageContent.context }}</p>
        </div>
        <span class="po-status" :class="['po-status--' + currentStageStatus]">
          {{ statusEmoji(currentStageStatus) }} {{ statusLabel(currentStageStatus) }}
        </span>
      </header>

      <p class="po-stage__explainer">{{ stageContent.explainer }}</p>

      <!-- Reference panel for value/canvas: show JTBD/Value summary alongside -->
      <aside v-if="activeStage === 'value' && jtbdSummary.length" class="po-ref">
        <div class="po-ref__h">📌 {{ $t('agileTraining.poPath.play.refJtbd') }}</div>
        <ul>
          <li v-for="kv in jtbdSummary" :key="'rj_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li>
        </ul>
      </aside>
      <aside v-if="activeStage === 'fit' && (jtbdSummary.length || valueSummary.length)" class="po-ref">
        <div class="po-ref__h">📌 {{ $t('agileTraining.poPath.play.refPrev') }}</div>
        <details v-if="jtbdSummary.length">
          <summary>JTBD</summary>
          <ul><li v-for="kv in jtbdSummary" :key="'rfj_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li></ul>
        </details>
        <details v-if="valueSummary.length">
          <summary>Value</summary>
          <ul><li v-for="kv in valueSummary" :key="'rfv_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li></ul>
        </details>
      </aside>
      <aside v-if="activeStage === 'canvas'" class="po-ref">
        <div class="po-ref__h">📌 {{ stageContent.auto_prefill_note }}</div>
        <button v-if="canPrefillCanvas" class="po-link-btn" @click="prefillCanvas">⤵ {{ $t('agileTraining.poPath.play.prefill') }}</button>
      </aside>

      <!-- Comments from facilitator (only on revision) -->
      <div v-if="latestRejectionComment" class="po-feedback">
        <div class="po-feedback__h">↩ {{ $t('agileTraining.poPath.play.rejectionTitle') }}</div>
        <p>{{ latestRejectionComment.text }}</p>
      </div>
      <div v-if="latestApprovalComment" class="po-feedback po-feedback--ok">
        <div class="po-feedback__h">✓ {{ $t('agileTraining.poPath.play.approvalTitle') }}</div>
        <p>{{ latestApprovalComment.text }}</p>
      </div>

      <!-- Canvas-style fields grid -->
      <div class="po-canvas-form" :class="['po-canvas-form--' + activeStage]">
        <div
          v-for="key in stageKeys"
          :key="'f_' + key"
          class="po-cell"
          :class="cellClass(key)"
          :style="cellStyle(key)"
        >
          <div class="po-cell__head">
            <label class="po-cell__label">{{ stageContent.fields[key]?.label || key }}</label>
            <span class="po-cell__num">{{ fieldNumber(key) }}</span>
          </div>
          <div class="po-cell__hint" v-if="stageContent.fields[key]?.hint">{{ stageContent.fields[key].hint }}</div>
          <textarea
            :value="stageData[key] || ''"
            @input="onFieldInput(key, $event.target.value)"
            :placeholder="stageContent.fields[key]?.placeholder || ''"
            :disabled="isStageLocked"
            rows="3"
          ></textarea>
          <div class="po-cell__actions">
            <button class="po-link-btn" :disabled="isStageLocked || aiBusy || !participantToken" @click="aiImproveField(key)">✨ {{ $t('agileTraining.poPath.play.aiImprove') }}</button>
            <button class="po-link-btn" :disabled="isStageLocked || aiBusy || !participantToken" @click="aiQuestionsField(key)">❓ {{ $t('agileTraining.poPath.play.aiQuestions') }}</button>
          </div>
        </div>
      </div>

      <!-- Stage-specific: Market Fit AI uncomfortable -->
      <section v-if="activeStage === 'fit'" class="po-uncomfortable">
        <div class="po-uncomfortable__head">
          <h3>🔥 {{ $t('agileTraining.poPath.play.uncomfortableTitle') }}</h3>
          <button class="po-btn-ghost" :disabled="aiBusy || isStageLocked || aiCallsRemaining <= 0 || !participantToken" @click="generateUncomfortable">
            {{ uncomfortableQuestions.length ? $t('agileTraining.poPath.play.regenerate') : $t('agileTraining.poPath.play.generate') }}
          </button>
        </div>
        <p class="po-uncomfortable__intro">{{ stageContent.ai_questions_intro }}</p>
        <ul v-if="uncomfortableQuestions.length" class="po-uncomfortable__list">
          <li v-for="q in uncomfortableQuestions" :key="q.id">
            <div class="po-uncomfortable__q">❓ {{ q.q }}</div>
            <textarea
              :value="q.answer || ''"
              @input="onQuestionAnswer(q.id, $event.target.value)"
              :disabled="isStageLocked"
              :placeholder="$t('agileTraining.poPath.play.uncomfortablePlaceholder')"
              rows="2"
            ></textarea>
          </li>
        </ul>
        <p v-else class="po-uncomfortable__empty">{{ $t('agileTraining.poPath.play.uncomfortableEmpty') }}</p>
      </section>

      <!-- Confidence -->
      <div class="po-confidence">
        <span class="po-confidence__label">{{ $t('agileTraining.poPath.play.confidence') }}</span>
        <div class="po-confidence__row">
          <button v-for="n in [0,1,2,3,4,5]" :key="'cf_' + n" class="po-conf-dot" :class="{ 'po-conf-dot--on': confidence === n }" :disabled="isStageLocked" @click="setConfidence(n)">{{ n }}</button>
        </div>
      </div>

      <!-- AI Reply -->
      <section v-if="aiReply" class="po-ai-reply">
        <div class="po-ai-reply__h">🤖 AI</div>
        <div class="po-ai-reply__body" v-html="renderMarkdown(aiReply)"></div>
        <div class="po-ai-reply__meta">{{ $t('agileTraining.poPath.play.aiCallsLeft', { n: aiCallsRemaining }) }}</div>
      </section>

      <!-- Actions -->
      <footer class="po-stage__foot">
        <div class="po-stage__foot-meta">
          <span v-if="lastSaveAt" class="po-stage__autosave">💾 {{ $t('agileTraining.poPath.play.autosaveAt', { at: lastSaveLabel }) }}</span>
        </div>
        <div class="po-stage__foot-actions">
          <button v-if="canReturnHere" class="po-btn-ghost" @click="returnHere">↩ {{ $t('agileTraining.poPath.play.returnAndEdit') }}</button>
          <button class="po-btn-primary" :disabled="!canSubmit || syncing" @click="submitStage">
            <span v-if="activeStage === 'canvas'">🏁 {{ $t('agileTraining.poPath.play.finishStage') }}</span>
            <span v-else>➡ {{ $t('agileTraining.poPath.play.nextStage') }}</span>
          </button>
        </div>
      </footer>
    </section>

    <!-- Final summary screen -->
    <section v-else class="po-card po-final">
      <header class="po-final__head">
        <h2>⭐ {{ content.summary.title }}</h2>
        <p>{{ content.summary.subtitle }}</p>
      </header>

      <div class="po-final__compact">
        <div class="po-final__block">
          <h3>1 · JTBD</h3>
          <ul><li v-for="kv in summaryStage('jtbd')" :key="'sj_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li></ul>
        </div>
        <div class="po-final__block">
          <h3>2 · Value Proposition</h3>
          <ul><li v-for="kv in summaryStage('value')" :key="'sv_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li></ul>
        </div>
        <div class="po-final__block">
          <h3>3 · Market Fit</h3>
          <ul><li v-for="kv in summaryStage('fit')" :key="'sf_' + kv.k"><b>{{ kv.label }}:</b> {{ kv.value }}</li></ul>
          <ol v-if="(getStageData('fit').ai_questions || []).length" class="po-final__qa">
            <li v-for="q in getStageData('fit').ai_questions" :key="'sfq_' + q.id">
              <div>❓ {{ q.q }}</div>
              <div v-if="q.answer">↳ {{ q.answer }}</div>
            </li>
          </ol>
        </div>
      </div>

      <div class="po-canvas">
        <h3>4 · Lean Canvas</h3>
        <div class="po-canvas__grid">
          <div class="po-canvas__cell po-canvas__cell--problem"><div class="po-canvas__h">1 · {{ canvasFieldLabel('problem') }}</div><pre>{{ getCanvasField('problem') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--solution"><div class="po-canvas__h">4 · {{ canvasFieldLabel('solution') }}</div><pre>{{ getCanvasField('solution') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--uvp"><div class="po-canvas__h">3 · {{ canvasFieldLabel('value_prop') }}</div><pre>{{ getCanvasField('value_prop') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--unfair"><div class="po-canvas__h">9 · {{ canvasFieldLabel('unfair_advantage') }}</div><pre>{{ getCanvasField('unfair_advantage') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--segments"><div class="po-canvas__h">2 · {{ canvasFieldLabel('segments') }}</div><pre>{{ getCanvasField('segments') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--metrics"><div class="po-canvas__h">8 · {{ canvasFieldLabel('metrics') }}</div><pre>{{ getCanvasField('metrics') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--channels"><div class="po-canvas__h">5 · {{ canvasFieldLabel('channels') }}</div><pre>{{ getCanvasField('channels') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--ea"><div class="po-canvas__h">{{ canvasFieldLabel('early_adopters') }}</div><pre>{{ getCanvasField('early_adopters') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--costs"><div class="po-canvas__h">7 · {{ canvasFieldLabel('costs') }}</div><pre>{{ getCanvasField('costs') }}</pre></div>
          <div class="po-canvas__cell po-canvas__cell--revenue"><div class="po-canvas__h">6 · {{ canvasFieldLabel('revenue') }}</div><pre>{{ getCanvasField('revenue') }}</pre></div>
        </div>
      </div>

      <footer class="po-final__foot">
        <button class="po-btn-ghost" @click="onPrint">🖨 {{ $t('agileTraining.poPath.play.print') }}</button>
        <button class="po-btn-ghost" @click="copySummary">📋 {{ $t('agileTraining.poPath.play.copyText') }}</button>
        <button class="po-btn-ghost" @click="activeStage = 'canvas'">↩ {{ $t('agileTraining.poPath.play.editCanvas') }}</button>
      </footer>
    </section>
  </div>
</template>

<script>
import axios from 'axios';

const STAGES = ['jtbd', 'value', 'fit', 'canvas'];

export default {
  name: 'AgilePoPathPlay',
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      loading: true,
      errorText: '',
      stages: STAGES,
      content: { stages: {}, summary: { title: '', subtitle: '' }, idea_examples: [], tips: [], status_labels: {} },
      contentLocale: 'ru',
      stageFields: {},
      stageLayout: {},
      aiCallsLimit: 30,
      // session/group
      groupName: '',
      // local UI
      activeStage: 'jtbd',
      displayNameInput: '',
      hasName: false,
      // server-mirrored answer
      answer: null,
      // autosave
      saveTimer: null,
      syncing: false,
      lastSaveAt: null,
      lastSaveError: false,
      // AI
      aiBusy: false,
      aiReply: '',
    };
  },
  computed: {
    participantToken() { return this.tokenFromStorage(); },
    storageKey() { return 'po_path:' + this.slug; },
    cacheKey() { return 'po_path_cache:' + this.slug; },
    stageContent() { return this.content.stages?.[this.activeStage] || {}; },
    stageKeys() { return this.stageFields[this.activeStage] || []; },
    stageIdx() { return STAGES.indexOf(this.activeStage); },
    stageData() { return this.getStageData(this.activeStage).data || {}; },
    confidence() { return this.getStageData(this.activeStage).confidence; },
    currentStageStatus() { return this.getStageData(this.activeStage).status || 'draft'; },
    aiCallsRemaining() { return this.answer?.ai_calls_remaining ?? this.aiCallsLimit; },
    serverCurrentStage() { return this.answer?.current_stage || 'jtbd'; },
    stagesCompleted() { return this.answer?.stages_completed ?? 0; },
    isStageLocked() {
      const cur = this.serverCurrentStage;
      if (cur === 'done') return false;
      const curIdx = STAGES.indexOf(cur);
      const myIdx = STAGES.indexOf(this.activeStage);
      if (myIdx > curIdx) return true;
      const status = this.currentStageStatus;
      return status === 'submitted' || status === 'in_review' || status === 'approved';
    },
    allApproved() {
      if (!this.answer) return false;
      return STAGES.every(s => this.answer.stages?.[s]?.status === 'approved');
    },
    canSubmit() {
      if (this.isStageLocked) return false;
      if (this.serverCurrentStage !== this.activeStage) return false;
      if (this.activeStage !== this.serverCurrentStage) return false;
      const hasContent = (this.stageKeys || []).some(k => (this.stageData[k] || '').trim());
      return hasContent;
    },
    canReturnHere() {
      if (!this.answer) return false;
      const cur = this.serverCurrentStage;
      if (cur === 'done') return this.activeStage !== 'canvas' || this.currentStageStatus !== 'approved' ? this.currentStageStatus === 'approved' : true;
      const curIdx = STAGES.indexOf(cur);
      const myIdx = STAGES.indexOf(this.activeStage);
      return myIdx < curIdx; // прошлый одобренный этап — можно вернуть
    },
    uncomfortableQuestions() {
      return (this.getStageData('fit').ai_questions || []);
    },
    jtbdSummary() { return this.summaryStage('jtbd'); },
    valueSummary() { return this.summaryStage('value'); },
    canPrefillCanvas() {
      const c = this.getStageData('canvas').data || {};
      return !c.problem && !c.value_prop;
    },
    latestRejectionComment() {
      const list = this.getStageData(this.activeStage).comments || [];
      for (let i = list.length - 1; i >= 0; i--) {
        if (list[i].verdict === 'needs_revision') return list[i];
      }
      return null;
    },
    latestApprovalComment() {
      if (this.currentStageStatus !== 'approved') return null;
      const list = this.getStageData(this.activeStage).comments || [];
      for (let i = list.length - 1; i >= 0; i--) {
        if (list[i].verdict === 'approved') return list[i];
      }
      return null;
    },
    lastSaveLabel() {
      if (!this.lastSaveAt) return '';
      try { return new Date(this.lastSaveAt).toLocaleTimeString(this.$i18n.locale === 'en' ? 'en-GB' : 'ru-RU'); } catch (_) { return ''; }
    },
  },
  async mounted() {
    this.restoreLocalCache();
    await this.loadState();
  },
  beforeUnmount() {
    if (this.saveTimer) clearTimeout(this.saveTimer);
  },
  methods: {
    tokenFromStorage() {
      try { return localStorage.getItem(this.storageKey) || ''; } catch (_) { return ''; }
    },
    saveTokenToStorage(token) {
      try { localStorage.setItem(this.storageKey, token); } catch (_) { /* noop */ }
    },
    restoreLocalCache() {
      try {
        const raw = localStorage.getItem(this.cacheKey);
        if (!raw) return;
        const parsed = JSON.parse(raw);
        if (parsed && typeof parsed === 'object') {
          this._localCache = parsed; // merge later when answer arrives
        }
      } catch (_) { /* noop */ }
    },
    persistLocalCache() {
      if (!this.answer) return;
      try {
        const slim = { stages: {} };
        for (const s of STAGES) {
          slim.stages[s] = {
            data: this.answer.stages[s]?.data || {},
            confidence: this.answer.stages[s]?.confidence ?? null,
          };
          if (s === 'fit') {
            slim.stages[s].ai_questions = this.answer.stages[s]?.ai_questions || [];
          }
        }
        localStorage.setItem(this.cacheKey, JSON.stringify(slim));
      } catch (_) { /* noop */ }
    },
    statusEmoji(s) {
      switch (s) {
        case 'draft': return '🟡';
        case 'submitted':
        case 'in_review': return '🔵';
        case 'needs_revision': return '🔴';
        case 'approved': return '🟢';
        default: return '⚪';
      }
    },
    statusLabel(s) {
      const map = this.content?.status_labels || {};
      return map[s] || this.$t('agileTraining.poPath.status.' + s) || s;
    },
    stageShort(s) { return this.$t('agileTraining.poPath.stages.' + s + '.short') || s; },
    canvasFieldLabel(key) { return this.content.stages?.canvas?.fields?.[key]?.label || key; },
    cellStyle(key) {
      const layout = (this.stageLayout?.[this.activeStage] || {})[key];
      if (!layout) return {};
      return {
        gridColumn: `${layout.col} / span ${layout.colspan || 1}`,
        gridRow: `${layout.row} / span ${layout.rowspan || 1}`,
      };
    },
    cellClass(key) {
      const layout = (this.stageLayout?.[this.activeStage] || {})[key];
      const cls = [];
      if (layout?.accent) cls.push('po-cell--' + layout.accent);
      if ((this.stageData[key] || '').trim()) cls.push('po-cell--filled');
      return cls;
    },
    fieldNumber(key) {
      const fields = this.stageFields[this.activeStage] || [];
      const idx = fields.indexOf(key);
      return idx < 0 ? '' : String(idx + 1);
    },
    onPrint() {
      try { window.print(); } catch (_) { /* noop */ }
    },
    stageStatus(s) { return (this.answer?.stages?.[s]?.status) || 'draft'; },
    getStageData(s) { return this.answer?.stages?.[s] || { status: 'draft', data: {}, comments: [] }; },
    getCanvasField(key) { return (this.getStageData('canvas').data || {})[key] || ''; },
    canSelectStage(stage, idx) {
      const cur = this.serverCurrentStage;
      if (cur === 'done') return true;
      const curIdx = STAGES.indexOf(cur);
      return idx <= curIdx; // ранее одобренные открыты для просмотра
    },
    stepClass(stage, idx) {
      const cls = [];
      if (this.activeStage === stage) cls.push('po-step--active');
      const status = this.stageStatus(stage);
      cls.push('po-step--' + status);
      if (!this.canSelectStage(stage, idx)) cls.push('po-step--locked');
      return cls;
    },
    goStage(stage) {
      const idx = STAGES.indexOf(stage);
      if (this.canSelectStage(stage, idx)) {
        this.activeStage = stage;
        this.aiReply = '';
      }
    },

    // ---------- API ----------
    async loadState() {
      this.loading = true;
      try {
        const res = await axios.get(`/api/agile-training/po-path/g/${this.slug}/state`, {
          params: this.participantToken ? { participant_token: this.participantToken, locale: this.$i18n.locale } : { locale: this.$i18n.locale },
        });
        this.content = res.data.content || this.content;
        this.contentLocale = res.data.effective_locale || 'ru';
        this.stageFields = res.data.stage_fields || {};
        this.stageLayout = res.data.stage_layout || {};
        this.aiCallsLimit = res.data.ai_calls_limit || this.aiCallsLimit;
        this.groupName = res.data.group?.name || '';
        const tokenProvided = res.data.token_provided ?? !!this.participantToken;
        const participantKnown = res.data.participant_known ?? !!res.data.answer;
        if (res.data.answer) {
          this.answer = res.data.answer;
          this.hasName = true;
          this.activeStage = this.answer.current_stage === 'done' ? 'canvas' : this.answer.current_stage;
          this.mergeLocalCacheIfPresent();
        } else if (tokenProvided && !participantKnown) {
          try { localStorage.removeItem(this.storageKey); } catch (_) { /* noop */ }
          this.hasName = false;
        } else if (!this.participantToken) {
          this.hasName = false;
        }
      } catch (e) {
        this.errorText = (e.response?.data?.error) || e.message || 'Error';
      } finally {
        this.loading = false;
      }
    },
    mergeLocalCacheIfPresent() {
      const cache = this._localCache;
      if (!cache || !cache.stages || !this.answer) return;
      // Поверх серверного ответа: добавляем поля, которых не было — клиент мог
      // ещё не успеть отправить последний autosave. Только для not-locked этапов.
      let dirty = false;
      for (const s of STAGES) {
        const status = this.answer.stages[s]?.status || 'draft';
        if (status !== 'draft' && status !== 'needs_revision') continue;
        const cached = cache.stages?.[s]?.data || {};
        const server = this.answer.stages[s].data || {};
        for (const k of Object.keys(cached)) {
          if (!server[k] && cached[k]) {
            server[k] = cached[k];
            dirty = true;
          }
        }
        this.answer.stages[s].data = server;
      }
      if (dirty) this.scheduleAutosave(0);
    },
    async startSession() {
      const name = (this.displayNameInput || '').trim();
      if (!name) return;
      try {
        const body = { display_name: name };
        const existing = this.participantToken;
        if (existing) body.participant_token = existing;
        const res = await axios.post(`/api/agile-training/g/${this.slug}/participant`, body);
        this.saveTokenToStorage(res.data.participant_token);
        this.hasName = true;
        await this.loadState();
      } catch (e) {
        alert((e.response?.data?.error) || e.message);
      }
    },
    onFieldInput(key, value) {
      if (!this.answer) return;
      const stage = this.answer.stages[this.activeStage] || (this.answer.stages[this.activeStage] = { status: 'draft', data: {}, comments: [] });
      stage.data = { ...(stage.data || {}), [key]: value };
      this.persistLocalCache();
      this.scheduleAutosave();
    },
    setConfidence(n) {
      if (!this.answer) return;
      const stage = this.answer.stages[this.activeStage];
      if (!stage) return;
      stage.confidence = n;
      this.persistLocalCache();
      this.scheduleAutosave(200);
    },
    onQuestionAnswer(qId, value) {
      if (!this.answer) return;
      const fit = this.answer.stages.fit;
      if (!fit) return;
      const list = fit.ai_questions || [];
      const q = list.find(x => x.id === qId);
      if (!q) return;
      q.answer = value;
      this.persistLocalCache();
      // ответ сохраняется отдельной ручкой — debounce
      if (this._qaTimer) clearTimeout(this._qaTimer);
      this._qaTimer = setTimeout(() => this.saveQuestionAnswer(qId, value), 600);
    },
    async saveQuestionAnswer(qId, value) {
      try {
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/fit/answer-question`, {
          participant_token: this.participantToken,
          q_id: qId,
          answer: value,
        });
        this.answer = res.data.answer;
      } catch (_) { /* ignore */ }
    },
    scheduleAutosave(delay = 800) {
      if (this.saveTimer) clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(() => this.flushAutosave(), delay);
    },
    async flushAutosave() {
      if (!this.answer || !this.participantToken) return;
      this.syncing = true;
      this.lastSaveError = false;
      try {
        const stage = this.activeStage;
        const data = { ...(this.answer.stages[stage]?.data || {}) };
        const conf = this.answer.stages[stage]?.confidence;
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/answer`, {
          participant_token: this.participantToken,
          stage,
          data,
          confidence: conf,
        });
        this.answer = res.data.answer;
        this.lastSaveAt = new Date().toISOString();
      } catch (e) {
        this.lastSaveError = true;
      } finally {
        this.syncing = false;
      }
    },
    async submitStage() {
      if (!this.participantToken) { this.handleLostParticipant(); return; }
      await this.flushAutosave();
      try {
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/submit`, {
          participant_token: this.participantToken,
          stage: this.activeStage,
        });
        this.answer = res.data.answer;
        this.aiReply = '';
        const next = res.data.next_stage;
        if (next && next !== 'done' && STAGES.includes(next)) {
          this.activeStage = next;
          this.scrollTop();
        } else if (next === 'done' || this.allApproved) {
          this.activeStage = 'done';
          this.scrollTop();
        }
      } catch (e) {
        const status = e.response?.status;
        const err = e.response?.data?.error;
        if (err === 'stage_empty') {
          alert(this.$t('agileTraining.poPath.play.errStageEmpty'));
        } else if (status === 404 || err === 'Participant not found') {
          this.handleLostParticipant();
        } else {
          alert(err || e.message);
        }
      }
    },
    scrollTop() {
      try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) { /* noop */ }
    },
    handleLostParticipant() {
      try { localStorage.removeItem(this.storageKey); } catch (_) { /* noop */ }
      this.answer = null;
      this.hasName = false;
      alert(this.$t('agileTraining.poPath.play.sessionLost'));
    },
    async returnHere() {
      if (!window.confirm(this.$t('agileTraining.poPath.play.returnConfirm'))) return;
      try {
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/return`, {
          participant_token: this.participantToken,
          stage: this.activeStage,
        });
        this.answer = res.data.answer;
      } catch (e) {
        alert((e.response?.data?.error) || e.message);
      }
    },
    summaryStage(s) {
      const data = this.getStageData(s).data || {};
      const fields = this.stageFields[s] || [];
      const out = [];
      for (const k of fields) {
        const value = (data[k] || '').trim();
        if (!value) continue;
        out.push({ k, label: this.content.stages?.[s]?.fields?.[k]?.label || k, value });
      }
      return out;
    },
    prefillCanvas() {
      if (!this.answer) return;
      const canvas = this.answer.stages.canvas;
      if (!canvas) return;
      const data = { ...(canvas.data || {}) };
      const jtbd = this.getStageData('jtbd').data || {};
      const value = this.getStageData('value').data || {};
      if (!data.problem) {
        const parts = [jtbd.barriers, jtbd.fears, value.pains].filter(Boolean);
        if (parts.length) data.problem = parts.join('\n').slice(0, 1500);
      }
      if (!data.value_prop) {
        if (value.product) data.value_prop = value.product;
      }
      if (!data.solution && value.pain_relievers) data.solution = value.pain_relievers;
      canvas.data = data;
      this.scheduleAutosave(0);
    },
    // ---------- AI ----------
    async aiAssistGeneric(mode, userInput) {
      if (this.aiBusy) return;
      if (!this.participantToken) { this.handleLostParticipant(); return; }
      this.aiBusy = true;
      try {
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/ai-assist`, {
          participant_token: this.participantToken,
          mode,
          stage: this.activeStage,
          user_input: userInput || '',
          locale: this.$i18n.locale,
        });
        this.aiReply = res.data.reply || '';
        if (this.answer) this.answer.ai_calls_remaining = res.data.ai_calls_remaining;
      } catch (e) {
        const status = e.response?.status;
        const err = e.response?.data?.error;
        if (err === 'ai_limit_exceeded') {
          alert(this.$t('agileTraining.poPath.play.aiLimit'));
        } else if (status === 404 || err === 'Participant not found' || err === 'participant_token required') {
          this.handleLostParticipant();
        } else {
          alert(err || e.message || this.$t('agileTraining.poPath.play.aiError'));
        }
      } finally {
        this.aiBusy = false;
      }
    },
    aiImproveField(key) {
      const text = (this.stageData[key] || '').trim();
      if (!text) { alert(this.$t('agileTraining.poPath.play.aiNeedText')); return; }
      this.aiAssistGeneric('improve', text);
    },
    aiQuestionsField(key) {
      const text = (this.stageData[key] || '').trim();
      if (!text) { alert(this.$t('agileTraining.poPath.play.aiNeedText')); return; }
      this.aiAssistGeneric('questions', text);
    },
    async generateUncomfortable() {
      if (this.aiBusy) return;
      if (!this.participantToken) { this.handleLostParticipant(); return; }
      this.aiBusy = true;
      try {
        const res = await axios.post(`/api/agile-training/po-path/g/${this.slug}/ai-uncomfortable`, {
          participant_token: this.participantToken,
          locale: this.$i18n.locale,
        });
        if (!this.answer) this.answer = { stages: { fit: {} } };
        if (!this.answer.stages.fit) this.answer.stages.fit = { status: 'draft', data: {}, comments: [] };
        this.answer.stages.fit.ai_questions = res.data.questions;
        this.answer.ai_calls_remaining = res.data.ai_calls_remaining;
        this.persistLocalCache();
      } catch (e) {
        const status = e.response?.status;
        const err = e.response?.data?.error;
        if (err === 'ai_limit_exceeded') alert(this.$t('agileTraining.poPath.play.aiLimit'));
        else if (status === 404 || err === 'Participant not found') this.handleLostParticipant();
        else alert(err || e.message);
      } finally {
        this.aiBusy = false;
      }
    },
    renderMarkdown(md) {
      if (!md) return '';
      const escape = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      let html = escape(String(md));
      html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/(^|\n)- (.+)(?=\n|$)/g, '$1<li>$2</li>');
      html = html.replace(/(<li>[\s\S]+?<\/li>)/g, '<ul>$1</ul>');
      html = html.replace(/\n{2,}/g, '</p><p>');
      html = html.replace(/\n/g, '<br>');
      return '<p>' + html + '</p>';
    },
    copySummary() {
      const lines = [];
      lines.push('=== ' + this.content.title + ' ===');
      for (const s of STAGES) {
        const items = this.summaryStage(s);
        if (!items.length) continue;
        lines.push('');
        lines.push('--- ' + (this.content.stages?.[s]?.title || s) + ' ---');
        for (const it of items) lines.push(it.label + ': ' + it.value);
      }
      try {
        navigator.clipboard.writeText(lines.join('\n'));
        alert(this.$t('agileTraining.poPath.play.copied'));
      } catch (_) { /* ignore */ }
    },
  },
};
</script>

<style scoped>
.po-play { max-width: 1100px; margin: 18px auto 60px; padding: 0 16px; color: #0f172a; font-family: inherit; }
.po-play__spinner { width: 36px; height: 36px; border-radius: 50%; border: 3px solid #eee; border-top-color: #7c3aed; animation: po-spin 1s linear infinite; margin: 60px auto 12px; }
@keyframes po-spin { to { transform: rotate(360deg); } }
.po-play--error { color: #b91c1c; text-align: center; padding-top: 60px; }

.po-play__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.po-play__head h1 { margin: 0; font-size: 24px; }
.po-play__subtitle { color: #64748b; margin: 4px 0 0; }
.po-play__meta { text-align: right; font-size: 13px; }
.po-play__group { font-weight: 700; }
.po-play__progress { color: #64748b; }
.po-play__sync { display: inline-block; margin-top: 4px; padding: 2px 10px; border-radius: 999px; background: #dcfce7; color: #166534; font-size: 12px; }
.po-play__sync--saving { background: #dbeafe; color: #1d4ed8; }
.po-play__sync--err { background: #fee2e2; color: #b91c1c; }

.po-stepper { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 16px; }
.po-step { display: flex; gap: 8px; align-items: center; background: #fff; border: 1px solid #e5e7eb; padding: 9px 14px; border-radius: 999px; font-weight: 600; font-size: 13px; cursor: pointer; color: #0f172a; line-height: 1.2; box-shadow: none; }
.po-step:disabled { opacity: 0.5; cursor: not-allowed; }
.po-step--active { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; border-color: transparent; }
.po-step--approved { border-color: #16a34a; color: #166534; }
.po-step--needs_revision { border-color: #dc2626; color: #b91c1c; }
.po-step--submitted, .po-step--in_review { border-color: #1d4ed8; color: #1d4ed8; }
.po-step--locked { background: #f1f5f9; color: #94a3b8; }
.po-step__num { background: rgba(0,0,0,0.07); padding: 2px 8px; border-radius: 999px; }
.po-step--active .po-step__num { background: rgba(255,255,255,0.25); }
.po-step--final { border-style: dashed; }

.po-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 16px; padding: 20px 22px; margin-bottom: 14px; }

.po-welcome h2 { margin: 0 0 8px; }
.po-welcome__tips { padding-left: 18px; color: #475569; }
.po-welcome__lead { margin-top: 14px; font-weight: 600; }
.po-welcome__row { display: flex; gap: 8px; margin-top: 8px; flex-wrap: wrap; }
.po-welcome__row input { flex: 1; min-width: 220px; padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-family: inherit; font-size: 15px; box-sizing: border-box; }
.po-welcome__row input:focus { outline: none; border-color: #8b5cf6; box-shadow: 0 0 0 3px rgba(139,92,246,0.15); }
.po-welcome__examples { margin-top: 18px; }
.po-welcome__examples-h { font-weight: 700; color: #475569; margin-bottom: 6px; }
.po-welcome__examples ul { list-style: '— '; padding-left: 16px; color: #475569; }

.po-stage__head { display: flex; gap: 12px; align-items: flex-start; justify-content: space-between; }
.po-stage__kicker { font-size: 12px; color: #7c3aed; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px; }
.po-stage__head h2 { margin: 0; }
.po-stage__context { color: #64748b; margin-top: 4px; }
.po-status { padding: 4px 12px; border-radius: 999px; background: #f1f5f9; color: #334155; font-size: 13px; font-weight: 600; white-space: nowrap; }
.po-status--approved { background: #dcfce7; color: #166534; }
.po-status--needs_revision { background: #fee2e2; color: #b91c1c; }
.po-status--submitted, .po-status--in_review { background: #dbeafe; color: #1d4ed8; }
.po-stage__explainer { background: #faf5ff; border-left: 3px solid #c4b5fd; padding: 10px 12px; border-radius: 8px; color: #4c1d95; }

.po-ref { background: #f8fafc; border: 1px dashed #cbd5e1; padding: 10px 12px; border-radius: 10px; margin-top: 10px; }
.po-ref__h { font-weight: 700; color: #475569; margin-bottom: 4px; }
.po-ref ul { padding-left: 18px; margin: 0; color: #334155; font-size: 14px; }
.po-link-btn { background: transparent; border: none; color: #7c3aed; font-weight: 600; cursor: pointer; padding: 0; }
.po-link-btn:disabled { color: #94a3b8; cursor: not-allowed; }

.po-feedback { margin-top: 12px; padding: 10px 12px; border-radius: 10px; background: #fef2f2; border-left: 3px solid #dc2626; }
.po-feedback--ok { background: #ecfdf5; border-left-color: #10b981; }
.po-feedback__h { font-weight: 700; color: #b91c1c; margin-bottom: 4px; }
.po-feedback--ok .po-feedback__h { color: #047857; }

.po-canvas-form {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  margin-top: 14px;
  background: linear-gradient(135deg, #f1f5f9 0%, #faf5ff 100%);
  padding: 8px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
}
.po-cell {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 10px 11px;
  display: flex;
  flex-direction: column;
  min-height: 130px;
  min-width: 0;
  position: relative;
  box-sizing: border-box;
  transition: border-color 0.18s, box-shadow 0.18s;
  overflow: hidden;
}
.po-cell--filled { border-color: #c4b5fd; box-shadow: 0 1px 4px rgba(124,58,237,0.07); }
.po-cell--primary { background: #faf5ff; border-color: #c4b5fd; }
.po-cell--ok { background: #f0fdf4; border-color: #bbf7d0; }
.po-cell--warm { background: #fffbeb; border-color: #fde68a; }
.po-cell--danger { background: #fef2f2; border-color: #fecaca; }
.po-cell__head { display: flex; align-items: baseline; justify-content: space-between; gap: 6px; }
.po-cell__label { font-weight: 700; font-size: 13.5px; color: #0f172a; line-height: 1.3; }
.po-cell__num { font-size: 11px; font-weight: 700; color: #94a3b8; background: rgba(15,23,42,0.04); border-radius: 999px; padding: 1px 7px; }
.po-cell__hint { color: #64748b; font-size: 12px; margin: 4px 0 6px; line-height: 1.4; }
.po-cell textarea {
  flex: 1;
  width: 100%;
  max-width: 100%;
  padding: 8px 10px;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  font-family: inherit;
  font-size: 13.5px;
  resize: vertical;
  line-height: 1.45;
  background: #fff;
  min-height: 70px;
  box-sizing: border-box;
  display: block;
}
.po-cell textarea:focus { outline: none; border-color: #8b5cf6; box-shadow: 0 0 0 3px rgba(139,92,246,0.15); }
.po-cell textarea:disabled { background: #f1f5f9; color: #475569; }
.po-cell__actions { display: flex; gap: 10px; margin-top: 6px; font-size: 12px; flex-wrap: wrap; }
@media (max-width: 900px) {
  .po-canvas-form { grid-template-columns: 1fr 1fr; }
  .po-cell { grid-column: auto !important; grid-row: auto !important; }
}
@media (max-width: 540px) {
  .po-canvas-form { grid-template-columns: 1fr; }
}

.po-uncomfortable { margin-top: 16px; padding: 14px 16px; border: 1px solid #fbbf24; background: #fffbeb; border-radius: 12px; }
.po-uncomfortable__head { display: flex; justify-content: space-between; align-items: center; gap: 10px; }
.po-uncomfortable__head h3 { margin: 0; }
.po-uncomfortable__intro { color: #92400e; }
.po-uncomfortable__list { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 10px; }
.po-uncomfortable__q { font-weight: 600; }
.po-uncomfortable__list textarea { width: 100%; max-width: 100%; box-sizing: border-box; padding: 7px 10px; border: 1px solid #fcd34d; border-radius: 8px; font-family: inherit; font-size: 14px; resize: vertical; background: #fff; margin-top: 4px; display: block; }
.po-uncomfortable__empty { color: #92400e; }

.po-confidence { display: flex; align-items: center; gap: 10px; margin: 14px 0 4px; }
.po-confidence__label { font-size: 13px; color: #475569; font-weight: 600; }
.po-confidence__row { display: flex; gap: 4px; }
.po-conf-dot { width: 30px; height: 30px; border-radius: 50%; border: 1px solid #cbd5e1; background: #fff; cursor: pointer; font-weight: 700; }
.po-conf-dot--on { background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; border-color: transparent; }
.po-conf-dot:disabled { opacity: 0.5; cursor: not-allowed; }

.po-ai-reply { margin-top: 14px; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 12px; padding: 12px 14px; }
.po-ai-reply__h { font-weight: 700; color: #1d4ed8; margin-bottom: 6px; }
.po-ai-reply__body { color: #1e3a8a; line-height: 1.5; }
.po-ai-reply__meta { color: #64748b; margin-top: 8px; font-size: 12px; }

.po-stage__foot { display: flex; justify-content: space-between; align-items: center; margin-top: 18px; gap: 10px; flex-wrap: wrap; }
.po-stage__autosave { color: #64748b; font-size: 12px; }
.po-stage__foot-actions { display: flex; gap: 8px; }

.po-btn-primary { padding: 10px 20px; border: none; border-radius: 10px; background: linear-gradient(135deg, #8b5cf6, #6d28d9); color: #fff; font-weight: 700; cursor: pointer; font-size: 15px; line-height: 1.2; }
.po-btn-primary:disabled { opacity: 0.4; cursor: not-allowed; }
.po-btn-primary:hover:not(:disabled) { box-shadow: 0 6px 18px rgba(124,58,237,0.25); }
.po-btn-ghost { background: #fff; border: 1px solid #cbd5e1; color: #475569; padding: 8px 14px; border-radius: 10px; font-weight: 600; cursor: pointer; font-size: 13px; line-height: 1.2; }
.po-btn-ghost:hover:not(:disabled) { border-color: #7c3aed; color: #7c3aed; }
.po-btn-ghost:disabled { opacity: 0.5; cursor: not-allowed; }

.po-final__head h2 { margin: 0; }
.po-final__compact { display: grid; gap: 14px; margin-top: 14px; }
.po-final__block { background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 12px; padding: 12px 14px; }
.po-final__block h3 { margin: 0 0 6px; }
.po-final__block ul { padding-left: 18px; margin: 0; }
.po-final__qa { padding-left: 18px; margin: 8px 0 0; color: #475569; }

.po-canvas { margin-top: 18px; }
.po-canvas h3 { margin: 0 0 10px; }
.po-canvas__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  grid-template-rows: 1fr 1fr 1fr;
  gap: 6px;
  background: #cbd5e1;
  padding: 6px;
  border-radius: 12px;
  min-height: 360px;
}
.po-canvas__cell { background: #fff; padding: 8px 10px; border-radius: 8px; overflow: hidden; }
.po-canvas__h { font-size: 11px; font-weight: 700; color: #475569; text-transform: uppercase; letter-spacing: 0.4px; margin-bottom: 4px; }
.po-canvas__cell pre { margin: 0; font: inherit; white-space: pre-wrap; font-size: 12px; line-height: 1.4; color: #0f172a; }
.po-canvas__cell--problem { grid-column: 1; grid-row: 1 / span 2; }
.po-canvas__cell--solution { grid-column: 2; grid-row: 1; }
.po-canvas__cell--metrics { grid-column: 2; grid-row: 2; }
.po-canvas__cell--uvp { grid-column: 3; grid-row: 1 / span 2; background: #faf5ff; }
.po-canvas__cell--unfair { grid-column: 4; grid-row: 1; }
.po-canvas__cell--channels { grid-column: 4; grid-row: 2; }
.po-canvas__cell--segments { grid-column: 5; grid-row: 1 / span 2; background: #ecfdf5; }
.po-canvas__cell--ea { grid-column: 5; grid-row: 1 / span 2; align-self: end; background: transparent; padding-top: 70%; }
.po-canvas__cell--costs { grid-column: 1 / span 2; grid-row: 3; }
.po-canvas__cell--revenue { grid-column: 3 / span 3; grid-row: 3; }

@media (max-width: 800px) {
  .po-canvas__grid { grid-template-columns: 1fr 1fr; grid-template-rows: auto; min-height: 0; }
  .po-canvas__cell { grid-column: auto !important; grid-row: auto !important; padding-top: 8px !important; }
}

.po-final__foot { display: flex; gap: 8px; justify-content: flex-end; margin-top: 14px; flex-wrap: wrap; }

@media print {
  .po-stepper, .po-stage__foot, .po-final__foot, .po-play__sync, .po-play__meta, .po-link-btn { display: none !important; }
  .po-card { border: none; box-shadow: none; }
  .po-canvas__grid { background: transparent; padding: 0; }
}
</style>
