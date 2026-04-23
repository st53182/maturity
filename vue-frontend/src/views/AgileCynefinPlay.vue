<template>
  <div class="cp-play">
    <!-- Переключатель языка (всегда виден) -->
    <div class="cp-lang" role="group" :aria-label="$t('agileTraining.common.language')" v-if="!loading">
      <button type="button" class="cp-lang__btn" :class="{ 'cp-lang__btn--active': $i18n.locale === 'ru' }" @click="switchLang('ru')">RU</button>
      <button type="button" class="cp-lang__btn" :class="{ 'cp-lang__btn--active': $i18n.locale === 'en' }" @click="switchLang('en')">EN</button>
    </div>

    <!-- Загрузка -->
    <div v-if="loading" class="cp-loading">
      <div class="cp-loading__spin" />
      <div>{{ $t('common.loading') }}…</div>
    </div>

    <!-- Ошибка -->
    <div v-else-if="error" class="cp-error">
      <h1>{{ $t('agileTraining.play.loadError') || 'Не удалось загрузить тренинг' }}</h1>
      <p>{{ error }}</p>
    </div>

    <!-- Экран 1: старт -->
    <section v-else-if="stage === 'start'" class="cp-start">
      <div class="cp-start__badge">🧭 Cynefin</div>
      <h1 class="cp-start__title">{{ group.name }}</h1>
      <p class="cp-start__lead">{{ $t('agileTraining.cynefin.play.startLead') }}</p>
      <ul class="cp-start__how">
        <li>{{ $t('agileTraining.cynefin.play.how1') }}</li>
        <li>{{ $t('agileTraining.cynefin.play.how2') }}</li>
        <li>{{ $t('agileTraining.cynefin.play.how3') }}</li>
      </ul>
      <button class="cp-btn cp-btn--primary" @click="startPlay" :disabled="starting">
        {{ $t('agileTraining.cynefin.play.startBtn') }}
      </button>
    </section>

    <!-- Экран 2+3: кейс + выбор домена -->
    <section v-else-if="stage === 'case' || stage === 'domain'" class="cp-case">
      <div class="cp-case__progress">
        <span>{{ currentIndex + 1 }} / {{ cases.length }}</span>
        <div class="cp-case__bar">
          <div class="cp-case__bar-fill" :style="{ width: progressPercent + '%' }" />
        </div>
      </div>

      <article class="cp-case__card" :draggable="stage === 'domain'" @dragstart="onCaseDragStart">
        <div class="cp-case__cat">{{ currentCase.category }}</div>
        <h2 class="cp-case__title">{{ currentCase.title }}</h2>
        <p class="cp-case__scenario">{{ currentCase.scenario }}</p>
        <div v-if="stage === 'case'" class="cp-case__actions">
          <button class="cp-btn cp-btn--primary" @click="stage = 'domain'">
            {{ $t('agileTraining.cynefin.play.chooseDomainBtn') }} →
          </button>
        </div>
      </article>

      <div v-if="stage === 'domain'" class="cp-domains">
        <p class="cp-domains__lead">
          {{ $t('agileTraining.cynefin.play.dropHint') }}
        </p>
        <div class="cp-domains__grid">
          <button
            v-for="dk in DOMAIN_KEYS"
            :key="dk"
            class="cp-domain"
            :class="['cp-domain--' + dk, { 'cp-domain--over': dragOverDomain === dk, 'cp-domain--chosen': selectedDomain === dk }]"
            @click="chooseDomain(dk)"
            @dragover.prevent="dragOverDomain = dk"
            @dragleave="dragOverDomain = (dragOverDomain === dk ? '' : dragOverDomain)"
            @drop.prevent="chooseDomain(dk)"
          >
            <span class="cp-domain__icon">{{ domainIcon(dk) }}</span>
            <span class="cp-domain__name">{{ $t('agileTraining.cynefin.domain.' + dk) }}</span>
            <span class="cp-domain__short">{{ $t('agileTraining.cynefin.domainShort.' + dk) }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Экран 4: выбор стратегии -->
    <section v-else-if="stage === 'strategy'" class="cp-strategy">
      <div class="cp-strategy__head">
        <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + selectedDomain]">
          {{ $t('agileTraining.cynefin.domain.' + selectedDomain) }}
        </span>
        <h2>{{ $t('agileTraining.cynefin.play.strategyTitle') }}</h2>
        <p class="cp-strategy__lead">{{ $t('agileTraining.cynefin.play.strategyLead') }}</p>
      </div>
      <div class="cp-strategy__list">
        <button
          v-for="s in strategiesForDomain"
          :key="s.key"
          class="cp-strategy__item"
          :class="{ 'cp-strategy__item--chosen': selectedStrategyKey === s.key }"
          @click="selectedStrategyKey = s.key; customStrategyText = ''"
        >
          <span class="cp-strategy__bullet">◆</span>
          <span>{{ s.label }}</span>
        </button>
        <div class="cp-strategy__custom">
          <label>{{ $t('agileTraining.cynefin.play.customStrategyLabel') }}</label>
          <textarea
            v-model="customStrategyText"
            :placeholder="$t('agileTraining.cynefin.play.customStrategyPlaceholder')"
            maxlength="1000"
            @focus="selectedStrategyKey = ''"
          />
        </div>
      </div>
      <div class="cp-strategy__actions">
        <button class="cp-btn cp-btn--ghost" @click="stage = 'domain'">← {{ $t('common.back') }}</button>
        <button class="cp-btn cp-btn--primary"
                :disabled="saving || (!selectedStrategyKey && !customStrategyText.trim())"
                @click="submitAnswer">
          {{ saving ? $t('common.loading') + '…' : $t('agileTraining.cynefin.play.submitBtn') }}
        </button>
      </div>
    </section>

    <!-- Экран 5: дебриф -->
    <section v-else-if="stage === 'debrief'" class="cp-debrief">
      <div class="cp-debrief__top">
        <span :class="[
          'cp-debrief__match',
          matchedExpert ? 'cp-debrief__match--yes' : 'cp-debrief__match--no'
        ]">
          {{ matchedExpert
             ? $t('agileTraining.cynefin.play.matchYes')
             : $t('agileTraining.cynefin.play.matchNo') }}
        </span>
        <h2>{{ currentCase.title }}</h2>
      </div>

      <div class="cp-debrief__pair">
        <div class="cp-debrief__col">
          <div class="cp-debrief__col-hdr">{{ $t('agileTraining.cynefin.play.yourChoice') }}</div>
          <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + selectedDomain]">
            {{ $t('agileTraining.cynefin.domain.' + selectedDomain) }}
          </span>
          <div class="cp-debrief__strategy" v-if="chosenStrategyLabel">
            <b>→</b> {{ chosenStrategyLabel }}
          </div>
        </div>
        <div class="cp-debrief__col">
          <div class="cp-debrief__col-hdr">{{ $t('agileTraining.cynefin.expertDomain') }}</div>
          <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + debrief.expert_domain]">
            {{ $t('agileTraining.cynefin.domain.' + debrief.expert_domain) }}
          </span>
        </div>
      </div>

      <div class="cp-debrief__rationale">
        <b>💡 {{ $t('agileTraining.cynefin.play.rationale') }}</b>
        <p>{{ debrief.expert_rationale }}</p>
      </div>

      <div class="cp-debrief__cons">
        <h3>{{ $t('agileTraining.cynefin.play.consequences') }}</h3>
        <div v-for="dk in DOMAIN_KEYS" :key="dk" class="cp-debrief__cons-item"
             :class="{ 'cp-debrief__cons-item--expert': dk === debrief.expert_domain }">
          <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + dk]">
            {{ $t('agileTraining.cynefin.domain.' + dk) }}
          </span>
          <p>{{ (debrief.consequences || {})[dk] }}</p>
        </div>
      </div>

      <div class="cp-debrief__stats">
        <h3>📊 {{ $t('agileTraining.cynefin.play.groupStats') }}</h3>
        <div class="cyn-bars">
          <div v-for="dk in DOMAIN_KEYS" :key="dk" class="cyn-bars__row">
            <div class="cyn-bars__label">{{ $t('agileTraining.cynefin.domain.' + dk) }}</div>
            <div class="cyn-bars__track">
              <div class="cyn-bars__fill"
                   :class="{ 'cyn-bars__fill--expert': dk === debrief.expert_domain }"
                   :style="{ width: (groupStats.percent[dk] || 0) + '%' }" />
            </div>
            <div class="cyn-bars__val">{{ groupStats.percent[dk] || 0 }}%</div>
          </div>
        </div>
        <p class="cp-debrief__stats-hint">
          {{ $t('agileTraining.cynefin.play.groupStatsHint', { n: groupStats.total || 0 }) }}
        </p>
      </div>

      <div class="cp-debrief__actions">
        <button v-if="currentIndex + 1 < cases.length"
                class="cp-btn cp-btn--primary" @click="nextCase">
          {{ $t('agileTraining.cynefin.play.nextCaseBtn') }} →
        </button>
        <button v-else class="cp-btn cp-btn--primary" @click="goToResults">
          {{ $t('agileTraining.cynefin.play.resultsBtn') }} →
        </button>
      </div>
    </section>

    <!-- Экран 7: результаты -->
    <section v-else-if="stage === 'results'" class="cp-results">
      <header class="cp-results__head">
        <h1>🏁 {{ $t('agileTraining.cynefin.play.resultsTitle') }}</h1>
        <p>{{ $t('agileTraining.cynefin.play.resultsLead', { group: group.name }) }}</p>
      </header>

      <div v-if="resultsLoading" class="cp-loading">
        <div class="cp-loading__spin" />
        <div>{{ $t('common.loading') }}…</div>
      </div>
      <div v-else-if="results">
        <p class="cp-pdf-bar">
          <button
            type="button"
            class="cp-btn cp-btn--ghost"
            :disabled="pdfExporting"
            @click="exportResultsPdf"
          >
            {{ pdfExporting ? $t('agileTraining.common.downloadPdfLoading') : $t('agileTraining.common.downloadPdf') }}
          </button>
        </p>
        <div ref="pdfExportRoot" class="cp-pdf-root">
        <div class="cp-results__summary">
          <div class="cp-results__stat">
            <span class="cp-results__stat-val">{{ results.my.matches_expert }}/{{ results.per_case.length }}</span>
            <span class="cp-results__stat-lbl">{{ $t('agileTraining.cynefin.play.matchesExpert') }}</span>
          </div>
          <div class="cp-results__stat">
            <span class="cp-results__stat-val">{{ results.participants_count }}</span>
            <span class="cp-results__stat-lbl">{{ $t('agileTraining.cynefin.play.teamParticipants') }}</span>
          </div>
        </div>

        <h3>📈 {{ $t('agileTraining.cynefin.play.overallDomains') }}</h3>
        <div class="cyn-bars cp-results__overall">
          <div v-for="dk in DOMAIN_KEYS" :key="dk" class="cyn-bars__row">
            <div class="cyn-bars__label">{{ $t('agileTraining.cynefin.domain.' + dk) }}</div>
            <div class="cyn-bars__track">
              <div class="cyn-bars__fill"
                   :style="{ width: (results.overall_domain_percent[dk] || 0) + '%' }" />
            </div>
            <div class="cyn-bars__val">{{ results.overall_domain_percent[dk] || 0 }}%</div>
          </div>
        </div>

        <h3>🔥 {{ $t('agileTraining.cynefin.play.topControversial') }}</h3>
        <p class="cp-hint">{{ $t('agileTraining.cynefin.play.topControversialHint') }}</p>
        <ul class="cp-top-list">
          <li v-for="r in results.top_controversial" :key="r.key">
            <span>{{ r.title }}</span>
            <span class="cp-top-list__val">{{ r.controversy }}%</span>
          </li>
          <li v-if="!results.top_controversial.length" class="cp-hint">{{ $t('agileTraining.cynefin.play.noControversy') }}</li>
        </ul>

        <h3>📚 {{ $t('agileTraining.cynefin.play.allCases') }}</h3>
        <details open class="cp-all">
          <summary>{{ $t('agileTraining.cynefin.play.allCasesToggle') }}</summary>
          <ul class="cp-all__list">
            <li v-for="row in results.per_case" :key="row.key" class="cp-all__item">
              <div class="cp-all__head">
                <div>
                  <span class="cp-all__cat">{{ row.category }}</span>
                  <b>{{ row.title }}</b>
                </div>
                <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + row.expert_domain]">
                  {{ $t('agileTraining.cynefin.domain.' + row.expert_domain) }}
                </span>
              </div>
              <p class="cp-all__scenario">{{ row.scenario }}</p>
              <div class="cp-all__my" v-if="row.my_domain">
                <span class="cp-all__my-lbl">{{ $t('agileTraining.cynefin.play.yourChoice') }}:</span>
                <span :class="['cyn-dom-pill', 'cyn-dom-pill--' + row.my_domain]">
                  {{ $t('agileTraining.cynefin.domain.' + row.my_domain) }}
                </span>
                <span v-if="row.matches_expert" class="cp-all__match">✓</span>
                <span v-else class="cp-all__mismatch">✗</span>
              </div>
              <div class="cyn-bars cp-all__bars">
                <div v-for="dk in DOMAIN_KEYS" :key="dk" class="cyn-bars__row">
                  <div class="cyn-bars__label">{{ $t('agileTraining.cynefin.domain.' + dk) }}</div>
                  <div class="cyn-bars__track">
                    <div class="cyn-bars__fill"
                         :class="{ 'cyn-bars__fill--expert': dk === row.expert_domain }"
                         :style="{ width: (row.stats.percent[dk] || 0) + '%' }" />
                  </div>
                  <div class="cyn-bars__val">{{ row.stats.percent[dk] || 0 }}%</div>
                </div>
              </div>
            </li>
          </ul>
        </details>
        </div>

        <div class="cp-results__actions">
          <button class="cp-btn cp-btn--ghost" @click="restart">{{ $t('agileTraining.cynefin.play.restart') }}</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
/**
 * Игровой экран упражнения Cynefin.
 *
 * Жизненный цикл:
 *   start → case → domain → strategy → debrief → (next case → case…) → results
 *
 * Идентификация участника — по `participant_token` в localStorage
 * (`at_cynefin_pt_<slug>`), чтобы несколько упражнений не мешали друг другу.
 */
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';

const TOKEN_KEY_PREFIX = 'at_cynefin_pt_';
const LANG_KEY = 'language';

export default {
  name: 'AgileCynefinPlay',
  props: {
    slug: { type: String, default: null },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      DOMAIN_KEYS: ['obvious', 'complicated', 'complex', 'chaotic'],
      loading: true,
      starting: false,
      saving: false,
      error: '',
      // группа и сессия
      group: null,
      session: null,
      // контент
      cases: [],
      strategies: { obvious: [], complicated: [], complex: [], chaotic: [] },
      // прохождение
      stage: 'start',
      currentIndex: 0,
      answered: {}, // { case_key: { selected_domain, selected_strategy, custom_strategy } }
      selectedDomain: '',
      selectedStrategyKey: '',
      customStrategyText: '',
      dragOverDomain: '',
      // дебриф текущего кейса
      debrief: { expert_domain: '', expert_rationale: '', consequences: {} },
      groupStats: { total: 0, percent: {}, counts: {}, strategies: {} },
      // идентификация
      participantToken: '',
      // финальные результаты
      results: null,
      resultsLoading: false,
      pdfExporting: false,
    };
  },
  computed: {
    effectiveSlug() { return this.slug || this.$route?.params?.slug; },
    currentCase() { return this.cases[this.currentIndex] || {}; },
    strategiesForDomain() { return this.strategies[this.selectedDomain] || []; },
    progressPercent() {
      if (!this.cases.length) return 0;
      return Math.round(100 * this.currentIndex / this.cases.length);
    },
    matchedExpert() {
      return this.selectedDomain && this.debrief && this.selectedDomain === this.debrief.expert_domain;
    },
    chosenStrategyLabel() {
      if (this.customStrategyText && this.customStrategyText.trim()) return this.customStrategyText.trim();
      const list = this.strategiesForDomain;
      const found = list.find(s => s.key === this.selectedStrategyKey);
      return found ? found.label : '';
    },
  },
  async mounted() {
    await this.loadAll();
  },
  methods: {
    _tokenKey() { return TOKEN_KEY_PREFIX + this.effectiveSlug; },
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem(LANG_KEY, lang); } catch (_) { /* ignore */ }
      // Перезагрузим контент на новом языке.
      this.reloadContent();
    },
    async loadAll() {
      this.loading = true;
      this.error = '';
      try {
        const groupRes = this.prefetchedSession
          ? Promise.resolve({ data: { group: null, session: this.prefetchedSession } })
          : axios.get(`/api/agile-training/g/${this.effectiveSlug}`);

        const [g1] = await Promise.all([groupRes]);
        // Если prefetchedSession — всё равно дёрнем полноценный /g/<slug> чтобы
        // получить данные о группе.
        const groupData = this.prefetchedSession
          ? (await axios.get(`/api/agile-training/g/${this.effectiveSlug}`)).data
          : g1.data;
        this.group = groupData.group;
        this.session = groupData.session;

        // Если пользователь явно не выбирал язык — возьмём локаль сессии.
        if (!localStorage.getItem(LANG_KEY) && this.session?.locale) {
          this.$i18n.locale = this.session.locale;
        }

        await this.reloadContent();

        this.participantToken = localStorage.getItem(this._tokenKey()) || '';
        if (this.participantToken) {
          await this.loadState();
        }
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.loading = false;
      }
    },
    async reloadContent() {
      const locale = this.$i18n.locale || 'ru';
      try {
        const res = await axios.get('/api/agile-training/cynefin/content', { params: { locale } });
        this.cases = res.data.cases || [];
        this.strategies = res.data.strategies || {};
      } catch (e) {
        console.error('reloadContent', e);
      }
    },
    async loadState() {
      try {
        const res = await axios.get(`/api/agile-training/cynefin/g/${this.effectiveSlug}/state`, {
          params: { participant_token: this.participantToken },
        });
        this.answered = res.data.answered || {};
        // Автоматически перемотаем на первый неотвеченный кейс.
        const firstUnanswered = this.cases.findIndex(c => !this.answered[c.key]);
        if (firstUnanswered >= 0) {
          this.currentIndex = firstUnanswered;
        } else {
          this.currentIndex = Math.max(0, this.cases.length - 1);
        }
      } catch (e) {
        console.error('loadState', e);
      }
    },
    async startPlay() {
      if (!this.group) return;
      this.starting = true;
      try {
        if (!this.participantToken) {
          const res = await axios.post(`/api/agile-training/g/${this.effectiveSlug}/participant`, {});
          this.participantToken = res.data.participant_token;
          try { localStorage.setItem(this._tokenKey(), this.participantToken); } catch (_) { /* ignore */ }
          await this.loadState();
        }
        // Если есть неотвеченные кейсы — начинаем с них.
        const firstUnanswered = this.cases.findIndex(c => !this.answered[c.key]);
        if (firstUnanswered >= 0) {
          this.currentIndex = firstUnanswered;
          this.resetChoice();
          this.stage = 'case';
        } else {
          await this.goToResults();
        }
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to start');
      } finally {
        this.starting = false;
      }
    },
    resetChoice() {
      this.selectedDomain = '';
      this.selectedStrategyKey = '';
      this.customStrategyText = '';
      this.dragOverDomain = '';
    },
    onCaseDragStart(ev) {
      try {
        ev.dataTransfer.setData('text/plain', this.currentCase.key);
        ev.dataTransfer.effectAllowed = 'move';
      } catch (_) { /* ignore */ }
    },
    chooseDomain(dk) {
      this.selectedDomain = dk;
      this.dragOverDomain = '';
      this.stage = 'strategy';
    },
    domainIcon(dk) {
      return { obvious: '✅', complicated: '🧩', complex: '🌱', chaotic: '⚡' }[dk] || '•';
    },
    async submitAnswer() {
      if (!this.selectedDomain) return;
      this.saving = true;
      try {
        const payload = {
          participant_token: this.participantToken,
          case_key: this.currentCase.key,
          selected_domain: this.selectedDomain,
          selected_strategy: this.selectedStrategyKey || null,
          custom_strategy: this.customStrategyText.trim() || null,
          locale: this.$i18n.locale || 'ru',
        };
        const res = await axios.post(`/api/agile-training/cynefin/g/${this.effectiveSlug}/answer`, payload);
        this.answered[this.currentCase.key] = {
          selected_domain: this.selectedDomain,
          selected_strategy: this.selectedStrategyKey || null,
          custom_strategy: this.customStrategyText.trim() || null,
        };
        this.debrief = res.data.debrief || { expert_domain: '', expert_rationale: '', consequences: {} };
        this.groupStats = res.data.stats || { total: 0, percent: {}, counts: {}, strategies: {} };
        this.stage = 'debrief';
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.saving = false;
      }
    },
    nextCase() {
      if (this.currentIndex + 1 >= this.cases.length) {
        this.goToResults();
        return;
      }
      this.currentIndex += 1;
      this.resetChoice();
      this.stage = 'case';
    },
    async goToResults() {
      this.stage = 'results';
      this.resultsLoading = true;
      try {
        const res = await axios.get(`/api/agile-training/cynefin/g/${this.effectiveSlug}/results`, {
          params: { participant_token: this.participantToken, locale: this.$i18n.locale || 'ru' },
        });
        this.results = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load results');
      } finally {
        this.resultsLoading = false;
      }
    },
    async exportResultsPdf() {
      const el = this.$refs.pdfExportRoot;
      if (!el) return;
      this.pdfExporting = true;
      try {
        const res = await exportElementToPdf(el, `agile-cynefin-${this.effectiveSlug}`);
        if (!res.ok) throw new Error(res.error || 'export');
      } catch (e) {
        console.error(e);
        alert(this.$t('agileTraining.common.downloadPdfError'));
      } finally {
        this.pdfExporting = false;
      }
    },
    restart() {
      this.currentIndex = 0;
      this.resetChoice();
      this.stage = 'start';
      this.results = null;
    },
  },
};
</script>

<style scoped>
.cp-pdf-bar { margin: 0 0 12px; }
.cp-pdf-root { min-height: 20px; }
.cp-play {
  max-width: 720px;
  margin: 0 auto;
  padding: 16px 18px 60px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  color: #0f172a;
  min-height: 100vh;
  position: relative;
}
.cp-lang {
  position: absolute;
  top: 18px;
  right: 18px;
  display: inline-flex;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(15,23,42,0.05);
}
.cp-lang__btn {
  background: transparent; border: none; padding: 5px 12px; font-size: 12px;
  font-weight: 700; color: #475569; cursor: pointer; font-family: inherit; letter-spacing: 0.5px;
}
.cp-lang__btn--active { background: #7c3aed; color: #fff; }

.cp-loading { text-align: center; padding: 80px 20px; color: #64748b; }
.cp-loading__spin { width: 36px; height: 36px; border-radius: 50%; border: 3px solid #eee; border-top-color: #7c3aed; animation: cp-spin 0.9s linear infinite; margin: 0 auto 12px; }
@keyframes cp-spin { to { transform: rotate(360deg); } }
.cp-error { text-align: center; padding: 60px 20px; color: #b91c1c; }

/* Экран старта */
.cp-start { text-align: center; padding-top: 40px; }
.cp-start__badge {
  display: inline-block; padding: 4px 14px; border-radius: 999px;
  background: #ede9fe; color: #6d28d9; font-weight: 700; letter-spacing: 0.5px;
  font-size: 12px; margin-bottom: 18px;
}
.cp-start__title { font-size: 40px; margin: 0 0 10px; letter-spacing: -0.5px; }
.cp-start__lead { color: #475569; font-size: 17px; max-width: 520px; margin: 0 auto 24px; line-height: 1.55; }
.cp-start__how { text-align: left; max-width: 440px; margin: 0 auto 28px; color: #334155; line-height: 1.7; }

.cp-btn {
  padding: 12px 28px;
  border-radius: 999px;
  border: none;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
  font-size: 16px;
  transition: transform 0.1s ease, box-shadow 0.2s ease;
}
.cp-btn--primary { background: linear-gradient(135deg, #8b5cf6, #7c3aed); color: #fff; box-shadow: 0 6px 20px rgba(124,58,237,0.35); }
.cp-btn--primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 10px 26px rgba(124,58,237,0.45); filter: brightness(1.05); }
.cp-btn--primary:active:not(:disabled) { transform: translateY(1px); box-shadow: 0 3px 10px rgba(124,58,237,0.3); }
.cp-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; box-shadow: none; }
.cp-btn--ghost { background: #fff; border: 1px solid #cbd5e1; color: #0f172a; }
.cp-btn--ghost:hover:not(:disabled) { border-color: #7c3aed; color: #7c3aed; background: #faf5ff; }
.cp-btn--ghost:active:not(:disabled) { background: #ede9fe; }

/* Экран кейса */
.cp-case { padding-top: 24px; }
.cp-case__progress { display: flex; gap: 12px; align-items: center; color: #64748b; font-size: 13px; margin-bottom: 16px; }
.cp-case__bar { flex: 1; height: 6px; background: #eef2f7; border-radius: 999px; overflow: hidden; }
.cp-case__bar-fill { height: 100%; background: linear-gradient(90deg, #8b5cf6, #ec4899); transition: width 0.3s ease; }
.cp-case__card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 20px;
  padding: 24px 22px; box-shadow: 0 6px 24px rgba(15,23,42,0.05);
  margin-bottom: 20px;
  cursor: grab;
}
.cp-case__card[draggable="true"]:active { cursor: grabbing; transform: rotate(-0.5deg); }
.cp-case__cat { color: #7c3aed; font-weight: 700; font-size: 12px; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 8px; }
.cp-case__title { margin: 0 0 12px; font-size: 24px; line-height: 1.3; }
.cp-case__scenario { color: #334155; line-height: 1.6; margin: 0 0 14px; font-size: 16px; }
.cp-case__actions { display: flex; justify-content: flex-end; }

/* Домены */
.cp-domains { margin-top: 12px; }
.cp-domains__lead { color: #64748b; margin: 0 0 12px; font-size: 13px; }
.cp-domains__grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.cp-domain {
  display: flex; flex-direction: column; align-items: flex-start; gap: 4px;
  padding: 16px 18px; border-radius: 18px; border: 2px dashed transparent;
  cursor: pointer; text-align: left; font: inherit;
  transition: transform 0.1s ease, border-color 0.15s ease;
  min-height: 110px;
}
.cp-domain:hover { transform: translateY(-2px); border-color: rgba(124,58,237,0.5); box-shadow: 0 8px 18px rgba(15,23,42,0.08); }
.cp-domain:active { transform: translateY(1px); }
.cp-domain--over { border-style: dashed; border-color: #111; }
.cp-domain--chosen { outline: 3px solid #7c3aed; outline-offset: -1px; box-shadow: 0 10px 24px rgba(124,58,237,0.25); transform: translateY(-1px); }
.cp-domain__icon { font-size: 24px; }
.cp-domain__name { font-weight: 700; font-size: 17px; }
.cp-domain__short { color: rgba(15,23,42,0.7); font-size: 13px; line-height: 1.35; }
.cp-domain--obvious { background: #dcfce7; color: #166534; }
.cp-domain--complicated { background: #dbeafe; color: #1d4ed8; }
.cp-domain--complex { background: #fce7f3; color: #9d174d; }
.cp-domain--chaotic { background: #fee2e2; color: #b91c1c; }

/* Стратегии */
.cp-strategy { padding-top: 20px; }
.cp-strategy__head { margin-bottom: 14px; text-align: center; }
.cp-strategy__head h2 { margin: 10px 0 4px; }
.cp-strategy__lead { color: #64748b; margin: 0; }
.cp-strategy__list { display: flex; flex-direction: column; gap: 8px; margin-bottom: 18px; }
.cp-strategy__item {
  display: flex; gap: 12px; align-items: flex-start; padding: 14px 16px;
  border-radius: 14px; border: 1px solid #e5e7eb; background: #fff; cursor: pointer;
  font: inherit; text-align: left; line-height: 1.4;
  transition: border-color 0.15s ease, background 0.15s ease, box-shadow 0.15s ease, transform 0.1s ease;
}
.cp-strategy__item:hover { border-color: #7c3aed; background: #faf5ff; }
.cp-strategy__item:active { transform: translateY(1px); }
.cp-strategy__item--chosen { border-color: #7c3aed; background: #ede9fe; box-shadow: 0 4px 14px rgba(124,58,237,0.2); }
.cp-strategy__item--chosen .cp-strategy__bullet { color: #fff; background: #7c3aed; border-radius: 999px; padding: 1px 8px; }
.cp-strategy__bullet { color: #7c3aed; font-size: 12px; margin-top: 3px; }
.cp-strategy__custom { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.cp-strategy__custom label { color: #64748b; font-size: 13px; }
.cp-strategy__custom textarea {
  resize: vertical; min-height: 60px; padding: 10px 12px;
  border-radius: 12px; border: 1px solid #cbd5e1; font: inherit;
}
.cp-strategy__custom textarea:focus { outline: none; border-color: #7c3aed; }
.cp-strategy__actions { display: flex; justify-content: space-between; gap: 10px; }

/* Дебриф */
.cp-debrief { padding-top: 16px; }
.cp-debrief__top { text-align: center; margin-bottom: 16px; }
.cp-debrief__top h2 { margin: 8px 0 0; font-size: 22px; }
.cp-debrief__match {
  display: inline-block; padding: 4px 14px; border-radius: 999px; font-weight: 700; font-size: 13px;
  letter-spacing: 0.5px;
}
.cp-debrief__match--yes { background: #dcfce7; color: #166534; }
.cp-debrief__match--no { background: #fee2e2; color: #b91c1c; }
.cp-debrief__pair { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 14px; }
.cp-debrief__col { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px 14px; }
.cp-debrief__col-hdr { color: #64748b; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; font-weight: 700; margin-bottom: 6px; }
.cp-debrief__strategy { margin-top: 8px; color: #334155; font-size: 14px; }

.cp-debrief__rationale {
  background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 14px;
  padding: 14px 16px; margin-bottom: 16px; color: #3b0764; line-height: 1.55;
}
.cp-debrief__rationale b { display: inline-block; margin-bottom: 4px; }
.cp-debrief__rationale p { margin: 0; }

.cp-debrief__cons h3, .cp-debrief__stats h3 { margin: 0 0 10px; font-size: 17px; }
.cp-debrief__cons { margin-bottom: 18px; }
.cp-debrief__cons-item {
  display: grid; grid-template-columns: 140px 1fr; gap: 10px; align-items: flex-start;
  padding: 10px 0; border-top: 1px solid #eef2f7;
}
.cp-debrief__cons-item:first-of-type { border-top: none; }
.cp-debrief__cons-item p { margin: 0; color: #334155; line-height: 1.5; font-size: 14px; }
.cp-debrief__cons-item--expert { background: linear-gradient(90deg, #dcfce7 0%, transparent 60%); padding-left: 8px; border-radius: 6px; }
.cp-debrief__stats-hint { color: #64748b; font-size: 12px; margin-top: 4px; }
.cp-debrief__actions { display: flex; justify-content: flex-end; margin-top: 20px; }

/* Полоски статистики */
.cyn-bars { display: flex; flex-direction: column; gap: 6px; }
.cyn-bars__row { display: grid; grid-template-columns: 110px 1fr 44px; gap: 8px; align-items: center; }
.cyn-bars__label { font-size: 13px; color: #334155; }
.cyn-bars__track { background: #eef2f7; border-radius: 999px; height: 10px; overflow: hidden; }
.cyn-bars__fill { height: 100%; background: #cbd5e1; border-radius: 999px; transition: width 0.3s ease; }
.cyn-bars__fill--expert { background: #22c55e; }
.cyn-bars__val { font-size: 12px; color: #64748b; text-align: right; }

/* Домен-таблетки (общие) */
.cyn-dom-pill {
  padding: 2px 10px; border-radius: 999px; font-weight: 700; font-size: 12px; letter-spacing: 0.3px;
  display: inline-block;
}
.cyn-dom-pill--obvious { background: #dcfce7; color: #166534; }
.cyn-dom-pill--complicated { background: #dbeafe; color: #1d4ed8; }
.cyn-dom-pill--complex { background: #fce7f3; color: #9d174d; }
.cyn-dom-pill--chaotic { background: #fee2e2; color: #b91c1c; }

/* Результаты */
.cp-results__head { text-align: center; margin-bottom: 20px; }
.cp-results__head h1 { margin: 0 0 6px; font-size: 30px; }
.cp-results__summary { display: flex; gap: 12px; justify-content: center; margin-bottom: 20px; flex-wrap: wrap; }
.cp-results__stat { background: #faf5ff; border: 1px solid #e9d5ff; border-radius: 14px; padding: 12px 18px; min-width: 120px; text-align: center; }
.cp-results__stat-val { display: block; font-size: 24px; font-weight: 700; color: #6d28d9; }
.cp-results__stat-lbl { color: #64748b; font-size: 12px; }
.cp-results h3 { margin-top: 18px; }
.cp-top-list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.cp-top-list li { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; padding: 10px 14px; display: flex; justify-content: space-between; align-items: center; }
.cp-top-list__val { color: #ec4899; font-weight: 700; }
.cp-hint { color: #64748b; font-size: 13px; margin: 4px 0 10px; }

.cp-all { background: #fff; border: 1px solid #e5e7eb; border-radius: 14px; padding: 12px 16px; margin-top: 10px; }
.cp-all summary { cursor: pointer; font-weight: 600; color: #0f172a; }
.cp-all__list { list-style: none; padding: 0; margin: 12px 0 0; display: flex; flex-direction: column; gap: 14px; }
.cp-all__item { padding: 12px 0; border-top: 1px solid #eef2f7; }
.cp-all__item:first-child { border-top: none; padding-top: 0; }
.cp-all__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; flex-wrap: wrap; margin-bottom: 6px; }
.cp-all__cat { color: #7c3aed; font-size: 11px; font-weight: 700; letter-spacing: 0.5px; text-transform: uppercase; margin-right: 6px; }
.cp-all__scenario { color: #475569; font-size: 13px; line-height: 1.55; margin: 0 0 8px; }
.cp-all__my { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; flex-wrap: wrap; }
.cp-all__my-lbl { color: #64748b; font-size: 12px; }
.cp-all__match { color: #16a34a; font-weight: 700; }
.cp-all__mismatch { color: #dc2626; font-weight: 700; }
.cp-all__bars { margin-top: 6px; }

.cp-results__actions { text-align: center; margin-top: 24px; }

@media (max-width: 520px) {
  .cp-domains__grid { grid-template-columns: 1fr; }
  .cp-debrief__pair { grid-template-columns: 1fr; }
  .cp-debrief__cons-item { grid-template-columns: 1fr; }
  .cyn-bars__row { grid-template-columns: 90px 1fr 40px; }
  .cp-start__title { font-size: 30px; }
}
</style>
