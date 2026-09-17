# Copiloto de apoyo al triage de urgencias (prototipo RAG offline)

Prototipo funcional de los **componentes 2 y 3 (versión mínima)** de un copiloto de
apoyo al triage de urgencias basado en generación aumentada por recuperación (RAG):
ingesta y recuperación sobre normativa colombiana de triage, más un clasificador
mínimo que produce una sugerencia de nivel **con cita obligatoria o abstención**.

El sistema **asiste, no decide**: produce una sugerencia trazable a un fragmento
normativo concreto, o se abstiene cuando la evidencia recuperada es insuficiente o
contradictoria. La clasificación final es siempre responsabilidad del personal de
salud.

Este repositorio implementa, en forma de software ejecutable, el diseño
experimental descrito en el documento del proyecto: ingesta de corpus en dos
formatos (crudo y reformateado), recuperación con dos modos de vectorización
(genérico y adaptado al dominio clínico en español), un clasificador mínimo con
citación obligatoria, una línea base de reglas, un registro de auditoría, y las
métricas formales (tasa de sub-triage ponderada, kappa ponderado, recall@k,
fidelidad de citación) necesarias para evaluar las cuatro celdas del diseño 2x2
más la línea base.

## Aviso importante

- El texto de `corpus/` es una **reconstrucción sintética**, elaborada por el
  equipo con fines académicos, de la estructura general de cinco niveles de
  triage y de señales de alarma usada en el sistema colombiano y en escalas
  internacionales comparables. **No es una transcripción literal ni oficial**
  de la Resolución 5596 de 2015 ni de ninguna guía clínica institucional.
- El conjunto de 34 viñetas de `data/cases.json` es sintético y fue etiquetado
  por el propio equipo (sin evaluadores clínicos externos). Es una versión
  reducida e ilustrativa del protocolo de 60-100 casos con doble ciego descrito
  en el documento del proyecto: sirve para ejercitar el pipeline y la
  maquinaria de métricas de extremo a extremo, **no** para sostener una
  afirmación de seguridad clínica real.
- Este software es un prototipo académico. **No debe usarse para tomar
  decisiones clínicas reales.**

## Instalación

Requiere Python 3.10+. No tiene dependencias externas (todo el pipeline usa la
biblioteca estándar), precisamente para que la evaluación offline sea
reproducible sin acceso a internet ni a paquetes de terceros.

```bash
git clone <url-del-repositorio>
cd triage-copiloto-rag
python -m unittest discover -s tests -v   # correr las pruebas
python -m experiments.run_experiment      # correr el diseño 2x2 + linea base
python demo.py "el paciente tiene dolor en el pecho y sudoracion fria"
```

## Estructura del repositorio

```
corpus/
  raw/            Guías en formato crudo (tablas y flujogramas sin reformatear)
  reformatted/    Las mismas guías, reformateadas a texto estructurado con citas
data/
  cases.json      34 viñetas sintéticas con gold standard intra-equipo
  keyword_rules.json  Línea base de reglas (C0), congelada antes de evaluar
src/
  ingest.py       Parseo de ambos formatos de corpus a fragmentos citables
  retrieval.py    Recuperación TF-IDF, modos 'generic' y 'clinical_es'
  generator.py    Componente 3 mínimo: nivel + cita, o abstención
  baseline.py     Línea base C0 (árbol de reglas, sin RAG)
  metrics.py      S (sub-triage), kappa ponderado, recall@k, abstención
  audit.py        Registro de auditoría (JSON Lines)
  pipeline.py     Orquesta un caso: recuperación -> generación -> auditoría
experiments/
  run_experiment.py  Ejecuta las celdas E1-E4 + C0 sobre data/cases.json
results/
  summary.md        Resultados en Markdown (generado por run_experiment.py)
  raw_results.json  Resultados en JSON (generado por run_experiment.py)
  audit_*.jsonl     Registro de auditoría por celda (generado por run_experiment.py)
tests/            Pruebas unitarias de cada módulo
demo.py           CLI de una sola consulta, para inspección manual
```

## Diseño experimental (resumen)

Se compara la línea base de reglas (**C0**) contra cuatro celdas de un diseño
factorial 2x2 sobre el copiloto:

| Celda | Corpus | Embeddings |
|---|---|---|
| E1 | crudo | genérico |
| E2 | reformateado | genérico |
| E3 | crudo | clínico en español |
| E4 | reformateado | clínico en español |

- **Factor A (formato del corpus):** crudo (tablas y flujogramas sin modificar,
  con ids de cita opacos) vs. reformateado (fragmentos estructurados con cita
  semántica explícita).
- **Factor B (embeddings):** este entorno no tiene garantizado acceso a
  internet ni a pesos preentrenados, así que **no se descarga un modelo real de
  embeddings**. En su lugar, ambos modos usan el mismo motor TF-IDF; el modo
  `clinical_es` añade, antes de vectorizar, un léxico de normalización que
  traduce expresiones coloquiales del relato ("me falta el aire") a su término
  clínico equivalente ("dificultad respiratoria"), como sustituto determinista
  y reproducible de un modelo de embeddings clínico en español (p. ej. Carrino
  et al., 2022). Sustituir esta pieza por un modelo real de embeddings es la
  ruta natural de evolución de este prototipo y no cambia el resto del
  pipeline ni la interfaz de `Retriever`.

El clasificador mínimo (componente 3) es una regla de vecino-más-cercano sobre
los fragmentos recuperados: sugiere el nivel del fragmento más similar si su
similitud supera un umbral mínimo y aventaja con un margen suficiente al mejor
fragmento que proponga un nivel distinto; en caso contrario, se abstiene.

## Métricas

- **S (tasa de sub-triage ponderada):** promedio de `max(0, nivel_sugerido -
  nivel_referencia)` sobre los casos con sugerencia no abstenida. Solo
  penaliza cuando el sistema subestima la urgencia.
- **Sensibilidad I-II:** de los casos cuyo nivel de referencia es I o II, qué
  fracción fue sugerida también como I o II (una abstención cuenta como fallo,
  por diseño conservador).
- **Recall@k:** fracción de casos en los que el fragmento normativo correcto
  apareció entre los k fragmentos recuperados (k=5).
- **Fidelidad de citación:** de las sugerencias no abstenidas, qué fracción
  cita efectivamente el criterio correcto.
- **Kappa ponderado cuadrático (κ_w):** acuerdo intra-equipo en el
  etiquetado del gold standard (no es una validación clínica externa).

Las fórmulas completas están documentadas como docstrings en `src/metrics.py`.

## Resultados

`results/summary.md` y `results/raw_results.json` contienen la salida real de
`python -m experiments.run_experiment` sobre las 34 viñetas de este
repositorio. Un extracto representativo (los números exactos pueden variar
levemente si se edita `data/cases.json` o los umbrales de `src/generator.py`):

- Con solo 34 casos, ninguna diferencia entre celdas es estadísticamente
  concluyente; el valor de este resultado es mostrar que el pipeline y las
  métricas funcionan de extremo a extremo, no establecer cuál celda "gana".
- El sistema se abstiene en una fracción considerable de los casos elegibles:
  es una consecuencia esperada de un corpus deliberadamente pequeño (13
  fragmentos) y un umbral de margen conservador, no un error del pipeline. Un
  corpus más completo (60-100 casos y más fragmentos normativos, como plantea
  el documento del proyecto) reduciría la tasa de abstención sin relajar el
  umbral de seguridad.

## Limitaciones (heredadas del documento del proyecto)

- El gold standard es intra-equipo, no una validación clínica externa. El
  κ_w reportado mide consistencia interna del criterio aplicado, no
  corrección clínica.
- El corpus normativo es una reconstrucción sintética reducida, no el texto
  oficial completo de la Resolución 5596 ni de guías clínicas institucionales.
- El componente de "embeddings clínicos en español" es un proxy determinista
  (TF-IDF + léxico de dominio), no un modelo de embeddings real, por
  restricciones del entorno de ejecución (sin acceso garantizado a internet).
- La evaluación es 100% offline y por lotes; no mide latencia bajo
  concurrencia ni incluye un despliegue en producción.

## Extensión a un despliegue real

Puntos de extensión ya previstos en el código, sin necesidad de rediseñar el
pipeline:

- Reemplazar `Retriever` (modo `clinical_es`) por un modelo de embeddings
  real vía una librería como `sentence-transformers`, manteniendo la misma
  interfaz `retrieve(texto, k)`.
- Reemplazar la regla determinista de `MinimalGenerator` por una llamada a un
  modelo de lenguaje vía API, manteniendo el contrato de salida (`Suggestion`:
  nivel, cita, confianza, abstención).
- Ampliar `data/cases.json` a 60-100 casos con doble ciego real por
  evaluadores clínicos externos, siguiendo el esquema ya definido en cada
  registro (`evaluator1`, `evaluator2`, `resolution_method`, etc.).

## Licencia

MIT. Ver `LICENSE`.
