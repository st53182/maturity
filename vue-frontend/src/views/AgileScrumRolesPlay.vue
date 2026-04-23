<template>
  <div class="sr-play" v-if="ready">
    <header class="sr-play__head">
      <div>
        <div class="sr-play__group">
          🧩 {{ content ? groupName : '...' }}
        </div>
        <h1>{{ $t('agileTraining.scrumRoles.playTitle') }}</h1>
      </div>
      <div class="sr-play__lang">
        <button class="sr-lang__btn" :class="{ active: effectiveLocale === 'ru' }" @click="switchLocale('ru')">RU</button>
        <button class="sr-lang__btn" :class="{ active: effectiveLocale === 'en' }" @click="switchLocale('en')">EN</button>
      </div>
    </header>

    <!-- ШАГ 1: старт / имя -->
    <section v-if="step === 'start'" class="sr-play__section">
      <h2>👋 {{ $t('agileTraining.scrumRoles.welcome') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.welcomeLead') }}</p>
      <label class="sr-play__field">
        <span>{{ $t('agileTraining.scrumRoles.yourName') }}</span>
        <input v-model.trim="displayName" maxlength="60"
               :placeholder="$t('agileTraining.scrumRoles.yourNamePh')" />
      </label>
      <button class="sr-btn sr-btn--primary" :disabled="!displayName" @click="start">
        {{ $t('agileTraining.scrumRoles.startBtn') }} →
      </button>
    </section>

    <!-- ШАГ 2: контекст -->
    <section v-else-if="step === 'context'" class="sr-play__section sr-ctx">
      <h2>🎯 {{ $t('agileTraining.scrumRoles.contextTitle') }}</h2>
      <p class="sr-ctx__lead">{{ $t('agileTraining.scrumRoles.contextLead') }}</p>
      <ul class="sr-ctx__list">
        <li>✅ {{ $t('agileTraining.scrumRoles.contextItem1') }}</li>
        <li>✅ {{ $t('agileTraining.scrumRoles.contextItem2') }}</li>
        <li>✅ {{ $t('agileTraining.scrumRoles.contextItem3') }}</li>
      </ul>
      <p class="sr-play__hint">{{ $t('agileTraining.scrumRoles.contextHint') }}</p>
      <button class="sr-btn sr-btn--primary" @click="step = 'roles'">
        {{ $t('agileTraining.scrumRoles.nextBtn') }} →
      </button>
    </section>

    <!-- ШАГ 3: обзор ролей -->
    <section v-else-if="step === 'roles'" class="sr-play__section">
      <h2>👥 {{ $t('agileTraining.scrumRoles.rolesTitle') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.rolesLead') }}</p>
      <div class="sr-roles">
        <article v-for="r in content.roles" :key="r.key" class="sr-role">
          <div class="sr-role__emoji">{{ r.emoji }}</div>
          <h3>{{ r.title }}</h3>
          <p class="sr-role__desc">{{ r.desc }}</p>
          <p class="sr-role__focus">
            <b>{{ $t('agileTraining.scrumRoles.focus') }}:</b> {{ r.focus }}
          </p>
        </article>
      </div>
      <button class="sr-btn sr-btn--primary" @click="openDistribute">
        {{ $t('agileTraining.scrumRoles.goDistribute') }} →
      </button>
    </section>

    <!-- ШАГ 4: распределение — ключевой экран -->
    <section v-else-if="step === 'distribute'" class="sr-play__section">
      <h2>🧩 {{ $t('agileTraining.scrumRoles.distributeTitle') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.distributeLead') }}</p>
      <div class="sr-legend">
        <span v-for="l in content.levels" :key="l.key">
          {{ l.emoji }} {{ l.title }}
        </span>
      </div>
      <div class="sr-cards-grid">
        <article v-for="c in orderedPlayCards" :key="c.key" class="sr-card">
          <div class="sr-card__title">{{ c.title }}</div>
          <p v-if="c.subtitle" class="sr-card__subtitle">{{ c.subtitle }}</p>
          <div class="sr-card__roles">
            <div v-for="r in content.roles" :key="r.key" class="sr-card__role">
              <div class="sr-card__role-name">
                <span>{{ r.emoji }}</span>
                <span>{{ r.title }}</span>
              </div>
              <div class="sr-chip-row">
                <button v-for="l in content.levels" :key="l.key"
                        type="button"
                        class="sr-chip"
                        :class="[
                          'sr-chip--' + l.key,
                          { 'sr-chip--active': selection[c.key]?.[r.key] === l.key },
                        ]"
                        @click="setLevel(c.key, r.key, l.key)">
                  {{ l.emoji }} {{ l.title }}
                </button>
                <button type="button"
                        class="sr-chip sr-chip--clear"
                        :class="{ 'sr-chip--active': !selection[c.key]?.[r.key] }"
                        @click="setLevel(c.key, r.key, null)">—</button>
              </div>
            </div>
          </div>
        </article>
      </div>
      <div class="sr-actions">
        <button class="sr-btn sr-btn--ghost" @click="step = 'roles'">← {{ $t('agileTraining.scrumRoles.backBtn') }}</button>
        <button class="sr-btn sr-btn--primary" @click="goWhy">
          {{ $t('agileTraining.scrumRoles.toWhy') }} →
        </button>
      </div>
    </section>

    <!-- ШАГ 5: зачем это нужно -->
    <section v-else-if="step === 'why'" class="sr-play__section">
      <h2>💡 {{ $t('agileTraining.scrumRoles.whyTitle') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.whyLead') }}</p>
      <ul class="sr-why">
        <li v-for="c in orderedPlayCards" :key="c.key">
          <b>{{ c.title }}</b>
          <div v-if="c.subtitle" class="sr-why__subtitle">{{ c.subtitle }}</div>
          <div class="sr-play__hint">{{ c.rationale }}</div>
        </li>
      </ul>
      <div class="sr-actions">
        <button class="sr-btn sr-btn--ghost" @click="step = 'distribute'">← {{ $t('agileTraining.scrumRoles.backBtn') }}</button>
        <button class="sr-btn sr-btn--primary" @click="step = 'errors'">
          {{ $t('agileTraining.scrumRoles.toErrors') }} →
        </button>
      </div>
    </section>

    <!-- ШАГ 6: типичные ошибки -->
    <section v-else-if="step === 'errors'" class="sr-play__section">
      <h2>⚠️ {{ $t('agileTraining.scrumRoles.errorsTitle') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.errorsLead') }}</p>
      <div class="sr-err-grid">
        <article v-for="e in content.errors" :key="e.key"
                 class="sr-err-card"
                 :class="{ 'sr-err-card--active': errorsSeen.includes(e.key) }"
                 @click="toggleError(e.key)">
          <div class="sr-err-card__head">
            <span class="sr-err-card__check">{{ errorsSeen.includes(e.key) ? '☑' : '☐' }}</span>
            <b>{{ e.title }}</b>
          </div>
          <ul>
            <li v-for="(c, i) in e.consequences" :key="i">→ {{ c }}</li>
          </ul>
        </article>
      </div>
      <div class="sr-actions">
        <button class="sr-btn sr-btn--ghost" @click="step = 'why'">← {{ $t('agileTraining.scrumRoles.backBtn') }}</button>
        <button class="sr-btn sr-btn--primary" @click="goFix">
          {{ $t('agileTraining.scrumRoles.toFix') }} →
        </button>
      </div>
    </section>

    <!-- ШАГ 7: исправление -->
    <section v-else-if="step === 'fix'" class="sr-play__section">
      <h2>🛠 {{ $t('agileTraining.scrumRoles.fixTitle') }}</h2>
      <p class="sr-play__lead">{{ $t('agileTraining.scrumRoles.fixLead') }}</p>
      <div v-if="cardsToFix.length === 0" class="sr-play__hint">
        ✅ {{ $t('agileTraining.scrumRoles.fixNothing') }}
      </div>
      <div v-else class="sr-cards-grid">
        <article v-for="c in shuffledCardsToFix" :key="c.key" class="sr-card sr-card--warn">
          <div class="sr-card__title">{{ c.title }}</div>
          <p v-if="c.subtitle" class="sr-card__subtitle">{{ c.subtitle }}</p>
          <div class="sr-play__hint">💡 {{ c.rationale }}</div>
          <div class="sr-card__roles">
            <div v-for="r in content.roles" :key="r.key" class="sr-card__role">
              <div class="sr-card__role-name">
                <span>{{ r.emoji }}</span>
                <span>{{ r.title }}</span>
              </div>
              <div class="sr-chip-row">
                <button v-for="l in content.levels" :key="l.key"
                        type="button"
                        class="sr-chip"
                        :class="[
                          'sr-chip--' + l.key,
                          { 'sr-chip--active': selection[c.key]?.[r.key] === l.key },
                        ]"
                        @click="setLevel(c.key, r.key, l.key)">
                  {{ l.emoji }} {{ l.title }}
                </button>
                <button type="button"
                        class="sr-chip sr-chip--clear"
                        :class="{ 'sr-chip--active': !selection[c.key]?.[r.key] }"
                        @click="setLevel(c.key, r.key, null)">—</button>
              </div>
            </div>
          </div>
        </article>
      </div>
      <div class="sr-actions">
        <button class="sr-btn sr-btn--ghost" @click="step = 'errors'">← {{ $t('agileTraining.scrumRoles.backBtn') }}</button>
        <button class="sr-btn sr-btn--primary" @click="finish">
          {{ $t('agileTraining.scrumRoles.finishBtn') }} →
        </button>
      </div>
    </section>

    <!-- ШАГ 8: итоговая доска по ролям -->
    <section v-else-if="step === 'final'" class="sr-play__section">
      <h2>🖼 {{ $t('agileTraining.scrumRoles.finalTitle') }}</h2>
      <p class="sr-pdf-bar">
        <button
          type="button"
          class="sr-btn sr-btn--ghost"
          :disabled="pdfExporting"
          @click="exportResultPdf"
        >
          {{ pdfExporting ? $t('agileTraining.common.downloadPdfLoading') : $t('agileTraining.common.downloadPdf') }}
        </button>
      </p>

      <div ref="pdfExportRoot" class="sr-pdf-root">
        <div class="sr-final-score">
          <div>
            <div class="sr-final-score__label">{{ $t('agileTraining.scrumRoles.yourHealth') }}</div>
            <div class="sr-final-score__value" :class="healthClass(myHealth)">{{ myHealth }}%</div>
          </div>
          <div v-if="groupResults && groupResults.participants_count > 1">
            <div class="sr-final-score__label">{{ $t('agileTraining.scrumRoles.groupHealth') }}</div>
            <div class="sr-final-score__value">{{ groupResults.avg_health_pct }}%</div>
          </div>
        </div>

        <div class="sr-color-totals">
          <span class="sr-pill sr-pill--green">🟢 {{ evalTotals.green }}</span>
          <span class="sr-pill sr-pill--yellow">🟡 {{ evalTotals.yellow }}</span>
          <span class="sr-pill sr-pill--red">🔴 {{ evalTotals.red }}</span>
          <span class="sr-pill sr-pill--muted">◻ {{ $t('agileTraining.scrumRoles.missingLabel') }}: {{ evalTotals.missing }}</span>
        </div>

        <div class="sr-board">
          <article v-for="r in content.roles" :key="r.key" class="sr-board__col">
            <header class="sr-board__col-head">
              <div class="sr-board__emoji">{{ r.emoji }}</div>
              <h3>{{ r.title }}</h3>
              <p>{{ r.desc }}</p>
            </header>
            <div class="sr-board__buckets">
              <div class="sr-board__bucket sr-board__bucket--responsible">
                <h4>🟢 {{ $t('agileTraining.scrumRoles.levels.responsible') }}</h4>
                <div v-for="c in cardsPerRole(r.key, 'responsible')" :key="'b1-' + r.key + '-' + c.key"
                     class="sr-sticker" :class="'sr-sticker--' + stickerColor(c.key, r.key)">
                  {{ c.title }}
                </div>
              </div>
              <div class="sr-board__bucket sr-board__bucket--participates">
                <h4>🟡 {{ $t('agileTraining.scrumRoles.levels.participates') }}</h4>
                <div v-for="c in cardsPerRole(r.key, 'participates')" :key="'b2-' + r.key + '-' + c.key"
                     class="sr-sticker" :class="'sr-sticker--' + stickerColor(c.key, r.key)">
                  {{ c.title }}
                </div>
              </div>
              <div class="sr-board__bucket sr-board__bucket--should_not">
                <h4>🔴 {{ $t('agileTraining.scrumRoles.levels.should_not') }}</h4>
                <div v-for="c in cardsPerRole(r.key, 'should_not')" :key="'b3-' + r.key + '-' + c.key"
                     class="sr-sticker" :class="'sr-sticker--' + stickerColor(c.key, r.key)">
                  {{ c.title }}
                </div>
              </div>
            </div>
          </article>
        </div>

        <div v-if="groupResults && groupResults.cards?.length" class="sr-compare">
          <h3>👥 {{ $t('agileTraining.scrumRoles.compareTitle') }}</h3>
          <p class="sr-play__hint">{{ $t('agileTraining.scrumRoles.compareLead') }}</p>
          <div class="sr-compare__grid">
            <div v-for="c in groupResults.cards" :key="'cmp-' + c.key" class="sr-compare__item">
              <b>{{ c.title }}</b>
              <div v-for="r in content.roles" :key="'cmp-' + c.key + '-' + r.key" class="sr-compare__row">
                <span class="sr-compare__role">{{ r.emoji }} {{ r.title }}</span>
                <span v-for="lv in (c.roles?.[r.key]?.levels || [])" :key="'cmp-' + c.key + '-' + r.key + '-' + (lv.level || 'n')"
                      class="sr-pill" :class="lv.level ? 'sr-pill--' + lv.level : 'sr-pill--muted'">
                  {{ levelEmoji(lv.level) }} {{ lv.pct }}%
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="sr-custom">
        <button type="button" class="sr-fac__participants-toggle sr-fac__open-btn"
                @click="customOpen = !customOpen">
          {{ customOpen ? '▾' : '▸' }} {{ $t('agileTraining.scrumRoles.customToggle') }}
        </button>
        <div v-if="customOpen" class="sr-custom__body">
          <p class="sr-play__hint">{{ $t('agileTraining.scrumRoles.customLead') }}</p>

          <h4 class="sr-section-title">✨ {{ $t('agileTraining.scrumRoles.customCards') }}</h4>
          <div v-for="(cc, i) in customCards" :key="'cc-' + i" class="sr-custom__card">
            <input v-model="cc.title" :placeholder="$t('agileTraining.scrumRoles.customCardPh')" maxlength="160" />
            <div class="sr-chip-row">
              <template v-for="r in content.roles" :key="'cc-' + i + '-' + r.key">
                <div class="sr-custom__role">
                  <span>{{ r.emoji }} {{ r.title }}</span>
                  <select v-model="cc.assigned[r.key]">
                    <option :value="null">—</option>
                    <option v-for="l in content.levels" :key="l.key" :value="l.key">{{ l.emoji }} {{ l.title }}</option>
                  </select>
                </div>
              </template>
            </div>
            <button class="sr-btn sr-btn--ghost" @click="removeCustomCard(i)">
              {{ $t('agileTraining.scrumRoles.remove') }}
            </button>
          </div>
          <button class="sr-btn sr-btn--ghost" @click="addCustomCard" :disabled="customCards.length >= 5">
            + {{ $t('agileTraining.scrumRoles.addCustomCard') }}
          </button>

          <h4 class="sr-section-title">🧑‍🤝‍🧑 {{ $t('agileTraining.scrumRoles.customRole') }}</h4>
          <div class="sr-custom__role-form">
            <input v-model="customRole.title" :placeholder="$t('agileTraining.scrumRoles.customRoleTitle')" maxlength="120" />
            <input v-model="customRole.desc" :placeholder="$t('agileTraining.scrumRoles.customRoleDesc')" maxlength="240" />
          </div>
          <button class="sr-btn sr-btn--primary" @click="saveCustom">
            {{ $t('agileTraining.scrumRoles.saveCustom') }}
          </button>
        </div>
      </div>

      <div class="sr-actions">
        <button class="sr-btn sr-btn--ghost" @click="step = 'fix'">← {{ $t('agileTraining.scrumRoles.backBtn') }}</button>
      </div>
    </section>
  </div>
</template>

<script>
import axios from 'axios';
import exportElementToPdf from '@/utils/trainingPdfExport.js';

const STORAGE_NS = 'agile_training_scrum_roles';

function uuid() {
  if (window.crypto?.randomUUID) return window.crypto.randomUUID();
  return 'p-' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default {
  name: 'AgileScrumRolesPlay',
  props: {
    slug: { type: String, required: true },
    prefetchedSession: { type: Object, default: null },
  },
  data() {
    return {
      ready: false,
      step: 'start',
      content: null,
      effectiveLocale: 'ru',
      sessionLocale: 'ru',
      groupName: '',
      participantToken: '',
      displayName: '',
      selection: {},
      errorsSeen: [],
      customOpen: false,
      customCards: [],
      customRole: { title: '', desc: '' },
      groupResults: null,
      evaluation: null,
      customLocale: null,
      pdfExporting: false,
      /** Порядок карточек на шаге «Распределение» (перемешивается для усложнения) */
      cardPlayOrder: null,
      /** Порядок карточек на шаге «Исправление» */
      fixCardOrder: null,
    };
  },
  computed: {
    evalTotals() {
      return this.evaluation?.total
        || { green: 0, yellow: 0, red: 0, missing: 0, health_pct: 0, score: 0 };
    },
    myHealth() { return this.evalTotals.health_pct || 0; },
    cardsToFix() {
      if (!this.evaluation?.cards) return [];
      const warn = Object.entries(this.evaluation.cards)
        .filter(([, v]) => v.color !== 'green')
        .map(([k]) => k);
      return (this.content?.cards || []).filter(c => warn.includes(c.key));
    },
    orderedPlayCards() {
      const cards = this.content?.cards || [];
      if (!this.cardPlayOrder?.length
          || this.cardPlayOrder.length !== cards.length) {
        return cards;
      }
      const map = new Map(cards.map(c => [c.key, c]));
      return this.cardPlayOrder.map(k => map.get(k)).filter(Boolean);
    },
    shuffledCardsToFix() {
      const list = this.cardsToFix;
      if (!this.fixCardOrder?.length) return list;
      const map = new Map(list.map(c => [c.key, c]));
      return this.fixCardOrder.map(k => map.get(k)).filter(Boolean);
    },
  },
  async mounted() {
    const tokenKey = `${STORAGE_NS}:${this.slug}:participantToken`;
    const nameKey = `${STORAGE_NS}:${this.slug}:displayName`;
    this.participantToken = localStorage.getItem(tokenKey) || uuid();
    localStorage.setItem(tokenKey, this.participantToken);
    this.displayName = localStorage.getItem(nameKey) || '';
    this.customLocale = localStorage.getItem(`${STORAGE_NS}:${this.slug}:locale`);
    await this.loadState();
    this.ready = true;
  },
  methods: {
    shuffleKeys(keys) {
      const a = keys.slice();
      for (let i = a.length - 1; i > 0; i -= 1) {
        const j = Math.floor(Math.random() * (i + 1));
        [a[i], a[j]] = [a[j], a[i]];
      }
      return a;
    },
    openDistribute() {
      const cards = this.content?.cards || [];
      this.cardPlayOrder = this.shuffleKeys(cards.map(c => c.key));
      this.step = 'distribute';
    },
    async loadState() {
      try {
        const params = { participant_token: this.participantToken };
        if (this.customLocale) params.locale = this.customLocale;
        const r = await axios.get(
          `/api/agile-training/scrum-roles/g/${this.slug}/state`,
          { params });
        this.content = r.data.content;
        this.sessionLocale = r.data.session_locale || 'ru';
        this.effectiveLocale = r.data.effective_locale || this.sessionLocale;
        this.groupName = r.data.group?.name || '';
        if (this.$i18n && this.effectiveLocale
            && this.$i18n.locale !== this.effectiveLocale
            && !this.customLocale) {
          this.$i18n.locale = this.effectiveLocale;
        }
        if (r.data.answer?.data) {
          this.selection = r.data.answer.data.selection || {};
          this.errorsSeen = r.data.answer.data.errors_seen || [];
          this.customCards = (r.data.answer.data.custom_cards || [])
            .map(cc => ({ title: cc.title, assigned: { ...cc.assigned } }));
          this.customRole = r.data.answer.data.custom_role
            || { title: '', desc: '' };
          this.evaluation = r.data.answer.data.evaluation || null;
          this.step = 'final';
          await this.refreshGroupResults();
        }
      } catch (e) { console.error(e); }
    },
    async switchLocale(lc) {
      if (lc === this.effectiveLocale) return;
      this.customLocale = lc;
      localStorage.setItem(`${STORAGE_NS}:${this.slug}:locale`, lc);
      this.$i18n.locale = lc;
      await this.loadState();
    },
    async ensureParticipant() {
      const tokenKey = `${STORAGE_NS}:${this.slug}:participantToken`;
      const res = await axios.post(
        `/api/agile-training/g/${this.slug}/participant`,
        {
          display_name: (this.displayName || '').trim() || null,
          participant_token: this.participantToken,
        },
      );
      if (res.data?.participant_token) {
        this.participantToken = res.data.participant_token;
        localStorage.setItem(tokenKey, this.participantToken);
      }
    },
    async start() {
      if (!this.displayName) return;
      this.cardPlayOrder = null;
      this.fixCardOrder = null;
      localStorage.setItem(`${STORAGE_NS}:${this.slug}:displayName`, this.displayName);
      try {
        await this.ensureParticipant();
      } catch (e) {
        console.error(e);
        alert(
          e.response?.data?.error
          || this.$t('agileTraining.common.saveFailed'),
        );
        return;
      }
      this.step = 'context';
    },
    setLevel(cardKey, roleKey, level) {
      const prev = this.selection[cardKey] || {};
      this.selection = {
        ...this.selection,
        [cardKey]: { ...prev, [roleKey]: level },
      };
    },
    async goWhy() {
      await this.persist(false);
      this.step = 'why';
    },
    toggleError(k) {
      if (this.errorsSeen.includes(k)) {
        this.errorsSeen = this.errorsSeen.filter(e => e !== k);
      } else {
        this.errorsSeen = [...this.errorsSeen, k];
      }
    },
    async goFix() {
      await this.persist(false);
      const toFix = this.cardsToFix;
      this.fixCardOrder = toFix.length
        ? this.shuffleKeys(toFix.map(c => c.key))
        : [];
      this.step = 'fix';
    },
    async finish() {
      await this.persist(true);
      this.step = 'final';
      await this.refreshGroupResults();
    },
    async persist(final) {
      const postAnswer = async () => {
        const r = await axios.post(
          `/api/agile-training/scrum-roles/g/${this.slug}/answer`,
          {
            participant_token: this.participantToken,
            selection: this.selection,
            errors_seen: this.errorsSeen,
            custom_cards: this.customCards,
            custom_role: this.customRole,
          },
        );
        this.evaluation = r.data.evaluation;
      };
      try {
        await postAnswer();
      } catch (e) {
        const msg = String((e.response?.data?.error) || '');
        const notFound = e.response?.status === 404
          && /participant/i.test(msg);
        if (notFound) {
          try {
            await this.ensureParticipant();
            await postAnswer();
            return;
          } catch (e2) {
            console.error(e2);
            if (final) {
              alert(
                e2.response?.data?.error
                || this.$t('agileTraining.common.saveFailed'),
              );
            }
            return;
          }
        }
        console.error(e);
        if (final) {
          alert(
            e.response?.data?.error
            || this.$t('agileTraining.common.saveFailed'),
          );
        }
      }
    },
    async refreshGroupResults() {
      try {
        const params = {};
        if (this.customLocale) params.locale = this.customLocale;
        const r = await axios.get(
          `/api/agile-training/scrum-roles/g/${this.slug}/results`, { params });
        this.groupResults = r.data;
      } catch (_) { this.groupResults = null; }
    },
    cardsPerRole(roleKey, level) {
      return (this.content?.cards || []).filter(c => {
        const picked = (this.selection[c.key] || {})[roleKey];
        if (level === 'should_not') return picked === 'should_not' || picked === null || picked === undefined;
        return picked === level;
      });
    },
    stickerColor(cardKey, roleKey) {
      const col = this.evaluation?.cards?.[cardKey]?.roles?.[roleKey]?.color;
      return col || 'gray';
    },
    healthClass(v) {
      if (v >= 70) return 'sr-final-score__value--ok';
      if (v >= 40) return 'sr-final-score__value--warn';
      return 'sr-final-score__value--bad';
    },
    levelEmoji(key) {
      if (!key) return '◻';
      const l = this.content.levels.find(x => x.key === key);
      return l ? l.emoji : '·';
    },
    addCustomCard() {
      if (this.customCards.length >= 5) return;
      this.customCards.push({
        title: '',
        assigned: { po: null, team: null, sm: null },
      });
    },
    removeCustomCard(i) { this.customCards.splice(i, 1); },
    async saveCustom() { await this.persist(true); },
    async exportResultPdf() {
      const el = this.$refs.pdfExportRoot;
      if (!el) return;
      this.pdfExporting = true;
      try {
        const res = await exportElementToPdf(el, `agile-scrum-roles-${this.slug}`);
        if (!res.ok) throw new Error(res.error || 'export');
      } catch (e) {
        console.error(e);
        alert(this.$t('agileTraining.common.downloadPdfError'));
      } finally {
        this.pdfExporting = false;
      }
    },
  },
};
</script>

<style scoped>
.sr-pdf-bar { margin: 0 0 12px; }
.sr-pdf-root { min-height: 20px; }
.sr-play {
  max-width: 1180px; margin: 0 auto; padding: 22px 18px 60px; color: #0f172a;
  font-family: "Segoe UI", system-ui, -apple-system, Roboto, "Noto Sans", "Helvetica Neue", Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}
.sr-play__head { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 16px; gap: 10px; flex-wrap: wrap; }
.sr-play__group { color: #7c3aed; font-weight: 700; font-size: 13px; }
.sr-play__head h1 { margin: 4px 0 0; font-size: 22px; line-height: 1.3; font-weight: 800; }
.sr-play__lang { display: flex; gap: 6px; }
.sr-lang__btn {
  padding: 6px 12px !important; border: 1px solid #cbd5e1 !important; border-radius: 10px !important;
  background: #fff !important; cursor: pointer; font-weight: 700; font-size: 12px;
}
.sr-lang__btn.active { background: #7c3aed !important; color: #fff !important; border-color: #7c3aed !important; }
.sr-lang__btn:hover { background: #f1f5f9 !important; }
.sr-lang__btn.active:hover { background: #6d28d9 !important; }

.sr-play__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 18px; padding: 22px 20px; margin-bottom: 14px; }
.sr-play__lead { margin: 0 0 12px; color: #475569; font-size: 15px; }
.sr-play__hint { color: #64748b; font-size: 13px; margin: 6px 0; }
.sr-play__field { display: flex; flex-direction: column; gap: 4px; margin-bottom: 16px; max-width: 400px; }
.sr-play__field input {
  padding: 10px 12px; border-radius: 12px; border: 1px solid #cbd5e1; font-size: 14px;
}

.sr-btn {
  padding: 10px 18px !important; border: none !important; border-radius: 12px !important;
  font-weight: 700; cursor: pointer; font-size: 14px;
}
.sr-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.sr-btn--primary {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important; color: #fff !important;
}
.sr-btn--primary:hover:not(:disabled) { background: linear-gradient(135deg, #7c3aed, #6d28d9) !important; }
.sr-btn--primary:active:not(:disabled) { transform: translateY(1px); }
.sr-btn--ghost {
  background: #f1f5f9 !important; color: #0f172a !important; border: 1px solid #e2e8f0 !important;
}
.sr-btn--ghost:hover:not(:disabled) { background: #e2e8f0 !important; }

.sr-actions { display: flex; gap: 8px; justify-content: flex-end; margin-top: 16px; flex-wrap: wrap; }

.sr-ctx { background: linear-gradient(135deg, #f5f3ff, #ede9fe); border-color: #c7d2fe; }
.sr-ctx__lead { font-size: 16px; }
.sr-ctx__list { list-style: none; padding: 0; margin: 0 0 10px; display: flex; flex-direction: column; gap: 6px; font-size: 14px; }

.sr-roles { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 12px; margin: 14px 0; }
.sr-role { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 16px; padding: 14px; }
.sr-role__emoji { font-size: 28px; }
.sr-role h3 { margin: 6px 0; font-size: 16px; }
.sr-role__desc { margin: 0 0 6px; color: #334155; font-size: 13px; }
.sr-role__focus { margin: 0; color: #7c3aed; font-size: 12px; }

.sr-legend { display: flex; gap: 10px; flex-wrap: wrap; font-size: 14px; color: #334155; margin-bottom: 12px; line-height: 1.4; }
.sr-cards-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; margin-bottom: 14px; }
.sr-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 14px; padding: 12px; }
.sr-card--warn { border-color: #f59e0b; background: #fffbeb; }
.sr-card__title { font-weight: 800; margin-bottom: 6px; font-size: 17px; line-height: 1.35; color: #0f172a; }
.sr-card__subtitle { margin: 0 0 10px; font-size: 13px; line-height: 1.45; color: #475569; font-weight: 500; }
.sr-why__subtitle { font-size: 14px; line-height: 1.45; color: #475569; margin: 4px 0 6px; font-weight: 500; }
.sr-card__roles { display: flex; flex-direction: column; gap: 6px; }
.sr-card__role { background: #f8fafc; border-radius: 10px; padding: 8px; }
.sr-card__role-name { display: flex; gap: 6px; align-items: center; font-size: 13px; font-weight: 700; margin-bottom: 4px; }
.sr-chip-row { display: flex; gap: 4px; flex-wrap: wrap; }
.sr-chip {
  padding: 6px 12px !important; border: 1px solid #cbd5e1 !important; border-radius: 999px !important;
  background: #fff !important; cursor: pointer; font-size: 13px; font-weight: 600; line-height: 1.3;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}
.sr-chip:hover { background: #f1f5f9 !important; }
.sr-chip--active {
  border-color: transparent !important;
}
.sr-chip--responsible.sr-chip--active { background: #86efac !important; color: #064e3b !important; }
.sr-chip--participates.sr-chip--active { background: #fcd34d !important; color: #78350f !important; }
.sr-chip--should_not.sr-chip--active   { background: #fca5a5 !important; color: #7f1d1d !important; }
.sr-chip--clear.sr-chip--active        { background: #cbd5e1 !important; color: #0f172a !important; }

.sr-why { list-style: none; padding: 0; margin: 0 0 12px; display: flex; flex-direction: column; gap: 8px; }
.sr-why li { padding: 10px 12px; border: 1px solid #e2e8f0; border-radius: 12px; background: #f8fafc; font-size: 14px; }

.sr-err-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; margin-bottom: 8px; }
.sr-err-card {
  padding: 12px; border: 2px solid #e2e8f0 !important; border-radius: 14px !important;
  background: #fff !important; cursor: pointer; text-align: left; font-family: inherit;
  transition: border-color 0.15s, background 0.15s;
}
.sr-err-card:hover { background: #f8fafc !important; border-color: #cbd5e1 !important; }
.sr-err-card--active { border-color: #ef4444 !important; background: #fef2f2 !important; }
.sr-err-card__head { display: flex; gap: 8px; margin-bottom: 6px; align-items: center; font-size: 14px; }
.sr-err-card__check { font-size: 18px; }
.sr-err-card ul { list-style: none; padding: 0; margin: 0; font-size: 12px; color: #475569; }
.sr-err-card li { padding: 2px 0; }

.sr-final-score { display: flex; gap: 30px; margin: 10px 0 14px; flex-wrap: wrap; }
.sr-final-score__label { font-size: 12px; color: #64748b; margin-bottom: 4px; }
.sr-final-score__value { font-size: 32px; font-weight: 900; color: #0f172a; }
.sr-final-score__value--ok { color: #047857; }
.sr-final-score__value--warn { color: #92400e; }
.sr-final-score__value--bad { color: #991b1b; }

.sr-color-totals { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 14px; }
.sr-pill { display: inline-block; background: #e2e8f0; padding: 2px 10px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.sr-pill--green { background: #dcfce7; color: #047857; }
.sr-pill--yellow { background: #fef3c7; color: #92400e; }
.sr-pill--red { background: #fee2e2; color: #991b1b; }
.sr-pill--responsible { background: #dcfce7; color: #047857; }
.sr-pill--participates { background: #fef3c7; color: #92400e; }
.sr-pill--should_not { background: #fee2e2; color: #991b1b; }
.sr-pill--muted { background: #f1f5f9; color: #64748b; }

.sr-board { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 12px; margin-top: 12px; padding: 14px; background: #fafaf9; border-radius: 16px; border: 1px dashed #cbd5e1; }
.sr-board__col { background: #fff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 10px; }
.sr-board__col-head { border-bottom: 1px dashed #e2e8f0; padding-bottom: 8px; margin-bottom: 10px; }
.sr-board__emoji { font-size: 24px; }
.sr-board__col-head h3 { margin: 4px 0 2px; font-size: 16px; line-height: 1.3; font-weight: 800; }
.sr-board__col-head p { margin: 0; font-size: 13px; line-height: 1.45; color: #475569; }
.sr-board__buckets { display: flex; flex-direction: column; gap: 10px; }
.sr-board__bucket { border-radius: 10px; padding: 8px; background: #f8fafc; }
.sr-board__bucket--responsible { background: #f0fdf4; }
.sr-board__bucket--participates { background: #fffbeb; }
.sr-board__bucket--should_not { background: #fef2f2; }
.sr-board__bucket h4 { margin: 0 0 6px; font-size: 13px; line-height: 1.35; color: #334155; font-weight: 700; }
.sr-sticker {
  background: #fef08a; padding: 6px 8px; border-radius: 6px; font-size: 12px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.08); margin-bottom: 4px;
  line-height: 1.3;
}
.sr-sticker--green { background: #bbf7d0; }
.sr-sticker--yellow { background: #fde68a; }
.sr-sticker--red { background: #fecaca; }
.sr-sticker--missing { background: #e2e8f0; color: #64748b; font-style: italic; }
.sr-sticker--gray { background: #f1f5f9; color: #64748b; }

.sr-compare { margin-top: 16px; padding: 14px; border: 1px solid #e2e8f0; border-radius: 14px; background: #fafafa; }
.sr-compare__grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
.sr-compare__item { padding: 8px; background: #fff; border-radius: 10px; border: 1px solid #e2e8f0; font-size: 12px; }
.sr-compare__row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-top: 4px; }
.sr-compare__role { font-weight: 700; color: #334155; min-width: 120px; }

.sr-custom { margin-top: 14px; }
.sr-custom__body { margin-top: 10px; padding: 12px; border: 1px dashed #cbd5e1; border-radius: 14px; background: #fafafa; }
.sr-custom__card { margin-bottom: 10px; padding: 10px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; display: flex; flex-direction: column; gap: 6px; }
.sr-custom__card input {
  padding: 8px 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px;
}
.sr-custom__role { display: flex; justify-content: space-between; align-items: center; gap: 6px; font-size: 12px; }
.sr-custom__role select { padding: 4px 8px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 12px; }
.sr-custom__role-form { display: flex; flex-direction: column; gap: 6px; margin-bottom: 8px; }
.sr-custom__role-form input { padding: 8px 10px; border-radius: 8px; border: 1px solid #cbd5e1; font-size: 13px; }
.sr-fac__open-btn, .sr-fac__participants-toggle {
  background: #f1f5f9 !important; border: 1px solid #e2e8f0 !important; padding: 8px 14px !important;
  border-radius: 12px !important; cursor: pointer; font-weight: 700; font-size: 13px;
}
.sr-fac__open-btn:hover, .sr-fac__participants-toggle:hover { background: #e2e8f0 !important; }
.sr-section-title { margin: 14px 0 6px; font-size: 14px; font-weight: 800; }
</style>
