"""Compila reporte, presentación y atlas de Parte 2 con latexmk."""

from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOCUMENTOS = [
    (ROOT / "docs/parte_2/reporte", "reporte_tecnico_parte_2.tex"),
    (ROOT / "docs/parte_2/presentacion", "presentacion_parte_2.tex"),
    (ROOT / "docs/parte_2/atlas", "atlas_clusters.tex"),
]


def main():
    for carpeta, nombre in DOCUMENTOS:
        print(f"Compilando {nombre}...", flush=True)
        subprocess.run(
            ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error", nombre],
            cwd=carpeta, check=True,
        )


if __name__ == "__main__":
    main()
