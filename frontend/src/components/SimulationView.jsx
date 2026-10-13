import React, { useState } from 'react'

/**
 * StackSimulation
 * - Visual plate pile with bottom-to-top rendering
 * - Push / Pop / Peek operations
 * - Capacity limit of 5 (with clear overflow warning)
 * - Underflow alert when popping from empty
 * - Predict-then-reveal mode
 * - Live Python list code panel showing append/pop operations
 * - Custom plate label input
 */
export function StackSimulation({ onBack }) {
  const [items, setItems] = useState([])
  const [customLabel, setCustomLabel] = useState('')
  const [peekHighlight, setPeekHighlight] = useState(false)
  const [predictMode, setPredictMode] = useState(false)
  const [predictionAnswer, setPredictionAnswer] = useState('')
  const [predictionFeedback, setPredictionFeedback] = useState(null)
  const [alertMsg, setAlertMsg] = useState('')
  const [lastAction, setLastAction] = useState('Initialized empty stack: items = []')

  const MAX_CAPACITY = 5

  function handlePush() {
    setAlertMsg('')
    setPeekHighlight(false)
    if (items.length >= MAX_CAPACITY) {
      setAlertMsg('⚠️ Stack Overflow! Max capacity (5 plates) reached. Pop an item before adding more.')
      return
    }
    const label = customLabel.trim() || `Plate ${items.length + 1}`
    const updated = [...items, label]
    setItems(updated)
    setCustomLabel('')
    setLastAction(`stack.append("${label}") # Pushed onto top of stack`)
  }

  function handlePop() {
    setAlertMsg('')
    setPeekHighlight(false)
    if (items.length === 0) {
      setAlertMsg('⚠️ Stack Underflow! Cannot pop from an empty stack.')
      return
    }

    if (predictMode && !predictionAnswer) {
      setAlertMsg('🤔 Predict first: Which item will be removed?')
      return
    }

    if (predictMode && predictionAnswer) {
      const expected = items[items.length - 1]
      if (predictionAnswer.toLowerCase().trim() === expected.toLowerCase().trim()) {
        setPredictionFeedback({ correct: true, text: `🎉 Correct! "${expected}" was the topmost plate (LIFO).` })
      } else {
        setPredictionFeedback({ correct: false, text: `❌ Not quite! Top item was "${expected}", not "${predictionAnswer}".` })
      }
    }

    const popped = items[items.length - 1]
    const updated = items.slice(0, -1)
    setItems(updated)
    setLastAction(`popped = stack.pop() # Removed "${popped}" from top`)
    setPredictionAnswer('')
  }

  function handlePeek() {
    setAlertMsg('')
    if (items.length === 0) {
      setAlertMsg('⚠️ Stack is empty! Nothing to peek.')
      return
    }
    setPeekHighlight(true)
    const topItem = items[items.length - 1]
    setLastAction(`top = stack[-1] # Peeked at top item: "${topItem}"`)
  }

  function handleClear() {
    setItems([])
    setAlertMsg('')
    setPeekHighlight(false)
    setPredictionFeedback(null)
    setLastAction('stack.clear() # Emptied stack')
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-indigo-100 dark:border-gray-700 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b dark:border-gray-700">
        <div>
          <h4 className="font-extrabold text-indigo-700 dark:text-indigo-400 text-sm flex items-center gap-2">
            <span>📚</span> Interactive Stack Simulation (LIFO)
          </h4>
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            Last-In, First-Out principle visualized as a pile of cafeteria plates.
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-[11px] font-bold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            ✕ Close
          </button>
        )}
      </div>

      {/* Everyday Analogy Banner */}
      <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl p-3 text-xs text-amber-900 dark:text-amber-200">
        💡 <strong>Everyday Analogy:</strong> Think of a spring-loaded cafeteria plate dispenser. You always place a clean plate onto the <em>top</em> (Push), and you can only take the <em>topmost</em> plate off (Pop). The bottom plate was added first, but gets taken last!
      </div>

      {/* Visual Canvas & Code Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Visualizer Pile */}
        <div className="p-4 bg-slate-50 dark:bg-gray-900 rounded-xl border dark:border-gray-700 flex flex-col items-center justify-end min-h-[260px] relative">
          <div className="absolute top-2 left-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
            Stack Pile ({items.length}/{MAX_CAPACITY})
          </div>

          {items.length === 0 ? (
            <div className="text-center text-xs text-gray-400 py-12">
              (Stack is empty. Type a label and click "Push" below!)
            </div>
          ) : (
            <div className="w-full max-w-[220px] flex flex-col-reverse gap-2">
              {items.map((item, idx) => {
                const isTop = idx === items.length - 1
                return (
                  <div
                    key={idx}
                    className={`py-2 px-3 rounded-xl border text-center font-bold text-xs transition-all shadow-sm flex items-center justify-between ${
                      isTop && peekHighlight
                        ? 'bg-amber-500 text-white border-amber-600 ring-4 ring-amber-300 dark:ring-amber-900'
                        : isTop
                        ? 'bg-indigo-600 text-white border-indigo-700 ring-2 ring-indigo-300 dark:ring-indigo-900'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <span>{item}</span>
                    {isTop && (
                      <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-black/20 text-white font-mono">
                        TOP (Index {idx})
                      </span>
                    )}
                  </div>
                )
              })}
            </div>
          )}
          {/* Base of plate holder */}
          <div className="w-full max-w-[240px] h-2 bg-gray-400 dark:bg-gray-600 rounded-b-md mt-2" />
        </div>

        {/* Live Python Code Panel & Status */}
        <div className="space-y-3 flex flex-col justify-between">
          <div className="bg-gray-900 text-emerald-400 rounded-xl p-3 font-mono text-xs shadow-inner space-y-1">
            <div className="text-gray-400 text-[10px] uppercase font-bold border-b border-gray-800 pb-1 flex justify-between">
              <span>Python List Implementation</span>
              <span>LIFO</span>
            </div>
            <p className="text-gray-400"># Current State:</p>
            <p className="text-indigo-300">stack = {JSON.stringify(items)}</p>
            <p className="text-gray-400 pt-1"># Last Operation:</p>
            <p className="text-amber-300 font-bold">{lastAction}</p>
          </div>

          {/* Predict Mode Toggle */}
          <div className="bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-xl p-3 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-indigo-900 dark:text-indigo-300">
                🎯 Predict-then-Reveal Challenge
              </span>
              <button
                onClick={() => {
                  setPredictMode(!predictMode)
                  setPredictionFeedback(null)
                }}
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full transition-all ${
                  predictMode
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                {predictMode ? 'Active (ON)' : 'Inactive (OFF)'}
              </button>
            </div>
            {predictMode && (
              <div className="space-y-1 pt-1">
                <p className="text-[11px] text-gray-600 dark:text-gray-400">
                  Before clicking Pop, predict which item will leave:
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={predictionAnswer}
                    onChange={(e) => setPredictionAnswer(e.target.value)}
                    placeholder="Type predicted item name..."
                    className="flex-1 px-2.5 py-1 text-xs rounded-lg border dark:border-gray-700 bg-white dark:bg-gray-900"
                  />
                </div>
                {predictionFeedback && (
                  <p className={`text-[11px] font-bold pt-1 ${predictionFeedback.correct ? 'text-emerald-600' : 'text-red-500'}`}>
                    {predictionFeedback.text}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alert banner */}
      {alertMsg && (
        <div className="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-xs text-red-700 dark:text-red-300 font-bold">
          {alertMsg}
        </div>
      )}

      {/* Interactive Controls */}
      <div className="flex flex-wrap items-center gap-2 pt-1 border-t dark:border-gray-700">
        <input
          type="text"
          value={customLabel}
          onChange={(e) => setCustomLabel(e.target.value)}
          placeholder="Custom plate label..."
          className="px-3 py-1.5 text-xs rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-900 max-w-[170px]"
          onKeyDown={(e) => { if (e.key === 'Enter') handlePush() }}
        />
        <button
          onClick={handlePush}
          disabled={items.length >= MAX_CAPACITY}
          className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm disabled:opacity-40"
        >
          ➕ Push (Add)
        </button>
        <button
          onClick={handlePop}
          disabled={items.length === 0}
          className="px-3.5 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs shadow-sm disabled:opacity-40"
        >
          ➖ Pop (Remove)
        </button>
        <button
          onClick={handlePeek}
          disabled={items.length === 0}
          className="px-3.5 py-1.5 rounded-xl border border-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950 text-amber-700 dark:text-amber-400 font-bold text-xs disabled:opacity-40"
        >
          👁️ Peek (Inspect Top)
        </button>
        <button
          onClick={handleClear}
          className="ml-auto text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline"
        >
          Clear Stack
        </button>
      </div>
    </div>
  )
}

/**
 * QueueSimulation
 * - Visual waiting line with FRONT and REAR markers
 * - Enqueue (adds to rear) / Dequeue (removes from front) / Peek
 * - Capacity limit of 5 (with overflow alert)
 * - Underflow alert when dequeuing from empty
 * - Predict-then-reveal mode
 * - Live Python collections.deque code panel
 * - Custom person label input
 */
export function QueueSimulation({ onBack }) {
  const [items, setItems] = useState([])
  const [customLabel, setCustomLabel] = useState('')
  const [peekHighlight, setPeekHighlight] = useState(false)
  const [predictMode, setPredictMode] = useState(false)
  const [predictionAnswer, setPredictionAnswer] = useState('')
  const [predictionFeedback, setPredictionFeedback] = useState(null)
  const [alertMsg, setAlertMsg] = useState('')
  const [lastAction, setLastAction] = useState('Initialized empty queue: deque([])')

  const MAX_CAPACITY = 5

  function handleEnqueue() {
    setAlertMsg('')
    setPeekHighlight(false)
    if (items.length >= MAX_CAPACITY) {
      setAlertMsg('⚠️ Queue Overflow! Max line capacity (5 people) reached. Dequeue someone first.')
      return
    }
    const label = customLabel.trim() || `Person ${items.length + 1}`
    const updated = [...items, label]
    setItems(updated)
    setCustomLabel('')
    setLastAction(`queue.append("${label}") # Joined rear of line`)
  }

  function handleDequeue() {
    setAlertMsg('')
    setPeekHighlight(false)
    if (items.length === 0) {
      setAlertMsg('⚠️ Queue Underflow! Cannot dequeue from an empty queue.')
      return
    }

    if (predictMode && !predictionAnswer) {
      setAlertMsg('🤔 Predict first: Who will be served next from the front?')
      return
    }

    if (predictMode && predictionAnswer) {
      const expected = items[0]
      if (predictionAnswer.toLowerCase().trim() === expected.toLowerCase().trim()) {
        setPredictionFeedback({ correct: true, text: `🎉 Correct! "${expected}" was served first (FIFO).` })
      } else {
        setPredictionFeedback({ correct: false, text: `❌ Not quite! Front person was "${expected}", not "${predictionAnswer}".` })
      }
    }

    const removed = items[0]
    const updated = items.slice(1)
    setItems(updated)
    setLastAction(`served = queue.popleft() # Served "${removed}" from front`)
    setPredictionAnswer('')
  }

  function handlePeek() {
    setAlertMsg('')
    if (items.length === 0) {
      setAlertMsg('⚠️ Queue is empty! Nobody at the front.')
      return
    }
    setPeekHighlight(true)
    const frontItem = items[0]
    setLastAction(`front = queue[0] # Checked front of line: "${frontItem}"`)
  }

  function handleClear() {
    setItems([])
    setAlertMsg('')
    setPeekHighlight(false)
    setPredictionFeedback(null)
    setLastAction('queue.clear() # Emptied line')
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-indigo-100 dark:border-gray-700 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b dark:border-gray-700">
        <div>
          <h4 className="font-extrabold text-indigo-700 dark:text-indigo-400 text-sm flex items-center gap-2">
            <span>🎟️</span> Interactive Queue Simulation (FIFO)
          </h4>
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            First-In, First-Out principle visualized as a ticket counter waiting line.
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-[11px] font-bold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            ✕ Close
          </button>
        )}
      </div>

      {/* Everyday Analogy Banner */}
      <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl p-3 text-xs text-amber-900 dark:text-amber-200">
        💡 <strong>Everyday Analogy:</strong> Think of people waiting in line at a movie ticket counter. The first person to arrive is the first person served (FIFO). New arrivals always join at the <em>back (rear)</em>, and served customers leave from the <em>front</em>!
      </div>

      {/* Visual Canvas & Code Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Waiting Line Canvas */}
        <div className="p-4 bg-slate-50 dark:bg-gray-900 rounded-xl border dark:border-gray-700 flex flex-col justify-center min-h-[260px] relative">
          <div className="flex justify-between items-center text-[10px] font-bold text-gray-400 uppercase tracking-wider mb-4">
            <span>Ticket Counter 🎟️ (FRONT)</span>
            <span>Arrivals 🚶 (REAR)</span>
          </div>

          {items.length === 0 ? (
            <div className="text-center text-xs text-gray-400 py-12">
              (Waiting line is empty. Type a label and click "Enqueue" below!)
            </div>
          ) : (
            <div className="flex items-center gap-2 overflow-x-auto py-2">
              {items.map((item, idx) => {
                const isFront = idx === 0
                const isRear = idx === items.length - 1
                return (
                  <div
                    key={idx}
                    className={`min-w-[90px] py-3 px-2 rounded-xl border text-center font-bold text-xs transition-all shadow-sm flex flex-col items-center gap-1 ${
                      isFront && peekHighlight
                        ? 'bg-amber-500 text-white border-amber-600 ring-4 ring-amber-300 dark:ring-amber-900'
                        : isFront
                        ? 'bg-emerald-600 text-white border-emerald-700 ring-2 ring-emerald-300 dark:ring-emerald-900'
                        : isRear
                        ? 'bg-indigo-600 text-white border-indigo-700'
                        : 'bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-200 border-gray-200 dark:border-gray-700'
                    }`}
                  >
                    <span className="text-lg">👤</span>
                    <span className="truncate w-full">{item}</span>
                    <span className="text-[9px] font-mono uppercase bg-black/20 text-white px-1 py-0.5 rounded">
                      {isFront ? 'FRONT' : isRear ? 'REAR' : `#${idx + 1}`}
                    </span>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Live Python Code Panel & Status */}
        <div className="space-y-3 flex flex-col justify-between">
          <div className="bg-gray-900 text-emerald-400 rounded-xl p-3 font-mono text-xs shadow-inner space-y-1">
            <div className="text-gray-400 text-[10px] uppercase font-bold border-b border-gray-800 pb-1 flex justify-between">
              <span>collections.deque Implementation</span>
              <span>FIFO</span>
            </div>
            <p className="text-gray-400"># Current State:</p>
            <p className="text-indigo-300">queue = deque({JSON.stringify(items)})</p>
            <p className="text-gray-400 pt-1"># Last Operation:</p>
            <p className="text-amber-300 font-bold">{lastAction}</p>
          </div>

          {/* Predict Mode Toggle */}
          <div className="bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-xl p-3 text-xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-indigo-900 dark:text-indigo-300">
                🎯 Predict-then-Reveal Challenge
              </span>
              <button
                onClick={() => {
                  setPredictMode(!predictMode)
                  setPredictionFeedback(null)
                }}
                className={`text-[10px] font-bold px-2 py-0.5 rounded-full transition-all ${
                  predictMode
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                }`}
              >
                {predictMode ? 'Active (ON)' : 'Inactive (OFF)'}
              </button>
            </div>
            {predictMode && (
              <div className="space-y-1 pt-1">
                <p className="text-[11px] text-gray-600 dark:text-gray-400">
                  Before clicking Dequeue, predict who will leave first:
                </p>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={predictionAnswer}
                    onChange={(e) => setPredictionAnswer(e.target.value)}
                    placeholder="Type predicted person label..."
                    className="flex-1 px-2.5 py-1 text-xs rounded-lg border dark:border-gray-700 bg-white dark:bg-gray-900"
                  />
                </div>
                {predictionFeedback && (
                  <p className={`text-[11px] font-bold pt-1 ${predictionFeedback.correct ? 'text-emerald-600' : 'text-red-500'}`}>
                    {predictionFeedback.text}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Alert banner */}
      {alertMsg && (
        <div className="p-2.5 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800 rounded-xl text-xs text-red-700 dark:text-red-300 font-bold">
          {alertMsg}
        </div>
      )}

      {/* Interactive Controls */}
      <div className="flex flex-wrap items-center gap-2 pt-1 border-t dark:border-gray-700">
        <input
          type="text"
          value={customLabel}
          onChange={(e) => setCustomLabel(e.target.value)}
          placeholder="Custom person label..."
          className="px-3 py-1.5 text-xs rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-900 max-w-[170px]"
          onKeyDown={(e) => { if (e.key === 'Enter') handleEnqueue() }}
        />
        <button
          onClick={handleEnqueue}
          disabled={items.length >= MAX_CAPACITY}
          className="px-3.5 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow-sm disabled:opacity-40"
        >
          ➕ Enqueue (Join Rear)
        </button>
        <button
          onClick={handleDequeue}
          disabled={items.length === 0}
          className="px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs shadow-sm disabled:opacity-40"
        >
          ➖ Dequeue (Leave Front)
        </button>
        <button
          onClick={handlePeek}
          disabled={items.length === 0}
          className="px-3.5 py-1.5 rounded-xl border border-amber-500 hover:bg-amber-50 dark:hover:bg-amber-950 text-amber-700 dark:text-amber-400 font-bold text-xs disabled:opacity-40"
        >
          👁️ Peek (Inspect Front)
        </button>
        <button
          onClick={handleClear}
          className="ml-auto text-[11px] text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 underline"
        >
          Clear Line
        </button>
      </div>
    </div>
  )
}

/**
 * SortingSimulation
 * - Bubble Sort, Selection Sort, and Insertion Sort step-through
 * - Interactive step controls: Back, Forward, Reset
 * - Comparisons in plain words ("Is 8 greater than 3? Yes, so swap them!")
 * - Predict-then-reveal mode
 * - Visual bar / card height rendering with active comparison highlight
 * - Live Python algorithm code panel
 */
export function SortingSimulation({ onBack }) {
  const [algorithm, setAlgorithm] = useState('bubble') // bubble | selection | insertion
  const [arrayInput, setArrayInput] = useState('5, 3, 8, 4, 2')
  const [steps, setSteps] = useState([])
  const [currentStepIdx, setCurrentStepIdx] = useState(0)
  const [predictMode, setPredictMode] = useState(false)
  const [predictSwap, setPredictSwap] = useState(null) // true | false
  const [predictionFeedback, setPredictionFeedback] = useState(null)

  // Generate steps based on algorithm
  function generateStepsFor(arr, algo) {
    const generated = []
    const a = [...arr]
    const n = a.length

    if (algo === 'bubble') {
      generated.push({
        array: [...a],
        comparing: [],
        swapped: false,
        explanation: 'Initial unsorted numbers: [' + a.join(', ') + ']. We compare adjacent pairs.',
        codeSnippet: '# Bubble sort starts:\nfor i in range(n):\n    for j in range(0, n - i - 1):',
      })
      for (let i = 0; i < n; i++) {
        for (let j = 0; j < n - i - 1; j++) {
          const shouldSwap = a[j] > a[j + 1]
          generated.push({
            array: [...a],
            comparing: [j, j + 1],
            willSwap: shouldSwap,
            explanation: `Comparing adjacent numbers ${a[j]} and ${a[j + 1]}. Is ${a[j]} > ${a[j + 1]}? ${shouldSwap ? 'Yes! They are out of order, so swap.' : 'No! Already in correct order.'}`,
            codeSnippet: `if arr[${j}] > arr[${j + 1}]: # ${a[j]} > ${a[j + 1]}\n    arr[${j}], arr[${j + 1}] = arr[${j + 1}], arr[${j}]`,
          })
          if (shouldSwap) {
            const temp = a[j]
            a[j] = a[j + 1]
            a[j + 1] = temp
            generated.push({
              array: [...a],
              comparing: [j, j + 1],
              swapped: true,
              explanation: `Swapped! Now ${a[j]} is before ${a[j + 1]}.`,
              codeSnippet: `# Array updated: [${a.join(', ')}]`,
            })
          }
        }
      }
      generated.push({
        array: [...a],
        comparing: [],
        completed: true,
        explanation: '🎉 All elements are now fully sorted in ascending order!',
        codeSnippet: '# Final sorted array:\nreturn arr',
      })
    } else if (algo === 'selection') {
      generated.push({
        array: [...a],
        comparing: [],
        explanation: 'Initial unsorted numbers: [' + a.join(', ') + ']. We find the smallest item and place it first.',
        codeSnippet: '# Selection sort starts:\nfor i in range(n):\n    min_idx = i',
      })
      for (let i = 0; i < n - 1; i++) {
        let minIdx = i
        for (let j = i + 1; j < n; j++) {
          generated.push({
            array: [...a],
            comparing: [minIdx, j],
            explanation: `Checking if ${a[j]} is smaller than current minimum ${a[minIdx]}.`,
            codeSnippet: `if arr[${j}] < arr[${minIdx}]:\n    min_idx = ${j}`,
          })
          if (a[j] < a[minIdx]) {
            minIdx = j
          }
        }
        if (minIdx !== i) {
          const temp = a[i]
          a[i] = a[minIdx]
          a[minIdx] = temp
          generated.push({
            array: [...a],
            comparing: [i, minIdx],
            swapped: true,
            explanation: `Smallest found was ${a[i]}. Swapped into position ${i}.`,
            codeSnippet: `arr[${i}], arr[${minIdx}] = arr[${minIdx}], arr[${i}]`,
          })
        }
      }
      generated.push({
        array: [...a],
        comparing: [],
        completed: true,
        explanation: '🎉 Selection sort complete! All numbers are sorted.',
        codeSnippet: '# Final sorted array:\nreturn arr',
      })
    } else { // insertion
      generated.push({
        array: [...a],
        comparing: [],
        explanation: 'Initial numbers: [' + a.join(', ') + ']. We insert each card into its sorted place like a hand of cards.',
        codeSnippet: '# Insertion sort starts:\nfor i in range(1, len(arr)):',
      })
      for (let i = 1; i < n; i++) {
        const key = a[i]
        let j = i - 1
        generated.push({
          array: [...a],
          comparing: [i],
          explanation: `Taking card ${key} to insert into the sorted portion to the left.`,
          codeSnippet: `key = arr[${i}] # ${key}`,
        })
        while (j >= 0 && a[j] > key) {
          generated.push({
            array: [...a],
            comparing: [j, j + 1],
            explanation: `${a[j]} is greater than ${key}, so shift ${a[j]} right.`,
            codeSnippet: `arr[${j + 1}] = arr[${j}]`,
          })
          a[j + 1] = a[j]
          j--
        }
        a[j + 1] = key
        generated.push({
          array: [...a],
          comparing: [j + 1],
          explanation: `Inserted ${key} at position ${j + 1}.`,
          codeSnippet: `arr[${j + 1}] = key`,
        })
      }
      generated.push({
        array: [...a],
        comparing: [],
        completed: true,
        explanation: '🎉 Insertion sort complete! All items in place.',
        codeSnippet: '# Final sorted array:\nreturn arr',
      })
    }

    return generated
  }

  // Initialize steps
  React.useEffect(() => {
    const parsed = arrayInput
      .split(',')
      .map(s => parseInt(s.trim(), 10))
      .filter(n => !isNaN(n))
    const valid = parsed.length >= 2 ? parsed.slice(0, 7) : [5, 3, 8, 4, 2]
    const gen = generateStepsFor(valid, algorithm)
    setSteps(gen)
    setCurrentStepIdx(0)
    setPredictionFeedback(null)
    setPredictSwap(null)
  }, [algorithm, arrayInput])

  const step = steps[currentStepIdx] || {
    array: [5, 3, 8, 4, 2],
    comparing: [],
    explanation: 'Ready to sort.',
    codeSnippet: '# Sorting algorithm',
  }

  function handleNext() {
    if (currentStepIdx < steps.length - 1) {
      if (predictMode && step.willSwap !== undefined && predictSwap === null) {
        setPredictionFeedback({ note: true, text: '🤔 Predict first: Will these two numbers swap?' })
        return
      }
      if (predictMode && step.willSwap !== undefined && predictSwap !== null) {
        if (predictSwap === step.willSwap) {
          setPredictionFeedback({ correct: true, text: `🎉 Correct prediction! (Swap = ${step.willSwap})` })
        } else {
          setPredictionFeedback({ correct: false, text: `❌ Not quite! Expected swap was ${step.willSwap}.` })
        }
      }
      setCurrentStepIdx(prev => prev + 1)
      setPredictSwap(null)
    }
  }

  function handlePrev() {
    if (currentStepIdx > 0) {
      setCurrentStepIdx(prev => prev - 1)
      setPredictionFeedback(null)
      setPredictSwap(null)
    }
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-2xl border border-indigo-100 dark:border-gray-700 p-5 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b dark:border-gray-700">
        <div>
          <h4 className="font-extrabold text-indigo-700 dark:text-indigo-400 text-sm flex items-center gap-2">
            <span>📊</span> Interactive Sorting Visualizer
          </h4>
          <p className="text-[11px] text-gray-500 dark:text-gray-400">
            Step-by-step visual sorting with comparisons explained in plain words.
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-[11px] font-bold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            ✕ Close
          </button>
        )}
      </div>

      {/* Algorithm selector pills */}
      <div className="flex items-center gap-2">
        <span className="text-[11px] font-bold text-gray-400 uppercase">Algorithm:</span>
        {[
          { id: 'bubble', label: 'Bubble Sort' },
          { id: 'selection', label: 'Selection Sort' },
          { id: 'insertion', label: 'Insertion Sort' },
        ].map(a => (
          <button
            key={a.id}
            onClick={() => setAlgorithm(a.id)}
            className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
              algorithm === a.id
                ? 'bg-indigo-600 text-white shadow-sm'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-gray-200'
            }`}
          >
            {a.label}
          </button>
        ))}
      </div>

      {/* Everyday Analogy Banner */}
      <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-xl p-3 text-xs text-amber-900 dark:text-amber-200">
        💡 <strong>Everyday Analogy:</strong>
        {algorithm === 'bubble' && ' Think of bubbles rising in soda: larger bubbles rise to the top (right) faster through repeated adjacent swaps.'}
        {algorithm === 'selection' && ' Think of picking the shortest student in a group, having them step to the front, and repeating for the next shortest.'}
        {algorithm === 'insertion' && ' Think of arranging playing cards in your hand: take each card one by one and insert it into its sorted spot.'}
      </div>

      {/* Visual Bars Canvas */}
      <div className="p-4 bg-slate-50 dark:bg-gray-900 rounded-xl border dark:border-gray-700 flex flex-col items-center justify-end min-h-[190px] relative">
        <div className="absolute top-2 left-3 text-[10px] font-bold text-gray-400 uppercase tracking-wider">
          Array State (Step {currentStepIdx + 1} of {Math.max(steps.length, 1)})
        </div>

        <div className="flex items-end justify-center gap-3 w-full max-w-[340px] h-[130px] pt-6">
          {step.array.map((val, idx) => {
            const isComparing = step.comparing.includes(idx)
            const heightPercent = Math.max(25, Math.min(100, val * 12))
            return (
              <div key={idx} className="flex-1 flex flex-col items-center gap-1">
                <span className="text-[11px] font-bold text-gray-700 dark:text-gray-300">{val}</span>
                <div
                  style={{ height: `${heightPercent}%` }}
                  className={`w-full rounded-t-lg transition-all shadow-sm ${
                    isComparing
                      ? 'bg-amber-500 ring-4 ring-amber-300 dark:ring-amber-900'
                      : 'bg-indigo-600 dark:bg-indigo-500'
                  }`}
                />
                <span className="text-[9px] font-mono text-gray-400">[{idx}]</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Narrative & Code panel */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        <div className="bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-xl p-3 text-xs text-gray-800 dark:text-gray-200 flex flex-col justify-between">
          <div>
            <span className="font-bold text-indigo-700 dark:text-indigo-400 block mb-1">
              Step Explanation (In Plain Words):
            </span>
            <p className="leading-relaxed">{step.explanation}</p>
          </div>

          {/* Predict Mode for Sorting */}
          {step.willSwap !== undefined && (
            <div className="pt-2 mt-2 border-t dark:border-gray-700 space-y-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-indigo-900 dark:text-indigo-300">
                  🎯 Predict: Will these two numbers swap?
                </span>
                <button
                  onClick={() => setPredictMode(!predictMode)}
                  className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                    predictMode ? 'bg-indigo-600 text-white' : 'bg-gray-200 dark:bg-gray-700'
                  }`}
                >
                  {predictMode ? 'ON' : 'OFF'}
                </button>
              </div>
              {predictMode && (
                <div className="flex gap-2 pt-1">
                  <button
                    onClick={() => setPredictSwap(true)}
                    className={`flex-1 py-1 rounded text-xs font-bold border ${
                      predictSwap === true ? 'bg-amber-500 text-white border-amber-600' : 'bg-white dark:bg-gray-800'
                    }`}
                  >
                    Yes, Swap
                  </button>
                  <button
                    onClick={() => setPredictSwap(false)}
                    className={`flex-1 py-1 rounded text-xs font-bold border ${
                      predictSwap === false ? 'bg-indigo-600 text-white border-indigo-700' : 'bg-white dark:bg-gray-800'
                    }`}
                  >
                    No Swap
                  </button>
                </div>
              )}
              {predictionFeedback && (
                <p className={`text-[10px] font-bold ${predictionFeedback.correct ? 'text-emerald-600' : 'text-red-500'}`}>
                  {predictionFeedback.text}
                </p>
              )}
            </div>
          )}
        </div>

        <div className="bg-gray-900 text-emerald-400 rounded-xl p-3 font-mono text-xs shadow-inner space-y-1">
          <div className="text-gray-400 text-[10px] uppercase font-bold border-b border-gray-800 pb-1">
            Python Code Execution
          </div>
          <pre className="text-emerald-300 whitespace-pre-wrap leading-tight text-[11px]">{step.codeSnippet}</pre>
        </div>
      </div>

      {/* Stepper Navigation Controls */}
      <div className="flex items-center justify-between pt-2 border-t dark:border-gray-700">
        <button
          onClick={handlePrev}
          disabled={currentStepIdx === 0}
          className="px-3 py-1.5 rounded-lg border dark:border-gray-700 text-xs font-bold disabled:opacity-30"
        >
          ◀ Back
        </button>
        <span className="text-[11px] font-bold text-gray-500">
          Step {currentStepIdx + 1} of {Math.max(steps.length, 1)}
        </span>
        <button
          onClick={handleNext}
          disabled={currentStepIdx >= steps.length - 1}
          className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold disabled:opacity-30"
        >
          {currentStepIdx >= steps.length - 1 ? 'Completed 🎉' : 'Forward ▶'}
        </button>
      </div>
    </div>
  )
}

/**
 * Universal Simulation View router:
 * Automatically routes to Stack, Queue, Sorting, or Process demonstration based on template
 */
export function ProcessSimulationView({ plan, onBack }) {
  const template = plan?.template?.toLowerCase() || 'process'
  const title = (plan?.title || '').toLowerCase()
  const intro = (plan?.intro || '').toLowerCase()

  // Dedicated Stack/Queue graphical widget is ONLY used if the simulation is genuinely about Stack or Queue
  const isDedicatedStack = template === 'stack' && (title.includes('stack') || intro.includes('stack') || intro.includes('lifo'))
  const isDedicatedQueue = template === 'queue' && (title.includes('queue') || intro.includes('queue') || intro.includes('fifo'))

  if (isDedicatedStack) {
    return <StackSimulation onBack={onBack} />
  }
  if (isDedicatedQueue) {
    return <QueueSimulation onBack={onBack} />
  }
  if (template === 'sorting' && (title.includes('sort') || intro.includes('sort'))) {
    return <SortingSimulation onBack={onBack} />
  }

  // Universal Process Simulation tailored directly to what the student asked and what the software answered
  return <UniversalProcessSimulation plan={plan} onBack={onBack} />
}

function UniversalProcessSimulation({ plan, onBack }) {
  // Normalize parts from plan.parts or plan.steps
  const parts = React.useMemo(() => {
    if (Array.isArray(plan?.parts) && plan.parts.length > 0) {
      return plan.parts.map((p, idx) => ({
        id: p.id || idx + 1,
        name: p.name || `Part ${idx + 1}`,
        role: p.role || 'Process Component',
        details: p.details || p.description || '',
        status: p.status || 'active',
      }))
    }
    if (Array.isArray(plan?.steps) && plan.steps.length > 0) {
      return plan.steps.map((s, idx) => ({
        id: s.id || s.step_number || idx + 1,
        name: s.title || s.name || `Part ${idx + 1}`,
        role: s.role || (s.element_states ? s.element_states.join(' • ') : `Component ${idx + 1}`),
        details: s.description || s.details || '',
        status: 'active',
      }))
    }
    return [
      { id: 1, name: 'Input & Initiation', role: 'Receives and validates input trigger', details: 'The entry point capturing raw parameters or signals.', status: 'active' },
      { id: 2, name: 'Core Processing Unit', role: 'Applies state transformations and logical rules', details: 'Executes core algorithms, computation, or business rules.', status: 'active' },
      { id: 3, name: 'Output & Resolution', role: 'Produces formatted output and updates state', details: 'The final destination delivering completed results.', status: 'active' },
    ]
  }, [plan])

  const [activePartId, setActivePartId] = useState(parts[0]?.id || 1)
  const [isSimulatingFlow, setIsSimulatingFlow] = useState(false)
  const [selectedPrediction, setSelectedPrediction] = useState(null)
  const [showPredictionFeedback, setShowPredictionFeedback] = useState(false)

  // Simulation flow animation across all parts
  const handleRunFlow = () => {
    if (isSimulatingFlow) return
    setIsSimulatingFlow(true)
    parts.forEach((p, idx) => {
      setTimeout(() => {
        setActivePartId(p.id)
        if (idx === parts.length - 1) {
          setTimeout(() => setIsSimulatingFlow(false), 900)
        }
      }, idx * 800)
    })
  }

  const prediction = plan?.prediction || plan?.steps?.[0]?.prediction

  return (
    <div className="bg-white dark:bg-gray-800 rounded-3xl border border-indigo-100 dark:border-gray-700 p-5 sm:p-6 space-y-5 shadow-xs">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b dark:border-gray-700">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-base">⚙️</span>
            <h4 className="font-extrabold text-indigo-700 dark:text-indigo-400 text-sm sm:text-base">
              {plan?.title || 'Single-Phase Process Architecture'}
            </h4>
          </div>
          <p className="text-[11px] sm:text-xs text-gray-500 dark:text-gray-400 mt-0.5">
            {plan?.intro || 'Comprehensive single-phase visual diagram showing all system components simultaneously.'}
          </p>
        </div>
        {onBack && (
          <button
            onClick={onBack}
            className="text-xs font-bold text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          >
            ✕ Close
          </button>
        )}
      </div>

      {/* Everyday Analogy Banner */}
      {plan?.analogy && (
        <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 rounded-2xl p-3.5 text-xs text-amber-900 dark:text-amber-200 leading-relaxed">
          💡 <strong>Everyday Analogy:</strong> {plan.analogy}
        </div>
      )}

      {/* Visual Canvas: Single Phase Pipeline Flow */}
      <div className="p-5 bg-gradient-to-br from-slate-900 via-gray-900 to-indigo-950 rounded-2xl border border-indigo-900/50 shadow-inner space-y-4 relative overflow-hidden">
        {/* Background circuit grid */}
        <div className="absolute inset-0 bg-[radial-gradient(#4f46e5_1px,transparent_1px)] [background-size:16px_16px] opacity-20 pointer-events-none" />

        <div className="flex items-center justify-between z-10 relative flex-wrap gap-2">
          <div className="text-[10px] font-black uppercase tracking-widest text-indigo-300 flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping inline-block" />
            <span>Unified Process Pipeline ({parts.length} Connected Parts)</span>
          </div>

          <button
            onClick={handleRunFlow}
            disabled={isSimulatingFlow}
            className="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white rounded-lg text-[11px] font-bold transition-all shadow-xs flex items-center gap-1.5"
          >
            <span>{isSimulatingFlow ? '⚡ Flowing…' : '▶ Simulate Flow'}</span>
          </button>
        </div>

        {/* Visual interconnected nodes in single view (Fully scrollable without left clipping) */}
        <div className="w-full overflow-x-auto py-3 z-10 relative">
          <div className="flex items-center gap-2 sm:gap-3 min-w-max px-4 mx-auto w-fit">
            {parts.map((p, idx) => {
              const isSelected = p.id === activePartId
              return (
                <React.Fragment key={p.id}>
                  {idx > 0 && (
                    <div className="text-indigo-400/80 font-mono text-base select-none shrink-0 flex items-center px-0.5">
                      <span className={isSimulatingFlow ? 'animate-pulse text-indigo-300 font-bold' : ''}>➔</span>
                    </div>
                  )}
                  <button
                    type="button"
                    onClick={() => setActivePartId(p.id)}
                    className={`group px-3.5 py-2.5 rounded-2xl text-left font-bold text-xs shadow-md transition-all duration-300 shrink-0 border cursor-pointer ${
                      isSelected
                        ? 'bg-gradient-to-r from-indigo-600 to-violet-600 text-white border-indigo-400 ring-2 ring-indigo-400/60 scale-105 shadow-indigo-500/40'
                        : 'bg-gray-800/90 text-gray-200 border-gray-700/80 hover:bg-gray-750 hover:border-indigo-500/50'
                    }`}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-[10px] px-1.5 py-0.2 rounded font-black uppercase tracking-wider ${
                        isSelected ? 'bg-white/20 text-white' : 'bg-indigo-950 text-indigo-300 border border-indigo-800'
                      }`}>
                        Part {idx + 1}
                      </span>
                      <span className={`w-2 h-2 rounded-full ${isSelected ? 'bg-emerald-300 animate-pulse' : 'bg-gray-500'}`} />
                    </div>
                    <div className="tracking-tight text-xs whitespace-nowrap">{p.name}</div>
                    <div className={`text-[10px] truncate max-w-[130px] font-normal ${isSelected ? 'text-indigo-100' : 'text-gray-400'}`}>
                      {p.role}
                    </div>
                  </button>
                </React.Fragment>
              )
            })}
          </div>
        </div>
      </div>

      {/* Parts Breakdown Section — Shows ALL parts properly in a unified view */}
      <div className="space-y-3 pt-1">
        <div className="flex items-center justify-between">
          <h5 className="text-xs font-black uppercase tracking-wider text-gray-500 dark:text-gray-400 flex items-center gap-1.5">
            <span>📋</span> All Process Components ({parts.length} Parts):
          </h5>
          <span className="text-[11px] text-gray-400">Click any part to inspect</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {parts.map((p, idx) => {
            const isSelected = p.id === activePartId
            return (
              <div
                key={p.id}
                onClick={() => setActivePartId(p.id)}
                className={`p-3.5 rounded-2xl border transition-all cursor-pointer space-y-1.5 ${
                  isSelected
                    ? 'bg-indigo-50/90 dark:bg-indigo-950/50 border-indigo-300 dark:border-indigo-700 ring-2 ring-indigo-400/40 shadow-xs'
                    : 'bg-gray-50/70 dark:bg-gray-900 border-gray-200 dark:border-gray-800 hover:border-indigo-300 dark:hover:border-indigo-800'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded-md ${
                    isSelected
                      ? 'bg-indigo-600 text-white'
                      : 'bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300'
                  }`}>
                    Part {idx + 1}
                  </span>
                  {isSelected && (
                    <span className="text-[10px] font-bold text-indigo-600 dark:text-indigo-400">
                      Active Focus
                    </span>
                  )}
                </div>

                <h6 className="font-extrabold text-xs text-gray-900 dark:text-gray-100">
                  {p.name}
                </h6>

                <div className="text-[11px] font-semibold text-indigo-600 dark:text-indigo-400">
                  {p.role}
                </div>

                <p className="text-[11px] text-gray-600 dark:text-gray-400 leading-relaxed pt-1 border-t dark:border-gray-800">
                  {p.details || 'Interconnected component supporting the overall process workflow.'}
                </p>
              </div>
            )
          })}
        </div>
      </div>

      {/* Optional Prediction Check */}
      {prediction && (
        <div className="bg-indigo-50/70 dark:bg-indigo-950/40 border border-indigo-200 dark:border-indigo-800 rounded-2xl p-3.5 space-y-2">
          <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-900 dark:text-indigo-300">
            <span>🎯</span>
            <span>Predict: {prediction.question}</span>
          </div>
          <div className="space-y-1.5">
            {prediction.options?.map((opt, optIdx) => (
              <button
                key={optIdx}
                onClick={() => {
                  setSelectedPrediction(optIdx)
                  setShowPredictionFeedback(true)
                }}
                className={`w-full text-left p-2 rounded-xl text-xs border transition-all ${
                  selectedPrediction === optIdx
                    ? optIdx === prediction.correct_index
                      ? 'bg-emerald-50 border-emerald-500 text-emerald-800 font-bold dark:bg-emerald-950/50 dark:text-emerald-200'
                      : 'bg-red-50 border-red-500 text-red-800 font-bold dark:bg-red-950/50 dark:text-red-200'
                    : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 hover:border-indigo-400'
                }`}
              >
                {opt}
              </button>
            ))}
          </div>
          {showPredictionFeedback && (
            <p className="text-[11px] text-gray-600 dark:text-gray-400 pt-1 font-medium">
              💡 {prediction.explanation}
            </p>
          )}
        </div>
      )}
    </div>
  )
}
