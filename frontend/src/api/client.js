// Phase 4: real backend wiring. Falls back to mock extraction (see
// utils/mockExtraction.js) automatically if VITE_API_BASE isn't reachable,
// so the UI keeps working in demos without a running backend.

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export async function extractFromFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/api/ai/extract`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Extraction failed (${res.status})`)
  return res.json() // { source, extracted }
}

export async function extractFromText(text) {
  const formData = new FormData()
  formData.append('text', text)
  const res = await fetch(`${API_BASE}/api/ai/extract`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Extraction failed (${res.status})`)
  return res.json()
}

export async function sendChatMessage(message, complaintId) {
  const formData = new FormData()
  formData.append('message', message)
  if (complaintId) formData.append('complaint_id', complaintId)
  const res = await fetch(`${API_BASE}/api/ai/chat`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Chat failed (${res.status})`)
  return res.json() // { reply }
}

export async function saveComplaint(payload) {
  const res = await fetch(`${API_BASE}/api/complaints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!res.ok) throw new Error(`Save failed (${res.status})`)
  return res.json()
}
