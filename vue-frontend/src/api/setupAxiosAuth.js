import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

/** Не считать 401 концом сессии (логин/регистрация и т.п.). */
const URLS_SKIP_SESSION_RESET = ['/login', '/register'];

function shouldIgnore401ForSessionReset(config) {
  const url = (config?.url || '').toLowerCase();
  return URLS_SKIP_SESSION_RESET.some((p) => url.includes(p));
}

function requestHadBearer(config) {
  const h = config?.headers || {};
  const direct = h.Authorization || h.authorization;
  if (direct && String(direct).startsWith('Bearer ')) return true;
  const common = axios.defaults.headers?.common;
  const cAuth = common?.Authorization || common?.authorization;
  return !!(cAuth && String(cAuth).startsWith('Bearer '));
}

/**
 * Реагирует на 401 после запроса с Bearer: чистит сессию и ведёт на /login с query.
 * Вызывать из main.js после app.use(pinia) и app.use(router).
 */
export function setupAxiosInterceptors(router) {
  let handlingSessionEnd = false;

  axios.interceptors.response.use(
    (response) => response,
    (error) => {
      const status = error.response?.status;
      const cfg = error.config || {};

      if (status !== 401 || cfg.skipSessionExpiredHandling) {
        return Promise.reject(error);
      }
      if (shouldIgnore401ForSessionReset(cfg)) {
        return Promise.reject(error);
      }
      if (!requestHadBearer(cfg)) {
        return Promise.reject(error);
      }

      if (handlingSessionEnd) {
        return Promise.reject(error);
      }
      handlingSessionEnd = true;

      try {
        const store = useAuthStore();
        store.logout();
      } catch {
        localStorage.removeItem('token');
        localStorage.removeItem('access_token');
      }

      const path = router.currentRoute?.value?.path || '';
      if (path !== '/login') {
        router
          .push({ path: '/login', query: { expired: '1' } })
          .catch(() => {})
          .finally(() => {
            setTimeout(() => {
              handlingSessionEnd = false;
            }, 300);
          });
      } else {
        handlingSessionEnd = false;
      }

      return Promise.reject(error);
    }
  );
}
