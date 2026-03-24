import { computed } from 'vue'
import { computeDashboardDerived } from '@/dashboard/derived'
import type { DashboardState } from '@/types/project-dashboard'
import { useProjectDashboardDemoStore } from '@/stores/projectDashboardDemo'

function toState(store: ReturnType<typeof useProjectDashboardDemoStore>): DashboardState {
  return {
    project: store.project,
    goals: store.goals,
    milestones: store.milestones,
    initiatives: store.initiatives,
    epics: store.epics,
    tasks: store.tasks,
    dependencies: store.dependencies,
    risks: store.risks,
    owners: store.owners,
    teams: store.teams,
    comments: store.comments,
    activity: store.activity
  }
}

export function useProjectDashboardDerived() {
  const store = useProjectDashboardDemoStore()
  const todayIso = () => new Date().toISOString().slice(0, 10)

  const derived = computed(() => computeDashboardDerived(toState(store), todayIso()))

  return { derived }
}
