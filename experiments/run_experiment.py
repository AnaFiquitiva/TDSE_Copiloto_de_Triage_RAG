"""Ejecuta el diseño experimental 2x2 (E1-E4) más la línea base C0 descrito
en la Sección 5 del documento del proyecto, sobre el conjunto de viñetas
de ``data/cases.json``, y escribe los resultados en ``results/``.

Uso:
    python -m experiments.run_experiment
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

from src import metrics  # noqa: E402
from src.baseline import RuleBasedBaseline  # noqa: E402
from src.ingest import canonical_citation  # noqa: E402
from src.pipeline import CopilotoPipeline  # noqa: E402

CASES_PATH = ROOT / "data" / "cases.json"
RESULTS_DIR = ROOT / "results"

CELLS = [
    ("E1", "raw", "generic"),
    ("E2", "reformatted", "generic"),
    ("E3", "raw", "clinical_es"),
    ("E4", "reformatted", "clinical_es"),
]


def load_cases() -> list[dict]:
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    return data["cases"]


def intra_team_kappa(cases: list[dict]) -> dict:
    pairs = [
        (c["evaluator1"]["level"], c["evaluator2"]["level"])
        for c in cases
        if c["evaluator1"]["level"] is not None and c["evaluator2"]["level"] is not None
    ]
    return {
        "n_pares": len(pairs),
        "kappa_ponderado_cuadratico": metrics.weighted_kappa(pairs),
    }


def run_cell(cell_name: str, corpus_format: str, embedding_mode: str, cases: list[dict]) -> dict:
    audit_path = RESULTS_DIR / f"audit_{cell_name}.jsonl"
    if audit_path.exists():
        audit_path.unlink()
    pipeline = CopilotoPipeline(corpus_format, embedding_mode, k=5, audit_path=audit_path)

    eligible_pairs: list[tuple[int, int]] = []
    sensitivity_pairs: list[tuple[int, int]] = []
    recall_hits: list[bool] = []
    citation_matches: list[bool] = []
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

        final_level = case["final_level"]
        n_eligible += 1

        hit = any(
            canonical_citation(rc.chunk.chunk_id) == case["final_citation"]
            for rc in suggestion.retrieved
        )
        recall_hits.append(hit)

        if suggestion.abstained:
            n_abstained_among_eligible += 1
            sensitivity_pairs.append((final_level, 99))  # 99 = fuera de I-II por construccion
            continue

        eligible_pairs.append((final_level, suggestion.level))
        sensitivity_pairs.append((final_level, suggestion.level))
        citation_matches.append(
            canonical_citation(suggestion.citation) == case["final_citation"]
        )

    abst = metrics.abstention_metrics(should_abstain_flags, actually_abstained_flags)

    return {
        "cell": cell_name,
        "corpus_format": corpus_format,
        "embedding_mode": embedding_mode,
        "n_eligible_cases": n_eligible,
        "n_abstained_among_eligible": n_abstained_among_eligible,
        "cobertura": (
            (n_eligible - n_abstained_among_eligible) / n_eligible if n_eligible else float("nan")
        ),
        "S_sub_triage": metrics.sub_triage_rate(eligible_pairs),
        "S_por_nivel": metrics.sub_triage_by_level(eligible_pairs),
        "sensibilidad_I_II": metrics.sensitivity_high_risk(sensitivity_pairs),
        "recall_at_k": metrics.recall_at_k(recall_hits),
        "fidelidad_citacion": metrics.citation_faithfulness(citation_matches),
        "tasa_abstencion_correcta": abst["tasa_abstencion_correcta"],
        "tasa_abstencion_indebida": abst["tasa_abstencion_indebida"],
    }


def run_baseline(cases: list[dict]) -> dict:
    baseline = RuleBasedBaseline()
    eligible_pairs: list[tuple[int, int]] = []
    citation_matches: list[bool] = []
    n_eligible = 0

    for case in cases:
        if case["should_abstain"] or case["ambiguous"] or case["final_level"] is None:
            continue
        n_eligible += 1
        result = baseline.classify(case["text"])
        eligible_pairs.append((case["final_level"], result.level))
        citation_matches.append(result.citation == case["final_citation"])

    return {
        "cell": "C0",
        "descripcion": "Linea base de reglas (arbol de decision congelado, sin RAG)",
        "n_eligible_cases": n_eligible,
        "S_sub_triage": metrics.sub_triage_rate(eligible_pairs),
        "S_por_nivel": metrics.sub_triage_by_level(eligible_pairs),
        "sensibilidad_I_II": metrics.sensitivity_high_risk(eligible_pairs),
        "fidelidad_citacion": metrics.citation_faithfulness(citation_matches),
    }


def format_markdown(kappa: dict, baseline: dict, cells: list[dict], n_total_cases: int) -> str:
    lines = [
        "# Resultados del diseño experimental 2x2 + línea base (C0)",
        "",
        "Generado automáticamente por `experiments/run_experiment.py`. Estas cifras son "
        f"el resultado de ejecutar el pipeline sobre las {n_total_cases} viñetas sintéticas "
        "de `data/cases.json` (versión reducida e ilustrativa del protocolo de 60-100 casos "
        "descrito en el documento del proyecto); no constituyen una validación clínica "
        "externa (ver `README.md`, sección de limitaciones).",
        "",
        "## Acuerdo intra-equipo (gold standard)",
        "",
        f"- Pares evaluados: {kappa['n_pares']}",
        f"- Kappa ponderado cuadrático (κ_w): {kappa['kappa_ponderado_cuadratico']:.3f}",
        "",
        "## Línea base C0 (árbol de reglas, sin RAG)",
        "",
        f"- Casos elegibles: {baseline['n_eligible_cases']}",
        f"- S (sub-triage ponderado): {baseline['S_sub_triage']:.3f}",
        f"- Sensibilidad niveles I-II: {baseline['sensibilidad_I_II']:.3f}",
        f"- Fidelidad de citación: {baseline['fidelidad_citacion']:.3f}",
        f"- S por nivel de referencia: {baseline['S_por_nivel']}",
        "",
        "## Celdas del diseño 2x2 (copiloto: recuperación + generación mínima)",
        "",
        "| Celda | Corpus | Embeddings | N elegibles | Cobertura | S | Sensib. I-II | "
        "Recall@k | Fidelidad citación | Abst. correcta | Abst. indebida |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for cell in cells:
        lines.append(
            "| {cell} | {corpus_format} | {embedding_mode} | {n} | {cov:.2f} | {s:.3f} | "
            "{sens:.3f} | {rec:.3f} | {fid:.3f} | {ac:.3f} | {ai:.3f} |".format(
                cell=cell["cell"],
                corpus_format=cell["corpus_format"],
                embedding_mode=cell["embedding_mode"],
                n=cell["n_eligible_cases"],
                cov=cell["cobertura"],
                s=cell["S_sub_triage"],
                sens=cell["sensibilidad_I_II"],
                rec=cell["recall_at_k"],
                fid=cell["fidelidad_citacion"],
                ac=cell["tasa_abstencion_correcta"],
                ai=cell["tasa_abstencion_indebida"],
            )
        )
    lines.append("")
    lines.append("### S desglosado por nivel de referencia, por celda")
    lines.append("")
    for cell in cells:
        lines.append(f"- **{cell['cell']}**: {cell['S_por_nivel']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    RESULTS_DIR.mkdir(exist_ok=True)
    cases = load_cases()

    kappa = intra_team_kappa(cases)
    baseline = run_baseline(cases)
    cells = [run_cell(name, fmt, mode, cases) for name, fmt, mode in CELLS]

    output = {"kappa_intra_equipo": kappa, "baseline_C0": baseline, "celdas": cells}
    (RESULTS_DIR / "raw_results.json").write_text(
        json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    summary_md = format_markdown(kappa, baseline, cells, n_total_cases=len(cases))
    (RESULTS_DIR / "summary.md").write_text(summary_md, encoding="utf-8")

    print(summary_md)


if __name__ == "__main__":
    main()
