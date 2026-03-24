<template>
  <div v-if="store.loading" class="border-b border-gb-border bg-gb-surface px-4 py-3 animate-pulse">
    <div class="flex flex-wrap gap-3">
      <div v-for="i in 5" :key="i" class="h-14 flex-1 min-w-[120px] rounded-lg bg-gb-soft" />
    </div>
  </div>
  <div v-else-if="store.error" class="border-b border-gb-border bg-red-50 px-4 py-2 text-sm text-gb-danger">
    {{ store.error }}
  </div>
  <div v-else class="border-b border-gb-border bg-gb-surface px-3 py-2">
    <div class="flex flex-wrap gap-2">
      <div class="gb-widget" title="Доля завершённых задач">
        <div class="gb-widget__label">Прогресс</div>
        <div class="gb-widget__val">{{ d.progressPercent }}%</div>
      </div>
      <div class="gb-widget" :class="{ 'ring-1 ring-amber-300': d.overdueCount > 0 }" title="Задачи и эпики с прошедшим end">
        <div class="gb-widget__label">Просрочено</div>
        <div class="gb-widget__val text-amber-700">{{ d.overdueCount }}</div>
      </div>
      <div class="gb-widget" title="Входящие blocks от незавершённых работ">
        <div class="gb-widget__label">Блокеры (завис.)</div>
        <div class="gb-widget__val">{{ d.blockedByDepsCount }}</div>
      </div>
      <div class="gb-widget" title="Явный статус blocked">
        <div class="gb-widget__label">Статус blocked</div>
        <div class="gb-widget__val">{{ d.statusBlockedCount }}</div>
      </div>
      <div class="gb-widget" title="Без ownerId">
        <div class="gb-widget__label">Без владельца</div>
        <div class="gb-widget__val">{{ d.unassignedCount }}</div>
      </div>
      <div class="gb-widget flex-[2] min-w-[200px]" title="Критический путь по связям blocks">
        <div class="gb-widget__label">Критический путь</div>
        <div v-if="d.criticalPathHasCycle" class="text-xs text-gb-danger font-medium">Цикл в графе blocks — проверьте зависимости</div>
        <div v-else class="text-xs text-gb-muted truncate">
          {{ cpPreview }}
        </div>
      </div>
      <div class="gb-widget flex-[2] min-w-[180px]">
        <div class="gb-widget__label">Ближайшие вехи</div>
        <ul class="text-xs text-gb-text space-y-0.5 mt-0.5">
          <li v-for="m in d.upcomingMilestones" :key="m.id" class="flex justify-between gap-2">
            <span class="truncate">{{ m.title }}</span>
            <span class="text-gb-muted shrink-0">{{ m.date }}</span>
          </li>
          <li v-if="!d.upcomingMilestones.length" class="text-gb-muted">Нет предстоящих</li>
        </ul>
      </div>
      <div class="gb-widget flex-[2] min-w-[200px]">
        <div class="gb-widget__label">Команда</div>
        <div class="flex flex-wrap gap-1 mt-1">
          <span
            v-for="o in ownersPreview"
            :key="o.id"
            class="inline-flex items-center rounded-full bg-gb-soft border border-gb-border px-2 py-0.5 text-[11px] text-gb-text"
          >{{ o.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'
import { useProjectDashboardDerived } from '@/composables/useProjectDashboardDerived'

const store = useProjectDashboardDemoStore()
const { derived } = useProjectDashboardDerived()
const d = computed(() => derived.value)

const cpPreview = computed(() => {
  const ids = [...d.value.criticalPathNodeIds]
  if (!ids.length) return 'Нет рёбер типа blocks'
  const labels = ids.slice(0, 6).map((id) => {
    const t = store.tasks.find((x) => x.id === id)
    if (t) return t.title.slice(0, 24)
    const e = store.epics.find((x) => x.id === id)
    if (e) return e.title.slice(0, 24)
    return id
  })
  return labels.join(' → ')
})

const ownersPreview = computed(() => store.owners.slice(0, 6))
</script>

<style scoped>
.gb-widget {
  @apply flex-1 min-w-[100px] rounded-lg border border-gb-border bg-white px-3 py-2;
}
.gb-widget__label {
  @apply text-[10px] font-semibold uppercase tracking-wide text-gb-muted;
}
.gb-widget__val {
  @apply text-xl font-bold text-gb-text tabular-nums mt-0.5;
}
</style>
