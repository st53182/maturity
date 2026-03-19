<template>
  <div class="new-tool-shell">
    <div class="new-tool-shell__header">
      <div class="new-tool-shell__title">{{ title }}</div>
      <div v-if="subtitle" class="new-tool-shell__subtitle">{{ subtitle }}</div>
    </div>
    <div class="new-tool-shell__inner">
      <slot />
    </div>
  </div>
</template>

<script>
export default {
  name: "NewToolShell",
  props: {
    title: { type: String, required: true },
    subtitle: { type: String, default: "" },
  },
};
</script>

<style scoped>
.new-tool-shell {
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 18px 46px;
  position: relative;
  animation: shellReveal 420ms ease-out;
}

.new-tool-shell::before {
  content: "";
  position: absolute;
  right: -160px;
  top: -100px;
  width: 380px;
  height: 380px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(120, 119, 255, 0.14), rgba(120, 119, 255, 0));
  pointer-events: none;
}

.new-tool-shell__header {
  border-radius: 18px;
  border: 1px solid rgba(10, 20, 45, 0.08);
  background: linear-gradient(175deg, rgba(255, 255, 255, 0.93), rgba(246, 249, 255, 0.82));
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.11);
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
}

.new-tool-shell__header::after {
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

.new-tool-shell__title {
  font-weight: 750;
  letter-spacing: -0.2px;
  font-size: 1.25rem;
  color: rgba(10, 20, 45, 0.94);
}

.new-tool-shell__subtitle {
  margin-top: 8px;
  color: rgba(10, 20, 45, 0.62);
  font-size: 14px;
  line-height: 1.45;
}

.new-tool-shell__inner {
  margin-top: 14px;
}

@media (max-width: 820px) {
  .new-tool-shell {
    padding: 16px 12px 28px;
  }

  .new-tool-shell__header {
    padding: 14px 14px;
  }

  .new-tool-shell__title {
    font-size: 1.1rem;
  }
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
