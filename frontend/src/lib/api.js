import mockHealth from '../mocks/health.json'
import mockExplain from '../mocks/explain.json'
import mockQuiz from '../mocks/quiz.json'
import mockSimulations from '../mocks/simulations_catalog.json'

const rawBase = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const BASE_URL = rawBase.trim().replace(/\/+$/, '')
const PRIMARY_BASE_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`
const FALLBACK_BASE_URL = BASE_URL.endsWith('/api') ? BASE_URL.replace(/\/api$/, '') : BASE_URL

function isMockMode() {
  if (typeof window !== 'undefined') {
    if (window.ASC_MOCK === true) return true
    try {
      if (localStorage.getItem('asc_mock') === 'true') return true
    } catch {
      // ignore
    }
  }
  return false
}

const delay = (ms = 600) => new Promise((resolve) => setTimeout(resolve, ms))

async function handleMockRequest(method, path, body) {
  await delay(600)

  const normalizedPath = path.startsWith('/') ? path : `/${path}`

  if (normalizedPath.includes('/health')) {
    return mockHealth
  }

  if (normalizedPath.includes('/explain')) {
    return mockExplain
  }

  if (normalizedPath.includes('/quiz') && normalizedPath.includes('/answers')) {
    // Scoring mock response
    let score = 4
    let total = 5
    if (body && Array.isArray(body.answers)) {
      total = body.answers.length
      // Count self-marked or matching answers
      let right = 0
      body.answers.forEach((ans, idx) => {
        if (ans.is_correct === true || (ans.is_correct === null && idx !== 2)) {
          right++
        }
      })
      score = right
    }

    return {
      score,
      total,
      weak_topics: score < total ? ['Stack Underflow'] : [],
      results: mockQuiz.questions.map((q, idx) => {
        const studentAns = body?.answers?.find((a) => a.question_id === q.id)
        const isCorrect = studentAns?.is_correct ?? (idx !== 2)
        return {
          id: q.id,
          question: q.question,
          is_correct: isCorrect,
          student_answer: studentAns?.answer || (isCorrect ? q.correct_answer : 'Wrong Choice'),
          correct_answer: q.correct_answer,
          explanation: q.explanation,
        }
      }),
    }
  }

  if (normalizedPath.includes('/quiz')) {
    return mockQuiz
  }

  if (normalizedPath.includes('/simulations')) {
    return mockSimulations
  }

  return { status: 'ok', mock: true }
}

async function fetchWithFallback(path, options = {}) {
  const cleanPath = path.startsWith('/') ? path : `/${path}`

  // Check offline
  if (typeof navigator !== 'undefined' && navigator.onLine === false) {
    return {
      error: 'offline',
      message: 'You are offline. Simulations and saved content still work.',
    }
  }

  const primaryUrl = `${PRIMARY_BASE_URL}${cleanPath}`
  const fallbackUrl = `${FALLBACK_BASE_URL}${cleanPath}`

  try {
    let res = await fetch(primaryUrl, options)
    // If 404, fallback to root base URL
    if (res.status === 404) {
      try {
        const fallbackRes = await fetch(fallbackUrl, options)
        if (fallbackRes.ok || fallbackRes.status !== 404) {
          res = fallbackRes
        }
      } catch {
        // use original res
      }
    }

    if (!res.ok) {
      let detail = `Request failed with status ${res.status}`
      try {
        const errorData = await res.json()
        if (errorData && (errorData.detail || errorData.message)) {
          detail = errorData.detail || errorData.message
        }
      } catch {
        // no json body
      }
      return {
        error: res.status,
        message: detail,
      }
    }

    return await res.json()
  } catch (err) {
    return {
      error: 'offline',
      message: err.message || 'Could not reach the server. Make sure the backend is running.',
    }
  }
}

export const api = {
  async get(path) {
    if (isMockMode()) {
      return handleMockRequest('GET', path)
    }
    return fetchWithFallback(path, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
      },
    })
  },

  async post(path, body) {
    if (isMockMode()) {
      return handleMockRequest('POST', path, body)
    }
    return fetchWithFallback(path, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Accept: 'application/json',
      },
      body: JSON.stringify(body),
    })
  },

  async postForm(path, formData) {
    if (isMockMode()) {
      return handleMockRequest('POST', path, formData)
    }
    return fetchWithFallback(path, {
      method: 'POST',
      body: formData,
    })
  },
}

export default api
