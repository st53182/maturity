<template>
  <div class="home-container">
    <header>
      <div class="logo">GrowBoard</div>
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
      <nav>
        <router-link to="/login" class="nav-btn">{{ $t('auth.login') }}</router-link>
        <router-link to="/register" class="nav-btn">{{ $t('register.title') }}</router-link>
      </nav>
    </header>

    <main>
      <h1>{{ $t('home.title') }}</h1>
      <p>{{ $t('home.description') }}</p>

      <div class="business-category">
        <label>{{ $t('home.businessCategory') }}</label>
        <select v-model="selectedCategory">
          <option v-for="category in categories" :key="category.id" :value="category.name">
            {{ $t(category.translationKey) }}
          </option>
        </select>
      </div>

      <router-link :to="'/survey?category=' + selectedCategory" class="start-btn">
        🚀 {{ $t('home.startAssessment') }}
      </router-link>

      <section class="features">
        <div class="feature-card">
          <img src="/icons/brain.png" alt="Анализ зрелости" />
          <h3>{{ $t('home.features.maturityAnalysis') }}</h3>
          <p>{{ $t('home.features.maturityDescription') }}</p>
        </div>
        <div class="feature-card">
          <img src="/icons/motivation.png" alt="Мотивация" />
          <h3>{{ $t('home.features.discMotivation') }}</h3>
          <p>{{ $t('home.features.discDescription') }}</p>
        </div>
        <div class="feature-card">
          <img src="/icons/conflict.png" alt="Конфликты" />
          <h3>{{ $t('home.features.conflictResolution') }}</h3>
          <p>{{ $t('home.features.conflictDescription') }}</p>
        </div>
      </section>
    </main>

    <footer>
      <p>{{ $t('home.footer') }}</p>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedCategory: "Разработка ПО",
      categories: [
        { id: 1, name: "Разработка ПО", translationKey: "home.categories.softwareDev" },
        { id: 2, name: "Фармацевтика (скоро)", translationKey: "home.categories.pharma" },
        { id: 3, name: "Производство (скоро)", translationKey: "home.categories.manufacturing" }
      ]
    };
  },
  methods: {
    switchLanguage(lang) {
      this.$i18n.locale = lang;
      localStorage.setItem('language', lang);
    }
  }
};
</script>

<style scoped>
.home-container {
  font-family: 'Segoe UI', sans-serif;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f9f9fb;
  color: #2c3e50;
  text-align: center;
}

header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 40px;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.language-switcher {
  display: flex;
  gap: 5px;
}

.lang-btn {
  padding: 5px 10px;
  border: 1px solid #007bff;
  background: transparent;
  color: #007bff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.lang-btn:hover {
  background: rgba(0, 123, 255, 0.1);
}

.lang-btn.active {
  background: #007bff;
  color: white;
}

.logo {
  font-size: 24px;
  font-weight: 600;
  color: #007bff;
}

nav .nav-btn {
  margin-left: 20px;
  text-decoration: none;
  color: #007bff;
  font-weight: 500;
  padding: 10px 18px;
  border: 2px solid #007bff;
  border-radius: 8px;
  transition: 0.3s;
}

nav .nav-btn:hover {
  background: #007bff;
  color: white;
}

main {
  padding: 60px 20px;
  flex: 1;
}

h1 {
  font-size: 32px;
  margin-bottom: 16px;
}

p {
  font-size: 18px;
  color: #555;
  margin-bottom: 30px;
}

.business-category {
  margin: 30px 0 20px;
}

.business-category label {
  font-weight: 500;
  margin-right: 10px;
}

select {
  padding: 10px;
  font-size: 16px;
  border-radius: 8px;
  border: 1px solid #ccc;
}

.start-btn {
  display: inline-block;
  padding: 14px 28px;
  margin-top: 10px;
  font-size: 18px;
  font-weight: 500;
  color: white;
  background-color: #28a745;
  border-radius: 10px;
  text-decoration: none;
  transition: background 0.3s ease;
}

.start-btn:hover {
  background-color: #218838;
}

/* Новая секция "Возможности" */
.features {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 30px;
  margin-top: 60px;
}

.feature-card {
  background: white;
  padding: 24px;
  border-radius: 16px;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.06);
  text-align: center;
  max-width: 300px;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.12);
}

.feature-card img {
  width: 48px;
  margin-bottom: 14px;
}

.feature-card h3 {
  font-size: 18px;
  color: #007bff;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 14px;
  color: #555;
}

/* Подвал */
footer {
  text-align: center;
  padding: 16px;
  background: white;
  font-size: 14px;
  color: #888;
}
</style>
