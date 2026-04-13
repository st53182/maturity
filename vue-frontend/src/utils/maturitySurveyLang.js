/**
 * Параметр ?lang= для API опроса зрелости.
 * Пустой объект → сервер берёт survey_locale сессии (после менеджера) или Accept-Language.
 */
export function maturitySurveyLangParams(token, route) {
  const q = route?.query?.lang;
  if (q === 'ru' || q === 'en') return { lang: q };
  if (token) {
    try {
      const s = window.sessionStorage.getItem(`maturitySurveyLang:${token}`);
      if (s === 'ru' || s === 'en') return { lang: s };
    } catch (_) {
      /* ignore */
    }
  }
  return {};
}

export function setMaturitySurveyLangPreference(token, lang) {
  if (!token || (lang !== 'ru' && lang !== 'en')) return;
  try {
    window.sessionStorage.setItem(`maturitySurveyLang:${token}`, lang);
  } catch (_) {
    /* ignore */
  }
}
