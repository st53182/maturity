<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <button class="modal-close-top" @click="$emit('close')" aria-label="Close">✕</button>
      <h3>🏅 Уровни команды</h3>
      <ul>
        <li><strong>Начинающий:</strong> до 2 баллов</li>
        <li><strong>Растущий:</strong> от 2 до 3 баллов</li>
        <li><strong>Прогрессирующий:</strong> от 3 до 4 баллов</li>
        <li><strong>Высокоэффективный:</strong> от 4 до 5 баллов</li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background-color: rgba(0, 0, 0, 0.4);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 9999;
}

.modal-content {
  background: #ffffff;
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
}
.modal-content ul {
  padding-left: 20px;
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
