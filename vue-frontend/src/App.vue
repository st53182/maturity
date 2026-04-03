<template>
  <div id="app" :class="{ 'app--new': isNewUi }">
    <!-- Mobile Hamburger Button -->
    <button v-if="isAuthenticated" class="mobile-hamburger" :class="{ 'menu-open': showMobileMenu }" :aria-label="$t('common.menu')" @click="showMobileMenu = !showMobileMenu">
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
          :aria-pressed="$i18n.locale === 'ru'"
          class="lang-btn"
        >
          RU
        </button>
        <button 
          @click="switchLanguage('en')" 
          :class="{ active: $i18n.locale === 'en' }"
          :aria-pressed="$i18n.locale === 'en'"
          class="lang-btn"
        >
          EN
        </button>
      </div>
      <div class="sidebar-buttons-container">
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/profile' : '/profile')">
          <span>👤</span>
          <small>{{ $t('nav.profile') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/dashboard' : '/dashboard')">
          <span>🏠</span>
          <small>{{ $t('nav.dashboard') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/survey' : '/survey')">
          <span>📝</span>
          <small>{{ $t('nav.survey') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/conflicts' : '/conflicts')">
          <span>🤝</span>
          <small>{{ $t('nav.conflicts') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/motivation' : '/motivation')">
          <span>🧠</span>
          <small>{{ $t('nav.motivation') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/meeting-design' : '/meeting-design')">
          <span>🎯</span>
          <small>{{ $t('nav.meetingDesign') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/backlog-prep' : '/backlog-prep')">
          <span>🧭</span>
          <small>{{ $t('nav.backlogPrep') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/system-thinking' : '/system-thinking')">
          <span>🧊</span>
          <small>{{ $t('newHome.links.systemThinking') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/agile-kata' : '/agile-kata')">
          <span>🔬</span>
          <small>{{ $t('nav.agileKata') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/agile-tools' : '/agile-tools')">
          <span>📚</span>
          <small>{{ $t('nav.agileTools') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/metrics-tree' : '/metrics-tree')">
          <span>🌲</span>
          <small>{{ $t('nav.metricsTree') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/surveys' : '/surveys')">
          <span>📋</span>
          <small>{{ $t('nav.surveys') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push('/new/chat')">
          <span>💬</span>
          <small>{{ $t('nav.communityChat') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push('/new/tests')">
          <span>🧪</span>
          <small>{{ $t('nav.tests') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/maturity' : '/maturity/create')">
          <span>🔗</span>
          <small>{{ $t('nav.maturityLink') }}</small>
        </button>
        <button class="sidebar-btn" @click="$router.push(isNewUi ? '/new/project-card' : '/project-card')">
          <span>📑</span>
          <small>{{ $t('nav.projectCard') }}</small>
        </button>
        <button class="sidebar-btn" @click="openExternalLink('https://poker.growboard.ru')">
          <span>♠️</span>
          <small>{{ $t('nav.poker') }}</small>
        </button>
        <button class="sidebar-btn" @click="showTeamModal = true">
          <span style="color: white;">➕</span>
          <small>{{ $t('dashboard.createTeam') }}</small>
        </button>
        <button class="sidebar-btn logout" @click="logout">
          <span>🚪</span>
          <small>{{ $t('nav.logout') }}</small>
        </button>
      </div>
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
              :aria-pressed="$i18n.locale === 'ru'"
              class="lang-btn-mobile"
            >
              RU
            </button>
            <button 
              @click="switchLanguage('en')" 
              :class="{ active: $i18n.locale === 'en' }"
              :aria-pressed="$i18n.locale === 'en'"
              class="lang-btn-mobile"
            >
              EN
            </button>
          </div>
          <button class="mobile-menu-close" :aria-label="$t('common.close')" @click="showMobileMenu = false">✕</button>
        </div>
        <div class="mobile-menu-items">
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/profile' : '/profile')">
            <span>👤</span>
            <span>{{ $t('nav.profile') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/dashboard' : '/dashboard')">
            <span>🏠</span>
            <span>{{ $t('nav.dashboard') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/survey' : '/survey')">
            <span>📝</span>
            <span>{{ $t('nav.survey') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/conflicts' : '/conflicts')">
            <span>🤝</span>
            <span>{{ $t('nav.conflicts') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/motivation' : '/motivation')">
            <span>🧠</span>
            <span>{{ $t('nav.motivation') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/meeting-design' : '/meeting-design')">
            <span>🎯</span>
            <span>{{ $t('nav.meetingDesign') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/backlog-prep' : '/backlog-prep')">
            <span>🧭</span>
            <span>{{ $t('nav.backlogPrep') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/system-thinking' : '/system-thinking')">
            <span>🧊</span>
            <span>{{ $t('newHome.links.systemThinking') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/agile-kata' : '/agile-kata')">
            <span>🔬</span>
            <span>{{ $t('nav.agileKata') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/agile-tools' : '/agile-tools')">
            <span>📚</span>
            <span>{{ $t('nav.agileTools') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/metrics-tree' : '/metrics-tree')">
            <span>🌲</span>
            <span>{{ $t('nav.metricsTree') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/surveys' : '/surveys')">
            <span>📋</span>
            <span>{{ $t('nav.surveys') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/new/chat')">
            <span>💬</span>
            <span>{{ $t('nav.communityChat') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose('/new/tests')">
            <span>🧪</span>
            <span>{{ $t('nav.tests') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/maturity' : '/maturity/create')">
            <span>🔗</span>
            <span>{{ $t('nav.maturityLink') }}</span>
          </button>
          <button class="mobile-menu-btn" @click="navigateAndClose(isNewUi ? '/new/project-card' : '/project-card')">
            <span>📑</span>
            <span>{{ $t('nav.projectCard') }}</span>
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

    <!-- Floating chat FAB -->
    <button
      v-if="isAuthenticated"
      class="chat-fab"
      :class="{ 'chat-fab--pulse': unreadCount > 0 }"
      :aria-label="$t('nav.communityChat')"
      @click="$router.push('/new/chat')"
    >
      💬
      <span v-if="unreadCount > 0" class="chat-fab__badge">{{ unreadCount > 9 ? '9+' : unreadCount }}</span>
    </button>

    <!-- Toast notification -->
    <transition name="toast-slide">
      <div
        v-if="toast"
        class="chat-toast"
        @click="goToChat"
      >
        <span class="chat-toast__icon">💬</span>
        <div class="chat-toast__body">
          <strong class="chat-toast__sender">{{ toast.sender }}</strong>
          <p class="chat-toast__text">{{ toast.text }}</p>
        </div>
        <button type="button" class="chat-toast__close" @click.stop="toast = null">×</button>
      </div>
    </transition>

<div v-if="showTeamModal" class="modal-overlay" @click.self="showTeamModal = false">
  <div class="modal">
    <button class="modal-close-top" :aria-label="$t('common.close')" @click="showTeamModal = false">✕</button>
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
import { computed, ref, watch, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import { io } from "socket.io-client";

function parseJwtPayload(token) {
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    let b64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4;
    if (pad) b64 += "=".repeat(4 - pad);
    return JSON.parse(atob(b64));
  } catch (_e) {
    return null;
  }
}

function playNotificationSound() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, ctx.currentTime);
    osc.frequency.setValueAtTime(1046, ctx.currentTime + 0.08);
    gain.gain.setValueAtTime(0.18, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);
    osc.start(ctx.currentTime);
    osc.stop(ctx.currentTime + 0.3);
  } catch (_e) {
    /* Web Audio not available */
  }
}

export default {
  setup() {
    const authStore = useAuthStore();
    const route = useRoute();
    const router = useRouter();
    const { locale } = useI18n();

    const isAuthenticated = computed(() => authStore.isAuthenticated);
    const isNewUi = computed(() => (route.path || "").startsWith("/new"));

    const showTeamModal = ref(false);
    const newTeamName = ref("");
    const showMobileMenu = ref(false);

    const toast = ref(null);
    const unreadCount = ref(0);
    let toastTimer = null;
    let globalSocket = null;
    let myUserId = null;

    function connectGlobalChat() {
      const token = localStorage.getItem("token");
      if (!token) return;
      if (globalSocket?.connected) return;
      if (globalSocket) { globalSocket.disconnect(); globalSocket = null; }
      const payload = parseJwtPayload(token);
      myUserId = payload?.sub ? parseInt(String(payload.sub), 10) : null;
      globalSocket = io(`${window.location.origin}/community`, {
        auth: { token },
        path: "/socket.io",
        transports: ["websocket", "polling"],
      });
      globalSocket.on("dm_new", (msg) => {
        if (!msg || msg.sender_id === myUserId) return;
        const onChatPage = route.path === "/new/chat" || route.path === "/chat";
        if (!onChatPage) {
          unreadCount.value++;
        }
        toast.value = {
          sender: msg.sender_name || `User #${msg.sender_id}`,
          text: (msg.body || "").slice(0, 100),
          peerId: msg.sender_id,
        };
        playNotificationSound();
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => { toast.value = null; }, 5000);
      });
    }

    function disconnectGlobalChat() {
      if (globalSocket) { globalSocket.disconnect(); globalSocket = null; }
    }

    watch(isAuthenticated, (val) => {
      if (val) connectGlobalChat();
      else disconnectGlobalChat();
    }, { immediate: true });

    watch(() => route.path, (p) => {
      if (p === "/new/chat" || p === "/chat") {
        unreadCount.value = 0;
      }
    });

    onBeforeUnmount(() => {
      disconnectGlobalChat();
      clearTimeout(toastTimer);
    });

    const goToChat = () => {
      toast.value = null;
      unreadCount.value = 0;
      router.push("/new/chat");
    };

    // ✅ Функция выхода
    const logout = () => {
      authStore.logout();
      showTeamModal.value = false;
      router.push("/login");
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
      router.push(route);
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
      isNewUi,
      showTeamModal, 
      newTeamName, 
      showMobileMenu,
      toast,
      unreadCount,
      goToChat,
      logout, 
      createTeam,
      navigateAndClose,
      openTeamModalAndClose,
      openExternalLink,
      openExternalLinkAndClose,
      switchLanguage(lang) {
        locale.value = lang;
        localStorage.setItem("language", lang);
      },
    };
  },
};

</script>


<style>
/* Основной контейнер */

.app--new .modern-sidebar {
  background: rgba(247, 249, 255, 0.82) !important;
  border-right: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 2px 0 18px rgba(10, 20, 45, 0.08);
}

.app--new .modern-sidebar .lang-btn {
  border-color: rgba(10, 20, 45, 0.14);
  color: rgba(10, 20, 45, 0.78);
  background: rgba(255, 255, 255, 0.8);
}

.app--new .modern-sidebar .lang-btn.active {
  border-color: rgba(32, 90, 255, 0.32);
  background: rgba(32, 90, 255, 0.1);
}

.app--new .modern-sidebar .sidebar-btn {
  color: rgba(10, 20, 45, 0.86);
}

.app--new .modern-sidebar .sidebar-btn.logout {
  color: rgba(220, 40, 70, 0.75);
}

.app--new .main-content,
.app--new .results-container {
  background: transparent;
}

.modern-sidebar {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 132px;
  box-sizing: border-box;
  padding: 0 5px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  display: flex;
  flex-direction: column;
  align-items: stretch;
  box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
  z-index: 1000;
  overflow-x: hidden;
  overflow-y: hidden;
}

.modern-sidebar .language-switcher {
  flex-shrink: 0;
  padding: 20px 0 15px 0;
  display: flex;
  justify-content: center;
}

.modern-sidebar .sidebar-buttons-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
  padding: 0 0 15px 0;
  box-sizing: border-box;
}

.modern-sidebar .sidebar-btn.logout {
  flex-shrink: 0;
  margin-top: auto;
  padding-bottom: 20px;
}

/* Стили для скроллбара в sidebar */
.modern-sidebar .sidebar-buttons-container::-webkit-scrollbar {
  width: 4px;
}

.modern-sidebar .sidebar-buttons-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
}

.modern-sidebar .sidebar-buttons-container::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
}

.modern-sidebar .sidebar-buttons-container::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5);
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
  font-size: 19px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  transition: transform 0.2s ease;
  width: 100%;
  max-width: 100%;
  box-sizing: border-box;
}

.sidebar-btn small {
  font-size: 10px;
  line-height: 1.2;
  text-align: center;
  width: 100%;
  max-width: 100%;
  white-space: normal;
  overflow-wrap: anywhere;
  word-break: break-word;
}

.sidebar-btn:hover {
  transform: translateY(-1px);
}

.sidebar-btn.logout {
  color: #ffcccc;
}
.main-content, .results-container {
  margin-left: 132px;
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
  position: relative;
  border: 1px solid rgba(10, 20, 45, 0.1);
  box-shadow: 0 22px 60px rgba(10, 20, 45, 0.24);
}

.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.82);
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-close-top:hover {
  background: rgba(10, 20, 45, 0.14);
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

.sidebar-btn:focus-visible,
.lang-btn:focus-visible,
.lang-btn-mobile:focus-visible,
.mobile-menu-btn:focus-visible,
.mobile-menu-close:focus-visible,
.mobile-hamburger:focus-visible {
  outline: 3px solid rgba(32, 90, 255, 0.55);
  outline-offset: 2px;
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

/* Floating Chat FAB */
.chat-fab {
  position: fixed;
  bottom: 28px;
  right: 28px;
  z-index: 900;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: none;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.8));
  color: #fff;
  font-size: 26px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 24px rgba(32, 90, 255, 0.3);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  padding: 0;
  line-height: 1;
}

.chat-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 8px 32px rgba(32, 90, 255, 0.4);
}

.chat-fab--pulse {
  animation: fab-pulse 2s ease-in-out infinite;
}

@keyframes fab-pulse {
  0%, 100% { box-shadow: 0 6px 24px rgba(32, 90, 255, 0.3); }
  50% { box-shadow: 0 6px 32px rgba(32, 90, 255, 0.55), 0 0 0 8px rgba(32, 90, 255, 0.1); }
}

.chat-fab__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 20px;
  height: 20px;
  border-radius: 10px;
  background: #ef4444;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 5px;
  box-shadow: 0 2px 6px rgba(239, 68, 68, 0.4);
  line-height: 1;
}

/* Toast notification */
.chat-toast {
  position: fixed;
  top: 24px;
  right: 24px;
  z-index: 10000;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  max-width: 380px;
  padding: 14px 16px;
  background: #fff;
  border: 1px solid rgba(32, 90, 255, 0.18);
  border-radius: 14px;
  box-shadow: 0 12px 40px rgba(10, 20, 45, 0.16);
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.chat-toast:hover {
  border-color: rgba(32, 90, 255, 0.35);
}

.chat-toast__icon {
  font-size: 28px;
  flex-shrink: 0;
  line-height: 1;
}

.chat-toast__body {
  flex: 1;
  min-width: 0;
}

.chat-toast__sender {
  display: block;
  font-size: 14px;
  font-weight: 700;
  color: rgba(10, 20, 45, 0.88);
  margin-bottom: 3px;
}

.chat-toast__text {
  margin: 0;
  font-size: 13px;
  line-height: 1.4;
  color: rgba(10, 20, 45, 0.6);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.chat-toast__close {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border: none;
  background: rgba(10, 20, 45, 0.06);
  border-radius: 8px;
  font-size: 18px;
  color: rgba(10, 20, 45, 0.4);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  line-height: 1;
}

.chat-toast__close:hover {
  background: rgba(10, 20, 45, 0.12);
  color: rgba(10, 20, 45, 0.7);
}

.toast-slide-enter-active {
  animation: toast-in 0.35s ease-out;
}

.toast-slide-leave-active {
  animation: toast-out 0.25s ease-in forwards;
}

@keyframes toast-in {
  from { opacity: 0; transform: translateX(80px) scale(0.9); }
  to { opacity: 1; transform: translateX(0) scale(1); }
}

@keyframes toast-out {
  from { opacity: 1; transform: translateX(0) scale(1); }
  to { opacity: 0; transform: translateX(80px) scale(0.9); }
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

  .chat-fab {
    bottom: 18px;
    right: 18px;
    width: 50px;
    height: 50px;
    font-size: 22px;
  }

  .chat-toast {
    top: auto;
    bottom: 80px;
    right: 12px;
    left: 12px;
    max-width: none;
  }
}
</style>
