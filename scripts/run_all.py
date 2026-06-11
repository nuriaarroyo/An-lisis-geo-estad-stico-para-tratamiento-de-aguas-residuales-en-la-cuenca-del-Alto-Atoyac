from __future__ import annotations

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "00_inventory_raw_data.py",
    "01_prepare_geodata.py",
    "02_filter_denue_textil.py",
    "03_process_saic.py",
    "04_spatial_analysis.py",
    "02b_clasificacion_productiva_denue.py",
    "05_make_maps.py",
    "05b_make_productive_classification_maps.py",
    "06_make_interactive_maps.py",
    "06b_make_plotly_productive_maps.py",
    "07_apply_denue_audit.py",
    "08_make_audited_maps.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\n=== Ejecutando {script} ===", flush=True)
        subprocess.run([sys.executable, str(PROJECT_ROOT / "scripts" / script)], cwd=PROJECT_ROOT, check=True)
    print("\nFlujo completo terminado.", flush=True)


if __name__ == "__main__":
    main()
