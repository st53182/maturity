<template>
  <div id="gb-dashboard" class="gb-page min-h-screen bg-[#f6f9ff]">
    <div class="max-w-[1600px] mx-auto">
      <div class="flex items-center justify-between px-3 pt-3 pb-1">
        <router-link
          to="/new"
          class="text-sm font-semibold text-gb-muted hover:text-gb-primary"
        >← На главную</router-link>
        <span class="text-xs text-gb-muted">Демо · данные в памяти (mock)</span>
      </div>
      <DashboardShell>
        <template #top>
          <DashboardTopBar ref="topBarRef" />
        </template>
        <template #summary>
          <DashboardSummaryStrip />
        </template>
        <template #sidebar>
          <DashboardSidebar />
        </template>
        <template #filters>
          <DashboardFiltersBar />
        </template>
        <RoadmapView v-if="store.viewMode === 'roadmap'" />
        <DependencyMapView v-else-if="store.viewMode === 'dependencies'" />
        <TableView v-else-if="store.viewMode === 'table'" />
        <TimelineView v-else />
        <template #drawer>
          <DetailsDrawer @close="store.selectItem(null)" />
        </template>
      </DashboardShell>
    </div>

    <div
      v-if="store.showShortcutsModal"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-black/40 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="gb-shortcuts-title"
      @click.self="store.toggleShortcutsModal(false)"
    >
      <div class="bg-white rounded-xl border border-gb-border shadow-xl max-w-md w-full p-5 text-sm">
        <h3 id="gb-shortcuts-title" class="text-base font-semibold text-gb-text mb-3">Горячие клавиши</h3>
        <ul class="space-y-2 text-gb-text">
          <li><kbd class="px-1.5 py-0.5 rounded bg-gb-soft border border-gb-border text-xs">/</kbd> — фокус в поиск</li>
          <li><kbd class="px-1.5 py-0.5 rounded bg-gb-soft border border-gb-border text-xs">Esc</kbd> — снять выделение / закрыть панель</li>
          <li><kbd class="px-1.5 py-0.5 rounded bg-gb-soft border border-gb-border text-xs">?</kbd> — эта подсказка</li>
        </ul>
        <button
          type="button"
          class="mt-4 w-full rounded-lg bg-gradient-to-br from-[#142b66] to-[#2754c7] py-2.5 font-semibold text-white"
          @click="store.toggleShortcutsModal(false)"
        >Понятно</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import '@/styles/gb-dashboard.css'
import DashboardShell from '@/components/project-dashboard/DashboardShell.vue'
import DashboardTopBar from '@/components/project-dashboard/DashboardTopBar.vue'
import DashboardSidebar from '@/components/project-dashboard/DashboardSidebar.vue'
import DashboardSummaryStrip from '@/components/project-dashboard/DashboardSummaryStrip.vue'
import DashboardFiltersBar from '@/components/project-dashboard/DashboardFiltersBar.vue'
import DetailsDrawer from '@/components/project-dashboard/DetailsDrawer.vue'
import RoadmapView from '@/components/project-dashboard/views/RoadmapView.vue'
import DependencyMapView from '@/components/project-dashboard/views/DependencyMapView.vue'
import TableView from '@/components/project-dashboard/views/TableView.vue'
import TimelineView from '@/components/project-dashboard/views/TimelineView.vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'
import { useDashboardShortcuts } from '@/composables/useDashboardShortcuts'

const store = useProjectDashboardDemoStore()
const topBarRef = ref(null)

useDashboardShortcuts({
  focusSearch: () => {
    const el = topBarRef.value?.searchRef
    if (el) {
      el.focus()
      el.select?.()
    }
  },
  onEsc: () => {
    store.toggleShortcutsModal(false)
    store.selectItem(null)
  },
  onHelp: () => store.toggleShortcutsModal(true)
})

onMounted(() => {
  store.simulateLoading()
})
</script>

<style scoped>
.gb-page {
  font-family: var(--vl-font, Inter, system-ui, sans-serif);
}
</style>
