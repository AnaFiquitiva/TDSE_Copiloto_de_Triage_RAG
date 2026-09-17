# Comparación de backends: determinista vs. Gemini

Generado por `experiments/compare_backends.py` sobre las mismas 74 viñetas de `data/cases.json`, ambas con corpus `reformatted`, para aislar el efecto del backend de generación/recuperación.

Backend Gemini realmente usado por caso: {'gemini': 71, 'gemini_fallback_deterministic': 3} (si aparece 'gemini_fallback_deterministic', esos casos cayeron al backend determinista por falta de `GEMINI_API_KEY` o un error de red — no es un fallo del experimento, es la salvaguarda de robustez de `src/pipeline.py`).

| Métrica | Determinista (TF-IDF) | Gemini (embeddings + LLM) |
|---|---|---|
| Casos elegibles | 66 | 66 |
| Cobertura (no abstención) | 0.48 | 0.91 |
| S (sub-triage ponderado) | 0.125 | 0.000 |
| Sensibilidad I-II | 0.303 | 0.879 |
| Recall@k | 0.606 | 0.909 |
| Tasa de abstención correcta | 0.500 | 1.000 |
| Tasa de abstención indebida | 0.515 | 0.091 |

Con solo 74 casos esta comparación es ilustrativa, no concluyente estadísticamente (igual que en `run_experiment.py`); su valor es mostrar que el backend Gemini es un reemplazo funcional del determinista bajo la misma interfaz y las mismas métricas, no declarar un ganador definitivo.
