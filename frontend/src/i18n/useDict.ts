import { useTranslation } from 'react-i18next'
import { en } from './en'
import { es } from './es'

/** Diccionario tipado del idioma activo. Se vuelve a renderizar al cambiar de idioma. */
export function useDict() {
  const { i18n } = useTranslation()
  return i18n.resolvedLanguage === 'es' ? es : en
}
