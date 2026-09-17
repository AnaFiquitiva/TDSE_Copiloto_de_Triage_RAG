"""Recuperación sobre el corpus normativo.

Implementa dos variantes del Factor B del diseño 2x2 (Sección 5 del documento
del proyecto):

- ``generic``: vectorización TF-IDF simple, sin ningún ajuste al dominio
  clínico en español. Sirve de proxy determinista y reproducible de un modelo
  de *embeddings* multilingüe genérico.
- ``clinical_es``: la misma vectorización TF-IDF, mediante un léxico de
  normalización que mapea expresiones coloquiales del relato del paciente a
  su término clínico equivalente antes de vectorizar (p. ej. "me falta el
  aire" -> "dificultad_respiratoria"). Sirve de proxy determinista de un
  modelo de *embeddings* clínico en español (p. ej. Carrino et al., 2022).

Este proyecto no descarga modelos de *embeddings* reales porque el entorno de
ejecución no tiene garantizado acceso a internet ni a pesos preentrenados; la
sustitución de estas dos funciones por un modelo real (p. ej. vía
``sentence-transformers``) es la ruta natural de evolución señalada en el
propio documento del proyecto (Sección 6, Fase 3) y no cambia el resto del
pipeline ni la interfaz de ``Retriever``.
"""
from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass

from .ingest import Chunk

# Léxico de normalización coloquial -> clínico usado únicamente por la
# variante ``clinical_es``. Las claves están ya normalizadas (minúsculas,
# sin tildes) para que el emparejamiento sea robusto frente a variaciones
# ortográficas del relato libre.
_CLINICAL_LEXICON: dict[str, str] = {
    "dolor en el pecho": "dolor toracico",
    "dolor de pecho": "dolor toracico",
    "me duele el pecho": "dolor toracico",
    "me falta el aire": "dificultad respiratoria",
    "no puedo respirar bien": "dificultad respiratoria",
    "cuesta respirar": "dificultad respiratoria",
    "se esta ahogando": "dificultad respiratoria",
    "se desmayo": "alteracion del estado de conciencia",
    "perdio el conocimiento": "alteracion del estado de conciencia",
    "no reacciona": "alteracion del estado de conciencia",
    "esta muy confundido": "alteracion del estado de conciencia",
    "sangra mucho": "hemorragia",
    "no para de sangrar": "hemorragia",
    "esta sangrando bastante": "hemorragia",
    "tiene mucha fiebre": "fiebre alta",
    "esta muy caliente": "fiebre alta",
    "quiere hacerse dano": "ideacion suicida",
    "quiere quitarse la vida": "ideacion suicida",
    "piensa en suicidarse": "ideacion suicida",
    "se golpeo la cabeza": "trauma craneoencefalico",
    "se pego en la cabeza": "trauma craneoencefalico",
    "le dieron temblores fuertes": "convulsion",
    "empezo a convulsionar": "convulsion",
    "vomito en chorro": "vomito en proyectil",
}


def _strip_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def _normalize_lexicon(text: str) -> str:
    """Reemplaza expresiones coloquiales por su equivalente clínico."""
    normalized = _strip_accents(text.lower())
    for phrase, canonical in _CLINICAL_LEXICON.items():
        normalized = normalized.replace(phrase, canonical)
    return normalized


_TOKEN_RE = re.compile(r"[a-z_]+")


def tokenize(text: str, embedding_mode: str) -> list[str]:
    if embedding_mode == "clinical_es":
        text = _normalize_lexicon(text)
    else:
        text = _strip_accents(text.lower())
    return _TOKEN_RE.findall(text)


@dataclass
class RankedChunk:
    chunk: Chunk
    score: float


class Retriever:
    """Índice TF-IDF minimalista, sin dependencias externas."""

    def __init__(self, chunks: list[Chunk], embedding_mode: str = "generic"):
        if embedding_mode not in {"generic", "clinical_es"}:
            raise ValueError("embedding_mode debe ser 'generic' o 'clinical_es'")
        self.chunks = chunks
        self.embedding_mode = embedding_mode
        self._doc_tokens = [tokenize(c.text, embedding_mode) for c in chunks]
        self._df = self._document_frequencies(self._doc_tokens)
        self._n_docs = len(chunks)
        self._doc_vectors = [
            self._tfidf_vector(tokens) for tokens in self._doc_tokens
        ]

    @staticmethod
    def _document_frequencies(doc_tokens: list[list[str]]) -> Counter:
        df: Counter = Counter()
        for tokens in doc_tokens:
            for term in set(tokens):
                df[term] += 1
        return df

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        # +1 en numerador y denominador (suavizado) para evitar división por
        # cero y para no descartar términos que solo aparecen en la consulta.
        return math.log((1 + self._n_docs) / (1 + df)) + 1.0

    def _tfidf_vector(self, tokens: list[str]) -> Counter:
        tf = Counter(tokens)
        vec: Counter = Counter()
        for term, count in tf.items():
            vec[term] = count * self._idf(term)
        norm = math.sqrt(sum(v * v for v in vec.values())) or 1.0
        return Counter({k: v / norm for k, v in vec.items()})

    @staticmethod
    def _cosine(a: Counter, b: Counter) -> float:
        common = set(a) & set(b)
        return sum(a[t] * b[t] for t in common)

    def retrieve(self, query: str, k: int = 3) -> list[RankedChunk]:
        query_tokens = tokenize(query, self.embedding_mode)
        query_vec = self._tfidf_vector(query_tokens)
        scored = [
            RankedChunk(chunk=chunk, score=self._cosine(query_vec, doc_vec))
            for chunk, doc_vec in zip(self.chunks, self._doc_vectors)
        ]
        scored.sort(key=lambda rc: rc.score, reverse=True)
        return scored[:k]
