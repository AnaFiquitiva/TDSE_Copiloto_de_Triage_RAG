# TDSE · Copiloto de Triage RAG

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

## Arquitectura

El prototipo sigue una arquitectura de **pipeline en capas**, con una separación
estricta entre recuperación (evidencia) y generación (sugerencia), y un registro
de auditoría transversal a ambas. No hay una capa de servicio/API: la evaluación
de este semestre es un pipeline offline por lotes, no un servicio desplegado (ver
"Limitaciones" más abajo).

```mermaid
flowchart LR
    subgraph Entrada
        R["Relato libre del paciente"]
    end

    subgraph Comp2["Componente 2 · Ingesta y recuperación (src/ingest.py, retrieval.py)"]
        C[("corpus/raw/ o\ncorpus/reformatted/")] --> ING["ingest.py\nfragmentos citables"]
        ING --> RET["retrieval.py\nTF-IDF: generic | clinical_es"]
    end

    subgraph Comp3["Componente 3 mínimo · Generación (src/generator.py)"]
        GEN["generator.py\nvecino más cercano +\nmargen de confianza"]
    end

    subgraph C0["Línea base C0 (src/baseline.py)"]
        BASE["baseline.py\nárbol de reglas congelado\n(data/keyword_rules.json)"]
    end

    R --> RET
    RET --> GEN
    R --> BASE

    GEN -->|"nivel + cita, o abstención"| AUD["audit.py\nregistro JSONL"]
    AUD --> HUM["Interfaz mínima de revisión\n(demo.py / componente 4, futuro)"]

    GEN -.-> MET["metrics.py\nS, kappa, recall@k, fidelidad"]
    BASE -.-> MET
```

**Flujo de datos (`src/pipeline.py` orquesta los tres primeros pasos):**

1. **Ingesta (`ingest.py`)** parsea `corpus/raw/` o `corpus/reformatted/` en
   `Chunk`s, cada uno con un id de cita y, cuando aplica, un único nivel de
   triage asociado. El formato crudo usa expresiones regulares frágiles a
   propósito (simula un extractor genérico de PDF/tabla); el reformateado usa
   encabezados `[CITA: ...]` limpios. Esta es la manifestación concreta de la
   brecha G3 del documento del proyecto (guías con *layout* complejo).
2. **Recuperación (`retrieval.py`)** indexa esos fragmentos con TF-IDF propio
   (sin dependencias externas) y expone `retrieve(texto, k)`. El modo
   `clinical_es` aplica un léxico de normalización coloquial→clínico antes de
   vectorizar, como sustituto determinista de un modelo de embeddings de
   dominio (Factor B del diseño 2x2).
3. **Generación (`generator.py`)** toma los fragmentos recuperados y aplica una
   regla de vecino-más-cercano con margen de confianza: sugiere el nivel del
   fragmento más similar, o se abstiene si la evidencia es insuficiente o
   contradictoria. Nunca emite un nivel sin una cita que lo respalde.
4. **Auditoría (`audit.py`)** registra, para cada caso, el relato de entrada,
   los fragmentos recuperados con su score, la versión de corpus/embeddings, y
   la sugerencia (incluida la abstención), en JSON Lines — la base para que un
   humano pueda revisar y para que `metrics.py` pueda evaluar.
5. La **línea base C0 (`baseline.py`)** es una ruta independiente y paralela:
   un árbol de reglas por palabras clave (`data/keyword_rules.json`, congelado
   antes de evaluar) que recibe el mismo relato de texto libre, sin pasar por
   recuperación ni por el componente 3.
6. **`experiments/run_experiment.py`** ejecuta las cuatro celdas del diseño 2x2
   (E1-E4) más C0 sobre `data/cases.json` y calcula las métricas formales de
   `metrics.py` (Sección "Métricas" abajo).

Esta arquitectura corresponde a una versión mínima y ejecutable de la "vista
arquitectónica preliminar" del documento del proyecto (componentes 1-4:
extracción del relato, recuperación, generación con citación, y revisión
humana): aquí los componentes 2 y 3 están implementados en versión mínima:
`demo.py` funciona como una interfaz de inspección manual muy básica del
componente 4 (revisión humana), no como la interfaz de producción descrita
conceptualmente en el documento. La integración con historia clínica (FHIR),
la multi-tenencia y el despliegue como servicio quedan fuera de esta
arquitectura de prototipo (ver "Limitaciones").

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
cd TDSE_Copiloto_de_Triage_RAG
python -m unittest discover -s tests -v   # correr las pruebas
python -m experiments.run_experiment      # correr el diseño 2x2 + linea base
python -m experiments.analyze_external_data  # analizar el dataset real (ver abajo)
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
  external_triage_urgencias_colombia.csv  Dataset real de Datos Abiertos Colombia (ver abajo)
src/
  ingest.py       Parseo de ambos formatos de corpus a fragmentos citables
  retrieval.py    Recuperación TF-IDF, modos 'generic' y 'clinical_es'
  generator.py    Componente 3 mínimo: nivel + cita, o abstención
  baseline.py     Línea base C0 (árbol de reglas, sin RAG)
  metrics.py      S (sub-triage), kappa ponderado, recall@k, abstención
  audit.py        Registro de auditoría (JSON Lines)
  pipeline.py     Orquesta un caso: recuperación -> generación -> auditoría
experiments/
  run_experiment.py        Ejecuta las celdas E1-E4 + C0 sobre data/cases.json
  analyze_external_data.py Analiza el dataset real (distribución de niveles y tiempos)
results/
  summary.md                  Resultados en Markdown (generado por run_experiment.py)
  raw_results.json            Resultados en JSON (generado por run_experiment.py)
  audit_*.jsonl                Registro de auditoría por celda (generado por run_experiment.py)
  external_data_summary.md    Análisis del dataset real (generado por analyze_external_data.py)
tests/            Pruebas unitarias de cada módulo
demo.py           CLI de una sola consulta, para inspección manual
```

## Fuentes de datos reales

Se buscaron activamente bases de datos reales que pudieran mejorar el
prototipo. El hallazgo central: **no existen historias clínicas reales de
triage con relato libre del paciente y de acceso abierto sin restricciones**
(por buenas razones de protección de datos de salud); lo que sí existe, y se
documenta aquí con honestidad sobre qué puede y qué no puede hacer cada
fuente:

### Integrado en este repositorio

- **[Clasificación en Triage Urgencias](https://www.datos.gov.co/Salud-y-Protecci-n-Social/Clasificaci-n-en-Triage-Urgencias/vt5n-eu2r)**
  (Datos Abiertos Colombia, dataset `vt5n-eu2r`, ~89.000 registros, acceso
  público sin credenciales vía API Socrata). Es un dataset **administrativo**:
  trae nivel de triage (I-V) y marcas de tiempo de ingreso/atención de una red
  de IPS, **no** el relato del paciente. Se descargó completo a
  `data/external_triage_urgencias_colombia.csv` y se analiza con
  `experiments/analyze_external_data.py` (resultado real en
  `results/external_data_summary.md`). Sirve para dos cosas que el documento
  del proyecto dejó como supuestos no verificados:
  - Confirma empíricamente que los niveles I-II son una fracción muy pequeña
    de los casos reales (~3.3% en este dataset), lo que justifica con datos —
    no solo con intuición — la decisión de sobremuestrearlos en
    `data/cases.json`.
  - Da una referencia real (aunque secundaria e ilustrativa) de tiempos de
    ingreso a atención por nivel, en lugar de las cifras puramente
    hipotéticas que el documento del proyecto declaraba explícitamente como
    no medidas.

### Relevantes para una fase posterior (no integradas)

- **[MIMIC-IV-ED Demo](https://physionet.org/content/mimic-iv-ed-demo/2.2/)**
  (PhysioNet, 100 pacientes, acceso abierto sin credenciales): sí incluye
  motivo de consulta en texto libre, nivel ESI (1-5) y signos vitales — la
  estructura más parecida a lo que necesita el clasificador de texto del
  copiloto — pero está en **inglés** y de un hospital de EE. UU., por lo que
  no es sustituto de datos en español sin una traducción/adaptación cuidadosa
  (y sería una forma razonable de probar si la arquitectura generaliza a otro
  idioma). El dataset completo (~425.000 estancias) existe en PhysioNet pero
  requiere registro, entrenamiento en sujetos humanos y firma de un acuerdo de
  uso de datos (DUA).
- **[ClinText-SP](https://arxiv.org/pdf/2503.18594)** y
  **CoWeSe (Corpus Web Salud Español)**: corpus abiertos de texto clínico y
  biomédico en español (26M y ~750M tokens respectivamente), no específicos de
  triage. Son la ruta natural para entrenar un modelo real de embeddings
  clínicos en español y así reemplazar el léxico de normalización de
  `retrieval.py` (modo `clinical_es`) por un modelo real, cerrando la brecha
  G1 del documento del proyecto.
- **[CARMEN-I](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12215073/)**:
  2.000 documentos clínicos anonimizados del Hospital Clínic de Barcelona en
  español/catalán (informes de alta, interconsultas, radiología). Útil para
  NER/anonimización, no para triage específicamente.

Ninguna de estas fuentes internacionales sustituye la necesidad, señalada en
el documento del proyecto, de una validación clínica externa con
profesionales de salud colombianos sobre el dominio y la normativa
específicos de este prototipo.

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
- El dataset externo real (`data/external_triage_urgencias_colombia.csv`) es
  administrativo y de una sola red de IPS reportante: no contiene relato de
  paciente, no es necesariamente representativo de todo el país, y no se usa
  para entrenar ni evaluar el clasificador de texto (ver "Fuentes de datos
  reales").

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
- Entrenar un modelo real de embeddings clínicos en español sobre corpus como
  ClinText-SP o CoWeSe (ver "Fuentes de datos reales"), y validar la
  generalización de la arquitectura con MIMIC-IV-ED (en inglés) antes de
  intentarlo en español.

## Licencia

MIT. Ver `LICENSE`.
