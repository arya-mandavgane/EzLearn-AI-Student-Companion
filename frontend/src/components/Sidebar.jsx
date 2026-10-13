import React, { useState, useEffect } from 'react'

export function Sidebar({
  conversations,
  activeConvId,
  onSelectConv,
  onNewConversation,
  onDeleteConv,
  apiUrl,
  currentUser,
  onOpenAuth,
  isOpen = false,
  onClose,
  reportRefreshKey,
}) {
  const [activeReportTab, setActiveReportTab] = useState(null) // 'daily' | 'weekly' | 'monthly' | null
  const [reportData, setReportData] = useState(null)
  const [reportLoading, setReportLoading] = useState(false)
  const [reportError, setReportError] = useState('')

  // Auto-reload report when a quiz is submitted
  useEffect(() => {
    if (activeReportTab) {
      loadReport(activeReportTab, true)
    }
  }, [reportRefreshKey])

  async function loadReport(timeframe, isAutoRefresh = false) {
    if (!isAutoRefresh && activeReportTab === timeframe) {
      setActiveReportTab(null)
      setReportData(null)
      setReportError('')
      return
    }

    setActiveReportTab(timeframe)
    setReportLoading(true)
    setReportError('')
    try {
      const token = localStorage.getItem('asc_token')
      const headers = {}
      if (token) headers['Authorization'] = `Bearer ${token}`

      const convQuery = activeConvId ? `?conv_id=${encodeURIComponent(activeConvId)}` : ''
      const res = await fetch(`${apiUrl}/api/chat/reports/${timeframe}${convQuery}`, { headers })
      const data = await res.json()
      if (!res.ok) {
        setReportError(data.detail || 'Could not load report.')
        setReportData(null)
      } else {
        setReportData(data)
      }
    } catch {
      setReportError('Network error loading report.')
      setReportData(null)
    } finally {
      setReportLoading(false)
    }
  }

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/50 backdrop-blur-xs md:hidden transition-opacity"
          aria-hidden="true"
        />
      )}

      <aside className={`fixed md:static inset-y-0 left-0 z-50 w-72 sm:w-80 h-full flex flex-col bg-white dark:bg-gray-900 border-r border-gray-200 dark:border-gray-800 transition-transform duration-300 ease-in-out select-none ${
        isOpen ? 'translate-x-0 shadow-2xl' : '-translate-x-full md:translate-x-0'
      }`}>
      
      {/* Brand Header */}
      <div className="p-4 border-b border-gray-100 dark:border-gray-800 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          {/* Cursive E & l Logo Badge */}
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 flex items-center justify-center shadow-md shadow-indigo-500/20 text-white select-none">
            <span
              className="text-base font-bold italic tracking-tighter"
              style={{ fontFamily: "'Brush Script MT', 'Dancing Script', 'Caveat', 'Great Vibes', cursive, sans-serif", transform: 'translateY(-1px)' }}
            >
              <span className="text-lg">ℰ</span><span className="text-sm font-semibold">ℓ</span>
            </span>
          </div>
          <div>
            <span className="font-black text-base tracking-tight bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
              EzLearn
            </span>
            <span className="block text-[9px] font-semibold text-gray-400 dark:text-gray-500 leading-none">
              AI Study Companion
            </span>
          </div>
        </div>
        <div className="flex items-center gap-1.5">
          {currentUser ? (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800">
              ● Signed In
            </span>
          ) : (
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/50 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800">
              Guest
            </span>
          )}

          {/* Close button on mobile drawer */}
          <button
            onClick={onClose}
            className="md:hidden p-1.5 -mr-1 rounded-xl text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            title="Close menu"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Top Tiers 1-4 */}
      <div className="p-3 space-y-2 border-b border-gray-100 dark:border-gray-800">
        
        {/* Tier 1, 2, 3: Reports */}
        <div className="space-y-1">
          <div className="flex items-center justify-between px-2">
            <span className="text-[10px] uppercase font-bold text-gray-400 dark:text-gray-500 tracking-wider">
              Performance Reports
            </span>
            <span className="text-[9px] font-bold text-emerald-600 dark:text-emerald-400">
              Live Analytics
            </span>
          </div>
          <div className="grid grid-cols-3 gap-1">
            {[
              { id: 'daily',   label: '📅 Daily' },
              { id: 'weekly',  label: '📊 Weekly' },
              { id: 'monthly', label: '📈 Monthly' },
            ].map(tier => (
              <button
                key={tier.id}
                onClick={() => loadReport(tier.id)}
                className={`py-1.5 px-2 rounded-xl text-xs font-bold transition-all text-center ${
                  activeReportTab === tier.id
                    ? 'bg-indigo-600 text-white shadow-sm'
                    : 'bg-gray-50 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
                title={`View ${tier.id} performance report`}
              >
                {tier.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tier 4: Start New Conversation Button */}
        <button
          onClick={() => {
            onNewConversation()
            if (onClose) onClose()
          }}
          className="w-full py-2.5 px-3 rounded-2xl bg-indigo-50 hover:bg-indigo-100 dark:bg-indigo-950/50 dark:hover:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 font-extrabold text-xs flex items-center justify-center gap-2 border border-indigo-200 dark:border-indigo-800 transition-all shadow-sm"
        >
          <span>➕</span> Start New Conversation
        </button>
      </div>

      {/* Expanded Report View in Sidebar */}
      {activeReportTab && (
        <div className="p-3 bg-indigo-50/50 dark:bg-indigo-950/30 border-b border-indigo-100 dark:border-indigo-900 space-y-2 text-xs animate-fadeIn">
          <div className="flex items-center justify-between font-bold text-indigo-900 dark:text-indigo-200">
            <span className="capitalize">{activeReportTab} Report ({reportData?.period_label || 'Current'})</span>
            <div className="flex items-center gap-1.5">
              <button
                onClick={() => loadReport(activeReportTab, true)}
                className="text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 p-0.5"
                title="Refresh report metrics"
              >
                🔄
              </button>
              <button onClick={() => setActiveReportTab(null)} className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">
                ✕
              </button>
            </div>
          </div>

          {reportLoading && <p className="text-[11px] text-gray-400">Loading metrics…</p>}

          {reportError && (
            <p className="text-[11px] text-rose-500 font-medium">{reportError}</p>
          )}

          {reportData && (
            <div className="space-y-2">
              <div className="grid grid-cols-3 gap-1 text-center">
                <div className="bg-white dark:bg-gray-800 p-1.5 rounded-xl border dark:border-gray-700">
                  <span className="text-[9px] uppercase font-bold text-gray-400 block">Accuracy</span>
                  <span className="font-black text-xs text-indigo-600 dark:text-indigo-400">
                    {reportData.overall_accuracy_pct}%
                  </span>
                </div>
                <div className="bg-white dark:bg-gray-800 p-1.5 rounded-xl border dark:border-gray-700">
                  <span className="text-[9px] uppercase font-bold text-gray-400 block">Quizzes</span>
                  <span className="font-bold text-xs text-gray-700 dark:text-gray-200">
                    {reportData.quizzes_completed}
                  </span>
                </div>
                <div className="bg-white dark:bg-gray-800 p-1.5 rounded-xl border dark:border-gray-700">
                  <span className="text-[9px] uppercase font-bold text-gray-400 block">Questions</span>
                  <span className="font-bold text-xs text-gray-700 dark:text-gray-200">
                    {reportData.total_questions_answered}
                  </span>
                </div>
              </div>

              {reportData.quizzes_completed === 0 ? (
                <div className="p-2.5 bg-white dark:bg-gray-800/80 rounded-xl border dark:border-gray-700 text-center text-gray-400">
                  <p className="text-[11px]">No quizzes completed in this period yet.</p>
                  <p className="text-[10px] mt-0.5 text-indigo-500">Take a 5-question quiz to see your live metrics!</p>
                </div>
              ) : (
                <>
                  {/* Strengths */}
                  {reportData.strengths?.length > 0 && (
                    <div className="p-2 bg-emerald-50 dark:bg-emerald-950/30 rounded-xl border border-emerald-200 dark:border-emerald-800">
                      <span className="font-bold text-[10px] uppercase text-emerald-800 dark:text-emerald-300 block">
                        💪 Strengths:
                      </span>
                      <div className="text-[11px] text-emerald-900 dark:text-emerald-200 truncate">
                        {reportData.strengths.map(s => s.topic).join(', ')}
                      </div>
                    </div>
                  )}

                  {/* Weaknesses */}
                  {reportData.weaknesses?.length > 0 && (
                    <div className="p-2 bg-rose-50 dark:bg-rose-950/30 rounded-xl border border-rose-200 dark:border-rose-800">
                      <span className="font-bold text-[10px] uppercase text-rose-800 dark:text-rose-300 block">
                        ⚠️ Needs Attention:
                      </span>
                      <div className="text-[11px] text-rose-900 dark:text-rose-200 truncate">
                        {reportData.weaknesses.map(w => w.topic).join(', ')}
                      </div>
                    </div>
                  )}

                  {/* Must-do Topics */}
                  {reportData.must_do_topics?.length > 0 && (
                    <div className="p-2 bg-amber-50 dark:bg-amber-950/30 rounded-xl border border-amber-200 dark:border-amber-800">
                      <span className="font-bold text-[10px] uppercase text-amber-800 dark:text-amber-300 block">
                        🎯 Must-Do Topics:
                      </span>
                      <div className="text-[11px] text-amber-900 dark:text-amber-200">
                        {reportData.must_do_topics.join(', ')}
                      </div>
                    </div>
                  )}
                </>
              )}

              {!currentUser && (
                <p className="text-[10px] text-indigo-500 dark:text-indigo-400 text-center cursor-pointer hover:underline pt-1" onClick={onOpenAuth}>
                  💡 Sign in to save progress permanently
                </p>
              )}
            </div>
          )}
        </div>
      )}

      {/* Tier 5: History List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        <div className="flex items-center justify-between px-2">
          <span className="text-[10px] uppercase font-bold text-gray-400 dark:text-gray-500 tracking-wider">
            Chat History
          </span>
          {!currentUser && (
            <span className="text-[9px] font-bold text-amber-600 dark:text-amber-400">
              🔒 Locked
            </span>
          )}
        </div>

        {!currentUser ? (
          <div className="p-4 bg-amber-50/70 dark:bg-amber-950/30 rounded-2xl border border-amber-200 dark:border-amber-900/60 text-center space-y-2 mt-2">
            <span className="text-2xl block">🔒</span>
            <p className="font-extrabold text-xs text-amber-900 dark:text-amber-200">
              History is for Registered Users
            </p>
            <p className="text-[11px] text-amber-800 dark:text-amber-300 leading-snug">
              Guest chats are volatile and not saved. Sign in or create an account to store chats and track study reports!
            </p>
            <button
              onClick={onOpenAuth}
              className="mt-1 w-full py-1.5 px-3 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs shadow-sm transition-all"
            >
              Sign In / Register
            </button>
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 text-xs text-gray-400">
            No previous chats yet.<br />Click "+ Start New Conversation".
          </div>
        ) : (
          conversations.map(conv => (
            <div
              key={conv.id}
              onClick={() => {
                onSelectConv(conv.id)
                if (onClose) onClose()
              }}
              className={`group flex items-center justify-between p-2.5 rounded-xl cursor-pointer text-xs font-semibold transition-all ${
                activeConvId === conv.id
                  ? 'bg-indigo-50 dark:bg-indigo-950/50 text-indigo-700 dark:text-indigo-300 font-bold border border-indigo-200 dark:border-indigo-800'
                  : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
              }`}
            >
              <div className="truncate flex-1 pr-2">
                <div className="truncate">{conv.title}</div>
                <div className="text-[10px] font-normal text-gray-400 flex items-center gap-2 mt-0.5">
                  <span>📎 {conv.resource_count} resources</span>
                  <span>💬 {conv.message_count} msgs</span>
                </div>
              </div>

              <button
                onClick={(e) => { e.stopPropagation(); onDeleteConv(conv.id) }}
                className="opacity-0 group-hover:opacity-100 text-gray-400 hover:text-rose-600 px-1 text-sm transition-opacity"
                title="Delete chat"
              >
                ✕
              </button>
            </div>
          ))
        )}
      </div>

      {/* Sidebar Footer Credits */}
      <div className="p-3 border-t border-gray-100 dark:border-gray-800 text-center select-none">
        <p className="text-[10px] text-gray-400 dark:text-gray-500 font-medium">
          Created by <span className="font-semibold text-gray-600 dark:text-gray-300">Arya Mandavgane</span> for <span className="font-bold text-indigo-600 dark:text-indigo-400">AIMPACT</span>
        </p>
      </div>

    </aside>
  </>
  )
}
