<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button
        type="button"
        class="modal-close-top"
        @click="$emit('close')"
        :aria-label="$t('common.close')"
      >
        ✕
      </button>
      <h3>🏅 {{ $t('assessmentResults.levelModalTitle') }}</h3>
      <ul>
        <li v-html="$t('assessmentResults.levelModalItem1')"></li>
        <li v-html="$t('assessmentResults.levelModalItem2')"></li>
        <li v-html="$t('assessmentResults.levelModalItem3')"></li>
        <li v-html="$t('assessmentResults.levelModalItem4')"></li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: "LevelInfoModal",
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.modal-content {
  background: #ffffff;
  color: var(--vl-text, #0d1733);
  padding: 20px 30px;
  border-radius: 16px;
  max-width: 400px;
  text-align: left;
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.24);
  border: 1px solid rgba(10, 20, 45, 0.12);
  position: relative;
}
.modal-content h3 {
  margin-top: 0;
  color: inherit;
}
.modal-content ul {
  padding-left: 20px;
  margin: 0;
  color: inherit;
}
.modal-content :deep(strong) {
  color: inherit;
}
.modal-close-top {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 32px;
  height: 32px;
  background: rgba(10, 20, 45, 0.08);
  color: rgba(10, 20, 45, 0.84);
  padding: 0;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  font-size: 18px;
}
</style>
