<template>
  <div class="new-app">
    <header class="new-header">
      <div class="brand">
        <div class="brand__logo">GrowBoard</div>
        <div class="brand__tag">New</div>
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
          <router-link to="/login" class="new-nav__btn">Войти</router-link>
          <router-link to="/register" class="new-nav__btn new-nav__btn--primary">Регистрация</router-link>
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
            <div class="hero__kicker">Новая версия интерфейса</div>
            <h1 class="hero__title">Инструменты развития команд и продуктов</h1>
            <p class="hero__subtitle">
              Мы группируем инструменты по ролям и будем улучшать функциональность постепенно — без поломок текущей версии.
            </p>

            <div class="hero__cta">
              <router-link to="/maturity/create" class="cta-btn cta-btn--primary">Начать с оценки зрелости</router-link>
              <router-link to="/dashboard" class="cta-btn">Открыть дашборд</router-link>
            </div>
          </div>

          <div class="hero__right">
            <div class="hero-panel">
              <div class="hero-panel__title">4 области инструментов</div>
              <div class="hero-panel__list">
                <div class="pill">Скрам Мастера / Тим Лиды</div>
                <div class="pill">PM / руководители</div>
                <div class="pill">Product / владельцы продукта</div>
                <div class="pill">Бизнес / предприниматели</div>
              </div>
              <div class="hero-panel__note">
                Дальше перенесём «Оценку зрелости команды» и «Дашборд» в ветку <code>/new</code>.
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="areas" :class="{ 'is-ready': isReady }">
        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">Для Скрам Мастеров / Тим Лидов / Фасилитаторов</h2>
            <p class="area-card__desc">Фасилитация, работа с конфликтами, улучшение процессов.</p>
          </div>
          <div class="area-card__links">
            <router-link to="/conflicts" class="area-link">Разрешение конфликтов</router-link>
            <router-link to="/meeting-design" class="area-link">Дизайн встреч</router-link>
            <router-link to="/system-thinking" class="area-link">Айсберг системного мышления</router-link>
            <router-link to="/backlog-prep" class="area-link">Подготовка бэклога</router-link>
          </div>
        </article>

        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">Для руководителей и менеджеров проекта</h2>
            <p class="area-card__desc">Прозрачность, управление рисками и предсказуемость поставки.</p>
          </div>
          <div class="area-card__links">
            <router-link to="/flow-metrics" class="area-link">Flow Metrics</router-link>
            <router-link to="/roadmap" class="area-link">Зависимости и дорожная карта</router-link>
            <router-link to="/project-card" class="area-link">Карточка проекта</router-link>
            <a class="area-link" href="https://poker.growboard.ru" target="_blank" rel="noreferrer">Planning Poker</a>
          </div>
        </article>

        <article class="area-card">
          <div class="area-card__head">
            <h2 class="area-card__title">Для владельцев продукта / менеджеров продукта</h2>
            <p class="area-card__desc">Качество гипотез, совместная работа с командой и фокус на ценности.</p>
          </div>
          <div class="area-card__links">
            <router-link to="/maturity/create" class="area-link">Оценка зрелости команды (по ссылке)</router-link>
            <router-link to="/surveys" class="area-link">Опросы и результаты</router-link>
            <router-link to="/qa" class="area-link">Практика QA</router-link>
          </div>
        </article>

        <article class="area-card area-card--accent">
          <div class="area-card__head">
            <h2 class="area-card__title">Для владельцев бизнеса / предпринимателей</h2>
            <p class="area-card__desc">Понимание проблем в поставке ценности и точки роста.</p>
          </div>
          <div class="area-card__links">
            <router-link to="/dashboard" class="area-link">Дашборд</router-link>
            <router-link to="/survey" class="area-link">Диагностика (опрос)</router-link>
            <router-link to="/usability-report" class="area-link">Отчёт по удобству</router-link>
          </div>
        </article>
      </section>

      <section class="next" :class="{ 'is-ready': isReady }">
        <div class="next__box">
          <div class="next__title">Дальше</div>
          <div class="next__text">
            Следующие шаги: переносим «Оценку зрелости команды» и «Дашборд» в ветку <code>/new</code>.
          </div>
        </div>
      </section>
    </main>

    <footer class="new-footer">
      <div class="new-footer__inner">
        <span>GrowBoard</span>
        <span class="dot">•</span>
        <router-link to="/" class="back-link">Перейти на текущую версию</router-link>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return { isReady: false };
  },
  mounted() {
    window.requestAnimationFrame(() => {
      this.isReady = true;
    });
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
  background: radial-gradient(900px 500px at 15% 10%, rgba(32, 90, 255, 0.25), transparent 60%),
    radial-gradient(900px 520px at 90% 18%, rgba(0, 194, 255, 0.16), transparent 62%),
    radial-gradient(700px 420px at 55% 90%, rgba(32, 90, 255, 0.12), transparent 58%),
    #060b19;
  color: rgba(255, 255, 255, 0.93);
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
  background: rgba(6, 11, 25, 0.62);
  border-bottom: 1px solid rgba(255, 255, 255, 0.09);
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

.brand__tag {
  font-size: 12px;
  padding: 4px 8px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.06);
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
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.9);
  border-radius: 10px;
  cursor: pointer;
  font-size: 12px;
  transition: 0.2s ease;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.lang-btn.active {
  border-color: rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.14);
}

.new-nav {
  display: flex;
  align-items: center;
  gap: 10px;
}

.new-nav__btn {
  text-decoration: none;
  color: rgba(255, 255, 255, 0.92);
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  transition: 0.2s ease;
  font-size: 14px;
}

.new-nav__btn:hover {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-1px);
}

.new-nav__btn--primary {
  border-color: rgba(32, 90, 255, 0.65);
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.95), rgba(0, 194, 255, 0.85));
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
  opacity: 0.55;
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
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.78);
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
  color: rgba(255, 255, 255, 0.72);
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
  color: rgba(255, 255, 255, 0.9);
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.06);
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
  font-size: 14px;
}

.cta-btn:hover {
  transform: translateY(-1px);
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.22);
}

.cta-btn--primary {
  border-color: rgba(32, 90, 255, 0.62);
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.82));
}

.hero-panel {
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  box-shadow: 0 20px 70px rgba(0, 0, 0, 0.35);
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
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(6, 11, 25, 0.35);
  font-size: 12px;
  color: rgba(255, 255, 255, 0.82);
}

.hero-panel__note {
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.68);
  font-size: 13px;
  line-height: 1.45;
}

.areas {
  margin-top: 26px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.area-card {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.06);
  overflow: hidden;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.22);
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
  color: rgba(255, 255, 255, 0.72);
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
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(11, 16, 32, 0.35);
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
  transition: transform 0.2s ease, background 0.2s ease, border-color 0.2s ease;
}

.area-link:hover {
  background: rgba(11, 16, 32, 0.55);
  border-color: rgba(255, 255, 255, 0.24);
  transform: translateY(-1px);
}

.next {
  margin-top: 18px;
}

.next__box {
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  padding: 16px 18px;
  box-shadow: 0 18px 60px rgba(0, 0, 0, 0.18);
}

.next__title {
  font-weight: 650;
}

.next__text {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.72);
  line-height: 1.5;
}

.new-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding: 18px 18px 24px;
  color: rgba(255, 255, 255, 0.7);
}

.new-footer__inner {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  opacity: 0.6;
}

.back-link {
  color: rgba(255, 255, 255, 0.88);
  text-decoration: none;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.35);
}

.back-link:hover {
  border-bottom-color: rgba(255, 255, 255, 0.65);
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
.areas,
.next {
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 420ms ease, transform 420ms ease;
}

.hero.is-ready,
.areas.is-ready,
.next.is-ready {
  opacity: 1;
  transform: translateY(0);
}

.areas.is-ready {
  transition-delay: 80ms;
}

.next.is-ready {
  transition-delay: 140ms;
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
</style>

