import { useEffect, useRef, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { UploadCloud, FileText, Info, Sparkles, Send, Bot, User } from 'lucide-react'
import {
  setUploadedFileName,
  togglePasteBox,
  setPastedText,
  startExtraction,
  setExtractionProgress,
  finishExtraction,
  addChatMessage,
  setDraftMessage
} from '../store/aiAssistantSlice'
import { applyExtractedData } from '../store/complaintSlice'
import { runMockExtraction } from '../utils/mockExtraction'
import { extractFromFile, extractFromText, sendChatMessage, generateRiskAssessment } from '../api/client'

export default function AIAssistantPanel() {
  const dispatch = useDispatch()
  const fileInputRef = useRef(null)
  const chatEndRef = useRef(null)
  const [isDragging, setIsDragging] = useState(false)
  const {
    uploadedFileName,
    showPasteBox,
    pastedText,
    isExtracting,
    extractionProgress,
    extractionStage,
    chatMessages,
    draftMessage
  } = useSelector((s) => s.aiAssistant)

  // Needed so chat/risk-assessment calls can reference the current
  // complaint — either the saved DB id, or the in-progress form fields
  // if it hasn't been saved yet.
  const lastSavedId = useSelector((s) => s.complaint.lastSavedId)
  const formFields = useSelector((s) => s.complaint.fields)

  const [isAssessingRisk, setIsAssessingRisk] = useState(false)
  const [riskAssessment, setRiskAssessment] = useState(null)

  // Auto-scroll the chat area (not the whole page) to the newest message
  // whenever the conversation grows.
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
  }, [chatMessages])

  const runExtractionFlow = async (sourceLabel, { file, text } = {}) => {
    dispatch(startExtraction())
    // Fake a smooth progress bar while the real request is in flight; the
    // backend call below runs concurrently and wins the race for accuracy.
    const steps = [10, 35, 60, 82]
    for (const pct of steps) {
      // eslint-disable-next-line no-await-in-loop
      await new Promise((r) => setTimeout(r, 300))
      dispatch(setExtractionProgress(pct))
    }

    let extracted
    try {
      const res = file ? await extractFromFile(file) : await extractFromText(text)
      extracted = res.extracted
    } catch (err) {
      // Backend not running / Groq not configured yet — fall back to the
      // Phase 1 mock so the UI/demo still works end to end.
      extracted = await runMockExtraction()
    }

    dispatch(setExtractionProgress(100))
    dispatch(applyExtractedData(extracted))
    dispatch(finishExtraction())
    dispatch(
      addChatMessage({
        id: `msg-${Date.now()}`,
        role: 'assistant',
        text: `I've extracted the details from ${sourceLabel} and populated the form. Please review Section 1-4, especially Initial Severity and Priority, before saving.`
      })
    )
  }

  const handleFileSelected = (file) => {
    if (!file) return
    dispatch(setUploadedFileName(file.name))
    runExtractionFlow(`"${file.name}"`, { file })
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files?.[0]
    handleFileSelected(file)
  }

  const handlePasteSubmit = () => {
    if (!pastedText.trim()) return
    runExtractionFlow('the pasted text', { text: pastedText })
    dispatch(togglePasteBox(false))
  }

  const handleSendChat = async () => {
    if (!draftMessage.trim()) return
    dispatch(addChatMessage({ id: `u-${Date.now()}`, role: 'user', text: draftMessage }))
    const question = draftMessage
    dispatch(setDraftMessage(''))

    try {
      const { reply, form_updates: formUpdates } = await sendChatMessage(question, lastSavedId)
      dispatch(addChatMessage({ id: `a-${Date.now()}`, role: 'assistant', text: reply }))

      // Addon 2 & 3: if the message asked to add/edit fields, apply them
      // to the complaint form now, same as a document-extraction result.
      if (formUpdates && Object.keys(formUpdates).length > 0) {
        dispatch(applyExtractedData(formUpdates))
      }
    } catch (err) {
      dispatch(
        addChatMessage({
          id: `a-${Date.now()}`,
          role: 'assistant',
          text: `I can't reach the AI backend right now, so here's a placeholder: once connected, I'll answer questions like "${question}" using the complaint context and QMS guidance.`
        })
      )
    }
  }

  // Addon 1: AI risk assessment
  const handleGenerateRiskAssessment = async () => {
    setIsAssessingRisk(true)
    setRiskAssessment(null)
    try {
      const { assessment } = await generateRiskAssessment(
        lastSavedId ? { complaintId: lastSavedId } : { fields: formFields }
      )
      setRiskAssessment(assessment)
    } catch (err) {
      dispatch(
        addChatMessage({
          id: `risk-err-${Date.now()}`,
          role: 'assistant',
          text: "I couldn't generate a risk assessment right now — check that the backend is reachable and try again."
        })
      )
    } finally {
      setIsAssessingRisk(false)
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-surface-border bg-surface-card shadow-card">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-surface-border px-6 py-5">
        <div className="flex items-center gap-2">
          <Sparkles className="text-brand-600" size={20} />
          <h2 className="text-base font-bold text-slate-900">AI Complaint Intake Assistant</h2>
        </div>
        <span className="rounded-full bg-brand-50 px-2.5 py-0.5 text-[10px] font-bold tracking-wide text-brand-700">
          BETA
        </span>
      </div>

      <div className="thin-scroll flex-1 min-h-0 space-y-5 overflow-y-auto px-6 py-5">
        {/* Drag & drop zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-xl border-2 border-dashed px-6 py-8 text-center transition ${
            isDragging ? 'border-brand-500 bg-brand-50/60' : 'border-slate-300 bg-slate-50/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.eml"
            className="hidden"
            onChange={(e) => handleFileSelected(e.target.files?.[0])}
          />
          <UploadCloud className="mx-auto mb-2 text-slate-400" size={26} />
          <p className="text-sm text-slate-600">
            {uploadedFileName ? (
              <span className="font-medium text-slate-800">{uploadedFileName}</span>
            ) : (
              <>
                Drag &amp; drop complaint document here
                <br />
                or{' '}
                <span className="font-semibold text-brand-600 underline underline-offset-2">
                  click to browse
                </span>
              </>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs font-medium text-slate-400">
          <div className="h-px flex-1 bg-surface-border" />
          OR
          <div className="h-px flex-1 bg-surface-border" />
        </div>

        {/* Paste text toggle */}
        <button
          onClick={() => dispatch(togglePasteBox(!showPasteBox))}
          className="flex w-full items-center justify-center gap-2 rounded-lg border border-surface-border bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"
        >
          <FileText size={16} />
          Paste Complaint Text / Email
        </button>

        {showPasteBox && (
          <div className="space-y-2">
            <textarea
              rows={5}
              value={pastedText}
              onChange={(e) => dispatch(setPastedText(e.target.value))}
              placeholder="Paste the complaint email or document text here..."
              className="w-full resize-none rounded-lg border border-surface-border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
            />
            <button
              onClick={handlePasteSubmit}
              className="w-full rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700"
            >
              Extract Details
            </button>
          </div>
        )}

        {/* Supported formats info */}
        <div className="flex items-start gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-800">
          <Info size={14} className="mt-0.5 shrink-0" />
          <div>
            <p className="font-medium">Supported formats: PDF, DOCX, TXT, EML</p>
            <p>Max file size: 10MB</p>
          </div>
        </div>

        {/* Extraction progress */}
        {isExtracting || extractionProgress > 0 ? (
          <div>
            <div className="mb-1.5 flex items-center justify-between text-xs font-semibold uppercase tracking-wide text-slate-500">
              <span>Extraction Progress</span>
              <span>{extractionProgress}%</span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-brand-500 transition-all duration-300"
                style={{ width: `${extractionProgress}%` }}
              />
            </div>
            <p className="mt-2 text-xs text-slate-500">
              {isExtracting
                ? extractionStage
                : 'Extraction complete. Review the populated fields on the left.'}
            </p>
            {isExtracting && (
              <p className="mt-0.5 text-xs text-slate-400">
                Please wait, this may take a few moments.
              </p>
            )}
          </div>
        ) : null}

        {/* Addon 1: AI Risk Assessment */}
        <div className="rounded-lg border border-surface-border bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Risk Assessment
            </p>
            <button
              onClick={handleGenerateRiskAssessment}
              disabled={isAssessingRisk}
              className="rounded-md bg-brand-600 px-3 py-1.5 text-xs font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
            >
              {isAssessingRisk ? 'Assessing...' : 'Generate Risk Assessment'}
            </button>
          </div>

          {riskAssessment && (
            <div className="space-y-2 text-sm">
              <div className="flex items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-[11px] font-bold ${
                    {
                      Critical: 'bg-red-100 text-red-700',
                      High: 'bg-orange-100 text-orange-700',
                      Medium: 'bg-amber-100 text-amber-700',
                      Low: 'bg-emerald-100 text-emerald-700'
                    }[riskAssessment.risk_level] || 'bg-slate-100 text-slate-600'
                  }`}
                >
                  {riskAssessment.risk_level || 'Unknown'} Risk
                </span>
                {riskAssessment.regulatory_flag && (
                  <span className="rounded-full bg-purple-100 px-2 py-0.5 text-[11px] font-bold text-purple-700">
                    Regulatory Review Suggested
                  </span>
                )}
              </div>
              <p className="text-slate-700">{riskAssessment.summary}</p>
              {riskAssessment.key_concerns?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500">Key Concerns</p>
                  <ul className="list-disc pl-4 text-xs text-slate-600">
                    {riskAssessment.key_concerns.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}
              {riskAssessment.recommended_actions?.length > 0 && (
                <div>
                  <p className="text-xs font-semibold text-slate-500">Recommended Actions</p>
                  <ul className="list-disc pl-4 text-xs text-slate-600">
                    {riskAssessment.recommended_actions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Chat */}
        <div>
          <p className="mb-2 text-xs font-semibold uppercase tracking-wide text-slate-500">
            AI Assistant
          </p>
          <div className="space-y-3">
            {chatMessages.map((msg) => (
              <div
                key={msg.id}
                className={`flex items-start gap-2 ${
                  msg.role === 'user' ? 'flex-row-reverse' : ''
                }`}
              >
                <div
                  className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                    msg.role === 'user' ? 'bg-slate-200 text-slate-600' : 'bg-brand-600 text-white'
                  }`}
                >
                  {msg.role === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>
                <div
                  className={`max-w-[85%] rounded-xl px-3.5 py-2.5 text-sm ${
                    msg.role === 'user'
                      ? 'bg-slate-100 text-slate-800'
                      : 'bg-brand-50 text-slate-700'
                  }`}
                >
                  {msg.text}
                </div>
              </div>
            ))}
            {/* Invisible anchor — auto-scroll target for new messages */}
            <div ref={chatEndRef} />
          </div>
        </div>
      </div>

      {/* Chat input */}
      <div className="border-t border-surface-border px-6 py-4">
        <div className="flex items-center gap-2">
          <input
            value={draftMessage}
            onChange={(e) => dispatch(setDraftMessage(e.target.value))}
            onKeyDown={(e) => e.key === 'Enter' && handleSendChat()}
            placeholder="Ask me anything about this complaint..."
            className="flex-1 rounded-lg border border-surface-border px-3 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500"
          />
          <button
            onClick={handleSendChat}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-white transition hover:bg-brand-700"
          >
            <Send size={16} />
          </button>
        </div>
        <p className="mt-2 text-center text-[11px] text-slate-400">
          AI responses may contain errors. Please verify information.
        </p>
      </div>
    </div>
  )
}