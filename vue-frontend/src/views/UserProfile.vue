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
<style scoped>
.profile-page {
  max-width: 800px;
  margin: 40px auto;
  padding: 30px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 15px 40px rgba(0, 0, 0, 0.05);
  font-family: "Segoe UI", sans-serif;
}

.profile-page h1 {
  text-align: center;
  font-size: 28px;
  margin-bottom: 30px;
  color: #2c3e50;
  font-weight: 800;
}

.profile-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.form-section {
  padding: 10px 20px;
  border-left: 4px solid #8e44ad;
  background: #fafafa;
  border-radius: 8px;
}

.form-section h2 {
  font-size: 20px;
  color: #2c3e50;
  margin-bottom: 20px;
}

label {
  font-weight: 600;
  margin-top: 12px;
  display: block;
  color: #34495e;
}

input {
  width: 100%;
  padding: 12px;
  margin-top: 6px;
  margin-bottom: 14px;
  border: 1px solid #ccc;
  border-radius: 8px;
  font-size: 15px;
  transition: border-color 0.3s;
}

input:focus {
  outline: none;
  border-color: #8e44ad;
  box-shadow: 0 0 0 2px rgba(142, 68, 173, 0.2);
}

hr {
  border: none;
  border-top: 1px solid #ddd;
  margin: 30px 0;
}

.modern-button {
  display: inline-block;
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.3s, transform 0.2s;
}

.modern-button.purple {
  background: linear-gradient(90deg, #8e44ad, #9b59b6);
  color: white;
  box-shadow: 0 4px 14px rgba(142, 68, 173, 0.2);
}

.modern-button.purple:hover {
  background: linear-gradient(90deg, #732d91, #884ea0);
  transform: scale(1.03);
}
</style>