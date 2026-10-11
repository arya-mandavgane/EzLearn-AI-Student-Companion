import { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react'
import en from '../locales/en.json'
import hi from '../locales/hi.json'
import mr from '../locales/mr.json'

const translations = { en, hi, mr }

export const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी' },
  { code: 'mr', label: 'मराठी' },
]

const LanguageContext = createContext(null)

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      const saved = localStorage.getItem('asc_lang')
      if (saved && translations[saved]) return saved
    } catch {
      // ignore localStorage errors
    }
    return 'en'
  })

  const setLanguage = useCallback((lang) => {
    if (translations[lang]) {
      setLanguageState(lang)
      try {
        localStorage.setItem('asc_lang', lang)
      } catch {
        // ignore localStorage errors
      }
    }
  }, [])

  // Resolve nested dot-notation key
  const t = useCallback((key, fallback) => {
    if (!key) return ''
    const keys = key.split('.')
    
    // Check current language
    let current = translations[language]
    for (const k of keys) {
      if (current && typeof current === 'object' && k in current) {
        current = current[k]
      } else {
        current = undefined
        break
      }
    }

    if (typeof current === 'string') return current

    // Fallback to English
    if (language !== 'en') {
      let fallbackVal = translations.en
      for (const k of keys) {
        if (fallbackVal && typeof fallbackVal === 'object' && k in fallbackVal) {
          fallbackVal = fallbackVal[k]
        } else {
          fallbackVal = undefined
          break
        }
      }
      if (typeof fallbackVal === 'string') return fallbackVal
    }

    return fallback ?? key
  }, [language])

  const value = useMemo(() => ({
    language,
    setLanguage,
    languages: LANGUAGES,
    t,
  }), [language, setLanguage, t])

  return (
    <LanguageContext.Provider value={value}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider')
  }
  return context
}

export function useT() {
  const { t } = useLanguage()
  return t
}
