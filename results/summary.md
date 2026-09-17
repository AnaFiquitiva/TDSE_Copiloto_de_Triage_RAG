# Resultados del diseño experimental 2x2 + línea base (C0)

Generado automáticamente por `experiments/run_experiment.py`. Estas cifras son el resultado de ejecutar el pipeline sobre las 48 viñetas sintéticas de `data/cases.json` (versión reducida e ilustrativa del protocolo de 60-100 casos descrito en el documento del proyecto); no constituyen una validación clínica externa (ver `README.md`, sección de limitaciones).

## Acuerdo intra-equipo (gold standard)

- Pares evaluados: 44
- Kappa ponderado cuadrático (κ_w): 0.972

## Línea base C0 (árbol de reglas, sin RAG)

- Casos elegibles: 43
- S (sub-triage ponderado): 0.581
- Sensibilidad niveles I-II: 0.333
- Fidelidad de citación: 0.279
- S por nivel de referencia: {1: 1.5714285714285714, 2: 0.42857142857142855, 3: 0.0, 4: 0.0, 5: 0.0}

## Celdas del diseño 2x2 (copiloto: recuperación + generación mínima)

| Celda | Corpus | Embeddings | N elegibles | Cobertura | S | Sensib. I-II | Recall@k | Fidelidad citación | Abst. correcta | Abst. indebida |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | raw | generic | 43 | 0.49 | 0.095 | 0.714 | 0.488 | 0.429 | 0.750 | 0.512 |
| E2 | reformatted | generic | 43 | 0.44 | 0.000 | 0.333 | 0.512 | 0.421 | 0.750 | 0.558 |
| E3 | raw | clinical_es | 43 | 0.51 | 0.091 | 0.714 | 0.558 | 0.500 | 0.750 | 0.488 |
| E4 | reformatted | clinical_es | 43 | 0.56 | 0.083 | 0.476 | 0.581 | 0.417 | 0.750 | 0.442 |

### S desglosado por nivel de referencia, por celda

- **E1**: {1: 0.09090909090909091, 2: 0.2, 3: 0.0, 4: 0.0, 5: 0.0}
- **E2**: {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
- **E3**: {1: 0.08333333333333333, 2: 0.25, 3: 0.0, 4: 0.0, 5: 0.0}
- **E4**: {1: 0.2857142857142857, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
