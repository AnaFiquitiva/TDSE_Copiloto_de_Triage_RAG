"""Métricas formales definidas en la Sección 5 del documento del proyecto.

Todas las funciones son deterministas y no dependen de librerías externas de
ciencia de datos, para que la evaluación sea reproducible con solo la
biblioteca estándar de Python.
"""
from __future__ import annotations

from collections import Counter


def sub_triage_rate(pairs: list[tuple[int, int]]) -> float:
    """Calcula S: tasa de sub-triage ponderada por distancia (Sección 5).

    ``pairs`` es una lista de tuplas ``(nivel_referencia, nivel_sugerido)``.
    Solo cuenta como sub-triage cuando el nivel sugerido es MENOS urgente
    (número mayor) que el de referencia.
    """
    if not pairs:
        return 0.0
    total = sum(max(0, sug - ref) for ref, sug in pairs)
    return total / len(pairs)


def sub_triage_by_level(pairs_with_ref_level: list[tuple[int, int]]) -> dict[int, float]:
    """Desglosa S por cada nivel de referencia (I-V)."""
    by_level: dict[int, list[tuple[int, int]]] = {}
    for ref, sug in pairs_with_ref_level:
        by_level.setdefault(ref, []).append((ref, sug))
    return {level: sub_triage_rate(p) for level, p in sorted(by_level.items())}


def sensitivity_high_risk(pairs: list[tuple[int, int]], high_risk_levels=(1, 2)) -> float:
    """Sensibilidad en los niveles de mayor riesgo (I-II): de los casos cuyo
    nivel de referencia es I o II, qué fracción fue sugerida también como I o
    II (es decir, no fue subestimada fuera del rango de alto riesgo)."""
    relevant = [(ref, sug) for ref, sug in pairs if ref in high_risk_levels]
    if not relevant:
        return float("nan")
    correct = sum(1 for ref, sug in relevant if sug in high_risk_levels)
    return correct / len(relevant)


def weighted_kappa(pairs: list[tuple[int, int]], levels=(1, 2, 3, 4, 5)) -> float:
    """Kappa de Cohen ponderado cuadráticamente para escalas ordinales.

    ``pairs`` es una lista de tuplas ``(nivel_evaluador_1, nivel_evaluador_2)``.
    """
    n = len(pairs)
    if n == 0:
        return float("nan")

    levels = list(levels)
    idx = {lvl: i for i, lvl in enumerate(levels)}
    k = len(levels)

    observed = [[0] * k for _ in range(k)]
    for a, b in pairs:
        observed[idx[a]][idx[b]] += 1

    row_totals = [sum(row) for row in observed]
    col_totals = [sum(observed[r][c] for r in range(k)) for c in range(k)]

    weights = [[(i - j) ** 2 for j in range(k)] for i in range(k)]

    observed_sum = sum(
        weights[i][j] * observed[i][j] for i in range(k) for j in range(k)
    )
    expected_sum = sum(
        weights[i][j] * (row_totals[i] * col_totals[j] / n)
        for i in range(k)
        for j in range(k)
    )

    if expected_sum == 0:
        return 1.0
    return 1 - (observed_sum / expected_sum)


def recall_at_k(hits: list[bool]) -> float:
    """Fracción de casos en los que el fragmento normativo correcto apareció
    entre los top-k recuperados. ``hits`` ya trae, por caso, si hubo acierto."""
    if not hits:
        return float("nan")
    return sum(hits) / len(hits)


def abstention_metrics(
    should_abstain_flags: list[bool], actually_abstained_flags: list[bool]
) -> dict[str, float]:
    """H4: tasa de abstención correcta y tasa de abstención indebida.

    - ``tasa_abstencion_correcta``: de los casos que deberían llevar a
      abstención (evidencia insuficiente), qué fracción el sistema realmente
      se abstuvo.
    - ``tasa_abstencion_indebida``: de los casos con evidencia suficiente,
      qué fracción el sistema se abstuvo de todas formas (costo de
      seguridad excesivo).
    """
    should = [
        actual
        for should_flag, actual in zip(should_abstain_flags, actually_abstained_flags)
        if should_flag
    ]
    should_not = [
        actual
        for should_flag, actual in zip(should_abstain_flags, actually_abstained_flags)
        if not should_flag
    ]
    return {
        "tasa_abstencion_correcta": (sum(should) / len(should)) if should else float("nan"),
        "tasa_abstencion_indebida": (sum(should_not) / len(should_not)) if should_not else float("nan"),
    }


def citation_faithfulness(citation_matches: list[bool]) -> float:
    """Fidelidad de citación (Sección 3.4, criterio de RAGAS adaptado):
    fracción de sugerencias (no abstenidas) cuya cita efectivamente
    corresponde al nivel sugerido según el corpus."""
    if not citation_matches:
        return float("nan")
    return sum(citation_matches) / len(citation_matches)


def confusion_counts(pairs: list[tuple[int, int]]) -> Counter:
    """Matriz de confusión (referencia, sugerido) como conteos, útil para
    inspección manual en el reporte de resultados."""
    return Counter(pairs)
