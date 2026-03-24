<template>
  <div class="shrink-0 border-b border-gb-border bg-gb-soft/50 px-3 py-2 flex flex-wrap items-center gap-2 text-sm">
    <span class="text-xs font-semibold text-gb-muted uppercase tracking-wide">Фильтры</span>
    <select
      :value="ownerSelect"
      class="rounded-lg border border-gb-border bg-white px-2 py-1.5 text-xs min-w-[140px]"
      @change="onOwnerChange"
    >
      <option value="">Все владельцы</option>
      <option v-for="o in store.owners" :key="o.id" :value="o.id">{{ o.name }}</option>
    </select>
    <select
      :value="statusSelect"
      class="rounded-lg border border-gb-border bg-white px-2 py-1.5 text-xs min-w-[130px]"
      @change="onStatusChange"
    >
      <option value="">Все статусы</option>
      <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
    </select>
    <label class="inline-flex items-center gap-1 text-xs text-gb-muted">
      <span>с</span>
      <input
        :value="store.filters.dateFrom || ''"
        type="date"
        class="rounded border border-gb-border px-1 py-1 text-xs"
        @input="store.setFilters({ dateFrom: $event.target.value || null })"
      />
    </label>
    <label class="inline-flex items-center gap-1 text-xs text-gb-muted">
      <span>по</span>
      <input
        :value="store.filters.dateTo || ''"
        type="date"
        class="rounded border border-gb-border px-1 py-1 text-xs"
        @input="store.setFilters({ dateTo: $event.target.value || null })"
      />
    </label>
    <div class="flex flex-wrap gap-1 items-center ml-auto">
      <span class="text-xs text-gb-muted mr-1">Типы:</span>
      <button
        v-for="k in kindOptions"
        :key="k.id"
        type="button"
        :class="[
          'rounded-full px-2 py-0.5 text-[11px] font-medium border transition-colors',
          store.filters.kinds.includes(k.id)
            ? 'bg-gb-primary/15 border-gb-primary text-gb-primary'
            : 'border-gb-border text-gb-muted hover:bg-white'
        ]"
        @click="toggleKind(k.id)"
      >
        {{ k.label }}
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const store = useProjectDashboardDemoStore()

const statuses = ['backlog', 'planned', 'in_progress', 'blocked', 'done', 'cancelled']

const kindOptions = [
  { id: 'epic', label: 'Эпики' },
  { id: 'task', label: 'Задачи' }
]

const ownerSelect = computed(() => store.filters.ownerIds[0] || '')
const statusSelect = computed(() => store.filters.statuses[0] || '')

function onOwnerChange(e) {
  const v = e.target.value
  store.setFilters({ ownerIds: v ? [v] : [] })
}

function onStatusChange(e) {
  const v = e.target.value
  store.setFilters({ statuses: v ? [v] : [] })
}

function toggleKind(id) {
  const set = new Set(store.filters.kinds)
  if (set.has(id)) set.delete(id)
  else set.add(id)
  store.setFilters({ kinds: [...set] })
}
</script>
