<template>
  <div class="modal-overlay" @click.self="$emit('close')">
    <div class="modal-content">
      <h3>🏅 {{ $t('modals.teamLevels') }}</h3>
      <ul>
        <li><strong>{{ $t('modals.levels.beginner') }}:</strong> {{ $t('modals.levelRanges.beginner') }}</li>
        <li><strong>{{ $t('modals.levels.growing') }}:</strong> {{ $t('modals.levelRanges.growing') }}</li>
        <li><strong>{{ $t('modals.levels.progressing') }}:</strong> {{ $t('modals.levelRanges.progressing') }}</li>
        <li><strong>{{ $t('modals.levels.highPerforming') }}:</strong> {{ $t('modals.levelRanges.highPerforming') }}</li>
      </ul>
      <button @click="$emit('close')">{{ $t('common.close') }}</button>
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
  background: #8c7bc6;
  padding: 20px 30px;
  border-radius: 10px;
  max-width: 400px;
  text-align: left;
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.2);
}
.modal-content h3 {
  margin-top: 0;
}
.modal-content ul {
  padding-left: 20px;
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
