<template>
  <div class="home-container">
    <header>
      <div class="logo"></div>
      <nav>
        <router-link to="/login" class="nav-btn">Войти</router-link>
        <router-link to="/register" class="nav-btn">Регистрация</router-link>
      </nav>
    </header>

    <main>
      <h1>Оцените зрелость вашей Agile-команды</h1>
      <p>Пройдите опрос и получите персонализированные рекомендации по улучшению вашей команды.</p>

      <div class="business-category">
        <label>Выберите сферу деятельности:</label>
        <select v-model="selectedCategory">
          <option v-for="category in categories" :key="category.id" :value="category.name">
            {{ category.name }}
          </option>
        </select>
      </div>

      <router-link :to="'/survey?category=' + selectedCategory" class="start-btn">Пройти оценку</router-link>
    </main>

    <footer>
      <p>&copy; 2025 Scrum Maturity. Все права защищены.</p>
    </footer>
  </div>
</template>

<script>
export default {
  data() {
    return {
      selectedCategory: "Разработка ПО",
      categories: [
        { id: 1, name: "Разработка ПО" },
        { id: 2, name: "Фармацевтика (скоро)" },
        { id: 3, name: "Производство (скоро)" }
      ]
    };
  },
  methods: {
    goToSurvey() {
      const token = localStorage.getItem("token");
      if (token) {
        this.$router.push("/survey");
      } else {
        this.$router.push("/login"); // 🔄 Если не авторизован, отправляем на логин
      }
    }
  }
};
</script>


<style scoped>
/* Общий контейнер */
.home-container {
  font-family: 'Arial', sans-serif;
  text-align: center;
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: #f8f9fa;
  color: #333;
}

/* Шапка */
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 30px;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.logo {
  font-size: 24px;
  font-weight: bold;
  color: #007bff;
}

nav .nav-btn {
  margin-left: 20px;
  text-decoration: none;
  color: #007bff;
  font-weight: bold;
  padding: 8px 16px;
  border-radius: 4px;
  border: 2px solid #007bff;
  transition: 0.3s;
}

nav .nav-btn:hover {
  background: #007bff;
  color: white;
}

/* Основной контент */
main {
  flex: 1;
  padding: 50px;
}

h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

p {
  font-size: 18px;
  color: #555;
  margin-bottom: 30px;
}

/* Категория бизнеса */
.business-category {
  margin-bottom: 20px;
}

select {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ccc;
  border-radius: 5px;
}

/* Кнопка "Пройти оценку" */
.start-btn {
  display: inline-block;
  padding: 12px 24px;
  background: #007bff;
  color: white;
  font-size: 18px;
  text-decoration: none;
  border-radius: 5px;
  transition: 0.3s;
}

.start-btn:hover {
  background: #0056b3;
}

/* Подвал */
footer {
  background: white;
  padding: 10px;
  font-size: 14px;
  color: #666;
}
</style>
