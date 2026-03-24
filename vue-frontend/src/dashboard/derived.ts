import type {
  DashboardState,
  Dependency,
  Epic,
  Milestone,
  Task,
  WorkItemStatus
} from '@/types/project-dashboard'

const TERMINAL: WorkItemStatus[] = ['done', 'cancelled']

export function isTerminalStatus(s: WorkItemStatus): boolean {
  return TERMINAL.includes(s)
}

export function progressPercentFromTasks(tasks: Task[]): number {
  if (!tasks.length) return 0
  const done = tasks.filter((t) => t.status === 'done').length
  return Math.round((100 * done) / tasks.length)
}

export function overdueCount(state: DashboardState, todayIso: string): number {
  let n = 0
  for (const t of state.tasks) {
    if (t.end && t.end < todayIso && !isTerminalStatus(t.status)) n++
  }
  for (const e of state.epics) {
    if (e.end && e.end < todayIso && !isTerminalStatus(e.status)) n++
  }
  return n
}

/** Блокирующие зависимости: есть входящее `blocks` от работы, которая ещё не завершена */
export function blockedByDependencyCount(state: DashboardState): number {
  const incomplete = new Set<string>()
  for (const t of state.tasks) {
    if (!isTerminalStatus(t.status)) incomplete.add(t.id)
  }
  for (const e of state.epics) {
    if (!isTerminalStatus(e.status)) incomplete.add(e.id)
  }
  const blockedTargets = new Set<string>()
  for (const d of state.dependencies) {
    if (d.type !== 'blocks') continue
    if (incomplete.has(d.fromId)) blockedTargets.add(d.toId)
  }
  let count = 0
  for (const id of blockedTargets) {
    const t = state.tasks.find((x) => x.id === id)
    const e = state.epics.find((x) => x.id === id)
    const st = t?.status ?? e?.status
    if (st && !isTerminalStatus(st)) count++
  }
  return count
}

export function statusBlockedCount(state: DashboardState): number {
  let n = 0
  for (const t of state.tasks) if (t.status === 'blocked') n++
  for (const e of state.epics) if (e.status === 'blocked') n++
  return n
}

export function unassignedWorkCount(state: DashboardState): number {
  let n = 0
  for (const t of state.tasks) {
    if (!t.ownerId && !isTerminalStatus(t.status)) n++
  }
  for (const e of state.epics) {
    if (!e.ownerId && !isTerminalStatus(e.status)) n++
  }
  return n
}

export function upcomingMilestones(state: DashboardState, todayIso: string, limit = 4): Milestone[] {
  return [...state.milestones]
    .filter((m) => m.date >= todayIso)
    .sort((a, b) => a.date.localeCompare(b.date))
    .slice(0, limit)
}

function nodeWeight(id: string, tasks: Task[], epics: Epic[]): number {
  const t = tasks.find((x) => x.id === id)
  if (t?.estimateDays != null) return Math.max(1, t.estimateDays)
  return 1
}

/**
 * Критический путь по рёбрам `blocks` (DAG). Вес ребра = длительность предшественника.
 */
export function computeCriticalPath(
  deps: Dependency[],
  tasks: Task[],
  epics: Epic[]
): { nodeIds: Set<string>; hasCycle: boolean } {
  const blocks = deps.filter((d) => d.type === 'blocks')
  const nodes = new Set<string>()
  for (const e of blocks) {
    nodes.add(e.fromId)
    nodes.add(e.toId)
  }
  if (nodes.size === 0) return { nodeIds: new Set(), hasCycle: false }

  const adj = new Map<string, string[]>()
  const indegree = new Map<string, number>()
  for (const n of nodes) {
    indegree.set(n, 0)
    adj.set(n, [])
  }
  for (const e of blocks) {
    if (!nodes.has(e.fromId) || !nodes.has(e.toId)) continue
    adj.get(e.fromId)!.push(e.toId)
    indegree.set(e.toId, (indegree.get(e.toId) || 0) + 1)
  }

  const q: string[] = []
  for (const [n, d] of indegree) if (d === 0) q.push(n)
  const order: string[] = []
  while (q.length) {
    const u = q.shift()!
    order.push(u)
    for (const v of adj.get(u) || []) {
      indegree.set(v, indegree.get(v)! - 1)
      if (indegree.get(v) === 0) q.push(v)
    }
  }
  if (order.length !== nodes.size) return { nodeIds: new Set(), hasCycle: true }

  const dist = new Map<string, number>()
  for (const n of nodes) dist.set(n, 0)
  for (const u of order) {
    const du = dist.get(u) || 0
    for (const v of adj.get(u) || []) {
      const cand = du + nodeWeight(u, tasks, epics)
      if (cand > (dist.get(v) || 0)) dist.set(v, cand)
    }
  }

  let end = [...nodes][0]
  let best = dist.get(end) || 0
  for (const n of nodes) {
    const d = dist.get(n) || 0
    if (d >= best) {
      best = d
      end = n
    }
  }

  const path = new Set<string>()
  path.add(end)
  let cur = end
  for (let guard = 0; guard < nodes.size + 2; guard++) {
    let pred: string | null = null
    let bestDp = -Infinity
    const curDist = dist.get(cur) || 0
    for (const e of blocks) {
      if (e.toId !== cur) continue
      const p = e.fromId
      if (!nodes.has(p)) continue
      const dp = dist.get(p) || 0
      const w = nodeWeight(p, tasks, epics)
      if (Math.abs(dp + w - curDist) < 1e-6 && dp >= bestDp) {
        bestDp = dp
        pred = p
      }
    }
    if (pred == null) break
    path.add(pred)
    cur = pred
  }
  return { nodeIds: path, hasCycle: false }
}

export function getProblematicNodeIds(state: DashboardState, todayIso: string): Set<string> {
  const s = new Set<string>()
  for (const t of state.tasks) {
    if (t.status === 'blocked') s.add(t.id)
    if (t.end && t.end < todayIso && !isTerminalStatus(t.status)) s.add(t.id)
    if (!t.ownerId && !isTerminalStatus(t.status)) s.add(t.id)
  }
  for (const e of state.epics) {
    if (e.status === 'blocked') s.add(e.id)
    if (e.end && e.end < todayIso && !isTerminalStatus(e.status)) s.add(e.id)
    if (!e.ownerId && !isTerminalStatus(e.status)) s.add(e.id)
  }
  return s
}

export interface DashboardDerived {
  progressPercent: number
  overdueCount: number
  blockedByDepsCount: number
  statusBlockedCount: number
  unassignedCount: number
  upcomingMilestones: Milestone[]
  criticalPathNodeIds: Set<string>
  criticalPathHasCycle: boolean
  problematicNodeIds: Set<string>
}

export function computeDashboardDerived(
  state: DashboardState,
  todayIso: string
): DashboardDerived {
  const cp = computeCriticalPath(state.dependencies, state.tasks, state.epics)
  return {
    progressPercent: progressPercentFromTasks(state.tasks),
    overdueCount: overdueCount(state, todayIso),
    blockedByDepsCount: blockedByDependencyCount(state),
    statusBlockedCount: statusBlockedCount(state),
    unassignedCount: unassignedWorkCount(state),
    upcomingMilestones: upcomingMilestones(state, todayIso),
    criticalPathNodeIds: cp.nodeIds,
    criticalPathHasCycle: cp.hasCycle,
    problematicNodeIds: getProblematicNodeIds(state, todayIso)
  }
}
