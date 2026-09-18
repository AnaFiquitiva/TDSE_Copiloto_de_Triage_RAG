import { useEffect, useMemo, useState } from 'react'
import { BookOpen, ListChecks, Search } from 'lucide-react'
import clsx from 'clsx'

import { fetchCasos, fetchCorpus } from '../api'
import type { CorpusFormat, CorpusChunk, GoldCase } from '../types'
import { Card, ErrorBox, SectionTitle, Spinner } from '../components/Common'
import { LevelBadge } from '../components/LevelBadge'

type SubTab = 'corpus' | 'casos'

/** Limpia el markdown crudo del fragmento (## encabezado, [CITA: ...], **negritas**)
 * para una vista de lectura más cómoda; el texto original completo sigue
 * disponible vía la API (/api/corpus) para quien lo necesite tal cual. */
function formatChunkText(text: string): string {
  return text
    .replace(/^##\s*\[CITA:[^\]]*\]\s*/m, '')
    .replace(/\*\*/g, '')
    .trim()
}

export function ExplorarView() {
  const [subTab, setSubTab] = useState<SubTab>('casos')

  return (
    <div className="mx-auto max-w-6xl">
      <SectionTitle
        eyebrow="Transparencia del gold standard"
        title="Explorar corpus y casos de prueba"
        description="Navega el corpus normativo reformateado (los 31 fragmentos citables) y las 74 viñetas sintéticas del gold standard, con su nivel de referencia y su cita."
      />

      <div className="mb-6 flex gap-2">
        <TabButton active={subTab === 'casos'} onClick={() => setSubTab('casos')} icon={ListChecks}>
          Casos de prueba (74)
        </TabButton>
        <TabButton active={subTab === 'corpus'} onClick={() => setSubTab('corpus')} icon={BookOpen}>
          Corpus normativo
        </TabButton>
      </div>

      {subTab === 'casos' ? <CasosExplorer /> : <CorpusExplorer />}
    </div>
  )
}

function TabButton({
  active,
  onClick,
  icon: Icon,
  children,
}: {
  active: boolean
  onClick: () => void
  icon: typeof BookOpen
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={clsx(
        'flex items-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition',
        active ? 'bg-teal-500 text-slate-950' : 'bg-slate-800/60 text-slate-400 hover:text-slate-200',
      )}
    >
      <Icon className="h-4 w-4" />
      {children}
    </button>
  )
}

function CasosExplorer() {
  const [cases, setCases] = useState<GoldCase[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<number | 'all' | 'ambiguo' | 'abstencion'>('all')

  useEffect(() => {
    fetchCasos()
      .then((r) => setCases(r.cases))
      .catch((e) => setError(e instanceof Error ? e.message : 'Error desconocido'))
  }, [])

  const filtered = useMemo(() => {
    if (!cases) return []
    return cases.filter((c) => {
      const matchesQuery = query.trim() === '' || c.text.toLowerCase().includes(query.toLowerCase())
      if (!matchesQuery) return false
      if (levelFilter === 'all') return true
      if (levelFilter === 'ambiguo') return c.ambiguous
      if (levelFilter === 'abstencion') return c.should_abstain
      return c.final_level === levelFilter
    })
  }, [cases, query, levelFilter])

  if (error) return <ErrorBox message={error} />
  if (!cases) return <Spinner label="Cargando casos..." />

  return (
    <Card>
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Buscar en el relato..."
            className="w-full rounded-lg border border-slate-700 bg-slate-800/80 py-2 pl-9 pr-3 text-sm text-slate-100 outline-none ring-teal-500/50 placeholder:text-slate-500 focus:ring-2"
          />
        </div>
        <div className="flex flex-wrap gap-1.5">
          {(['all', 1, 2, 3, 4, 5, 'ambiguo', 'abstencion'] as const).map((f) => (
            <button
              key={String(f)}
              onClick={() => setLevelFilter(f)}
              className={clsx(
                'rounded-full px-2.5 py-1 text-xs font-medium transition',
                levelFilter === f ? 'bg-teal-500 text-slate-950' : 'bg-slate-800/60 text-slate-400 hover:text-slate-200',
              )}
            >
              {f === 'all' ? 'Todos' : f === 'ambiguo' ? 'Ambiguos' : f === 'abstencion' ? 'Abstención' : `N${f}`}
            </button>
          ))}
        </div>
      </div>

      <p className="mb-3 text-xs text-slate-500">{filtered.length} de {cases.length} casos</p>

      <div className="flex max-h-[32rem] flex-col gap-2 overflow-y-auto pr-1">
        {filtered.map((c) => (
          <div key={c.case_id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
            <div className="mb-1.5 flex flex-wrap items-center gap-2">
              <code className="text-xs font-semibold text-slate-400">{c.case_id}</code>
              {c.should_abstain ? (
                <span className="rounded-full bg-slate-700/60 px-2 py-0.5 text-[11px] text-slate-300">
                  caso de abstención
                </span>
              ) : c.ambiguous ? (
                <span className="rounded-full bg-purple-500/15 px-2 py-0.5 text-[11px] text-purple-300">
                  ambiguo (excluido)
                </span>
              ) : (
                <LevelBadge level={c.final_level} compact />
              )}
              {c.final_citation && (
                <code className="text-[11px] text-slate-600">{c.final_citation}</code>
              )}
            </div>
            <p className="text-sm text-slate-300">{c.text}</p>
          </div>
        ))}
      </div>
    </Card>
  )
}

function CorpusExplorer() {
  const [format, setFormat] = useState<CorpusFormat>('reformatted')
  const [chunks, setChunks] = useState<CorpusChunk[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setChunks(null)
    fetchCorpus(format)
      .then((r) => setChunks(r.chunks))
      .catch((e) => setError(e instanceof Error ? e.message : 'Error desconocido'))
  }, [format])

  return (
    <Card>
      <div className="mb-4 flex items-center gap-2">
        {(['reformatted', 'raw'] as const).map((f) => (
          <button
            key={f}
            onClick={() => setFormat(f)}
            className={clsx(
              'rounded-full px-3 py-1 text-xs font-medium transition',
              format === f ? 'bg-teal-500 text-slate-950' : 'bg-slate-800/60 text-slate-400 hover:text-slate-200',
            )}
          >
            {f === 'reformatted' ? 'Reformateado' : 'Crudo'}
          </button>
        ))}
      </div>

      {error && <ErrorBox message={error} />}
      {!chunks && !error && <Spinner label="Cargando corpus..." />}

      {chunks && (
        <div className="flex max-h-[32rem] flex-col gap-2 overflow-y-auto pr-1">
          {chunks.map((c) => (
            <div key={c.chunk_id} className="rounded-xl border border-slate-800 bg-slate-950/40 p-3">
              <div className="mb-1.5 flex items-center gap-2">
                <code className="text-xs font-semibold text-teal-300">{c.chunk_id}</code>
                <LevelBadge level={c.level} compact />
              </div>
              <p className="whitespace-pre-line text-xs leading-relaxed text-slate-400">
                {formatChunkText(c.text)}
              </p>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}
