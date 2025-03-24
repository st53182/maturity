<template>
  <div id="app">
    <nav></nav>

    <!-- 🔹 Меню доступно только для авторизованных пользователей -->
    <div v-if="isAuthenticated" class="dashboard-menu">
      <button @click="$router.push('/dashboard')" class="menu-btn">🏠 Личный кабинет</button>
      <button @click="$router.push('/survey')" class="menu-btn">📝 Определить зрелость</button>
      <button @click="showTeamModal = true" class="menu-btn">➕ Создать команду</button>
      <button @click="logout" class="logout-btn">🚪 Выйти</button>
    </div>

    <router-view />

    <!-- 🔹 Pop-up для создания команды -->
    <div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
      <div class="modal">
        <h2>Создать новую команду</h2>
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
          "http://127.0.0.1:5000/create_team",
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
nav {
  display: flex;
  gap: 20px;
  padding: 10px;
}
.dashboard-menu {
  display: flex;
  justify-content: left;

  background: rgba(206, 221, 250, 0.56);
  padding: 15px;
  border-radius: 10px;
  margin-bottom: 20px;
  gap: 15px;
}

.menu-btn {
  background: #3498db;
  color: white;
  font-size: 16px;
  font-weight: bold;
   padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s ease;
}

.menu-btn:hover {
  background: #2980b9;
}

.logout-btn {
  color: white;
  font-size: 16px;
  font-weight: bold;
   padding: 12px 20px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.3s ease;
  background: #e74c3c;
}

.logout-btn:hover {
  background: #c0392b;
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
.delete-btn {
  background: #e74c3c;
  color: white;
  padding: 10px 15px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  font-weight: bold;
  transition: 0.3s;
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

.delete-btn:hover {
  background: #c0392b;
}
</style>