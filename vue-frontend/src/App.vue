<template>
  <div id="app">
   <!-- Sidebar -->
<aside class="modern-sidebar" v-if="isAuthenticated">
  <button class="sidebar-btn" @click="$router.push('/profile')">
    <span>👤</span>
    <small>Мой профиль</small>
  </button>
  <button class="sidebar-btn" @click="$router.push('/dashboard')">
    <span>🏠</span>
    <small>Мои команды</small>
  </button>
  <button class="sidebar-btn" @click="$router.push('/survey')">
    <span>📝</span>
    <small>Зрелость</small>
  </button>
  <button class="sidebar-btn" @click="$router.push('/conflicts')">
  <span>🤝</span>
  <small>Конфликты & Проблемы</small>
</button>
  <button class="sidebar-btn" @click="$router.push('/motivation')">
    <span>🧠</span>
    <small>Сотрудники & Мотивация</small>
  </button>
  <button class="sidebar-btn" @click="showTeamModal = true">
     <span style="color: white;">➕</span>
    <small>Создать команду</small>
  </button>
  <button class="sidebar-btn" @click="logout">
    <span>🚪</span>
    <small>Выйти</small>
  </button>
</aside>

    <!-- Основной контент -->
    <main class="main-content">
      <router-view />


    </main>

<div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
  <div class="modal">
    <h2 style="text-align: center;">Создать новую команду</h2>
    <p class="modal-subtitle"></p>
    <input
      v-model="newTeamName"
      placeholder="Название команды"
      class="team-input"
      @keyup.enter="createTeam"
    />
    <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ Создать</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ Отмена</button>

    </div>
  </div>
</div>

  </div>
</template>


<script>
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { computed, ref } from "vue";


export default {
  setup() {
    const authStore = useAuthStore();

    // ✅ Проверяем авторизацию
    const isAuthenticated = computed(() => authStore.isAuthenticated);

    // ✅ Добавляем реактивные переменные
    const showTeamModal = ref(false);
    const newTeamName = ref("");

    // ✅ Функция выхода
    const logout = () => {
      authStore.logout();
      showTeamModal.value = false;
      window.location.href = "/login"; // Обновляем страницу после выхода
    };

    // ✅ Функция создания команды
    const createTeam = async () => {
      if (!newTeamName.value.trim()) {
        alert("Введите название команды!");
        return;
      }

      try {
        console.log("📤 Создание команды...");
        const token = localStorage.getItem("token");

        if (!token) {
          console.error("❌ Нет токена авторизации!");
          alert("🚫 Вы не авторизованы!");
          return;
        }

        const res = await axios.post(
          "/create_team",
          { team_name: newTeamName.value },
          { headers: { Authorization: `Bearer ${token}` } }
        );

        console.log("✅ Команда успешно создана:", res.data);


        showTeamModal.value = false; // Закрываем pop-up
        alert("🎉 Команда создана!");

        // Можно обновить список команд через authStore (если там есть `fetchTeams`)


          window.location.reload();

      } catch (error) {
        console.error("❌ Ошибка создания команды:", error.response?.data || error);
        alert("❌ Ошибка создания команды. Убедись не занято ли имя команды");
      }
    };

    return { isAuthenticated, showTeamModal, newTeamName, logout, createTeam };
  },
};

</script>


<style>
/* Основной контейнер */


.modern-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 85px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  z-index: 1000;
  gap: 15px;
}

.sidebar-btn {
  background: none;
  border: none;
  color: white;
  font-size: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.sidebar-btn small {
  font-size: 12px;
}

.sidebar-btn:hover {
  transform: scale(1.1);
}

.sidebar-btn.logout {
  margin-top: auto;
  color: #ffcccc;
}
.main-content, .results-container {
  margin-left: 70px; /* равен ширине sidebar */
  padding: 20px;
   flex-grow: 1;
}
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal {
  background: white;
  padding: 20px;
  border-radius: 10px;
  width: 350px; /* Ширина Pop-up */
  max-width: 90%; /* Адаптация к мобильным экранам */
}

.confirm-btn,
.cancel-btn {
  flex: 1; /* Одинаковая ширина */
  background: #2ecc71;
  color: white;
  padding: 15px;
  border-radius: 12px;
  font-size: 18px;
  font-weight: bold;
  cursor: pointer;
  border: none;
  transition: 0.3s;
  text-align: center;
  max-width: 160px; /* Максимальная ширина кнопки */
  max-height: 100px;
}

.confirm-btn:hover {
  background: #27ae60;
}

.cancel-btn {
  background: #e74c3c;
}

.cancel-btn:hover {
  background: #c0392b;
}

.team-input:focus {
  border-color: #2ecc71;
  outline: none;
}
.team-input {
  width: 90%;
  padding: 14px;
  border: 3px solid #3498db;
  border-radius: 10px;
  font-size: 18px;
  text-align: center;
  transition: 0.3s;
  margin-top: 5px;
}

.modal-buttons {
  display: flex;
  justify-content: space-evenly; /* Равномерное распределение */
  align-items: center;
  margin-top: 25px;
  gap: 15px;
}
</style>