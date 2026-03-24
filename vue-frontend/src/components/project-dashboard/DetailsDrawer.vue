<template>
  <aside
    class="gb-drawer fixed lg:relative inset-y-0 right-0 z-40 w-full max-w-md shrink-0 border-l border-gb-border bg-gb-surface shadow-xl flex flex-col lg:shadow-none"
    role="complementary"
    aria-label="Детали элемента"
  >
    <div class="flex items-center justify-between border-b border-gb-border px-3 py-2 shrink-0">
      <h2 class="text-sm font-semibold text-gb-text truncate pr-2">{{ title }}</h2>
      <button
        type="button"
        class="rounded-lg p-2 text-gb-muted hover:bg-gb-soft hover:text-gb-text text-lg leading-none"
        aria-label="Закрыть"
        @click="close"
      >×</button>
    </div>

    <div v-if="!item" class="flex-1 flex flex-col items-center justify-center p-6 text-center text-gb-muted text-sm">
      <p>Выберите эпик, задачу или веху в центральной области.</p>
      <p class="mt-2 text-xs">Двойной клик в таблице или клик по полосе / узлу графа.</p>
    </div>

    <template v-else>
      <div class="flex gap-1 border-b border-gb-border px-2 py-1.5 shrink-0 overflow-x-auto">
        <button
          v-for="t in tabs"
          :key="t.id"
          type="button"
          :class="[
            'whitespace-nowrap rounded-md px-2 py-1 text-xs font-medium',
            tab === t.id ? 'bg-gb-soft text-gb-primary' : 'text-gb-muted hover:text-gb-text'
          ]"
          @click="tab = t.id"
        >
          {{ t.label }}
        </button>
      </div>
      <div class="flex-1 overflow-y-auto p-3 text-sm">
        <div v-show="tab === 'overview'" class="space-y-3">
          <div v-if="item.kind === 'task' || item.kind === 'epic'">
            <div class="text-xs text-gb-muted uppercase font-semibold">Статус</div>
            <select
              :value="workStatus"
              class="mt-1 w-full rounded-lg border border-gb-border px-2 py-1.5 text-sm"
              @change="patchStatus($event.target.value)"
            >
              <option v-for="s in statuses" :key="s" :value="s">{{ s }}</option>
            </select>
          </div>
          <div v-if="item.kind === 'task'">
            <div class="text-xs text-gb-muted uppercase font-semibold">Приоритет</div>
            <select
              :value="item.data.priority"
              class="mt-1 w-full rounded-lg border border-gb-border px-2 py-1.5 text-sm"
              @change="store.patchTask(item.data.id, { priority: $event.target.value })"
            >
              <option value="p0">p0</option>
              <option value="p1">p1</option>
              <option value="p2">p2</option>
              <option value="p3">p3</option>
            </select>
          </div>
          <div>
            <div class="text-xs text-gb-muted uppercase font-semibold">Владелец</div>
            <select
              :value="item.data.ownerId || ''"
              class="mt-1 w-full rounded-lg border border-gb-border px-2 py-1.5 text-sm"
              @change="patchOwner($event.target.value)"
            >
              <option value="">Не назначен</option>
              <option v-for="o in store.owners" :key="o.id" :value="o.id">{{ o.name }}</option>
            </select>
          </div>
          <div v-if="startEnd" class="grid grid-cols-2 gap-2">
            <div>
              <div class="text-xs text-gb-muted uppercase font-semibold">Начало</div>
              <div class="mt-1 font-mono text-xs">{{ startEnd.start || '—' }}</div>
            </div>
            <div>
              <div class="text-xs text-gb-muted uppercase font-semibold">Окончание</div>
              <div class="mt-1 font-mono text-xs">{{ startEnd.end || '—' }}</div>
            </div>
          </div>
          <div v-if="item.kind === 'task' && item.data.estimateDays != null">
            <div class="text-xs text-gb-muted uppercase font-semibold">Оценка, дн</div>
            <div class="mt-1">{{ item.data.estimateDays }}</div>
          </div>
          <div v-if="item.kind === 'milestone'">
            <div class="text-xs text-gb-muted uppercase font-semibold">Дата вехи</div>
            <div class="mt-1 font-mono">{{ item.data.date }}</div>
          </div>
        </div>

        <div v-show="tab === 'deps'" class="space-y-2">
          <p v-if="!relatedDeps.length" class="text-gb-muted text-xs">Нет связей для этого элемента.</p>
          <ul v-else class="space-y-2">
            <li v-for="d in relatedDeps" :key="d.id" class="rounded-lg border border-gb-border p-2 text-xs">
              <span class="font-medium text-gb-primary">{{ depLabel(d.type) }}</span>
              <div class="text-gb-muted mt-1">
                <button type="button" class="text-gb-primary hover:underline" @click="go(d.fromId)">{{ shortLabel(d.fromId) }}</button>
                →
                <button type="button" class="text-gb-primary hover:underline" @click="go(d.toId)">{{ shortLabel(d.toId) }}</button>
              </div>
            </li>
          </ul>
          <div class="pt-2 border-t border-gb-border">
            <div class="text-xs font-semibold text-gb-muted mb-1">Быстро добавить (demo)</div>
            <div class="flex flex-col gap-1">
              <select v-model="depTo" class="rounded border border-gb-border px-2 py-1 text-xs">
                <option value="">Целевой элемент…</option>
                <option v-for="opt in depTargets" :key="opt.id" :value="opt.id">{{ opt.label }}</option>
              </select>
              <select v-model="depType" class="rounded border border-gb-border px-2 py-1 text-xs">
                <option value="blocks">blocks</option>
                <option value="depends_on">depends_on</option>
                <option value="related_to">related_to</option>
              </select>
              <button
                type="button"
                class="rounded-lg bg-gb-soft border border-gb-border py-1.5 text-xs font-semibold"
                :disabled="!depTo || !item"
                @click="addDep"
              >Добавить связь</button>
            </div>
          </div>
        </div>

        <div v-show="tab === 'risks'" class="space-y-2">
          <p v-if="!relatedRisks.length" class="text-gb-muted text-xs">Риски не привязаны.</p>
          <div v-for="r in relatedRisks" :key="r.id" class="rounded-lg border border-gb-border p-2">
            <div class="font-medium text-sm">{{ r.title }}</div>
            <div class="text-xs text-gb-muted mt-1">Важность: {{ r.severity }}</div>
            <p v-if="r.mitigation" class="text-xs mt-1 text-gb-text">{{ r.mitigation }}</p>
          </div>
        </div>

        <div v-show="tab === 'comments'" class="space-y-3">
          <div v-for="c in itemComments" :key="c.id" class="rounded-lg bg-gb-soft p-2 text-xs">
            <div class="text-gb-muted mb-1">{{ authorName(c.authorId) }} · {{ formatDate(c.createdAt) }}</div>
            <div>{{ c.body }}</div>
          </div>
          <p v-if="!itemComments.length" class="text-gb-muted text-xs">Нет комментариев.</p>
        </div>

        <div v-show="tab === 'history'" class="space-y-2">
          <div v-for="a in itemActivity" :key="a.id" class="text-xs border-l-2 border-gb-border pl-2">
            <div class="text-gb-muted">{{ formatDate(a.at) }} · {{ authorName(a.actorId) }}</div>
            <div class="font-medium">{{ a.action }}</div>
            <div v-if="a.detail" class="text-gb-muted">{{ a.detail }}</div>
          </div>
          <p v-if="!itemActivity.length" class="text-gb-muted text-xs">Нет записей.</p>
        </div>
      </div>
    </template>
  </aside>
</template>

<script setup>
/* eslint-disable no-undef -- defineEmits compiler macro */
import { ref, computed, watch } from 'vue'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

const emit = defineEmits(['close'])

const store = useProjectDashboardDemoStore()
const tab = ref('overview')
const depTo = ref('')
const depType = ref('blocks')

const tabs = [
  { id: 'overview', label: 'Обзор' },
  { id: 'deps', label: 'Зависимости' },
  { id: 'risks', label: 'Риски' },
  { id: 'comments', label: 'Комментарии' },
  { id: 'history', label: 'История' }
]

const statuses = ['backlog', 'planned', 'in_progress', 'blocked', 'done', 'cancelled']

const item = computed(() => store.selectedItem)

watch(
  () => store.selectedItemId,
  () => {
    tab.value = 'overview'
    depTo.value = ''
  }
)

const title = computed(() => {
  if (!item.value) return 'Детали'
  if (item.value.kind === 'goal') return item.value.data.title
  if (item.value.kind === 'milestone') return item.value.data.title
  if (item.value.kind === 'initiative') return item.value.data.title
  if (item.value.kind === 'epic') return item.value.data.title
  return item.value.data.title
})

const workStatus = computed(() => {
  if (!item.value) return ''
  if (item.value.kind === 'task' || item.value.kind === 'epic') return item.value.data.status
  return ''
})

const startEnd = computed(() => {
  if (!item.value) return null
  if (item.value.kind === 'task' || item.value.kind === 'epic') {
    return { start: item.value.data.start, end: item.value.data.end }
  }
  return null
})

const relatedDeps = computed(() => {
  if (!item.value) return []
  const id = item.value.data.id
  return store.dependencies.filter((d) => d.fromId === id || d.toId === id)
})

const relatedRisks = computed(() => {
  if (!item.value) return []
  const id = item.value.data.id
  return store.risks.filter((r) => r.linkedItemIds.includes(id))
})

const itemComments = computed(() => {
  if (!item.value) return []
  const id = item.value.data.id
  return store.comments.filter((c) => c.itemId === id)
})

const itemActivity = computed(() => {
  if (!item.value) return []
  const id = item.value.data.id
  return store.activity.filter((a) => a.itemId === id).sort((a, b) => b.at.localeCompare(a.at))
})

const depTargets = computed(() => {
  const id = item.value?.data.id
  const out = []
  for (const e of store.epics) {
    if (e.id !== id) out.push({ id: e.id, label: `Эпик: ${e.title}` })
  }
  for (const t of store.tasks) {
    if (t.id !== id) out.push({ id: t.id, label: `Задача: ${t.title}` })
  }
  return out
})

function close() {
  emit('close')
  store.selectItem(null)
}

function go(id) {
  store.selectItem(id)
}

function shortLabel(id) {
  const t = store.tasks.find((x) => x.id === id)
  if (t) return t.title.slice(0, 32)
  const e = store.epics.find((x) => x.id === id)
  if (e) return e.title.slice(0, 32)
  return id
}

function depLabel(type) {
  const m = {
    blocks: 'Блокирует',
    depends_on: 'Зависит от',
    related_to: 'Связан',
    requires: 'Требует',
    precedes: 'Предшествует',
    follows: 'Следует'
  }
  return m[type] || type
}

function authorName(id) {
  return store.owners.find((o) => o.id === id)?.name || id
}

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString('ru-RU', { dateStyle: 'short', timeStyle: 'short' })
  } catch {
    return iso
  }
}

function patchStatus(v) {
  if (!item.value) return
  if (item.value.kind === 'task') store.patchTask(item.value.data.id, { status: v })
  if (item.value.kind === 'epic') store.patchEpic(item.value.data.id, { status: v })
}

function patchOwner(v) {
  if (!item.value) return
  const oid = v || undefined
  if (item.value.kind === 'task') store.patchTask(item.value.data.id, { ownerId: oid })
  if (item.value.kind === 'epic') store.patchEpic(item.value.data.id, { ownerId: oid })
}

function addDep() {
  if (!item.value || !depTo.value) return
  store.addDependency(item.value.data.id, depTo.value, depType.value)
  depTo.value = ''
}
</script>

<style scoped>
@media (min-width: 1024px) {
  .gb-drawer {
    position: relative;
    box-shadow: none;
  }
}
@media (max-width: 1023px) {
  .gb-drawer {
    max-height: 85vh;
    top: auto;
    bottom: 0;
    border-radius: 12px 12px 0 0;
  }
}
</style>
