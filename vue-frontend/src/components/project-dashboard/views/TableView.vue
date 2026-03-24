<template>
  <div class="h-full overflow-auto p-2 text-sm">
    <table class="w-full border-collapse text-left">
      <thead class="sticky top-0 z-10 bg-gb-soft border-b border-gb-border text-xs uppercase text-gb-muted font-semibold">
        <tr>
          <th class="p-2 w-10">Тип</th>
          <th class="p-2 cursor-pointer hover:text-gb-text" @click="sortBy('title')">Название</th>
          <th class="p-2 cursor-pointer hover:text-gb-text" @click="sortBy('status')">Статус</th>
          <th class="p-2">Владелец</th>
          <th class="p-2 cursor-pointer hover:text-gb-text" @click="sortBy('start')">Начало</th>
          <th class="p-2 cursor-pointer hover:text-gb-text" @click="sortBy('end')">Конец</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in sortedRows"
          :key="row.id"
          :class="[
            'border-b border-gb-border/80 hover:bg-gb-soft/80 cursor-pointer',
            store.selectedItemId === row.id ? 'bg-gb-primary/5' : ''
          ]"
          @click="store.selectItem(row.id)"
          @dblclick="store.selectItem(row.id)"
        >
          <td class="p-2 text-xs text-gb-muted">{{ row.kind === 'epic' ? 'Эпик' : 'Задача' }}</td>
          <td class="p-2 font-medium text-gb-text">{{ row.title }}</td>
          <td class="p-2">
            <span class="inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium" :class="statusPill(row.status)">{{ row.status }}</span>
          </td>
          <td class="p-2 text-gb-muted text-xs">{{ ownerName(row.ownerId) }}</td>
          <td class="p-2 font-mono text-xs">{{ row.start || '—' }}</td>
          <td class="p-2 font-mono text-xs">{{ row.end || '—' }}</td>
        </tr>
      </tbody>
    </table>
    <p v-if="!sortedRows.length" class="text-center text-gb-muted py-12">Нет строк по фильтрам.</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const store = useProjectDashboardDemoStore()
const sortKey = ref('end')
const sortDir = ref(1)

const rows = computed(() => {
  const out = []
  for (const e of store.filteredEpics) {
    out.push({ kind: 'epic', id: e.id, title: e.title, status: e.status, ownerId: e.ownerId, start: e.start, end: e.end })
  }
  for (const t of store.filteredTasks) {
    out.push({
      kind: 'task',
      id: t.id,
      title: t.title,
      status: t.status,
      ownerId: t.ownerId,
      start: t.start,
      end: t.end
    })
  }
  return out
})

const sortedRows = computed(() => {
  const k = sortKey.value
  const d = sortDir.value
  return [...rows.value].sort((a, b) => {
    const av = a[k] || ''
    const bv = b[k] || ''
    if (av < bv) return -1 * d
    if (av > bv) return 1 * d
    return 0
  })
})

function sortBy(k) {
  if (sortKey.value === k) sortDir.value *= -1
  else {
    sortKey.value = k
    sortDir.value = 1
  }
}

function ownerName(id) {
  if (!id) return '—'
  return store.owners.find((o) => o.id === id)?.name || id
}

function statusPill(s) {
  if (s === 'done') return 'bg-emerald-100 text-emerald-800'
  if (s === 'blocked') return 'bg-red-100 text-red-800'
  if (s === 'in_progress') return 'bg-blue-100 text-blue-800'
  if (s === 'planned') return 'bg-slate-100 text-slate-700'
  return 'bg-gray-100 text-gray-700'
}
</script>
