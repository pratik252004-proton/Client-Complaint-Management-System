export default function SectionHeader({ number, title }) {
  return (
    <div className="mb-4 flex items-center gap-2 border-b border-surface-border pb-2">
      <span className="text-xs font-semibold text-slate-400">{number}.</span>
      <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</h3>
    </div>
  )
}
