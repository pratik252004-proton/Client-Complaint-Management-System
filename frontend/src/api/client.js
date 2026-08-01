// Falls back to mock extraction (see
// utils/mockExtraction.js) automatically if VITE_API_BASE isn't reachable,
// so the UI keeps working in demos without a running backend.

const API_BASE = import.meta.env.VITE_API_BASE || 'https://client-complaint-management-system.onrender.com'

// The backend (Pydantic/SQLAlchemy) uses snake_case field names
// (customer_name, product_name, ...). Redux/the form use camelCase
// (customerName, productName, ...). Without converting at this boundary,
// keys silently don't match on either side and get dropped with no error
// — which is exactly what was happening. Convert here, once, in both
// directions, so nothing above this file needs to know about naming.
function snakeToCamel(obj) {
  if (!obj || typeof obj !== 'object') return obj
  const out = {}
  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase())
    out[camelKey] = value
  }
  return out
}

function camelToSnake(obj) {
  if (!obj || typeof obj !== 'object') return obj
  const out = {}
  for (const [key, value] of Object.entries(obj)) {
    const snakeKey = key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`)
    out[snakeKey] = value
  }
  return out
}

export async function extractFromFile(file) {
  const formData = new FormData()
  formData.append('file', file)
  const res = await fetch(`${API_BASE}/api/ai/extract`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Extraction failed (${res.status})`)
  const data = await res.json() // { source, extracted } — extracted is snake_case
  return { ...data, extracted: snakeToCamel(data.extracted) }
}

export async function extractFromText(text) {
  const formData = new FormData()
  formData.append('text', text)
  const res = await fetch(`${API_BASE}/api/ai/extract`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Extraction failed (${res.status})`)
  const data = await res.json()
  return { ...data, extracted: snakeToCamel(data.extracted) }
}

export async function sendChatMessage(message, complaintId) {
  const formData = new FormData()
  formData.append('message', message)
  if (complaintId) formData.append('complaint_id', complaintId)
  const res = await fetch(`${API_BASE}/api/ai/chat`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Chat failed (${res.status})`)
  const data = await res.json() // { reply, form_updates } — form_updates is snake_case
  return { ...data, form_updates: snakeToCamel(data.form_updates) }
}

// Addon 1: AI risk assessment. Pass complaintId if the record is already
// saved, otherwise pass the current in-progress form fields so it works
// pre-save too.
export async function generateRiskAssessment({ complaintId, fields }) {
  const formData = new FormData()
  if (complaintId) {
    formData.append('complaint_id', complaintId)
  } else {
    // fields comes from Redux (camelCase) — convert to snake_case so the
    // backend's risk-assessment prompt sees the field names it expects.
    formData.append('fields_json', JSON.stringify(camelToSnake(fields || {})))
  }
  const res = await fetch(`${API_BASE}/api/ai/risk-assessment`, { method: 'POST', body: formData })
  if (!res.ok) throw new Error(`Risk assessment failed (${res.status})`)
  return res.json() // { assessment: { risk_level, summary, key_concerns, recommended_actions, regulatory_flag } }
}

export async function saveComplaint(payload) {
  // payload comes from Redux (camelCase) — convert to snake_case to match
  // the backend's ComplaintCreate schema, or every field silently saves
  // as null (Pydantic ignores unrecognized extra keys instead of erroring).
  const snakePayload = camelToSnake(payload)
  const res = await fetch(`${API_BASE}/api/complaints`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(snakePayload)
  })
  if (!res.ok) throw new Error(`Save failed (${res.status})`)
  return res.json()
}