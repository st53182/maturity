import { createRouter, createWebHistory } from 'vue-router';
import UserLogin from '../views/UserLogin.vue';
import UserRegister from '../views/UserRegister.vue';
import UserSurvey from '../views/UserSurvey.vue';
import AssessmentResults from '../views/AssessmentResults.vue';

const routes = [
  { path: '/', redirect: '/new' },
  { path: '/new', name: 'NewHome', component: () => import('@/views/NewHome.vue') },
  { path: '/new/interview-simulator', name: 'InterviewSimulatorHome', component: () => import('@/views/InterviewSimulatorHome.vue') },
  { path: '/new/interview-simulator/setup', name: 'InterviewSimulatorSetup', component: () => import('@/views/InterviewSimulatorSetup.vue') },
  { path: '/new/interview-simulator/session', name: 'InterviewSimulatorSession', component: () => import('@/views/InterviewSimulatorSession.vue') },
  { path: '/new/interview-simulator/results', name: 'InterviewSimulatorResults', component: () => import('@/views/InterviewSimulatorResults.vue') },
  { path: '/interview-simulator', redirect: '/new/interview-simulator' },
  { path: '/new/artdash', redirect: '/new/maturity/artdash' },
  { path: '/new/maturity', name: 'NewMaturity', component: () => import('@/views/NewMaturity.vue'), meta: { requiresAuth: true } },
  { path: '/new/maturity/artdash', name: 'MaturityLinkAdminNew', component: () => import('@/views/MaturityLinkAdminDashboard.vue'), meta: { requiresAuth: true, maturityLinkAdmin: true } },
  { path: '/new/maturity/team/:teamToken', name: 'TakeMaturityTeamNew', component: () => import('@/views/TakeMaturity.vue'), props: { variant: 'new', teamSelfMode: true } },
  { path: '/new/dashboard', name: 'NewDashboard', component: () => import('@/views/NewDashboard.vue') },
  { path: '/new/survey', name: 'NewUserSurvey', component: UserSurvey, meta: { requiresAuth: true }, props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token/edit', name: 'EditMaturityNew', component: () => import('@/views/EditMaturity.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token/results', name: 'MaturityResultsNew', component: () => import('@/views/MaturityResults.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/maturity/:token', name: 'TakeMaturityNew', component: () => import('@/views/TakeMaturity.vue'), props: () => ({ variant: 'new' }) },
  { path: '/new/conflicts', name: 'NewConflicts', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'conflicts' } },
  { path: '/new/profile', name: 'NewProfile', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'profile' } },
  { path: '/new/surveys', name: 'NewSurveys', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'surveys' }, meta: { requiresAuth: true } },
  { path: '/new/chat', name: 'CommunityChat', component: () => import('@/views/CommunityChat.vue'), meta: { requiresAuth: true } },
  { path: '/new/tests', name: 'TestRunner', component: () => import('@/views/TestRunner.vue'), meta: { requiresAuth: true } },
  { path: '/new/backlog-prep', name: 'NewBacklogPrep', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'backlog-prep' }, meta: { requiresAuth: true } },
  { path: '/new/business-value', name: 'BusinessValueAssessment', component: () => import('@/views/BusinessValueAssessment.vue') },
  { path: '/new/system-thinking', name: 'NewSystemThinking', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'system-thinking' }, meta: { requiresAuth: true } },
  { path: '/new/agile-kata', name: 'NewAgileKata', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'agile-kata' }, meta: { requiresAuth: true } },
  { path: '/new/agile-tools', name: 'NewAgileTools', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'agile-tools' }, meta: { requiresAuth: true } },
  { path: '/new/meeting-design', name: 'NewMeetingDesign', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'meeting-design' }, meta: { requiresAuth: true } },
  { path: '/new/motivation', name: 'NewMotivation', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'motivation' } },
  { path: '/new/project-card', name: 'NewProjectCard', component: () => import('@/views/NewWrappedTool.vue'), props: { toolId: 'project-card' }, meta: { requiresAuth: true } },
  { path: '/new/disc-assessment', name: 'DISCAssessment', component: () => import('@/views/DISCAssessment.vue'), meta: { requiresAuth: true } },
  { path: '/new/metrics-tree', name: 'MetricsTreeNew', component: () => import('@/views/MetricsTreeView.vue'), meta: { requiresAuth: true } },
  { path: '/new/project-dashboard', name: 'ProjectDashboardDemo', component: () => import('@/views/ProjectDashboardDemo.vue') },
  { path: '/new/report-insights', name: 'ReportInsightsAnalyzer', component: () => import('@/views/ReportInsightsAnalyzer.vue'), meta: { requiresAuth: true } },
  { path: '/new/strategy-builder', name: 'StrategyBuilder', component: () => import('@/views/StrategyBuilder.vue'), meta: { requiresAuth: true } },
  { path: '/report-insights', redirect: '/new/report-insights' },
  { path: '/strategy-builder', redirect: '/new/strategy-builder' },
  /* Канон /new: редиректы со старых URL */
  { path: '/dashboard', redirect: '/new/dashboard' },
  { path: '/survey', redirect: '/new/survey' },
  { path: '/conflicts', redirect: '/new/conflicts' },
  { path: '/profile', redirect: '/new/profile' },
  { path: '/motivation', redirect: '/new/motivation' },
  { path: '/surveys', redirect: '/new/surveys' },
  { path: '/chat', redirect: '/new/chat' },
  { path: '/tests', redirect: '/new/tests' },
  { path: '/backlog-prep', redirect: '/new/backlog-prep' },
  { path: '/business-value', redirect: '/new/business-value' },
  { path: '/system-thinking', redirect: '/new/system-thinking' },
  { path: '/agile-kata', redirect: '/new/agile-kata' },
  { path: '/agile-tools', redirect: '/new/agile-tools' },
  { path: '/meeting-design', redirect: '/new/meeting-design' },
  { path: '/project-card', redirect: '/new/project-card' },
  { path: '/metrics-tree', redirect: '/new/metrics-tree' },
  { path: '/login', component: UserLogin },
  { path: '/register', component: UserRegister },
  { path: "/assessment-results/:team_id/:assessment_id", name: "AssessmentResults", component: AssessmentResults, props: true },
  { path: '/disc-assessment', redirect: '/new/disc-assessment' },
  {path: '/survey/:token', name: 'TakeSurvey', component: () => import('@/views/TakeSurvey.vue')},
  {path: '/survey/:surveyId/results', name: 'SurveyResults', component: () => import('@/views/SurveyResults.vue'), meta: { requiresAuth: true }},
  {path: '/planning-poker/:roomId', name: 'PlanningPoker', component: () => import('@/views/PlanningPoker.vue')},
  {path: '/roadmap', name: 'RoadmapList', component: () => import('@/views/RoadmapList.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/:id', name: 'DependencyRoadmap', component: () => import('@/views/DependencyRoadmap.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/shared/:token', name: 'SharedRoadmap', component: () => import('@/views/DependencyRoadmap.vue')},
  {path: '/qa', name: 'QAPractice', component: () => import('@/views/QAPractice.vue')},
  {path: '/agile-training', name: 'AgileTrainingHub', component: () => import('@/views/AgileTrainingHub.vue')},
  {path: '/agile-training/principles', name: 'AgilePrinciplesFacilitator', component: () => import('@/views/AgilePrinciplesFacilitator.vue'), meta: { requiresAuth: true }},
  {path: '/agile-training/cynefin', name: 'AgileCynefinFacilitator', component: () => import('@/views/AgileCynefinFacilitator.vue'), meta: { requiresAuth: true }},
  {path: '/agile-training/iceberg', name: 'AgileIcebergFacilitator', component: () => import('@/views/AgileIcebergFacilitator.vue'), meta: { requiresAuth: true }},
  {path: '/agile-training/mvp', name: 'AgileMvpFacilitator', component: () => import('@/views/AgileMvpFacilitator.vue'), meta: { requiresAuth: true }},
  {path: '/g/:slug', name: 'GroupPlay', component: () => import('@/views/GroupPlayGateway.vue')},
  {path: '/testing-types', name: 'TestingTypesAssignment', component: () => import('@/views/TestingTypesAssignment.vue'), meta: { requiresAuth: true }},
  {path: '/usability-report', name: 'UsabilityReport', component: () => import('@/views/UsabilityReport.vue'), meta: { requiresAuth: true }},
  {path: '/qa/user-story', name: 'QAUserStoryAssignment', component: () => import('@/views/QAUserStoryAssignment.vue')},
  {path: '/qa/test-plan', name: 'QATestPlanAssignment', component: () => import('@/views/QATestPlanAssignment.vue'), meta: { requiresAuth: true }},
  {path: '/qa/test-case', name: 'QATestCaseAssignment', component: () => import('@/views/QATestCaseAssignment.vue') },
  {path: '/qa/sql', name: 'QASqlPractice', component: () => import('@/views/QASqlPractice.vue') },
  { path: '/maturity/artdash', name: 'MaturityLinkAdminDashboard', component: () => import('@/views/MaturityLinkAdminDashboard.vue'), meta: { requiresAuth: true, maturityLinkAdmin: true } },
  { path: '/maturity/team/:teamToken', redirect: (to) => `/new/maturity/team/${to.params.teamToken}` },
  { path: '/maturity/create', redirect: '/new/maturity' },
  { path: '/maturity/:token/edit', redirect: to => `/new/maturity/${to.params.token}/edit` },
  { path: '/maturity/:token/results', redirect: to => `/new/maturity/${to.params.token}/results` },
  { path: '/maturity/:token', redirect: to => `/new/maturity/${to.params.token}` },
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


