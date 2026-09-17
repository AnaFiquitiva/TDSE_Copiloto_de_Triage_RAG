"""Analiza el conjunto de datos externo real `data/external_triage_urgencias_colombia.csv`
(Datos Abiertos Colombia, dataset "Clasificación en Triage Urgencias", id `vt5n-eu2r`,
https://www.datos.gov.co/Salud-y-Protecci-n-Social/Clasificaci-n-en-Triage-Urgencias/vt5n-eu2r).

Este conjunto es administrativo y operativo (~89.000 registros de una red de IPS
reportante), NO contiene el relato libre del paciente: trae únicamente el nivel de
triage asignado (I-V) y las marcas de tiempo de ingreso y atención. Por eso NO se usa
para entrenar ni evaluar el clasificador de texto del copiloto (eso sigue siendo
tarea de `data/cases.json`); se usa para dos cosas que sí puede responder sin
depender de una alianza con una IPS ni de datos de campo (ver Sección 3 del
documento del proyecto):

1. Contrastar, con datos reales, la prevalencia natural de cada nivel de triage
   (justifica empíricamente la decisión de sobremuestrear los niveles I-II en el
   gold standard sintético: en la práctica son un porcentaje muy pequeño de los
   casos).
2. Estimar, de forma secundaria e ilustrativa, el tiempo real transcurrido entre
   el ingreso y la atención por nivel, como referencia frente al ejercicio
   numérico hipotético de la Sección de business case del documento (sin que esto
   sustituya el instrumento de observación de tiempos in situ que el documento
   deja pendiente para una fase posterior).

Uso:
    python -m experiments.analyze_external_data
"""
from __future__ import annotations

import csv
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.stats import build_contingency_table, chi_square_independence_test  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass

DATA_PATH = ROOT / "data" / "external_triage_urgencias_colombia.csv"
RESULTS_PATH = ROOT / "results" / "external_data_summary.md"
LEVEL_ORDER = ["I", "II", "III", "IV", "V"]
MAX_PLAUSIBLE_MINUTES = 24 * 60  # descarta registros con mas de 24h como error de captura


def load_rows() -> list[dict]:
    with open(DATA_PATH, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def level_distribution(rows: list[dict]) -> Counter:
    return Counter(row["triage"] for row in rows)


def time_to_attention_minutes(rows: list[dict]) -> dict[str, list[float]]:
    durations: dict[str, list[float]] = defaultdict(list)
    for row in rows:
        try:
            ingreso = datetime.fromisoformat(row["fecha_ing"])
            atencion = datetime.fromisoformat(row["fecha_atencion"])
        except (KeyError, ValueError):
            continue
        delta_min = (atencion - ingreso).total_seconds() / 60.0
        if delta_min < 0 or delta_min > MAX_PLAUSIBLE_MINUTES:
            continue
        durations[row["triage"]].append(delta_min)
    return durations


def distribution_by_group(rows: list[dict], group_key: str) -> dict[str, Counter]:
    by_group: dict[str, Counter] = defaultdict(Counter)
    for row in rows:
        by_group[row[group_key]][row["triage"]] += 1
    return by_group


def independence_test_by_group(rows: list[dict], group_key: str) -> dict:
    """¿La distribución de niveles de triage difiere significativamente entre
    los grupos de ``group_key`` (p. ej. entre redes de IPS)? Prueba
    chi-cuadrado de independencia sobre la tabla de contingencia
    (grupo x nivel)."""
    row_labels, col_labels, table = build_contingency_table(rows, group_key, "triage")
    result = chi_square_independence_test(table)
    result["row_labels"] = row_labels
    result["col_labels"] = col_labels
    result["table"] = table
    return result


def format_markdown(rows: list[dict], distribution: Counter, durations: dict[str, list[float]]) -> str:
    total = sum(distribution.values())
    lines = [
        "# Análisis del conjunto de datos externo real (Datos Abiertos Colombia)",
        "",
        "Fuente: [Clasificación en Triage Urgencias](https://www.datos.gov.co/Salud-y-Protecci-n-Social/"
        "Clasificaci-n-en-Triage-Urgencias/vt5n-eu2r), Datos Abiertos Colombia "
        "(dataset id `vt5n-eu2r`), descargado el 2026-09-17 vía la API Socrata "
        "(`https://www.datos.gov.co/resource/vt5n-eu2r.csv`).",
        "",
        f"Registros totales: {total}. **Este conjunto no contiene el relato libre del "
        "paciente**, solo nivel de triage y marcas de tiempo administrativas; no se usa "
        "para entrenar ni evaluar el copiloto (ver `experiments/analyze_external_data.py`).",
        "",
        "## Distribución real de niveles de triage",
        "",
        "| Nivel | N | % |",
        "|---|---|---|",
    ]
    for level in LEVEL_ORDER:
        n = distribution.get(level, 0)
        pct = 100 * n / total if total else 0.0
        lines.append(f"| {level} | {n} | {pct:.2f}% |")

    lines += [
        "",
        "Esta distribución respalda empíricamente la decisión metodológica del documento "
        "del proyecto de sobremuestrear los niveles I-II en el conjunto de prueba sintético "
        "(Sección 5): en datos operativos reales, los niveles I-II representan apenas "
        f"{100*(distribution.get('I',0)+distribution.get('II',0))/total:.1f}% de los casos, "
        "insuficiente para medir con precisión el desempeño donde el costo de un error es mayor.",
        "",
        "## Tiempo de ingreso a atención, por nivel (minutos)",
        "",
        "Se descartan registros con duración negativa o mayor a 24 horas (errores de "
        "captura administrativa). Esto es un dato agregado de una red de IPS reportante, "
        "no una medición prospectiva in situ como la que describe el documento del "
        "proyecto (Sección 3); se reporta aquí únicamente como referencia secundaria.",
        "",
        "| Nivel | N válidos | Mediana (min) | Media (min) |",
        "|---|---|---|---|",
    ]
    for level in LEVEL_ORDER:
        d = durations.get(level, [])
        if not d:
            continue
        lines.append(
            f"| {level} | {len(d)} | {statistics.median(d):.1f} | {statistics.mean(d):.1f} |"
        )

    by_red = distribution_by_group(rows, "red")
    red_test = independence_test_by_group(rows, "red")
    lines += [
        "",
        "## Distribución de niveles por red de IPS",
        "",
        "| Red | N | " + " | ".join(LEVEL_ORDER) + " |",
        "|---|---|" + "---|" * len(LEVEL_ORDER),
    ]
    for red in sorted(by_red):
        counts = by_red[red]
        n_red = sum(counts.values())
        pcts = " | ".join(f"{100*counts.get(lvl,0)/n_red:.1f}%" for lvl in LEVEL_ORDER)
        lines.append(f"| {red} | {n_red} | {pcts} |")

    lines += [
        "",
        f"**Prueba de independencia chi-cuadrado** (¿la distribución de niveles "
        f"depende de la red?): χ² = {red_test['chi2']:.2f}, "
        f"df = {red_test['df']}, p = {red_test['p_value']:.2e}. "
        + (
            "La diferencia entre redes es estadísticamente significativa (p < 0.01); "
            "esto sugiere que la práctica de clasificación (o la población atendida) "
            "no es homogénea entre redes, lo cual es relevante si en una fase futura "
            "se usara este dataset para calibrar el prototipo por región."
            if red_test["p_value"] < 0.01
            else "No hay evidencia suficiente de que la distribución de niveles "
            "difiera entre redes."
        ),
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    if not DATA_PATH.exists():
        raise SystemExit(
            f"No se encontró {DATA_PATH}. Ver README.md, sección 'Fuentes de datos reales', "
            "para el enlace de descarga."
        )
    rows = load_rows()
    distribution = level_distribution(rows)
    durations = time_to_attention_minutes(rows)

    summary = format_markdown(rows, distribution, durations)
    RESULTS_PATH.parent.mkdir(exist_ok=True)
    RESULTS_PATH.write_text(summary, encoding="utf-8")
    print(summary)


if __name__ == "__main__":
    main()
