/**
 * App.jsx — AI Study Companion (Chatbot Experience)
 * ────────────────────────────────────────────────
 * Gemini Webapp Style Interface:
 * - Left Sidebar with 5 Tiers:
 *   1) Daily report
 *   2) Weekly report
 *   3) Monthly report
 *   4) Start new conversation
 *   5) History (List)
 * - Top-right: Dark / Light mode toggle & Auth status
 * - Main chat window:
 *   - Input area with '+' button on leftmost side, text input, and submit on rightmost side
 *   - Resource enforcement: User cannot chat until resources (text, image, audio, files) are attached
 *   - Dynamic resources panel for active chat
 *   - Message turns rendering:
 *     1. What you asked
 *     2. Explanation (everyday analogy, key terms, summary)
 *     3. Demonstration / simulation
 *     4. 5-Question Quiz (single attempt lock)
 *     5. AI suggestions regarding strengths, weaknesses, must-do topics
 */

import React, { useState, useEffect, useRef } from 'react'
import { Sidebar } from './components/Sidebar'
import { ResourceModal } from './components/ResourceModal'
import { ProcessSimulationView } from './components/SimulationView'
import { TenQuestionQuiz } from './components/TenQuestionQuiz'
import AuthModal from './components/AuthModal'

export function getApiBaseUrl() {
  if (typeof window !== 'undefined') {
    const override = localStorage.getItem('ezlearn_api_url')
    if (override && override.trim()) {
      return override.trim().replace(/\/+$/, '').replace(/\/api$/, '')
    }
  }
  const rawApiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
  return rawApiUrl.trim().replace(/\/+$/, '').replace(/\/api$/, '')
}

export default function App() {
  const [apiUrl, setApiUrl] = useState(getApiBaseUrl)
  const API_URL = apiUrl

  const [darkMode, setDarkMode] = useState(() => {
    return localStorage.getItem('asc_theme') === 'dark' || false
  })

  // Auth state: Check if previous login data exists
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      const stored = localStorage.getItem('asc_user')
      return stored ? JSON.parse(stored) : null
    } catch {
      return null
    }
  })

  // Open login/register modal automatically on initial load if user is not logged in
  const [isAuthOpen, setIsAuthOpen] = useState(() => {
    try {
      const storedUser = localStorage.getItem('asc_user')
      const storedToken = localStorage.getItem('asc_token')
      return !(storedUser && storedToken)
    } catch {
      return true
    }
  })

  // Conversation state
  const [conversations, setConversations] = useState([])
  const [activeConvId, setActiveConvId] = useState(null)
  const [currentConvData, setCurrentConvData] = useState(null) // { id, title, resources, messages }
  const [loadingConv, setLoadingConv] = useState(false)

  // Chat input state
  const [promptInput, setPromptInput] = useState('')
  const [sendingMessage, setSendingMessage] = useState(false)
  const [pendingQuestion, setPendingQuestion] = useState('')
  const [errorNotice, setErrorNotice] = useState('')
  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false)
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false)
  const [isListening, setIsListening] = useState(false)
  // Backend Health & Auto Wake-up State: 'checking' | 'online' | 'offline' | 'waking'
  const [backendStatus, setBackendStatus] = useState('checking') // 'checking' | 'online' | 'offline' | 'waking'
  const [isWakingUp, setIsWakingUp] = useState(false)
  const [backendInfo, setBackendInfo] = useState(null)

  const messagesEndRef = useRef(null)
  const recognitionRef = useRef(null)

  // Apply dark mode class to root
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark')
      localStorage.setItem('asc_theme', 'dark')
    } else {
      document.documentElement.classList.remove('dark')
      localStorage.setItem('asc_theme', 'light')
    }
  }, [darkMode])

  // Initial load: Fetch conversations if user is signed in, or start volatile guest chat
  useEffect(() => {
    if (currentUser) {
      fetchConversations()
    } else {
      setConversations([])
      startNewConversation()
    }
  }, [currentUser])

  // Backend Health Checker & Auto-Wakeup Loop
  async function checkBackendHealth() {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 6000)
      const res = await fetch(`${API_URL}/api/health`, { signal: controller.signal })
      clearTimeout(timeoutId)
      if (res.ok) {
        const data = await res.json()
        setBackendStatus('online')
        setBackendInfo(data)
        setIsWakingUp(false)
        return true
      } else {
        setBackendStatus('offline')
        return false
      }
    } catch {
      setBackendStatus('offline')
      return false
    }
  }

  async function triggerWakeUp() {
    setIsWakingUp(true)
    setBackendStatus('waking')
    // Ping health endpoint to wake up Render container
    try {
      fetch(`${API_URL}/api/health`).catch(() => {})
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    let intervalId = null
    let active = true

    async function initialCheck() {
      const isUp = await checkBackendHealth()
      if (!isUp && active) {
        // If down on first load, immediately trigger wake-up ping
        triggerWakeUp()
      }
    }

    initialCheck()

    // Poll every 5s if offline/waking, or every 45s if online to keep alive
    intervalId = setInterval(async () => {
      const isUp = await checkBackendHealth()
      if (!isUp && active) {
        // keep waking ping alive until online
        try {
          fetch(`${API_URL}/api/health`).catch(() => {})
        } catch {
          // ignore
        }
      }
    }, backendStatus === 'online' ? 45000 : 5000)

    return () => {
      active = false
      if (intervalId) clearInterval(intervalId)
    }
  }, [backendStatus, API_URL])

  function getAuthHeaders(extraHeaders = {}) {
    const token = localStorage.getItem('asc_token')
    const headers = { ...extraHeaders }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  async function fetchConversations() {
    if (!currentUser) {
      setConversations([])
      return
    }
    try {
      const res = await fetch(`${API_URL}/api/chat/conversations`, {
        headers: getAuthHeaders(),
      })
      const list = await res.json()
      setConversations(list || [])
      if (list && list.length > 0 && !activeConvId) {
        loadConversation(list[0].id)
      } else if (!list || list.length === 0) {
        startNewConversation()
      }
    } catch {
      console.warn('Could not load chat history from server.')
    }
  }

  async function loadConversation(id) {
    if (!id) return
    setActiveConvId(id)
    setPromptInput('')
    setPendingQuestion('')
    setErrorNotice('')
    // Clear out previous chat data immediately so resources from other chats never leak into current view
    setCurrentConvData(null)
    setLoadingConv(true)
    try {
      const res = await fetch(`${API_URL}/api/chat/conversations/${id}`, {
        headers: getAuthHeaders(),
      })
      const data = await res.json()
      if (!res.ok) {
        setErrorNotice(data.detail || 'Could not load conversation details.')
      } else {
        setCurrentConvData(data)
      }
    } catch {
      setErrorNotice('Could not load conversation details.')
    } finally {
      setLoadingConv(false)
    }
  }

  async function startNewConversation() {
    setPromptInput('')
    setPendingQuestion('')
    setErrorNotice('')
    // Immediately clear current conversation so no resources carry over from previous chat
    setActiveConvId(null)
    setCurrentConvData(null)
    setLoadingConv(true)
    try {
      const res = await fetch(`${API_URL}/api/chat/conversations`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ title: 'New Study Session' }),
      })
      const data = await res.json()
      if (res.ok && data?.id) {
        const freshConv = {
          id: data.id,
          title: data.title || 'New Study Session',
          resources: [],
          messages: [],
        }
        setActiveConvId(data.id)
        setCurrentConvData(freshConv)
        if (currentUser) {
          setConversations(prev => [
            { id: data.id, title: data.title, resource_count: 0, message_count: 0, updated_at: data.created_at },
            ...prev.filter(c => c.id !== data.id),
          ])
        } else {
          // Guest users: volatile current chat only, no history list
          setConversations([])
        }
      } else {
        setErrorNotice('Failed to start a new chat.')
      }
    } catch {
      setErrorNotice('Failed to start a new chat.')
    } finally {
      setLoadingConv(false)
    }
  }

  async function deleteConversation(id) {
    try {
      await fetch(`${API_URL}/api/chat/conversations/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      })
      const remaining = conversations.filter(c => c.id !== id)
      setConversations(remaining)
      if (activeConvId === id) {
        if (remaining.length > 0) loadConversation(remaining[0].id)
        else startNewConversation()
      }
    } catch {
      setErrorNotice('Failed to delete chat.')
    }
  }

  // Handle adding resources to active conversation
  async function handleAddResource({ type, title, text, formData }) {
    if (!activeConvId) return
    if (type === 'text') {
      const res = await fetch(`${API_URL}/api/chat/conversations/${activeConvId}/resources/text`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ text, title }),
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Could not add text resource.')
      }
    } else if (type === 'upload') {
      const res = await fetch(`${API_URL}/api/chat/conversations/${activeConvId}/resources/upload`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json()
        throw new Error(err.detail || 'Could not upload resource.')
      }
    }
    // Refresh active conversation and history list
    await loadConversation(activeConvId)
    if (currentUser) {
      await fetchConversations()
    }
  }

  // Handle sending a chat message
  async function handleSendMessage(e) {
    e?.preventDefault()
    const text = promptInput.trim()
    if (!text || !activeConvId) return

    // Strict requirement: User must upload resources before chatting
    const hasResources = (currentConvData?.resources?.length || 0) > 0
    if (!hasResources) {
      setErrorNotice('⚠️ Please attach study notes, images, PDFs, or audio first using the "+" button before asking questions.')
      setIsResourceModalOpen(true)
      return
    }

    setPendingQuestion(text)
    setSendingMessage(true)
    setErrorNotice('')
    setPromptInput('')

    try {
      const res = await fetch(`${API_URL}/api/chat/conversations/${activeConvId}/messages`, {
        method: 'POST',
        headers: getAuthHeaders({ 'Content-Type': 'application/json' }),
        body: JSON.stringify({ prompt: text }),
      })
      const data = await res.json()
      if (!res.ok) {
        setErrorNotice(data.detail || 'Server error while generating response.')
      } else {
        await loadConversation(activeConvId)
        if (currentUser) {
          fetchConversations()
        }
      }
    } catch {
      setErrorNotice('Could not reach backend to send message.')
    } finally {
      setSendingMessage(false)
      setPendingQuestion('')
      setTimeout(() => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 200)
    }
  }

  // Voice speech-to-text recognition
  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // ignore
        }
      }
    }
  }, [])

  function handleToggleSpeechRecognition() {
    if (!hasAttachedResources) {
      setErrorNotice('⚠️ This chat has no attached resources. Please attach study notes, images, PDFs, or audio first using the "+" button before using voice input.')
      setIsResourceModalOpen(true)
      return
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) {
      setErrorNotice('Voice recognition is not supported in this browser. Please try Google Chrome or Edge.')
      return
    }

    if (isListening) {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop()
        } catch {
          // ignore
        }
      }
      setIsListening(false)
      return
    }

    try {
      const recognition = new SpeechRecognition()
      recognition.lang = 'en-US'
      recognition.continuous = false
      recognition.interimResults = true

      recognition.onstart = () => {
        setIsListening(true)
        setErrorNotice('')
      }

      recognition.onresult = (event) => {
        let transcript = ''
        for (let i = 0; i < event.results.length; i++) {
          transcript += event.results[i][0].transcript
        }
        if (transcript) {
          setPromptInput(prev => {
            const trimmed = prev.trim()
            return trimmed ? `${trimmed} ${transcript}` : transcript
          })
        }
      }

      recognition.onerror = (event) => {
        if (event.error !== 'no-speech') {
          setErrorNotice(`Microphone error: ${event.error}`)
        }
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
      recognition.start()
    } catch (err) {
      setErrorNotice('Failed to start microphone: ' + (err.message || 'Permission denied'))
      setIsListening(false)
    }
  }

  function handleLogout() {
    localStorage.removeItem('asc_token')
    localStorage.removeItem('asc_user')
    setCurrentUser(null)
    setConversations([])
  }

  // STRICT ISOLATION: Question typing enabled ONLY if current active chat itself has attached resources.
  // Resources uploaded in previous or other chats NEVER enable question typing in this chat.
  const hasAttachedResources = Boolean(
    !loadingConv &&
    activeConvId &&
    currentConvData &&
    currentConvData.id === activeConvId &&
    Array.isArray(currentConvData.resources) &&
    currentConvData.resources.length > 0
  )

  return (
    <div className={`h-screen w-screen flex overflow-hidden ${darkMode ? 'dark bg-gray-950 text-gray-100' : 'bg-slate-50 text-gray-800'}`}>
      
      {/* ── Left Sidebar (Tiers 1 to 5) ── */}
      <Sidebar
        conversations={conversations}
        activeConvId={activeConvId}
        onSelectConv={loadConversation}
        onNewConversation={startNewConversation}
        onDeleteConv={deleteConversation}
        apiUrl={API_URL}
        currentUser={currentUser}
        onOpenAuth={() => setIsAuthOpen(true)}
        isOpen={isMobileSidebarOpen}
        onClose={() => setIsMobileSidebarOpen(false)}
      />

      {/* ── Main Chat Area ── */}
      <main className="flex-1 h-full flex flex-col min-w-0 bg-white dark:bg-gray-950 relative">
        
        {/* Top Navbar */}
        <header className="h-14 border-b border-gray-100 dark:border-gray-800 px-3 sm:px-6 flex items-center justify-between bg-white/80 dark:bg-gray-900/80 backdrop-blur z-10 shrink-0">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            {/* Mobile Hamburger Drawer Button */}
            <button
              onClick={() => setIsMobileSidebarOpen(true)}
              className="md:hidden p-2 rounded-xl text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-200 dark:border-gray-800 flex items-center justify-center transition-colors"
              title="Open Navigation Menu"
              aria-label="Open navigation menu"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>

            {/* Mobile Brand Mark */}
            <div className="md:hidden w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center text-white shrink-0 shadow-xs">
              <span
                className="text-xs font-bold italic tracking-tighter"
                style={{ fontFamily: "'Brush Script MT', 'Dancing Script', 'Caveat', cursive, sans-serif" }}
              >
                ℰℓ
              </span>
            </div>

            <h2 className="font-extrabold text-sm sm:text-base text-gray-800 dark:text-gray-100 truncate max-w-[140px] sm:max-w-xs md:max-w-none">
              {currentConvData?.title || 'Study Session'}
            </h2>
            {hasAttachedResources && (
              <span className="hidden sm:inline-flex text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 shrink-0">
                📎 {currentConvData.resources.length}
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5 sm:gap-2 shrink-0">
            {/* Hovering Backend Health Indicator Circle */}
            <div className="relative group">
              <button
                onClick={() => {
                  if (backendStatus !== 'online') {
                    triggerWakeUp()
                  } else {
                    checkBackendHealth()
                  }
                }}
                className={`flex items-center gap-1.5 px-2 py-1 rounded-full border text-[11px] font-bold transition-all shadow-2xs cursor-pointer ${
                  backendStatus === 'online'
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 border-emerald-200 dark:border-emerald-800 text-emerald-700 dark:text-emerald-300'
                    : backendStatus === 'waking' || backendStatus === 'checking'
                    ? 'bg-amber-50 dark:bg-amber-950/40 border-amber-200 dark:border-amber-800 text-amber-700 dark:text-amber-300'
                    : 'bg-rose-50 dark:bg-rose-950/40 border-rose-200 dark:border-rose-800 text-rose-700 dark:text-rose-300 hover:ring-2 hover:ring-rose-300'
                }`}
                title="Backend server status indicator (Click to test/wake up)"
              >
                {/* Glowing / Hovering animated circle */}
                <span className="relative flex h-2.5 w-2.5">
                  {backendStatus !== 'online' ? (
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 dark:bg-amber-500 opacity-75"></span>
                  ) : null}
                  <span className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                    backendStatus === 'online'
                      ? 'bg-emerald-500 ring-2 ring-emerald-300 dark:ring-emerald-700'
                      : backendStatus === 'waking' || backendStatus === 'checking'
                      ? 'bg-amber-500 animate-pulse'
                      : 'bg-rose-500 ring-2 ring-rose-300 dark:ring-rose-700'
                  }`}></span>
                </span>
                
                <span className="hidden sm:inline">
                  {backendStatus === 'online'
                    ? 'Backend Live'
                    : backendStatus === 'waking'
                    ? 'Waking Server…'
                    : backendStatus === 'checking'
                    ? 'Checking…'
                    : 'Backend Asleep'}
                </span>
              </button>

              {/* Hovering Popover Card */}
              <div className="absolute right-0 top-full mt-2 w-64 p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-2xl shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50 text-left pointer-events-none group-hover:pointer-events-auto">
                <div className="flex items-center justify-between pb-1.5 border-b border-gray-100 dark:border-gray-800 mb-2">
                  <span className="text-xs font-black text-gray-800 dark:text-gray-100 flex items-center gap-1.5">
                    <span>⚡</span> Backend Status
                  </span>
                  <span className={`text-[10px] font-extrabold uppercase px-1.5 py-0.5 rounded ${
                    backendStatus === 'online'
                      ? 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200'
                      : 'bg-amber-100 dark:bg-amber-900/60 text-amber-800 dark:text-amber-200'
                  }`}>
                    {backendStatus}
                  </span>
                </div>

                <p className="text-[11px] text-gray-500 dark:text-gray-400 leading-relaxed mb-2.5">
                  {backendStatus === 'online'
                    ? 'FastAPI server on Render is online, healthy, and handling requests.'
                    : 'Free cloud hosting spins down after inactivity. Click below to immediately wake it up.'}
                </p>

                {backendStatus === 'online' && (
                  <div className="mb-2 p-2 rounded-xl bg-gray-50 dark:bg-gray-800/60 border border-gray-100 dark:border-gray-800 text-[10px] space-y-1">
                    <div className="flex justify-between items-center text-gray-500 dark:text-gray-400">
                      <span>Server Build:</span>
                      <span className="font-mono font-bold text-indigo-600 dark:text-indigo-400">
                        {backendInfo?.build_version || 'pre-v2.1 (Needs Redeploy)'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center text-gray-500 dark:text-gray-400">
                      <span>Grounding Guard:</span>
                      <span className={`font-semibold ${backendInfo?.grounding ? 'text-emerald-600 dark:text-emerald-400' : 'text-amber-600'}`}>
                        {backendInfo?.grounding ? 'Strict Dual-Schema' : 'Not Deployed'}
                      </span>
                    </div>
                  </div>
                )}

                {backendStatus !== 'online' && (
                  <button
                    onClick={triggerWakeUp}
                    className="w-full py-1.5 px-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold transition-all shadow-xs flex items-center justify-center gap-1.5"
                  >
                    <span>🚀</span> Turn On Backend Now
                  </button>
                )}
              </div>
            </div>

            {/* Dark / Light Mode Button */}
            <button
              onClick={() => setDarkMode(!darkMode)}
              className="p-1.5 sm:p-2 rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-gray-100 dark:hover:bg-gray-800 text-xs sm:text-sm transition-all"
              title="Toggle Dark/Light Mode"
            >
              {darkMode ? '☀️' : '🌙'}
            </button>

            {/* User status */}
            {currentUser ? (
              <div className="flex items-center gap-1.5 sm:gap-2">
                <div className="flex items-center gap-1.5 px-2 py-1 rounded-xl bg-gray-100 dark:bg-gray-800 text-xs">
                  <span className="w-5 h-5 rounded-full bg-indigo-600 text-white flex items-center justify-center text-[10px] font-bold uppercase shrink-0">
                    {(currentUser.name || currentUser.email)[0]}
                  </span>
                  <span className="font-bold text-gray-800 dark:text-gray-200 hidden sm:inline truncate max-w-[90px]">
                    {currentUser.name}
                  </span>
                </div>
                <button
                  onClick={handleLogout}
                  className="px-2 sm:px-2.5 py-1 rounded-xl border border-gray-200 dark:border-gray-800 hover:bg-rose-50 dark:hover:bg-rose-950/40 text-gray-500 hover:text-rose-600 dark:text-gray-400 dark:hover:text-rose-400 font-bold text-[11px] sm:text-xs transition-all"
                  title="Sign out (Return to Guest mode)"
                >
                  Sign Out
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsAuthOpen(true)}
                className="px-2.5 sm:px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-[11px] sm:text-xs shadow-sm transition-all whitespace-nowrap"
              >
                Sign In
              </button>
            )}
          </div>
        </header>

        {/* Floating Auto-Wakeup Notice Banner if Backend is Asleep or Waking */}
        {backendStatus !== 'online' && (
          <div className="bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-indigo-500/10 dark:from-amber-950/40 dark:to-indigo-950/30 border-b border-amber-200/80 dark:border-amber-800/60 px-4 py-2 flex items-center justify-between gap-3 text-xs shrink-0 animate-fadeIn">
            <div className="flex items-center gap-2 min-w-0">
              <span className="relative flex h-2 w-2 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
              </span>
              <span className="text-amber-800 dark:text-amber-200 font-medium truncate">
                {backendStatus === 'waking'
                  ? 'Render backend server is waking up from idle mode (takes ~30-45s on free plan)…'
                  : 'Backend server is in sleep mode. Auto-waking now…'}
              </span>
            </div>
            <button
              onClick={triggerWakeUp}
              disabled={isWakingUp}
              className="px-2.5 py-1 rounded-lg bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white font-bold text-[11px] shadow-2xs whitespace-nowrap shrink-0 transition-all"
            >
              {isWakingUp ? 'Waking…' : 'Wake Now ⚡'}
            </button>
          </div>
        )}

        {/* Dynamic Attached Resources Banner */}
        {hasAttachedResources && (
          <div className="bg-indigo-50/50 dark:bg-indigo-950/20 border-b border-indigo-100 dark:border-indigo-900/40 px-6 py-2 flex items-center gap-2 overflow-x-auto text-xs">
            <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-500 whitespace-nowrap">
              Active Resources:
            </span>
            {currentConvData.resources.map(r => (
              <div
                key={r.id}
                className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-white dark:bg-gray-900 border border-indigo-200 dark:border-indigo-800 text-indigo-900 dark:text-indigo-300 whitespace-nowrap font-medium text-[11px] shadow-2xs"
              >
                <span>{r.resource_type === 'image' ? '🖼️' : r.resource_type === 'audio' ? '🎙️' : r.resource_type === 'file' ? '📄' : '📝'}</span>
                <span className="truncate max-w-[120px]">{r.title}</span>
              </div>
            ))}
            <button
              onClick={() => setIsResourceModalOpen(true)}
              className="text-[11px] text-indigo-600 dark:text-indigo-400 hover:underline font-bold whitespace-nowrap ml-1"
            >
              + Add More
            </button>
          </div>
        )}

        {/* Scrollable Message Transcript */}
        <div className="flex-1 overflow-y-auto px-4 md:px-8 py-6 space-y-8">
          
          {/* Welcome / Empty chat state */}
          {(!currentConvData?.messages || currentConvData.messages.length === 0) && (
            <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto space-y-4">
              <div className="w-16 h-16 rounded-3xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-violet-500 border border-indigo-400/30 flex items-center justify-center text-white shadow-xl shadow-indigo-500/20 select-none">
                <span
                  className="text-3xl font-bold italic tracking-tighter"
                  style={{ fontFamily: "'Dancing Script', 'Brush Script MT', 'Great Vibes', 'Caveat', cursive, sans-serif", transform: 'translateY(-2px)' }}
                >
                  <span className="text-3xl">ℰ</span><span className="text-2xl font-semibold">ℓ</span>
                </span>
              </div>
              <div className="space-y-1">
                <h3 className="text-2xl font-black bg-gradient-to-r from-indigo-600 to-violet-600 dark:from-indigo-400 dark:to-violet-400 bg-clip-text text-transparent">
                  Welcome to EzLearn
                </h3>
                <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
                  To get started, attach study notes, images, PDFs, or audio using the{' '}
                  <strong className="text-indigo-600 dark:text-indigo-400 font-bold">+</strong> button on the input bar below.
                </p>
              </div>

              {!hasAttachedResources && (
                <button
                  onClick={() => setIsResourceModalOpen(true)}
                  className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-xs shadow-md transition-all flex items-center gap-2"
                >
                  <span>➕</span> Add Study Resource to Begin
                </button>
              )}
            </div>
          )}

          {/* Render Turns in Required Order */}
          {currentConvData?.messages?.map((msg) => (
            <div key={msg.id} className="space-y-4 max-w-3xl mx-auto">
              
              {/* 1. What You Asked */}
              <div className="flex justify-end">
                <div className="bg-indigo-600 text-white rounded-3xl rounded-tr-xs px-5 py-3.5 max-w-xl text-sm font-medium shadow-md">
                  <div className="text-[10px] uppercase font-black text-indigo-200 tracking-wider mb-1">
                    What You Asked
                  </div>
                  <div>{msg.user_prompt}</div>
                </div>
              </div>

              {/* Assistant Response Box */}
              <div className="space-y-4 animate-fadeIn">
                
                {/* 2. Explanation */}
                {msg.explanation && (
                  <div className="bg-white dark:bg-gray-900 rounded-3xl border border-gray-200 dark:border-gray-800 p-6 space-y-4 shadow-sm">
                    <div className="flex items-center justify-between pb-2 border-b dark:border-gray-800 flex-wrap gap-2">
                      <h4 className="font-extrabold text-base text-gray-900 dark:text-gray-100 flex items-center gap-2">
                        {msg.explanation.is_outlier ? (
                          <>
                            <span className="text-amber-500">⚠️</span> Question Outside File Context
                          </>
                        ) : (
                          <>
                            <span>💡</span> Explanation: {msg.explanation.topic || 'Concept Overview'}
                          </>
                        )}
                      </h4>
                      {msg.explanation.is_outlier ? (
                        <span className="text-[10px] bg-amber-50 dark:bg-amber-950/50 text-amber-800 dark:text-amber-200 border border-amber-300 dark:border-amber-800 px-2.5 py-1 rounded-full font-bold flex items-center gap-1">
                          <span>🚫</span> Not Answered (Out of Context)
                        </span>
                      ) : null}
                    </div>

                    {/* Outlier / Out of Context Notice */}
                    {msg.explanation.outlier_notice && (
                      <div className="p-4 bg-amber-50/90 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-2xl text-xs text-amber-900 dark:text-amber-200 font-medium leading-relaxed flex items-start gap-3">
                        <span className="text-base shrink-0 leading-none">⚠️</span>
                        <div className="space-y-1">
                          <p className="font-bold text-amber-950 dark:text-amber-100">Question not in context of uploaded file</p>
                          <p>{msg.explanation.outlier_notice}</p>
                          {msg.explanation.file_context && (
                            <div className="mt-2 p-2 rounded-xl bg-amber-100/70 dark:bg-amber-900/40 border border-amber-200 dark:border-amber-800 text-[11px]">
                              <span className="font-bold">Detected File Context:</span> {msg.explanation.file_context}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Everyday Physical Picture / Analogy First (for regular topics) */}
                    {!msg.explanation.is_outlier && msg.explanation.real_life_picture && (
                      <div className="bg-amber-50/70 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-2xl p-4 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                        <span className="font-extrabold uppercase tracking-wide block">
                          🖼️ Everyday Physical Picture:
                        </span>
                        <p className="leading-relaxed">{msg.explanation.real_life_picture}</p>
                      </div>
                    )}

                    {/* Summary (for regular topics) */}
                    {!msg.explanation.is_outlier && msg.explanation.summary && (
                      <p className="text-xs text-gray-700 dark:text-gray-300 font-sans leading-relaxed">
                        {msg.explanation.summary}
                      </p>
                    )}

                    {/* Body */}
                    {msg.explanation.body && (
                      <div className="text-xs text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed">
                        {msg.explanation.body}
                      </div>
                    )}

                    {/* Key Technical Terms */}
                    {msg.explanation.key_terms?.length > 0 && (
                      <div className="pt-2 border-t dark:border-gray-800 space-y-2">
                        <span className="text-[10px] font-bold uppercase text-gray-400 tracking-wider">
                          Key Terms (English + Meaning)
                        </span>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                          {msg.explanation.key_terms.map((kt, kIdx) => (
                            <div key={kIdx} className="p-2.5 rounded-xl bg-gray-50 dark:bg-gray-800 border dark:border-gray-700 text-xs">
                              <span className="font-bold text-indigo-600 dark:text-indigo-400 block">{kt.term}</span>
                              <span className="text-[11px] text-gray-500 dark:text-gray-400">{kt.meaning}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Citations from Attached Resources */}
                    {msg.citations?.length > 0 && (
                      <div className="pt-2 border-t dark:border-gray-800 flex items-center gap-2 flex-wrap text-[11px]">
                        <span className="font-bold text-gray-400 uppercase">Resource Citations:</span>
                        {msg.citations.map((c, cIdx) => (
                          <span key={cIdx} className="px-2 py-0.5 rounded-md bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 font-medium">
                            📄 Page {c.page}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* 3. Demonstration / Simulation */}
                {msg.simulation && (
                  <ProcessSimulationView plan={msg.simulation} />
                )}

                {/* 4. 5-Question Quiz (Attempt once / locked results) */}
                {msg.quiz && (
                  <TenQuestionQuiz
                    quizData={msg.quiz}
                    messageId={msg.id}
                    convId={activeConvId}
                    apiUrl={API_URL}
                    initialAttempt={msg.quiz_attempt}
                    initialSuggestions={msg.ai_suggestions}
                  />
                )}

              </div>
            </div>
          ))}

          {/* Loading indicator with User's Question Shown Above */}
          {sendingMessage && (
            <div className="space-y-4 max-w-3xl mx-auto animate-fadeIn">
              {/* User's Question Bubble Above Generating Indicator */}
              {pendingQuestion && (
                <div className="flex justify-end">
                  <div className="bg-indigo-600 text-white rounded-3xl rounded-tr-xs px-5 py-3.5 max-w-xl text-sm font-medium shadow-md">
                    <div className="text-[10px] uppercase font-black text-indigo-200 tracking-wider mb-1">
                      What You Asked
                    </div>
                    <div>{pendingQuestion}</div>
                  </div>
                </div>
              )}

              {/* Generating Answer Message Box */}
              <div className="max-w-xl p-5 bg-white dark:bg-gray-900 rounded-3xl border border-indigo-100 dark:border-gray-800 space-y-2 animate-pulse shadow-xs">
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-indigo-600 animate-ping" />
                  <span className="text-xs font-bold text-indigo-600 dark:text-indigo-400">
                    Generating Answer from Attached Resources…
                  </span>
                </div>
                <div className="h-4 bg-gray-200 dark:bg-gray-800 rounded w-1/3" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-full" />
                <div className="h-3 bg-gray-200 dark:bg-gray-800 rounded w-4/5" />
                <p className="text-[11px] text-gray-400 dark:text-gray-500 pt-2 font-medium">
                  ✨ Synthesizing explanation, visual demonstration, and 5-question quiz…
                </p>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error Notice */}
        {errorNotice && (
          <div className="mx-6 mb-2 p-3 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800 rounded-2xl text-xs text-rose-700 dark:text-rose-300 font-medium flex items-center justify-between">
            <span>{errorNotice}</span>
            <button onClick={() => setErrorNotice('')} className="font-bold ml-2">✕</button>
          </div>
        )}

        {/* ── Chatbot Input Bar (Gemini Webapp Style) ── */}
        <div className="p-4 md:p-6 bg-white dark:bg-gray-950 border-t border-gray-100 dark:border-gray-800">
          <form
            onSubmit={handleSendMessage}
            className={`max-w-3xl mx-auto flex items-center gap-2 p-2 rounded-3xl border transition-all ${
              hasAttachedResources
                ? 'border-gray-300 dark:border-gray-700 bg-gray-50/50 dark:bg-gray-900 focus-within:ring-2 focus-within:ring-indigo-400 focus-within:border-indigo-400'
                : 'border-amber-300 bg-amber-50/20 dark:bg-gray-900 cursor-not-allowed'
            }`}
          >
            {/* Leftmost '+' button for adding resources */}
            <button
              type="button"
              onClick={() => setIsResourceModalOpen(true)}
              className="w-10 h-10 rounded-2xl bg-indigo-50 hover:bg-indigo-100 dark:bg-gray-800 dark:hover:bg-gray-700 text-indigo-700 dark:text-indigo-300 flex items-center justify-center text-lg font-black transition-all shadow-2xs"
              title="Add Resource (Text, Image, Audio, File)"
            >
              +
            </button>

            {/* Input Text Box */}
            <input
              type="text"
              value={promptInput}
              onChange={e => {
                if (!hasAttachedResources) return
                setPromptInput(e.target.value)
              }}
              disabled={!hasAttachedResources || sendingMessage || loadingConv}
              placeholder={
                loadingConv
                  ? 'Loading chat session…'
                  : isListening
                  ? 'Listening… speak your question now…'
                  : hasAttachedResources
                  ? 'Ask anything about your study notes…'
                  : '⚠️ Current chat has no resources. Attach notes using "+" to type questions…'
              }
              className={`flex-1 bg-transparent px-2 text-sm text-gray-800 dark:text-gray-100 focus:outline-none placeholder:text-gray-400 dark:placeholder:text-gray-500 ${
                !hasAttachedResources ? 'cursor-not-allowed opacity-60' : ''
              }`}
            />

            {/* Microphone Voice Button */}
            <button
              type="button"
              onClick={handleToggleSpeechRecognition}
              disabled={!hasAttachedResources || sendingMessage || loadingConv}
              className={`w-10 h-10 rounded-2xl flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-2xs ${
                isListening
                  ? 'bg-rose-500 hover:bg-rose-600 text-white animate-pulse ring-4 ring-rose-200 dark:ring-rose-950'
                  : 'bg-indigo-50 hover:bg-indigo-100 dark:bg-gray-800 dark:hover:bg-gray-700 text-indigo-700 dark:text-indigo-300'
              }`}
              title={
                hasAttachedResources
                  ? (isListening ? 'Stop listening' : 'Speak your question (Voice Input)')
                  : 'Current chat has no resources. Attach notes first to enable voice input'
              }
              aria-label={isListening ? 'Stop microphone' : 'Start microphone'}
            >
              <span className="text-base leading-none">
                {isListening ? '⏹️' : '🎙️'}
              </span>
            </button>

            {/* Rightmost Submit Button */}
            <button
              type="submit"
              disabled={!hasAttachedResources || !promptInput.trim() || sendingMessage || loadingConv}
              className="w-10 h-10 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white flex items-center justify-center transition-all disabled:opacity-40 disabled:cursor-not-allowed shadow-sm shrink-0"
              title={hasAttachedResources ? "Send Message" : "Attach resources to this chat before sending"}
            >
              ➔
            </button>
          </form>

          {/* ── Footer Credits ── */}
          <footer className="text-center text-[11px] sm:text-xs text-gray-400 dark:text-gray-500 font-medium pt-2 pb-0.5 select-none px-2 flex items-center justify-center gap-1.5 flex-wrap">
            <span>Created by</span>
            <span className="font-bold text-gray-700 dark:text-gray-300">Arya Mandavgane</span>
            <span>for</span>
            <span className="font-extrabold text-indigo-600 dark:text-indigo-400">AIMPACT</span>
          </footer>
        </div>

      </main>

      {/* ── Modal for Adding Resources ── */}
      <ResourceModal
        isOpen={isResourceModalOpen}
        onClose={() => setIsResourceModalOpen(false)}
        onAddResource={handleAddResource}
      />

      {/* ── Auth Modal ── */}
      <AuthModal
        isOpen={isAuthOpen}
        onClose={() => setIsAuthOpen(false)}
        onAuthSuccess={(user) => setCurrentUser(user)}
        apiUrl={API_URL}
      />

    </div>
  )
}
