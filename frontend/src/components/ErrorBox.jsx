import { useT } from '../lib/i18n'

export default function ErrorBox({ message, onRetry }) {
  const t = useT()

  return (
    <div
      role="alert"
      className="bg-red-50 dark:bg-red-950/40 border border-red-300 dark:border-red-800 text-red-900 dark:text-red-200 rounded-2xl p-5 space-y-3 shadow-sm"
    >
      <div className="flex items-start gap-3">
        <span aria-hidden="true" className="text-2xl flex-shrink-0">⚠️</span>
        <div className="space-y-1">
          <h3 className="text-base font-bold text-red-900 dark:text-red-100">
            {t('common.error', 'Something went wrong.')}
          </h3>
          <p className="text-base text-red-800 dark:text-red-300 leading-relaxed">
            {message || t('common.error', 'Something went wrong.')}
          </p>
        </div>
      </div>

      {onRetry && (
        <div className="pt-1 flex justify-end">
          <button
            type="button"
            onClick={onRetry}
            className="min-h-[44px] min-w-[44px] px-4 py-2.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-semibold text-base transition-colors focus:outline-none focus:ring-2 focus:ring-red-400 focus:ring-offset-2 dark:focus:ring-offset-gray-900"
          >
            {t('common.retry', 'Try again')}
          </button>
        </div>
      )}
    </div>
  )
}
