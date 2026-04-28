<template>
  <div class="rq-play modern-ui" v-if="ready">
    <header class="rq-play__head">
      <div>
        <div class="rq-play__group">🎯 {{ groupName }}</div>
        <h1>{{ $t('agileTraining.roleQuiz.playTitle') }}</h1>
      </div>
      <div class="rq-play__lang">
        <button type="button" class="rq-lang__btn" :class="{ active: effectiveLocale === 'ru' }" @click="switchLocale('ru')">RU</button>
        <button type="button" class="rq-lang__btn" :class="{ active: effectiveLocale === 'en' }" @click="switchLocale('en')">EN</button>
      </div>
    </header>

    <!-- Welcome -->
    <section v-if="step === 'start'" class="rq-play__section">
      <h2>👋 {{ $t('agileTraining.roleQuiz.welcome') }}</h2>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.welcomeLead') }}</p>
      <ul class="rq-context">
        <li>📋 {{ $t('agileTraining.roleQuiz.contextItem1', { n: situationsCount }) }}</li>
        <li>🧠 {{ $t('agileTraining.roleQuiz.contextItem2') }}</li>
        <li>💬 {{ $t('agileTraining.roleQuiz.contextItem3') }}</li>
      </ul>
      <label class="rq-play__field">
        <span>{{ $t('agileTraining.roleQuiz.yourName') }}</span>
        <input v-model.trim="displayName" maxlength="60"
               :placeholder="$t('agileTraining.roleQuiz.yourNamePh')" />
      </label>
      <button type="button" class="rq-btn rq-btn--primary" :disabled="!displayName || joining" @click="start">
        {{ $t('agileTraining.roleQuiz.startBtn') }} →
      </button>
      <p v-if="joinError" class="rq-error">{{ joinError }}</p>
    </section>

    <!-- Roles + levels legend -->
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
            <b>{{ l.title }} <span v-if="l.short && l.short !== l.title" class="rq-legend__short">({{ l.short }})</span></b>
            <span class="rq-legend__desc">{{ l.desc }}</span>
          </div>
        </li>
      </ul>
      <div class="rq-actions">
        <button type="button" class="rq-btn rq-btn--ghost" @click="step = 'start'">← {{ $t('agileTraining.roleQuiz.backBtn') }}</button>
        <button type="button" class="rq-btn rq-btn--primary" @click="step = 'quiz'">
          {{ $t('agileTraining.roleQuiz.toQuiz') }} →
        </button>
      </div>
    </section>

    <!-- Quiz -->
    <section v-else-if="step === 'quiz'" class="rq-play__section">
      <header class="rq-quiz__head">
        <h2>🧩 {{ $t('agileTraining.roleQuiz.quizTitle') }}</h2>
        <div class="rq-progress" v-if="situationsCount">
          <div class="rq-progress__bar"><div class="rq-progress__fill" :style="{ width: progressPct + '%' }"></div></div>
          <span class="rq-progress__label">{{ filledCount }} / {{ situationsCount }}</span>
        </div>
      </header>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.quizLead') }}</p>

      <!-- Inline legend so the player always sees what each chip means -->
      <div class="rq-legend rq-legend--inline">
        <span v-for="l in content.levels" :key="'mini-' + l.key" :class="`rq-mini rq-mini--${l.key}`" :title="l.desc">
          {{ l.emoji }}
          <span class="rq-mini__title">{{ l.title }}</span>
          <span v-if="l.short && l.short !== l.title" class="rq-mini__short">({{ l.short }})</span>
        </span>
      </div>

      <article v-for="(s, idx) in content.situations" :key="s.key"
               class="rq-sit"
               :class="{ 'rq-sit--filled': isFilled(s.key) }">
        <header class="rq-sit__head">
          <div class="rq-sit__num">{{ idx + 1 }}</div>
          <div class="rq-sit__head-text">
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
                      :title="l.title + ' — ' + l.desc"
                      @click="setLevel(s.key, r.key, l.key)">
                {{ l.emoji }}
                <span class="rq-chip__label">{{ l.title }}</span>
              </button>
              <button type="button"
                      class="rq-chip rq-chip--clear"
                      :class="{ 'rq-chip--active': !selection[s.key]?.[r.key] }"
                      :title="$t('agileTraining.roleQuiz.clearChip')"
                      @click="setLevel(s.key, r.key, null)">×</button>
            </div>
          </div>
        </div>
      </article>

      <div class="rq-actions rq-actions--sticky">
        <span class="rq-save-hint">
          <span v-if="autoSaved" class="rq-save-hint__ok">💾 {{ $t('agileTraining.roleQuiz.savedAuto') }}</span>
          <span v-else-if="saving" class="rq-save-hint__busy">{{ $t('agileTraining.roleQuiz.saving') }}…</span>
        </span>
        <button type="button" class="rq-btn rq-btn--ghost" @click="step = 'intro'">← {{ $t('agileTraining.roleQuiz.backBtn') }}</button>
        <button type="button" class="rq-btn rq-btn--primary" :disabled="!filledCount || saving" @click="submit">
          {{ saving ? $t('agileTraining.roleQuiz.savingBtn') : $t('agileTraining.roleQuiz.sendBtn') }} →
        </button>
      </div>
    </section>

    <!-- Submitted: thanks + "review with facilitator" + your answers + discussion notes -->
    <section v-else-if="step === 'thanks'" class="rq-play__section">
      <h2>✅ {{ $t('agileTraining.roleQuiz.thanksTitle') }}</h2>
      <p class="rq-play__lead">{{ $t('agileTraining.roleQuiz.thanksLead') }}</p>

      <article v-for="(s, idx) in content.situations" :key="'rec-' + s.key" class="rq-review">
        <header class="rq-review__head">
          <span class="rq-review__num">{{ idx + 1 }}</span>
          <h3>{{ s.title }}</h3>
        </header>
        <p v-if="s.subtitle" class="rq-review__sub">{{ s.subtitle }}</p>

        <table class="rq-review__table">
          <thead>
            <tr>
              <th>{{ $t('agileTraining.roleQuiz.role') }}</th>
              <th>{{ $t('agileTraining.roleQuiz.youPicked') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in content.roles" :key="'rev-' + s.key + '-' + r.key">
              <td><span>{{ r.emoji }}</span> {{ r.title }}</td>
              <td :class="`rq-review__cell rq-review__cell--${pickedKey(s.key, r.key) || 'empty'}`">
                {{ pickedLabel(s.key, r.key) }}
              </td>
            </tr>
          </tbody>
        </table>

        <p v-if="s.discussion" class="rq-review__notes">
          <b>💬 {{ $t('agileTraining.roleQuiz.discussionPrompt') }}:</b> {{ s.discussion }}
        </p>
        <p v-if="s.common_mistake" class="rq-review__pitfall">
          <b>⚠ {{ $t('agileTraining.roleQuiz.pitfall') }}:</b> {{ s.common_mistake }}
        </p>
      </article>

      <div class="rq-actions">
        <button type="button" class="rq-btn rq-btn--ghost" @click="goEditAgain">
          ↺ {{ $t('agileTraining.roleQuiz.editAgain') }}
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
      autoSaved: false,
      autosaveTimer: null,
      autosavedAtMs: 0,
      submitted: false,
      selection: {},
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
  beforeUnmount() {
    if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
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
          this.submitted = !!ans.data.submitted;
          if (this.submitted && this.step === 'start') {
            this.step = 'thanks';
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
      this.scheduleAutosave();
    },
    scheduleAutosave() {
      this.autoSaved = false;
      if (this.autosaveTimer) clearTimeout(this.autosaveTimer);
      this.autosaveTimer = setTimeout(() => this.autosave(), 600);
    },
    async autosave() {
      if (!this.participantToken) return;
      try {
        await axios.post(`/api/agile-training/role-quiz/g/${this.routeSlug}/answer`, {
          participant_token: this.participantToken,
          selection: this.selection,
          submitted: false,
        });
        this.autoSaved = true;
        this.autosavedAtMs = Date.now();
        setTimeout(() => {
          if (Date.now() - this.autosavedAtMs >= 1700) this.autoSaved = false;
        }, 1800);
      } catch (_) { /* ignore — пользователь увидит на submit */ }
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
        await axios.post(`/api/agile-training/role-quiz/g/${this.routeSlug}/answer`, {
          participant_token: this.participantToken,
          selection: this.selection,
          submitted: true,
        });
        this.submitted = true;
        this.step = 'thanks';
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
    pickedKey(situationKey, roleKey) {
      return (this.selection[situationKey] || {})[roleKey] || '';
    },
    pickedLabel(situationKey, roleKey) {
      const key = this.pickedKey(situationKey, roleKey);
      if (!key) return '—';
      const lv = (this.content.levels || []).find((l) => l.key === key);
      return lv ? `${lv.emoji} ${lv.title}` : key;
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
.rq-lang__btn { background: transparent; border: none; padding: 4px 10px; border-radius: 999px; cursor: pointer; font-weight: 700; font-size: 12px; color: #64748b; min-height: 0; }
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
  font-weight: 700; cursor: pointer; font-size: 14px; color: #0f172a;
  display: inline-flex; align-items: center; gap: 6px; line-height: 1.2;
}
.rq-btn--primary { background: linear-gradient(135deg, #6366f1, #4f46e5); color: #fff; border-color: transparent; }
.rq-btn--primary:hover:not(:disabled) { box-shadow: 0 8px 18px rgba(79,70,229,0.25); }
.rq-btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
.rq-btn--ghost { color: #475569; }
.rq-btn--ghost:hover { border-color: #6366f1; color: #4338ca; }
.rq-actions { display: flex; gap: 10px; justify-content: flex-end; margin-top: 14px; flex-wrap: wrap; align-items: center; }
.rq-actions--sticky {
  position: sticky; bottom: 12px; background: rgba(255,255,255,0.96);
  backdrop-filter: blur(6px); padding: 10px; border-radius: 12px;
  box-shadow: 0 -2px 12px rgba(15,23,42,0.06); border: 1px solid #e2e8f0;
}
.rq-save-hint { font-size: 12px; color: #64748b; margin-right: auto; }
.rq-save-hint__ok { color: #047857; }
.rq-save-hint__busy { color: #4338ca; }

.rq-roles { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; margin: 8px 0 16px; }
.rq-role { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 12px; }
.rq-role__emoji { font-size: 22px; }
.rq-role h3 { margin: 4px 0 4px; font-size: 14px; }
.rq-role__desc { color: #475569; font-size: 13px; margin: 0; }

.rq-section-h { margin: 16px 0 6px; font-size: 14px; }
.rq-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 8px; padding: 0; list-style: none; margin: 8px 0; }
.rq-legend__item { display: flex; gap: 10px; align-items: flex-start; padding: 8px 12px; border-radius: 10px; border: 1px solid #e2e8f0; background: #f8fafc; }
.rq-legend__emoji { font-size: 18px; line-height: 1; }
.rq-legend__short { color: #64748b; font-weight: 500; font-size: 12px; }
.rq-legend__desc { display: block; color: #475569; font-size: 12px; margin-top: 2px; }
.rq-legend__item--responsible { border-color: #fca5a5; background: #fef2f2; }
.rq-legend__item--participates { border-color: #6ee7b7; background: #ecfdf5; }
.rq-legend__item--informed { border-color: #c4b5fd; background: #f5f3ff; }
.rq-legend__item--not_involved { border-color: #cbd5e1; background: #f1f5f9; }

.rq-legend--inline {
  display: flex; flex-wrap: wrap; gap: 6px;
  margin: 0 0 14px;
  padding: 8px 10px; background: #f8fafc;
  border: 1px dashed #cbd5e1; border-radius: 10px;
}
.rq-mini { background: #fff; padding: 4px 10px; border: 1px solid #cbd5e1; border-radius: 999px; font-size: 12.5px; font-weight: 600; color: #0f172a; display: inline-flex; gap: 4px; align-items: center; }
.rq-mini__title { font-weight: 700; }
.rq-mini__short { color: #64748b; font-weight: 500; }
.rq-mini--responsible { background: #fef2f2; color: #7f1d1d; border-color: #fca5a5; }
.rq-mini--participates { background: #ecfdf5; color: #065f46; border-color: #6ee7b7; }
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
.rq-sit__head-text { flex: 1; min-width: 0; }
.rq-sit__head h3 { margin: 0; font-size: 15px; line-height: 1.35; }
.rq-sit__sub { color: #475569; font-size: 13px; margin: 4px 0 0; }
.rq-sit__roles { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 10px 16px; margin-top: 8px; }
.rq-sit__role { display: flex; flex-direction: column; gap: 4px; }
.rq-sit__role-name { font-size: 13px; font-weight: 600; color: #0f172a; display: flex; gap: 6px; align-items: center; }
.rq-sit__role-emoji { font-size: 14px; }

.rq-chip-row { display: flex; flex-wrap: wrap; gap: 4px; }
/*
 * Чипы уровня выглядят одинаково по форме и текстом подписаны полным
 * названием уровня, чтобы пользователь не угадывал, что значит «У»/«И».
 * Активная chip заливается цветом своего уровня (см. ниже).
 */
.rq-chip {
  background: #fff; border: 1px solid #cbd5e1; color: #1e293b;
  padding: 6px 12px; border-radius: 999px; font-size: 12px; font-weight: 600;
  cursor: pointer; line-height: 1.2;
  display: inline-flex; gap: 6px; align-items: center;
  min-height: 0;
}
.rq-chip:hover { border-color: #6366f1; color: #4338ca; background: #fff; }
.rq-chip__label { font-weight: 600; }
.rq-chip--clear { color: #94a3b8; min-width: 26px; padding: 6px 10px; justify-content: center; }
.rq-chip--clear:hover { background: #f1f5f9; color: #0f172a; border-color: #94a3b8; }
.rq-chip--responsible.rq-chip--active { background: #fee2e2; color: #7f1d1d; border-color: #f87171; }
.rq-chip--participates.rq-chip--active { background: #d1fae5; color: #065f46; border-color: #34d399; }
.rq-chip--informed.rq-chip--active { background: #ede9fe; color: #5b21b6; border-color: #a78bfa; }
.rq-chip--not_involved.rq-chip--active { background: #e2e8f0; color: #1e293b; border-color: #94a3b8; }
.rq-chip--clear.rq-chip--active { background: #0f172a; color: #fff; border-color: #0f172a; }

/* Review (after submit) */
.rq-review { background: #fff; border: 1px solid #e2e8f0; border-left: 4px solid #6366f1; border-radius: 12px; padding: 14px 16px; margin: 12px 0; }
.rq-review__head { display: flex; gap: 8px; align-items: center; }
.rq-review__head h3 { margin: 0; font-size: 15px; }
.rq-review__num { background: #0f172a; color: #fff; min-width: 26px; height: 26px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 13px; }
.rq-review__sub { color: #475569; font-size: 13px; margin: 4px 0 8px; }
.rq-review__table { width: 100%; border-collapse: collapse; margin: 6px 0; font-size: 13px; }
.rq-review__table th, .rq-review__table td { padding: 6px 8px; text-align: left; border-bottom: 1px dashed #e2e8f0; }
.rq-review__cell--responsible { color: #7f1d1d; font-weight: 700; }
.rq-review__cell--participates { color: #047857; font-weight: 600; }
.rq-review__cell--informed { color: #5b21b6; font-weight: 600; }
.rq-review__cell--not_involved { color: #475569; }
.rq-review__cell--empty { color: #94a3b8; font-style: italic; }
.rq-review__notes, .rq-review__pitfall { background: #f8fafc; border-radius: 8px; padding: 8px 10px; margin: 6px 0 0; font-size: 13.5px; color: #1e293b; }
.rq-review__pitfall { background: #fef2f2; color: #7f1d1d; }
</style>
