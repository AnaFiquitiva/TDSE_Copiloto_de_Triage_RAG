# Resultados del diseño experimental 2x2 + línea base (C0)

Generado automáticamente por `experiments/run_experiment.py`. Estas cifras son el resultado de ejecutar el pipeline sobre las 74 viñetas sintéticas de `data/cases.json` (dentro del rango de 60-100 casos del protocolo del documento del proyecto, pero con doble ciego intra-equipo, no evaluadores clínicos externos); no constituyen una validación clínica externa (ver `README.md`, sección de limitaciones).

## Acuerdo intra-equipo (gold standard)

- Pares evaluados: 68
- Kappa ponderado cuadrático (κ_w): 0.953

## Línea base C0 (árbol de reglas, sin RAG)

- Casos elegibles: 66
- S (sub-triage ponderado): 0.545
- Sensibilidad niveles I-II: 0.303
- Fidelidad de citación: 0.227
- S por nivel de referencia: {1: 1.4444444444444444, 2: 0.6666666666666666, 3: 0.0, 4: 0.0, 5: 0.0}

## Celdas del diseño 2x2 (copiloto: recuperación + generación mínima)

| Celda | Corpus | Embeddings | N elegibles | Cobertura | S | Sensib. I-II | Recall@k | Fidelidad citación | Abst. correcta | Abst. indebida |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | raw | generic | 66 | 0.47 | 0.258 | 0.485 | 0.500 | 0.387 | 0.500 | 0.530 |
| E2 | reformatted | generic | 66 | 0.41 | 0.074 | 0.212 | 0.561 | 0.407 | 0.500 | 0.591 |
| E3 | raw | clinical_es | 66 | 0.48 | 0.250 | 0.485 | 0.545 | 0.438 | 0.500 | 0.515 |
| E4 | reformatted | clinical_es | 66 | 0.48 | 0.125 | 0.303 | 0.606 | 0.406 | 0.500 | 0.515 |

### S desglosado por nivel de referencia, por celda

- **E1**: {1: 0.08333333333333333, 2: 0.6, 3: 0.0, 4: 0.5, 5: 0.0}
- **E2**: {1: 0.0, 2: 0.6666666666666666, 3: 0.0, 4: 0.0, 5: 0.0}
- **E3**: {1: 0.07692307692307693, 2: 0.6666666666666666, 3: 0.0, 4: 0.5, 5: 0.0}
- **E4**: {1: 0.2857142857142857, 2: 0.3333333333333333, 3: 0.0, 4: 0.0, 5: 0.0}
