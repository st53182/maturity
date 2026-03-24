import { defineStore } from 'pinia'
import { createProjectDashboardSeed } from '@/data/project-dashboard-seed'
import type {
  DashboardFilters,
  DashboardItem,
  DashboardViewMode,
  Dependency,
  DependencyType,
  Epic,
  RoadmapGroupBy,
  SavedViewPreset,
  Task,
  WorkItemKind,
  WorkItemStatus
} from '@/types/project-dashboard'

const LS_VIEWS = 'gb-dashboard-saved-views-v1'

function defaultFilters(): DashboardFilters {
  return {
    search: '',
    ownerIds: [],
    statuses: [],
    kinds: ['epic', 'task'],
    dateFrom: null,
    dateTo: null,
    quick: null
  }
}

function loadSavedViews(): SavedViewPreset[] {
  try {
    const raw = localStorage.getItem(LS_VIEWS)
    if (!raw) return []
    const p = JSON.parse(raw)
    return Array.isArray(p) ? p : []
  } catch {
    return []
  }
}

function saveViewsToLs(views: SavedViewPreset[]) {
  try {
    localStorage.setItem(LS_VIEWS, JSON.stringify(views))
  } catch {
    /* ignore */
  }
}

function seedState() {
  return createProjectDashboardSeed()
}

export const useProjectDashboardDemoStore = defineStore('projectDashboardDemo', {
  state: () => {
    const s = seedState()
    return {
      project: s.project,
      goals: s.goals,
      milestones: s.milestones,
      initiatives: s.initiatives,
      epics: s.epics,
      tasks: s.tasks,
      dependencies: s.dependencies,
      risks: s.risks,
      owners: s.owners,
      teams: s.teams,
      comments: s.comments,
      activity: s.activity,
      selectedItemId: null as string | null,
      viewMode: 'roadmap' as DashboardViewMode,
      roadmapGroupBy: 'team' as RoadmapGroupBy,
      graphDetail: 'all' as 'all' | 'epics_only',
      filters: defaultFilters(),
      savedViews: loadSavedViews(),
      loading: false,
      error: null as string | null,
      showShortcutsModal: false,
      currentUserOwnerId: 'u-anna' as string | null
    }
  },
  getters: {
    selectedItem(state): DashboardItem | null {
      if (!state.selectedItemId) return null
      const id = state.selectedItemId
      const g = state.goals.find((x) => x.id === id)
      if (g) return { kind: 'goal', data: g }
      const m = state.milestones.find((x) => x.id === id)
      if (m) return { kind: 'milestone', data: m }
      const i = state.initiatives.find((x) => x.id === id)
      if (i) return { kind: 'initiative', data: i }
      const e = state.epics.find((x) => x.id === id)
      if (e) return { kind: 'epic', data: e }
      const t = state.tasks.find((x) => x.id === id)
      if (t) return { kind: 'task', data: t }
      return null
    },
    filteredEpics(state): Epic[] {
      return state.epics.filter((e) => matchesFilters(e, state.filters, 'epic', state.currentUserOwnerId))
    },
    filteredTasks(state): Task[] {
      return state.tasks.filter((t) => matchesFilters(t, state.filters, 'task', state.currentUserOwnerId))
    }
  },
  actions: {
    resetDemo() {
      const s = seedState()
      this.project = s.project
      this.goals = s.goals
      this.milestones = s.milestones
      this.initiatives = s.initiatives
      this.epics = s.epics
      this.tasks = s.tasks
      this.dependencies = s.dependencies
      this.risks = s.risks
      this.owners = s.owners
      this.teams = s.teams
      this.comments = s.comments
      this.activity = s.activity
      this.selectedItemId = null
      this.filters = defaultFilters()
      this.error = null
    },
    selectItem(id: string | null) {
      this.selectedItemId = id
    },
    setViewMode(mode: DashboardViewMode) {
      this.viewMode = mode
    },
    setRoadmapGroupBy(g: RoadmapGroupBy) {
      this.roadmapGroupBy = g
    },
    setGraphDetail(d: 'all' | 'epics_only') {
      this.graphDetail = d
    },
    setFilters(patch: Partial<DashboardFilters>) {
      this.filters = { ...this.filters, ...patch }
    },
    applyQuick(quick: DashboardFilters['quick']) {
      this.filters.quick = quick
    },
    setSearch(q: string) {
      this.filters.search = q
    },
    toggleShortcutsModal(v?: boolean) {
      this.showShortcutsModal = v ?? !this.showShortcutsModal
    },
    simulateLoading() {
      this.loading = true
      this.error = null
      setTimeout(() => {
        this.loading = false
      }, 650)
    },
    saveCurrentView(name: string) {
      const preset: SavedViewPreset = {
        id: `sv-${Date.now()}`,
        name,
        view: this.viewMode,
        filters: { ...this.filters }
      }
      this.savedViews = [...this.savedViews, preset]
      saveViewsToLs(this.savedViews)
    },
    applySavedView(preset: SavedViewPreset) {
      this.viewMode = preset.view
      this.filters = { ...defaultFilters(), ...preset.filters }
    },
    removeSavedView(id: string) {
      this.savedViews = this.savedViews.filter((v) => v.id !== id)
      saveViewsToLs(this.savedViews)
    },
    patchTask(id: string, patch: Partial<Task>) {
      const i = this.tasks.findIndex((t) => t.id === id)
      if (i === -1) return
      this.tasks[i] = { ...this.tasks[i], ...patch }
    },
    patchEpic(id: string, patch: Partial<Epic>) {
      const i = this.epics.findIndex((e) => e.id === id)
      if (i === -1) return
      this.epics[i] = { ...this.epics[i], ...patch }
    },
    shiftTaskDates(id: string, deltaDays: number) {
      const t = this.tasks.find((x) => x.id === id)
      if (!t || !t.start || !t.end) return
      const ns = addDaysIso(t.start, deltaDays)
      const ne = addDaysIso(t.end, deltaDays)
      this.patchTask(id, { start: ns, end: ne })
    },
    addDependency(fromId: string, toId: string, type: DependencyType) {
      const id = `d-${Date.now()}`
      const d: Dependency = {
        id,
        projectId: this.project.id,
        fromId,
        toId,
        type
      }
      this.dependencies.push(d)
    },
    addEpicQuick() {
      const id = `ep-new-${Date.now()}`
      this.epics.push({
        id,
        projectId: this.project.id,
        initiativeId: this.initiatives[0]?.id,
        title: 'Новый эпик',
        ownerId: this.currentUserOwnerId || undefined,
        status: 'backlog',
        start: this.project.period.start,
        end: this.project.period.end
      })
      this.selectedItemId = id
    },
    addTaskQuick() {
      const id = `tk-new-${Date.now()}`
      this.tasks.push({
        id,
        projectId: this.project.id,
        epicId: this.epics[0]?.id,
        title: 'Новая задача',
        ownerId: this.currentUserOwnerId || undefined,
        status: 'backlog',
        priority: 'p2',
        start: this.project.period.start,
        end: this.project.period.end,
        estimateDays: 3
      })
      this.selectedItemId = id
    },
    addMilestoneQuick() {
      const id = `ms-new-${Date.now()}`
      const t = new Date()
      const iso = t.toISOString().slice(0, 10)
      this.milestones.push({
        id,
        projectId: this.project.id,
        title: 'Новая веха',
        date: iso
      })
      this.selectedItemId = id
    },
    addRiskQuick() {
      const id = `r-new-${Date.now()}`
      this.risks.push({
        id,
        projectId: this.project.id,
        title: 'Новый риск',
        severity: 'medium',
        linkedItemIds: this.selectedItemId ? [this.selectedItemId] : []
      })
    }
  }
})

function addDaysIso(iso: string, d: number): string {
  const x = new Date(iso + 'T12:00:00')
  x.setDate(x.getDate() + d)
  return x.toISOString().slice(0, 10)
}

function matchesFilters(
  row: { id: string; title: string; ownerId?: string; status: WorkItemStatus; start?: string; end?: string },
  f: DashboardFilters,
  kind: WorkItemKind,
  currentUserId: string | null
): boolean {
  if (f.kinds.length && !f.kinds.includes(kind)) return false
  if (f.ownerIds.length && (!row.ownerId || !f.ownerIds.includes(row.ownerId))) return false
  if (f.statuses.length && !f.statuses.includes(row.status)) return false
  if (f.dateFrom && row.end && row.end < f.dateFrom) return false
  if (f.dateTo && row.start && row.start > f.dateTo) return false
  const q = f.search.trim().toLowerCase()
  if (q && !row.title.toLowerCase().includes(q) && !row.id.toLowerCase().includes(q)) return false

  if (f.quick === 'mine' && currentUserId) {
    if (row.ownerId !== currentUserId) return false
  }
  if (f.quick === 'unassigned') {
    if (row.ownerId) return false
  }
  if (f.quick === 'blocked') {
    const blocked = row.status === 'blocked'
    if (!blocked) return false
  }
  if (f.quick === 'overdue') {
    const t = new Date().toISOString().slice(0, 10)
    if (!row.end || row.end >= t) return false
    if (row.status === 'done' || row.status === 'cancelled') return false
  }
  return true
}
