<template>
  <div class="prep-page">
    <div class="prep-container">
      <h1>{{ $t('backlogPrep.title') }}</h1>
      <p class="subtitle">{{ $t('backlogPrep.subtitle') }}</p>
      <p v-if="aiUsageRemaining !== null" class="ai-usage-line">
        {{ $t('backlogPrep.aiUsageLeft', { n: aiUsageRemaining }) }}
      </p>
      <p v-if="copiedFeedback" class="copy-feedback" role="status">{{ copiedFeedback }}</p>

      <section class="prep-intro" aria-labelledby="bp-intro-title">
        <h2 id="bp-intro-title" class="prep-intro__title">{{ $t('backlogPrep.introTitle') }}</h2>
        <p class="prep-intro__lead">{{ $t('backlogPrep.introLead') }}</p>
        <button type="button" class="prep-intro__toggle" @click="introExpanded = !introExpanded">
          {{ introExpanded ? $t('backlogPrep.introCollapse') : $t('backlogPrep.introExpand') }}
        </button>
        <div v-show="introExpanded" class="prep-intro__body">
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">1</span> {{ $t('backlogPrep.introStep1Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep1Body') }}</p>
          </article>
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">2</span> {{ $t('backlogPrep.introStep2Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep2Body') }}</p>
          </article>
          <article class="prep-intro__card">
            <h3><span class="prep-intro__badge">3</span> {{ $t('backlogPrep.introStep3Title') }}</h3>
            <p>{{ $t('backlogPrep.introStep3Body') }}</p>
          </article>
        </div>
      </section>

      <!-- Блок 1: декомпозиция и файл -->
      <section class="prep-block prep-block--decompose" aria-labelledby="block-decompose-title">
        <header class="prep-block__header">
          <span class="prep-block__badge" aria-hidden="true">1</span>
          <div class="prep-block__head-text">
            <h2 id="block-decompose-title" class="prep-block__title">{{ $t('backlogPrep.blockDecomposeTitle') }}</h2>
            <p class="prep-block__lead">{{ $t('backlogPrep.blockDecomposeLead') }}</p>
          </div>
        </header>
        <div class="prep-block__body spec-card spec-card--nested">
          <h3 id="spec-title" class="spec-card__subtitle">{{ $t('backlogPrep.specTitle') }}</h3>
          <p class="section-lead">{{ $t('backlogPrep.specLead') }}</p>
        <div class="spec-row">
          <label class="file-label">
            <input
              type="file"
              accept=".txt,.md,.markdown,.csv,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              class="file-input"
              @change="onSpecFile"
            />
            <span class="file-btn">{{ $t('backlogPrep.specChooseFile') }}</span>
          </label>
          <span v-if="specFileName" class="file-name">{{ specFileName }}</span>
        </div>
        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">📄</span>
            <textarea
              v-model="specPaste"
              rows="5"
              class="modern-input modern-textarea"
              :class="{ 'has-value': specPaste }"
            />
            <label class="floating-label">{{ $t('backlogPrep.specPasteLabel') }}</label>
          </div>
        </div>
        <button type="button" class="secondary-btn" :disabled="specLoading" @click="runSpecDecompose">
          {{ specLoading ? $t('backlogPrep.specLoading') : $t('backlogPrep.specRun') }}
        </button>
        <p v-if="specError" class="assist-error">{{ specError }}</p>
        <div v-if="specResult" class="spec-result">
          <h3 class="spec-result__title">{{ specResult.epic_title }}</h3>
          <p class="spec-result__body">{{ specResult.epic_description }}</p>
          <p v-if="specResult.epic_context" class="spec-result__ctx"><strong>{{ $t('backlogPrep.context') }}:</strong> {{ specResult.epic_context }}</p>
          <h4 class="spec-result__sub">{{ $t('backlogPrep.suggestedStories') }}</h4>
          <ol class="spec-stories">
            <li v-for="(s, idx) in specResult.suggested_stories" :key="idx">
              <strong>{{ s.title }}</strong> — {{ s.summary }}
              <div v-if="s.acceptance_hint" class="spec-ac-hint">{{ s.acceptance_hint }}</div>
            </li>
          </ol>
          <div class="spec-result__actions">
            <button type="button" class="primary small" @click="applySpecToForm">{{ $t('backlogPrep.applyEpicToForm') }}</button>
            <button type="button" class="primary small ghost" @click="saveSpecBundle">{{ $t('backlogPrep.saveEpicBundle') }}</button>
          </div>
        </div>
        </div>
      </section>

      <!-- Блок 2: черновик истории / эпика -->
      <section class="prep-block prep-block--compose" aria-labelledby="block-compose-title">
        <header class="prep-block__header">
          <span class="prep-block__badge" aria-hidden="true">2</span>
          <div class="prep-block__head-text">
            <h2 id="block-compose-title" class="prep-block__title">{{ $t('backlogPrep.blockComposeTitle') }}</h2>
            <p class="prep-block__lead">{{ $t('backlogPrep.blockComposeLead') }}</p>
          </div>
        </header>
        <div class="prep-block__body">
      <section class="ai-assist-card" aria-label="AI">
        <h2 class="ai-assist-card__title">✨ {{ $t('backlogPrep.assistTitle') }}</h2>
        <p class="ai-assist-card__hint">{{ $t('backlogPrep.assistHint') }}</p>
        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">💡</span>
          <textarea
            v-model="assistHint"
            rows="3"
            class="modern-input modern-textarea"
            :class="{ 'has-value': assistHint }"
          />
          <label class="floating-label">{{ $t('backlogPrep.assistHintLabel') }}</label>
        </div>
        <div class="ai-assist-card__actions">
          <button type="button" class="secondary-btn" :disabled="assistLoading" @click="runAssist">
            {{ assistLoading ? $t('backlogPrep.assistLoading') : $t('backlogPrep.assistRun') }}
          </button>
        </div>
        <p v-if="assistError" class="assist-error">{{ assistError }}</p>
      </section>

      <div class="modern-form">
        <p v-if="editingLibraryId" class="edit-banner">
          {{ $t('backlogPrep.editingItem', { id: editingLibraryId }) }}
          <button type="button" class="linkish" @click="clearLibraryEdit">{{ $t('backlogPrep.cancelEdit') }}</button>
        </p>

        <div class="field-block">
          <div class="input-wrapper">
            <span class="input-icon">🏷️</span>
            <input
              v-model="form.title"
              type="text"
              class="modern-input"
              :class="{ 'has-value': form.title }"
            />
            <label class="floating-label">{{ $t('backlogPrep.itemTitle') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintTitle') }}</p>
        </div>

        <div class="form-grid">
          <div class="field-block">
            <div class="input-wrapper">
              <span class="input-icon">📋</span>
              <select
                v-model="form.workType"
                class="modern-input modern-select"
                :class="{ 'has-value': form.workType }"
              >
                <option value=""></option>
                <option value="story">{{ $t('backlogPrep.story') }}</option>
                <option value="epic">{{ $t('backlogPrep.epic') }}</option>
              </select>
              <label class="floating-label">{{ $t('backlogPrep.workType') }}</label>
            </div>
            <p class="field-hint">{{ $t('backlogPrep.hintWorkType') }}</p>
          </div>

          <div class="field-block">
            <div class="input-wrapper">
              <span class="input-icon">🌐</span>
              <select
                v-model="form.language"
                class="modern-input modern-select"
                :class="{ 'has-value': form.language }"
              >
                <option value=""></option>
                <option value="ru">Русский</option>
                <option value="en">English</option>
              </select>
              <label class="floating-label">{{ $t('backlogPrep.language') }}</label>
            </div>
            <p class="field-hint">{{ $t('backlogPrep.hintLanguage') }}</p>
          </div>
        </div>

        <div v-if="form.workType === 'story'" class="field-block field-block--plain-select">
          <label class="plain-field-label" for="backlog-parent-epic">{{ $t('backlogPrep.parentEpic') }}</label>
          <div class="input-wrapper input-wrapper--plain-select">
            <span class="input-icon" aria-hidden="true">🔗</span>
            <select
              id="backlog-parent-epic"
              v-model="form.parentEpicId"
              class="modern-input modern-select modern-select--plain"
            >
              <option :value="''">{{ $t('backlogPrep.noParentEpic') }}</option>
              <option v-for="e in epicSelectOptions" :key="e.id" :value="String(e.id)">{{ e.title }}</option>
            </select>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintParentEpic') }}</p>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">📝</span>
            <textarea
              v-model="form.text"
              rows="7"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.text }"
            />
            <label class="floating-label">{{ $t('backlogPrep.description') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintDescription') }}</p>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">✅</span>
            <textarea
              v-model="form.acceptance_criteria"
              rows="4"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.acceptance_criteria }"
            />
            <label class="floating-label">{{ $t('backlogPrep.acceptanceCriteria') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintAc') }}</p>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">⚙️</span>
            <textarea
              v-model="form.nfr"
              rows="3"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.nfr }"
            />
            <label class="floating-label">{{ $t('backlogPrep.nfr') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintNfr') }}</p>
        </div>

        <div class="field-block">
          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon">🎯</span>
            <textarea
              v-model="form.context"
              rows="4"
              class="modern-input modern-textarea"
              :class="{ 'has-value': form.context }"
            />
            <label class="floating-label">{{ $t('backlogPrep.context') }}</label>
          </div>
          <p class="field-hint">{{ $t('backlogPrep.hintContext') }}</p>
        </div>
      </div>

      <div class="actions actions--wrap">
        <button class="primary" :disabled="loading" @click="analyze">
          {{ loading ? $t('common.loading') : $t('backlogPrep.run') }}
        </button>
        <button type="button" class="primary ghost" :disabled="saveLibraryLoading" @click="saveToLibrary">
          {{ saveLibraryLoading ? $t('common.loading') : $t('backlogPrep.saveLibrary') }}
        </button>
        <button type="button" class="secondary-btn" @click="copyCurrentJira('wiki')">{{ $t('backlogPrep.copyFormWiki') }}</button>
        <button type="button" class="secondary-btn" @click="copyCurrentJira('plain')">{{ $t('backlogPrep.copyFormPlain') }}</button>
        <button type="button" class="secondary-btn" @click="copyCurrentSummary">{{ $t('backlogPrep.copySummary') }}</button>
        <span v-if="error" class="error">{{ error }}</span>
      </div>

      <section class="library-card library-card--nested" aria-labelledby="lib-title">
        <h2 id="lib-title" class="library-card__title">{{ $t('backlogPrep.libraryTitle') }}</h2>
        <p class="section-lead">{{ $t('backlogPrep.libraryLead') }}</p>
        <p v-if="libraryLoading" class="muted">{{ $t('common.loading') }}</p>
        <p v-else-if="!libraryItems.length" class="muted">{{ $t('backlogPrep.libraryEmpty') }}</p>
        <div v-else class="library-list">
          <article v-for="root in libraryItems" :key="root.id" class="library-epic">
            <div class="library-epic__head">
              <span class="badge badge-epic">Epic</span>
              <strong>{{ root.title }}</strong>
              <div class="library-epic__actions">
                <button type="button" class="linkish" @click="editLibraryItem(root)">{{ $t('backlogPrep.edit') }}</button>
                <button type="button" class="linkish" @click="copyJira(root, 'wiki')">{{ $t('backlogPrep.copyJiraWiki') }}</button>
                <button type="button" class="linkish" @click="copyJira(root, 'plain')">{{ $t('backlogPrep.copyJiraPlain') }}</button>
                <button type="button" class="linkish danger" @click="deleteLibraryItem(root)">{{ $t('backlogPrep.delete') }}</button>
              </div>
            </div>
            <p v-if="root.description" class="library-preview">{{ truncate(root.description, 160) }}</p>
            <ul v-if="root.children && root.children.length" class="library-stories">
              <li v-for="ch in root.children" :key="ch.id" class="library-story">
                <span class="badge badge-story">Story</span>
                <span class="library-story__title">{{ ch.title }}</span>
                <div class="library-story__actions">
                  <button type="button" class="linkish" @click="editLibraryItem(ch)">{{ $t('backlogPrep.edit') }}</button>
                  <button type="button" class="linkish" @click="copyJira(ch, 'wiki')">{{ $t('backlogPrep.copyJiraWiki') }}</button>
                  <button type="button" class="linkish" @click="copyJira(ch, 'plain')">{{ $t('backlogPrep.copyJiraPlain') }}</button>
                  <button type="button" class="linkish danger" @click="deleteLibraryItem(ch)">{{ $t('backlogPrep.delete') }}</button>
                </div>
              </li>
            </ul>
          </article>
        </div>
      </section>

        </div>
      </section>

      <!-- Блок 3: проверка и рекомендации -->
      <section class="prep-block prep-block--review" aria-labelledby="block-review-title">
        <header class="prep-block__header">
          <span class="prep-block__badge" aria-hidden="true">3</span>
          <div class="prep-block__head-text">
            <h2 id="block-review-title" class="prep-block__title">{{ $t('backlogPrep.blockReviewTitle') }}</h2>
            <p class="prep-block__lead">{{ $t('backlogPrep.blockReviewLead') }}</p>
          </div>
        </header>
        <div class="review-shell">
          <div v-if="!result" class="review-shell__empty">
            {{ $t('backlogPrep.blockReviewEmpty') }}
          </div>
          <div v-else class="review-shell__filled">
            <div class="review-report">
              <div v-if="result.missing_fields?.length" class="review-card">
                <h3 class="review-card__title">🧩 {{ $t('backlogPrep.missingFields') }}</h3>
                <ul class="review-card__list">
                  <li v-for="item in result.missing_fields" :key="'m-' + item">{{ item }}</li>
                </ul>
              </div>
              <div v-if="result.questions?.length" class="review-card">
                <h3 class="review-card__title">❓ {{ $t('backlogPrep.questions') }}</h3>
                <ul class="review-card__list">
                  <li v-for="item in result.questions" :key="'q-' + item">{{ item }}</li>
                </ul>
              </div>
              <div v-if="result.suggestions?.length" class="review-card">
                <h3 class="review-card__title">💡 {{ $t('backlogPrep.suggestions') }}</h3>
                <ul class="review-card__list">
                  <li v-for="item in result.suggestions" :key="'s-' + item">{{ item }}</li>
                </ul>
              </div>

              <div v-if="improvedStructured" class="review-card review-card--improved">
                <div class="improved-card__head">
                  <h3 class="review-card__title">📝 {{ $t('backlogPrep.improvedExample') }}</h3>
                  <span
                    class="improved-type-pill"
                    :class="improvedStructured.item_type === 'epic' ? 'improved-type-pill--epic' : 'improved-type-pill--story'"
                  >
                    {{ improvedStructured.item_type === 'epic' ? $t('backlogPrep.epic') : $t('backlogPrep.story') }}
                  </span>
                </div>
                <div class="improved-sections">
                  <section class="improved-block">
                    <h4 class="improved-block__label">{{ $t('backlogPrep.improvedDescription') }}</h4>
                    <p class="improved-block__text">{{ improvedStructured.description }}</p>
                  </section>
                  <section v-if="improvedStructured.context_goal" class="improved-block">
                    <h4 class="improved-block__label">{{ $t('backlogPrep.improvedContext') }}</h4>
                    <p class="improved-block__text">{{ improvedStructured.context_goal }}</p>
                  </section>
                  <section v-if="improvedStructured.acceptance_criteria?.length" class="improved-block">
                    <h4 class="improved-block__label">{{ $t('backlogPrep.improvedAcHeading') }}</h4>
                    <ol class="improved-ac-list">
                      <li v-for="(ac, idx) in improvedStructured.acceptance_criteria" :key="'ac-' + idx">{{ ac }}</li>
                    </ol>
                  </section>
                  <section v-if="improvedStructured.non_functional_requirements?.length" class="improved-block">
                    <h4 class="improved-block__label">{{ $t('backlogPrep.improvedNfrHeading') }}</h4>
                    <ul class="improved-nfr-list">
                      <li v-for="(n, idx) in improvedStructured.non_functional_requirements" :key="'nfr-' + idx">{{ n }}</li>
                    </ul>
                  </section>
                </div>
                <div class="improved-card__actions">
                  <button type="button" class="secondary-btn" @click="applyImprovedToForm">
                    {{ $t('backlogPrep.applyImprovedToForm') }}
                  </button>
                  <button
                    v-if="improvedStructured.item_type === 'epic'"
                    type="button"
                    class="primary small"
                    :disabled="decomposeEpicLoading"
                    @click="runEpicDecompose"
                  >
                    {{ decomposeEpicLoading ? $t('common.loading') : $t('backlogPrep.decomposeEpic') }}
                  </button>
                </div>
                <p v-if="decomposeEpicError" class="assist-error">{{ decomposeEpicError }}</p>
                <div v-if="result.epic_decompose_stories?.length" class="decompose-stories">
                  <h4 class="decompose-stories__title">{{ $t('backlogPrep.decomposeStoriesTitle') }}</h4>
                  <ul class="decompose-stories__list">
                    <li v-for="(st, idx) in result.epic_decompose_stories" :key="'ds-' + idx" class="decompose-story">
                      <div class="decompose-story__body">
                        <strong>{{ st.title }}</strong>
                        <p>{{ st.summary }}</p>
                        <p v-if="st.acceptance_hint" class="decompose-story__hint">{{ st.acceptance_hint }}</p>
                      </div>
                      <button type="button" class="linkish" @click="applyDecomposedStory(st)">
                        {{ $t('backlogPrep.applyStoryToForm') }}
                      </button>
                    </li>
                  </ul>
                </div>
              </div>
              <div v-else-if="legacyImprovedText" class="review-card review-card--example">
                <h3 class="review-card__title">📝 {{ $t('backlogPrep.improvedExample') }}</h3>
                <pre class="review-card__pre">{{ legacyImprovedText }}</pre>
              </div>
              <p
                v-if="reviewReportIsEmpty"
                class="review-shell__empty"
              >
                {{ $t('backlogPrep.blockReviewEmpty') }}
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "BacklogPrep",
  data() {
    return {
      loading: false,
      error: "",
      result: null,
      introExpanded: false,
      assistHint: "",
      assistLoading: false,
      assistError: "",
      aiUsageRemaining: null,
      libraryItems: [],
      libraryLoading: false,
      saveLibraryLoading: false,
      editingLibraryId: null,
      specPaste: "",
      specFile: null,
      specFileName: "",
      specLoading: false,
      specError: "",
      specResult: null,
      copiedFeedback: "",
      copyTimer: null,
      decomposeEpicLoading: false,
      decomposeEpicError: "",
      form: {
        title: "",
        text: "",
        context: "",
        acceptance_criteria: "",
        nfr: "",
        workType: "story",
        language: "ru",
        parentEpicId: "",
      },
    };
  },
  computed: {
    epicSelectOptions() {
      return (this.libraryItems || []).filter((r) => r.item_type === "epic");
    },
    improvedStructured() {
      const r = this.result;
      if (!r) return null;
      if (r.improved && typeof r.improved === "object" && (r.improved.description || (r.improved.acceptance_criteria && r.improved.acceptance_criteria.length))) {
        return this.normalizeImproved(r.improved);
      }
      return this.parseLegacyImprovedExample(r);
    },
    legacyImprovedText() {
      const r = this.result;
      if (!r || this.improvedStructured) return "";
      const ex = r.improved_example;
      if (ex == null || ex === "") return "";
      return typeof ex === "string" ? ex : String(ex);
    },
    reviewReportIsEmpty() {
      const r = this.result;
      if (!r) return false;
      const hasLists =
        (r.missing_fields && r.missing_fields.length) ||
        (r.questions && r.questions.length) ||
        (r.suggestions && r.suggestions.length);
      const hasImp = !!this.improvedStructured || !!this.legacyImprovedText;
      const hasDec = r.epic_decompose_stories && r.epic_decompose_stories.length;
      return !hasLists && !hasImp && !hasDec;
    },
  },
  mounted() {
    this.fetchAiUsage();
    this.loadLibrary();
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem("token");
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    normalizeImproved(im) {
      const ac = Array.isArray(im.acceptance_criteria) ? im.acceptance_criteria : [];
      const nfr = Array.isArray(im.non_functional_requirements) ? im.non_functional_requirements : [];
      return {
        item_type: im.item_type === "epic" ? "epic" : "story",
        description: (im.description || "").trim(),
        context_goal: (im.context_goal || "").trim(),
        acceptance_criteria: ac.map((x) => String(x).trim()).filter(Boolean),
        non_functional_requirements: nfr.map((x) => String(x).trim()).filter(Boolean),
      };
    },
    parseLegacyImprovedExample(r) {
      const ex = r.improved_example;
      if (ex == null || typeof ex !== "string") return null;
      const s = ex.trim();
      if (!s.startsWith("{")) return null;
      try {
        const o = JSON.parse(s);
        const ac = o.acceptance_criteria;
        const nfr = o.non_functional_requirements;
        return {
          item_type: o.type === "epic" || o.item_type === "epic" ? "epic" : "story",
          description: (o.description || "").trim(),
          context_goal: (o.context_goal || o.context || "").trim(),
          acceptance_criteria: Array.isArray(ac) ? ac.map((x) => String(x).trim()).filter(Boolean) : [],
          non_functional_requirements: Array.isArray(nfr) ? nfr.map((x) => String(x).trim()).filter(Boolean) : [],
        };
      } catch {
        return null;
      }
    },
    applyImprovedToForm() {
      const imp = this.improvedStructured;
      if (!imp) return;
      this.form.workType = imp.item_type;
      this.form.text = imp.description;
      this.form.context = imp.context_goal;
      this.form.acceptance_criteria = imp.acceptance_criteria.join("\n");
      this.form.nfr = imp.non_functional_requirements.join("\n");
      this.flashCopied(this.$t("backlogPrep.appliedImprovedToForm"));
    },
    applyDecomposedStory(st) {
      if (!st) return;
      this.form.workType = "story";
      this.form.title = (st.title || "").trim();
      this.form.text = (st.summary || "").trim();
      this.form.acceptance_criteria = (st.acceptance_hint || "").trim();
      this.form.parentEpicId = "";
      this.flashCopied(this.$t("backlogPrep.appliedToForm"));
      window.scrollTo({ top: 320, behavior: "smooth" });
    },
    async runEpicDecompose() {
      this.decomposeEpicError = "";
      const imp = this.improvedStructured;
      const text = ((imp && imp.description) || this.form.text || "").trim();
      if (!text) {
        this.decomposeEpicError = this.$t("backlogPrep.validation");
        return;
      }
      this.decomposeEpicLoading = true;
      try {
        const { data } = await axios.post(
          "/api/backlog/prep/decompose-epic",
          {
            text,
            context: (imp && imp.context_goal) || this.form.context,
            nfr: this.form.nfr,
            language: this.form.language,
          },
          { headers: { ...this.authHeaders(), "Content-Type": "application/json" } }
        );
        this.result = {
          ...this.result,
          epic_decompose_stories: data.suggested_stories || [],
        };
        await this.fetchAiUsage();
      } catch (e) {
        this.decomposeEpicError =
          e?.response?.data?.error || e?.response?.data?.details || e?.message || this.$t("common.error");
      } finally {
        this.decomposeEpicLoading = false;
      }
    },
    truncate(s, n) {
      if (!s) return "";
      return s.length <= n ? s : `${s.slice(0, n)}…`;
    },
    deriveTitle(text) {
      const line = (text || "")
        .split("\n")
        .map((x) => x.trim())
        .find(Boolean);
      if (!line) return this.$t("backlogPrep.untitled");
      return line.length > 120 ? `${line.slice(0, 117)}…` : line;
    },
    flashCopied(msg) {
      this.copiedFeedback = msg;
      if (this.copyTimer) clearTimeout(this.copyTimer);
      this.copyTimer = setTimeout(() => {
        this.copiedFeedback = "";
      }, 2200);
    },
    async copyText(text, msgKey) {
      try {
        await navigator.clipboard.writeText(text);
        this.flashCopied(this.$t(msgKey));
      } catch {
        this.flashCopied(this.$t("backlogPrep.copyFailed"));
      }
    },
    buildExportPayload(item) {
      return {
        title: (item.title || "").trim() || this.deriveTitle(item.description),
        description: item.description || "",
        acceptance_criteria: item.acceptance_criteria || "",
        nfr: item.nfr || "",
        context: item.context || "",
      };
    },
    formatJiraWiki(p) {
      const lines = [];
      lines.push(`*${p.title}*`);
      lines.push("");
      lines.push("h2. Description");
      lines.push(p.description || "—");
      if (p.context) {
        lines.push("");
        lines.push("h3. Context");
        lines.push(p.context);
      }
      if (p.acceptance_criteria) {
        lines.push("");
        lines.push("h3. Acceptance criteria");
        p.acceptance_criteria
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .forEach((l) => {
            const t = l.replace(/^[-*•]\s*/, "");
            lines.push(`* ${t}`);
          });
      }
      if (p.nfr) {
        lines.push("");
        lines.push("h3. Non-functional requirements");
        p.nfr
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .forEach((l) => {
            const t = l.replace(/^[-*•]\s*/, "");
            lines.push(`* ${t}`);
          });
      }
      return lines.join("\n");
    },
    formatJiraPlain(p) {
      const sep = "────────────────────────";
      const lines = [];
      lines.push(`SUMMARY: ${p.title}`);
      lines.push(sep);
      lines.push("DESCRIPTION");
      lines.push(p.description || "—");
      if (p.context) {
        lines.push("");
        lines.push("CONTEXT");
        lines.push(p.context);
      }
      if (p.acceptance_criteria) {
        lines.push("");
        lines.push("ACCEPTANCE CRITERIA");
        p.acceptance_criteria
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .forEach((l) => {
            lines.push(`- ${l.replace(/^[-*•]\s*/, "")}`);
          });
      }
      if (p.nfr) {
        lines.push("");
        lines.push("NON-FUNCTIONAL");
        p.nfr
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .forEach((l) => {
            lines.push(`- ${l.replace(/^[-*•]\s*/, "")}`);
          });
      }
      return lines.join("\n");
    },
    copyJira(item, mode) {
      const p = this.buildExportPayload(item);
      const text = mode === "wiki" ? this.formatJiraWiki(p) : this.formatJiraPlain(p);
      this.copyText(text, "backlogPrep.copied");
    },
    copyCurrentJira(mode) {
      const p = this.buildExportPayload({
        title: this.form.title,
        description: this.form.text,
        acceptance_criteria: this.form.acceptance_criteria,
        nfr: this.form.nfr,
        context: this.form.context,
      });
      const text = mode === "wiki" ? this.formatJiraWiki(p) : this.formatJiraPlain(p);
      this.copyText(text, "backlogPrep.copied");
    },
    copyCurrentSummary() {
      const t = (this.form.title || "").trim() || this.deriveTitle(this.form.text);
      this.copyText(t, "backlogPrep.copiedSummary");
    },
    async fetchAiUsage() {
      try {
        const { data } = await axios.get("/api/ai-usage", { headers: this.authHeaders() });
        this.aiUsageRemaining = data?.remaining ?? null;
      } catch {
        this.aiUsageRemaining = null;
      }
    },
    async loadLibrary() {
      this.libraryLoading = true;
      try {
        const { data } = await axios.get("/api/backlog/items", { headers: this.authHeaders() });
        this.libraryItems = data.items || [];
      } catch {
        this.libraryItems = [];
      } finally {
        this.libraryLoading = false;
      }
    },
    clearLibraryEdit() {
      this.editingLibraryId = null;
    },
    editLibraryItem(item) {
      this.editingLibraryId = item.id;
      this.form.workType = item.item_type || "story";
      this.form.title = item.title || "";
      this.form.text = item.description || "";
      this.form.context = item.context || "";
      this.form.acceptance_criteria = item.acceptance_criteria || "";
      this.form.nfr = item.nfr || "";
      this.form.parentEpicId = item.parent_id != null ? String(item.parent_id) : "";
      window.scrollTo({ top: 0, behavior: "smooth" });
    },
    async deleteLibraryItem(item) {
      if (!window.confirm(this.$t("backlogPrep.deleteConfirm"))) return;
      try {
        await axios.delete(`/api/backlog/items/${item.id}`, { headers: this.authHeaders() });
        await this.loadLibrary();
      } catch (e) {
        this.error = e?.response?.data?.error || this.$t("common.error");
      }
    },
    async saveToLibrary() {
      this.error = "";
      const title = (this.form.title || "").trim() || this.deriveTitle(this.form.text);
      if (!(this.form.text || "").trim()) {
        this.error = this.$t("backlogPrep.validation");
        return;
      }
      const payload = {
        item_type: this.form.workType || "story",
        title,
        description: (this.form.text || "").trim(),
        acceptance_criteria: (this.form.acceptance_criteria || "").trim(),
        nfr: (this.form.nfr || "").trim(),
        context: (this.form.context || "").trim(),
      };
      if (this.form.workType === "story") {
        if (this.form.parentEpicId) {
          const pid = parseInt(String(this.form.parentEpicId), 10);
          payload.parent_id = Number.isNaN(pid) ? null : pid;
        } else {
          payload.parent_id = null;
        }
      }
      this.saveLibraryLoading = true;
      try {
        if (this.editingLibraryId) {
          await axios.put(`/api/backlog/items/${this.editingLibraryId}`, payload, {
            headers: { ...this.authHeaders(), "Content-Type": "application/json" },
          });
        } else {
          await axios.post("/api/backlog/items", payload, {
            headers: { ...this.authHeaders(), "Content-Type": "application/json" },
          });
        }
        this.editingLibraryId = null;
        await this.loadLibrary();
        this.flashCopied(this.$t("backlogPrep.savedLibrary"));
      } catch (e) {
        this.error = e?.response?.data?.error || this.$t("common.error");
      } finally {
        this.saveLibraryLoading = false;
      }
    },
    onSpecFile(ev) {
      const f = ev.target.files && ev.target.files[0];
      this.specFile = f || null;
      this.specFileName = f ? f.name : "";
    },
    async runSpecDecompose() {
      this.specError = "";
      this.specResult = null;
      const hasText = (this.specPaste || "").trim().length >= 80;
      if (!this.specFile && !hasText) {
        this.specError = this.$t("backlogPrep.specTooShort");
        return;
      }
      this.specLoading = true;
      try {
        const fd = new FormData();
        if (this.specFile) fd.append("file", this.specFile);
        if ((this.specPaste || "").trim()) fd.append("text", (this.specPaste || "").trim());
        fd.append("language", this.form.language || "ru");
        const { data } = await axios.post("/api/backlog/spec-decompose", fd, {
          headers: { ...this.authHeaders() },
        });
        this.specResult = data;
        await this.fetchAiUsage();
      } catch (e) {
        this.specError =
          e?.response?.data?.error || e?.response?.data?.details || e?.message || this.$t("common.error");
      } finally {
        this.specLoading = false;
      }
    },
    applySpecToForm() {
      if (!this.specResult) return;
      this.form.workType = "epic";
      this.form.title = this.specResult.epic_title || "";
      this.form.text = this.specResult.epic_description || "";
      this.form.context = this.specResult.epic_context || "";
      this.form.acceptance_criteria = "";
      this.form.nfr = "";
      this.form.parentEpicId = "";
      this.flashCopied(this.$t("backlogPrep.appliedToForm"));
    },
    async saveSpecBundle() {
      if (!this.specResult) return;
      try {
        await axios.post("/api/backlog/items/from-spec", this.specResult, {
          headers: { ...this.authHeaders(), "Content-Type": "application/json" },
        });
        this.specResult = null;
        this.specPaste = "";
        this.specFile = null;
        this.specFileName = "";
        await this.loadLibrary();
        this.flashCopied(this.$t("backlogPrep.bundleSaved"));
      } catch (e) {
        this.specError = e?.response?.data?.error || this.$t("common.error");
      }
    },
    async runAssist() {
      this.assistError = "";
      const hint = (this.assistHint || "").trim();
      if (!hint && !(this.form.text || "").trim()) {
        this.assistError = this.$t("backlogPrep.assistNeedHint");
        return;
      }
      this.assistLoading = true;
      try {
        const { data } = await axios.post(
          "/api/backlog/prep/assist",
          {
            hint,
            work_type: this.form.workType,
            language: this.form.language,
            existing_text: this.form.text,
            existing_context: this.form.context,
            existing_acceptance_criteria: this.form.acceptance_criteria,
            existing_nfr: this.form.nfr,
          },
          { headers: { ...this.authHeaders(), "Content-Type": "application/json" } }
        );
        if (data.suggested_text) this.form.text = data.suggested_text;
        if (data.suggested_context) this.form.context = data.suggested_context;
        if (data.suggested_acceptance_criteria != null) this.form.acceptance_criteria = data.suggested_acceptance_criteria;
        if (data.suggested_nfr != null) this.form.nfr = data.suggested_nfr;
        await this.fetchAiUsage();
      } catch (err) {
        this.assistError = err?.response?.data?.error || err?.message || this.$t("common.error");
      } finally {
        this.assistLoading = false;
      }
    },
    async analyze() {
      this.error = "";
      this.result = null;
      this.decomposeEpicError = "";

      if (!this.form.text.trim()) {
        this.error = this.$t("backlogPrep.validation");
        return;
      }

      this.loading = true;
      try {
        const { data } = await axios.post(
          "/api/backlog/prep",
          {
            text: this.form.text,
            context: this.form.context,
            acceptance_criteria: this.form.acceptance_criteria,
            nfr: this.form.nfr,
            work_type: this.form.workType,
            language: this.form.language,
          },
          { headers: { ...this.authHeaders(), "Content-Type": "application/json" } }
        );
        this.result = data;
        await this.fetchAiUsage();
      } catch (err) {
        this.error = err?.response?.data?.error || err?.message || this.$t("common.error");
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped>
.prep-page {
  max-width: 1280px;
  margin: 0 auto;
  padding: 24px 16px 48px;
}

.prep-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  border: 1px solid #bae6fd;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 12px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

.subtitle {
  color: #6b7280;
  margin-bottom: 16px;
  font-size: 16px;
  line-height: 1.6;
}

.ai-usage-line {
  margin: 0 0 20px;
  font-size: 14px;
  color: #475569;
}

.copy-feedback {
  margin: 0 0 12px;
  font-size: 14px;
  color: #059669;
  font-weight: 600;
}

.prep-intro {
  margin-bottom: 28px;
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.prep-intro__title {
  font-size: 1.2rem;
  margin: 0 0 12px;
  color: #0c4a6e;
}

.prep-intro__lead {
  margin: 0 0 16px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.prep-intro__toggle {
  background: #fff;
  border: 2px solid #0ea5e9;
  color: #0369a1;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.prep-intro__body {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.prep-intro__card {
  background: #fff;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.prep-intro__card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.prep-intro__card p {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.prep-intro__badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #0ea5e9;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
}

.prep-block {
  margin-bottom: 32px;
  border-radius: 18px;
  border: 2px solid #bae6fd;
  background: #fff;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(14, 165, 233, 0.08);
}

.prep-block--decompose {
  border-color: #7dd3fc;
}

.prep-block--compose {
  border-color: #c7d2fe;
}

.prep-block--review {
  border-color: #5eead4;
}

.prep-block__header {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  padding: 20px 22px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-bottom: 1px solid #e2e8f0;
}

.prep-block--compose .prep-block__header {
  background: linear-gradient(135deg, #eef2ff 0%, #f5f3ff 100%);
}

.prep-block--review .prep-block__header {
  background: linear-gradient(135deg, #f0fdfa 0%, #ecfeff 100%);
}

.prep-block__badge {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: #0ea5e9;
  color: #fff;
  font-weight: 800;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.prep-block--compose .prep-block__badge {
  background: #6366f1;
}

.prep-block--review .prep-block__badge {
  background: #0d9488;
}

.prep-block__head-text {
  flex: 1;
  min-width: 0;
}

.prep-block__title {
  margin: 0 0 6px;
  font-size: 1.25rem;
  color: #0f172a;
}

.prep-block__lead {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.prep-block__body {
  padding: 20px 22px 24px;
}

.plain-field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 8px;
  padding-left: 4px;
}

.input-wrapper--plain-select .modern-select--plain {
  padding-top: 14px;
  padding-bottom: 14px;
  min-height: 52px;
  line-height: 1.45;
}

.input-wrapper--plain-select .modern-select--plain:focus,
.input-wrapper--plain-select .modern-select--plain.has-value {
  padding-top: 14px;
  padding-bottom: 14px;
}

.review-shell {
  padding: 20px 22px 24px;
}

.review-shell__empty {
  margin: 0;
  padding: 28px 20px;
  text-align: center;
  font-size: 15px;
  color: #64748b;
  background: #f8fafc;
  border: 2px dashed #cbd5e1;
  border-radius: 14px;
  line-height: 1.55;
}

.review-report {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.review-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 18px 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.review-card__title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.review-card__list {
  margin: 0;
  padding-left: 22px;
  color: #374151;
  line-height: 1.65;
}

.review-card--example {
  border-color: #bae6fd;
  background: linear-gradient(to bottom, #fff 0%, #f0f9ff 100%);
}

.review-card__example {
  white-space: pre-wrap;
  color: #1e293b;
  line-height: 1.65;
  font-size: 14px;
  padding: 14px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e0f2fe;
}

.review-card__pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 13px;
  line-height: 1.55;
  color: #334155;
  padding: 14px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  max-height: 420px;
  overflow: auto;
}

.review-card--improved {
  border-color: #93c5fd;
  background: linear-gradient(to bottom, #fff 0%, #f8fafc 100%);
}

.improved-card__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.improved-card__head .review-card__title {
  margin: 0;
  flex: 1 1 auto;
}

.improved-type-pill {
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 6px 12px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}

.improved-type-pill--story {
  background: #dbeafe;
  color: #1d4ed8;
}

.improved-type-pill--epic {
  background: #ede9fe;
  color: #5b21b6;
}

.improved-sections {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.improved-block__label {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 700;
  color: #475569;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.improved-block__text {
  margin: 0;
  font-size: 15px;
  line-height: 1.6;
  color: #1e293b;
}

.improved-ac-list {
  margin: 0;
  padding-left: 22px;
  color: #334155;
  line-height: 1.65;
  font-size: 14px;
}

.improved-ac-list li {
  margin-bottom: 8px;
}

.improved-nfr-list {
  margin: 0;
  padding-left: 20px;
  color: #334155;
  line-height: 1.6;
  font-size: 14px;
}

.improved-card__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #e2e8f0;
}

.decompose-stories {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px dashed #cbd5e1;
}

.decompose-stories__title {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: #0f172a;
}

.decompose-stories__list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.decompose-story {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: flex-start;
  justify-content: space-between;
  padding: 14px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.decompose-story__body {
  flex: 1 1 220px;
  min-width: 0;
  font-size: 14px;
  color: #374151;
  line-height: 1.55;
}

.decompose-story__body p {
  margin: 8px 0 0;
}

.decompose-story__hint {
  font-size: 13px;
  color: #64748b;
  white-space: pre-wrap;
}

.spec-card__subtitle {
  margin: 0 0 8px;
  font-size: 1.05rem;
  color: #0c4a6e;
}

.library-card__title {
  margin: 0 0 8px;
  font-size: 1.1rem;
  color: #312e81;
}

.library-card--nested {
  margin-top: 8px;
}

.section-title {
  margin: 0 0 8px;
  font-size: 1.15rem;
  color: #0c4a6e;
}

.section-lead {
  margin: 0 0 14px;
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

.spec-card {
  margin-bottom: 28px;
  padding: 22px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fafafa;
}

.spec-card--nested {
  margin-bottom: 0;
  background: #f8fafc;
}

.library-card {
  margin-bottom: 28px;
  padding: 22px;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: #fafafa;
}

.library-card--nested {
  margin-bottom: 0;
  background: #f8fafc;
  border-style: dashed;
}

.muted {
  color: #94a3b8;
  font-size: 14px;
}

.library-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.library-epic {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 14px 16px;
}

.library-epic__head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.library-epic__head strong {
  flex: 1 1 200px;
  color: #111827;
}

.library-epic__actions,
.library-story__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.library-preview {
  margin: 8px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.library-stories {
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
  border-top: 1px solid #f3f4f6;
}

.library-story {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 14px;
}

.library-story__title {
  flex: 1 1 180px;
  color: #374151;
}

.badge {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 6px;
}

.badge-epic {
  background: #ede9fe;
  color: #5b21b6;
}

.badge-story {
  background: #dbeafe;
  color: #1d4ed8;
}

.linkish {
  border: none;
  background: none;
  color: #2563eb;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  padding: 0;
  font-family: inherit;
}

.linkish.danger {
  color: #dc2626;
}

.spec-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.file-input {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
}

.file-label {
  cursor: pointer;
}

.file-btn {
  display: inline-block;
  padding: 10px 16px;
  background: #fff;
  border: 2px solid #0ea5e9;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  color: #0369a1;
}

.file-name {
  font-size: 13px;
  color: #64748b;
}

.spec-result {
  margin-top: 18px;
  padding: 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid #bae6fd;
}

.spec-result__title {
  margin: 0 0 8px;
  font-size: 1.1rem;
  color: #0f172a;
}

.spec-result__body {
  margin: 0 0 10px;
  font-size: 14px;
  line-height: 1.55;
  color: #374151;
}

.spec-result__ctx {
  font-size: 14px;
  color: #4b5563;
  margin: 0 0 12px;
}

.spec-result__sub {
  margin: 16px 0 8px;
  font-size: 15px;
  color: #111827;
}

.spec-stories {
  margin: 0;
  padding-left: 20px;
  font-size: 14px;
  color: #374151;
  line-height: 1.55;
}

.spec-ac-hint {
  margin-top: 4px;
  font-size: 13px;
  color: #6b7280;
  white-space: pre-wrap;
}

.spec-result__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 16px;
}

.primary.small {
  padding: 10px 18px;
  font-size: 14px;
}

.primary.ghost {
  background: #fff;
  color: #0284c7;
  border: 2px solid #0ea5e9;
  box-shadow: none;
}

.edit-banner {
  padding: 10px 14px;
  background: #fef3c7;
  border-radius: 10px;
  font-size: 14px;
  color: #92400e;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.ai-assist-card {
  margin-bottom: 28px;
  padding: 20px 22px;
  background: linear-gradient(145deg, #faf5ff 0%, #eef2ff 100%);
  border-radius: 16px;
  border: 1px solid #c7d2fe;
}

.ai-assist-card__title {
  margin: 0 0 8px;
  font-size: 1.05rem;
  color: #312e81;
}

.ai-assist-card__hint {
  margin: 0 0 14px;
  font-size: 13px;
  color: #5b21b6;
  line-height: 1.45;
}

.ai-assist-card__actions {
  margin-top: 12px;
}

.secondary-btn {
  border: 2px solid #6366f1;
  background: #fff;
  color: #4338ca;
  padding: 10px 20px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  font-family: inherit;
}

.secondary-btn:hover:not(:disabled) {
  background: #eef2ff;
}

.secondary-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.assist-error {
  margin-top: 10px;
  color: #dc2626;
  font-size: 14px;
}

.field-block {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-hint {
  margin: 0;
  font-size: 13px;
  color: #64748b;
  line-height: 1.45;
  padding-left: 4px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 24px;
}

.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
  margin-top: 0;
}

.input-wrapper.textarea-wrapper {
  margin-top: 0;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.textarea-wrapper .input-icon {
  top: 24px;
  transform: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.modern-textarea {
  padding-top: 32px;
  min-height: 120px;
  resize: vertical;
  line-height: 1.6;
}

.modern-select {
  padding-right: 52px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%236b7280' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
  z-index: 1;
}

.textarea-wrapper .floating-label {
  top: 32px;
  transform: none;
}

.modern-input:focus,
.modern-input.has-value {
  padding-top: 20px;
  padding-bottom: 8px;
  border-color: #0ea5e9;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f9ff 100%);
  box-shadow: 0 0 0 4px rgba(14, 165, 233, 0.12);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #0284c7;
  font-weight: 600;
  transform: none;
}

.textarea-wrapper .modern-input:focus + .floating-label,
.textarea-wrapper .modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
}

.modern-input:focus {
  outline: none;
}

.actions {
  display: flex;
  align-items: center;
  gap: 16px;
  margin: 24px 0 32px;
}

.actions--wrap {
  flex-wrap: wrap;
}

.primary {
  background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%);
  color: #fff;
  border: none;
  padding: 14px 28px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 600;
  font-size: 15px;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(14, 165, 233, 0.35);
}

.primary:hover:not(:disabled) {
  transform: translateY(-1px);
}

.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.error {
  color: #ef4444;
  font-size: 14px;
  font-weight: 500;
}

@media (max-width: 768px) {
  .prep-container {
    padding: 24px 20px;
  }

  h1 {
    font-size: 24px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .actions {
    flex-direction: column;
    align-items: stretch;
  }

  .primary {
    width: 100%;
  }
}
</style>
