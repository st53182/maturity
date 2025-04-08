<!-- src/components/MarketInfoModal.vue -->
<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <div class="modal-content">
      <h2>📈 Относительно среднего по индустрии</h2>
      <p>
        Этот показатель рассчитывается на основе данных, собранных среди более чем <strong>100 организаций и дополняется командами, что прошли оценку на платформе GrowBoard раз в квартал.</strong>, использующих сервисы консалтинговых компаний на территории СНГ. Он отражает среднее значение оценки команд в различных отраслях и позволяет сравнить вашу команду с общей тенденцией.
      </p>
      <button @click="$emit('close')">Закрыть</button>
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
}
</style>
