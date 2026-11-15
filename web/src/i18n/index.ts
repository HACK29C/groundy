import i18n from 'i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import { initReactI18next } from 'react-i18next'
import { en } from './en'
import { es } from './es'

// Inglés por defecto (regla del evento). El idioma elegido se recuerda en el navegador; ?lang=es también funciona.
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, es: { translation: es } },
    fallbackLng: 'en',
    supportedLngs: ['en', 'es'],
    nonExplicitSupportedLngs: true,
    detection: { order: ['querystring', 'localStorage'], lookupQuerystring: 'lang', caches: ['localStorage'] },
    interpolation: { escapeValue: false },
    returnObjects: true,
  })

const syncHtmlLang = (lng: string) => {
  document.documentElement.lang = lng.startsWith('es') ? 'es' : 'en'
}
syncHtmlLang(i18n.resolvedLanguage ?? 'en')
i18n.on('languageChanged', syncHtmlLang)

export const toggleLanguage = () => i18n.changeLanguage(i18n.resolvedLanguage === 'es' ? 'en' : 'es')

export default i18n
