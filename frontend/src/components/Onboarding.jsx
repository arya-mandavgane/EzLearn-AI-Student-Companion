import { useState, useEffect } from 'react'
import { useT } from '../lib/i18n'

export default function Onboarding({ forceShow = false, onClose }) {
  const t = useT()
  const [isOpen, setIsOpen] = useState(false)
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    if (forceShow) {
      setIsOpen(true)
      return
    }
    try {
      const onboarded = localStorage.getItem('asc_onboarded')
      if (onboarded !== 'true') {
        setIsOpen(true)
      }
    } catch {
      setIsOpen(true)
    }
  }, [forceShow])

  if (!isOpen) return null

  const screens = [
    {
      emoji: '📝',
      title: t('onboarding.screen1_title', 'Turn any notes into simple explanations'),
      body: t('onboarding.screen1_body', "Paste text, upload a PDF or photo, or record your voice. We'll convert it all to text for you."),
    },
    {
      emoji: '🎯',
      title: t('onboarding.screen2_title', 'Test yourself with instant quizzes'),
      body: t('onboarding.screen2_body', "After reading the explanation, take a quick quiz. We'll track which topics you need to review."),
    },
    {
      emoji: '🥞',
      title: t('onboarding.screen3_title', 'Practice with interactive simulations'),
      body: t('onboarding.screen3_body', 'See data structures like Stack and Queue come to life with step-by-step animations.'),
    },
  ]

  const isLast = currentStep === screens.length - 1

  function handleFinish() {
    try {
      localStorage.setItem('asc_onboarded', 'true')
    } catch {
      // ignore
    }
    setIsOpen(false)
    if (onClose) onClose()
  }

  function handleNext() {
    if (isLast) {
      handleFinish()
    } else {
      setCurrentStep((prev) => prev + 1)
    }
  }

  function handleSkip() {
    handleFinish()
  }

  const current = screens[currentStep]

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm transition-opacity"
      role="dialog"
      aria-modal="true"
      aria-label="Welcome Tour"
    >
      <div className="bg-white dark:bg-gray-800 rounded-3xl max-w-md w-full p-6 sm:p-8 shadow-2xl border border-gray-100 dark:border-gray-700 flex flex-col justify-between motion-safe:transition-all">
        {/* Top bar with step indicators & close/skip */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            {screens.map((_, idx) => (
              <span
                key={idx}
                className={`h-2.5 rounded-full transition-all duration-300 ${
                  idx === currentStep
                    ? 'w-8 bg-indigo-600 dark:bg-indigo-400'
                    : 'w-2.5 bg-gray-200 dark:bg-gray-700'
                }`}
                aria-label={`Step ${idx + 1}`}
              />
            ))}
          </div>
          {!isLast && (
            <button
              type="button"
              onClick={handleSkip}
              className="text-base font-semibold text-gray-500 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-200 min-h-[44px] min-w-[44px] px-2 py-1"
            >
              {t('onboarding.skip', 'Skip')}
            </button>
          )}
        </div>

        {/* Content */}
        <div className="text-center my-6 space-y-4">
          <div
            className="text-6xl sm:text-7xl mb-4 select-none"
            aria-hidden="true"
          >
            {current.emoji}
          </div>
          <h2 className="text-xl sm:text-2xl font-bold text-gray-900 dark:text-white leading-snug">
            {current.title}
          </h2>
          <p className="text-base text-gray-600 dark:text-gray-300 leading-relaxed max-w-sm mx-auto">
            {current.body}
          </p>
        </div>

        {/* Bottom actions */}
        <div className="mt-6 pt-4 border-t border-gray-100 dark:border-gray-700 flex gap-3">
          {currentStep > 0 && (
            <button
              type="button"
              onClick={() => setCurrentStep((prev) => prev - 1)}
              className="min-h-[44px] px-5 py-2.5 rounded-xl border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 font-semibold text-base hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              {t('common.back', 'Back')}
            </button>
          )}
          <button
            type="button"
            onClick={handleNext}
            className="flex-1 min-h-[44px] px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 text-white font-bold text-base transition-colors shadow-md flex items-center justify-center"
          >
            {isLast ? t('onboarding.done', 'Got it!') : t('onboarding.next', 'Next')}
          </button>
        </div>
      </div>
    </div>
  )
}
