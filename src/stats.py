"""Utilidades estadísticas de propósito general (no específicas del dominio de
triage), usadas para analizar el dataset externo real en
``experiments/analyze_external_data.py``. Se implementan desde la biblioteca
estándar (sin `scipy`) para mantener el prototipo completo libre de
dependencias externas.
"""
from __future__ import annotations

import math


def _regularized_gamma_lower_series(a: float, x: float) -> float:
    """P(a, x) mediante serie de potencias (válido para x < a + 1)."""
    if x <= 0:
        return 0.0
    gln = math.lgamma(a)
    ap = a
    total = 1.0 / a
    delta = total
    for _ in range(500):
        ap += 1
        delta *= x / ap
        total += delta
        if abs(delta) < abs(total) * 1e-14:
            break
    return total * math.exp(-x + a * math.log(x) - gln)


def _regularized_gamma_upper_cf(a: float, x: float) -> float:
    """Q(a, x) mediante fracción continua de Lentz (válido para x >= a + 1)."""
    gln = math.lgamma(a)
    tiny = 1e-300
    b = x + 1 - a
    c = 1 / tiny
    d = 1 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_sf(x: float, df: int) -> float:
    """Función de supervivencia (valor p) de la distribución chi-cuadrado con
    ``df`` grados de libertad, evaluada en ``x``. Implementación estándar
    (Numerical Recipes) vía la función gamma incompleta regularizada, para no
    depender de `scipy.stats.chi2`.
    """
    if x <= 0:
        return 1.0
    a = df / 2.0
    xx = x / 2.0
    if xx < a + 1:
        return 1.0 - _regularized_gamma_lower_series(a, xx)
    return _regularized_gamma_upper_cf(a, xx)


def build_contingency_table(
    rows: list[dict], row_key: str, col_key: str
) -> tuple[list[str], list[str], list[list[int]]]:
    """Construye una tabla de contingencia (conteos) a partir de una lista de
    registros, agrupando por ``row_key`` (filas) y ``col_key`` (columnas).
    Devuelve las etiquetas de fila, las de columna, y la matriz de conteos.
    """
    row_labels = sorted({r[row_key] for r in rows})
    col_labels = sorted({r[col_key] for r in rows})
    row_idx = {label: i for i, label in enumerate(row_labels)}
    col_idx = {label: i for i, label in enumerate(col_labels)}

    table = [[0] * len(col_labels) for _ in row_labels]
    for r in rows:
        table[row_idx[r[row_key]]][col_idx[r[col_key]]] += 1
    return row_labels, col_labels, table


def chi_square_independence_test(table: list[list[int]]) -> dict:
    """Prueba de independencia chi-cuadrado sobre una tabla de contingencia.

    Devuelve el estadístico, los grados de libertad y el valor p. Se usa para
    responder si la distribución de niveles de triage difiere de forma
    estadísticamente significativa entre grupos (p. ej. entre redes de IPS).
    """
    n_rows = len(table)
    n_cols = len(table[0]) if table else 0
    total = sum(sum(row) for row in table)
    if total == 0 or n_rows < 2 or n_cols < 2:
        return {"chi2": 0.0, "df": 0, "p_value": float("nan")}

    row_totals = [sum(row) for row in table]
    col_totals = [sum(table[r][c] for r in range(n_rows)) for c in range(n_cols)]

    chi2 = 0.0
    for r in range(n_rows):
        for c in range(n_cols):
            expected = row_totals[r] * col_totals[c] / total
            if expected > 0:
                chi2 += (table[r][c] - expected) ** 2 / expected

    df = (n_rows - 1) * (n_cols - 1)
    p_value = chi2_sf(chi2, df)
    return {"chi2": chi2, "df": df, "p_value": p_value}
