<template>
  <div class="register-container">
    <div class="language-switcher">
      <button @click="changeLanguage('ru')" :class="{ active: $i18n.locale === 'ru' }">RU</button>
      <button @click="changeLanguage('en')" :class="{ active: $i18n.locale === 'en' }">EN</button>
    </div>
    <div class="register-box">
      <h2>{{ $t('register.title') }}</h2>
      <form @submit.prevent="register">
        <input type="email" v-model="email" :placeholder="$t('register.email')" required />
        <input type="password" v-model="password" :placeholder="$t('register.password')" required />
        <button type="submit">{{ $t('register.registerButton') }}</button>
      </form>
      <p class="login-link">{{ $t('register.hasAccount') }} <router-link to="/login">{{ $t('register.login') }}</router-link></p>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      password: '',
      email: '',

    };
  },
  methods: {
    changeLanguage(lang) {
      this.$i18n.locale = lang;
      localStorage.setItem('language', lang);
    },
    async register() {
      try {
        const response = await fetch('/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email: this.email, password: this.password })
        });
        const data = await response.json();
        if (response.ok) {
          alert(this.$t('register.success'));
          this.$router.push('/login');
        } else {
          alert(data.message);
        }
      } catch (error) {
        console.error(this.$t('register.error'), error);
      }
    }
  }
};
</script>

<style scoped>
/* Фон */
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
  position: relative;
}

.language-switcher {
  position: absolute;
  top: 20px;
  right: 20px;
  display: flex;
  gap: 5px;
}

.language-switcher button {
  padding: 5px 10px;
  border: 1px solid rgba(0, 0, 0, 0.3);
  background: transparent;
  color: #333;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.language-switcher button:hover {
  background: rgba(0, 0, 0, 0.1);
}

.language-switcher button.active {
  background: rgba(0, 0, 0, 0.2);
  border-color: rgba(0, 0, 0, 0.5);
}

/* Карточка */
.register-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 360px;
  width: 100%;
}

/* Заголовок */
h2 {
  margin-bottom: 20px;
  font-size: 24px;
  color: #333;
}

/* Поля ввода */
input {
  width: 100%;
  padding: 14px 18px;
  margin: 12px 0;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  background: #ffffff;
  color: #111827;
  box-sizing: border-box;
}

input::placeholder {
  color: #9ca3af;
  font-weight: 400;
}

input:hover {
  border-color: #cbd5e1;
}

input:focus {
  outline: none;
  border-color: #10b981;
  box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.12), 0 2px 8px rgba(16, 185, 129, 0.08);
  background: #f0fdf4;
}

/* Кнопка */
button {
  width: 100%;
  padding: 12px;
  background-color: #34a853;
  color: white;
  font-size: 18px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s ease;
}

/* Эффект кнопки */
button:hover {
  background-color: #2c8c47;
}

/* Ссылка на вход */
.login-link {
  margin-top: 15px;
  font-size: 14px;
}
</style>

