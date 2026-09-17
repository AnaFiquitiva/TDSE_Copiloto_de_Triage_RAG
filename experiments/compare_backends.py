"""Compara el backend determinista (TF-IDF + vecino-más-cercano, sin red) contra
el backend Gemini (embeddings + generación reales, requiere `GEMINI_API_KEY`)
sobre las mismas 34 viñetas de `data/cases.json`, usando siempre el corpus
reformateado (para aislar el efecto del backend del efecto del formato del
corpus, que ya se evalúa por separado en `run_experiment.py`).

Requiere `GEMINI_API_KEY` configurada (ver README.md, sección "Backend LLM
opcional"). Si no está configurada, el backend "gemini" cae automáticamente
al determinista para cada caso (el pipeline nunca se cae por falta de key),
así que en ese caso ambas columnas terminan siendo iguales — no es un error,
es la salvaguarda de robustez descrita en `src/pipeline.py`.

Uso:
    python -m experiments.compare_backends
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from src import metrics  # noqa: E402
from src.audit import AuditLog  # noqa: E402
from src.ingest import canonical_citation  # noqa: E402
from src.pipeline import CopilotoPipeline  # noqa: E402

CASES_PATH = ROOT / "data" / "cases.json"
RESULTS_DIR = ROOT / "results"
CORPUS_FORMAT = "reformatted"


def load_cases() -> list[dict]:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def evaluate_backend(backend: str, cases: list[dict]) -> dict:
    audit_path = RESULTS_DIR / f"audit_compare_{backend}.jsonl"
    if audit_path.exists():
        audit_path.unlink()
    pipeline = CopilotoPipeline(corpus_format=CORPUS_FORMAT, backend=backend, audit_path=audit_path)

    eligible_pairs: list[tuple[int, int]] = []
    sensitivity_pairs: list[tuple[int, int]] = []
    recall_hits: list[bool] = []
    should_abstain_flags: list[bool] = []
    actually_abstained_flags: list[bool] = []
    n_eligible = 0
    n_abstained_among_eligible = 0

    for case in cases:
        suggestion = pipeline.run_case(case["case_id"], case["text"])

        if case["should_abstain"]:
            should_abstain_flags.append(True)
            actually_abstained_flags.append(suggestion.abstained)
            continue
        if case["ambiguous"] or case["final_level"] is None:
            continue

        should_abstain_flags.append(False)
        actually_abstained_flags.append(suggestion.abstained)
        n_eligible += 1

        hit = any(
            canonical_citation(rc.chunk.chunk_id) == case["final_citation"]
            for rc in suggestion.retrieved
        )
        recall_hits.append(hit)

        if suggestion.abstained:
            n_abstained_among_eligible += 1
            sensitivity_pairs.append((case["final_level"], 99))
            continue

        eligible_pairs.append((case["final_level"], suggestion.level))
        sensitivity_pairs.append((case["final_level"], suggestion.level))

    records = AuditLog(audit_path).read_all()
    backend_usage = Counter(r["backend"] for r in records)
    abst = metrics.abstention_metrics(should_abstain_flags, actually_abstained_flags)

    return {
        "backend_solicitado": backend,
        "backend_realmente_usado": dict(backend_usage),
        "n_eligible_cases": n_eligible,
        "cobertura": (
            (n_eligible - n_abstained_among_eligible) / n_eligible if n_eligible else float("nan")
        ),
        "S_sub_triage": metrics.sub_triage_rate(eligible_pairs),
        "sensibilidad_I_II": metrics.sensitivity_high_risk(sensitivity_pairs),
        "recall_at_k": metrics.recall_at_k(recall_hits),
        "tasa_abstencion_correcta": abst["tasa_abstencion_correcta"],
        "tasa_abstencion_indebida": abst["tasa_abstencion_indebida"],
    }


def format_markdown(det: dict, gem: dict) -> str:
    lines = [
        "# Comparación de backends: determinista vs. Gemini",
        "",
        "Generado por `experiments/compare_backends.py` sobre las mismas 34 viñetas "
        f"de `data/cases.json`, ambas con corpus `{CORPUS_FORMAT}`, para aislar el "
        "efecto del backend de generación/recuperación.",
        "",
        f"Backend Gemini realmente usado por caso: {gem['backend_realmente_usado']} "
        "(si aparece 'gemini_fallback_deterministic', esos casos cayeron al backend "
        "determinista por falta de `GEMINI_API_KEY` o un error de red — no es un fallo "
        "del experimento, es la salvaguarda de robustez de `src/pipeline.py`).",
        "",
        "| Métrica | Determinista (TF-IDF) | Gemini (embeddings + LLM) |",
        "|---|---|---|",
        f"| Casos elegibles | {det['n_eligible_cases']} | {gem['n_eligible_cases']} |",
        f"| Cobertura (no abstención) | {det['cobertura']:.2f} | {gem['cobertura']:.2f} |",
        f"| S (sub-triage ponderado) | {det['S_sub_triage']:.3f} | {gem['S_sub_triage']:.3f} |",
        f"| Sensibilidad I-II | {det['sensibilidad_I_II']:.3f} | {gem['sensibilidad_I_II']:.3f} |",
        f"| Recall@k | {det['recall_at_k']:.3f} | {gem['recall_at_k']:.3f} |",
        f"| Tasa de abstención correcta | {det['tasa_abstencion_correcta']:.3f} | "
        f"{gem['tasa_abstencion_correcta']:.3f} |",
        f"| Tasa de abstención indebida | {det['tasa_abstencion_indebida']:.3f} | "
        f"{gem['tasa_abstencion_indebida']:.3f} |",
        "",
        "Con solo 34 casos esta comparación es ilustrativa, no concluyente "
        "estadísticamente (igual que en `run_experiment.py`); su valor es mostrar "
        "que el backend Gemini es un reemplazo funcional del determinista bajo la "
        "misma interfaz y las mismas métricas, no declarar un ganador definitivo.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    cases = load_cases()

    print("Evaluando backend determinista...")
    det = evaluate_backend("deterministic", cases)
    print("Evaluando backend Gemini (esto llama a la API real, puede tardar)...")
    gem = evaluate_backend("gemini", cases)

    summary = format_markdown(det, gem)
    (RESULTS_DIR / "backend_comparison.md").write_text(summary, encoding="utf-8")
    (RESULTS_DIR / "backend_comparison.json").write_text(
        json.dumps({"deterministic": det, "gemini": gem}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(summary)


if __name__ == "__main__":
    main()
