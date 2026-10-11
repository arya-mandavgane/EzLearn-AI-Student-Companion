import { useState, useEffect } from 'react'
import { useT } from '../lib/i18n'

export default function OfflineBanner({ offline }) {
  const t = useT()
  const [isOffline, setIsOffline] = useState(() => {
    if (typeof offline === 'boolean') return offline
    return typeof navigator !== 'undefined' ? !navigator.onLine : false
  })

  useEffect(() => {
    if (typeof offline === 'boolean') {
      setIsOffline(offline)
      return
    }

    const handleOnline = () => setIsOffline(false)
    const handleOffline = () => setIsOffline(true)

    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)

    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [offline])

  if (!isOffline) return null

  return (
    <div
      role="status"
      aria-live="polite"
      className="w-full bg-amber-500 text-amber-950 px-4 py-2.5 text-center text-sm font-semibold shadow-sm flex items-center justify-center gap-2"
    >
      <span aria-hidden="true" className="text-base">📡</span>
      <span>{t('common.offline', 'You are offline. Simulations and saved content still work.')}</span>
    </div>
  )
}
