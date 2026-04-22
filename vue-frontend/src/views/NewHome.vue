<template>
  <div class="new-app">
    <header class="new-header">
      <div class="brand">
        <div class="brand__logo">GrowBoard</div>
      </div>

      <div class="new-header__right">
        <div class="language-switcher">
          <button
            @click="switchLanguage('ru')"
            :class="{ active: $i18n.locale === 'ru' }"
            class="lang-btn"
          >
            RU
          </button>
          <button
            @click="switchLanguage('en')"
            :class="{ active: $i18n.locale === 'en' }"
            class="lang-btn"
          >
            EN
          </button>
        </div>

        <nav class="new-nav">
          <router-link to="/login" class="new-nav__btn">{{ $t('newHome.navLogin') }}</router-link>
          <router-link to="/register" class="new-nav__btn new-nav__btn--primary">{{ $t('newHome.navRegister') }}</router-link>
        </nav>
      </div>
    </header>

    <main class="new-main">
      <div class="bg-orbs" aria-hidden="true">
        <div class="orb orb--1"></div>
        <div class="orb orb--2"></div>
        <div class="orb orb--3"></div>
      </div>

      <section class="hero" :class="{ 'is-ready': isReady }">
        <div class="hero__grid">
          <div class="hero__left">
            <div class="hero__kicker">{{ $t('newHome.kicker') }}</div>
            <h1 class="hero__title">{{ $t('newHome.title') }}</h1>
            <p class="hero__subtitle">
              {{ $t('newHome.subtitle') }}
            </p>

            <div class="hero__cta">
              <router-link to="/new/maturity" class="cta-btn cta-btn--primary">{{ $t('newHome.ctaPrimary') }}</router-link>
              <router-link to="/new/dashboard" class="cta-btn">{{ $t('newHome.ctaSecondary') }}</router-link>
            </div>
          </div>

          <div class="hero__right">
            <div class="hero-panel">
              <div class="hero-panel__title">{{ $t('newHome.panelTitle') }}</div>
              <div class="hero-panel__list">
                <div class="pill">{{ $t('newHome.panelPill1') }}</div>
                <div class="pill">{{ $t('newHome.panelPill2') }}</div>
                <div class="pill">{{ $t('newHome.panelPill3') }}</div>
                <div class="pill">{{ $t('newHome.panelPill4') }}</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="trusted" :class="{ 'is-ready': isReady }">
        <div class="trusted__inner">
          <div class="trusted__title">{{ $t('newHome.trustedTitle') }}</div>
          <div class="trusted__subtitle">{{ $t('newHome.trustedSubtitle') }}</div>

          <div class="marquee" aria-label="Trusted by brands">
            <div class="marquee__track">
              <div v-for="(c, idx) in trustedCompaniesLoop" :key="`a-${idx}-${c.name}`" class="logo-pill">
                <span class="logo-wordmark">{{ c.name }}</span>
              </div>
            </div>
            <div class="marquee__track marquee__track--clone" aria-hidden="true">
              <div v-for="(c, idx) in trustedCompaniesLoop" :key="`b-${idx}-${c.name}`" class="logo-pill">
                <span class="logo-wordmark">{{ c.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="areas" :class="{ 'is-ready': isReady }">
        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">{{ $t('newHome.areas.smTitle') }}</h2>
            <p class="area-card__desc">{{ $t('newHome.areas.smDesc') }}</p>
          </div>
          <div class="area-card__links">
            <router-link to="/new/conflicts" class="area-link">{{ $t('newHome.links.conflicts') }}</router-link>
            <router-link to="/new/meeting-design" class="area-link">{{ $t('newHome.links.meetingDesign') }}</router-link>
            <router-link to="/new/system-thinking" class="area-link">{{ $t('newHome.links.systemThinking') }}</router-link>
            <router-link to="/new/agile-kata" class="area-link">{{ $t('newHome.links.agileKata') }}</router-link>
            <router-link to="/new/agile-tools" class="area-link">{{ $t('newHome.links.agileTools') }}</router-link>
            <router-link to="/agile-training" class="area-link">{{ $t('newHome.links.agileTraining') }}</router-link>
            <router-link to="/new/interview-simulator" class="area-link">{{ $t('newHome.links.interviewSimulator') }}</router-link>
          </div>
        </article>

        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">{{ $t('newHome.areas.pmTitle') }}</h2>
            <p class="area-card__desc">{{ $t('newHome.areas.pmDesc') }}</p>
          </div>
          <div class="area-card__links">
            <router-link to="/new/metrics-tree" class="area-link">{{ $t('newHome.links.metricsTree') }}</router-link>
            <router-link to="/new/backlog-prep" class="area-link">{{ $t('newHome.links.backlogPrep') }}</router-link>
            <router-link to="/new/project-dashboard" class="area-link">{{ $t('newHome.links.projectDashboard') }}</router-link>
            <router-link to="/new/project-card" class="area-link">{{ $t('newHome.links.projectCard') }}</router-link>
            <a class="area-link" href="https://poker.growboard.ru" target="_blank" rel="noopener noreferrer">{{ $t('newHome.links.planningPoker') }}</a>
          </div>
        </article>

        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">{{ $t('newHome.areas.poTitle') }}</h2>
            <p class="area-card__desc">{{ $t('newHome.areas.poDesc') }}</p>
          </div>
          <div class="area-card__links">
            <router-link to="/new/maturity" class="area-link">{{ $t('newHome.links.maturityLink') }}</router-link>
            <router-link to="/new/business-value" class="area-link">{{ $t('newHome.links.businessValue') }}</router-link>
            <router-link to="/new/surveys" class="area-link">{{ $t('newHome.links.surveys') }}</router-link>
          </div>
        </article>

        <article class="area-card area-card--accent">
          <div class="area-card__head">
            <h2 class="area-card__title">{{ $t('newHome.areas.bizTitle') }}</h2>
            <p class="area-card__desc">{{ $t('newHome.areas.bizDesc') }}</p>
          </div>
          <div class="area-card__links">
            <router-link to="/new/dashboard" class="area-link">{{ $t('newHome.links.dashboard') }}</router-link>
            <router-link to="/new/survey" class="area-link">{{ $t('newHome.links.survey') }}</router-link>
            <router-link to="/new/report-insights" class="area-link">{{ $t('newHome.links.reportInsights') }}</router-link>
            <router-link to="/new/strategy-builder" class="area-link">{{ $t('newHome.links.strategyBuilder') }}</router-link>
          </div>
        </article>
      </section>

      <section id="feedback" class="testimonials" :class="{ 'is-ready': isReady }" aria-labelledby="feedback-heading">
        <div class="testimonials__inner">
          <h2 id="feedback-heading" class="testimonials__title">{{ $t('newHome.feedback.title') }}</h2>
          <p class="testimonials__lead">{{ $t('newHome.feedback.lead') }}</p>
          <div class="testimonials__grid">
            <blockquote v-for="(item, i) in testimonialKeys" :key="i" class="testimonial-card">
              <p class="testimonial-card__quote">«{{ $t(`newHome.feedback.items.${item}.quote`) }}»</p>
              <footer class="testimonial-card__meta">
                <span class="testimonial-card__author">{{ $t(`newHome.feedback.items.${item}.author`) }}</span>
                <span class="testimonial-card__role">{{ $t(`newHome.feedback.items.${item}.role`) }}</span>
              </footer>
            </blockquote>
          </div>
        </div>
      </section>

      <section class="legal-blocks" :class="{ 'is-ready': isReady }" aria-label="Information">
        <div id="about" class="legal-card legal-card--span">
          <h2 class="legal-card__title">{{ $t('newHome.about.title') }}</h2>
          <p v-for="(k, idx) in aboutParagraphKeys" :key="'ab-' + idx" class="legal-card__p">
            {{ $t(`newHome.about.p${k}`) }}
          </p>
        </div>
        <div class="legal-blocks__row">
          <div id="security" class="legal-card">
            <h2 class="legal-card__title">{{ $t('newHome.security.title') }}</h2>
            <p v-for="(k, idx) in securityParagraphKeys" :key="'sec-' + idx" class="legal-card__p">
              {{ $t(`newHome.security.p${k}`) }}
            </p>
          </div>
          <div id="pricing" class="legal-card">
            <h2 class="legal-card__title">{{ $t('newHome.pricing.title') }}</h2>
            <p v-for="(k, idx) in pricingParagraphKeys" :key="'pr-' + idx" class="legal-card__p">
              {{ $t(`newHome.pricing.p${k}`) }}
            </p>
          </div>
        </div>
      </section>
    </main>

    <footer class="new-footer">
      <div class="new-footer__inner new-footer__inner--cols">
        <div class="new-footer__brand">
          <span>GrowBoard</span>
          <span class="dot">•</span>
          <span class="footer-copy">{{ $t('home.footer') }}</span>
        </div>
        <nav class="new-footer__nav" aria-label="Footer">
          <a href="#feedback" class="footer-nav-link">{{ $t('newHome.footerNav.feedback') }}</a>
          <a href="#about" class="footer-nav-link">{{ $t('newHome.footerNav.about') }}</a>
          <a href="#security" class="footer-nav-link">{{ $t('newHome.footerNav.security') }}</a>
          <a href="#pricing" class="footer-nav-link">{{ $t('newHome.footerNav.pricing') }}</a>
        </nav>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      isReady: false,
      testimonialKeys: ['a', 'b', 'c'],
      aboutParagraphKeys: [1, 2, 3],
      securityParagraphKeys: [1, 2, 3],
      pricingParagraphKeys: [1, 2, 3],
      trustedCompanies: [
        { name: "Mastercard" },
        { name: "TUI" },
        { name: "Toyota" },
        { name: "Nordea" },
        { name: "Auchan" },
        { name: "Renault" },
        { name: "1NCE" },
        { name: "Novartis" },
        { name: "Sanofi" },
        { name: "Ipsen" },
        { name: "Semrush" },
        { name: "Mars" },
        { name: "Cognizant" },
        { name: "Danone" },
        { name: "JavaGuru" },
        { name: "Bella" },
        { name: "Vialet" }
      ],
    };
  },
  mounted() {
    window.requestAnimationFrame(() => {
      this.isReady = true;
    });
  },
  computed: {
    trustedCompaniesLoop() {
      // repeat to keep marquee dense even on wide screens
      return [...this.trustedCompanies, ...this.trustedCompanies, ...this.trustedCompanies];
    },
  },
  methods: {
    switchLanguage(lang) {
      this.$i18n.locale = lang;
      localStorage.setItem("language", lang);
    },
  },
};
</script>

<style scoped>
.new-app {
  min-height: 100vh;
  background: radial-gradient(1100px 560px at 15% 10%, rgba(32, 90, 255, 0.12), transparent 60%),
    radial-gradient(900px 520px at 90% 18%, rgba(0, 194, 255, 0.1), transparent 62%),
    radial-gradient(800px 520px at 55% 95%, rgba(32, 90, 255, 0.08), transparent 58%),
    #f7f9ff;
  color: rgba(10, 20, 45, 0.92);
  font-family: ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, Arial, "Noto Sans", "Apple Color Emoji",
    "Segoe UI Emoji";
}

.new-header {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  background: rgba(247, 249, 255, 0.72);
  border-bottom: 1px solid rgba(10, 20, 45, 0.08);
  backdrop-filter: blur(10px);
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand__logo {
  font-weight: 700;
  letter-spacing: 0.2px;
}

.new-header__right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.language-switcher {
  display: flex;
  gap: 6px;
}

.lang-btn {
  padding: 6px 10px;
  border: 1px solid rgba(10, 20, 45, 0.14);
  background: rgba(255, 255, 255, 0.7);
  color: rgba(10, 20, 45, 0.88);
  border-radius: 10px;
  cursor: pointer;
  font-size: 12px;
  transition: 0.2s ease;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.92);
}

.lang-btn.active {
  border-color: rgba(32, 90, 255, 0.35);
  background: rgba(32, 90, 255, 0.1);
}

.new-nav {
  display: flex;
  align-items: center;
  gap: 10px;
}

.new-nav__btn {
  text-decoration: none;
  color: rgba(10, 20, 45, 0.9);
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(10, 20, 45, 0.12);
  background: rgba(255, 255, 255, 0.78);
  transition: 0.2s ease;
  font-size: 14px;
}

.new-nav__btn:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
  border-color: rgba(32, 90, 255, 0.28);
}

.new-nav__btn--primary {
  border-color: rgba(32, 90, 255, 0.65);
  color: white;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.96), rgba(0, 194, 255, 0.88));
}

.new-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 34px 18px 56px;
  position: relative;
}

.bg-orbs {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}

.orb {
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.6;
  transform: translate3d(0, 0, 0);
  animation: float 8.5s ease-in-out infinite;
}

.orb--1 {
  left: -220px;
  top: -160px;
  background: radial-gradient(circle at 30% 30%, rgba(32, 90, 255, 0.55), transparent 62%);
}

.orb--2 {
  right: -240px;
  top: 40px;
  background: radial-gradient(circle at 35% 35%, rgba(0, 194, 255, 0.42), transparent 60%);
  animation-delay: -2.4s;
}

.orb--3 {
  left: 280px;
  bottom: -280px;
  background: radial-gradient(circle at 40% 40%, rgba(32, 90, 255, 0.32), transparent 60%);
  animation-delay: -4.1s;
}

.hero {
  padding: 10px 4px 6px;
  position: relative;
}

.hero__grid {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 18px;
  align-items: start;
}

.hero__kicker {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.76);
  border: 1px solid rgba(10, 20, 45, 0.12);
  color: rgba(10, 20, 45, 0.78);
  font-size: 13px;
  width: fit-content;
}

.hero__title {
  margin: 12px 0 0;
  font-size: 42px;
  line-height: 1.06;
  letter-spacing: -0.8px;
}

.hero__subtitle {
  margin: 14px 0 0;
  color: rgba(10, 20, 45, 0.72);
  max-width: 840px;
  line-height: 1.5;
}

.hero__cta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 18px;
}

.cta-btn {
  text-decoration: none;
  color: rgba(10, 20, 45, 0.9);
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(10, 20, 45, 0.12);
  background: rgba(255, 255, 255, 0.82);
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
  font-size: 14px;
}

.cta-btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.97);
  border-color: rgba(32, 90, 255, 0.24);
}

.cta-btn--primary {
  border-color: rgba(32, 90, 255, 0.62);
  color: white;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
}

.cta-btn--primary:hover {
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.96), rgba(0, 194, 255, 0.9));
  border-color: rgba(32, 90, 255, 0.72);
  box-shadow: 0 14px 34px rgba(32, 90, 255, 0.22);
}

.hero-panel {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(255, 255, 255, 0.78);
  box-shadow: 0 20px 70px rgba(10, 20, 45, 0.12);
  padding: 16px;
}

.hero-panel__title {
  font-weight: 650;
}

.hero-panel__list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.pill {
  padding: 8px 10px;
  border-radius: 999px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(247, 249, 255, 0.85);
  font-size: 12px;
  color: rgba(10, 20, 45, 0.78);
}

.hero-panel__note {
  margin-top: 12px;
  color: rgba(10, 20, 45, 0.68);
  font-size: 13px;
  line-height: 1.45;
}

.trusted {
  margin-top: 18px;
}

.trusted__inner {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: 0 18px 60px rgba(10, 20, 45, 0.1);
  padding: 16px 18px;
  overflow: hidden;
}

.trusted__title {
  font-weight: 650;
}

.trusted__subtitle {
  margin-top: 6px;
  color: rgba(10, 20, 45, 0.62);
  font-size: 13px;
}

.marquee {
  position: relative;
  margin-top: 14px;
  mask-image: linear-gradient(to right, transparent, black 8%, black 92%, transparent);
}

.marquee__track {
  display: flex;
  gap: 10px;
  width: max-content;
  animation: marquee 58s linear infinite;
}

.marquee__track--clone {
  position: absolute;
  left: 0;
  top: 0;
  transform: translateX(100%);
}

.logo-pill {
  padding: 10px 12px;
  border-radius: 999px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(247, 249, 255, 0.9);
  color: rgba(10, 20, 45, 0.78);
  font-weight: 600;
  letter-spacing: 0.2px;
  white-space: nowrap;
}

.logo-wordmark {
  font-weight: 750;
  letter-spacing: 0.6px;
  text-transform: uppercase;
  font-size: 12px;
  color: rgba(10, 20, 45, 0.72);
}

.areas {
  margin-top: 26px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.area-card {
  border: 1px solid rgba(10, 20, 45, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.76);
  overflow: hidden;
  box-shadow: 0 18px 60px rgba(10, 20, 45, 0.12);
  transition: transform 0.2s ease, border-color 0.2s ease;
}

.area-card--accent {
  border-color: rgba(32, 90, 255, 0.4);
  background: linear-gradient(180deg, rgba(32, 90, 255, 0.2), rgba(255, 255, 255, 0.06));
}

.area-card:hover {
  transform: translateY(-2px);
  border-color: rgba(255, 255, 255, 0.18);
}

.area-card__head {
  padding: 18px 18px 12px;
}

.area-card__title {
  margin: 0;
  font-size: 16px;
  line-height: 1.25;
}

.area-card__desc {
  margin: 10px 0 0;
  color: rgba(10, 20, 45, 0.68);
  font-size: 13px;
  line-height: 1.45;
}

.area-card__links {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 0 18px 18px;
}

.area-link {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-radius: 14px;
  text-decoration: none;
  border: 1px solid rgba(10, 20, 45, 0.12);
  background: rgba(247, 249, 255, 0.92);
  color: rgba(10, 20, 45, 0.86);
  font-size: 13px;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.area-link:hover {
  background: rgba(255, 255, 255, 0.98);
  border-color: rgba(32, 90, 255, 0.22);
  transform: translateY(-1px);
}

.new-footer {
  border-top: 1px solid rgba(10, 20, 45, 0.08);
  padding: 18px 18px 24px;
  color: rgba(10, 20, 45, 0.62);
}

.new-footer__inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.new-footer__inner--cols {
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 16px;
}

.new-footer__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.new-footer__nav {
  display: flex;
  flex-wrap: wrap;
  gap: 14px 18px;
  align-items: center;
}

.footer-nav-link {
  color: rgba(10, 20, 45, 0.72);
  text-decoration: none;
  font-size: 13px;
  border-bottom: 1px solid transparent;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.footer-nav-link:hover {
  color: rgba(32, 90, 255, 0.95);
  border-bottom-color: rgba(32, 90, 255, 0.35);
}

.testimonials {
  margin-top: 28px;
  scroll-margin-top: 88px;
}

.testimonials__inner {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.92), rgba(246, 249, 255, 0.78));
  box-shadow: 0 18px 60px rgba(10, 20, 45, 0.1);
  padding: 22px 20px 24px;
}

.testimonials__title {
  margin: 0;
  font-size: 20px;
  font-weight: 650;
}

.testimonials__lead {
  margin: 10px 0 0;
  color: rgba(10, 20, 45, 0.65);
  font-size: 14px;
  line-height: 1.5;
  max-width: 720px;
}

.testimonials__grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.testimonial-card {
  margin: 0;
  padding: 16px 16px 14px;
  border-radius: 14px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(255, 255, 255, 0.88);
}

.testimonial-card__quote {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: rgba(10, 20, 45, 0.88);
}

.testimonial-card__meta {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: rgba(10, 20, 45, 0.55);
}

.testimonial-card__author {
  font-weight: 600;
  color: rgba(10, 20, 45, 0.72);
}

.legal-blocks {
  margin-top: 18px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.legal-blocks__row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.legal-card {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.88), rgba(246, 249, 255, 0.72));
  box-shadow: 0 14px 48px rgba(10, 20, 45, 0.08);
  padding: 20px 18px 22px;
  scroll-margin-top: 88px;
}

.legal-card--span {
  scroll-margin-top: 88px;
}

.legal-card__title {
  margin: 0;
  font-size: 18px;
  font-weight: 650;
}

.legal-card__p {
  margin: 12px 0 0;
  font-size: 14px;
  line-height: 1.55;
  color: rgba(10, 20, 45, 0.72);
}

.legal-card__p:first-of-type {
  margin-top: 14px;
}

@media (max-width: 900px) {
  .testimonials__grid {
    grid-template-columns: 1fr;
  }

  .legal-blocks__row {
    grid-template-columns: 1fr;
  }
}

.dot {
  opacity: 0.6;
}

.back-link {
  color: rgba(10, 20, 45, 0.8);
  text-decoration: none;
  border-bottom: 1px dashed rgba(10, 20, 45, 0.35);
}

.back-link:hover {
  border-bottom-color: rgba(32, 90, 255, 0.55);
}

.lang-btn:focus-visible,
.new-nav__btn:focus-visible,
.cta-btn:focus-visible,
.area-link:focus-visible,
.back-link:focus-visible,
.footer-nav-link:focus-visible {
  outline: 3px solid rgba(32, 90, 255, 0.55);
  outline-offset: 2px;
}

@media (max-width: 820px) {
  .areas {
    grid-template-columns: 1fr;
  }

  .new-header {
    gap: 12px;
    flex-wrap: wrap;
  }

  .hero__title {
    font-size: 30px;
  }

  .hero__grid {
    grid-template-columns: 1fr;
  }
}

.hero,
.trusted,
.areas,
.testimonials,
.legal-blocks {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 420ms ease, transform 420ms ease;
}

.hero.is-ready,
.trusted.is-ready,
.areas.is-ready,
.testimonials.is-ready,
.legal-blocks.is-ready {
  opacity: 1;
  transform: translateY(0);
}

.trusted.is-ready {
  transition-delay: 60ms;
}

.areas.is-ready {
  transition-delay: 110ms;
}

.testimonials.is-ready {
  transition-delay: 140ms;
}

.legal-blocks.is-ready {
  transition-delay: 170ms;
}

@keyframes float {
  0%,
  100% {
    transform: translate3d(0, 0, 0);
  }
  50% {
    transform: translate3d(0, -14px, 0);
  }
}

@keyframes marquee {
  0% {
    transform: translateX(0);
  }
  100% {
    transform: translateX(-100%);
  }
}

@media (prefers-reduced-motion: reduce) {
  .orb,
  .marquee__track,
  .hero-panel {
    animation: none !important;
  }
  .hero,
  .trusted,
  .areas,
  .testimonials,
  .legal-blocks,
  .cta-btn,
  .new-nav__btn,
  .area-link,
  .area-card {
    transition: none !important;
  }
}

/* Premium refresh */
.new-app {
  background:
    radial-gradient(980px 560px at 8% 6%, rgba(98, 70, 255, 0.16), transparent 62%),
    radial-gradient(900px 520px at 88% 14%, rgba(0, 194, 255, 0.14), transparent 64%),
    radial-gradient(760px 520px at 55% 92%, rgba(32, 90, 255, 0.13), transparent 58%),
    linear-gradient(180deg, #f4f7ff 0%, #f8fbff 56%, #f7f9ff 100%);
}

.new-header {
  background: rgba(248, 250, 255, 0.78);
  border-bottom-color: rgba(10, 20, 45, 0.07);
  box-shadow: 0 8px 30px rgba(10, 20, 45, 0.06);
}

.hero__title {
  font-size: clamp(34px, 5.5vw, 52px);
  line-height: 1.02;
}

.hero__subtitle {
  font-size: 16px;
}

.hero-panel,
.trusted__inner,
.area-card {
  background: linear-gradient(170deg, rgba(255, 255, 255, 0.88), rgba(246, 249, 255, 0.72));
  border: 1px solid rgba(10, 20, 45, 0.08);
  backdrop-filter: blur(6px);
}

.hero-panel {
  box-shadow: 0 24px 80px rgba(10, 20, 45, 0.12);
  transform: translateZ(0);
  animation: panelFloat 9s ease-in-out infinite;
}

.hero-panel__title {
  font-size: 17px;
}

.pill {
  border-color: rgba(32, 90, 255, 0.2);
  background: rgba(255, 255, 255, 0.86);
}

.cta-btn,
.new-nav__btn,
.area-link {
  position: relative;
  overflow: hidden;
}

.cta-btn::after,
.new-nav__btn::after,
.area-link::after {
  content: "";
  position: absolute;
  inset: 0;
  background: linear-gradient(120deg, transparent 22%, rgba(255, 255, 255, 0.35), transparent 78%);
  transform: translateX(-125%);
  transition: transform 0.6s ease;
}

.cta-btn:hover::after,
.new-nav__btn:hover::after,
.area-link:hover::after {
  transform: translateX(125%);
}

.cta-btn {
  padding: 13px 16px;
  border-radius: 15px;
  font-weight: 560;
}

.cta-btn--primary {
  background: linear-gradient(135deg, #365cff 0%, #2a7dff 55%, #14b8ff 100%);
  box-shadow: 0 14px 34px rgba(41, 84, 255, 0.26);
}

.cta-btn--primary:hover {
  box-shadow: 0 18px 42px rgba(41, 84, 255, 0.32);
}

.area-card {
  transition: transform 0.28s ease, box-shadow 0.28s ease, border-color 0.28s ease;
}

.area-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 26px 70px rgba(16, 35, 70, 0.15);
  border-color: rgba(32, 90, 255, 0.24);
}

.area-card__title {
  font-size: 18px;
}

.area-link {
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.88);
  border-color: rgba(10, 20, 45, 0.11);
}

.area-link:hover {
  background: rgba(255, 255, 255, 0.96);
}

.logo-pill {
  background: rgba(255, 255, 255, 0.85);
}

@keyframes panelFloat {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-5px);
  }
}
</style>

