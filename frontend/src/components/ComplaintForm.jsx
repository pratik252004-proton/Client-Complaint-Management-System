import { useDispatch, useSelector } from 'react-redux'
import { RotateCcw, Save } from 'lucide-react'
import SectionHeader from './SectionHeader'
import { TextField, SelectField, TextAreaField } from './FormField'
import { updateField, resetForm, setSaving, setStatus, setSaveError, setLastSavedId } from '../store/complaintSlice'
import { resetAssistant } from '../store/aiAssistantSlice'
import { saveComplaint } from '../api/client'

const STATUS_STYLES = {
  'Pending Triage': 'bg-amber-50 text-amber-700 border-amber-200',
  'Under Review': 'bg-brand-50 text-brand-700 border-brand-200',
  Investigation: 'bg-purple-50 text-purple-700 border-purple-200',
  'CAPA Initiated': 'bg-orange-50 text-orange-700 border-orange-200',
  Closed: 'bg-emerald-50 text-emerald-700 border-emerald-200'
}

export default function ComplaintForm() {
  const dispatch = useDispatch()
  const { fields, aiPopulatedFields, status, isSaving, saveError } = useSelector((s) => s.complaint)

  const isAi = (field) => aiPopulatedFields.includes(field)
  const set = (field) => (value) => dispatch(updateField({ field, value }))

  const handleSave = async () => {
    dispatch(setSaving(true))
    dispatch(setSaveError(null))
    try {
      const saved = await saveComplaint({ ...fields, ai_populated_fields: aiPopulatedFields })
      dispatch(setLastSavedId(saved.id))
      dispatch(setStatus('Under Review'))
    } catch (err) {
      dispatch(setSaveError(err.message || 'Failed to save complaint.'))
    } finally {
      dispatch(setSaving(false))
    }
  }

  const handleReset = () => {
    dispatch(resetForm())
    dispatch(resetAssistant())
  }

  return (
    <div className="flex h-full min-h-0 flex-col rounded-xl border border-surface-border bg-surface-card shadow-card">
      {/* Header */}
      <div className="flex items-start justify-between border-b border-surface-border px-6 py-5">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Customer Complaint Log</h1>
          <p className="mt-0.5 text-sm text-slate-500">API &amp; FDF Quality Assurance Module</p>
        </div>
        <span
          className={`rounded-full border px-3 py-1 text-xs font-semibold ${
            STATUS_STYLES[status] || 'bg-slate-50 text-slate-600 border-slate-200'
          }`}
        >
          {status}
        </span>
      </div>

      {/* Scrollable form body */}
      <div className="thin-scroll flex-1 min-h-0 space-y-8 overflow-y-auto px-6 py-6">
        <section>
          <SectionHeader number={1} title="Origin & Customer Details" />
          <div className="grid grid-cols-2 gap-4">
            <TextField
              label="Complaint Source"
              value={fields.complaintSource}
              onChange={set('complaintSource')}
              isAiPopulated={isAi('complaintSource')}
            />
            <TextField
              label="Customer Name"
              value={fields.customerName}
              onChange={set('customerName')}
              isAiPopulated={isAi('customerName')}
            />
          </div>
        </section>

        <section>
          <SectionHeader number={2} title="Product & Batch Identification" />
          <div className="grid grid-cols-2 gap-4">
            <TextField
              label="Product Name"
              value={fields.productName}
              onChange={set('productName')}
              isAiPopulated={isAi('productName')}
            />
            <TextField
              label="Product Strength/Grade"
              value={fields.productStrength}
              onChange={set('productStrength')}
              isAiPopulated={isAi('productStrength')}
            />
            <TextField
              label="Batch/Lot Number"
              value={fields.batchLotNumber}
              onChange={set('batchLotNumber')}
              isAiPopulated={isAi('batchLotNumber')}
            />
            <TextField
              label="Manufacturing Date"
              type="date"
              value={fields.manufacturingDate}
              onChange={set('manufacturingDate')}
              isAiPopulated={isAi('manufacturingDate')}
            />
            <TextField
              label="Expiry Date"
              type="date"
              value={fields.expiryDate}
              onChange={set('expiryDate')}
              isAiPopulated={isAi('expiryDate')}
            />
            <TextField
              label="Quantity Affected"
              value={fields.quantityAffected}
              onChange={set('quantityAffected')}
              isAiPopulated={isAi('quantityAffected')}
              suffix="kg"
            />
          </div>
        </section>

        <section>
          <SectionHeader number={3} title="Complaint Details" />
          <div className="grid grid-cols-2 gap-4">
            <TextField
              label="Complaint Type"
              value={fields.complaintType}
              onChange={set('complaintType')}
              isAiPopulated={isAi('complaintType')}
            />
            <TextField
              label="Complaint Date"
              type="date"
              value={fields.complaintDate}
              onChange={set('complaintDate')}
              isAiPopulated={isAi('complaintDate')}
            />
          </div>
          <div className="mt-4">
            <TextAreaField
              label="Detailed Complaint Description"
              value={fields.detailedDescription}
              onChange={set('detailedDescription')}
              isAiPopulated={isAi('detailedDescription')}
            />
          </div>
        </section>

        <section>
          <SectionHeader number={4} title="Initial Assessment & Priority" />
          <div className="grid grid-cols-2 gap-4">
            <SelectField
              label="Initial Severity"
              value={fields.initialSeverity}
              onChange={set('initialSeverity')}
              options={['Critical', 'Major', 'Minor']}
              isAiPopulated={isAi('initialSeverity')}
            />
            <SelectField
              label="Priority"
              value={fields.priority}
              onChange={set('priority')}
              options={['High', 'Medium', 'Low']}
              isAiPopulated={isAi('priority')}
            />
          </div>
        </section>
      </div>

      {/* Save error banner */}
      {saveError && (
        <div className="mx-6 mb-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-xs text-red-700">
          {saveError}
        </div>
      )}

      {/* Footer actions */}
      <div className="flex items-center justify-between border-t border-surface-border px-6 py-4">
        <button
          onClick={handleReset}
          className="inline-flex items-center gap-2 rounded-lg border border-surface-border bg-white px-4 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-50"
        >
          <RotateCcw size={16} />
          Reset Form
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-brand-700 disabled:opacity-60"
        >
          <Save size={16} />
          {isSaving ? 'Saving...' : 'Save Complaint'}
        </button>
      </div>
    </div>
  )
}