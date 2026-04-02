<template>
  <div class="community-chat-page">
    <h1>{{ $t('chat.title') }}</h1>
    <p class="chat-hint">{{ $t('chat.hint') }}</p>

    <div class="chat-resolve-row">
      <input
        v-model="emailInput"
        type="email"
        autocomplete="email"
        class="modern-input chat-email-input"
        :placeholder="$t('chat.emailPlaceholder')"
        @keydown.enter.prevent="resolvePeer"
      />
      <button
        type="button"
        class="community-chat__btn"
        :disabled="resolveLoading"
        @click="resolvePeer"
      >
        {{ $t('chat.openChat') }}
      </button>
    </div>
    <p v-if="resolveError" class="chat-error" role="alert">{{ resolveError }}</p>

    <section v-if="contacts.length" class="chat-friends" aria-labelledby="chat-friends-heading">
      <h2 id="chat-friends-heading" class="chat-friends__title">{{ $t('chat.friendsTitle') }}</h2>
      <ul class="chat-friends__list" role="list">
        <li v-for="c in contacts" :key="c.id" class="chat-friends__item">
          <button
            type="button"
            class="chat-friends__peer"
            :class="{ 'chat-friends__peer--active': peer && peer.id === c.id }"
            @click="selectContact(c)"
          >
            <span
              class="chat-friends__dot"
              :class="{
                'chat-friends__dot--on': presenceById[c.id],
                'chat-friends__dot--off': !presenceById[c.id],
              }"
              aria-hidden="true"
            />
            <span class="chat-friends__peer-text">
              <span class="chat-friends__name">{{ contactDisplayName(c) }}</span>
              <span class="chat-friends__email">{{ c.username }}</span>
            </span>
          </button>
          <button
            type="button"
            class="community-chat__remove"
            :title="$t('chat.removeContact')"
            :aria-label="$t('chat.removeContact')"
            @click.stop="removeContact(c)"
          >
            ×
          </button>
        </li>
      </ul>
    </section>

    <div v-if="peer" class="chat-panel">
      <div class="chat-header">
        <div class="chat-header__who">
          <strong>{{ peerDisplayName }}</strong>
          <span class="chat-header__email">{{ peer.username }}</span>
        </div>
        <span
          class="chat-presence"
          :class="{ 'chat-presence--on': activePeerOnline, 'chat-presence--off': !activePeerOnline }"
        >
          {{ activePeerOnline ? $t('chat.online') : $t('chat.offline') }}
        </span>
      </div>

      <div ref="logEl" class="chat-log">
        <div
          v-for="m in messages"
          :key="m.id"
          class="chat-bubble"
          :class="{ 'chat-bubble--mine': m.mine }"
        >
          <div class="chat-bubble__body">{{ m.body }}</div>
          <div class="chat-bubble__meta">{{ formatTime(m.created_at) }}</div>
        </div>
        <p v-if="!messages.length" class="chat-empty">{{ $t('chat.noMessages') }}</p>
      </div>

      <div class="chat-compose">
        <textarea
          v-model="draft"
          class="modern-input chat-textarea"
          rows="3"
          :placeholder="$t('chat.messagePlaceholder')"
          @keydown.enter.exact.prevent="send"
        />
        <button
          type="button"
          class="community-chat__btn community-chat__btn--send"
          :disabled="sendLoading || !draft.trim()"
          @click="send"
        >
          {{ $t('chat.send') }}
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
import { io } from "socket.io-client";

function parseJwtSub(token) {
  try {
    const part = token.split(".")[1];
    if (!part) return null;
    let b64 = part.replace(/-/g, "+").replace(/_/g, "/");
    const pad = b64.length % 4;
    if (pad) b64 += "=".repeat(4 - pad);
    const payload = JSON.parse(atob(b64));
    const sub = payload.sub;
    return sub != null ? parseInt(String(sub), 10) : null;
  } catch (_e) {
    return null;
  }
}

export default {
  name: "CommunityChat",
  data() {
    return {
      emailInput: "",
      resolveLoading: false,
      resolveError: "",
      peer: null,
      messages: [],
      draft: "",
      sendLoading: false,
      socket: null,
      presenceById: {},
      contacts: [],
      myUserId: null,
    };
  },
  computed: {
    peerDisplayName() {
      if (!this.peer) return "";
      return (this.peer.name && this.peer.name.trim()) || this.peer.username;
    },
    activePeerOnline() {
      if (!this.peer) return false;
      return !!this.presenceById[this.peer.id];
    },
  },
  watch: {
    messages() {
      this.$nextTick(() => this.scrollLog());
    },
  },
  mounted() {
    const token = localStorage.getItem("token");
    this.myUserId = token ? parseJwtSub(token) : null;
    this.connectSocket();
    this.fetchContacts();
  },
  beforeUnmount() {
    this.unwatchAllContacts();
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  },
  methods: {
    authHeaders() {
      const token = localStorage.getItem("token");
      return { Authorization: `Bearer ${token}` };
    },
    connectSocket() {
      const token = localStorage.getItem("token");
      if (!token) return;
      if (this.socket?.connected) return;
      if (this.socket) {
        this.socket.disconnect();
        this.socket = null;
      }
      this.socket = io(`${window.location.origin}/community`, {
        auth: { token },
        path: "/socket.io",
        transports: ["websocket", "polling"],
      });
      this.socket.on("peer_presence", (data) => {
        if (data == null || data.peer_id == null) return;
        this.presenceById = {
          ...this.presenceById,
          [data.peer_id]: !!data.online,
        };
      });
      this.socket.on("dm_new", (msg) => {
        if (!this.peer || !this.myUserId) return;
        const involves =
          (msg.sender_id === this.peer.id && msg.recipient_id === this.myUserId) ||
          (msg.sender_id === this.myUserId && msg.recipient_id === this.peer.id);
        if (!involves) return;
        if (this.messages.some((x) => x.id === msg.id)) return;
        this.messages.push({
          ...msg,
          mine: msg.sender_id === this.myUserId,
        });
      });
      this.socket.on("connect", () => {
        this.syncContactWatches();
      });
      this.socket.on("chat_contacts_changed", () => {
        this.fetchContacts();
      });
    },
    contactDisplayName(c) {
      return (c.name && String(c.name).trim()) || c.username;
    },
    syncContactWatches() {
      if (!this.socket?.connected || !this.myUserId) return;
      for (const c of this.contacts) {
        if (c.id === this.myUserId) continue;
        this.socket.emit("watch_presence", { peer_id: c.id });
      }
    },
    unwatchAllContacts() {
      if (!this.socket?.connected) return;
      for (const c of this.contacts) {
        if (c.id === this.myUserId) continue;
        this.socket.emit("unwatch_presence", { peer_id: c.id });
      }
    },
    async fetchContacts() {
      try {
        const { data } = await axios.get("/api/chat/contacts", {
          headers: this.authHeaders(),
        });
        this.contacts = data.contacts || [];
        this.$nextTick(() => this.syncContactWatches());
      } catch (_e) {
        this.contacts = [];
      }
    },
    async selectContact(c) {
      this.resolveError = "";
      this.peer = { id: c.id, name: c.name || "", username: c.username };
      await this.loadMessages();
      if (this.socket?.connected) {
        this.socket.emit("watch_presence", { peer_id: c.id });
      }
    },
    async removeContact(c) {
      try {
        await axios.delete(`/api/chat/contacts/${c.id}`, {
          headers: this.authHeaders(),
        });
        if (this.socket?.connected) {
          this.socket.emit("unwatch_presence", { peer_id: c.id });
        }
        const next = { ...this.presenceById };
        delete next[c.id];
        this.presenceById = next;
        if (this.peer && this.peer.id === c.id) {
          this.peer = null;
          this.messages = [];
        }
        await this.fetchContacts();
      } catch {
        /* ignore */
      }
    },
    scrollLog() {
      const el = this.$refs.logEl;
      if (el) el.scrollTop = el.scrollHeight;
    },
    formatTime(iso) {
      if (!iso) return "";
      try {
        const d = new Date(iso);
        return d.toLocaleString(this.$i18n.locale === "en" ? "en-GB" : "ru-RU", {
          day: "2-digit",
          month: "2-digit",
          hour: "2-digit",
          minute: "2-digit",
        });
      } catch (_e) {
        return iso;
      }
    },
    async resolvePeer() {
      this.resolveError = "";
      const email = (this.emailInput || "").trim();
      if (!email || !email.includes("@")) {
        this.resolveError = this.$t("chat.errorInvalidEmail");
        return;
      }
      this.resolveLoading = true;
      try {
        this.connectSocket();
        const { data } = await axios.post(
          "/api/chat/resolve",
          { email },
          { headers: this.authHeaders() }
        );
        if (data.error === "self") {
          this.resolveError = this.$t("chat.errorSelf");
          return;
        }
        if (!data.found) {
          this.resolveError = this.$t("chat.userNotFound");
          this.peer = null;
          this.messages = [];
          return;
        }
        await this.fetchContacts();
        this.peer = data.user;
        await this.loadMessages();
        if (this.socket?.connected) {
          this.socket.emit("watch_presence", { peer_id: this.peer.id });
        }
      } catch (e) {
        this.resolveError =
          e.response?.data?.error || e.message || this.$t("chat.errorGeneric");
      } finally {
        this.resolveLoading = false;
      }
    },
    async loadMessages() {
      if (!this.peer) return;
      try {
        const { data } = await axios.get(`/api/chat/messages/${this.peer.id}`, {
          headers: this.authHeaders(),
          params: { limit: 100 },
        });
        const list = data.messages || [];
        this.messages = list.map((m) => ({
          ...m,
          mine: m.mine != null ? m.mine : m.sender_id === this.myUserId,
        }));
      } catch (_e) {
        this.messages = [];
      }
    },
    async send() {
      const text = (this.draft || "").trim();
      if (!text || !this.peer) return;
      this.sendLoading = true;
      try {
        await axios.post(
          "/api/chat/send",
          { recipient_id: this.peer.id, body: text },
          { headers: this.authHeaders() }
        );
        this.draft = "";
      } catch (e) {
        this.resolveError =
          e.response?.data?.error || e.message || this.$t("chat.errorSend");
      } finally {
        this.sendLoading = false;
      }
    },
  },
};
</script>

<style scoped>
.community-chat-page {
  max-width: 640px;
  margin: 0 auto 48px;
  padding: 24px 18px 40px;
}

.community-chat-page h1 {
  font-size: 1.5rem;
  font-weight: 750;
  letter-spacing: -0.02em;
  color: rgba(10, 20, 45, 0.92);
  margin: 0 0 10px;
}

.chat-hint {
  margin: 0 0 20px;
  font-size: 14px;
  line-height: 1.45;
  color: rgba(10, 20, 45, 0.55);
  text-align: left;
}

.chat-resolve-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: stretch;
}

.chat-email-input {
  flex: 1 1 220px;
  min-width: 0;
}

.modern-input {
  border-radius: 12px;
  border: 1px solid rgba(10, 20, 45, 0.12);
  padding: 12px 14px;
  font-size: 15px;
  width: 100%;
  box-sizing: border-box;
}

.modern-input:focus {
  outline: none;
  border-color: rgba(32, 90, 255, 0.45);
  box-shadow: 0 0 0 3px rgba(32, 90, 255, 0.12);
}

.community-chat__btn {
  flex: 0 0 auto;
  padding: 12px 18px;
  border-radius: 12px;
  border: 1px solid rgba(32, 90, 255, 0.35);
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.92), rgba(0, 194, 255, 0.75));
  color: #fff;
  font-weight: 650;
  font-size: 15px;
  cursor: pointer;
  min-height: 44px;
}

.community-chat__btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.chat-error {
  margin: 12px 0 0;
  font-size: 14px;
  color: #b91c1c;
  text-align: left;
}

.chat-panel {
  margin-top: 24px;
  border-radius: 16px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 12px 40px rgba(10, 20, 45, 0.08);
  overflow: hidden;
}

.chat-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(248, 250, 255, 0.9);
}

.chat-header__who {
  display: flex;
  flex-direction: column;
  gap: 4px;
  text-align: left;
  min-width: 0;
}

.chat-header__who strong {
  font-size: 16px;
  color: rgba(10, 20, 45, 0.9);
}

.chat-header__email {
  font-size: 13px;
  color: rgba(10, 20, 45, 0.45);
  overflow-wrap: anywhere;
}

.chat-presence {
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  padding: 6px 10px;
  border-radius: 999px;
}

.chat-presence--on {
  background: rgba(34, 197, 94, 0.15);
  color: #15803d;
}

.chat-presence--off {
  background: rgba(10, 20, 45, 0.06);
  color: rgba(10, 20, 45, 0.45);
}

.chat-log {
  min-height: 220px;
  max-height: 420px;
  overflow-y: auto;
  padding: 14px 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(246, 249, 255, 0.5);
}

.chat-empty {
  margin: auto;
  font-size: 14px;
  color: rgba(10, 20, 45, 0.4);
}

.chat-bubble {
  align-self: flex-start;
  max-width: 88%;
  padding: 10px 12px;
  border-radius: 14px 14px 14px 4px;
  background: #fff;
  border: 1px solid rgba(10, 20, 45, 0.08);
  box-shadow: 0 2px 8px rgba(10, 20, 45, 0.04);
  text-align: left;
}

.chat-bubble--mine {
  align-self: flex-end;
  border-radius: 14px 14px 4px 14px;
  background: linear-gradient(135deg, rgba(32, 90, 255, 0.12), rgba(0, 194, 255, 0.08));
  border-color: rgba(32, 90, 255, 0.2);
}

.chat-bubble__body {
  font-size: 15px;
  line-height: 1.45;
  color: rgba(10, 20, 45, 0.9);
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.chat-bubble__meta {
  margin-top: 6px;
  font-size: 11px;
  color: rgba(10, 20, 45, 0.38);
}

.chat-compose {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 12px 16px;
  border-top: 1px solid rgba(10, 20, 45, 0.08);
  background: #fff;
}

.chat-textarea {
  resize: vertical;
  min-height: 72px;
  font-family: inherit;
}

.community-chat__btn--send {
  align-self: flex-end;
}

.chat-friends {
  margin-top: 22px;
  text-align: left;
}

.chat-friends__title {
  margin: 0 0 10px;
  font-size: 0.95rem;
  font-weight: 700;
  color: rgba(10, 20, 45, 0.72);
}

.chat-friends__list {
  list-style: none;
  margin: 0;
  padding: 0;
  border-radius: 14px;
  border: 1px solid rgba(10, 20, 45, 0.1);
  background: rgba(248, 250, 255, 0.65);
  overflow: hidden;
}

.chat-friends__item {
  display: flex;
  align-items: stretch;
  border-bottom: 1px solid rgba(10, 20, 45, 0.06);
}

.chat-friends__item:last-child {
  border-bottom: none;
}

.chat-friends__peer {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 10px 12px 14px;
  border: none;
  background: transparent;
  cursor: pointer;
  text-align: left;
  font: inherit;
  color: inherit;
  transition: background 0.15s ease;
}

.chat-friends__peer:hover {
  background: rgba(32, 90, 255, 0.06);
}

.chat-friends__peer--active {
  background: rgba(32, 90, 255, 0.1);
}

.chat-friends__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.chat-friends__dot--on {
  background: #22c55e;
  box-shadow: 0 0 0 2px rgba(34, 197, 94, 0.25);
}

.chat-friends__dot--off {
  background: rgba(10, 20, 45, 0.18);
}

.chat-friends__peer-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.chat-friends__name {
  font-weight: 650;
  font-size: 15px;
  color: rgba(10, 20, 45, 0.9);
}

.chat-friends__email {
  font-size: 12px;
  color: rgba(10, 20, 45, 0.45);
  overflow-wrap: anywhere;
}

.community-chat__remove {
  flex-shrink: 0;
  width: 44px;
  min-height: 44px;
  border: none;
  background: transparent;
  color: rgba(10, 20, 45, 0.35);
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  border-left: 1px solid rgba(10, 20, 45, 0.06);
  transition: color 0.15s ease, background 0.15s ease;
}

.community-chat__remove:hover {
  color: #b91c1c;
  background: rgba(220, 38, 38, 0.06);
}
</style>
