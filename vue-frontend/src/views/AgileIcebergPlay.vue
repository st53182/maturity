<template>
  <div class="ice-play">
    <!-- Переключатель языка -->
    <div class="ice-lang" role="group" v-if="!loading">
      <button type="button" class="ice-lang__btn" :class="{ 'ice-lang__btn--active': $i18n.locale === 'ru' }" @click="switchLang('ru')">RU</button>
      <button type="button" class="ice-lang__btn" :class="{ 'ice-lang__btn--active': $i18n.locale === 'en' }" @click="switchLang('en')">EN</button>
    </div>

    <div v-if="loading" class="ice-loading">
      <div class="ice-loading__spin" />
      <div>{{ $t('common.loading') }}…</div>
    </div>
    <div v-else-if="error" class="ice-error">
      <h1>{{ $t('agileTraining.play.loadError') || 'Не удалось загрузить тренинг' }}</h1>
      <p>{{ error }}</p>
    </div>

    <!-- Экран 1: старт -->
    <section v-else-if="stage === 'start'" class="ice-start">
      <div class="ice-start__badge">🧊 {{ $t('agileTraining.hub.iceberg.title') }}</div>
      <h1 class="ice-start__title">{{ group.name }}</h1>
      <p class="ice-start__lead">{{ $t('agileTraining.iceberg.play.startLead') }}</p>
      <ul class="ice-start__how">
        <li>{{ $t('agileTraining.iceberg.play.how1') }}</li>
        <li>{{ $t('agileTraining.iceberg.play.how2') }}</li>
        <li>{{ $t('agileTraining.iceberg.play.how3') }}</li>
        <li>{{ $t('agileTraining.iceberg.play.how4') }}</li>
      </ul>
      <button class="ice-btn ice-btn--primary" @click="startPlay" :disabled="starting">
        {{ $t('agileTraining.iceberg.play.startBtn') }}
      </button>
    </section>

    <!-- Общая шапка прогресса для всех рабочих стадий -->
    <div v-else-if="['case','iceberg','chain','thinking','interventions','debrief'].includes(stage)" class="ice-progress">
      <span>{{ currentIndex + 1 }} / {{ cases.length }}</span>
      <div class="ice-progress__bar">
        <div class="ice-progress__fill" :style="{ width: progressPercent + '%' }" />
      </div>
      <span class="ice-progress__step">{{ stageLabel }}</span>
    </div>

    <!-- Экран 2: ситуация -->
    <section v-if="stage === 'case'" class="ice-case">
      <div class="ice-case__card">
        <div class="ice-case__cat">{{ currentCase.category }}</div>
        <h2 class="ice-case__title">{{ currentCase.title }}</h2>
        <p class="ice-case__scenario">{{ currentCase.scenario }}</p>
        <div class="ice-case__actions">
          <button class="ice-btn ice-btn--primary" @click="stage = 'iceberg'">
            {{ $t('agileTraining.iceberg.play.goIceberg') }} →
          </button>
        </div>
      </div>
    </section>

    <!-- Экран 3: разбор айсберга (drag & drop) -->
    <section v-else-if="stage === 'iceberg'" class="ice-board">
      <h2 class="ice-board__title">🏔 {{ $t('agileTraining.iceberg.play.icebergTitle') }}</h2>
      <p class="ice-board__hint">{{ $t('agileTraining.iceberg.play.icebergHint') }}</p>

      <!-- Bench: неразмещённые карточки -->
      <div class="ice-bench"
           @dragover.prevent
           @drop.prevent="onDropToBench">
        <div class="ice-bench__label">{{ $t('agileTraining.iceberg.play.benchLabel') }}</div>
        <div class="ice-bench__cards">
          <div v-for="it in benchItems" :key="it.key"
               class="ice-card"
               draggable="true"
               @dragstart="onDragStart($event, it.key)"
               @click="toggleCardMenu(it.key)">
            <span>{{ it.text }}</span>
            <div v-if="cardMenuOpen === it.key" class="ice-card__menu" @click.stop>
              <button v-for="lk in LEVEL_KEYS" :key="lk" @click="placeCard(it.key, lk)">
                {{ $t('agileTraining.iceberg.level.' + lk) }}
              </button>
            </div>
          </div>
          <div v-if="!benchItems.length" class="ice-bench__empty">
            {{ $t('agileTraining.iceberg.play.benchEmpty') }}
          </div>
        </div>
      </div>

      <!-- 4 уровня сверху вниз (от поверхности к глубине) -->
      <div class="ice-levels">
        <div v-for="lk in LEVEL_KEYS" :key="lk"
             class="ice-level" :class="'ice-level--' + lk"
             @dragover.prevent="dragOverLevel = lk"
             @dragleave="dragOverLevel = dragOverLevel === lk ? '' : dragOverLevel"
             @drop.prevent="onDropToLevel($event, lk)">
          <div class="ice-level__head">
            <span class="ice-level__icon">{{ levelIcon(lk) }}</span>
            <div>
              <div class="ice-level__name">{{ levelName(lk) }}</div>
              <div class="ice-level__hint">{{ levelHint(lk) }}</div>
            </div>
          </div>
          <div class="ice-level__cards" :class="{ 'ice-level__cards--over': dragOverLevel === lk }">
            <div v-for="it in itemsAtLevel(lk)" :key="it.key"
                 class="ice-card ice-card--placed"
                 draggable="true"
                 @dragstart="onDragStart($event, it.key)"
                 @click="removeCard(it.key)">
              <span>{{ it.text }}</span>
              <span class="ice-card__remove">×</span>
            </div>
            <div v-if="!itemsAtLevel(lk).length" class="ice-level__empty">
              {{ $t('agileTraining.iceberg.play.levelEmpty') }}
            </div>
          </div>
        </div>
      </div>

      <!-- Свои карточки -->
      <div class="ice-custom">
        <div class="ice-custom__head">
          <b>{{ $t('agileTraining.iceberg.play.customTitle') }}</b>
          <span class="ice-hint">{{ $t('agileTraining.iceberg.play.customHint') }}</span>
        </div>
        <div class="ice-custom__form">
          <input v-model="customDraftText" :placeholder="$t('agileTraining.iceberg.play.customPh')" maxlength="160" />
          <select v-model="customDraftLevel">
            <option value="">{{ $t('agileTraining.iceberg.play.chooseLevel') }}</option>
            <option v-for="lk in LEVEL_KEYS" :key="lk" :value="lk">{{ levelName(lk) }}</option>
          </select>
          <button class="ice-btn ice-btn--ghost" :disabled="!customDraftText.trim() || !customDraftLevel" @click="addCustomItem">
            + {{ $t('agileTraining.iceberg.play.addCustom') }}
          </button>
        </div>
        <ul v-if="customItems.length" class="ice-custom__list">
          <li v-for="(ci, idx) in customItems" :key="'c' + idx">
            <span class="ice-custom__level">{{ levelName(ci.level) }}</span>
            <span>{{ ci.text }}</span>
            <button class="ice-custom__del" @click="removeCustomItem(idx)">×</button>
          </li>
        </ul>
      </div>

      <div class="ice-board__actions">
        <button class="ice-btn ice-btn--ghost" @click="stage = 'case'">← {{ $t('common.back') }}</button>
        <button class="ice-btn ice-btn--primary" @click="stage = 'chain'" :disabled="!allPlaced">
          {{ $t('agileTraining.iceberg.play.goChain') }} →
        </button>
      </div>
    </section>

    <!-- Экран 4: причинная цепочка -->
    <section v-else-if="stage === 'chain'" class="ice-chain">
      <h2 class="ice-chain__title">🔗 {{ $t('agileTraining.iceberg.play.chainTitle') }}</h2>
      <p class="ice-hint">{{ $t('agileTraining.iceberg.play.chainHint') }}</p>
      <div class="ice-chain__flow">
        <template v-for="(lk, i) in LEVEL_KEYS" :key="lk">
          <div class="ice-chain__step">
            <div class="ice-chain__lvl">
              <span>{{ levelIcon(lk) }}</span>
              <span>{{ levelName(lk) }}</span>
            </div>
            <select v-model="chain[lk]">
              <option value="">{{ $t('agileTraining.iceberg.play.chooseItem') }}</option>
              <option v-for="it in itemsAtLevel(lk)" :key="it.key" :value="it.key">{{ it.text }}</option>
            </select>
          </div>
          <div v-if="i < LEVEL_KEYS.length - 1" class="ice-chain__arrow">↓</div>
        </template>
      </div>
      <div class="ice-chain__actions">
        <button class="ice-btn ice-btn--ghost" @click="stage = 'iceberg'">← {{ $t('common.back') }}</button>
        <button class="ice-btn ice-btn--primary" @click="stage = 'thinking'">
          {{ $t('agileTraining.iceberg.play.goThinking') }} →
        </button>
      </div>
    </section>

    <!-- Экран 5: проверка мышления -->
    <section v-else-if="stage === 'thinking'" class="ice-thinking">
      <h2 class="ice-thinking__title">🧠 {{ $t('agileTraining.iceberg.play.thinkingTitle') }}</h2>
      <p class="ice-hint">{{ $t('agileTraining.iceberg.play.thinkingHint') }}</p>
      <ul class="ice-thinking__list">
        <li v-for="sx in currentCase.superficial" :key="sx.key" class="ice-thinking__row">
          <div class="ice-thinking__text">«{{ sx.text }}»</div>
          <div class="ice-thinking__choice">
            <button class="ice-btn ice-btn--choice"
                    :class="{ 'ice-btn--choice-active': superficial[sx.key] === true }"
                    @click="superficial[sx.key] = true">
              {{ $t('agileTraining.iceberg.play.isSymptom') }}
            </button>
            <button class="ice-btn ice-btn--choice"
                    :class="{ 'ice-btn--choice-active': superficial[sx.key] === false }"
                    @click="superficial[sx.key] = false">
              {{ $t('agileTraining.iceberg.play.isRealCause') }}
            </button>
          </div>
        </li>
      </ul>
      <div class="ice-chain__actions">
        <button class="ice-btn ice-btn--ghost" @click="stage = 'chain'">← {{ $t('common.back') }}</button>
        <button class="ice-btn ice-btn--primary" :disabled="!allThinkingAnswered" @click="stage = 'interventions'">
          {{ $t('agileTraining.iceberg.play.goInterventions') }} →
        </button>
      </div>
    </section>

    <!-- Экран 6: интервенции -->
    <section v-else-if="stage === 'interventions'" class="ice-int">
      <h2 class="ice-int__title">🛠 {{ $t('agileTraining.iceberg.play.interventionsTitle') }}</h2>
      <p class="ice-hint">{{ $t('agileTraining.iceberg.play.interventionsHint') }}</p>
      <div class="ice-int__grid">
        <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-int__box" :class="'ice-int__box--' + lk">
          <div class="ice-int__head">
            <span>{{ levelIcon(lk) }}</span>
            <b>{{ levelName(lk) }}</b>
          </div>
          <p class="ice-int__sub">{{ levelHint(lk) }}</p>
          <textarea v-model="interventions[lk]"
                    :placeholder="$t('agileTraining.iceberg.play.interventionsPh')"
                    maxlength="1000" />
        </div>
      </div>
      <div class="ice-chain__actions">
        <button class="ice-btn ice-btn--ghost" @click="stage = 'thinking'">← {{ $t('common.back') }}</button>
        <button class="ice-btn ice-btn--primary" :disabled="saving || !anyIntervention" @click="submitAnswer">
          {{ saving ? $t('common.loading') + '…' : $t('agileTraining.iceberg.play.submitBtn') }}
        </button>
      </div>
    </section>

    <!-- Экран 7: обратная связь / дебриф -->
    <section v-else-if="stage === 'debrief'" class="ice-debrief">
      <h2 class="ice-debrief__title">💡 {{ $t('agileTraining.iceberg.play.debriefTitle') }}</h2>

      <div class="ice-debrief__score">
        <div class="ice-debrief__score-val">{{ lastScore }}</div>
        <div class="ice-debrief__score-lbl">{{ $t('agileTraining.iceberg.play.yourCaseScore') }}</div>
      </div>

      <!-- Что участник разложил vs. эксперт -->
      <div class="ice-dbg">
        <h4>🏔 {{ $t('agileTraining.iceberg.play.placementsCheck') }}</h4>
        <ul class="ice-dbg__placements">
          <li v-for="it in standardItemsForCurrent" :key="it.key"
              :class="{ 'ice-dbg__ok': myPlacementFor(it.key) === debriefExpertItems[it.key],
                        'ice-dbg__bad': myPlacementFor(it.key) && myPlacementFor(it.key) !== debriefExpertItems[it.key] }">
            <div class="ice-dbg__text">{{ it.text }}</div>
            <div class="ice-dbg__levels">
              <span>{{ $t('agileTraining.iceberg.play.you') }}: <b>{{ myPlacementFor(it.key) ? levelName(myPlacementFor(it.key)) : '—' }}</b></span>
              <span class="ice-dbg__sep">·</span>
              <span>{{ $t('agileTraining.iceberg.play.expert') }}: <b>{{ levelName(debriefExpertItems[it.key]) }}</b></span>
            </div>
          </li>
        </ul>
      </div>

      <!-- Проверка мышления -->
      <div class="ice-dbg">
        <h4>🧠 {{ $t('agileTraining.iceberg.play.thinkingReview') }}</h4>
        <ul class="ice-dbg__list">
          <li v-for="sx in currentCase.superficial" :key="sx.key"
              :class="{ 'ice-dbg__ok': superficialWasCorrect(sx.key), 'ice-dbg__bad': superficial[sx.key] !== undefined && !superficialWasCorrect(sx.key) }">
            <div class="ice-dbg__text">«{{ sx.text }}»</div>
            <div class="ice-dbg__expl">
              {{ debriefSuperficial[sx.key] && debriefSuperficial[sx.key].is_symptom
                 ? $t('agileTraining.iceberg.play.expertSymptom')
                 : $t('agileTraining.iceberg.play.expertRealCause') }}
              — {{ debriefSuperficial[sx.key] && debriefSuperficial[sx.key].explanation }}
            </div>
          </li>
        </ul>
      </div>

      <!-- Экспертные интервенции -->
      <div class="ice-dbg">
        <h4>🛠 {{ $t('agileTraining.iceberg.play.expertInterventions') }}</h4>
        <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-dbg__iv" :class="'ice-int__box--' + lk">
          <div class="ice-int__head">
            <span>{{ levelIcon(lk) }}</span>
            <b>{{ levelName(lk) }}</b>
            <span v-if="debriefInterventions[lk]" class="ice-dbg__horizon">⏱ {{ debriefInterventions[lk].horizon_label }}</span>
          </div>
          <div v-if="interventions[lk]" class="ice-dbg__my">
            <span class="ice-dbg__badge">{{ $t('agileTraining.iceberg.play.yours') }}</span>
            <span>{{ interventions[lk] }}</span>
          </div>
          <div v-if="debriefInterventions[lk]" class="ice-dbg__theirs">
            <span class="ice-dbg__badge ice-dbg__badge--exp">{{ $t('agileTraining.iceberg.play.expert') }}</span>
            <div>
              <div>{{ debriefInterventions[lk].text }}</div>
              <div class="ice-dbg__effect">{{ debriefInterventions[lk].effect }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Последствия и сводка -->
      <div class="ice-dbg ice-dbg--consequences">
        <div class="ice-dbg__summary"><b>📌 {{ $t('agileTraining.iceberg.expertSummary') }}:</b> {{ debriefData.summary }}</div>
        <div class="ice-dbg__cons">
          <div class="ice-dbg__cons-box ice-dbg__cons-box--bad">
            <b>⚠️ {{ $t('agileTraining.iceberg.play.consequencesEventsOnly') }}:</b>
            <p>{{ debriefData.consequences_events_only }}</p>
          </div>
          <div class="ice-dbg__cons-box ice-dbg__cons-box--good">
            <b>✅ {{ $t('agileTraining.iceberg.play.consequencesSystem') }}:</b>
            <p>{{ debriefData.consequences_system }}</p>
          </div>
        </div>
      </div>

      <!-- Статистика группы -->
      <div class="ice-dbg">
        <h4>👥 {{ $t('agileTraining.iceberg.play.groupStats') }}</h4>
        <p class="ice-hint">
          {{ $t('agileTraining.iceberg.play.groupStatsHint', { n: groupStats.total }, groupStats.total) }}
        </p>
        <div class="ice-bars">
          <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-bars__row">
            <div class="ice-bars__label">{{ levelName(lk) }}</div>
            <div class="ice-bars__track">
              <div class="ice-bars__fill" :class="'ice-bars__fill--' + lk"
                   :style="{ width: (groupStats.primary_level_pct[lk] || 0) + '%' }" />
            </div>
            <div class="ice-bars__val">{{ groupStats.primary_level_pct[lk] || 0 }}%</div>
          </div>
        </div>
      </div>

      <div class="ice-chain__actions ice-chain__actions--end">
        <button v-if="currentIndex + 1 < cases.length" class="ice-btn ice-btn--primary" @click="nextCase">
          {{ $t('agileTraining.iceberg.play.nextCaseBtn') }} →
        </button>
        <button v-else class="ice-btn ice-btn--primary" @click="goToResults">
          {{ $t('agileTraining.iceberg.play.goResultsBtn') }} →
        </button>
      </div>
    </section>

    <!-- Экран 8: итоговые результаты -->
    <section v-else-if="stage === 'results'" class="ice-results">
      <h2 class="ice-results__title">🏁 {{ $t('agileTraining.iceberg.play.resultsTitle') }}</h2>

      <div v-if="resultsLoading" class="ice-hint">{{ $t('common.loading') }}…</div>
      <div v-else-if="results">
        <div class="ice-results__head">
          <div class="ice-results__score">
            <div class="ice-results__score-val">{{ results.my.avg_score }}</div>
            <div class="ice-results__score-lbl">{{ $t('agileTraining.iceberg.play.avgDepthScore') }}</div>
          </div>
          <div class="ice-results__score">
            <div class="ice-results__score-val">{{ results.my.answered }} / {{ cases.length }}</div>
            <div class="ice-results__score-lbl">{{ $t('agileTraining.iceberg.play.casesAnswered') }}</div>
          </div>
          <div class="ice-results__score">
            <div class="ice-results__score-val">{{ results.participants_count }}</div>
            <div class="ice-results__score-lbl">{{ $t('agileTraining.iceberg.play.groupSize') }}</div>
          </div>
        </div>

        <div class="ice-results__block">
          <h4>{{ $t('agileTraining.iceberg.play.yourTendency') }}</h4>
          <p v-if="!myTendencyLevel" class="ice-hint">{{ $t('agileTraining.iceberg.play.noTendency') }}</p>
          <div v-else class="ice-tendency">
            <span class="ice-tendency__pill" :class="'ice-bars__fill--' + myTendencyLevel">
              {{ levelIcon(myTendencyLevel) }} {{ levelName(myTendencyLevel) }}
            </span>
            <p>{{ $t('agileTraining.iceberg.play.tendency.' + myTendencyLevel) }}</p>
          </div>
        </div>

        <div class="ice-results__block">
          <h4>👥 {{ $t('agileTraining.iceberg.play.groupDistribution') }}</h4>
          <div class="ice-bars">
            <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-bars__row">
              <div class="ice-bars__label">{{ levelName(lk) }}</div>
              <div class="ice-bars__track">
                <div class="ice-bars__fill" :class="'ice-bars__fill--' + lk"
                     :style="{ width: (results.group_totals.primary_level_pct[lk] || 0) + '%' }" />
              </div>
              <div class="ice-bars__val">{{ results.group_totals.primary_level_pct[lk] || 0 }}%</div>
            </div>
          </div>
        </div>

        <div class="ice-results__block">
          <h4>📋 {{ $t('agileTraining.iceberg.play.perCase') }}</h4>
          <ul class="ice-results__cases">
            <li v-for="r in results.per_case" :key="r.key">
              <div class="ice-case-row__head">
                <div>
                  <span class="ice-case-row__cat">{{ r.category }}</span>
                  <b>{{ r.title }}</b>
                </div>
                <div class="ice-case-row__stats">
                  <span class="ice-pill">{{ $t('agileTraining.iceberg.answersCount', { n: r.stats.total }, r.stats.total) }}</span>
                  <span v-if="r.my && r.my.depth_score !== undefined" class="ice-pill ice-pill--score">
                    {{ $t('agileTraining.iceberg.play.yourScore') }}: {{ r.my.depth_score }}
                  </span>
                </div>
              </div>
              <div class="ice-bars ice-bars--small">
                <div v-for="lk in LEVEL_KEYS" :key="lk" class="ice-bars__row">
                  <div class="ice-bars__label">{{ levelName(lk) }}</div>
                  <div class="ice-bars__track">
                    <div class="ice-bars__fill" :class="'ice-bars__fill--' + lk"
                         :style="{ width: (r.stats.primary_level_pct[lk] || 0) + '%' }" />
                  </div>
                  <div class="ice-bars__val">{{ r.stats.primary_level_pct[lk] || 0 }}%</div>
                </div>
              </div>
            </li>
          </ul>
        </div>

        <div class="ice-chain__actions ice-chain__actions--end">
          <button class="ice-btn ice-btn--ghost" @click="restart">{{ $t('agileTraining.iceberg.play.restart') }}</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
/**
 * Игровой экран упражнения «Айсберг» (системное мышление).
 *
 * Стадии (в порядке прохождения одного кейса):
 *   start → case → iceberg → chain → thinking → interventions → debrief
 *   → (next case → case…) → results
 *
 * Идентификация участника — по `participant_token` в localStorage
 * (`at_iceberg_pt_<slug>`), чтобы разные упражнения не смешивались.
 *
 * Логика разделена: в каждом методе — одна задача, UI не пересчитывает
 * скор сам, а доверяет ответу сервера (`depth_score`, `primary_level`).
 */
import axios from 'axios';

const TOKEN_KEY_PREFIX = 'at_iceberg_pt_';
const LANG_KEY = 'language';

export default {
  name: 'AgileIcebergPlay',
  props: {
    slug: { type: String, default: null },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      LEVEL_KEYS: ['events', 'patterns', 'structures', 'mental_models'],
      loading: true,
      starting: false,
      saving: false,
      error: '',

      group: null,
      session: null,
      levelsMeta: [],     // [{ key, name, hint, icon, weight }]
      cases: [],

      stage: 'start',
      currentIndex: 0,
      answered: {},       // { case_key: { data, depth_score, primary_level } }

      // состояние текущего кейса
      placements: {},     // { item_key: level_key }
      customItems: [],    // [{ text, level }]
      customDraftText: '',
      customDraftLevel: '',
      chain: { events: '', patterns: '', structures: '', mental_models: '' },
      superficial: {},    // { sup_key: bool }  — true = симптом
      interventions: { events: '', patterns: '', structures: '', mental_models: '' },

      // drag-state
      dragOverLevel: '',
      cardMenuOpen: '',

      // дебриф текущего кейса
      debriefData: { items_expert: {}, superficial_expert: {}, interventions_expert: {}, summary: '', consequences_events_only: '', consequences_system: '' },
      groupStats: { total: 0, primary_level_pct: {} },
      lastScore: 0,

      participantToken: '',
      results: null,
      resultsLoading: false,
    };
  },
  computed: {
    effectiveSlug() { return this.slug || this.$route?.params?.slug; },
    currentCase() { return this.cases[this.currentIndex] || { items: [], superficial: [] }; },
    progressPercent() {
      if (!this.cases.length) return 0;
      return Math.round(100 * this.currentIndex / this.cases.length);
    },
    stageLabel() {
      const k = this.stage;
      if (!['case','iceberg','chain','thinking','interventions','debrief'].includes(k)) return '';
      return this.$t('agileTraining.iceberg.play.stage.' + k);
    },
    standardItemsForCurrent() {
      return this.currentCase.items || [];
    },
    benchItems() {
      return this.standardItemsForCurrent.filter(it => !this.placements[it.key]);
    },
    allPlaced() {
      return this.standardItemsForCurrent.every(it => this.placements[it.key]);
    },
    allThinkingAnswered() {
      const sup = this.currentCase.superficial || [];
      return sup.every(sx => this.superficial[sx.key] === true || this.superficial[sx.key] === false);
    },
    anyIntervention() {
      return this.LEVEL_KEYS.some(lk => (this.interventions[lk] || '').trim());
    },
    debriefExpertItems() { return this.debriefData.items_expert || {}; },
    debriefSuperficial() { return this.debriefData.superficial_expert || {}; },
    debriefInterventions() { return this.debriefData.interventions_expert || {}; },
    myTendencyLevel() {
      if (!this.results || !this.results.my) return '';
      const c = this.results.my.primary_level_counts || {};
      let best = '', bw = 0;
      this.LEVEL_KEYS.forEach(lk => { if ((c[lk] || 0) > bw) { best = lk; bw = c[lk]; } });
      return best;
    },
  },
  async mounted() { await this.loadAll(); },
  methods: {
    _tokenKey() { return TOKEN_KEY_PREFIX + this.effectiveSlug; },

    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem(LANG_KEY, lang); } catch (_) { /* ignore */ }
      this.reloadContent();
    },

    levelIcon(lk) { return (this.levelsMeta.find(m => m.key === lk) || {}).icon || '•'; },
    levelName(lk) { return (this.levelsMeta.find(m => m.key === lk) || {}).name || lk; },
    levelHint(lk) { return (this.levelsMeta.find(m => m.key === lk) || {}).hint || ''; },

    async loadAll() {
      this.loading = true; this.error = '';
      try {
        const res = await axios.get(`/api/agile-training/g/${this.effectiveSlug}`);
        this.group = res.data.group;
        this.session = res.data.session || this.prefetchedSession;
        if (!localStorage.getItem(LANG_KEY) && this.session?.locale) {
          this.$i18n.locale = this.session.locale;
        }
        await this.reloadContent();
        this.participantToken = localStorage.getItem(this._tokenKey()) || '';
        if (this.participantToken) await this.loadState();
      } catch (e) {
        this.error = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.loading = false;
      }
    },

    async reloadContent() {
      const locale = this.$i18n.locale || 'ru';
      try {
        const res = await axios.get('/api/agile-training/iceberg/content', { params: { locale } });
        this.cases = res.data.cases || [];
        this.levelsMeta = res.data.levels || [];
      } catch (e) {
        console.error('reloadContent', e);
      }
    },

    async loadState() {
      try {
        const res = await axios.get(`/api/agile-training/iceberg/g/${this.effectiveSlug}/state`, {
          params: { participant_token: this.participantToken },
        });
        this.answered = res.data.answered || {};
        const firstUnanswered = this.cases.findIndex(c => !this.answered[c.key]);
        this.currentIndex = firstUnanswered >= 0 ? firstUnanswered : Math.max(0, this.cases.length - 1);
      } catch (e) { console.error('loadState', e); }
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
      this.placements = {};
      this.customItems = [];
      this.customDraftText = '';
      this.customDraftLevel = '';
      this.chain = { events: '', patterns: '', structures: '', mental_models: '' };
      this.superficial = {};
      this.interventions = { events: '', patterns: '', structures: '', mental_models: '' };
      this.dragOverLevel = '';
      this.cardMenuOpen = '';
    },

    // ---------- placements ----------
    itemsAtLevel(lk) {
      return this.standardItemsForCurrent.filter(it => this.placements[it.key] === lk);
    },
    myPlacementFor(itemKey) { return this.placements[itemKey] || null; },
    onDragStart(ev, itemKey) {
      try {
        ev.dataTransfer.setData('text/plain', itemKey);
        ev.dataTransfer.effectAllowed = 'move';
      } catch (_) { /* ignore */ }
    },
    onDropToLevel(ev, lk) {
      const k = ev.dataTransfer.getData('text/plain');
      if (!k) return;
      this.placements = { ...this.placements, [k]: lk };
      this.dragOverLevel = '';
    },
    onDropToBench(ev) {
      const k = ev.dataTransfer.getData('text/plain');
      if (!k) return;
      const np = { ...this.placements };
      delete np[k];
      this.placements = np;
    },
    placeCard(itemKey, lk) {
      this.placements = { ...this.placements, [itemKey]: lk };
      this.cardMenuOpen = '';
    },
    removeCard(itemKey) {
      const np = { ...this.placements };
      delete np[itemKey];
      this.placements = np;
    },
    toggleCardMenu(itemKey) {
      this.cardMenuOpen = this.cardMenuOpen === itemKey ? '' : itemKey;
    },

    addCustomItem() {
      if (!this.customDraftText.trim() || !this.customDraftLevel) return;
      this.customItems.push({ text: this.customDraftText.trim(), level: this.customDraftLevel });
      this.customDraftText = '';
      this.customDraftLevel = '';
    },
    removeCustomItem(idx) { this.customItems.splice(idx, 1); },

    // ---------- submit ----------
    async submitAnswer() {
      if (!this.anyIntervention) return;
      this.saving = true;
      try {
        const payload = {
          participant_token: this.participantToken,
          case_key: this.currentCase.key,
          placements: this.placements,
          custom_items: this.customItems,
          chain: this.chain,
          superficial: this.superficial,
          interventions: this.interventions,
          locale: this.$i18n.locale || 'ru',
        };
        const res = await axios.post(`/api/agile-training/iceberg/g/${this.effectiveSlug}/answer`, payload);
        this.answered[this.currentCase.key] = {
          data: {
            placements: this.placements,
            custom_items: this.customItems,
            chain: this.chain,
            superficial: this.superficial,
            interventions: this.interventions,
          },
          depth_score: res.data.depth_score,
          primary_level: res.data.primary_level,
        };
        this.debriefData = res.data.debrief || this.debriefData;
        this.groupStats = res.data.stats || this.groupStats;
        this.lastScore = res.data.depth_score || 0;
        this.stage = 'debrief';
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to save');
      } finally {
        this.saving = false;
      }
    },

    superficialWasCorrect(supKey) {
      if (this.superficial[supKey] === undefined) return false;
      const exp = this.debriefSuperficial[supKey];
      if (!exp) return false;
      return !!this.superficial[supKey] === !!exp.is_symptom;
    },

    nextCase() {
      if (this.currentIndex + 1 >= this.cases.length) { this.goToResults(); return; }
      this.currentIndex += 1;
      this.resetChoice();
      this.stage = 'case';
    },

    async goToResults() {
      this.stage = 'results';
      this.resultsLoading = true;
      try {
        const res = await axios.get(`/api/agile-training/iceberg/g/${this.effectiveSlug}/results`, {
          params: { participant_token: this.participantToken, locale: this.$i18n.locale || 'ru' },
        });
        this.results = res.data;
      } catch (e) {
        alert(e.response?.data?.error || 'Failed to load results');
      } finally {
        this.resultsLoading = false;
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
.ice-play {
  min-height: 100vh;
  background: linear-gradient(180deg, #f0f9ff 0%, #ecfeff 100%);
  padding: 20px 16px 80px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', sans-serif;
  color: #0f172a;
}
.ice-lang {
  position: absolute; top: 16px; right: 16px;
  display: inline-flex; background: #fff; border: 1px solid #e5e7eb;
  border-radius: 999px; overflow: hidden;
}
.ice-lang__btn {
  background: transparent; border: none; padding: 6px 14px;
  font-size: 12px; font-weight: 700; color: #475569; cursor: pointer;
}
.ice-lang__btn--active { background: #0ea5e9; color: #fff; }

.ice-loading, .ice-error { text-align: center; padding: 80px 16px; color: #475569; }
.ice-loading__spin {
  width: 36px; height: 36px; border-radius: 50%;
  border: 4px solid #e0f2fe; border-top-color: #0ea5e9;
  margin: 0 auto 12px; animation: ice-spin 0.9s linear infinite;
}
@keyframes ice-spin { to { transform: rotate(360deg); } }

.ice-start {
  max-width: 620px; margin: 40px auto; background: #fff;
  border-radius: 22px; padding: 32px 28px; text-align: center;
  border: 1px solid #bae6fd; box-shadow: 0 12px 40px rgba(2, 132, 199, 0.08);
}
.ice-start__badge {
  display: inline-block; background: #0ea5e9; color: #fff;
  padding: 4px 12px; border-radius: 999px; font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
}
.ice-start__title { margin: 12px 0 8px; font-size: 28px; }
.ice-start__lead { color: #475569; margin: 0 0 18px; line-height: 1.6; }
.ice-start__how {
  text-align: left; background: #f0f9ff; border-radius: 14px;
  padding: 14px 20px; margin: 0 0 22px; color: #334155; line-height: 1.7;
}

.ice-btn {
  padding: 12px 22px; border-radius: 12px; border: none;
  font: inherit; font-weight: 700; cursor: pointer;
}
.ice-btn--primary { background: #0ea5e9; color: #fff; }
.ice-btn--primary:hover { background: #0284c7; }
.ice-btn--primary:disabled { background: #cbd5e1; cursor: not-allowed; }
.ice-btn--ghost { background: #fff; border: 1px solid #cbd5e1; color: #0f172a; }
.ice-btn--ghost:hover { border-color: #0ea5e9; color: #0ea5e9; }
.ice-btn--choice {
  background: #fff; border: 2px solid #cbd5e1; color: #334155;
  padding: 8px 16px; border-radius: 10px; font-weight: 600; font-size: 14px;
}
.ice-btn--choice-active { background: #0ea5e9; border-color: #0ea5e9; color: #fff; }

.ice-progress {
  max-width: 820px; margin: 0 auto 18px;
  display: flex; gap: 12px; align-items: center;
  background: #fff; border-radius: 999px; padding: 6px 14px; font-size: 12px; color: #475569;
  border: 1px solid #e0f2fe;
}
.ice-progress__bar { flex: 1; background: #e0f2fe; border-radius: 999px; height: 8px; overflow: hidden; }
.ice-progress__fill { background: #0ea5e9; height: 100%; transition: width 0.3s; }
.ice-progress__step { font-weight: 700; color: #0369a1; }

.ice-case {
  max-width: 680px; margin: 0 auto;
}
.ice-case__card {
  background: #fff; border-radius: 18px; padding: 24px 22px;
  box-shadow: 0 12px 30px rgba(2, 132, 199, 0.07); border: 1px solid #bae6fd;
}
.ice-case__cat { color: #0369a1; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }
.ice-case__title { margin: 6px 0 12px; font-size: 22px; }
.ice-case__scenario { color: #334155; line-height: 1.6; }
.ice-case__actions { margin-top: 18px; text-align: right; }

/* Board */
.ice-board { max-width: 980px; margin: 0 auto; }
.ice-board__title { margin: 0 0 6px; }
.ice-board__hint { color: #475569; margin: 0 0 18px; }

.ice-bench {
  background: #fff; border: 2px dashed #bae6fd; border-radius: 16px;
  padding: 14px; margin-bottom: 16px; min-height: 80px;
}
.ice-bench__label { font-size: 12px; color: #0369a1; font-weight: 700; text-transform: uppercase; margin-bottom: 8px; }
.ice-bench__cards { display: flex; flex-wrap: wrap; gap: 10px; }
.ice-bench__empty { color: #94a3b8; font-style: italic; font-size: 14px; }

.ice-card {
  background: linear-gradient(135deg, #f0f9ff, #ecfeff);
  border: 1px solid #bae6fd; padding: 8px 12px; border-radius: 10px;
  cursor: grab; position: relative; user-select: none; max-width: 300px;
  font-size: 13px; line-height: 1.4;
}
.ice-card:active { cursor: grabbing; }
.ice-card--placed { background: #fff; border-color: #0ea5e9; display: flex; gap: 6px; align-items: center; }
.ice-card__remove { color: #94a3b8; font-size: 16px; margin-left: auto; }
.ice-card__menu {
  position: absolute; top: 100%; left: 0; z-index: 20;
  background: #fff; border: 1px solid #cbd5e1; border-radius: 10px;
  box-shadow: 0 10px 30px rgba(15,23,42,0.15);
  display: flex; flex-direction: column; min-width: 200px;
  padding: 4px; margin-top: 4px;
}
.ice-card__menu button {
  background: transparent; border: none; text-align: left; padding: 8px 12px;
  cursor: pointer; font: inherit; border-radius: 6px; color: #0f172a;
}
.ice-card__menu button:hover { background: #f1f5f9; }

.ice-levels { display: flex; flex-direction: column; gap: 10px; }
.ice-level {
  background: #fff; border-radius: 16px; padding: 14px 16px;
  border: 2px solid transparent; transition: border-color 0.2s;
}
.ice-level--events { background: #f0f9ff; }
.ice-level--patterns { background: #e0f2fe; }
.ice-level--structures { background: #bae6fd; }
.ice-level--mental_models { background: #7dd3fc; color: #0c4a6e; }
.ice-level__head { display: flex; gap: 12px; align-items: center; margin-bottom: 10px; }
.ice-level__icon { font-size: 22px; }
.ice-level__name { font-weight: 700; font-size: 15px; }
.ice-level__hint { font-size: 12px; color: rgba(15,23,42,0.7); }
.ice-level__cards {
  min-height: 54px; padding: 6px; border-radius: 10px;
  display: flex; gap: 8px; flex-wrap: wrap; background: rgba(255,255,255,0.4);
}
.ice-level__cards--over { background: #bae6fd; outline: 2px dashed #0ea5e9; }
.ice-level__empty { color: #64748b; font-size: 12px; font-style: italic; padding: 10px; }

.ice-custom { margin-top: 16px; background: #fff; border-radius: 14px; padding: 12px 14px; border: 1px solid #e0f2fe; }
.ice-custom__head { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-bottom: 8px; }
.ice-hint { color: #64748b; font-size: 12px; }
.ice-custom__form { display: flex; gap: 8px; flex-wrap: wrap; }
.ice-custom__form input { flex: 1 1 220px; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font: inherit; }
.ice-custom__form select { padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font: inherit; }
.ice-custom__list { list-style: none; padding: 0; margin: 10px 0 0; display: flex; flex-direction: column; gap: 6px; }
.ice-custom__list li { display: flex; gap: 8px; align-items: center; background: #f0f9ff; padding: 6px 10px; border-radius: 8px; font-size: 13px; }
.ice-custom__level { font-size: 11px; font-weight: 700; color: #0369a1; text-transform: uppercase; }
.ice-custom__del { margin-left: auto; background: transparent; border: none; cursor: pointer; color: #94a3b8; font-size: 16px; }

.ice-board__actions, .ice-chain__actions {
  display: flex; gap: 10px; justify-content: space-between; margin-top: 20px;
}
.ice-chain__actions--end { justify-content: flex-end; }

/* Chain */
.ice-chain { max-width: 680px; margin: 0 auto; background: #fff; border-radius: 18px; padding: 22px; border: 1px solid #bae6fd; }
.ice-chain__title { margin: 0 0 6px; }
.ice-chain__flow { margin: 14px 0; display: flex; flex-direction: column; gap: 6px; align-items: center; }
.ice-chain__step { width: 100%; background: #f0f9ff; border-radius: 10px; padding: 10px 12px; display: flex; gap: 10px; align-items: center; }
.ice-chain__lvl { display: flex; gap: 6px; align-items: center; font-weight: 700; color: #0369a1; width: 180px; }
.ice-chain__step select { flex: 1; padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font: inherit; background: #fff; }
.ice-chain__arrow { color: #0ea5e9; font-size: 20px; }

/* Thinking */
.ice-thinking { max-width: 780px; margin: 0 auto; background: #fff; border-radius: 18px; padding: 22px; border: 1px solid #bae6fd; }
.ice-thinking__title { margin: 0 0 6px; }
.ice-thinking__list { list-style: none; padding: 0; margin: 14px 0; display: flex; flex-direction: column; gap: 10px; }
.ice-thinking__row { background: #f0f9ff; border-radius: 12px; padding: 12px 14px; }
.ice-thinking__text { margin-bottom: 10px; color: #0f172a; line-height: 1.5; }
.ice-thinking__choice { display: flex; gap: 8px; flex-wrap: wrap; }

/* Interventions */
.ice-int { max-width: 900px; margin: 0 auto; }
.ice-int__title { margin: 0 0 6px; }
.ice-int__grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 14px 0 18px; }
.ice-int__box { border-radius: 14px; padding: 14px; border: 1px solid #bae6fd; background: #fff; }
.ice-int__box--events { background: #f0f9ff; }
.ice-int__box--patterns { background: #e0f2fe; }
.ice-int__box--structures { background: #bae6fd; }
.ice-int__box--mental_models { background: #7dd3fc; color: #0c4a6e; }
.ice-int__head { display: flex; gap: 8px; align-items: center; margin-bottom: 4px; font-size: 15px; }
.ice-int__sub { margin: 0 0 8px; font-size: 12px; color: rgba(15,23,42,0.7); }
.ice-int__box textarea {
  width: 100%; min-height: 80px; padding: 8px 10px;
  border: 1px solid #cbd5e1; border-radius: 10px; font: inherit; resize: vertical;
  background: rgba(255,255,255,0.7);
}

/* Debrief */
.ice-debrief { max-width: 880px; margin: 0 auto; }
.ice-debrief__title { margin: 0 0 10px; }
.ice-debrief__score {
  background: #fff; border-radius: 16px; padding: 14px 18px; margin-bottom: 14px;
  border: 1px solid #bae6fd; display: flex; gap: 16px; align-items: center;
}
.ice-debrief__score-val { font-size: 28px; font-weight: 800; color: #0369a1; }
.ice-debrief__score-lbl { color: #475569; }

.ice-dbg { background: #fff; border-radius: 16px; padding: 16px 18px; margin-bottom: 12px; border: 1px solid #e0f2fe; }
.ice-dbg h4 { margin: 0 0 8px; }
.ice-dbg__placements, .ice-dbg__list { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 8px; }
.ice-dbg__placements li, .ice-dbg__list li { background: #f8fafc; padding: 8px 10px; border-radius: 8px; border-left: 3px solid #cbd5e1; }
.ice-dbg__ok { border-left-color: #22c55e !important; background: #f0fdf4 !important; }
.ice-dbg__bad { border-left-color: #ef4444 !important; background: #fef2f2 !important; }
.ice-dbg__text { font-size: 13px; color: #0f172a; }
.ice-dbg__levels { font-size: 12px; color: #64748b; margin-top: 4px; display: flex; gap: 6px; flex-wrap: wrap; }
.ice-dbg__expl { font-size: 12px; color: #475569; margin-top: 4px; line-height: 1.5; }

.ice-dbg__iv { margin: 8px 0; padding: 12px; border-radius: 12px; }
.ice-dbg__horizon { margin-left: auto; color: #475569; font-size: 12px; font-weight: 600; }
.ice-dbg__my, .ice-dbg__theirs { display: flex; gap: 8px; padding: 8px 10px; margin-top: 8px; background: rgba(255,255,255,0.7); border-radius: 8px; font-size: 13px; }
.ice-dbg__badge { background: #e0f2fe; color: #0369a1; padding: 2px 8px; border-radius: 999px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; }
.ice-dbg__badge--exp { background: #fef3c7; color: #92400e; }
.ice-dbg__effect { color: #475569; font-size: 12px; margin-top: 2px; }

.ice-dbg--consequences { background: linear-gradient(135deg, #f0f9ff, #ecfeff); }
.ice-dbg__summary { margin-bottom: 10px; line-height: 1.55; color: #0f172a; }
.ice-dbg__cons { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }
.ice-dbg__cons-box { padding: 10px 12px; border-radius: 10px; }
.ice-dbg__cons-box--bad { background: #fef2f2; border: 1px solid #fecaca; }
.ice-dbg__cons-box--good { background: #f0fdf4; border: 1px solid #bbf7d0; }
.ice-dbg__cons-box p { margin: 4px 0 0; font-size: 13px; line-height: 1.5; }

/* Bars */
.ice-bars { display: flex; flex-direction: column; gap: 6px; }
.ice-bars--small .ice-bars__row { grid-template-columns: 140px 1fr 44px; }
.ice-bars__row { display: grid; grid-template-columns: 160px 1fr 44px; gap: 8px; align-items: center; }
.ice-bars__label { font-size: 13px; color: #334155; }
.ice-bars__track { background: #eef2f7; border-radius: 999px; height: 10px; overflow: hidden; }
.ice-bars__fill { height: 100%; background: #94a3b8; border-radius: 999px; transition: width 0.3s; }
.ice-bars__fill--events { background: #bae6fd; }
.ice-bars__fill--patterns { background: #7dd3fc; }
.ice-bars__fill--structures { background: #0ea5e9; }
.ice-bars__fill--mental_models { background: #0c4a6e; }
.ice-bars__val { font-size: 12px; color: #64748b; text-align: right; }

/* Results */
.ice-results { max-width: 880px; margin: 0 auto; }
.ice-results__title { margin: 0 0 14px; }
.ice-results__head { display: flex; gap: 10px; margin-bottom: 18px; flex-wrap: wrap; }
.ice-results__score { flex: 1; min-width: 140px; background: #fff; border: 1px solid #bae6fd; border-radius: 14px; padding: 14px 16px; text-align: center; }
.ice-results__score-val { font-size: 28px; font-weight: 800; color: #0369a1; }
.ice-results__score-lbl { color: #64748b; font-size: 13px; }

.ice-results__block { background: #fff; border-radius: 16px; padding: 16px 18px; margin-bottom: 12px; border: 1px solid #e0f2fe; }
.ice-results__block h4 { margin: 0 0 8px; }

.ice-tendency { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
.ice-tendency__pill { padding: 4px 12px; border-radius: 999px; color: #fff; font-weight: 700; font-size: 13px; }
.ice-tendency p { margin: 0; color: #475569; font-size: 13px; }

.ice-results__cases { list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 10px; }
.ice-results__cases li { background: #f8fafc; border-radius: 10px; padding: 10px 12px; }

.ice-case-row__head { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 6px; }
.ice-case-row__cat { color: #0369a1; font-size: 11px; font-weight: 700; letter-spacing: 0.4px; text-transform: uppercase; margin-right: 6px; }
.ice-case-row__stats { display: flex; gap: 6px; flex-wrap: wrap; }
.ice-pill { background: #f1f5f9; color: #334155; padding: 2px 10px; border-radius: 999px; font-weight: 600; font-size: 12px; }
.ice-pill--score { background: #ecfeff; color: #0369a1; }

@media (max-width: 720px) {
  .ice-int__grid { grid-template-columns: 1fr; }
  .ice-dbg__cons { grid-template-columns: 1fr; }
  .ice-bars__row { grid-template-columns: 100px 1fr 40px; }
  .ice-chain__lvl { width: 140px; font-size: 13px; }
}
</style>
