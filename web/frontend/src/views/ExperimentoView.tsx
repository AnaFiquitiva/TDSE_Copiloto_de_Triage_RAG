import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { FlaskConical, RefreshCw } from 'lucide-react'

import { fetchExperimento } from '../api'
import type { ExperimentoResponse } from '../types'
import { Card, ErrorBox, SectionTitle, Spinner, StatCard } from '../components/Common'

export function ExperimentoView() {
  const [data, setData] = useState<ExperimentoResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchExperimento())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const chartData = data
    ? [
        {
          celda: 'C0 (reglas)',
          'S (sub-triage)': round(data.baseline.S_sub_triage),
          'Sensibilidad I-II': round(data.baseline.sensibilidad_I_II),
          'Recall@k': 0,
        },
        ...data.cells.map((c) => ({
          celda: c.cell,
          'S (sub-triage)': round(c.S_sub_triage),
          'Sensibilidad I-II': round(c.sensibilidad_I_II),
          'Recall@k': round(c.recall_at_k),
        })),
      ]
    : []

  return (
    <div className="mx-auto max-w-6xl">
      <div className="flex items-start justify-between gap-4">
        <SectionTitle
          eyebrow="Diseño experimental 2x2"
          title="Experimento E1–E4 + línea base C0"
          description="Corre el mismo cómputo que `python -m experiments.run_experiment` sobre el gold standard de 74 viñetas, comparando formato de corpus (crudo/reformateado) y modo de embeddings (genérico/clínico ES) contra la línea base de reglas."
        />
        <button
          onClick={load}
          disabled={loading}
          className="mt-1 flex shrink-0 items-center gap-2 rounded-lg border border-slate-700 bg-slate-800/60 px-3 py-2 text-xs font-medium text-slate-300 transition hover:border-teal-500/50 hover:text-teal-300 disabled:opacity-50"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? 'animate-spin' : ''}`} />
          Volver a ejecutar
        </button>
      </div>

      {loading && <Spinner label="Ejecutando las 4 celdas + línea base sobre 74 casos..." />}
      {error && <ErrorBox message={error} />}

      {data && !loading && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Casos totales" value={String(data.n_total_cases)} accent="teal" />
            <StatCard
              label="Kappa intra-equipo"
              value={data.kappa.kappa_ponderado_cuadratico.toFixed(3)}
              hint={`sobre ${data.kappa.n_pares} pares`}
              accent="sky"
            />
            <StatCard
              label="Mejor S (menor es mejor)"
              value={Math.min(...data.cells.map((c) => c.S_sub_triage)).toFixed(3)}
              accent="amber"
            />
            <StatCard
              label="Mejor sensibilidad I-II"
              value={`${(Math.max(...data.cells.map((c) => c.sensibilidad_I_II)) * 100).toFixed(0)}%`}
              accent="red"
            />
          </div>

          <Card>
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <FlaskConical className="h-4 w-4 text-teal-400" />
              Comparación por celda
            </h3>
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="celda" stroke="#64748b" fontSize={12} />
                  <YAxis stroke="#64748b" fontSize={12} domain={[0, 1]} />
                  <Tooltip
                    contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                    labelStyle={{ color: '#e2e8f0' }}
                  />
                  <Legend wrapperStyle={{ fontSize: 12 }} />
                  <Bar dataKey="S (sub-triage)" fill="#f87171" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Sensibilidad I-II" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="Recall@k" fill="#34d399" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <p className="mt-2 text-xs text-slate-500">
              S (sub-triage): más bajo es mejor. Sensibilidad I-II y Recall@k: más alto es mejor. C0 no
              recupera fragmentos, por eso no tiene Recall@k.
            </p>
          </Card>

          <Card className="overflow-x-auto">
            <h3 className="mb-4 text-sm font-semibold text-slate-200">Tabla completa</h3>
            <table className="w-full min-w-[720px] text-left text-xs">
              <thead>
                <tr className="border-b border-slate-800 text-slate-500">
                  {['Celda', 'Corpus', 'Embeddings', 'N', 'Cobertura', 'S', 'Sens. I-II', 'Recall@k', 'Fidelidad', 'Abst. correcta', 'Abst. indebida'].map(
                    (h) => (
                      <th key={h} className="whitespace-nowrap px-3 py-2 font-medium">
                        {h}
                      </th>
                    ),
                  )}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-slate-800/60 text-slate-400">
                  <td className="px-3 py-2 font-semibold text-slate-200">C0</td>
                  <td className="px-3 py-2">reglas</td>
                  <td className="px-3 py-2">—</td>
                  <td className="px-3 py-2">{data.baseline.n_eligible_cases}</td>
                  <td className="px-3 py-2">—</td>
                  <td className="px-3 py-2">{data.baseline.S_sub_triage.toFixed(3)}</td>
                  <td className="px-3 py-2">{data.baseline.sensibilidad_I_II.toFixed(3)}</td>
                  <td className="px-3 py-2">—</td>
                  <td className="px-3 py-2">{data.baseline.fidelidad_citacion.toFixed(3)}</td>
                  <td className="px-3 py-2">—</td>
                  <td className="px-3 py-2">—</td>
                </tr>
                {data.cells.map((c) => (
                  <tr key={c.cell} className="border-b border-slate-800/60 text-slate-400">
                    <td className="px-3 py-2 font-semibold text-teal-300">{c.cell}</td>
                    <td className="px-3 py-2">{c.corpus_format}</td>
                    <td className="px-3 py-2">{c.embedding_mode}</td>
                    <td className="px-3 py-2">{c.n_eligible_cases}</td>
                    <td className="px-3 py-2">{c.cobertura.toFixed(2)}</td>
                    <td className="px-3 py-2">{c.S_sub_triage.toFixed(3)}</td>
                    <td className="px-3 py-2">{c.sensibilidad_I_II.toFixed(3)}</td>
                    <td className="px-3 py-2">{c.recall_at_k.toFixed(3)}</td>
                    <td className="px-3 py-2">{c.fidelidad_citacion.toFixed(3)}</td>
                    <td className="px-3 py-2">{c.tasa_abstencion_correcta.toFixed(3)}</td>
                    <td className="px-3 py-2">{c.tasa_abstencion_indebida.toFixed(3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Card>
        </div>
      )}
    </div>
  )
}

function round(n: number): number {
  return Math.round(n * 1000) / 1000
}
