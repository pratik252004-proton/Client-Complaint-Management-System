import ComplaintForm from './components/ComplaintForm'
import AIAssistantPanel from './components/AIAssistantPanel'

export default function App() {
  return (
    <div className="min-h-screen bg-surface-bg px-4 py-6 md:px-8">
      <div className="mx-auto grid h-[calc(100vh-3rem)] min-h-0 max-w-[1400px] grid-cols-1 gap-6 lg:grid-cols-2">
        <ComplaintForm />
        <AIAssistantPanel />
      </div>
    </div>
  )
}