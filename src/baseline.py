"""Línea base C0: árbol de decisión por palabras clave, sin recuperación ni
modelo de lenguaje (ver Sección 5 del documento del proyecto).

Las reglas se cargan desde ``data/keyword_rules.json``, que se trata como un
artefacto congelado antes de ejecutar la evaluación sobre las celdas E1-E4,
precisamente para evitar el riesgo de ajustar la línea base a posteriori en
función de los resultados observados.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from .retrieval import _strip_accents

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "keyword_rules.json"


@dataclass
class BaselineResult:
    level: int
    citation: str
    matched_keyword: str | None


class RuleBasedBaseline:
    def __init__(self, rules_path: Path = RULES_PATH):
        with open(rules_path, encoding="utf-8") as f:
            config = json.load(f)
        self.priority_order: list[int] = config["priority_order"]
        self.rules: dict[int, dict] = {
            int(level): rule for level, rule in config["rules"].items()
        }
        self.default_level: int = config["default"]["level"]
        self.default_citation: str = config["default"]["citation"]

    def classify(self, patient_text: str) -> BaselineResult:
        normalized = _strip_accents(patient_text.lower())
        for level in self.priority_order:
            rule = self.rules[level]
            for keyword in rule["keywords"]:
                if _strip_accents(keyword) in normalized:
                    return BaselineResult(
                        level=level, citation=rule["citation"], matched_keyword=keyword
                    )
        return BaselineResult(
            level=self.default_level,
            citation=self.default_citation,
            matched_keyword=None,
        )
