import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  uploadedFileName: null,
  pastedText: '',
  showPasteBox: false,
  isExtracting: false,
  extractionProgress: 0,
  extractionStage: '', // e.g. "Analyzing document content and extracting key details..."
  chatMessages: [
    {
      id: 'welcome',
      role: 'assistant',
      text: 'Upload a complaint document or paste text above. I will automatically extract the details and populate the form for you.'
    }
  ],
  draftMessage: ''
}

const aiAssistantSlice = createSlice({
  name: 'aiAssistant',
  initialState,
  reducers: {
    setUploadedFileName: (state, action) => {
      state.uploadedFileName = action.payload
    },
    togglePasteBox: (state, action) => {
      state.showPasteBox = action.payload
    },
    setPastedText: (state, action) => {
      state.pastedText = action.payload
    },
    startExtraction: (state) => {
      state.isExtracting = true
      state.extractionProgress = 0
      state.extractionStage = 'Analyzing document content and extracting key details...'
    },
    setExtractionProgress: (state, action) => {
      state.extractionProgress = action.payload
    },
    finishExtraction: (state) => {
      state.isExtracting = false
      state.extractionProgress = 100
      state.extractionStage = 'Extraction complete.'
    },
    addChatMessage: (state, action) => {
      state.chatMessages.push(action.payload)
    },
    setDraftMessage: (state, action) => {
      state.draftMessage = action.payload
    },
    resetAssistant: (state) => {
      state.uploadedFileName = null
      state.pastedText = ''
      state.showPasteBox = false
      state.isExtracting = false
      state.extractionProgress = 0
      state.extractionStage = ''
      state.draftMessage = ''
    }
  }
})

export const {
  setUploadedFileName,
  togglePasteBox,
  setPastedText,
  startExtraction,
  setExtractionProgress,
  finishExtraction,
  addChatMessage,
  setDraftMessage,
  resetAssistant
} = aiAssistantSlice.actions

export default aiAssistantSlice.reducer
