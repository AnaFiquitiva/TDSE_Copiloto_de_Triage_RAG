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

Estas dos variantes son deterministas y no requieren red ni credenciales:
siguen siendo el backend **por defecto**. Además, este módulo ofrece un
tercer backend **opcional** (`GeminiRetriever`, más abajo) que usa
*embeddings* reales de la API de Gemini en vez de TF-IDF, para quien tenga
configurada una `GEMINI_API_KEY` y quiera mayor robustez semántica a costa de
depender de una API externa (ver README.md, sección "Backend LLM opcional").
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .ingest import Chunk
from .llm_client import embed_text

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


DEFAULT_EMBEDDING_CACHE_PATH = (
    Path(__file__).resolve().parent.parent / "data" / ".gemini_embedding_cache.json"
)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a)) or 1.0
    norm_b = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (norm_a * norm_b)


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


class GeminiRetriever:
    """Recuperación con *embeddings* reales de la API de Gemini
    (`gemini-embedding-001`), en vez de TF-IDF. Backend opcional: requiere
    `GEMINI_API_KEY` (ver README.md, sección "Backend LLM opcional").

    Los embeddings de los fragmentos del corpus se cachean en disco
    (`cache_path`, por defecto `data/.gemini_embedding_cache.json`, excluido
    de git) para no volver a llamar a la API por cada corrida: la key de
    caché es un hash del texto exacto del fragmento, así que un cambio en el
    corpus invalida automáticamente solo las entradas afectadas.

    Implementa la misma interfaz que `Retriever` (`.retrieve(query, k)`) para
    que `MinimalGenerator`/`LLMBackedGenerator` puedan usar cualquiera de los
    dos sin distinción.
    """

    def __init__(
        self,
        chunks: list[Chunk],
        cache_path: Path = DEFAULT_EMBEDDING_CACHE_PATH,
        embed_fn=embed_text,
    ):
        self.chunks = chunks
        self.cache_path = cache_path
        self._embed_fn = embed_fn
        self._cache = self._load_cache()
        self._doc_vectors = [self._embed_cached(c.text) for c in chunks]

    def _load_cache(self) -> dict[str, list[float]]:
        if self.cache_path.exists():
            return json.loads(self.cache_path.read_text(encoding="utf-8"))
        return {}

    def _save_cache(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self._cache), encoding="utf-8")

    def _embed_cached(self, text: str) -> list[float]:
        key = _text_hash(text)
        if key not in self._cache:
            self._cache[key] = self._embed_fn(text)
            self._save_cache()
        return self._cache[key]

    def retrieve(self, query: str, k: int = 5) -> list[RankedChunk]:
        query_vec = self._embed_fn(query)
        scored = [
            RankedChunk(chunk=chunk, score=_cosine_similarity(query_vec, doc_vec))
            for chunk, doc_vec in zip(self.chunks, self._doc_vectors)
        ]
        scored.sort(key=lambda rc: rc.score, reverse=True)
        return scored[:k]
