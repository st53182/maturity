<!-- src/components/MarketInfoModal.vue -->
<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <h2>📈 {{ $t('modals.relativeToIndustryAverage') }}</h2>
      <p>
Этот показатель рассчитывается на основе данных, собранных среди более чем <strong>100 организаций</strong>, а также регулярно обновляется с учетом результатов команд, проходящих оценку на платформе GrowBoard <strong>ежеквартально</strong>.

В расчет включены команды, использующие сервисы платформы и консалтинговых партнеров на территории СНГ.

Он отражает усредненное значение по ключевым метрикам эффективности команд в ИТ и позволяет объективно сравнить текущий уровень вашей команды с рыночной тенденцией.      </p>
      <button @click="$emit('close')">{{ $t('common.close') }}</button>
    </div>
  </div>
</template>

<script>
export default {
  name: "MarketInfoModal"
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
  background: #6f5fbe;
  padding: 20px 30px;
  border-radius: 10px;
  max-width: 500px;
  box-shadow: 0 0 12px rgba(0,0,0,0.2);
  text-align: left;
}
.modal-content button {
  margin-top: 20px;
  background: #3f51b5;
  color: white;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>
