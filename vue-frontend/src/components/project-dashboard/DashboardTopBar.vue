<template>
  <header class="border-b border-gb-border bg-gb-surface px-4 py-3 shrink-0">
    <div class="flex flex-wrap items-start justify-between gap-3">
      <div class="min-w-0">
        <h1 class="text-lg font-semibold text-gb-text truncate tracking-tight">{{ store.project.name }}</h1>
        <p class="text-xs text-gb-muted mt-0.5">
          Период: {{ store.project.period.start }} — {{ store.project.period.end }}
        </p>
      </div>
      <div class="flex flex-wrap items-center gap-2">
        <div class="relative group">
          <input
            ref="searchRef"
            :value="store.filters.search"
            type="search"
            placeholder="Поиск…"
            class="w-44 sm:w-56 rounded-lg border border-gb-border bg-white px-3 py-2 text-sm text-gb-text placeholder:text-gb-muted focus:outline-none focus:ring-2 focus:ring-gb-primary/25 focus:border-gb-primary"
            @input="store.setSearch($event.target.value)"
          />
          <span
            class="pointer-events-none absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-gb-muted opacity-0 group-focus-within:opacity-100 hidden sm:inline"
            title="Сокращение: /"
          >/</span>
        </div>
        <div ref="addRootRef" class="relative">
          <button
            type="button"
            class="inline-flex items-center gap-1 rounded-lg bg-gradient-to-br from-[#142b66] to-[#2754c7] px-3 py-2 text-sm font-semibold text-white shadow-sm hover:opacity-95"
            @click="addOpen = !addOpen"
          >
            Добавить
            <span class="text-white/80 text-xs">▾</span>
          </button>
          <div
            v-if="addOpen"
            class="absolute right-0 z-50 mt-1 w-48 rounded-lg border border-gb-border bg-white py-1 shadow-lg text-sm"
          >
            <button type="button" class="block w-full text-left px-3 py-2 hover:bg-gb-soft" @click="quick('epic')">Эпик</button>
            <button type="button" class="block w-full text-left px-3 py-2 hover:bg-gb-soft" @click="quick('task')">Задача</button>
            <button type="button" class="block w-full text-left px-3 py-2 hover:bg-gb-soft" @click="quick('milestone')">Веха</button>
            <button type="button" class="block w-full text-left px-3 py-2 hover:bg-gb-soft" @click="quick('risk')">Риск</button>
          </div>
        </div>
      </div>
    </div>
    <nav class="mt-3 flex flex-wrap gap-1" aria-label="Режимы">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        type="button"
        :class="[
          'rounded-lg px-3 py-1.5 text-sm font-medium transition-colors',
          store.viewMode === tab.id
            ? 'bg-gb-soft text-gb-primary border border-gb-border'
            : 'text-gb-muted hover:text-gb-text hover:bg-gb-soft/80'
        ]"
        @click="setView(tab.id)"
      >
        {{ tab.label }}
      </button>
    </nav>
  </header>
</template>

<script setup>
/* eslint-disable no-undef -- defineExpose compiler macro */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const store = useProjectDashboardDemoStore()
const router = useRouter()
const route = useRoute()
const addOpen = ref(false)
const searchRef = ref(null)
const addRootRef = ref(null)

const tabs = [
  { id: 'roadmap', label: 'Roadmap' },
  { id: 'dependencies', label: 'Зависимости' },
  { id: 'table', label: 'Таблица' },
  { id: 'timeline', label: 'Timeline' }
]

function setView(id) {
  store.setViewMode(id)
  router.replace({ query: { ...route.query, view: id } })
}

function quick(kind) {
  addOpen.value = false
  if (kind === 'epic') store.addEpicQuick()
  if (kind === 'task') store.addTaskQuick()
  if (kind === 'milestone') store.addMilestoneQuick()
  if (kind === 'risk') store.addRiskQuick()
}

function onDocClick(e) {
  if (addRootRef.value && !addRootRef.value.contains(e.target)) addOpen.value = false
}

onMounted(() => {
  const v = route.query.view
  if (v && ['roadmap', 'dependencies', 'table', 'timeline'].includes(String(v))) {
    store.setViewMode(String(v))
  }
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
})

defineExpose({ searchRef })
</script>
