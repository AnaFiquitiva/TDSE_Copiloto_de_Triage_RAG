import clsx from 'clsx'

const LEVEL_STYLES: Record<number, { label: string; classes: string }> = {
  1: { label: 'I · Resucitación', classes: 'bg-red-500/15 text-red-300 ring-red-500/40' },
  2: { label: 'II · Emergencia', classes: 'bg-orange-500/15 text-orange-300 ring-orange-500/40' },
  3: { label: 'III · Urgencia', classes: 'bg-amber-400/15 text-amber-300 ring-amber-400/40' },
  4: { label: 'IV · Urgencia menor', classes: 'bg-sky-500/15 text-sky-300 ring-sky-500/40' },
  5: { label: 'V · No urgencia', classes: 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/40' },
}

export function LevelBadge({ level, compact = false }: { level: number | null; compact?: boolean }) {
  if (level === null) {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-700/50 px-3 py-1 text-xs font-semibold text-slate-300 ring-1 ring-inset ring-slate-600">
        Sin nivel
      </span>
    )
  }
  const style = LEVEL_STYLES[level]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold ring-1 ring-inset',
        style.classes,
      )}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {compact ? `Nivel ${level}` : style.label}
    </span>
  )
}

export function levelColor(level: number | null): string {
  if (level === null) return '#64748b'
  return { 1: '#f87171', 2: '#fb923c', 3: '#fbbf24', 4: '#38bdf8', 5: '#34d399' }[level] ?? '#64748b'
}
