<template>
  <div class="profile-page">
    <h1>👤 Мой профиль</h1>

    <form @submit.prevent="saveProfile" class="profile-form">
      <div class="form-section">
        <h2>📌 Общая информация</h2>

        <label>Имя</label>
        <input v-model="profile.name" placeholder="Ваше имя" />

        <label>Должность</label>
        <input v-model="profile.position" placeholder="Например, Тимлид" />

        <label>Компания</label>
        <input v-model="profile.company" placeholder="Название компании" />

        <label>Тип личности</label>
        <input v-model="profile.personality_type" placeholder="MBTI / DISC / другое" />
      </div>

      <hr />

      <div class="form-section">
        <h2>🔐 Смена email и пароля</h2>

        <label>Email</label>
        <input v-model="profile.email" type="email" />

        <label>Старый пароль</label>
        <input v-model="oldPassword" type="password" />

        <label>Новый пароль</label>
        <input v-model="newPassword" type="password" />
      </div>

      <button type="submit" class="modern-button purple">💾 Сохранить изменения</button>
    </form>
  </div>
</template>
<script>
import axios from "axios";

export default {
  name: "UserProfile",
  data() {
    return {
      profile: {
        name: "",
        position: "",
        company: "",
        personality_type: "",
        email: ""
      },
      oldPassword: "",
      newPassword: ""
    };
  },
  async mounted() {
    try {
      const res = await axios.get("/user_profile", {
        headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      });
      this.profile = res.data;
    } catch (e) {
      console.error("Ошибка загрузки профиля:", e);
      alert("❌ Не удалось загрузить профиль.");
    }
  },
  methods: {
    async saveProfile() {
      try {
        await axios.post("/update_profile", {
          ...this.profile,
          old_password: this.oldPassword,
          new_password: this.newPassword
        }, {
          headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
        });

        alert("✅ Профиль обновлен!");
        this.oldPassword = "";
        this.newPassword = "";
      } catch (e) {
        console.error("Ошибка сохранения:", e);
        alert("❌ Не удалось сохранить профиль.");
      }
    }
  }
};
</script>
<style>
.profile-page {
  max-width: 800px;
  margin: auto;
  padding: 30px;
  background: #ffffff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.05);
  font-family: "Arial", sans-serif;
}

.profile-page h1 {
  font-size: 28px;
  margin-bottom: 24px;
  text-align: center;
  color: #2c3e50;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-section {
  margin-bottom: 20px;
}

label {
  font-weight: bold;
  display: block;
  margin: 10px 0 4px;
}

input {
  padding: 12px;
  width: 100%;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 16px;
  transition: 0.2s ease;
}

input:focus {
  border-color: #8e44ad;
  outline: none;
}

hr {
  border: none;
  height: 1px;
  background: #ddd;
  margin: 20px 0;
}

button.modern-button.purple {
  align-self: center;
  padding: 12px 24px;
  font-size: 16px;
}
</style>