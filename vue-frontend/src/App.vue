<template>
  <div id="app">
    <!-- Mobile Hamburger Button -->
    <button v-if="isAuthenticated" class="mobile-hamburger" :class="{ 'menu-open': showMobileMenu }" @click="showMobileMenu = !showMobileMenu">
      <span class="hamburger-line"></span>
      <span class="hamburger-line"></span>
      <span class="hamburger-line"></span>
    </button>

    <!-- Desktop Sidebar -->
    <aside class="modern-sidebar" v-if="isAuthenticated">
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
      <button class="sidebar-btn" @click="$router.push('/profile')">
        <span>👤</span>
        <small>{{ $t('nav.dashboard') }}</small>
      </button>
      <button class="sidebar-btn" @click="$router.push('/dashboard')">
        <span>🏠</span>
        <small>{{ $t('nav.dashboard') }}</small>
      </button>
      <button class="sidebar-btn" @click="$router.push('/survey')">
        <span>📝</span>
        <small>{{ $t('nav.survey') }}</small>
      </button>
      <button class="sidebar-btn" @click="$router.push('/conflicts')">
        <span>🤝</span>
        <small>{{ $t('nav.conflicts') }}</small>
      </button>
      <button class="sidebar-btn" @click="$router.push('/motivation')">
        <span>🧠</span>
        <small>{{ $t('nav.motivation') }}</small>
      </button>
      <button class="sidebar-btn" @click="$router.push('/meeting-design')">
        <span>🎯</span>
        <small>{{ $t('meetingDesign.title') }}</small>
      </button>
      <button class="sidebar-btn" @click="openExternalLink('https://poker.growboard.ru')">
        <span>♠️</span>
        <small>{{ $t('nav.poker') }}</small>
      </button>
      <button class="sidebar-btn" @click="showTeamModal = true">
        <span style="color: white;">➕</span>
        <small>{{ $t('dashboard.createTeam') }}</small>
      </button>
      <button class="sidebar-btn" @click="logout">
        <span>🚪</span>
        <small>{{ $t('nav.logout') }}</small>
      </button>
    </aside>

    <!-- Mobile Navigation Menu -->
    <div v-if="isAuthenticated && showMobileMenu" class="mobile-menu-overlay" @click.self="showMobileMenu = false">
      <nav class="mobile-menu">
        <div class="mobile-menu-header">
          <h3>{{ $t('nav.dashboard') }}</h3>
          <div class="mobile-language-switcher">
            <button 
              @click="switchLanguage('ru')" 
              :class="{ active: $i18n.locale === 'ru' }"
              class="lang-btn-mobile"
            >
              RU
            </button>
            <button 
              @click="switchLanguage('en')" 
              :class="{ active: $i18n.locale === 'en' }"
              class="lang-btn-mobile"
            >
              EN
            </button>
          </div>
          <button class="mobile-menu-close" @click="showMobileMenu = false">✕</button>
        </div>
        <div class="mobile-menu-items">
          <button class="mobile-menu-btn" @click="navigateAndClose('/profile')">
            <span>👤</span>
            <span>{{ $t('nav.dashboard') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/dashboard')">
            <span>🏠</span>
            <span>{{ $t('nav.dashboard') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/survey')">
            <span>📝</span>
            <span>{{ $t('nav.survey') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/conflicts')">
            <span>🤝</span>
            <span>{{ $t('nav.conflicts') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/motivation')">
            <span>🧠</span>
            <span>{{ $t('nav.motivation') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/meeting-design')">
            <span>🎯</span>
            <span>{{ $t('meetingDesign.title') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="openExternalLinkAndClose('https://poker.growboard.ru')">
            <span>♠️</span>
            <span>{{ $t('nav.poker') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="openTeamModalAndClose()">
            <span>➕</span>
            <span>{{ $t('dashboard.createTeam') }}</span>
          </button>
          <button class="mobile-menu-btn logout-btn" @click="logout">
            <span>🚪</span>
            <span>{{ $t('nav.logout') }}</span>
          </button>
        </div>
      </nav>
    </div>

    <!-- Основной контент -->
    <main class="main-content">
      <router-view />


    </main>

<div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
  <div class="modal">
    <h2 style="text-align: center;">{{ $t('survey.createNewTeam') }}</h2>
    <p class="modal-subtitle"></p>
    <input
      v-model="newTeamName"
      :placeholder="$t('survey.teamName')"
      class="team-input"
      @keyup.enter="createTeam"
    />
    <div class="modal-buttons">
          <button class="confirm-btn" @click="createTeam">✅ {{ $t('survey.create') }}</button>
          <button class="cancel-btn" @click="showTeamModal = false">❌ {{ $t('survey.cancel') }}</button>

    </div>
  </div>
</div>

  </div>
</template>


<script>
import axios from "axios";
import { useAuthStore } from "@/stores/auth";
import { computed, ref, getCurrentInstance } from "vue";


export default {
  setup() {
    const authStore = useAuthStore();

    // ✅ Проверяем авторизацию
    const isAuthenticated = computed(() => authStore.isAuthenticated);

    // ✅ Добавляем реактивные переменные
    const showTeamModal = ref(false);
    const newTeamName = ref("");
    const showMobileMenu = ref(false);

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

    // ✅ Функции для мобильного меню
    const navigateAndClose = (route) => {
      showMobileMenu.value = false;
      window.location.href = route;
    };

    const openTeamModalAndClose = () => {
      showMobileMenu.value = false;
      showTeamModal.value = true;
    };

    const openExternalLink = (url) => {
      try {
        window.open(url, '_blank');
      } catch (error) {
        console.error('Error opening external link:', error);
        window.location.href = url;
      }
    };

    const openExternalLinkAndClose = (url) => {
      showMobileMenu.value = false;
      try {
        window.open(url, '_blank');
      } catch (error) {
        console.error('Error opening external link:', error);
        window.location.href = url;
      }
    };

    return { 
      isAuthenticated, 
      showTeamModal, 
      newTeamName, 
      showMobileMenu,
      logout, 
      createTeam,
      navigateAndClose,
      openTeamModalAndClose,
      openExternalLink,
      openExternalLinkAndClose,
      switchLanguage: (lang) => {
        // Access i18n through the global properties
        const app = getCurrentInstance();
        if (app) {
          app.appContext.config.globalProperties.$i18n.locale = lang;
          localStorage.setItem('language', lang);
        }
      }
    };
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

.language-switcher {
  display: flex;
  gap: 5px;
  margin-bottom: 15px;
  justify-content: center;
}

.lang-btn {
  padding: 5px 10px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: transparent;
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s ease;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.lang-btn.active {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
}

.mobile-language-switcher {
  display: flex;
  gap: 5px;
}

.lang-btn-mobile {
  padding: 3px 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: transparent;
  color: #fff;
  border-radius: 3px;
  cursor: pointer;
  font-size: 10px;
  transition: all 0.3s ease;
}

.lang-btn-mobile:hover {
  background: rgba(255, 255, 255, 0.1);
}

.lang-btn-mobile.active {
  background: rgba(255, 255, 255, 0.2);
  border-color: rgba(255, 255, 255, 0.5);
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

/* Mobile Hamburger Button */
.mobile-hamburger {
  display: none;
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 999;
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  border-radius: 8px;
  width: 50px;
  height: 50px;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: all 0.3s ease;
}

.mobile-hamburger.menu-open {
  opacity: 0;
  pointer-events: none;
}

.mobile-hamburger:hover {
  transform: scale(1.05);
}

.hamburger-line {
  width: 20px;
  height: 2px;
  background: white;
  border-radius: 1px;
  transition: all 0.3s ease;
}

/* Mobile Menu Overlay */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  z-index: 1002;
  display: flex;
  justify-content: flex-start;
  align-items: flex-start;
  animation: fadeIn 0.3s ease;
}

.mobile-menu {
  background: white;
  width: 280px;
  height: 100%;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.1);
  animation: slideInLeft 0.3s ease;
  display: flex;
  flex-direction: column;
}

.mobile-menu-header {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.mobile-menu-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.mobile-menu-close {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: background 0.2s ease;
}

.mobile-menu-close:hover {
  background: rgba(255, 255, 255, 0.2);
}

.mobile-menu-items {
  flex: 1;
  padding: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.mobile-menu-btn {
  background: none;
  border: none;
  padding: 15px 20px;
  display: flex;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  transition: background 0.2s ease;
  font-size: 16px;
  color: #333;
  text-align: left;
  width: 100%;
}

.mobile-menu-btn:hover {
  background: #f8f9fa;
}

.mobile-menu-btn span:first-child {
  font-size: 20px;
  width: 24px;
  text-align: center;
}

.mobile-menu-btn.logout-btn {
  margin-top: auto;
  color: #e74c3c;
  border-top: 1px solid #eee;
}

.mobile-menu-btn.logout-btn:hover {
  background: #ffeaea;
}

/* Animations */
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideInLeft {
  from { transform: translateX(-100%); }
  to { transform: translateX(0); }
}

@media (max-width: 768px) {
  .mobile-hamburger {
    display: flex !important;
  }
  
  .modern-sidebar {
    display: none !important;
  }
  
  .main-content, .results-container {
    margin-left: 0 !important;
    padding: 15px !important;
    padding-top: 80px !important;
  }
  
  .modal {
    width: 95% !important;
    max-width: 95% !important;
    margin: 10px !important;
    padding: 15px !important;
  }
  
  .team-input {
    width: 100% !important;
    font-size: 16px !important;
    box-sizing: border-box !important;
  }
  
  .modal-buttons {
    flex-direction: column !important;
    gap: 10px !important;
  }
  
  .confirm-btn,
  .cancel-btn {
    max-width: 100% !important;
    width: 100% !important;
  }
}
</style>
