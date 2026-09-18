import { AlertTriangle, Loader2, ShieldAlert } from 'lucide-react'
import type { ReactNode } from 'react'
import clsx from 'clsx'

export function DisclaimerBanner() {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
      <ShieldAlert className="mt-0.5 h-5 w-5 shrink-0" />
      <p>
        Prototipo académico. Las sugerencias <strong>asisten, no deciden</strong>: la
        clasificación final es siempre responsabilidad del personal de salud. No usar para
        decisiones clínicas reales.
      </p>
    </div>
  )
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={clsx(
        'rounded-2xl border border-slate-800 bg-slate-900/60 p-5 shadow-lg shadow-black/20 backdrop-blur',
        className,
      )}
    >
      {children}
    </div>
  )
}

export function SectionTitle({ eyebrow, title, description }: { eyebrow: string; title: string; description?: string }) {
  return (
    <div className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-widest text-teal-400">{eyebrow}</p>
      <h2 className="mt-1 text-2xl font-bold text-slate-50">{title}</h2>
      {description && <p className="mt-2 max-w-3xl text-sm leading-relaxed text-slate-400">{description}</p>}
    </div>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center gap-3 py-10 text-slate-400">
      <Loader2 className="h-5 w-5 animate-spin text-teal-400" />
      <span className="text-sm">{label ?? 'Cargando...'}</span>
    </div>
  )
}

export function ErrorBox({ message }: { message: string }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300">
      <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" />
      <p>{message}</p>
    </div>
  )
}

export function ScoreBar({ value, max = 1, color = '#2dd4bf' }: { value: number; max?: number; color?: string }) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100))
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-800">
      <div
        className="h-full rounded-full transition-all duration-700 ease-out"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  )
}

export function StatCard({
  label,
  value,
  hint,
  accent = 'teal',
}: {
  label: string
  value: string
  hint?: string
  accent?: 'teal' | 'red' | 'amber' | 'sky'
}) {
  const accentClasses = {
    teal: 'from-teal-500/20 to-transparent text-teal-300',
    red: 'from-red-500/20 to-transparent text-red-300',
    amber: 'from-amber-500/20 to-transparent text-amber-300',
    sky: 'from-sky-500/20 to-transparent text-sky-300',
  }[accent]

  return (
    <div className={clsx('rounded-2xl bg-gradient-to-br p-5', accentClasses, 'border border-slate-800 bg-slate-900/60')}>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-400">{label}</p>
      <p className="mt-2 text-3xl font-bold text-slate-50">{value}</p>
      {hint && <p className="mt-1 text-xs text-slate-500">{hint}</p>}
    </div>
  )
}
