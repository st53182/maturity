import { createI18n } from 'vue-i18n'
import ru from './locales/ru.json'
import en from './locales/en.json'

const messages = {
  ru,
  en
}

const i18n = createI18n({
  legacy: false,
  locale: (typeof localStorage !== 'undefined' && localStorage.getItem('language')) || 'ru',
  fallbackLocale: 'ru',
  messages
})

export default i18n
