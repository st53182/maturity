<!-- src/components/MarketInfoModal.vue -->
<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="modal-close-top" @click="$emit('close')" aria-label="Close">✕</button>
      <h2>📈 Относительно среднего по индустрии</h2>
      <p>
Этот показатель рассчитывается на основе данных, собранных среди более чем <strong>100 организаций</strong>, а также регулярно обновляется с учетом результатов команд, проходящих оценку на платформе GrowBoard <strong>ежеквартально</strong>.

В расчет включены команды, использующие сервисы платформы и консалтинговых партнеров на территории СНГ.

Он отражает усредненное значение по ключевым метрикам эффективности команд в ИТ и позволяет объективно сравнить текущий уровень вашей команды с рыночной тенденцией.      </p>
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
  background: #ffffff;
  padding: 20px 30px;
  border-radius: 16px;
  max-width: 500px;
  box-shadow: 0 24px 70px rgba(10, 20, 45, 0.24);
  text-align: left;
  border: 1px solid rgba(10, 20, 45, 0.12);
  position: relative;
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
