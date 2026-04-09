import { createI18n } from 'vue-i18n'
import ru from './locales/ru.json'
import en from './locales/en.json'

const messages = {
  ru,
  en
}

const i18n = createI18n({
  legacy: false,
  locale: 'ru',
  fallbackLocale: 'ru',
  messages
})

if (typeof localStorage !== 'undefined') {
  const savedLanguage = localStorage.getItem('language');
  if (savedLanguage && (savedLanguage === 'ru' || savedLanguage === 'en')) {
    i18n.global.locale.value = savedLanguage;
  } else {
    // Auto-detect for first-time visitors (heuristic without IP geolocation):
    // - Russian language or Russian timezones -> ru
    // - Most European timezones -> en
    // - Otherwise fall back to browser language; default ru
    try {
      const navLang = (navigator?.language || '').toLowerCase();
      const tz = Intl.DateTimeFormat().resolvedOptions().timeZone || '';

      const russianTimeZones = new Set([
        'Europe/Moscow',
        'Europe/Kaliningrad',
        'Europe/Samara',
        'Asia/Yekaterinburg',
        'Asia/Omsk',
        'Asia/Krasnoyarsk',
        'Asia/Irkutsk',
        'Asia/Yakutsk',
        'Asia/Vladivostok',
        'Asia/Magadan',
        'Asia/Kamchatka',
        'Asia/Anadyr',
        'Asia/Novosibirsk',
        'Asia/Barnaul',
        'Asia/Tomsk',
        'Asia/Kemerovo',
        'Asia/Chita',
        'Asia/Sakhalin',
      ]);

      const isRussian = navLang.startsWith('ru') || russianTimeZones.has(tz);
      const isEurope = tz.startsWith('Europe/') && tz !== 'Europe/Moscow' && tz !== 'Europe/Kaliningrad' && tz !== 'Europe/Samara';

      if (isRussian) {
        i18n.global.locale.value = 'ru';
      } else if (isEurope) {
        i18n.global.locale.value = 'en';
      } else if (navLang.startsWith('en')) {
        i18n.global.locale.value = 'en';
      } else {
        i18n.global.locale.value = 'ru';
      }
    } catch (e) {
      // keep default
    }
  }
}

export function syncI18nFallback() {
  const loc = i18n.global.locale.value
  i18n.global.fallbackLocale.value = loc === 'en' ? 'en' : 'ru'
}

syncI18nFallback()

export default i18n
