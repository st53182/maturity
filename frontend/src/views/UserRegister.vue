<template>
  <div class="register-container">
    <div class="register-box">
      <h2>Регистрация</h2>
      <form @submit.prevent="register">
        <input type="text" v-model="username" placeholder="Логин" required />
        <input type="password" v-model="password" placeholder="Пароль" required />
        <button type="submit">Зарегистрироваться</button>
      </form>
      <p class="login-link">Уже есть аккаунт? <router-link to="/login">Войти</router-link></p>
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
    async register() {
      try {
        const response = await fetch('http://localhost:5000/register', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username: this.username, password: this.password })
        });
        const data = await response.json();
        if (response.ok) {
          alert('Регистрация успешна! Теперь войдите.');
          this.$router.push('/login');
        } else {
          alert(data.message);
        }
      } catch (error) {
        console.error('Ошибка регистрации:', error);
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
  padding: 12px;
  margin: 10px 0;
  border: 1px solid #ccc;
  border-radius: 6px;
  font-size: 16px;
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

