"""Ejecutor final reproducible de toda la Parte 2, desde fuentes hasta PDFs."""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PASOS = [
    "201_auditar_y_construir_matriz.py", "202_preparar_geometrias.py",
    "203_diagnosticar_estructura_espacial.py", "204_evaluar_clustering_espacial.py",
    "205_seleccionar_solucion_espacial.py", "206_construir_clusters_y_borde.py",
    "207_perfilar_clusters.py", "208_analizar_sobrerrepresentacion.py",
    "209_comparar_perfiles_clusters.py", "210_generar_figuras_y_coexistencia.py",
    "211_generar_documentos_parte2.py", "213_auditar_y_diagnosticar_cierre.py",
    "214_cerrar_analisis_composicion.py", "215_generar_figuras_finales_y_atlas.py",
    "216_generar_latex_parte2.py", "217_compilar_documentos_parte2.py",
    "218_validar_cierre_parte2.py",
]


def main():
    for nombre in PASOS:
        print(f"\n=== {nombre} ===", flush=True)
        subprocess.run([sys.executable, str(ROOT / "scripts" / nombre)], cwd=ROOT, check=True)


if __name__ == "__main__":
    main()
