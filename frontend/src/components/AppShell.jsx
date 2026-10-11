import { useLanguage, useT } from '../lib/i18n'
import { useTheme } from '../lib/theme'
import OfflineBanner from './OfflineBanner'

export default function AppShell({ children, activePage = 'home', onNavigate }) {
  const { language, setLanguage, languages } = useLanguage()
  const { isDark, toggleTheme } = useTheme()
  const t = useT()

  const navItems = [
    { id: 'home', label: t('nav.home', 'Home'), icon: '🏠' },
    { id: 'learn', label: t('nav.learn', 'Learn'), icon: '📚' },
    { id: 'quiz', label: t('nav.quiz', 'Quiz'), icon: '🎯' },
    { id: 'progress', label: t('nav.progress', 'Progress'), icon: '📊' },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 text-gray-900 dark:text-gray-100 flex flex-col font-sans transition-colors duration-200">
      {/* Offline Alert Banner */}
      <OfflineBanner />

      {/* Top Header Bar */}
      <header className="sticky top-0 z-30 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-b border-gray-200 dark:border-gray-800 transition-colors">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
          {/* Logo / Brand */}
          <div
            onClick={() => onNavigate && onNavigate('home')}
            className="flex items-center gap-2.5 cursor-pointer select-none"
          >
            <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20 text-white select-none">
              <span
                className="text-base font-bold italic tracking-tighter"
                style={{ fontFamily: "'Dancing Script', 'Brush Script MT', 'Great Vibes', 'Caveat', cursive, sans-serif", transform: 'translateY(-1px)' }}
              >
                <span className="text-lg">ℰ</span><span className="text-sm font-semibold">ℓ</span>
              </span>
            </div>
            <span className="text-lg sm:text-xl font-black bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
              EzLearn
            </span>
          </div>

          {/* Controls: Language Dropdown & Theme Toggle */}
          <div className="flex items-center gap-3">
            {/* Language Switcher */}
            <div className="relative">
              <label htmlFor="language-select" className="sr-only">
                {t('language.label', 'Language')}
              </label>
              <select
                id="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="min-h-[44px] px-3 py-2 bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 text-sm font-semibold rounded-xl border border-gray-200 dark:border-gray-700 hover:border-indigo-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-colors cursor-pointer"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>

            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
              className="min-h-[44px] min-w-[44px] flex items-center justify-center p-2.5 rounded-xl bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 dark:hover:bg-gray-700 text-gray-800 dark:text-gray-200 border border-gray-200 dark:border-gray-700 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500"
            >
              <span className="text-xl" aria-hidden="true">
                {isDark ? '☀️' : '🌙'}
              </span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Container: Sidebar (Desktop) + Content Area */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Desktop Sidebar (md+) */}
        <aside className="hidden md:flex flex-col w-64 p-4 border-r border-gray-200 dark:border-gray-800 shrink-0">
          <nav aria-label="Main Navigation" className="space-y-1 sticky top-20">
            {navItems.map((item) => {
              const isActive = activePage === item.id
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onNavigate && onNavigate(item.id)}
                  className={`w-full flex items-center gap-3.5 px-4 py-3 rounded-2xl text-base font-bold min-h-[44px] transition-all text-left ${
                    isActive
                      ? 'bg-indigo-600 text-white shadow-md shadow-indigo-500/20'
                      : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800/80 hover:text-gray-900 dark:hover:text-white'
                  }`}
                >
                  <span className="text-xl" aria-hidden="true">{item.icon}</span>
                  <span>{item.label}</span>
                </button>
              )
            })}
          </nav>
        </aside>

        {/* Content Area */}
        <main className="flex-1 pb-24 md:pb-8 px-4 sm:px-6 py-6 overflow-x-hidden min-w-0 flex flex-col justify-between">
          <div>{children}</div>
          <footer className="text-center text-[11px] text-gray-400 dark:text-gray-500 font-medium pt-8 pb-2 select-none">
            Created by Arya Mandavgane for AIMPACT
          </footer>
        </main>
      </div>

      {/* Mobile Bottom Navigation Bar (hidden on md+) */}
      <nav
        aria-label="Mobile Navigation"
        className="md:hidden fixed bottom-0 left-0 right-0 z-30 bg-white/95 dark:bg-gray-900/95 backdrop-blur-md border-t border-gray-200 dark:border-gray-800 px-2 py-1 safe-area-pb"
      >
        <div className="flex items-center justify-around">
          {navItems.map((item) => {
            const isActive = activePage === item.id
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onNavigate && onNavigate(item.id)}
                className={`flex flex-col items-center justify-center min-h-[48px] min-w-[56px] px-2 py-1 rounded-xl transition-all ${
                  isActive
                    ? 'text-indigo-600 dark:text-indigo-400 font-bold scale-105'
                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200 font-medium'
                }`}
              >
                <span className="text-xl" aria-hidden="true">{item.icon}</span>
                <span className="text-xs mt-0.5 tracking-tight">{item.label}</span>
              </button>
            )
          })}
        </div>
      </nav>
    </div>
  )
}
