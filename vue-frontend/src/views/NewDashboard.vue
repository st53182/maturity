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
  position: relative;
  animation: shellReveal 420ms ease-out;
}

.new-shell::before {
  content: "";
  position: absolute;
  right: -180px;
  top: -120px;
  width: 420px;
  height: 420px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(120, 119, 255, 0.18), rgba(120, 119, 255, 0));
  pointer-events: none;
}

.new-shell__header {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(175deg, rgba(255, 255, 255, 0.93), rgba(246, 249, 255, 0.82));
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.11);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
}

.new-shell__header::after {
  content: "";
  position: absolute;
  top: -120%;
  left: -22%;
  width: 30%;
  height: 300%;
  background: linear-gradient(120deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  transform: rotate(16deg);
  animation: headerShine 8.8s linear infinite;
  pointer-events: none;
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

@keyframes shellReveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes headerShine {
  0% {
    transform: translateX(-220px) rotate(16deg);
  }
  45%,
  100% {
    transform: translateX(820px) rotate(16deg);
  }
}
</style>

