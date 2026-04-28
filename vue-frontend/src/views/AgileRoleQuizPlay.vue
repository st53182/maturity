<template>
  <div class="rq-play" v-if="ready">
    <header class="rq-play__head">
      <div>
        <div class="rq-play__group">🎯 {{ groupName }}</div>
        <h1>{{ $t('agileTraining.roleQuiz.playTitle') }}</h1>
      </div>
      <div class="rq-play__lang">
        <button class="rq-lang__btn" :class="{ active: effectiveLocale === 'ru' }" @click="switchLocale('ru')">RU</button>
        <button class="rq-lang__btn" :class="{ active: effectiveLocale === 'en' }" @click="switchLocale('en')">EN</button>
      </div>
    </header>

    <!-- Welcome -->
    <section v-if="step === 'start'" class="rq-play__section">
      <h2>👋 {{ $t('agileTraining.roleQuiz.welcome') }}</h2>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.welcomeLead') }}</p>
      <ul class="rq-context">
        <li>📋 {{ $t('agileTraining.roleQuiz.contextItem1', { n: situationsCount }) }}</li>
        <li>🧠 {{ $t('agileTraining.roleQuiz.contextItem2') }}</li>
        <li>💡 {{ $t('agileTraining.roleQuiz.contextItem3') }}</li>
      </ul>
      <label class="rq-play__field">
        <span>{{ $t('agileTraining.roleQuiz.yourName') }}</span>
        <input v-model.trim="displayName" maxlength="60"
               :placeholder="$t('agileTraining.roleQuiz.yourNamePh')" />
      </label>
      <button class="rq-btn rq-btn--primary" :disabled="!displayName || joining" @click="start">
        {{ $t('agileTraining.roleQuiz.startBtn') }} →
      </button>
      <p v-if="joinError" class="rq-error">{{ joinError }}</p>
    </section>

    <!-- Roles + RACI legend -->
    <section v-else-if="step === 'intro'" class="rq-play__section">
      <h2>👥 {{ $t('agileTraining.roleQuiz.rolesTitle') }}</h2>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.rolesLead') }}</p>
      <div class="rq-roles">
        <article v-for="r in content.roles" :key="r.key" class="rq-role">
          <div class="rq-role__emoji">{{ r.emoji }}</div>
          <h3>{{ r.title }}</h3>
          <p class="rq-role__desc">{{ r.desc }}</p>
        </article>
      </div>
      <h3 class="rq-section-h">🟦 {{ $t('agileTraining.roleQuiz.legendTitle') }}</h3>
      <p class="rq-play__hint">{{ $t('agileTraining.roleQuiz.legendLead') }}</p>
      <ul class="rq-legend">
        <li v-for="l in content.levels" :key="l.key" :class="`rq-legend__item rq-legend__item--${l.key}`">
          <span class="rq-legend__emoji">{{ l.emoji }}</span>
          <div>
            <b>{{ l.title }}</b>
            <span class="rq-legend__desc">{{ l.desc }}</span>
          </div>
        </li>
      </ul>
      <div class="rq-actions">
        <button class="rq-btn rq-btn--ghost" @click="step = 'start'">← {{ $t('agileTraining.roleQuiz.backBtn') }}</button>
        <button class="rq-btn rq-btn--primary" @click="step = 'quiz'">
          {{ $t('agileTraining.roleQuiz.toQuiz') }} →
        </button>
      </div>
    </section>

    <!-- Quiz: situations × roles -->
    <section v-else-if="step === 'quiz'" class="rq-play__section">
      <header class="rq-quiz__head">
        <h2>🧩 {{ $t('agileTraining.roleQuiz.quizTitle') }}</h2>
        <div class="rq-progress" v-if="situationsCount">
          <div class="rq-progress__bar"><div class="rq-progress__fill" :style="{ width: progressPct + '%' }"></div></div>
          <span class="rq-progress__label">{{ filledCount }} / {{ situationsCount }}</span>
        </div>
      </header>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.quizLead') }}</p>

      <div class="rq-legend rq-legend--inline">
        <span v-for="l in content.levels" :key="'mini-' + l.key" :class="`rq-mini rq-mini--${l.key}`">
          {{ l.emoji }} {{ l.short }}
        </span>
      </div>

      <article v-for="(s, idx) in content.situations" :key="s.key"
               class="rq-sit"
               :class="{ 'rq-sit--filled': isFilled(s.key) }">
        <header class="rq-sit__head">
          <div class="rq-sit__num">{{ idx + 1 }}</div>
          <div>
            <h3>{{ s.title }}</h3>
            <p v-if="s.subtitle" class="rq-sit__sub">{{ s.subtitle }}</p>
          </div>
        </header>
        <div class="rq-sit__roles">
          <div v-for="r in content.roles" :key="r.key" class="rq-sit__role">
            <div class="rq-sit__role-name">
              <span class="rq-sit__role-emoji">{{ r.emoji }}</span>
              <span>{{ r.title }}</span>
            </div>
            <div class="rq-chip-row">
              <button v-for="l in content.levels" :key="l.key"
                      type="button"
                      class="rq-chip"
                      :class="[
                        `rq-chip--${l.key}`,
                        { 'rq-chip--active': selection[s.key]?.[r.key] === l.key },
                      ]"
                      :title="l.title"
                      @click="setLevel(s.key, r.key, l.key)">
                {{ l.emoji }} <span class="rq-chip__short">{{ l.short }}</span>
              </button>
              <button type="button"
                      class="rq-chip rq-chip--clear"
                      :class="{ 'rq-chip--active': !selection[s.key]?.[r.key] }"
                      :title="$t('agileTraining.roleQuiz.clearChip')"
                      @click="setLevel(s.key, r.key, null)">—</button>
            </div>
          </div>
        </div>
        <p v-if="accountableWarning(s.key)" class="rq-warn">
          ⚠ {{ accountableWarning(s.key) }}
        </p>
      </article>

      <div class="rq-actions rq-actions--sticky">
        <button class="rq-btn rq-btn--ghost" @click="step = 'intro'">← {{ $t('agileTraining.roleQuiz.backBtn') }}</button>
        <button class="rq-btn rq-btn--primary" :disabled="!filledCount || saving" @click="submit">
          {{ saving ? $t('agileTraining.roleQuiz.savingBtn') : $t('agileTraining.roleQuiz.checkBtn') }} →
        </button>
      </div>
    </section>

    <!-- Result + per-situation explanations -->
    <section v-else-if="step === 'result' && evaluation" class="rq-play__section">
      <header class="rq-result__head">
        <h2>📊 {{ $t('agileTraining.roleQuiz.resultTitle') }}</h2>
        <div class="rq-result__score">
          <div>
            <div class="rq-result__score-num">{{ evaluation.total.health_pct }}%</div>
            <div class="rq-result__score-label">{{ $t('agileTraining.roleQuiz.health') }}</div>
          </div>
          <div class="rq-result__chips">
            <span class="rq-pill rq-pill--green">🟢 {{ evaluation.total.green }}</span>
            <span class="rq-pill rq-pill--yellow">🟡 {{ evaluation.total.yellow }}</span>
            <span class="rq-pill rq-pill--red">🔴 {{ evaluation.total.red }}</span>
            <span class="rq-pill rq-pill--muted">◻ {{ evaluation.total.missing }}</span>
          </div>
        </div>
      </header>
      <p class="rq-play__lead">
        {{ $t('agileTraining.roleQuiz.resultLead', {
          a: evaluation.accountable_correct,
          n: evaluation.answered,
        }) }}
      </p>

      <article v-for="(s, idx) in content.situations" :key="'res-' + s.key"
               class="rq-resi"
               :class="`rq-resi--${(evaluation.situations[s.key] || {}).color || 'green'}`">
        <header class="rq-resi__head">
          <span class="rq-resi__num">{{ idx + 1 }}</span>
          <h3>{{ s.title }}</h3>
          <span class="rq-resi__color">{{ resiColorIcon(s.key) }}</span>
        </header>
        <p v-if="s.subtitle" class="rq-resi__sub">{{ s.subtitle }}</p>
        <table class="rq-resi__table">
          <thead>
            <tr>
              <th>{{ $t('agileTraining.roleQuiz.role') }}</th>
              <th>{{ $t('agileTraining.roleQuiz.youPicked') }}</th>
              <th>{{ $t('agileTraining.roleQuiz.expected') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in content.roles" :key="'res-' + s.key + '-' + r.key"
                :class="`rq-resi__row rq-resi__row--${cellColor(s.key, r.key)}`">
              <td><span>{{ r.emoji }}</span> {{ r.title }}</td>
              <td>{{ pickedLabel(s.key, r.key) }}</td>
              <td>{{ expectedLabel(s.key, r.key) }}</td>
            </tr>
          </tbody>
        </table>
        <p class="rq-resi__why"><b>💡 {{ $t('agileTraining.roleQuiz.why') }}:</b> {{ s.rationale }}</p>
        <p v-if="s.common_mistake" class="rq-resi__pitfall">
          <b>⚠ {{ $t('agileTraining.roleQuiz.pitfall') }}:</b> {{ s.common_mistake }}
        </p>
      </article>

      <div class="rq-actions">
        <button class="rq-btn rq-btn--ghost" @click="goEditAgain">
          ↺ {{ $t('agileTraining.roleQuiz.tryAgain') }}
        </button>
        <button class="rq-btn rq-btn--primary" @click="goShareResults">
          📤 {{ $t('agileTraining.roleQuiz.shareResults') }}
        </button>
      </div>
    </section>
  </div>
  <div v-else class="rq-play__loading">{{ $t('common.loading') }}…</div>
</template>

<script>
import axios from 'axios';

const TOKEN_KEY_PREFIX = 'role_quiz_token:';
const NAME_KEY_PREFIX = 'role_quiz_name:';

function readLs(prefix, slug) {
  try { return localStorage.getItem(prefix + slug) || ''; } catch (_) { return ''; }
}
function writeLs(prefix, slug, value) {
  try { localStorage.setItem(prefix + slug, value || ''); } catch (_) { /* noop */ }
}

export default {
  name: 'AgileRoleQuizPlay',
  props: {
    slug: { type: String, default: '' },
  },
  data() {
    return {
      ready: false,
      step: 'start',
      content: { situations: [], roles: [], levels: [] },
      group: { name: '', slug: '' },
      effectiveLocale: 'ru',
      participantToken: '',
      displayName: '',
      joining: false,
      joinError: '',
      saving: false,
      selection: {},
      evaluation: null,
      notesSeen: [],
    };
  },
  computed: {
    routeSlug() { return this.slug || this.$route.params.slug; },
    groupName() { return this.group.name || '...'; },
    situationsCount() { return (this.content.situations || []).length; },
    filledCount() {
      let n = 0;
      for (const s of this.content.situations || []) {
        const row = this.selection[s.key] || {};
        if (Object.values(row).some((v) => !!v)) n += 1;
      }
      return n;
    },
    progressPct() {
      if (!this.situationsCount) return 0;
      return Math.round((this.filledCount / this.situationsCount) * 100);
    },
  },
  watch: {
    '$i18n.locale'(val) {
      if (val !== this.effectiveLocale) this.refreshContent(val);
    },
  },
  async mounted() {
    this.participantToken = readLs(TOKEN_KEY_PREFIX, this.routeSlug);
    this.displayName = readLs(NAME_KEY_PREFIX, this.routeSlug);
    await this.refreshContent(this.$i18n.locale);
    this.ready = true;
  },
  methods: {
    async refreshContent(locale) {
      try {
        const res = await axios.get(`/api/agile-training/role-quiz/g/${this.routeSlug}/state`, {
          params: this.participantToken
            ? { participant_token: this.participantToken, locale }
            : { locale },
        });
        this.content = res.data.content || { situations: [], roles: [], levels: [] };
        this.group = res.data.group || this.group;
        this.effectiveLocale = res.data.effective_locale || locale || 'ru';
        const ans = res.data.answer;
        if (ans && ans.data) {
          this.selection = ans.data.selection || {};
          this.evaluation = ans.data.evaluation || null;
          this.notesSeen = ans.data.notes_seen || [];
          if (this.evaluation && Object.keys(this.selection).length > 0 && this.step === 'start') {
            this.step = 'result';
          } else if (this.participantToken && this.step === 'start') {
            this.step = 'intro';
          }
        }
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      }
    },
    switchLocale(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* noop */ }
    },
    isFilled(situationKey) {
      const row = this.selection[situationKey] || {};
      return Object.values(row).some((v) => !!v);
    },
    setLevel(situationKey, roleKey, level) {
      const next = { ...(this.selection[situationKey] || {}) };
      next[roleKey] = level;
      this.selection = { ...this.selection, [situationKey]: next };
    },
    accountableWarning(situationKey) {
      const row = this.selection[situationKey] || {};
      const accs = Object.values(row).filter((v) => v === 'accountable');
      const anyPicked = Object.values(row).some((v) => !!v);
      if (!anyPicked) return '';
      if (accs.length === 0) return this.$t('agileTraining.roleQuiz.warnNoAccountable');
      if (accs.length > 1) return this.$t('agileTraining.roleQuiz.warnExtraAccountable');
      return '';
    },
    async start() {
      if (!this.displayName) return;
      this.joining = true; this.joinError = '';
      try {
        if (!this.participantToken) {
          const r = await axios.post(`/api/agile-training/g/${this.routeSlug}/participant`,
            { display_name: this.displayName });
          this.participantToken = r.data.participant_token;
          writeLs(TOKEN_KEY_PREFIX, this.routeSlug, this.participantToken);
          writeLs(NAME_KEY_PREFIX, this.routeSlug, this.displayName);
        }
        this.step = 'intro';
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.joining = false;
      }
    },
    async submit() {
      if (!this.participantToken) {
        this.joinError = this.$t('agileTraining.roleQuiz.errNoToken');
        this.step = 'start';
        return;
      }
      this.saving = true;
      try {
        const res = await axios.post(`/api/agile-training/role-quiz/g/${this.routeSlug}/answer`, {
          participant_token: this.participantToken,
          selection: this.selection,
          notes_seen: this.notesSeen,
        });
        this.evaluation = res.data.evaluation;
        this.step = 'result';
        try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) { /* noop */ }
      } catch (e) {
        this.joinError = (e.response && e.response.data && e.response.data.error) || e.message || 'Error';
      } finally {
        this.saving = false;
      }
    },
    goEditAgain() {
      this.step = 'quiz';
      try { window.scrollTo({ top: 0, behavior: 'smooth' }); } catch (_) { /* noop */ }
    },
    goShareResults() {
      try {
        const url = window.location.href;
        navigator.clipboard.writeText(url);
        this.joinError = this.$t('agileTraining.roleQuiz.linkCopied');
      } catch (_) { /* noop */ }
    },
    cellColor(situationKey, roleKey) {
      if (!this.evaluation) return '';
      const sit = (this.evaluation.situations || {})[situationKey];
      if (!sit) return '';
      const role = (sit.roles || {})[roleKey];
      return (role && role.color) || '';
    },
    pickedLabel(situationKey, roleKey) {
      const sit = (this.evaluation && this.evaluation.situations || {})[situationKey];
      const picked = sit && sit.roles && sit.roles[roleKey] && sit.roles[roleKey].picked;
      return this.levelLabel(picked) || '—';
    },
    expectedLabel(situationKey, roleKey) {
      const sit = (this.evaluation && this.evaluation.situations || {})[situationKey];
      const expected = sit && sit.roles && sit.roles[roleKey] && sit.roles[roleKey].expected;
      return this.levelLabel(expected) || '—';
    },
    levelLabel(key) {
      if (!key) return '';
      const lv = (this.content.levels || []).find((l) => l.key === key);
      return lv ? `${lv.emoji} ${lv.short}` : key;
    },
    resiColorIcon(situationKey) {
      const sit = (this.evaluation && this.evaluation.situations || {})[situationKey];
      const c = sit && sit.color;
      if (c === 'green') return '🟢';
      if (c === 'yellow') return '🟡';
      if (c === 'red') return '🔴';
      return '⚪';
    },
  },
};
</script>

<style scoped>
.rq-play { max-width: 980px; margin: 32px auto 80px; padding: 0 16px; color: #0f172a; }
.rq-play__loading { text-align: center; color: #64748b; padding: 80px 0; }
.rq-play__head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; margin-bottom: 18px; }
.rq-play__head h1 { margin: 4px 0 0; font-size: 22px; }
.rq-play__group { font-size: 12px; font-weight: 700; color: #6366f1; letter-spacing: 0.04em; text-transform: uppercase; }

.rq-play__lang { display: inline-flex; gap: 4px; background: #f1f5f9; padding: 3px; border-radius: 999px; }
.rq-lang__btn { background: transparent; border: none; padding: 4px 10px; border-radius: 999px; cursor: pointer; font-weight: 700; font-size: 12px; color: #64748b; }
.rq-lang__btn.active { background: #0f172a; color: #fff; }

.rq-play__section { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; padding: 20px; margin-bottom: 16px; }
.rq-play__section h2 { margin: 0 0 8px; font-size: 18px; }
.rq-play__lead { color: #475569; margin: 0 0 12px; }
.rq-play__field { display: flex; flex-direction: column; gap: 6px; max-width: 460px; margin: 12px 0; }
.rq-play__field input { padding: 10px 12px; border: 1px solid #cbd5e1; border-radius: 10px; font-size: 14px; }
.rq-play__field input:focus { outline: none; border-color: #6366f1; box-shadow: 0 0 0 3px rgba(99,102,241,0.15); }
.rq-play__hint { color: #64748b; font-size: 13px; }
.rq-error { color: #b91c1c; margin-top: 8px; font-size: 13px; }

.rq-context { padding-left: 20px; color: #334155; }
.rq-context li { margin: 4px 0; }

.rq-btn {
  background: #fff; border: 1px solid #cbd5e1; padding: 10px 18px; border-radius: 10px;
  font-weight: 700; cursor: pointer; font-size: 14px;
}
.rq-btn--primary { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; border-color: transparent; }
.rq-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.rq-btn--ghost { color: #475569; }
.rq-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 14px; flex-wrap: wrap; }
.rq-actions--sticky {
  position: sticky; bottom: 12px; background: rgba(255,255,255,0.94);
  backdrop-filter: blur(6px); padding: 10px; border-radius: 12px;
  box-shadow: 0 -2px 12px rgba(15,23,42,0.06); border: 1px solid #e2e8f0;
}

.rq-roles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 8px 0 16px; }
.rq-role { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; }
.rq-role__emoji { font-size: 22px; }
.rq-role h3 { margin: 4px 0 4px; font-size: 14px; }
.rq-role__desc { color: #475569; font-size: 13px; margin: 0; }

.rq-section-h { margin: 16px 0 6px; font-size: 14px; }
.rq-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; padding: 0; list-style: none; margin: 8px 0; }
.rq-legend__item { display: flex; gap: 10px; align-items: flex-start; padding: 8px 12px; border-radius: 10px; border: 1px solid #e2e8f0; background: #f8fafc; }
.rq-legend__emoji { font-size: 18px; }
.rq-legend__desc { display: block; color: #475569; font-size: 12px; margin-top: 2px; }
.rq-legend__item--accountable { border-color: #fbbf24; background: #fffbeb; }
.rq-legend__item--responsible { border-color: #6ee7b7; background: #ecfdf5; }
.rq-legend__item--consulted { border-color: #93c5fd; background: #eff6ff; }
.rq-legend__item--informed { border-color: #c4b5fd; background: #f5f3ff; }
.rq-legend__item--not_involved { border-color: #cbd5e1; background: #f1f5f9; }

.rq-legend--inline { display: flex; flex-wrap: wrap; gap: 6px; margin: 0 0 10px; }
.rq-mini { background: #fff; padding: 2px 8px; border: 1px solid #cbd5e1; border-radius: 999px; font-size: 12px; font-weight: 700; }
.rq-mini--accountable { background: #fffbeb; color: #92400e; border-color: #fbbf24; }
.rq-mini--responsible { background: #ecfdf5; color: #065f46; border-color: #6ee7b7; }
.rq-mini--consulted { background: #eff6ff; color: #1e3a8a; border-color: #93c5fd; }
.rq-mini--informed { background: #f5f3ff; color: #5b21b6; border-color: #c4b5fd; }
.rq-mini--not_involved { background: #f1f5f9; color: #475569; border-color: #cbd5e1; }

.rq-quiz__head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.rq-progress { display: flex; align-items: center; gap: 8px; font-size: 13px; color: #475569; }
.rq-progress__bar { width: 160px; height: 8px; background: #e2e8f0; border-radius: 999px; overflow: hidden; }
.rq-progress__fill { height: 100%; background: linear-gradient(90deg, #6366f1, #22c55e); transition: width .25s ease; }

.rq-sit { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 14px; margin: 12px 0; transition: border-color .15s; }
.rq-sit--filled { border-color: #93c5fd; background: #fff; box-shadow: 0 1px 4px rgba(99,102,241,0.08); }
.rq-sit__head { display: flex; gap: 12px; align-items: flex-start; margin-bottom: 8px; }
.rq-sit__num { background: #0f172a; color: #fff; min-width: 28px; height: 28px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; }
.rq-sit__head h3 { margin: 0; font-size: 15px; line-height: 1.35; }
.rq-sit__sub { color: #475569; font-size: 13px; margin: 4px 0 0; }
.rq-sit__roles { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px 16px; margin-top: 8px; }
.rq-sit__role { display: flex; flex-direction: column; gap: 4px; }
.rq-sit__role-name { font-size: 13px; font-weight: 600; color: #0f172a; display: flex; gap: 6px; align-items: center; }
.rq-sit__role-emoji { font-size: 14px; }

.rq-chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
.rq-chip {
  background: #fff; border: 1px solid #cbd5e1; color: #475569;
  padding: 5px 9px; border-radius: 999px; font-size: 12px; font-weight: 600;
  cursor: pointer; line-height: 1.2;
}
.rq-chip:hover { border-color: #6366f1; color: #4338ca; }
.rq-chip__short { font-weight: 700; }
.rq-chip--clear { color: #94a3b8; min-width: 26px; text-align: center; padding: 5px 8px; }
.rq-chip--accountable.rq-chip--active { background: #fbbf24; color: #78350f; border-color: #f59e0b; }
.rq-chip--responsible.rq-chip--active { background: #6ee7b7; color: #064e3b; border-color: #10b981; }
.rq-chip--consulted.rq-chip--active { background: #93c5fd; color: #1e3a8a; border-color: #3b82f6; }
.rq-chip--informed.rq-chip--active { background: #c4b5fd; color: #4c1d95; border-color: #8b5cf6; }
.rq-chip--not_involved.rq-chip--active { background: #cbd5e1; color: #1e293b; border-color: #94a3b8; }
.rq-chip--clear.rq-chip--active { background: #0f172a; color: #fff; border-color: #0f172a; }

.rq-warn { color: #b45309; background: #fffbeb; border: 1px solid #fcd34d; padding: 6px 10px; border-radius: 8px; margin: 8px 0 0; font-size: 12.5px; }

.rq-result__head { display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap; }
.rq-result__score { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }
.rq-result__score-num { font-size: 32px; font-weight: 800; color: #0f172a; line-height: 1; }
.rq-result__score-label { font-size: 12px; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; }
.rq-result__chips { display: flex; gap: 6px; flex-wrap: wrap; }
.rq-pill { padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; background: #f1f5f9; }
.rq-pill--green { background: #ecfdf5; color: #065f46; }
.rq-pill--yellow { background: #fffbeb; color: #92400e; }
.rq-pill--red { background: #fef2f2; color: #7f1d1d; }
.rq-pill--muted { background: #f1f5f9; color: #475569; }

.rq-resi { background: #fff; border: 1px solid #e2e8f0; border-left-width: 4px; border-radius: 12px; padding: 14px 16px; margin: 12px 0; }
.rq-resi--green { border-left-color: #16a34a; }
.rq-resi--yellow { border-left-color: #f59e0b; }
.rq-resi--red { border-left-color: #dc2626; }
.rq-resi__head { display: flex; gap: 8px; align-items: center; }
.rq-resi__head h3 { margin: 0; font-size: 15px; flex: 1; }
.rq-resi__num { background: #0f172a; color: #fff; min-width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; }
.rq-resi__color { font-size: 16px; }
.rq-resi__sub { color: #475569; font-size: 13px; margin: 4px 0 8px; }
.rq-resi__table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 13px; }
.rq-resi__table th, .rq-resi__table td { padding: 6px 8px; text-align: left; border-bottom: 1px dashed #e2e8f0; }
.rq-resi__row--green td:nth-child(2) { color: #16a34a; font-weight: 600; }
.rq-resi__row--yellow td:nth-child(2) { color: #b45309; font-weight: 600; }
.rq-resi__row--red td:nth-child(2) { color: #b91c1c; font-weight: 700; }
.rq-resi__row--missing td:nth-child(2) { color: #64748b; font-style: italic; }
.rq-resi__why, .rq-resi__pitfall { background: #f8fafc; border-radius: 8px; padding: 8px 10px; margin: 6px 0 0; font-size: 13.5px; color: #1e293b; }
.rq-resi__pitfall { background: #fef2f2; color: #7f1d1d; }
</style>
