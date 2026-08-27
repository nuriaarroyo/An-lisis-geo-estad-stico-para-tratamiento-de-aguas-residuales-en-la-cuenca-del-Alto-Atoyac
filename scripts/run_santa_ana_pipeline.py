from __future__ import annotations

import subprocess
import sys
from pathlib import Path


SCRIPTS_DIR = Path(__file__).resolve().parent


def run(script: str) -> None:
    subprocess.run([sys.executable, str(SCRIPTS_DIR / script)], check=True)


def main() -> None:
    print("[atoyac] Etapa 1/7: universo productivo amplio", flush=True)
    run("02_classify_independent_universe.py")
    print("[atoyac] Etapa 2/7: refinamiento y prioridades", flush=True)
    run("03_refine_and_prioritize.py")
    print("[atoyac] Etapa 3/7: auditoría de seis casos especiales", flush=True)
    run("05_apply_special_audit.py")
    print("[atoyac] Etapa 4/7: preparar revisión de maquila", flush=True)
    run("06_prepare_maquila_review.py")
    print("[atoyac] Etapa 5/7: preparar revisión de producción", flush=True)
    run("07_prepare_production_review.py")
    print("[atoyac] Etapa 6/7: comparación externa y reporte", flush=True)
    run("08_compare_and_report.py")
    print("[atoyac] Etapa 7/7: universo hídrico preliminar", flush=True)
    run("09_build_preliminary_hydric_universe.py")
    print("[atoyac] Pipeline reproducible terminado", flush=True)


if __name__ == "__main__":
    main()
