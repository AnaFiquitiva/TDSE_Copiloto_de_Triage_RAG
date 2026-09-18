import { useEffect, useState } from 'react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { Database, ExternalLink } from 'lucide-react'

import { fetchDataset } from '../api'
import type { DatasetResponse } from '../types'
import { Card, ErrorBox, SectionTitle, Spinner, StatCard } from '../components/Common'
import { levelColor } from '../components/LevelBadge'

const LEVEL_ORDER = ['I', 'II', 'III', 'IV', 'V']
const LEVEL_NUM: Record<string, number> = { I: 1, II: 2, III: 3, IV: 4, V: 5 }

export function DatasetView() {
  const [data, setData] = useState<DatasetResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchDataset()
      .then(setData)
      .catch((e) => setError(e instanceof Error ? e.message : 'Error desconocido'))
      .finally(() => setLoading(false))
  }, [])

  const distributionData = LEVEL_ORDER.map((lvl) => ({
    nivel: lvl,
    n: data?.distribution[lvl] ?? 0,
    pct: data ? ((data.distribution[lvl] ?? 0) / data.total) * 100 : 0,
  }))

  const durationData = LEVEL_ORDER.filter((lvl) => data?.duration_stats[lvl]).map((lvl) => ({
    nivel: lvl,
    medianaMin: data?.duration_stats[lvl]?.median ?? 0,
  }))

  return (
    <div className="mx-auto max-w-6xl">
      <SectionTitle
        eyebrow="Fuente de datos reales"
        title="Datos Abiertos Colombia"
        description="Análisis del dataset público 'Clasificación en Triage Urgencias' (datos.gov.co, ~89.000 registros reales). No contiene el relato del paciente, así que no se usa para entrenar ni evaluar el copiloto — sirve para contrastar supuestos de diseño con datos reales."
      />

      {loading && <Spinner label="Cargando ~89.000 registros..." />}
      {error && <ErrorBox message={error} />}

      {data && !loading && (
        <div className="flex flex-col gap-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Registros totales" value={data.total.toLocaleString('es-CO')} accent="teal" />
            <StatCard
              label="Niveles I-II reales"
              value={`${(((data.distribution.I ?? 0) + (data.distribution.II ?? 0)) / data.total * 100).toFixed(1)}%`}
              hint="justifica sobremuestrear en el gold standard"
              accent="red"
            />
            <StatCard label="χ² (nivel × red de IPS)" value={data.chi2_independence_test.chi2.toFixed(0)} accent="sky" />
            <StatCard
              label="Valor p"
              value={data.chi2_independence_test.p_value < 0.001 ? '< 0.001' : data.chi2_independence_test.p_value.toFixed(3)}
              hint="diferencia significativa entre redes"
              accent="amber"
            />
          </div>

          <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
            <Card>
              <h3 className="mb-4 text-sm font-semibold text-slate-200">Distribución real de niveles de triage</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={distributionData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="nivel" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      formatter={(v) => `${Number(v).toFixed(2)}%`}
                      contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Bar dataKey="pct" radius={[6, 6, 0, 0]}>
                      {distributionData.map((d) => (
                        <Cell key={d.nivel} fill={levelColor(LEVEL_NUM[d.nivel])} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Los niveles I-II son una fracción muy pequeña en la práctica: por eso el gold standard de
                74 casos los sobremuestrea deliberadamente (18 y 15 casos respectivamente).
              </p>
            </Card>

            <Card>
              <h3 className="mb-4 text-sm font-semibold text-slate-200">Tiempo de ingreso a atención (mediana, min)</h3>
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={durationData} margin={{ top: 4, right: 8, left: -16, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="nivel" stroke="#64748b" fontSize={12} />
                    <YAxis stroke="#64748b" fontSize={12} />
                    <Tooltip
                      formatter={(v) => `${Number(v).toFixed(1)} min`}
                      contentStyle={{ background: '#0f172a', border: '1px solid #1e293b', borderRadius: 8 }}
                      labelStyle={{ color: '#e2e8f0' }}
                    />
                    <Bar dataKey="medianaMin" radius={[6, 6, 0, 0]}>
                      {durationData.map((d) => (
                        <Cell key={d.nivel} fill={levelColor(LEVEL_NUM[d.nivel])} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <p className="mt-2 text-xs text-slate-500">
                Dato agregado de una red de IPS reportante, no una medición prospectiva in situ. Se
                reporta como referencia secundaria, no como sustituto del instrumento de observación
                descrito en el documento del proyecto.
              </p>
            </Card>
          </div>

          <Card>
            <h3 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-200">
              <Database className="h-4 w-4 text-teal-400" />
              Distribución por red de IPS
            </h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[500px] text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-800 text-slate-500">
                    <th className="px-3 py-2 font-medium">Red</th>
                    {LEVEL_ORDER.map((l) => (
                      <th key={l} className="px-3 py-2 font-medium">
                        {l}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(data.by_red).map(([red, counts]) => {
                    const total = Object.values(counts).reduce((a, b) => a + b, 0)
                    return (
                      <tr key={red} className="border-b border-slate-800/60 text-slate-400">
                        <td className="px-3 py-2 font-semibold text-slate-200">{red}</td>
                        {LEVEL_ORDER.map((l) => (
                          <td key={l} className="px-3 py-2">
                            {(((counts[l] ?? 0) / total) * 100).toFixed(1)}%
                          </td>
                        ))}
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
            <a
              href="https://www.datos.gov.co/Salud-y-Protecci-n-Social/Clasificaci-n-en-Triage-Urgencias/vt5n-eu2r"
              target="_blank"
              rel="noreferrer"
              className="mt-4 inline-flex items-center gap-1.5 text-xs text-teal-400 hover:underline"
            >
              Ver dataset original en datos.gov.co <ExternalLink className="h-3 w-3" />
            </a>
          </Card>
        </div>
      )}
    </div>
  )
}
