<template>
  <div class="iceberg-container">
    <h1>{{ $t("systemThinking.title") }}</h1>
    <p v-if="aiUsageRemaining !== null" class="ai-usage-line">{{ $t("systemThinking.aiUsageRemaining", { count: aiUsageRemaining }) }}</p>

    <!-- Введение до начала работы -->
    <section class="iceberg-intro" aria-labelledby="iceberg-intro-title">
      <h2 id="iceberg-intro-title" class="iceberg-intro__title">{{ $t("systemThinking.introTitle") }}</h2>
      <p class="iceberg-intro__lead">
        {{ $t("systemThinking.introLead") }}
      </p>
      <button type="button" class="iceberg-intro__toggle" @click="introExpanded = !introExpanded">
        {{ introExpanded ? $t("systemThinking.toggleCollapse") : $t("systemThinking.toggleExpand") }}
      </button>
      <div v-show="introExpanded" class="iceberg-intro__levels">
        <article v-for="lvl in levelDefinitions" :key="lvl.id" class="iceberg-intro__level-card">
          <h3>
            <span class="iceberg-intro__badge">{{ lvl.order }}</span>
            {{ lvl.title }}
          </h3>
          <p class="iceberg-intro__q"><strong>{{ $t("systemThinking.levelQuestion") }}</strong> {{ lvl.question }}</p>
          <p class="iceberg-intro__ex">{{ lvl.description }}</p>
        </article>
      </div>
    </section>

    <div class="iceberg-list-section">
      <div class="filter-bar">
        <button type="button" class="add-btn" @click="openCreateFlow">{{ $t("systemThinking.createNew") }}</button>
      </div>

      <div class="iceberg-list">
        <div
          v-for="iceberg in icebergs"
          :key="iceberg.id"
          class="iceberg-card"
          @click="openIceberg(iceberg)"
        >
          <h3>{{ $t("systemThinking.icebergN", { id: iceberg.id }) }}</h3>
          <p>
            <strong>{{ $t("systemThinking.eventLabel") }}</strong>
            {{ (iceberg.event || $t("systemThinking.notSpecified")).slice(0, 100) }}{{ iceberg.event && iceberg.event.length > 100 ? "..." : "" }}
          </p>
          <p><strong>{{ $t("systemThinking.progressLabel") }}</strong> {{ $t("systemThinking.levelsOf5", { filled: fillCount(iceberg) }) }}</p>
          <div v-if="iceberg.solutions" class="solutions-badge">{{ $t("systemThinking.solutionsReady") }}</div>
          <button type="button" class="delete-btn" @click.stop="deleteIceberg(iceberg.id)">{{ $t("systemThinking.delete") }}</button>
        </div>
      </div>
    </div>

    <!-- Создание: примеры + подсказка ИИ + событие -->
    <div v-if="showCreateForm" class="modal-overlay" @click.self="showCreateForm = false">
      <div class="modal-content modal-content--wide">
        <button type="button" class="modal-close-top" @click="showCreateForm = false" :aria-label="$t('systemThinking.closeAria')">✕</button>
        <h2>{{ $t("systemThinking.createModalTitle") }}</h2>
        <p class="create-lead" v-html="$t('systemThinking.createLead')" />

        <div class="create-toolbar">
          <div class="ai-assistant-badge" @mouseenter="showCreateAiPopover = true" @mouseleave="showCreateAiPopover = false" @focusin="showCreateAiPopover = true" @focusout="showCreateAiPopover = false">
            <span class="ai-assistant-badge__icon" aria-hidden="true">✨</span>
            <span>{{ $t("systemThinking.createAiBadge") }}</span>
            <div v-show="showCreateAiPopover" class="ai-popover" role="tooltip">
              <p>{{ $t("systemThinking.createAiPopover1") }}</p>
              <p>{{ $t("systemThinking.createAiPopover2") }}</p>
              <p>{{ $t("systemThinking.createAiPopover3") }}</p>
            </div>
          </div>
        </div>

        <p class="scenarios-title">{{ $t("systemThinking.scenariosTitle") }}</p>
        <div class="scenario-chips">
          <button v-for="(s, i) in scenarioPresets" :key="i" type="button" class="scenario-chip" @click="applyScenario(s)">
            {{ s.label }}
          </button>
        </div>

        <div class="modern-form">
          <div class="textarea-wrapper textarea-wrapper--stacked">
            <label for="iceberg-new-event" class="stacked-field-label">{{ $t("systemThinking.eventFieldLabel") }}</label>
            <div class="textarea-with-icon">
              <span class="input-icon input-icon--stacked" aria-hidden="true">📝</span>
              <textarea
                id="iceberg-new-event"
                v-model="newEvent"
                rows="5"
                class="modern-input modern-textarea modern-textarea--stacked"
                :placeholder="$t('systemThinking.eventPlaceholder')"
              />
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="save-btn" :disabled="!newEvent.trim() || creating" @click="createIceberg">
            {{ creating ? $t("systemThinking.creating") : $t("systemThinking.createBtn") }}
          </button>
        </div>
      </div>
    </div>

    <!-- Работа с айсбергом -->
    <div v-if="showIcebergModal && currentIceberg" class="modal-overlay">
      <div class="modal-content iceberg-modal">
        <header class="iceberg-work-header">
          <h2>{{ $t("systemThinking.modalWorkTitle") }}</h2>
          <div class="iceberg-work-header__right">
            <div class="iceberg-work-actions">
              <button type="button" class="toolbar-btn" :title="$t('systemThinking.hintBtnTitle')" @click="showHelpModal = true">{{ $t("systemThinking.hintBtn") }}</button>
              <div
                class="ai-assistant-inline"
                tabindex="0"
                @mouseenter="showWorkAiPopover = true"
                @mouseleave="showWorkAiPopover = false"
                @focusin="showWorkAiPopover = true"
                @focusout="showWorkAiPopover = false"
              >
                <span class="ai-assistant-inline__icon" aria-hidden="true">✨</span>
                <span class="sr-only">{{ $t("systemThinking.srAiAssistant") }}</span>
                <div v-show="showWorkAiPopover" class="ai-popover ai-popover--work" role="tooltip">
                  <p v-html="$t('systemThinking.workAiPopover1')" />
                  <p>{{ $t("systemThinking.workAiPopover2") }}</p>
                  <p>{{ $t("systemThinking.workAiPopover3") }}</p>
                </div>
              </div>
              <button type="button" class="toolbar-btn toolbar-btn--primary" :disabled="exportingPdf" @click="exportPdf">
                {{ exportingPdf ? $t("systemThinking.exportingPdf") : $t("systemThinking.savePdf") }}
              </button>
            </div>
            <button type="button" class="modal-close-inline" @click="closeIcebergModal" :aria-label="$t('systemThinking.closeAria')">✕</button>
          </div>
        </header>

        <p class="progress-line">
          {{ $t("systemThinking.progressFilled") }} <strong>{{ filledDraftCount }} / 5</strong>
          <span v-if="saveStatus === 'saving'" class="save-pill">{{ $t("systemThinking.saveSaving") }}</span>
          <span v-else-if="saveStatus === 'saved'" class="save-pill save-pill--ok">{{ $t("systemThinking.saveSaved") }}</span>
        </p>

        <div class="iceberg-level-nav">
          <button
            v-for="lvl in levelDefinitions"
            :key="lvl.id"
            type="button"
            class="level-tab"
            :class="{
              active: selectedLevel === lvl.id,
              filled: !!(draft[lvl.id] && draft[lvl.id].trim())
            }"
            @click="selectLevel(lvl.id)"
          >
            <span class="level-tab__num">{{ lvl.order }}</span>
            {{ lvl.shortTitle }}
          </button>
        </div>

        <div class="iceberg-editor">
          <p class="level-question">{{ currentLevelDef.question }}</p>
          <p class="level-hint">{{ currentLevelDef.description }}</p>

          <div class="input-wrapper textarea-wrapper">
            <span class="input-icon" aria-hidden="true">✍️</span>
            <textarea
              v-model="draft[selectedLevel]"
              rows="6"
              class="modern-input modern-textarea"
              :class="{ 'has-value': draft[selectedLevel] }"
              :aria-label="$t('systemThinking.levelTextAria', { title: currentLevelDef.title })"
              @input="scheduleSave"
            />
            <label class="floating-label">{{ $t("systemThinking.floatingAnswerLabel", { title: currentLevelDef.title }) }}</label>
          </div>

          <div class="editor-actions">
            <button type="button" class="secondary-btn" :disabled="loading" @click="submitAiAnswer">
              {{ loading ? $t("systemThinking.aiProcessing") : $t("systemThinking.aiHelp") }}
            </button>
          </div>

          <div v-if="aiQuestionText" class="question-block question-block--soft">
            <div class="question-text">{{ aiQuestionText }}</div>
          </div>

          <div v-if="suggestions.length" class="suggestions-block">
            <p class="suggestions-title">{{ $t("systemThinking.suggestionsTitle") }}</p>
            <div class="suggestions-list">
              <button v-for="(suggestion, index) in suggestions" :key="index" type="button" class="suggestion-btn" @click="applySuggestion(suggestion)">
                {{ suggestion }}
              </button>
            </div>
          </div>

        </div>

        <!-- Скрытый блок для PDF / печати -->
        <div ref="pdfRoot" class="pdf-root">
          <h1>{{ $t("systemThinking.title") }}</h1>
          <p class="pdf-meta">{{ $t("systemThinking.pdfMeta", { id: currentIceberg.id, date: pdfExportDate }) }}</p>
          <div v-for="lvl in levelDefinitions" :key="'p-' + lvl.id" class="pdf-section">
            <h2>{{ lvl.order }}. {{ lvl.title }}</h2>
            <p class="pdf-q">{{ lvl.question }}</p>
            <p class="pdf-body">{{ draft[lvl.id] || $t("systemThinking.pdfEmpty") }}</p>
          </div>
          <template v-if="currentIceberg.solutions && currentIceberg.solutions.length">
            <h2>{{ $t("systemThinking.solutionsTitle") }}</h2>
            <div v-for="(solution, index) in currentIceberg.solutions" :key="index" class="pdf-section">
              <h3>{{ solution.title }}</h3>
              <p class="pdf-body">{{ solution.text }}</p>
            </div>
          </template>
        </div>

        <div v-if="currentIceberg.solutions && currentIceberg.solutions.length" class="solutions-block">
          <div class="solutions-header">
            <h3>{{ $t("systemThinking.solutionsTitle") }}</h3>
          </div>
          <div v-for="(solution, index) in currentIceberg.solutions" :key="index" class="solution-card">
            <h4>{{ solution.title }}</h4>
            <p>{{ solution.text }}</p>
          </div>
        </div>

        <div v-if="canGenerateSolutions" class="generate-solutions-block">
          <button type="button" class="generate-btn" :disabled="generatingSolutions" @click="generateSolutions">
            {{ generatingSolutions ? $t("systemThinking.generatingSolutions") : $t("systemThinking.generateSolutions") }}
          </button>
          <p class="gen-hint">{{ $t("systemThinking.genHint") }}</p>
        </div>
      </div>
    </div>

    <!-- Модалка «Подсказка» -->
    <div v-if="showHelpModal" class="modal-overlay" @click.self="showHelpModal = false">
      <div class="modal-content modal-content--wide">
        <button type="button" class="modal-close-top" @click="showHelpModal = false" :aria-label="$t('systemThinking.closeAria')">✕</button>
        <h2>{{ $t("systemThinking.helpModalTitle") }}</h2>
        <article v-for="lvl in levelDefinitions" :key="'h-' + lvl.id" class="help-card">
          <h3>{{ lvl.order }}. {{ lvl.title }}</h3>
          <p><strong>{{ $t("systemThinking.helpQuestion") }}</strong> {{ lvl.question }}</p>
          <p><strong>{{ $t("systemThinking.helpExample") }}</strong> {{ lvl.description }}</p>
        </article>
        <div class="modal-actions">
          <button type="button" class="save-btn" @click="showHelpModal = false">{{ $t("systemThinking.helpOk") }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import html2canvas from "html2canvas";
import { jsPDF } from "jspdf";

const LEVEL_META = [
  { id: "event", order: 1 },
  { id: "pattern", order: 2 },
  { id: "system_structure", order: 3 },
  { id: "mental_model", order: 4 },
  { id: "experience", order: 5 }
];

const LEVEL_IDS = LEVEL_META.map((m) => m.id);

const SCENARIO_KEYS = ["deadlines", "meetings", "quality"];

function authHeaders() {
  const token = localStorage.getItem("token");
  const h = { "Content-Type": "application/json" };
  if (token) h.Authorization = `Bearer ${token}`;
  return h;
}

function emptyDraft() {
  return {
    event: "",
    pattern: "",
    system_structure: "",
    mental_model: "",
    experience: ""
  };
}

export default {
  name: "SystemThinkingIceberg",
  data() {
    return {
      introExpanded: false,
      icebergs: [],
      showCreateForm: false,
      showCreateAiPopover: false,
      showIcebergModal: false,
      showHelpModal: false,
      showWorkAiPopover: false,
      currentIceberg: null,
      newEvent: "",
      creating: false,
      selectedLevel: "event",
      draft: emptyDraft(),
      saveTimer: null,
      saveStatus: "idle",
      aiQuestionText: "",
      suggestions: [],
      loading: false,
      generatingSolutions: false,
      exportingPdf: false,
      pdfExportDate: "",
      aiUsageRemaining: null
    };
  },
  computed: {
    levelDefinitions() {
      return LEVEL_META.map(({ id, order }) => ({
        id,
        order,
        title: this.$t(`systemThinking.levels.${id}.title`),
        shortTitle: this.$t(`systemThinking.levels.${id}.shortTitle`),
        question: this.$t(`systemThinking.levels.${id}.question`),
        description: this.$t(`systemThinking.levels.${id}.description`)
      }));
    },
    scenarioPresets() {
      return SCENARIO_KEYS.map((key) => ({
        label: this.$t(`systemThinking.scenarios.${key}.label`),
        text: this.$t(`systemThinking.scenarios.${key}.text`)
      }));
    },
    currentLevelDef() {
      return this.levelDefinitions.find((l) => l.id === this.selectedLevel) || this.levelDefinitions[0];
    },
    filledDraftCount() {
      return LEVEL_IDS.filter((id) => (this.draft[id] || "").trim()).length;
    },
    canGenerateSolutions() {
      return this.filledDraftCount === 5 && !(this.currentIceberg && this.currentIceberg.solutions && this.currentIceberg.solutions.length);
    }
  },
  watch: {
    selectedLevel() {
      this.aiQuestionText = "";
      this.suggestions = [];
      this.scheduleSave();
    }
  },
  mounted() {
    this.fetchIcebergs();
    this.fetchAiUsage();
    window.addEventListener("beforeunload", this.onBeforeUnload);
  },
  beforeUnmount() {
    window.removeEventListener("beforeunload", this.onBeforeUnload);
    if (this.saveTimer) clearTimeout(this.saveTimer);
  },
  methods: {
    fillCount(iceberg) {
      return LEVEL_IDS.filter((id) => (iceberg[id] || "").trim()).length;
    },
    openCreateFlow() {
      this.newEvent = "";
      this.showCreateForm = true;
    },
    applyScenario(s) {
      this.newEvent = s.text;
    },
    applySuggestion(text) {
      this.draft[this.selectedLevel] = text;
      this.suggestions = [];
      this.scheduleSave();
    },
    selectLevel(id) {
      this.selectedLevel = id;
    },
    onBeforeUnload() {
      if (this.showIcebergModal && this.currentIceberg) {
        this.flushSaveKeepalive();
      }
    },
    async fetchIcebergs() {
      try {
        const res = await fetch("/api/system-thinking", { headers: authHeaders() });
        if (res.ok) this.icebergs = await res.json();
      } catch (err) {
        console.error(err);
      }
    },
    async fetchAiUsage() {
      try {
        const res = await fetch("/api/ai-usage", { headers: authHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        this.aiUsageRemaining = data.remaining;
      } catch (err) {
        console.error(err);
      }
    },
    async createIceberg() {
      if (!this.newEvent.trim()) return;
      this.creating = true;
      try {
        const res = await fetch("/api/system-thinking", {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ event: this.newEvent })
        });
        if (!res.ok) {
          alert(this.$t("systemThinking.alertCreateError"));
          return;
        }
        const iceberg = await res.json();
        this.showCreateForm = false;
        this.newEvent = "";
        await this.fetchIcebergs();
        await this.openIceberg(iceberg);
      } catch (err) {
        console.error(err);
        alert(this.$t("systemThinking.alertConnectionError"));
      } finally {
        this.creating = false;
      }
    },
    syncDraftFromIceberg(iceberg) {
      const d = emptyDraft();
      LEVEL_IDS.forEach((id) => {
        d[id] = iceberg[id] || "";
      });
      this.draft = d;
    },
    async openIceberg(iceberg) {
      try {
        const res = await fetch(`/api/system-thinking/${iceberg.id}`, { headers: authHeaders() });
        if (!res.ok) {
          alert(this.$t("systemThinking.alertLoadIcebergError"));
          return;
        }
        this.currentIceberg = await res.json();
        this.syncDraftFromIceberg(this.currentIceberg);
        const cl = this.currentIceberg.current_level;
        this.selectedLevel = LEVEL_IDS.includes(cl) ? cl : "event";
        this.showIcebergModal = true;
        this.aiQuestionText = "";
        this.suggestions = [];
      } catch (err) {
        console.error(err);
        alert(this.$t("systemThinking.alertLoadError"));
      }
    },
    scheduleSave() {
      if (!this.currentIceberg) return;
      if (this.saveTimer) clearTimeout(this.saveTimer);
      this.saveTimer = setTimeout(() => this.flushSave(), 800);
    },
    async flushSave() {
      if (!this.currentIceberg) return;
      this.saveStatus = "saving";
      try {
        const res = await fetch(`/api/system-thinking/${this.currentIceberg.id}/save-state`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            fields: { ...this.draft },
            active_level: this.selectedLevel
          })
        });
        if (res.ok) {
          this.currentIceberg = await res.json();
          this.syncDraftFromIceberg(this.currentIceberg);
          this.saveStatus = "saved";
          setTimeout(() => {
            if (this.saveStatus === "saved") this.saveStatus = "idle";
          }, 2000);
        } else {
          this.saveStatus = "idle";
        }
      } catch (e) {
        console.error(e);
        this.saveStatus = "idle";
      }
    },
    flushSaveKeepalive() {
      if (!this.currentIceberg) return;
      const body = JSON.stringify({
        fields: { ...this.draft },
        active_level: this.selectedLevel
      });
      const token = localStorage.getItem("token");
      const headers = { "Content-Type": "application/json" };
      if (token) headers.Authorization = `Bearer ${token}`;
      fetch(`/api/system-thinking/${this.currentIceberg.id}/save-state`, {
        method: "POST",
        headers,
        body,
        keepalive: true
      }).catch(() => {});
    },
    async closeIcebergModal() {
      await this.flushSave();
      this.showIcebergModal = false;
      this.currentIceberg = null;
      await this.fetchIcebergs();
    },
    async submitAiAnswer() {
      if (!this.currentIceberg) return;
      const response = (this.draft[this.selectedLevel] || "").trim() || this.$t("systemThinking.dontKnow");
      this.loading = true;
      try {
        const questionRes = await fetch(`/api/system-thinking/${this.currentIceberg.id}/ask-question`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            response: "",
            level: this.selectedLevel
          })
        });
        if (questionRes.ok) {
          const questionData = await questionRes.json();
          this.aiQuestionText = questionData.question || this.aiQuestionText;
        }

        const suggestionsRes = await fetch(`/api/system-thinking/${this.currentIceberg.id}/ask-question`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({
            response,
            level: this.selectedLevel
          })
        });
        const data = await suggestionsRes.json();
        if (!suggestionsRes.ok) {
          alert(data.error || this.$t("systemThinking.alertGenericError"));
          return;
        }
        if (data.suggestions && data.suggestions.length) {
          this.suggestions = data.suggestions;
          this.aiQuestionText = data.question || this.aiQuestionText;
        } else if (data.iceberg) {
          this.currentIceberg = data.iceberg;
          this.syncDraftFromIceberg(data.iceberg);
          this.suggestions = [];
        }
        await this.fetchAiUsage();
      } catch (e) {
        console.error(e);
        alert(this.$t("systemThinking.alertConnectionError"));
      } finally {
        this.loading = false;
      }
    },
    async generateSolutions() {
      if (!this.currentIceberg) return;
      await this.flushSave();
      this.generatingSolutions = true;
      try {
        const res = await fetch(`/api/system-thinking/${this.currentIceberg.id}/generate-solutions`, {
          method: "POST",
          headers: authHeaders()
        });
        const data = await res.json();
        if (!res.ok) {
          alert(data.error || this.$t("systemThinking.alertGenSolutionsError"));
          return;
        }
        this.currentIceberg = data.iceberg || this.currentIceberg;
        if (data.solutions) this.currentIceberg.solutions = data.solutions;
        await this.fetchAiUsage();
      } catch (e) {
        console.error(e);
        alert(this.$t("systemThinking.alertConnectionError"));
      } finally {
        this.generatingSolutions = false;
      }
    },
    async deleteIceberg(id) {
      if (!confirm(this.$t("systemThinking.confirmDelete"))) return;
      try {
        const res = await fetch(`/api/system-thinking/${id}`, {
          method: "DELETE",
          headers: authHeaders()
        });
        if (res.ok) {
          await this.fetchIcebergs();
          if (this.currentIceberg && this.currentIceberg.id === id) {
            this.showIcebergModal = false;
            this.currentIceberg = null;
          }
        }
      } catch (e) {
        console.error(e);
      }
    },
    async exportPdf() {
      if (!this.$refs.pdfRoot || !this.currentIceberg) return;
      this.exportingPdf = true;
      const loc = typeof this.$i18n.locale === "string" ? this.$i18n.locale : this.$i18n.locale.value;
      this.pdfExportDate = new Date().toLocaleString(loc === "en" ? "en-US" : "ru-RU");
      await this.$nextTick();
      try {
        const el = this.$refs.pdfRoot;
        const canvas = await html2canvas(el, { scale: 2, useCORS: true, logging: false });
        const imgData = canvas.toDataURL("image/png", 0.92);
        const pdf = new jsPDF({ orientation: "p", unit: "mm", format: "a4" });
        const pageW = pdf.internal.pageSize.getWidth();
        const pageH = pdf.internal.pageSize.getHeight();
        const margin = 10;
        const imgW = pageW - margin * 2;
        const imgH = (canvas.height * imgW) / canvas.width;
        let heightLeft = imgH;
        let y = margin;
        pdf.addImage(imgData, "PNG", margin, y, imgW, imgH);
        heightLeft -= pageH - margin * 2;
        while (heightLeft > 1) {
          y = heightLeft - imgH + margin;
          pdf.addPage();
          pdf.addImage(imgData, "PNG", margin, y, imgW, imgH);
          heightLeft -= pageH - margin * 2;
        }
        pdf.save(`iceberg-${this.currentIceberg.id}.pdf`);
      } catch (e) {
        console.error(e);
        alert(this.$t("systemThinking.alertPdfError"));
      } finally {
        this.exportingPdf = false;
      }
    }
  }
};
</script>

<style scoped>
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.iceberg-container {
  max-width: 1280px;
  margin: 40px auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 24px;
  color: #1a1a1a;
}

.ai-usage-line {
  margin: -10px 0 20px;
  color: #475569;
  font-size: 14px;
}

.iceberg-intro {
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #f0f9ff 0%, #ecfeff 100%);
  border-radius: 16px;
  border: 1px solid #bae6fd;
}

.iceberg-intro__title {
  font-size: 1.25rem;
  margin: 0 0 12px;
  color: #0c4a6e;
}

.iceberg-intro__lead {
  margin: 0 0 16px;
  line-height: 1.6;
  color: #334155;
  font-size: 15px;
}

.iceberg-intro__toggle {
  background: #fff;
  border: 2px solid #0ea5e9;
  color: #0369a1;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  font-size: 14px;
}

.iceberg-intro__levels {
  margin-top: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.iceberg-intro__level-card {
  background: #fff;
  padding: 16px 18px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.iceberg-intro__level-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
  color: #0f172a;
  display: flex;
  align-items: center;
  gap: 10px;
}

.iceberg-intro__badge {
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

.iceberg-intro__q {
  margin: 0 0 8px;
  font-size: 14px;
  color: #334155;
}

.iceberg-intro__ex {
  margin: 0;
  font-size: 14px;
  color: #64748b;
  line-height: 1.55;
}

.filter-bar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 24px;
  border-bottom: 1px solid #e5e7eb;
}

.add-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.add-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.iceberg-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 24px;
}

.iceberg-card {
  background: #ffffff;
  padding: 24px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
}

.iceberg-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.iceberg-card h3 {
  font-size: 18px;
  font-weight: 600;
  margin-bottom: 12px;
  color: #111827;
}

.iceberg-card p {
  font-size: 14px;
  color: #6b7280;
  margin: 8px 0;
  line-height: 1.6;
}

.solutions-badge {
  display: inline-block;
  background: #10b981;
  color: white;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  margin-top: 12px;
}

.delete-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 12px;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #ffffff;
  padding: 40px;
  border-radius: 20px;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-content--wide {
  max-width: 720px;
}

.iceberg-modal {
  max-width: 920px;
}

.textarea-wrapper--stacked {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stacked-field-label {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  line-height: 1.4;
}

.textarea-with-icon {
  position: relative;
}

.textarea-with-icon .input-icon--stacked {
  position: absolute;
  left: 16px;
  top: 14px;
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
}

.modern-textarea--stacked {
  padding: 14px 16px 14px 52px;
  min-height: 120px;
}

.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.84);
  cursor: pointer;
  font-size: 18px;
  z-index: 3;
}

.create-lead {
  color: #475569;
  line-height: 1.55;
  margin-bottom: 16px;
}

.create-toolbar {
  margin-bottom: 16px;
}

.ai-assistant-badge {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  color: #5b21b6;
  cursor: default;
}

.ai-assistant-badge__icon {
  font-size: 20px;
}

.ai-assistant-inline {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: linear-gradient(135deg, #ede9fe 0%, #e0e7ff 100%);
  cursor: help;
}

.ai-assistant-inline__icon {
  font-size: 22px;
}

.ai-popover {
  position: absolute;
  left: 0;
  top: 100%;
  margin-top: 8px;
  width: min(340px, 85vw);
  padding: 14px 16px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  font-size: 13px;
  font-weight: 400;
  color: #334155;
  line-height: 1.5;
  z-index: 20;
}

.ai-popover p {
  margin: 0 0 8px;
}

.ai-popover p:last-child {
  margin-bottom: 0;
}

.ai-popover--work {
  left: auto;
  right: 0;
}

.scenarios-title {
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  margin-bottom: 10px;
}

.scenario-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.scenario-chip {
  border: 2px solid #e5e7eb;
  background: #fff;
  padding: 10px 16px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
  transition: border-color 0.2s, background 0.2s;
}

.scenario-chip:hover {
  border-color: #10b981;
  background: #ecfdf5;
}

.iceberg-work-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 8px;
}

.iceberg-work-header h2 {
  margin: 0;
  font-size: 1.35rem;
  flex: 1;
  min-width: min(100%, 200px);
}

.iceberg-work-header__right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.iceberg-work-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.modal-close-inline {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.84);
  cursor: pointer;
  font-size: 18px;
  flex-shrink: 0;
  line-height: 1;
}

.modal-close-inline:hover {
  background: rgba(10, 20, 45, 0.14);
}

.toolbar-btn {
  border: 2px solid #e5e7eb;
  background: #fff;
  padding: 8px 14px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 13px;
  cursor: pointer;
  color: #374151;
}

.toolbar-btn--primary {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1d4ed8;
}

.progress-line {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px;
}

.save-pill {
  margin-left: 10px;
  font-size: 12px;
  color: #94a3b8;
}

.save-pill--ok {
  color: #059669;
}

.iceberg-level-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
}

.level-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: 2px solid #e5e7eb;
  background: #f8fafc;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  transition: all 0.2s;
}

.level-tab.active {
  border-color: #3b82f6;
  background: #eff6ff;
  color: #1e40af;
}

.level-tab.filled:not(.active) {
  border-color: #86efac;
  background: #f0fdf4;
}

.level-tab__num {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #cbd5e1;
  color: #fff;
  font-size: 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.level-tab.active .level-tab__num {
  background: #3b82f6;
}

.level-tab.filled .level-tab__num {
  background: #22c55e;
}

.iceberg-editor {
  margin-bottom: 24px;
}

.level-question {
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 8px;
  line-height: 1.45;
}

.level-hint {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 16px;
  line-height: 1.55;
  padding: 12px 14px;
  background: #f8fafc;
  border-radius: 10px;
  border-left: 4px solid #94a3b8;
}

.secondary-btn {
  border: 2px solid #cbd5e1;
  background: #fff;
  padding: 10px 18px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  color: #334155;
}

.editor-actions {
  margin-top: 12px;
}

.question-block--soft {
  margin-top: 16px;
  background: #f1f5f9;
}

.ai-answer-row {
  margin-top: 20px;
}

.modal-actions--tight {
  margin-top: 12px;
  padding-top: 12px;
  border-top: none;
}

.pdf-root {
  position: fixed;
  left: -9999px;
  top: 0;
  width: 794px;
  padding: 32px;
  background: #fff;
  font-family: Arial, sans-serif;
  color: #111;
}

.pdf-root h1 {
  font-size: 22px;
  margin-bottom: 8px;
}

.pdf-meta {
  font-size: 12px;
  color: #666;
  margin-bottom: 24px;
}

.pdf-section {
  margin-bottom: 20px;
  page-break-inside: avoid;
}

.pdf-section h2 {
  font-size: 16px;
  margin: 0 0 6px;
}

.pdf-q {
  font-size: 12px;
  color: #555;
  margin: 0 0 8px;
}

.pdf-body {
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  white-space: pre-wrap;
}

.help-card {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 14px;
}

.help-card h3 {
  margin: 0 0 10px;
  font-size: 16px;
}

.help-card p {
  margin: 6px 0;
  font-size: 14px;
  line-height: 1.5;
  color: #475569;
}

.gen-hint {
  font-size: 13px;
  color: #64748b;
  margin-top: 8px;
}

.iceberg-visualization {
  margin: 32px 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.question-block {
  margin-top: 32px;
  padding: 24px;
  background: #f9fafb;
  border-radius: 12px;
}

.question-text {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  border-left: 4px solid #3b82f6;
}

.suggestions-block {
  margin-bottom: 24px;
}

.suggestions-title {
  font-weight: 600;
  color: #374151;
  margin-bottom: 12px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-btn {
  background: white;
  border: 2px solid #e5e7eb;
  padding: 12px 16px;
  border-radius: 8px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  color: #374151;
}

.suggestion-btn:hover {
  border-color: #3b82f6;
  background: #eff6ff;
}

.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 24px;
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: inherit;
  transition: all 0.3s ease;
  background: white;
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
}

.modern-textarea {
  padding-top: 32px;
  min-height: 100px;
  resize: vertical;
  line-height: 1.6;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 32px;
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s ease;
  z-index: 1;
}

.modern-input:focus,
.modern-input.has-value {
  border-color: #3b82f6;
  outline: none;
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
}

.modal-actions {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.generate-btn {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.save-btn {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.solutions-block {
  margin-top: 32px;
  padding: 24px;
  background: #f0fdf4;
  border-radius: 12px;
  border: 2px solid #10b981;
}

.solutions-header h3 {
  font-size: 20px;
  font-weight: 700;
  color: #059669;
  margin: 0 0 16px;
}

.solution-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 16px;
  border-left: 4px solid #10b981;
}

.solution-card h4 {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  margin-bottom: 12px;
}

.solution-card p {
  font-size: 14px;
  color: #4b5563;
  line-height: 1.6;
  margin: 0;
}

.generate-solutions-block {
  margin-top: 24px;
  text-align: center;
}

@media (max-width: 768px) {
  .iceberg-container {
    margin: 20px 10px;
    padding: 20px;
  }

  .iceberg-list {
    grid-template-columns: 1fr;
  }

  .modal-content {
    padding: 24px 20px;
    max-width: 100%;
  }
}
</style>
