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
  }
}

export default i18n
