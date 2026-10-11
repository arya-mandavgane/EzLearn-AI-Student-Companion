import React, { useState } from 'react'

export function ResourceModal({ isOpen, onClose, onAddResource }) {
  const [activeTab, setActiveTab] = useState('text') // 'text' | 'image' | 'audio' | 'file'
  const [textInput, setTextInput] = useState('')
  const [titleInput, setTitleInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [audioRecording, setAudioRecording] = useState(false)
  const [mediaRecorder, setMediaRecorder] = useState(null)
  const [recordedBlob, setRecordedBlob] = useState(null)

  if (!isOpen) return null

  async function handleAddText(e) {
    e.preventDefault()
    if (!textInput.trim()) return
    setLoading(true)
    setError('')
    try {
      await onAddResource({
        type: 'text',
        title: titleInput || 'Pasted Notes',
        text: textInput.trim(),
      })
      setTextInput('')
      setTitleInput('')
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to add text resource.')
    } finally {
      setLoading(false)
    }
  }

  async function handleFileUpload(file, type = 'file') {
    if (!file) return
    setLoading(true)
    setError('')
    try {
      const form = new FormData()
      form.append('resource_type', type)
      form.append('title', file.name)
      form.append('file', file)
      await onAddResource({ type: 'upload', formData: form })
      onClose()
    } catch (err) {
      setError(err.message || 'Failed to upload resource.')
    } finally {
      setLoading(false)
    }
  }

  // Audio Recording helpers
  async function startAudioRecording() {
    setError('')
    setRecordedBlob(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      const rec = new MediaRecorder(stream)
      const chunks = []
      rec.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data) }
      rec.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' })
        setRecordedBlob(blob)
        stream.getTracks().forEach(t => t.stop())
      }
      rec.start()
      setMediaRecorder(rec)
      setAudioRecording(true)
    } catch (err) {
      setError(`Microphone access failed: ${err.message}`)
    }
  }

  function stopAudioRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
      mediaRecorder.stop()
    }
    setAudioRecording(false)
  }

  async function handleSendAudio() {
    if (!recordedBlob) return
    const file = new File([recordedBlob], 'voice_recording.webm', { type: 'audio/webm' })
    await handleFileUpload(file, 'audio')
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white dark:bg-gray-800 rounded-3xl shadow-2xl max-w-lg w-full p-6 space-y-5 border border-gray-100 dark:border-gray-700">
        
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b dark:border-gray-700">
          <div>
            <h3 className="text-lg font-black text-gray-900 dark:text-gray-100 flex items-center gap-2">
              <span>➕</span> Add Study Resource
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Attach study notes, images, or audio before chatting
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 text-lg font-bold"
          >
            ✕
          </button>
        </div>

        {/* Resource Type Selector */}
        <div className="grid grid-cols-4 gap-2 bg-gray-100 dark:bg-gray-900 p-1.5 rounded-2xl text-xs font-bold">
          {[
            { id: 'text',  label: '📝 Text' },
            { id: 'image', label: '🖼️ Image' },
            { id: 'audio', label: '🎙️ Audio' },
            { id: 'file',  label: '📄 File' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setActiveTab(tab.id); setError('') }}
              className={`py-2 rounded-xl transition-all ${
                activeTab === tab.id
                  ? 'bg-white dark:bg-gray-800 text-indigo-600 dark:text-indigo-400 shadow-sm'
                  : 'text-gray-600 dark:text-gray-400 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {error && <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-700 font-medium">⚠️ {error}</div>}

        {/* Tab 1: Text */}
        {activeTab === 'text' && (
          <form onSubmit={handleAddText} className="space-y-3">
            <input
              type="text"
              value={titleInput}
              onChange={e => setTitleInput(e.target.value)}
              placeholder="Title / Subject (e.g. Biology Cell Notes)"
              className="w-full border dark:border-gray-700 rounded-xl p-2.5 text-xs bg-gray-50 dark:bg-gray-900 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
            <textarea
              rows={6}
              value={textInput}
              onChange={e => setTextInput(e.target.value)}
              placeholder="Paste or type complete study notes, syllabus material, textbook paragraphs..."
              className="w-full border dark:border-gray-700 rounded-xl p-3 text-xs bg-gray-50 dark:bg-gray-900 dark:text-gray-200 focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none leading-relaxed"
            />
            <button
              type="submit"
              disabled={loading || !textInput.trim()}
              className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs shadow transition-all disabled:opacity-50"
            >
              {loading ? 'Adding…' : 'Add Text Resource'}
            </button>
          </form>
        )}

        {/* Tab 2: Image (Camera or Gallery) */}
        {activeTab === 'image' && (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <label className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-indigo-200 hover:border-indigo-400 dark:border-gray-700 rounded-2xl cursor-pointer bg-indigo-50/30 dark:bg-gray-900 hover:bg-indigo-50 transition-all text-center">
                <span className="text-3xl mb-1">📸</span>
                <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400">Use Camera</span>
                <span className="text-[10px] text-gray-400">Snap textbook/diagram</span>
                <input
                  type="file"
                  accept="image/*"
                  capture="environment"
                  className="hidden"
                  onChange={e => handleFileUpload(e.target.files?.[0], 'image')}
                />
              </label>

              <label className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-indigo-200 hover:border-indigo-400 dark:border-gray-700 rounded-2xl cursor-pointer bg-indigo-50/30 dark:bg-gray-900 hover:bg-indigo-50 transition-all text-center">
                <span className="text-3xl mb-1">🖼️</span>
                <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400">From Gallery</span>
                <span className="text-[10px] text-gray-400">Upload screenshot/photo</span>
                <input
                  type="file"
                  accept="image/*"
                  className="hidden"
                  onChange={e => handleFileUpload(e.target.files?.[0], 'image')}
                />
              </label>
            </div>
            {loading && <p className="text-center text-xs text-indigo-600 animate-pulse">Running OCR on image…</p>}
          </div>
        )}

        {/* Tab 3: Audio (Record or Pre-recorded) */}
        {activeTab === 'audio' && (
          <div className="space-y-4">
            <div className="flex flex-col items-center justify-center p-5 bg-gray-50 dark:bg-gray-900 rounded-2xl border dark:border-gray-700 space-y-3">
              <div className="text-3xl">🎙️</div>
              {!audioRecording ? (
                <button
                  type="button"
                  onClick={startAudioRecording}
                  className="px-5 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-xl text-xs font-bold shadow transition-all flex items-center gap-1.5"
                >
                  <span>🔴</span> Start Recording
                </button>
              ) : (
                <button
                  type="button"
                  onClick={stopAudioRecording}
                  className="px-5 py-2 bg-gray-800 hover:bg-gray-900 text-white rounded-xl text-xs font-bold animate-pulse"
                >
                  <span>⏹️</span> Stop Recording
                </button>
              )}

              {recordedBlob && !audioRecording && (
                <div className="w-full space-y-2 pt-2 border-t dark:border-gray-700">
                  <audio src={URL.createObjectURL(recordedBlob)} controls className="w-full h-8" />
                  <button
                    onClick={handleSendAudio}
                    disabled={loading}
                    className="w-full py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-xs font-bold"
                  >
                    {loading ? 'Transcribing…' : 'Attach Voice Recording'}
                  </button>
                </div>
              )}
            </div>

            <div className="text-center">
              <span className="text-[11px] text-gray-400 uppercase font-semibold">Or upload pre-recorded audio</span>
              <label className="block mt-1 cursor-pointer">
                <span className="inline-block px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-xl text-xs font-bold">
                  📁 Choose Audio File (.mp3, .wav, .m4a)
                </span>
                <input
                  type="file"
                  accept="audio/*"
                  className="hidden"
                  onChange={e => handleFileUpload(e.target.files?.[0], 'audio')}
                />
              </label>
            </div>
          </div>
        )}

        {/* Tab 4: File (PDF) */}
        {activeTab === 'file' && (
          <div className="space-y-3">
            <label className="flex flex-col items-center justify-center p-8 border-2 border-dashed border-indigo-200 hover:border-indigo-400 dark:border-gray-700 rounded-2xl cursor-pointer bg-indigo-50/20 dark:bg-gray-900 hover:bg-indigo-50 transition-all text-center">
              <span className="text-4xl mb-2">📑</span>
              <span className="text-xs font-bold text-indigo-700 dark:text-indigo-400">Choose PDF Document</span>
              <span className="text-[11px] text-gray-400 mt-1">Extracts pages, text, and headings for RAG</span>
              <input
                type="file"
                accept=".pdf,.txt,.md"
                className="hidden"
                onChange={e => handleFileUpload(e.target.files?.[0], 'file')}
              />
            </label>
            {loading && <p className="text-center text-xs text-indigo-600 animate-pulse">Extracting document pages…</p>}
          </div>
        )}

      </div>
    </div>
  )
}
