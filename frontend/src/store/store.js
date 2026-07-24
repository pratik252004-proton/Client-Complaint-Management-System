import { configureStore } from '@reduxjs/toolkit'
import complaintReducer from './complaintSlice'
import aiAssistantReducer from './aiAssistantSlice'

export const store = configureStore({
  reducer: {
    complaint: complaintReducer,
    aiAssistant: aiAssistantReducer
  }
})
