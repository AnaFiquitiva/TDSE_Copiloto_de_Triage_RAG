# Resultados del diseño experimental 2x2 + línea base (C0)

Generado automáticamente por `experiments/run_experiment.py`. Estas cifras son el resultado de ejecutar el pipeline sobre las 34 viñetas sintéticas de `data/cases.json` (versión reducida e ilustrativa del protocolo de 60-100 casos descrito en el documento del proyecto); no constituyen una validación clínica externa (ver `README.md`, sección de limitaciones).

## Acuerdo intra-equipo (gold standard)

- Pares evaluados: 30
- Kappa ponderado cuadrático (κ_w): 0.965

## Línea base C0 (árbol de reglas, sin RAG)

- Casos elegibles: 29
- S (sub-triage ponderado): 0.379
- Sensibilidad niveles I-II: 0.500
- Fidelidad de citación: 0.414
- S por nivel de referencia: {1: 1.1428571428571428, 2: 0.42857142857142855, 3: 0.0, 4: 0.0, 5: 0.0}

## Celdas del diseño 2x2 (copiloto: recuperación + generación mínima)

| Celda | Corpus | Embeddings | N elegibles | Cobertura | S | Sensib. I-II | Recall@k | Fidelidad citación | Abst. correcta | Abst. indebida |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | raw | generic | 29 | 0.52 | 0.267 | 0.500 | 0.621 | 0.333 | 0.500 | 0.483 |
| E2 | reformatted | generic | 29 | 0.34 | 0.200 | 0.214 | 0.483 | 0.400 | 0.750 | 0.655 |
| E3 | raw | clinical_es | 29 | 0.48 | 0.286 | 0.429 | 0.655 | 0.357 | 0.500 | 0.517 |
| E4 | reformatted | clinical_es | 29 | 0.48 | 0.357 | 0.357 | 0.552 | 0.357 | 0.750 | 0.517 |

### S desglosado por nivel de referencia, por celda

- **E1**: {1: 1.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
- **E2**: {1: 2.0, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
- **E3**: {1: 1.3333333333333333, 2: 0.0, 3: 0.0, 4: 0.0, 5: 0.0}
- **E4**: {1: 2.0, 2: 0.16666666666666666, 3: 0.0, 4: 0.0, 5: 0.0}
