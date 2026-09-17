"""Demostracion rapida por linea de comandos del copiloto (componentes 2 y 3
version minima), pensada para inspeccionar una sola sugerencia con su
evidencia recuperada y su cita, tal como la veria el personal de salud en la
interfaz minima de revision descrita en el documento del proyecto.

Uso:
    python demo.py "el paciente tiene dolor en el pecho y sudoracion fria"
    python demo.py "el paciente tiene dolor en el pecho" --corpus raw --embeddings generic
"""
from __future__ import annotations

import argparse
import sys

from src.baseline import RuleBasedBaseline
from src.pipeline import CopilotoPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texto", help="Relato libre del paciente, en espanol.")
    parser.add_argument(
        "--corpus", choices=["raw", "reformatted"], default="reformatted",
        help="Version del corpus normativo a usar (por defecto: reformatted).",
    )
    parser.add_argument(
        "--embeddings", choices=["generic", "clinical_es"], default="clinical_es",
        help="Modo de vectorizacion (por defecto: clinical_es).",
    )
    args = parser.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

    pipeline = CopilotoPipeline(corpus_format=args.corpus, embedding_mode=args.embeddings)
    suggestion = pipeline.run_case("demo", args.texto)

    baseline = RuleBasedBaseline().classify(args.texto)

    print(f"Relato: {args.texto}")
    print(f"Corpus={args.corpus} | Embeddings={args.embeddings}")
    print("-" * 60)
    if suggestion.abstained:
        print(f"Copiloto: SE ABSTIENE (razon: {suggestion.reason})")
    else:
        print(f"Copiloto: Nivel {suggestion.level} | Cita: {suggestion.citation} "
              f"| Confianza: {suggestion.confidence:.2f}")
    print("Fragmentos recuperados:")
    for rc in suggestion.retrieved:
        print(f"  - {rc.chunk.chunk_id} (score={rc.score:.3f}): {rc.chunk.text[:90]!r}")
    print("-" * 60)
    print(f"Linea base (reglas): Nivel {baseline.level} | Cita: {baseline.citation} "
          f"| Palabra clave: {baseline.matched_keyword}")
    print()
    print("Recordatorio: esta sugerencia asiste, no decide. La clasificacion final "
          "es responsabilidad del personal de salud (ver README.md).")


if __name__ == "__main__":
    main()
