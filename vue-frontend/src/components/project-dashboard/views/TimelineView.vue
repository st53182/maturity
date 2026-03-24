<template>
  <div class="h-full overflow-auto p-3 text-sm">
    <div class="text-xs text-gb-muted mb-3">Компактная шкала относительно периода проекта (как Gantt-строка на элемент).</div>
    <div class="space-y-2 min-w-[600px]">
      <div
        v-for="row in allRows"
        :key="row.id"
        class="flex items-center gap-2 rounded-lg border border-gb-border bg-white p-2 hover:bg-gb-soft/50 cursor-pointer"
        :class="{ 'ring-2 ring-gb-primary/25': store.selectedItemId === row.id }"
        @click="store.selectItem(row.id)"
      >
        <div class="w-36 shrink-0 text-xs font-medium text-gb-text truncate" :title="row.title">{{ row.title }}</div>
        <div class="flex-1 h-6 relative bg-gb-soft rounded-md overflow-hidden">
          <div
            class="absolute top-0.5 bottom-0.5 rounded-md"
            :class="row.kind === 'epic' ? 'bg-amber-400/90' : 'bg-blue-500/85'"
            :style="barStyle(row)"
          />
        </div>
        <div class="w-24 shrink-0 text-[11px] font-mono text-gb-muted text-right">{{ row.start }} → {{ row.end }}</div>
      </div>
    </div>
    <p v-if="!allRows.length" class="text-gb-muted text-center py-12">Нет элементов.</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const store = useProjectDashboardDemoStore()

const periodSpan = computed(() => {
  const p = store.project.period
  const a = new Date(p.start + 'T12:00:00').getTime()
  const b = new Date(p.end + 'T12:00:00').getTime()
  return { start: a, end: b, span: Math.max(1, b - a) }
})

const allRows = computed(() => {
  const out = []
  for (const e of store.filteredEpics) {
    out.push({ kind: 'epic', id: e.id, title: e.title, start: e.start, end: e.end })
  }
  for (const t of store.filteredTasks) {
    out.push({ kind: 'task', id: t.id, title: t.title, start: t.start, end: t.end })
  }
  return out
})

function barStyle(row) {
  const { start, span } = periodSpan.value
  const p = store.project.period
  const s = new Date((row.start || p.start) + 'T12:00:00').getTime()
  const e = new Date((row.end || p.end) + 'T12:00:00').getTime()
  const left = ((s - start) / span) * 100
  const w = ((e - s) / span) * 100
  return {
    left: `${Math.max(0, left)}%`,
    width: `${Math.max(2, w)}%`
  }
}
</script>
