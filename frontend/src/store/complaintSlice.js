import { createSlice } from '@reduxjs/toolkit'

const initialFormState = {
  complaintSource: '',
  customerName: '',
  productName: '',
  productStrength: '',
  batchLotNumber: '',
  manufacturingDate: '',
  expiryDate: '',
  quantityAffected: '',
  complaintType: '',
  complaintDate: '',
  detailedDescription: '',
  initialSeverity: '',
  priority: ''
}

const initialState = {
  status: 'Pending Triage', // Pending Triage | Under Review | Closed
  fields: { ...initialFormState },
  // tracks which fields were populated by the AI so the UI can badge them
  aiPopulatedFields: [],
  isSaving: false,
  saveError: null,
  lastSavedId: null
}

const complaintSlice = createSlice({
  name: 'complaint',
  initialState,
  reducers: {
    updateField: (state, action) => {
      const { field, value } = action.payload
      state.fields[field] = value
      // manual edits after AI extraction demote the field from "AI populated"
      state.aiPopulatedFields = state.aiPopulatedFields.filter((f) => f !== field)
    },
    applyExtractedData: (state, action) => {
      // action.payload: partial fields object returned by the AI extraction step
      const extracted = action.payload
      Object.keys(extracted).forEach((key) => {
        if (key in state.fields && extracted[key]) {
          state.fields[key] = extracted[key]
          if (!state.aiPopulatedFields.includes(key)) {
            state.aiPopulatedFields.push(key)
          }
        }
      })
    },
    setStatus: (state, action) => {
      state.status = action.payload
    },
    setSaving: (state, action) => {
      state.isSaving = action.payload
    },
    setSaveError: (state, action) => {
      state.saveError = action.payload
    },
    setLastSavedId: (state, action) => {
      state.lastSavedId = action.payload
    },
    resetForm: (state) => {
      state.fields = { ...initialFormState }
      state.aiPopulatedFields = []
      state.status = 'Pending Triage'
      state.saveError = null
    }
  }
})

export const {
  updateField,
  applyExtractedData,
  setStatus,
  setSaving,
  setSaveError,
  setLastSavedId,
  resetForm
} = complaintSlice.actions

export default complaintSlice.reducer
