<template>
  <div class="motivation-container">
    <h1>{{ $t('motivation.title') }}</h1>

    <!-- 🔹 Список сотрудников -->
    <div class="employee-list">
      <div
        v-for="employee in employees"
        :key="employee.id"
        class="employee-card"
        @click="selectEmployee(employee)"
      >
        <img
          class="avatar"
          :src="getAvatarUrl(employee)"
          alt="avatar"
          @click="openAvatarModal(employee)"
          @error="setDefaultAvatar"
        />
        <div class="card-header">
          <h4 class="employee-name">{{ employee.name }}</h4>
          <button class="delete-btn" @click.stop="deleteEmployee(employee.id)">🗑</button>

        </div>
        <p class="team-name">🏢 {{ $t('motivation.teamLabel') }}: <strong>{{ getTeamName(employee.team_id) || '—' }}</strong></p>
        <p class="disc-type-full">🧠 {{ $t('motivation.discTypeLabel') }}: <strong>{{ extractDISCFullType(employee.ai_analysis) }}</strong></p>
        <div class="employee-card-footer">
    <button class="update-btn" @click="handleEmployeeClick(employee)">
      🔄 {{ $t('motivation.updateRecommendations') }}
    </button>
  </div>

        <div v-if="employee.ai_analysis" class="factors">
          <div class="column">
            <h5>⬆️ {{ $t('motivation.motivatorsTitle') }}</h5>
            <ul>
              <li v-for="item in employee.motivators" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div class="column">
            <h5>⬇️ {{ $t('motivation.demotivatorsTitle') }}</h5>
            <ul>
              <li v-for="item in employee.demotivators" :key="item">{{ item }}</li>
            </ul>
          </div>

        </div>

    <div v-if="employee.ai_analysis" class="manager-tips-block" v-html="extractManagerTips(employee.ai_analysis)"></div>

<div class="form-footer">

</div>

      </div>

      <div class="employee-card add-card" @click="resetForm">
        <span>➕</span>
        <p>{{ $t('motivation.addEmployee') }}</p>
      </div>
    </div>

    <!-- 🔹 Форма -->


    <!-- 🔹 Результат -->

  </div>
  <div v-if="showModal" class="modal-overlay">
  <div class="modal-content motivation-modal-iceberg">
    <button type="button" class="modal-close-top" @click="showModal = false" :aria-label="$t('common.close')">✕</button>

    <header class="mot-iceberg-hero">
      <h2 class="mot-iceberg-title">{{ $t('motivation.icebergModalTitle') }}</h2>
      <p class="mot-iceberg-lead">{{ $t('motivation.icebergModalLead') }}</p>
    </header>

    <form @submit.prevent="submitMotivation(false)" class="form-group modern-form mot-iceberg-form">

      <section class="mot-iceberg-tier mot-iceberg-tier--identity">
        <h3 class="mot-iceberg-tier-title">{{ $t('motivation.tierContext') }}</h3>
        <div class="input-wrapper">
          <span class="input-icon">👤</span>
          <input
            v-model="form.name"
            required
            class="modern-input"
            :class="{ 'has-value': form.name }"
          />
          <label class="floating-label">{{ $t('motivation.employeeName') }}</label>
        </div>

        <div class="input-wrapper">
          <span class="input-icon">💼</span>
          <input
            v-model="form.role"
            required
            class="modern-input"
            :class="{ 'has-value': form.role }"
          />
          <label class="floating-label">{{ $t('motivation.role') }}</label>
        </div>

        <div class="input-wrapper">
          <span class="input-icon">🏢</span>
          <select
            v-model="form.team_id"
            class="modern-input modern-select"
            :class="{ 'has-value': form.team_id }"
          >
            <option value=""></option>
            <option v-for="team in teams" :key="team.id" :value="team.id">
              {{ team.name }}
            </option>
          </select>
          <label class="floating-label">{{ $t('motivation.team') }} ({{ $t('common.select') }})</label>
        </div>
      </section>

      <div class="mot-iceberg-waterline" aria-hidden="true" />

      <section class="mot-iceberg-tier mot-iceberg-tier--surface">
        <h3 class="mot-iceberg-tier-title">{{ $t('motivation.tierVisible') }}</h3>
        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">😰</span>
          <textarea
            v-model="form.stress"
            required
            class="modern-input modern-textarea"
            :class="{ 'has-value': form.stress }"
          />
          <label class="floating-label">{{ $t('motivation.fieldStressBehavior') }}</label>
        </div>

        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">🤝</span>
          <textarea
            v-model="form.communication"
            required
            class="modern-input modern-textarea"
            :class="{ 'has-value': form.communication }"
          />
          <label class="floating-label">{{ $t('motivation.fieldInteraction') }}</label>
        </div>
      </section>

      <section class="mot-iceberg-tier mot-iceberg-tier--deep">
        <h3 class="mot-iceberg-tier-title">{{ $t('motivation.tierDeep') }}</h3>
        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">⚡</span>
          <textarea
            v-model="form.behavior"
            required
            class="modern-input modern-textarea"
            :class="{ 'has-value': form.behavior }"
          />
          <label class="floating-label">{{ $t('motivation.fieldWorkStyle') }}</label>
        </div>

        <div class="input-wrapper textarea-wrapper">
          <span class="input-icon">💬</span>
          <textarea
            v-model="form.feedback"
            required
            class="modern-input modern-textarea"
            :class="{ 'has-value': form.feedback }"
          />
          <label class="floating-label">{{ $t('motivation.fieldFeedbackReaction') }}</label>
        </div>
      </section>

      <div class="modal-actions mot-iceberg-actions">
        <button
          type="button"
          @click="submitMotivation(false)"
          :disabled="loading"
        >
          💾 {{ $t('common.save') }}
        </button>
        <button
          type="button"
          @click="submitMotivation(true)"
          :disabled="loading"
        >
          <span v-if="loading">⏳ {{ $t('motivation.generating') }}</span>
          <span v-else>💬 {{ $t('motivation.analyze') }}</span>
        </button>
      </div>
    </form>
  </div>
</div>

<!-- Avatar Selection Modal -->
<div v-if="showAvatarModal" class="modal-overlay">
  <div class="modal-content avatar-modal">
    <button class="modal-close-top" @click="showAvatarModal = false" aria-label="Close">✕</button>
    <h2>🎭 Выбор аватара</h2>
    
    <div class="avatar-section">
      <h3>👨 Мужские</h3>
      <div class="avatar-grid">
        <img 
          v-for="avatar in avatars.male" 
          :key="avatar"
          :src="`/avatars/${avatar}`"
          class="avatar-option"
          @click="selectAvatar(avatar)"
        />
      </div>
    </div>
    
    <div class="avatar-section">
      <h3>👩 {{ $t('motivation.avatarFemale') }}</h3>
      <div class="avatar-grid">
        <img 
          v-for="avatar in avatars.female" 
          :key="avatar"
          :src="`/avatars/${avatar}`"
          class="avatar-option"
          @click="selectAvatar(avatar)"
        />
      </div>
    </div>
    
  </div>
</div>
</template>

<script>
export default {
  data() {
    return {
      form: {
        id: null,
        name: "",
        role: "",
        team_id: "",
        stress: "",
        communication: "",
        behavior: "",
        feedback: ""
      },
      teams: [],
      employees: [],
      result: "",
      loading: false,
      showModal: false,
      showAvatarModal: false,
      selectedEmployee: null,
      avatars: {
        male: ['male1.png', 'male2.png', 'male3.png', 'male4.png', 'male5.png', 'male6.png'],
        female: ['female1.png', 'female2.png', 'female3.png', 'female4.png', 'female5.png', 'female6.png']
      },
      avatar: "default.png"
    };
  },

  watch: {
    '$i18n.locale'() {
      this.employees = this.employees.map((e) => this.enrichEmployee(e));
    }
  },

  async mounted() {
    const token = localStorage.getItem("token");

    try {
      // Получение команд
      const teamRes = await fetch("/user_teams", {
        headers: { Authorization: `Bearer ${token}` }
      });
      this.teams = await teamRes.json();

      // Получение сотрудников
      const empRes = await fetch("/employees", {
        headers: { Authorization: `Bearer ${token}` }
      });

      const rawEmployees = await empRes.json();

      if (!Array.isArray(rawEmployees)) {
        console.error("Сотрудники не получены:", rawEmployees);
        return;
      }

      this.employees = rawEmployees.map((e) => this.enrichEmployee(e));
    } catch (err) {
      console.error("Ошибка при загрузке:", err);
    }
  },

  methods: {
    enrichEmployee(e) {
      return {
        ...e,
        motivators: this.extractFactors(e.ai_analysis, 'motivators'),
        demotivators: this.extractFactors(e.ai_analysis, 'demotivators'),
        managerTips: this.extractManagerTips(e.ai_analysis)
      };
    },

    async submitMotivation(generate = false) {
  this.loading = true;
  const token = localStorage.getItem("token");

  const url = generate ? "/motivation" : "/employees";
  const method = "POST";

  try {
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(
        generate
          ? {
              ...this.form,
              id: this.form.id,
              team_id: this.form.team_id || null,
              lang: this.$i18n.locale === 'en' ? 'en' : 'ru'
            }
          : {
              ...this.form,
              id: this.form.id,
              team_id: this.form.team_id || null
            }
      )
    });

    const data = await res.json();

    if (res.ok) {
      this.result = data.analysis || data.message;
      this.form.id = data.employee_id || data.id;

      const analysis =
        data.analysis !== undefined && data.analysis !== null && String(data.analysis).trim() !== ''
          ? data.analysis
          : (this.form.ai_analysis || '');
      const updated = this.enrichEmployee({
        ...this.form,
        id: this.form.id,
        ai_analysis: analysis
      });

      const index = this.employees.findIndex(e => e.id === this.form.id);
      if (index !== -1) {
        this.employees.splice(index, 1, updated);
      } else {
        this.employees.push(updated);
      }

      this.showModal = false;
      setTimeout(() => {
    location.reload();
  }, 300);
    } else {
      alert(data.error || this.$t('motivation.errorSaving'));
    }
  } catch (err) {
    console.error(err);
    alert(this.$t('motivation.networkError'));
  } finally {
    this.loading = false;
  }
},

    resetForm() {
      this.form = {
        id: null,
        name: "",
        role: "",
        team_id: "",
        stress: "",
        communication: "",
        behavior: "",
        feedback: ""
      };
      this.result = "";
      this.showModal = true;
    },

    async deleteEmployee(id) {
      const token = localStorage.getItem("token");
      if (!confirm(this.$t('motivation.confirmDelete'))) return;

      try {
        await fetch(`/employee/${id}`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` }
        });
        this.employees = this.employees.filter(e => e.id !== id);
      } catch (e) {
        console.error("Ошибка удаления", e);
      }
    },

    handleEmployeeClick(employee) {
      this.selectEmployee(employee);
      this.showModal = true;
    },

    selectEmployee(employee) {
      this.form = { ...employee };
      this.result = employee.ai_analysis;
    },

    extractDISCFullType(aiText) {
      const unknown = this.$t('motivation.discUnknown');
      if (!aiText) return unknown;
      const patterns = [
        /DISC\s+Type:\s*<\/?strong>?[\s"]*([A-ZА-Я][^<]*?\([^)]+\))/i,
        /DISC\s+Type:\s*([A-ZА-Я][^<\n]*?\([^)]+\))/i,
        /Тип\s*DISC:\s*<\/?strong>?[\s"]*([A-ZА-Я][^<]*?\([^)]+\))/i,
        /Тип\s*DISC:\s*([A-ZА-Я][^<\n]*?\([^)]+\))/i
      ];
      for (let i = 0; i < patterns.length; i++) {
        const m = aiText.match(patterns[i]);
        if (m) {
          const s = m[1].replace(/<[^>]+>/g, '').trim();
          if (s) return s;
        }
      }
      return unknown;
    },

    extractFactors(html, kind) {
      if (!html) return [];
      const en = this.$i18n.locale === 'en';
      const motivPrimary = en
        ? ['motivating factor', 'motivating', 'motivator']
        : ['мотивирующ', 'мотиватор'];
      const motivFallback = en
        ? ['мотивирующ', 'мотиватор']
        : ['motivating factor', 'motivating', 'motivator'];
      const demPrimary = en ? ['demotivator'] : ['демотиватор'];
      const demFallback = en ? ['демотиватор'] : ['demotivator'];
      const needleSets =
        kind === 'motivators' ? [motivPrimary, motivFallback] : [demPrimary, demFallback];

      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = html;
      const headers = Array.from(tempDiv.querySelectorAll('h3, h4, strong'));

      const findList = (needles) => {
        const header = headers.find((h) => {
          const t = h.textContent.toLowerCase();
          return needles.some((n) => t.includes(n));
        });
        if (!header) return null;
        let node = header.nextElementSibling;
        while (node && node.tagName !== 'UL') {
          node = node.nextElementSibling;
        }
        if (!node || node.tagName !== 'UL') return null;
        return Array.from(node.querySelectorAll('li')).map((li) => li.textContent.trim());
      };

      for (let i = 0; i < needleSets.length; i++) {
        const list = findList(needleSets[i]);
        if (list && list.length) return list;
      }
      return [];
    },

    extractDISCType(aiText) {
      if (!aiText) return "Неизвестно";

      const match =
        aiText.match(/Тип DISC[:-]?\s*<\/?strong>?[\s"]*([A-ZА-Я][^)<\n:]*\([A-ZА-Я]\))/i) ||
        aiText.match(/тип\s+[A-ZА-Я]\s*\([^)]+\)/i) ||
        aiText.match(/тип\s+["«]?(.)["»]?/i);

      return match ? match[1].trim() : "Неизвестно";
    },

    extractManagerTips(text) {
      if (!text) return '';
      const match = text.match(
        /<h3>(?:Рекомендации для руководителя|Recommendations for manager):.*?<\/ul>/is
      );
      return match ? match[0] : '';
    },

    getTeamName(teamId) {
      const team = this.teams.find(t => t.id === teamId);
      return team ? team.name : "—";
    },

    getAvatarUrl(employee) {
      return `/avatars/${employee.avatar || "default.png"}`;
    },

    openAvatarModal(employee) {
      this.selectedEmployee = employee;
      this.showAvatarModal = true;
    },

    async selectAvatar(avatarFile) {
      if (!this.selectedEmployee) return;
      
      const token = localStorage.getItem("token");
      try {
        const response = await fetch("/employees", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify({
            ...this.selectedEmployee,
            avatar: avatarFile
          })
        });
        
        if (response.ok) {
          const employeeIndex = this.employees.findIndex(e => e.id === this.selectedEmployee.id);
          if (employeeIndex !== -1) {
            this.employees[employeeIndex].avatar = avatarFile;
          }
          this.showAvatarModal = false;
        }
      } catch (error) {
        console.error("Error updating avatar:", error);
      }
    },

    setDefaultAvatar(event) {
      event.target.src = "/avatars/default.png";
    }
  }
};
</script>





<style scoped>
.motivation-container {
  max-width: 1280px;
  margin: 40px auto;
  background: #ffffff;
  padding: 32px;
  border-radius: 20px;
  box-shadow: 0 2px 16px rgba(0, 0, 0, 0.04);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
}

h1 {
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #1a1a1a;
  letter-spacing: -0.5px;
}

form {
  margin-top: 30px;
}

.form-group {
  max-width: 700px;
  margin: 1rem auto;
  padding: 32px;
  background: #ffffff;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
}

input,
textarea,
select {
  padding: 12px 16px;
  font-size: 14px;
  border-radius: 10px;
  border: 1.5px solid #d1d5db;
  font-family: inherit;
  transition: all 0.2s ease;
  background: #ffffff;
}

input:focus,
textarea:focus,
select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

button {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin-top: 10px;
  font-weight: 600;
  font-size: 14px;
  transition: all 0.2s ease;
  font-family: inherit;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

button:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.result-block {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  margin-top: 40px;
  padding: 24px;
  border-radius: 12px;
  border: 1px solid #bae6fd;
}

.employee-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 24px;
  margin-bottom: 32px;
  align-items: start;
}

.employee-card {
  min-height: 100px;
  padding: 24px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.employee-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
  border-color: #d1d5db;
}

.employee-card .avatar {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 50%;
  margin: 0 auto;
  border: 3px solid #f3f4f6;
  transition: all 0.2s ease;
}

.employee-card .avatar:hover {
  transform: scale(1.05);
  border-color: #3b82f6;
}

.employee-card .employee-name {
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #111827;
  margin: 0;
}

.employee-card .team-name,
.employee-card .disc-type-full {
  text-align: center;
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}

.disc-type-full strong {
  color: #374151;
  font-weight: 600;
}

.employee-card .delete-btn {
  position: absolute;
  top: 16px;
  right: 16px;
  background: #ef4444;
  border: none;
  cursor: pointer;
  font-size: 14px;
  color: white;
  padding: 6px 12px;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.employee-card .delete-btn:hover {
  background: #dc2626;
  transform: scale(1.05);
}

.employee-card.add-card {
  min-height: 240px;
  background: linear-gradient(135deg, #f9fafb 0%, #f3f4f6 100%);
  justify-content: center;
  align-items: center;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  border-radius: 16px;
  padding: 2rem;
  border: 2px dashed #d1d5db;
  transition: all 0.2s ease;
}

.employee-card.add-card:hover {
  border-color: #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #3b82f6;
}

.factors {
  display: flex;
  flex-direction: row;
  gap: 16px;
  margin-top: 12px;
}

.factors .column {
  flex: 1;
  min-width: 0;
  background: #f9fafb;
  padding: 16px;
  border-radius: 10px;
  overflow: visible;
  max-height: none;
  border: 1px solid #e5e7eb;
}

.factors h5 {
  margin-bottom: 12px;
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  border-bottom: 2px solid #e5e7eb;
  padding-bottom: 8px;
}

.factors ul {
  padding-left: 20px;
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  list-style: disc;
}

.factors li {
  margin-bottom: 8px;
  line-height: 1.5;
}

.manager-tips-block {
  margin-top: 12px;
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  padding: 16px;
  border-radius: 10px;
  font-size: 13px;
  border: 1px solid #fcd34d;
  color: #92400e;
}

.manager-tips-block ul {
  padding-left: 20px;
  list-style-type: disc;
  margin-top: 8px;
}

.manager-tips-block li {
  margin-bottom: 6px;
  line-height: 1.6;
}

.manager-tips-block h3 {
  margin-bottom: 8px;
  font-size: 14px;
  color: #78350f;
  font-weight: 600;
}

.employee-card-footer {
  margin-top: 12px;
  display: flex;
  justify-content: center;
}

.update-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%);
  color: #fff;
  font-weight: 600;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 14px;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.3);
}

.update-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(139, 92, 246, 0.4);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 20px;
}

.modal-content {
  background: #fff;
  padding: 40px;
  border-radius: 20px;
  width: 100%;
  max-width: 720px;
  max-height: 90vh;
  overflow-y: auto;
  position: relative;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.motivation-modal-iceberg {
  padding: 0;
  max-width: 760px;
  background: linear-gradient(180deg, #f0f9ff 0%, #e0f2fe 28%, #ffffff 55%, #f8fafc 100%);
  border: 1px solid rgba(14, 165, 233, 0.22);
}

.mot-iceberg-hero {
  padding: 28px 40px 18px;
  text-align: left;
  border-bottom: 1px solid rgba(14, 165, 233, 0.22);
  background: linear-gradient(135deg, rgba(224, 242, 254, 0.9) 0%, rgba(255, 255, 255, 0.95) 100%);
}

.motivation-modal-iceberg h2.mot-iceberg-title {
  margin: 0 0 10px;
  font-size: 1.45rem;
  font-weight: 700;
  color: #0c4a6e;
  letter-spacing: -0.02em;
}

.mot-iceberg-lead {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #475569;
}

.mot-iceberg-form.form-group {
  margin: 0;
  padding: 22px 40px 32px;
  background: transparent;
  border: none;
  box-shadow: none;
  max-width: none;
  gap: 0;
}

.mot-iceberg-tier {
  margin-bottom: 18px;
}

.mot-iceberg-tier--identity {
  padding: 4px 0 4px;
}

.mot-iceberg-tier-title {
  margin: 0 0 14px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: #0369a1;
}

.mot-iceberg-tier--surface {
  padding: 16px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.78);
  border: 1px solid rgba(14, 165, 233, 0.22);
  box-shadow: 0 6px 28px rgba(14, 165, 233, 0.1);
}

.mot-iceberg-waterline {
  height: 20px;
  margin: 4px 0 16px;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1440 40' preserveAspectRatio='none'%3E%3Cpath fill='%230ea5e9' fill-opacity='0.28' d='M0 20 C360 4 720 36 1080 20 C1260 12 1380 28 1440 20 V40 H0Z'/%3E%3C/svg%3E")
    center / 100% 100% no-repeat;
  opacity: 0.95;
}

.mot-iceberg-tier--deep {
  padding: 16px 18px;
  border-radius: 14px;
  background: linear-gradient(168deg, #dbeafe 0%, #cffafe 45%, #bae6fd 100%);
  border: 1px solid rgba(2, 132, 199, 0.3);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
}

.mot-iceberg-tier--deep .mot-iceberg-tier-title {
  color: #0c4a6e;
}

.mot-iceberg-actions.modal-actions {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(14, 165, 233, 0.2);
}

.modal-content h2 {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 32px;
  color: #111827;
  letter-spacing: -0.5px;
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
  color: rgba(10, 20, 45, 0.84);
  cursor: pointer;
  font-size: 18px;
  z-index: 2;
}

/* Modern Form Styles with Floating Labels */
.modern-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.input-wrapper {
  position: relative;
  margin-top: 0;
}

.input-wrapper.textarea-wrapper {
  margin-top: 0;
}

.input-icon {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 20px;
  z-index: 2;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.textarea-wrapper .input-icon {
  top: 24px;
  transform: none;
}

.modern-input {
  width: 100%;
  padding: 20px 18px 8px 52px;
  border: 2px solid #e5e7eb;
  border-radius: 14px;
  font-size: 15px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", "Roboto", sans-serif;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(to bottom, #ffffff 0%, #fafbfc 100%);
  box-sizing: border-box;
  color: #111827;
  line-height: 1.5;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.modern-textarea {
  padding-top: 32px;
  min-height: 120px;
  resize: vertical;
  line-height: 1.6;
}

.modern-select {
  padding-right: 52px;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 14 14'%3E%3Cpath fill='%236b7280' d='M7 10L2 5h10z'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 18px center;
}

.floating-label {
  position: absolute;
  left: 52px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 15px;
  color: #9ca3af;
  font-weight: 500;
  pointer-events: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: transparent;
  z-index: 1;
}

.textarea-wrapper .floating-label {
  top: 32px;
  transform: none;
}

.modern-input:focus,
.modern-input.has-value {
  padding-top: 20px;
  padding-bottom: 8px;
  border-color: #3b82f6;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f7ff 100%);
  box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1), 0 4px 12px rgba(59, 130, 246, 0.15), 0 2px 4px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.modern-input:focus + .floating-label,
.modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
  font-size: 12px;
  color: #3b82f6;
  font-weight: 600;
  transform: none;
}

.textarea-wrapper .modern-input:focus + .floating-label,
.textarea-wrapper .modern-input.has-value + .floating-label {
  top: 12px;
  left: 52px;
}

.modern-input:hover:not(:focus) {
  border-color: #cbd5e1;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.08);
  transform: translateY(-1px);
}

.modern-input:focus {
  outline: none;
}

.modern-input:focus ~ .input-icon {
  transform: translateY(-50%) scale(1.1);
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
}

.textarea-wrapper .modern-input:focus ~ .input-icon {
  transform: scale(1.1);
  filter: drop-shadow(0 2px 4px rgba(59, 130, 246, 0.3));
}

/* Кнопки в модальном окне */
.modal-actions {
  margin-top: 32px;
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 12px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.modal-actions button {
  padding: 12px 24px;
  border: none;
  border-radius: 10px;
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
}

.modal-actions button:first-child {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

.modal-actions button:first-child:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
}

.modal-actions button:nth-child(2) {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.modal-actions button:nth-child(2):hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(59, 130, 246, 0.4);
}

.modal-actions .modal-close {
  background: #f3f4f6;
  color: #374151;
  font-size: 20px;
  padding: 10px 16px;
  min-width: 44px;
}

.modal-actions .modal-close:hover {
  background: #e5e7eb;
  color: #111827;
}

.avatar-modal {
  max-width: 600px;
}

.avatar-section {
  margin-bottom: 32px;
}

.avatar-section h3 {
  margin-bottom: 16px;
  color: #111827;
  font-size: 18px;
  font-weight: 600;
}

.avatar-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}

.avatar-option {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  cursor: pointer;
  border: 3px solid transparent;
  transition: all 0.2s ease;
  object-fit: cover;
}

.avatar-option:hover {
  border-color: #3b82f6;
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.employee-card .avatar {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.employee-card .avatar:hover {
  transform: scale(1.05);
}

@media (max-width: 900px) {
  .factors {
    flex-direction: column;
  }
}

@media (max-width: 768px) {
  .motivation-container {
    margin: 20px 10px !important;
    padding: 20px !important;
  }
  
  h1 {
    font-size: 24px;
    margin-bottom: 24px;
  }
  
  .employee-list {
    grid-template-columns: 1fr;
    gap: 16px;
  }
  
  .employee-card {
    padding: 20px;
  }
  
  .factors {
    flex-direction: column;
    gap: 12px;
  }
  
  .modal-content {
    width: 100% !important;
    max-width: 100% !important;
    padding: 24px 20px !important;
    margin: 0 !important;
    border-radius: 16px 16px 0 0;
  }

  .motivation-modal-iceberg {
    padding: 0 !important;
  }

  .mot-iceberg-hero {
    padding: 20px 20px 16px !important;
  }

  .mot-iceberg-form.form-group {
    padding: 18px 20px 24px !important;
  }
  
  .modal-content h2 {
    font-size: 22px;
    margin-bottom: 24px;
  }
  
  .modal-content textarea,
  .modal-content select,
  .modal-content input {
    width: 100% !important;
    font-size: 16px !important;
  }
  
  .modal-actions {
    flex-direction: column !important;
    gap: 10px !important;
  }
  
  .modal-actions button {
    width: 100% !important;
    margin: 0 !important;
  }
  
  .avatar-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
  }
  
  .avatar-option {
    width: 56px;
    height: 56px;
  }
}

@media (max-width: 480px) {
  .employee-list {
    gap: 12px;
  }
  
  .avatar-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

</style>

