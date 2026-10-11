import { useT } from '../lib/i18n'

export default function LoadingSpinner({ message, size = 'md' }) {
  const t = useT()
  const displayMsg = message ?? t('common.loading', 'Loading...')

  const sizeClasses = {
    sm: 'w-5 h-5 border-2',
    md: 'w-8 h-8 border-3',
    lg: 'w-12 h-12 border-4',
  }[size] || 'w-8 h-8 border-3'

  return (
    <div
      role="status"
      aria-live="polite"
      className="flex flex-col items-center justify-center p-6 space-y-3 min-h-[44px]"
    >
      <div
        className={`${sizeClasses} rounded-full border-indigo-200 border-t-indigo-600 dark:border-indigo-900 dark:border-t-indigo-400 motion-safe:animate-spin`}
        aria-hidden="true"
      />
      {displayMsg && (
        <p className="text-base font-medium text-gray-600 dark:text-gray-300">
          {displayMsg}
        </p>
      )}
      <span className="sr-only">{displayMsg}</span>
    </div>
  )
}
