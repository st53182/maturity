<template>
  <div class="login-container">
    <div class="login-box">
      <div class="language-switcher-login">
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
      <h2>{{ $t('auth.login') }}</h2>
      <form @submit.prevent="login">
        <input type="text" v-model="username" :placeholder="$t('auth.username')" required />
        <input type="password" v-model="password" :placeholder="$t('auth.password')" required />
        <button type="submit">{{ $t('auth.loginButton') }}</button>
      </form>
      <p class="register-link">{{ $t('auth.noAccount') }} <router-link to="/register">{{ $t('auth.register') }}</router-link></p>
      <div class="forgot-password-toggle">
  <button @click="showHelp = !showHelp" class="link-button">
    {{ $t('auth.forgotPassword') }}
  </button>

  <div v-if="showHelp" class="forgot-password-block">
    <p>
      {{ $t('auth.contactUs') }}
      <a href="mailto:artjoms.grinakins@gmail.com">artjoms.grinakins@gmail.com</a>, {{ $t('auth.weWillHelp') }}
    </p>
  </div>
</div>
    </div>

  </div>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: '',
      showHelp: false,
    };
  },
  methods: {
    async login() {
      try {
        const response = await fetch('/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: this.username, password: this.password })
        });
        const data = await response.json();
        if (response.ok) {
          localStorage.setItem('token', data.access_token);
          this.$router.push('/dashboard');
        } else {
          alert(data.message);
        }
      } catch (error) {
        console.error('Ошибка входа:', error);
      }
    },
    switchLanguage(lang) {
      this.$i18n.locale = lang;
      localStorage.setItem('language', lang);
    }
  }
};
</script>

<style scoped>
/* Фон в стиле Google */
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(to bottom, #f8f9fa, #e9ecef);
}

/* Карточка формы */
.login-box {
  background: white;
  padding: 40px;
  border-radius: 12px;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 360px;
  width: 100%;
  position: relative;
}

.language-switcher-login {
  position: absolute;
  top: 15px;
  right: 15px;
  display: flex;
  gap: 5px;
}

.lang-btn {
  padding: 5px 10px;
  border: 1px solid #ddd;
  background: transparent;
  color: #333;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.lang-btn:hover {
  background: rgba(0, 123, 255, 0.1);
}

.lang-btn.active {
  background: #007bff;
  border-color: #007bff;
  color: white;
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
  border-color: #3b82f6;
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.12), 0 2px 8px rgba(59, 130, 246, 0.08);
  background: #fafbff;
}

/* Кнопка входа */
button {
  width: 100%;
  padding: 12px;
  background-color: #4285f4;
  color: white;
  font-size: 18px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.3s ease;
}

/* Анимация кнопки */
button:hover {
  background-color: #357ae8;
}

/* Ссылка на регистрацию */
.register-link {
  margin-top: 15px;
  font-size: 14px;
}

.forgot-password-block {
  margin-top: 20px;
  background-color: #f8f9fa;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
}

.forgot-password-block a {
  color: #007bff;
  text-decoration: underline;
}

.link-button {
  background: none;
  border: none;
  color: #999;
  font-weight: normal;
  font-size: 14px;
  cursor: pointer;
  margin-top: 15px;
  padding: 0;
  transition: color 0.3s ease;
}

.link-button:hover {
  color: #555;
  text-decoration: underline;
}

.forgot-password-block {
  background: #f8f9fa;
  padding: 12px;
  margin-top: 10px;
  border-radius: 8px;
  font-size: 14px;
  color: #333;
}
</style>
