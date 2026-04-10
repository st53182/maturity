<!-- src/components/MarketInfoModal.vue -->
<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <button
        type="button"
        class="modal-close-top"
        @click="$emit('close')"
        :aria-label="$t('common.close')"
      >
        ✕
      </button>
      <h2>📈 {{ $t('assessmentResults.marketModalTitle') }}</h2>
      <p>{{ $t('assessmentResults.marketModalP1') }}</p>
      <p>{{ $t('assessmentResults.marketModalP2') }}</p>
      <p>{{ $t('assessmentResults.marketModalP3') }}</p>
    </div>
  </div>
</template>

<script>
export default {
  name: "MarketInfoModal",
};
</script>

<style scoped>
.modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 999;
}
.modal-content {
  background: #ffffff;
  color: var(--vl-text, #0d1733);
  padding: 20px 30px;
  border-radius: 16px;
  max-width: 500px;
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.24);
  text-align: left;
  border: 1px solid rgba(10, 20, 45, 0.12);
  position: relative;
}
.modal-content h2 {
  margin-top: 0;
  font-size: 1.15rem;
  line-height: 1.35;
  color: inherit;
}
.modal-content p {
  margin: 0 0 12px;
  line-height: 1.5;
  color: inherit;
}
.modal-content p:last-child {
  margin-bottom: 0;
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
