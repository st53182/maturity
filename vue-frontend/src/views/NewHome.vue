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
      <section class="hero">
        <h1 class="hero__title">Инструменты развития команд и продуктов</h1>
        <p class="hero__subtitle">
          Новая версия: группируем инструменты по ролям. Функциональность будем переносить постепенно.
        </p>
      </section>

      <section class="areas">
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

      <section class="next">
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
  background: radial-gradient(1200px 600px at 10% 10%, rgba(102, 126, 234, 0.15), transparent 60%),
    radial-gradient(1000px 500px at 90% 20%, rgba(118, 75, 162, 0.14), transparent 55%),
    #0b1020;
  color: rgba(255, 255, 255, 0.92);
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
  background: rgba(11, 16, 32, 0.7);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
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
}

.new-nav__btn--primary {
  border-color: rgba(102, 126, 234, 0.65);
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.95), rgba(118, 75, 162, 0.9));
}

.new-main {
  max-width: 1100px;
  margin: 0 auto;
  padding: 34px 18px 56px;
}

.hero {
  padding: 22px 4px 10px;
}

.hero__title {
  margin: 0;
  font-size: 34px;
  line-height: 1.12;
  letter-spacing: -0.4px;
}

.hero__subtitle {
  margin: 14px 0 0;
  color: rgba(255, 255, 255, 0.72);
  max-width: 840px;
  line-height: 1.5;
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
}

.area-card--accent {
  border-color: rgba(102, 126, 234, 0.4);
  background: linear-gradient(180deg, rgba(102, 126, 234, 0.18), rgba(255, 255, 255, 0.06));
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
  transition: 0.2s ease;
}

.area-link:hover {
  background: rgba(11, 16, 32, 0.55);
  border-color: rgba(255, 255, 255, 0.24);
}

.next {
  margin-top: 18px;
}

.next__box {
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.05);
  padding: 16px 18px;
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
    font-size: 28px;
  }
}
</style>

