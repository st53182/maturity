<template>
  <div class="p-3 text-sm">
    <div class="text-[11px] font-semibold uppercase tracking-wide text-gb-muted mb-2">Проекты</div>
    <button
      type="button"
      class="w-full text-left rounded-lg px-2 py-2 font-medium bg-gb-soft text-gb-text border border-gb-border"
    >
      {{ store.project.name }}
    </button>
    <button
      type="button"
      class="mt-2 w-full text-left text-xs text-gb-primary font-medium hover:underline"
      @click="store.resetDemo(); store.simulateLoading()"
    >
      Сбросить демо-данные
    </button>

    <div class="text-[11px] font-semibold uppercase tracking-wide text-gb-muted mt-5 mb-2">Быстрые фильтры</div>
    <div class="flex flex-col gap-1">
      <button
        v-for="q in quicks"
        :key="q.id"
        type="button"
        :class="[
          'text-left rounded-lg px-2 py-1.5 text-xs transition-colors',
          store.filters.quick === q.id ? 'bg-gb-primary/10 text-gb-primary font-semibold' : 'text-gb-text hover:bg-gb-soft'
        ]"
        @click="toggleQuick(q.id)"
      >
        {{ q.label }}
      </button>
      <button
        type="button"
        class="text-left rounded-lg px-2 py-1.5 text-xs text-gb-muted hover:bg-gb-soft"
        @click="store.applyQuick(null)"
      >
        Сбросить быстрый фильтр
      </button>
    </div>

    <div class="text-[11px] font-semibold uppercase tracking-wide text-gb-muted mt-5 mb-2">Сохранённые виды</div>
    <div v-if="!store.savedViews.length" class="text-xs text-gb-muted px-1">Пока нет. Задайте фильтры и сохраните.</div>
    <ul v-else class="space-y-1">
      <li v-for="v in store.savedViews" :key="v.id" class="flex items-center gap-1 group">
        <button type="button" class="flex-1 text-left truncate text-xs rounded px-2 py-1 hover:bg-gb-soft" @click="store.applySavedView(v)">
          {{ v.name }}
        </button>
        <button
          type="button"
          class="text-gb-muted text-xs px-1 opacity-0 group-hover:opacity-100 hover:text-gb-danger"
          title="Удалить"
          @click="store.removeSavedView(v.id)"
        >×</button>
      </li>
    </ul>
    <div class="mt-2 flex gap-1">
      <input v-model="saveName" type="text" placeholder="Название вида" class="flex-1 min-w-0 rounded border border-gb-border px-2 py-1 text-xs" />
      <button
        type="button"
        class="shrink-0 rounded bg-gb-soft border border-gb-border px-2 py-1 text-xs font-semibold"
        @click="saveView"
      >OK</button>
    </div>

    <div class="mt-6 text-[11px] text-gb-muted leading-relaxed px-1">
      <span class="font-semibold text-gb-text">Подсказка:</span> «Мои» — владелец Anna (демо). Сокращения: <kbd class="px-1 rounded bg-gb-soft border border-gb-border text-[10px]">/</kbd> поиск,
      <kbd class="px-1 rounded bg-gb-soft border border-gb-border text-[10px]">?</kbd> шпаргалка,
      <kbd class="px-1 rounded bg-gb-soft border border-gb-border text-[10px]">Esc</kbd> закрыть панель.
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const store = useProjectDashboardDemoStore()
const saveName = ref('')

const quicks = [
  { id: 'mine', label: 'Мои элементы' },
  { id: 'overdue', label: 'Просрочено' },
  { id: 'blocked', label: 'Статус blocked' },
  { id: 'unassigned', label: 'Без владельца' }
]

function toggleQuick(id) {
  store.applyQuick(store.filters.quick === id ? null : id)
}

function saveView() {
  const n = saveName.value.trim()
  if (!n) return
  store.saveCurrentView(n)
  saveName.value = ''
}
</script>
