"""Ejecutor integral y ordenado de la Parte 2."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "201_auditar_y_construir_matriz.py",
    "202_preparar_geometrias.py",
    "203_diagnosticar_estructura_espacial.py",
    "204_evaluar_clustering_espacial.py",
    "205_seleccionar_solucion_espacial.py",
    "206_construir_clusters_y_borde.py",
    "207_perfilar_clusters.py",
    "208_analizar_sobrerrepresentacion.py",
    "209_comparar_perfiles_clusters.py",
    "210_generar_figuras_y_coexistencia.py",
    "211_generar_documentos_parte2.py",
]


def main():
    for nombre in SCRIPTS:
        ruta = ROOT / "scripts" / nombre
        print(f"\n=== {nombre} ===", flush=True)
        subprocess.run([sys.executable, str(ruta)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
