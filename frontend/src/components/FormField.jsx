import { Sparkles } from 'lucide-react'

function AiBadge() {
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-brand-50 px-2 py-0.5 text-[10px] font-medium text-brand-700">
      <Sparkles size={10} />
      AI
    </span>
  )
}

export function TextField({
  label,
  value,
  onChange,
  placeholder = 'Awaiting AI extraction...',
  isAiPopulated,
  suffix,
  type = 'text'
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-2">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        {isAiPopulated && <AiBadge />}
      </div>
      <div className="relative">
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full rounded-lg border px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 ${
            isAiPopulated ? 'border-brand-200 bg-brand-50/40' : 'border-surface-border bg-white'
          }`}
        />
        {suffix && (
          <span className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400">
            {suffix}
          </span>
        )}
      </div>
    </div>
  )
}

export function SelectField({ label, value, onChange, options, isAiPopulated }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-2">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        {isAiPopulated && <AiBadge />}
      </div>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 ${
          value ? 'text-slate-900' : 'text-slate-400'
        } ${isAiPopulated ? 'border-brand-200 bg-brand-50/40' : 'border-surface-border bg-white'}`}
      >
        <option value="" disabled hidden>
          Awaiting AI extraction...
        </option>
        {options.map((opt) => (
          <option key={opt} value={opt} className="text-slate-900">
            {opt}
          </option>
        ))}
      </select>
    </div>
  )
}

export function TextAreaField({ label, value, onChange, isAiPopulated, rows = 4 }) {
  return (
    <div>
      <div className="mb-1.5 flex items-center gap-2">
        <label className="text-sm font-medium text-slate-700">{label}</label>
        {isAiPopulated && <AiBadge />}
      </div>
      <textarea
        rows={rows}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Awaiting AI extraction..."
        className={`w-full resize-none rounded-lg border px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/40 focus:border-brand-500 ${
          isAiPopulated ? 'border-brand-200 bg-brand-50/40' : 'border-surface-border bg-white'
        }`}
      />
    </div>
  )
}
