<template>
  <div class="login-container">
    <div class="login-box">
      <h2>Вход</h2>
      <form @submit.prevent="login">
        <input type="text" v-model="username" placeholder="Логин" required />
        <input type="password" v-model="password" placeholder="Пароль" required />
        <button type="submit">Войти</button>
      </form>
      <p class="register-link">Нет аккаунта? <router-link to="/register">Зарегистрироваться</router-link></p>
    </div>
    <div class="forgot-password-block">
  ❓ <strong>Забыли пароль?</strong>
  <p>Напишите нам на <a href="mailto:artjoms.grinakins@gmail.com">artjoms.grinakins@gmail.com</a>, и мы вам поможем.</p>
</div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      username: '',
      password: ''
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
}

/* Заголовок */
h2 {
  margin-bottom: 20px;
  font-size: 24px;
  color: #333;
}

/* Поля ввода */
input {
  width: 90%;
  padding: 12px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 16px;
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
.forgot-password-block a:hover {
  color: #0056b3;
}
</style>
