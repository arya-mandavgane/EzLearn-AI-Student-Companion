import { useState } from 'react'

export default function AuthModal({ isOpen, onClose, onAuthSuccess, apiUrl = 'http://localhost:8000' }) {
  const [mode, setMode] = useState('login') // 'login' | 'register'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [age, setAge] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  if (!isOpen) return null

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setNotice('')

    if (mode === 'register' && !name.trim()) {
      setError('Please enter your name.')
      return
    }

    if (!email.trim() || !email.includes('@')) {
      setError('Please enter a valid email address.')
      return
    }

    if (mode === 'register') {
      const parsedAge = parseInt(age, 10)
      if (isNaN(parsedAge) || parsedAge < 1 || parsedAge > 120) {
        setError('Please enter a valid age (between 1 and 120).')
        return
      }
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    setLoading(true)
    const endpoint = mode === 'register' ? `${apiUrl}/api/auth/register` : `${apiUrl}/api/auth/login`
    const payload = mode === 'register'
      ? { email: email.trim(), password, name: name.trim(), age: parseInt(age, 10) }
      : { email: email.trim(), password }

    try {
      const controller = new AbortController()
      const timer = setTimeout(() => controller.abort(), 75000)

      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
      clearTimeout(timer)
      const data = await res.json()

      if (!res.ok) {
        setError(data.detail || 'Authentication failed. Please check your credentials.')
      } else {
        localStorage.setItem('asc_token', data.access_token)
        localStorage.setItem('asc_user', JSON.stringify(data.user))
        onAuthSuccess(data.user, data.access_token)
        onClose()
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Server took too long to respond. The free backend server on Render might still be waking up — please try again in 10 seconds.')
      } else {
        setError(`Unable to reach server (${apiUrl}). Please make sure your backend is running or has finished waking up.`)
      }
    } finally {
      setLoading(false)
    }
  }

  function handleGoogleClick() {
    setNotice('Google sign-in is not configured on this server. Please use email & password to sign in.')
  }

  function handleGuestMode() {
    localStorage.removeItem('asc_token')
    localStorage.removeItem('asc_user')
    onAuthSuccess(null, null)
    onClose()
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="bg-white rounded-3xl shadow-2xl max-w-md w-full p-6 space-y-5 border border-gray-100 relative">
        {/* ── Close Button ── */}
        <button
          onClick={onClose}
          className="absolute top-5 right-5 text-gray-400 hover:text-gray-700 text-lg w-8 h-8 rounded-full flex items-center justify-center hover:bg-gray-100 transition-colors"
        >
          ✕
        </button>

        {/* ── Header ── */}
        <div className="text-center pt-2">
          <div className="w-12 h-12 bg-indigo-100 text-indigo-700 rounded-2xl flex items-center justify-center mx-auto text-2xl shadow-inner mb-2">
            🎓
          </div>
          <h2 className="text-2xl font-black text-gray-800">
            {mode === 'login' ? 'Welcome Back!' : 'Create Student Account'}
          </h2>
          <p className="text-xs text-gray-500 mt-1">
            {mode === 'login'
              ? 'Log in to sync your study notes and progress across devices.'
              : 'Join to track your weak topics and practice quizzes.'}
          </p>
        </div>

        {/* ── Tabs: Login vs Register ── */}
        <div className="flex bg-gray-100 p-1 rounded-xl text-xs font-bold text-gray-600">
          <button
            onClick={() => { setMode('login'); setError(''); setNotice('') }}
            className={`flex-1 py-2 rounded-lg transition-all ${
              mode === 'login' ? 'bg-white text-indigo-700 shadow-sm' : 'hover:text-gray-900'
            }`}
          >
            Log In
          </button>
          <button
            onClick={() => { setMode('register'); setError(''); setNotice('') }}
            className={`flex-1 py-2 rounded-lg transition-all ${
              mode === 'register' ? 'bg-white text-indigo-700 shadow-sm' : 'hover:text-gray-900'
            }`}
          >
            Create Account
          </button>
        </div>

        {/* ── Error & Notice Alerts ── */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 text-rose-800 text-xs p-3 rounded-xl flex items-start gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
        )}
        {notice && (
          <div className="bg-amber-50 border border-amber-200 text-amber-800 text-xs p-3 rounded-xl flex items-start gap-2">
            <span>ℹ️</span>
            <span>{notice}</span>
          </div>
        )}

        {/* ── Form ── */}
        <form onSubmit={handleSubmit} className="space-y-3.5">
          {mode === 'register' && (
            <>
              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Full Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={e => setName(e.target.value)}
                  placeholder="e.g. Alex Sharma"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-gray-700 mb-1">Age</label>
                <input
                  type="number"
                  required
                  min="1"
                  max="120"
                  value={age}
                  onChange={e => setAge(e.target.value)}
                  placeholder="e.g. 19"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-400"
                />
              </div>
            </>
          )}

          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              placeholder="student@example.com"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-gray-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              placeholder="At least 6 characters"
              className="w-full px-3.5 py-2.5 rounded-xl border border-gray-300 text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-extrabold text-sm shadow-md transition-all disabled:opacity-60 flex items-center justify-center gap-2"
          >
            {loading && <span className="animate-spin text-sm">⏳</span>}
            {loading ? 'Connecting to backend…' : (mode === 'login' ? 'Log In' : 'Create Account')}
          </button>

          {loading && (
            <p className="text-[11px] text-amber-600 text-center animate-pulse pt-1">
              ⏳ If the free backend is waking up, this can take up to 45–60 seconds on the first request.
            </p>
          )}
        </form>

        {/* ── Social / Alternative Options ── */}
        <div className="space-y-2 pt-1 border-t border-gray-100">
          <button
            type="button"
            onClick={handleGoogleClick}
            className="w-full py-2.5 px-4 rounded-xl border border-gray-200 hover:bg-gray-50 text-gray-700 text-xs font-bold flex items-center justify-center gap-2 transition-colors"
          >
            <span>🌐</span> Continue with Google
          </button>

          <button
            type="button"
            onClick={handleGuestMode}
            className="w-full py-2 text-center text-xs text-gray-500 hover:text-indigo-600 font-semibold transition-colors"
          >
            Continue as Guest (limited features) →
          </button>
        </div>
      </div>
    </div>
  )
}
