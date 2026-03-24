export type WorkItemStatus =
  | 'backlog'
  | 'planned'
  | 'in_progress'
  | 'blocked'
  | 'done'
  | 'cancelled'

export type DependencyType =
  | 'blocks'
  | 'depends_on'
  | 'related_to'
  | 'requires'
  | 'precedes'
  | 'follows'

export type DashboardViewMode = 'roadmap' | 'dependencies' | 'table' | 'timeline'

export type RoadmapGroupBy = 'team' | 'owner' | 'kind'

export interface Owner {
  id: string
  name: string
  avatarUrl?: string
  teamId?: string
}

export interface Team {
  id: string
  name: string
}

export interface Project {
  id: string
  name: string
  description?: string
  period: { start: string; end: string }
  teamIds: string[]
}

export interface Goal {
  id: string
  projectId: string
  title: string
  targetDate?: string
}

export interface Milestone {
  id: string
  projectId: string
  title: string
  date: string
}

export interface Initiative {
  id: string
  projectId: string
  goalId?: string
  title: string
}

export interface Epic {
  id: string
  projectId: string
  initiativeId?: string
  title: string
  ownerId?: string
  status: WorkItemStatus
  start?: string
  end?: string
}

export interface Task {
  id: string
  projectId: string
  epicId?: string
  title: string
  ownerId?: string
  status: WorkItemStatus
  priority: 'p0' | 'p1' | 'p2' | 'p3'
  start?: string
  end?: string
  estimateDays?: number
}

export interface Dependency {
  id: string
  projectId: string
  fromId: string
  toId: string
  type: DependencyType
}

export interface Risk {
  id: string
  projectId: string
  title: string
  severity: 'low' | 'medium' | 'high'
  linkedItemIds: string[]
  mitigation?: string
}

export interface Comment {
  id: string
  itemId: string
  authorId: string
  body: string
  createdAt: string
}

export interface ActivityEvent {
  id: string
  itemId: string
  at: string
  actorId: string
  action: string
  detail?: string
}

export type WorkItemKind = 'goal' | 'milestone' | 'initiative' | 'epic' | 'task'

export type DashboardItem =
  | { kind: 'goal'; data: Goal }
  | { kind: 'milestone'; data: Milestone }
  | { kind: 'initiative'; data: Initiative }
  | { kind: 'epic'; data: Epic }
  | { kind: 'task'; data: Task }

export interface DashboardState {
  project: Project
  goals: Goal[]
  milestones: Milestone[]
  initiatives: Initiative[]
  epics: Epic[]
  tasks: Task[]
  dependencies: Dependency[]
  risks: Risk[]
  owners: Owner[]
  teams: Team[]
  comments: Comment[]
  activity: ActivityEvent[]
}

export interface DashboardFilters {
  search: string
  ownerIds: string[]
  statuses: WorkItemStatus[]
  kinds: WorkItemKind[]
  dateFrom: string | null
  dateTo: string | null
  quick: null | 'mine' | 'overdue' | 'blocked' | 'unassigned'
}

export interface SavedViewPreset {
  id: string
  name: string
  view: DashboardViewMode
  filters: DashboardFilters
}
