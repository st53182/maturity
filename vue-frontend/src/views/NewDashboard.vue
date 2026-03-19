<template>
  <div class="new-shell">
    <div class="new-shell__header">
      <div class="new-shell__title">Dashboard</div>
      <div class="new-shell__subtitle">
        Команды и оценка зрелости в обновлённом оформлении (маршрут <code>/new/dashboard</code>).
      </div>
    </div>

    <div class="new-shell__content">
      <UserDashboard variant="new" />
    </div>
  </div>
</template>

<script>
import UserDashboard from "@/views/UserDashboard.vue";

export default {
  components: { UserDashboard },
};
</script>

<style scoped>
.new-shell {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 18px 46px;
}

.new-shell__header {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: rgba(255, 255, 255, 0.74);
  box-shadow: 0 18px 60px rgba(10, 20, 45, 0.1);
  padding: 16px 18px;
}

.new-shell__title {
  font-weight: 750;
  letter-spacing: -0.2px;
}

.new-shell__subtitle {
  margin-top: 8px;
  color: rgba(10, 20, 45, 0.65);
}

.new-shell__content {
  margin-top: 14px;
}
</style>

