import React, { useState } from 'react'

export function TenQuestionQuiz({ quizData, messageId, convId, apiUrl, initialAttempt, initialSuggestions, onQuizSubmitted }) {
  const questions = quizData?.questions || []
  const [answers, setAnswers] = useState({}) // { [qId]: option }
  const [attemptResult, setAttemptResult] = useState(initialAttempt || null)
  const [aiSuggestions, setAiSuggestions] = useState(initialSuggestions || '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const [currentIdx, setCurrentIdx] = useState(0)

  // If already attempted, lock into result review view (Attempt Once)
  const isLocked = Boolean(attemptResult)

  const currentQ = questions[currentIdx] || {}
  const total = questions.length

  function handleSelect(opt) {
    if (isLocked) return
    setAnswers(prev => ({ ...prev, [currentQ.id]: opt }))
  }

  async function handleSubmit() {
    setSubmitting(true)
    setError('')
    try {
      const payload = {
        message_id: messageId,
        answers: questions.map(q => ({
          question_id: q.id,
          answer: answers[q.id] || '',
        })),
      }
      const token = localStorage.getItem('asc_token')
      const headers = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      const res = await fetch(`${apiUrl}/api/chat/conversations/${convId}/messages/${messageId}/submit-quiz`, {
        method: 'POST',
        headers,
        body: JSON.stringify(payload),
      })
      const data = await res.json()
      if (!res.ok) {
        setError(data.detail || 'Could not submit quiz.')
      } else {
        setAttemptResult(data.quiz_attempt)
        setAiSuggestions(data.ai_suggestions)
        if (onQuizSubmitted) {
          onQuizSubmitted(messageId, data.quiz_attempt, data.ai_suggestions)
        }
      }
    } catch {
      setError('Network error while scoring quiz.')
    } finally {
      setSubmitting(false)
    }
  }

  if (total === 0) return null

  // ── RESULT & REVIEW VIEW (Attempted & Locked) ──
  if (isLocked && attemptResult) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-2xl border border-indigo-100 dark:border-gray-700 p-5 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b dark:border-gray-700">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🏆</span>
            <div>
              <h4 className="font-extrabold text-gray-900 dark:text-gray-100 text-sm">
                Quiz Results{quizData?.topic ? `: ${quizData.topic}` : ''} (Attempt Locked)
              </h4>
              <p className="text-[11px] text-gray-400">Attempted Once • Cannot be retaken</p>
            </div>
          </div>
          <div className="px-3 py-1 bg-indigo-50 dark:bg-indigo-900/50 border border-indigo-200 dark:border-indigo-700 rounded-full font-mono text-xs font-black text-indigo-700 dark:text-indigo-300">
            {attemptResult.score} / {attemptResult.total} ({attemptResult.accuracy_pct}%)
          </div>
        </div>

        {/* AI Pedagogical Suggestions */}
        <div className="bg-gradient-to-br from-purple-50/90 via-indigo-50/50 to-purple-50/80 dark:from-purple-950/40 dark:via-indigo-950/30 dark:to-purple-950/40 border border-purple-200 dark:border-purple-800/80 rounded-2xl p-4 sm:p-5 space-y-3 text-xs shadow-xs">
          <div className="flex items-center justify-between pb-2 border-b border-purple-200/60 dark:border-purple-800/60">
            <div className="flex items-center gap-2 font-black text-purple-900 dark:text-purple-200 uppercase tracking-wider text-xs">
              <span className="text-base">🤖</span>
              <span>AI Performance Assessment & Suggestions</span>
            </div>
            <span className="text-[10px] font-extrabold px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/60 text-purple-800 dark:text-purple-200 border border-purple-300 dark:border-purple-700">
              Personalized
            </span>
          </div>

          {aiSuggestions ? (
            <p className="text-gray-800 dark:text-gray-200 whitespace-pre-wrap leading-relaxed font-medium">
              {aiSuggestions}
            </p>
          ) : (
            <div className="space-y-2">
              <p className="text-gray-800 dark:text-gray-200 leading-relaxed font-medium">
                {attemptResult.accuracy_pct >= 80
                  ? `Outstanding mastery! You achieved ${attemptResult.score}/${attemptResult.total} (${attemptResult.accuracy_pct}%). You demonstrate a solid grasp of core fundamentals.`
                  : attemptResult.accuracy_pct >= 50
                  ? `Good effort! You scored ${attemptResult.score}/${attemptResult.total} (${attemptResult.accuracy_pct}%). You have a solid base, but key areas need targeted revision.`
                  : `Needs revision: You scored ${attemptResult.score}/${attemptResult.total} (${attemptResult.accuracy_pct}%). Don't worry — review the concept notes and re-check the missed questions below.`}
              </p>
            </div>
          )}

          {/* Weak Topics to Review */}
          {attemptResult.weak_topics?.length > 0 ? (
            <div className="mt-2 p-3 bg-amber-50 dark:bg-amber-950/50 border border-amber-200 dark:border-amber-800/80 rounded-xl text-xs text-amber-900 dark:text-amber-200 flex items-start gap-2">
              <span className="text-base shrink-0 leading-none">📌</span>
              <div>
                <span className="font-extrabold block mb-0.5">Must-Do Revision Topics:</span>
                <span>{attemptResult.weak_topics.join(', ')}</span>
              </div>
            </div>
          ) : (
            <div className="mt-2 p-3 bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800/80 rounded-xl text-xs text-emerald-900 dark:text-emerald-200 flex items-start gap-2">
              <span className="text-base shrink-0 leading-none">🌟</span>
              <div>
                <span className="font-extrabold block mb-0.5">Zero Weak Topics:</span>
                <span>You answered all questions accurately! Ready to advance to the next topic.</span>
              </div>
            </div>
          )}
        </div>

        {/* Question Review Breakdown */}
        <div className="space-y-3">
          <h5 className="font-bold text-xs uppercase tracking-wider text-gray-500 dark:text-gray-400">
            Question Breakdown
          </h5>
          {attemptResult.results?.map((r, i) => (
            <div
              key={r.id}
              className={`p-3 rounded-xl border text-xs space-y-1.5 ${
                r.is_correct
                  ? 'border-green-200 bg-green-50/40 dark:bg-green-950/20 text-gray-800 dark:text-gray-200'
                  : 'border-rose-200 bg-rose-50/40 dark:bg-rose-950/20 text-gray-800 dark:text-gray-200'
              }`}
            >
              <div className="flex justify-between font-bold">
                <span>{i + 1}. {r.question}</span>
                <span className={r.is_correct ? 'text-green-600' : 'text-rose-600'}>
                  {r.is_correct ? '✅ Correct' : '❌ Missed'}
                </span>
              </div>
              {!r.is_correct && r.student_answer && (
                <div className="text-[11px] text-gray-500">
                  Your answer: <span className="font-semibold text-rose-700">{r.student_answer}</span>
                </div>
              )}
              <div className="text-[11px] text-indigo-700 dark:text-indigo-300">
                Correct answer: <span className="font-bold">{r.correct_answer}</span>
              </div>
              {r.explanation && (
                <div className="text-[10px] text-gray-500 dark:text-gray-400 italic">
                  💡 {r.explanation}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    )
  }

  // ── ACTIVE QUIZ TAKER (Single Attempt Mode) ──
  const isAnswered = Boolean(answers[currentQ.id])
  const answeredCount = Object.keys(answers).length

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-indigo-100 dark:border-gray-700 p-5 space-y-4">
      <div className="flex items-center justify-between pb-2 border-b dark:border-gray-700">
        <div>
          <h4 className="font-extrabold text-indigo-700 dark:text-indigo-400 text-sm">
            🎯 {total}-Question Knowledge Check{quizData?.topic ? `: ${quizData.topic}` : ''}
          </h4>
          <p className="text-[11px] text-gray-400">Attempt Once • Test your mastery</p>
        </div>
        <span className="text-xs font-bold text-gray-500 dark:text-gray-400">
          Q {currentIdx + 1} / {total}
        </span>
      </div>

      {/* Question prompt */}
      <div className="text-xs font-bold text-gray-800 dark:text-gray-200 leading-relaxed">
        {currentQ.question}
      </div>

      {/* Options */}
      <div className="space-y-2">
        {currentQ.options?.map((opt, oIdx) => {
          const selected = answers[currentQ.id] === opt
          return (
            <button
              key={oIdx}
              type="button"
              onClick={() => handleSelect(opt)}
              className={`w-full text-left p-3 rounded-xl border text-xs font-medium transition-all ${
                selected
                  ? 'border-indigo-600 bg-indigo-50 dark:bg-indigo-950/50 text-indigo-900 dark:text-indigo-200 ring-2 ring-indigo-400'
                  : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 text-gray-700 dark:text-gray-300 hover:bg-gray-50'
              }`}
            >
              <span className="font-bold mr-2 text-indigo-500">{String.fromCharCode(65 + oIdx)}.</span>
              {opt}
            </button>
          )
        })}
      </div>

      {error && <div className="text-xs text-rose-600 font-bold">⚠️ {error}</div>}

      {/* Navigation & Submit */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={() => setCurrentIdx(prev => Math.max(0, prev - 1))}
          disabled={currentIdx === 0}
          className="px-3 py-1.5 rounded-lg border dark:border-gray-700 text-xs font-bold disabled:opacity-30"
        >
          ◀ Prev
        </button>

        <span className="text-[11px] text-gray-400 font-medium">
          Answered {answeredCount} / {total}
        </span>

        {currentIdx < total - 1 ? (
          <button
            type="button"
            onClick={() => setCurrentIdx(prev => Math.min(total - 1, prev + 1))}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold"
          >
            Next ▶
          </button>
        ) : (
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitting}
            className="px-4 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-bold disabled:opacity-50"
          >
            {submitting ? 'Scoring…' : '🏁 Submit Quiz'}
          </button>
        )}
      </div>
    </div>
  )
}
