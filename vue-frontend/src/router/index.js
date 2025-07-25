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
  {path: '/planning-poker/:roomId', name: 'PlanningPoker', component: () => import('@/views/PlanningPoker.vue')
}

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


