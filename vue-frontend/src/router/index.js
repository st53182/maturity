import { createRouter, createWebHistory } from 'vue-router';
import UserHome from '../views/UserHome.vue';
import UserLogin from '../views/UserLogin.vue';
import UserRegister from '../views/UserRegister.vue';
import UserSurvey from '../views/UserSurvey.vue';
import UserDashboard from '../views/UserDashboard.vue';
import AssessmentResults from '../views/AssessmentResults.vue';

const routes = [
  { path: '/', component: UserHome },
  { path: '/login', component: UserLogin },
  { path: '/register', component: UserRegister },
  { path: '/survey', name: "UserSurvey", component: UserSurvey, meta: { requiresAuth: true } },
  { path: '/dashboard', component: UserDashboard },
  { path: "/assessment-results/:team_id/:assessment_id", name: "AssessmentResults", component: AssessmentResults, props: true },
  {path: '/conflicts', name: 'Conflicts', component: () => import('@/views/ConflictResolution.vue') },
  {path: '/motivation', name: 'Motivation', component: () => import('@/views/UserMotivation.vue')},
  {path: "/profile", name: "UserProfile", component: () => import("@/views/UserProfile.vue")},
  {path: '/disc-assessment', name: 'DISCAssessment', component: () => import('@/views/DISCAssessment.vue'), meta: { requiresAuth: true }},
  {path: '/meeting-design', name: 'MeetingDesign', component: () => import('@/views/MeetingDesign.vue'), meta: { requiresAuth: true }},
  {path: '/surveys', name: 'Surveys', component: () => import('@/views/Surveys.vue'), meta: { requiresAuth: true }},
  {path: '/survey/:token', name: 'TakeSurvey', component: () => import('@/views/TakeSurvey.vue')},
  {path: '/survey/:surveyId/results', name: 'SurveyResults', component: () => import('@/views/SurveyResults.vue'), meta: { requiresAuth: true }},
  {path: '/planning-poker/:roomId', name: 'PlanningPoker', component: () => import('@/views/PlanningPoker.vue')},
  {path: '/backlog-prep', name: 'BacklogPrep', component: () => import('@/views/BacklogPrep.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap', name: 'RoadmapList', component: () => import('@/views/RoadmapList.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/:id', name: 'DependencyRoadmap', component: () => import('@/views/DependencyRoadmap.vue'), meta: { requiresAuth: true }},
  {path: '/roadmap/shared/:token', name: 'SharedRoadmap', component: () => import('@/views/DependencyRoadmap.vue')},
  {path: '/system-thinking', name: 'SystemThinking', component: () => import('@/views/SystemThinkingIceberg.vue'), meta: { requiresAuth: true }},
  {path: '/qa', name: 'QAPractice', component: () => import('@/views/QAPractice.vue')},
  {path: '/project-card', name: 'ProjectManagementCard', component: () => import('@/views/ProjectManagementCard.vue'), meta: { requiresAuth: true }},
  {path: '/testing-types', name: 'TestingTypesAssignment', component: () => import('@/views/TestingTypesAssignment.vue'), meta: { requiresAuth: true }},
  {path: '/usability-report', name: 'UsabilityReport', component: () => import('@/views/UsabilityReport.vue'), meta: { requiresAuth: true }},
  { path: '/maturity/create', name: 'CreateMaturityLink', component: () => import('@/views/CreateMaturityLink.vue'), meta: { requiresAuth: true } },
  { path: '/maturity/:token', name: 'TakeMaturity', component: () => import('@/views/TakeMaturity.vue') },
  { path: '/maturity/:token/results', name: 'MaturityResults', component: () => import('@/views/MaturityResults.vue') },
  { path: '/flow-metrics', name: 'FlowMetricsDashboard', component: () => import('@/views/FlowMetricsDashboard.vue') },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

// 🔹 Перехват маршрутов: перенаправление на логин, если пользователь не авторизован
router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('token');

  if (to.meta.requiresAuth && !isAuthenticated) {
    next('/login'); // 🔄 Если не авторизован, отправляем на страницу логина
  } else {
    next();
  }
});

export default router;


