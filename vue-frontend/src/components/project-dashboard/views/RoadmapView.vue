<template>
  <div class="h-full flex flex-col min-h-0 text-sm">
    <div class="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-gb-border shrink-0">
      <span class="text-xs text-gb-muted font-semibold uppercase">Группировка</span>
      <button
        v-for="g in groups"
        :key="g.id"
        type="button"
        :class="[
          'rounded-md px-2 py-1 text-xs font-medium',
          store.roadmapGroupBy === g.id ? 'bg-gb-primary/15 text-gb-primary' : 'text-gb-muted hover:bg-gb-soft'
        ]"
        @click="store.setRoadmapGroupBy(g.id)"
      >
        {{ g.label }}
      </button>
    </div>

    <div v-if="!lanes.length" class="flex-1 flex items-center justify-center text-gb-muted text-sm p-8">
      Нет элементов по текущим фильтрам.
    </div>

    <div v-else class="flex-1 overflow-auto min-h-0">
      <div class="min-w-[720px]">
        <div class="flex border-b border-gb-border bg-gb-soft/80 sticky top-0 z-10">
          <div class="w-44 shrink-0 px-2 py-2 text-xs font-semibold text-gb-muted border-r border-gb-border">Шкала</div>
          <div class="flex-1 relative h-10">
            <div
              v-for="ms in milestonesInPeriod"
              :key="ms.id"
              class="absolute top-0 bottom-0 w-px bg-gb-primary/40 z-20"
              :style="lineStyle(ms.date)"
              :title="ms.title"
            />
            <div
              v-for="(w, i) in weekTicks"
              :key="i"
              class="absolute top-0 bottom-0 border-l border-gb-border/60 text-[10px] text-gb-muted pl-0.5 pt-1"
              :style="{ left: w.pct + '%' }"
            >
              {{ w.label }}
            </div>
          </div>
        </div>
        <div v-for="lane in lanes" :key="lane.key" class="flex border-b border-gb-border min-h-[48px]">
          <div class="w-44 shrink-0 px-2 py-2 text-xs text-gb-text border-r border-gb-border bg-white/80 truncate" :title="lane.label">
            {{ lane.label }}
          </div>
          <div class="flex-1 relative bg-white/50 py-2">
            <button
              v-for="b in lane.bars"
              :key="b.id"
              type="button"
              class="absolute top-1 h-7 rounded-md border text-left px-2 text-[11px] font-medium truncate shadow-sm transition-shadow hover:shadow-md focus:outline-none focus:ring-2 focus:ring-gb-primary/30"
              :class="barClass(b)"
              :style="{ ...barPos(b), maxWidth: 'calc(100% - 4px)' }"
              :title="b.title + ' (перетащите горизонтально)'"
              @click="store.selectItem(b.id)"
              @pointerdown.prevent="startDrag($event, b)"
            >
              {{ b.title }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'
import { useProjectDashboardDerived } from '@/composables/useProjectDashboardDerived'

const store = useProjectDashboardDemoStore()
const { derived } = useProjectDashboardDerived()

const groups = [
  { id: 'team', label: 'Команда' },
  { id: 'owner', label: 'Владелец' },
  { id: 'kind', label: 'Тип' }
]

const period = computed(() => store.project.period)

const periodSpan = computed(() => {
  const a = new Date(period.value.start + 'T12:00:00').getTime()
  const b = new Date(period.value.end + 'T12:00:00').getTime()
  return { start: a, end: b, span: Math.max(1, b - a) }
})

function barPos(b) {
  const { start, span } = periodSpan.value
  const s = new Date((b.start || period.value.start) + 'T12:00:00').getTime()
  const e = new Date((b.end || period.value.end) + 'T12:00:00').getTime()
  const left = ((s - start) / span) * 100
  const w = ((e - s) / span) * 100
  return {
    left: `${Math.max(0, Math.min(99, left))}%`,
    width: `${Math.max(1, Math.min(100 - left, w))}%`
  }
}

function lineStyle(iso) {
  const { start, span } = periodSpan.value
  const t = new Date(iso + 'T12:00:00').getTime()
  const p = ((t - start) / span) * 100
  return { left: `${Math.max(0, Math.min(100, p))}%` }
}

const milestonesInPeriod = computed(() =>
  store.milestones.filter((m) => m.date >= period.value.start && m.date <= period.value.end)
)

const weekTicks = computed(() => {
  const { start, end, span } = periodSpan.value
  const ticks = []
  const cur = new Date(start)
  cur.setUTCHours(12, 0, 0, 0)
  const endD = new Date(end)
  let guard = 0
  while (cur <= endD && guard++ < 80) {
    const t = cur.getTime()
    const pct = ((t - start) / span) * 100
    ticks.push({
      pct,
      label: cur.toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
    })
    cur.setDate(cur.getDate() + 7)
  }
  return ticks
})

function laneKey(row, kind) {
  if (store.roadmapGroupBy === 'owner') {
    return row.ownerId || '_none'
  }
  if (store.roadmapGroupBy === 'kind') {
    return kind
  }
  const o = store.owners.find((x) => x.id === row.ownerId)
  return o?.teamId || '_none'
}

function laneLabel(key) {
  if (store.roadmapGroupBy === 'owner') {
    if (key === '_none') return 'Без владельца'
    return store.owners.find((o) => o.id === key)?.name || key
  }
  if (store.roadmapGroupBy === 'kind') {
    return key === 'epic' ? 'Эпики' : 'Задачи'
  }
  const t = store.teams.find((x) => x.id === key)
  if (t) return t.name
  if (key === '_none') return 'Без команды'
  return key
}

const lanes = computed(() => {
  const map = new Map()
  const push = (row, kind) => {
    const k = laneKey(row, kind)
    if (!map.has(k)) map.set(k, { key: k, label: laneLabel(k), bars: [] })
    map.get(k).bars.push({
      id: row.id,
      title: row.title,
      start: row.start,
      end: row.end,
      status: row.status,
      kind
    })
  }
  for (const e of store.filteredEpics) push(e, 'epic')
  for (const t of store.filteredTasks) push(t, 'task')
  return [...map.values()]
})

function barClass(b) {
  const prob = derived.value.problematicNodeIds.has(b.id)
  const cp = derived.value.criticalPathNodeIds.has(b.id)
  const base =
    b.kind === 'epic'
      ? 'border-amber-600/50 bg-amber-50 text-amber-950'
      : 'border-blue-600/40 bg-blue-50 text-blue-950'
  if (b.status === 'done' || b.status === 'cancelled') return base + ' opacity-60'
  if (prob) return base + ' ring-2 ring-gb-danger/40'
  if (cp) return base + ' ring-2 ring-violet-500/50'
  return base
}

let dragState = null

function startDrag(ev, b) {
  if (b.kind !== 'task') return
  ev.target.setPointerCapture(ev.pointerId)
  dragState = {
    id: b.id,
    startX: ev.clientX,
    pxPerDay: 3
  }
}

function onMove(ev) {
  if (!dragState) return
  const dx = ev.clientX - dragState.startX
  if (Math.abs(dx) < 4) return
  const days = Math.round(dx / dragState.pxPerDay)
  if (days !== 0) {
    store.shiftTaskDates(dragState.id, days)
    dragState.startX = ev.clientX
  }
}

function onUp(ev) {
  if (dragState && ev.target.releasePointerCapture) {
    try {
      ev.target.releasePointerCapture(ev.pointerId)
    } catch {
      /* ignore */
    }
  }
  dragState = null
}

onMounted(() => {
  window.addEventListener('pointermove', onMove)
  window.addEventListener('pointerup', onUp)
})
onUnmounted(() => {
  window.removeEventListener('pointermove', onMove)
  window.removeEventListener('pointerup', onUp)
})
</script>
