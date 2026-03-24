import { createRouter, createWebHistory } from 'vue-router';
import UserLogin from '../views/UserLogin.vue';
import UserRegister from '../views/UserRegister.vue';
import UserSurvey from '../views/UserSurvey.vue';
import AssessmentResults from '../views/AssessmentResults.vue';

const routes = [
  { path: '/', redirect: '/new' },
  { path: '/new', name: 'NewHome', component: () => import('@/views/NewHome.vue') },
  { path: '/new/artdash', redirect: '/new/maturity/artdash' },
  { path: '/new/maturity', name: 'NewMaturity', component: () => import('@/views/NewMaturity.vue'), meta: { requiresAuth: true } },
  { path: '/new/maturity/artdash', name: 'MaturityLinkAdminNew', component: () => import('@/views/MaturityLinkAdminDashboard.vue'), meta: { requiresAuth: true, maturityLinkAdmin: true } },
  { path: '/new/dashboard', name: 'NewDashboard', component: () => import('@/views/NewDashboard.vue') },
  { path: '/new/survey', name: 'NewUserSurvey', component: UserSurvey, meta: { requiresAuth: true }, props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token/edit', name: 'EditMaturityNew', component: () => import('@/views/EditMaturity.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token/results', name: 'MaturityResultsNew', component: () => import('@/views/MaturityResults.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token', name: 'TakeMaturityNew', component: () => import('@/views/TakeMaturity.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/conflicts', name: 'NewConflicts', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'conflicts' } },
  { path: '/new/profile', name: 'NewProfile', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'profile' } },
  { path: '/new/surveys', name: 'NewSurveys', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'surveys' }, meta: { requiresAuth: true } },
  { path: '/new/backlog-prep', name: 'NewBacklogPrep', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'backlog-prep' }, meta: { requiresAuth: true } },
  { path: '/new/system-thinking', name: 'NewSystemThinking', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'system-thinking' }, meta: { requiresAuth: true } },
  { path: '/new/meeting-design', name: 'NewMeetingDesign', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'meeting-design' }, meta: { requiresAuth: true } },
  { path: '/new/motivation', name: 'NewMotivation', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'motivation' } },
  { path: '/new/project-card', name: 'NewProjectCard', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'project-card' }, meta: { requiresAuth: true } },
  /* Канон /new: редиректы со старых URL */
  { path: '/dashboard', redirect: '/new/dashboard' },
  { path: '/survey', redirect: '/new/survey' },
  { path: '/conflicts', redirect: '/new/conflicts' },
  { path: '/profile', redirect: '/new/profile' },
  { path: '/motivation', redirect: '/new/motivation' },
  { path: '/surveys', redirect: '/new/surveys' },
  { path: '/backlog-prep', redirect: '/new/backlog-prep' },
  { path: '/system-thinking', redirect: '/new/system-thinking' },
  { path: '/meeting-design', redirect: '/new/meeting-design' },
  { path: '/project-card', redirect: '/new/project-card' },
  { path: '/login', component: UserLogin },
  { path: '/register', component: UserRegister },
  { path: "/assessment-results/:team_id/:assessment_id", name: "AssessmentResults", component: AssessmentResults, props: true },
  {path: '/disc-assessment', name: 'DISCAssessment', component: () => import('@/views/DISCAssessment.vue'), meta: { requiresAuth: true }},
  {path: '/survey/:token', name: 'TakeSurvey', component: () => import('@/views/TakeSurvey.vue')},
  {path: '/survey/:surveyId/results', name: 'SurveyResults', component: () => import('@/views/SurveyResults.vue'), meta: { requiresAuth: true }},
  {path: '/planning-poker/:roomId', name: 'PlanningPoker', component: () => import('@/views/PlanningPoker.vue')},
  {path: '/roadmap', name: 'RoadmapList', component: () => import('@/views/RoadmapList.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/:id', name: 'DependencyRoadmap', component: () => import('@/views/DependencyRoadmap.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/shared/:token', name: 'SharedRoadmap', component: () => import('@/views/DependencyRoadmap.vue')},
  {path: '/qa', name: 'QAPractice', component: () => import('@/views/QAPractice.vue')},
  {path: '/testing-types', name: 'TestingTypesAssignment', component: () => import('@/views/TestingTypesAssignment.vue'), meta: { requiresAuth: true }},
  {path: '/usability-report', name: 'UsabilityReport', component: () => import('@/views/UsabilityReport.vue'), meta: { requiresAuth: true }},
  {path: '/qa/user-story', name: 'QAUserStoryAssignment', component: () => import('@/views/QAUserStoryAssignment.vue')},
  { path: '/maturity/artdash', name: 'MaturityLinkAdminDashboard', component: () => import('@/views/MaturityLinkAdminDashboard.vue'), meta: { requiresAuth: true, maturityLinkAdmin: true } },
  { path: '/maturity/create', redirect: '/new/maturity' },
  { path: '/maturity/:token/edit', redirect: to => `/new/maturity/${to.params.token}/edit` },
  { path: '/maturity/:token/results', redirect: to => `/new/maturity/${to.params.token}/results` },
  { path: '/maturity/:token', redirect: to => `/new/maturity/${to.params.token}` },
  { path: '/flow-metrics', name: 'FlowMetricsDashboard', component: () => import('@/views/FlowMetricsDashboard.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 🔹 Доступ к maturity admin: только requiresAuth; allowlist проверяется на API (без пересборки фронта).
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('token');

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login');
    return;
  }

  next();
});

export default router;


