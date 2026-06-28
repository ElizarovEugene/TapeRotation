import { createContext, useContext, useEffect, type ReactNode } from 'react'
import { useAuth } from '../auth/AuthContext'
import { translations, type Lang, type TranslationKey } from './translations'

interface I18nContextValue {
  t: (key: TranslationKey, vars?: Record<string, string | number>) => string
  lang: Lang
}

const I18nContext = createContext<I18nContextValue>(null!)

export function I18nProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const lang = (user?.language ?? localStorage.getItem('lang') ?? 'en') as Lang

  useEffect(() => {
    if (user?.language) localStorage.setItem('lang', user.language)
  }, [user?.language])

  const t = (key: TranslationKey, vars?: Record<string, string | number>): string => {
    const dict = translations[lang] ?? translations.ru
    let str: string = dict[key] ?? translations.ru[key] ?? key
    if (vars) {
      for (const [k, v] of Object.entries(vars)) {
        str = str.replace(`{${k}}`, String(v))
      }
    }
    return str
  }

  return <I18nContext.Provider value={{ t, lang }}>{children}</I18nContext.Provider>
}

export const useI18n = () => useContext(I18nContext)
