<template>
  <div class="at-hub">
    <div class="at-hub__toolbar">
      <div class="at-lang" role="group" :aria-label="$t('agileTraining.common.language')">
        <button
          type="button"
          class="at-lang__btn"
          :class="{ 'at-lang__btn--active': $i18n.locale === 'ru' }"
          @click="switchLang('ru')"
        >RU</button>
        <button
          type="button"
          class="at-lang__btn"
          :class="{ 'at-lang__btn--active': $i18n.locale === 'en' }"
          @click="switchLang('en')"
        >EN</button>
      </div>
    </div>

    <header class="at-hub__head">
      <h1>🎓 {{ $t('agileTraining.hub.title') }}</h1>
      <p class="at-hub__subtitle">{{ $t('agileTraining.hub.subtitle') }}</p>
      <p class="at-hub__lead">{{ $t('agileTraining.hub.lead') }}</p>
    </header>

    <div class="at-hub__grid">
      <article class="at-card" @click="$router.push('/agile-training/principles')">
        <span class="at-card__icon">🃏</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.principles.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.principles.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.principles.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.principles.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.principles.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>

      <article class="at-card" @click="$router.push('/agile-training/cynefin')">
        <span class="at-card__icon">🧭</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.cynefin.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.cynefin.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.cynefin.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.cynefin.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.cynefin.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>

      <article class="at-card" @click="$router.push('/agile-training/iceberg')">
        <span class="at-card__icon">🧊</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.iceberg.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.iceberg.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.iceberg.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.iceberg.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.iceberg.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>

      <article class="at-card" @click="$router.push('/agile-training/mvp')">
        <span class="at-card__icon">🚀</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.mvp.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.mvp.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.mvp.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.mvp.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.mvp.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>

      <article class="at-card" @click="$router.push('/agile-training/dor-dod')">
        <span class="at-card__icon">📋</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.dorDod.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.dorDod.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.dorDod.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.dorDod.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.dorDod.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>

      <article class="at-card" @click="$router.push('/agile-training/wsjf')">
        <span class="at-card__icon">⚖️</span>
        <h2 class="at-card__title">{{ $t('agileTraining.hub.wsjf.title') }}</h2>
        <p class="at-card__desc">{{ $t('agileTraining.hub.wsjf.desc') }}</p>
        <ul class="at-card__list">
          <li>{{ $t('agileTraining.hub.wsjf.bullet1') }}</li>
          <li>{{ $t('agileTraining.hub.wsjf.bullet2') }}</li>
          <li>{{ $t('agileTraining.hub.wsjf.bullet3') }}</li>
        </ul>
        <span class="at-card__cta">{{ $t('agileTraining.hub.start') }} →</span>
      </article>
    </div>

    <section class="at-hub__helper">
      <h3>{{ $t('agileTraining.hub.howItWorks.title') }}</h3>
      <ol>
        <li>{{ $t('agileTraining.hub.howItWorks.step1') }}</li>
        <li>{{ $t('agileTraining.hub.howItWorks.step2') }}</li>
        <li>{{ $t('agileTraining.hub.howItWorks.step3') }}</li>
        <li>{{ $t('agileTraining.hub.howItWorks.step4') }}</li>
      </ol>
    </section>
  </div>
</template>

<script>
export default {
  name: 'AgileTrainingHub',
  methods: {
    switchLang(lang) {
      if (lang !== 'ru' && lang !== 'en') return;
      this.$i18n.locale = lang;
      try { localStorage.setItem('language', lang); } catch (_) { /* ignore */ }
    }
  }
};
</script>

<style scoped>
.at-hub {
  max-width: 1080px;
  margin: 32px auto;
  padding: 0 20px 48px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', 'Roboto', sans-serif;
  color: #0f172a;
}
.at-hub__toolbar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.at-lang {
  display: inline-flex;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.05);
}
.at-lang__btn {
  background: transparent;
  border: none;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 600;
  color: #475569;
  cursor: pointer;
  font-family: inherit;
  letter-spacing: 0.5px;
  transition: all 0.15s ease;
}
.at-lang__btn:hover { color: #7c3aed; background: #faf5ff; }
.at-lang__btn--active {
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
}
.at-lang__btn--active:hover { color: #fff; background: linear-gradient(135deg, #8b5cf6 0%, #6d28d9 100%); }

.at-hub__head { text-align: center; margin-bottom: 32px; }
.at-hub__head h1 {
  font-size: 34px;
  font-weight: 700;
  letter-spacing: -0.5px;
  margin: 0 0 8px;
}
.at-hub__subtitle {
  color: #64748b;
  font-size: 17px;
  margin: 0 0 10px;
}
.at-hub__lead {
  max-width: 720px;
  margin: 0 auto;
  color: #475569;
  line-height: 1.6;
}

.at-hub__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 20px;
  margin: 28px 0;
}

.at-card {
  background: #fff;
  border-radius: 20px;
  border: 1px solid #e5e7eb;
  padding: 28px 24px 24px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 12px;
  transition: all 0.2s ease;
  position: relative;
  overflow: hidden;
}
.at-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 12px 28px rgba(139, 92, 246, 0.15);
  transform: translateY(-2px);
}
.at-card--soon {
  background: #f8fafc;
  cursor: default;
  opacity: 0.85;
}
.at-card--soon:hover { transform: none; border-color: #e5e7eb; box-shadow: none; }

.at-card__icon { font-size: 32px; }
.at-card__title {
  font-size: 20px;
  font-weight: 700;
  margin: 0;
  color: #0f172a;
}
.at-card__desc {
  color: #475569;
  line-height: 1.55;
  font-size: 14px;
  margin: 0;
}
.at-card__list {
  margin: 8px 0 0;
  padding-left: 18px;
  color: #64748b;
  font-size: 13px;
  line-height: 1.7;
}
.at-card__cta {
  margin-top: auto;
  color: #7c3aed;
  font-weight: 600;
  font-size: 14px;
}
.at-card__cta--muted { color: #94a3b8; }

.at-hub__helper {
  margin-top: 32px;
  background: linear-gradient(135deg, #faf5ff 0%, #eff6ff 100%);
  border-radius: 16px;
  padding: 24px 28px;
  border: 1px solid #e9d5ff;
}
.at-hub__helper h3 {
  margin: 0 0 12px;
  font-size: 18px;
  color: #312e81;
}
.at-hub__helper ol {
  margin: 0;
  padding-left: 20px;
  color: #475569;
  line-height: 1.7;
}
</style>
