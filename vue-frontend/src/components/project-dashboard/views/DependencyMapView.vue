<template>
  <div class="h-full flex flex-col min-h-0">
    <div class="flex flex-wrap items-center gap-2 px-3 py-2 border-b border-gb-border shrink-0 text-xs">
      <span class="font-semibold text-gb-muted uppercase">Граф</span>
      <button
        type="button"
        :class="chip(store.graphDetail === 'all')"
        @click="store.setGraphDetail('all')"
      >Все узлы</button>
      <button
        type="button"
        :class="chip(store.graphDetail === 'epics_only')"
        @click="store.setGraphDetail('epics_only')"
      >Только эпики</button>
      <span v-if="derived.criticalPathHasCycle" class="text-gb-danger font-medium ml-2">Цикл в связях «blocks»</span>
      <span class="ml-auto text-gb-muted hidden sm:inline">Клик по узлу — детали · критический путь — фиолетовая обводка</span>
    </div>
    <div class="flex-1 min-h-0 relative">
      <VueFlow
        v-model:nodes="nodes"
        v-model:edges="edges"
        :default-viewport="{ zoom: 0.85, x: 40, y: 20 }"
        :min-zoom="0.15"
        :max-zoom="1.6"
        fit-view-on-init
        class="gb-flow"
        @node-click="onNodeClick"
      >
        <Background pattern-color="#d8e0f0" :gap="18" />
        <Controls />
        <MiniMap pannable zoomable />
      </VueFlow>
      <div class="absolute bottom-3 left-3 z-10 rounded-lg border border-gb-border bg-white/95 px-2 py-1.5 text-[10px] text-gb-muted max-w-[200px]">
        <div class="font-semibold text-gb-text mb-1">Легенда</div>
        <div>Сплошная линия — blocks / зависимость</div>
        <div>Пунктир — прочие типы</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watchEffect, computed } from 'vue'
import { VueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { MiniMap } from '@vue-flow/minimap'
import '@vue-flow/core/dist/style.css'
import '@vue-flow/core/dist/theme-default.css'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'
import { useProjectDashboardDerived } from '@/composables/useProjectDashboardDerived'

const store = useProjectDashboardDemoStore()
const { derived } = useProjectDashboardDerived()

const nodes = ref([])
const edges = ref([])

function chip(on) {
  return on
    ? 'rounded-md px-2 py-1 font-medium bg-gb-primary/15 text-gb-primary'
    : 'rounded-md px-2 py-1 font-medium text-gb-muted hover:bg-gb-soft'
}

const sel = computed(() => store.selectedItemId)

function buildGraph() {
  const d = derived.value
  const cp = d.criticalPathNodeIds
  const prob = d.problematicNodeIds
  const focus = sel.value

  const epicRows = store.filteredEpics
  const taskRows = store.graphDetail === 'epics_only' ? [] : store.filteredTasks
  const epicIds = new Set(epicRows.map((e) => e.id))
  const rows = [...epicRows, ...taskRows]
  const idSet = new Set(rows.map((r) => r.id))

  const layout = new Map()
  let idx = 0
  const cols = 4
  for (const r of rows) {
    const i = idx++
    layout.set(r.id, { x: (i % cols) * 240, y: Math.floor(i / cols) * 96 })
  }

  const n = rows.map((r) => {
    const isEpic = epicIds.has(r.id)
    const onCp = cp.has(r.id)
    const bad = prob.has(r.id)
    const dim =
      focus &&
      !(
        r.id === focus ||
        store.dependencies.some(
          (dep) =>
            (dep.fromId === focus || dep.toId === focus) && (dep.fromId === r.id || dep.toId === r.id)
        )
      )
    const pos = layout.get(r.id) || { x: 0, y: 0 }
    return {
      id: r.id,
      type: 'default',
      position: pos,
      data: { label: r.title },
      style: {
        opacity: dim ? 0.22 : 1,
        borderWidth: 2,
        borderColor: bad ? '#d43b50' : onCp ? '#7c3aed' : isEpic ? '#d97706' : '#2754c7',
        background: isEpic ? '#fffbeb' : '#eff6ff',
        borderRadius: '10px',
        padding: '8px 10px',
        fontSize: '12px',
        fontWeight: '600',
        width: '200px',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis'
      }
    }
  })

  const e = store.dependencies
    .filter((dep) => idSet.has(dep.fromId) && idSet.has(dep.toId))
    .map((dep) => {
      const critical = cp.has(dep.fromId) && cp.has(dep.toId) && dep.type === 'blocks'
      const dashed = dep.type !== 'blocks'
      return {
        id: dep.id,
        source: dep.fromId,
        target: dep.toId,
        label: dep.type,
        animated: dep.type === 'blocks',
        style: {
          stroke: critical ? '#7c3aed' : '#64748b',
          strokeWidth: critical ? 2.5 : 1.5,
          strokeDasharray: dashed ? '6 4' : undefined
        },
        labelStyle: { fontSize: 9, fill: '#64748b' }
      }
    })

  nodes.value = n
  edges.value = e
}

watchEffect(() => {
  store.filteredEpics
  store.filteredTasks
  store.dependencies
  store.graphDetail
  derived.value
  sel.value
  buildGraph()
})

function onNodeClick({ node }) {
  store.selectItem(node.id)
}
</script>

<style>
.gb-flow {
  width: 100%;
  height: 100%;
  min-height: 320px;
}
</style>
