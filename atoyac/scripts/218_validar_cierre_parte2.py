"""Valida integridad, documentos y exclusión del alcance hidrológico."""

from importlib import import_module
from pathlib import Path

import pandas as pd

comun = import_module("200_parte2_comun")


def main():
    maestra = comun.cargar_maestra()
    escenarios = comun.leer_membresias()
    solucion = pd.read_csv(comun.OUT / "06_clusters/membresia_solucion_principal.csv", dtype={"d_llave": str})
    perfiles = pd.read_csv(comun.OUT / "07_perfiles/establecimientos_perfilados_cuenca.csv", dtype={"d_llave": str}, low_memory=False)
    cierre = pd.read_csv(comun.OUT / "11_cierre/fichas_resumen_clusters.csv")
    sensibilidad = pd.read_csv(comun.OUT / "11_cierre/sensibilidad_coexistencia.csv")
    documentos = [
        comun.DOCS / "reporte/reporte_tecnico_parte_2.pdf",
        comun.DOCS / "presentacion/presentacion_parte_2.pdf",
        comun.DOCS / "atlas/atlas_clusters.pdf",
    ]
    checks = [
        ("matriz_4365", len(maestra) == 4365),
        ("interior_4010", int(maestra.dentro_cuenca.astype(bool).sum()) == 4010),
        ("escenarios_57", escenarios.escenario_id.nunique() == 57),
        ("membresia_completa", escenarios.groupby("escenario_id").size().eq(4365).all()),
        ("solucion_fija_4365", len(solucion) == 4365),
        ("perfilado_interior_4010", len(perfiles) == 4010),
        ("clusters_interiores_18", cierre.grupo_espacial.str.startswith("CLUSTER").sum() == 18),
        ("ficha_ruido_unica", cierre.grupo_espacial.eq("RUIDO_DISPERSO").sum() == 1),
        ("atlas_19_imagenes", len(list((comun.OUT / "12_atlas").glob("*.png"))) == 19),
        ("figuras_finales_11", len(list((comun.OUT / "13_figuras_finales").glob("*.png"))) == 11),
        ("sensibilidad_sin_cluster_lavanderias_80", sensibilidad.clusters_lavanderias_80pct.eq(0).all()),
        *[(f"documento_{p.stem}", p.exists() and p.stat().st_size > 50_000) for p in documentos],
    ]
    resultado = pd.DataFrame(checks, columns=["verificacion", "cumple"])
    resultado["detalle"] = ""
    comun.guardar_csv(resultado, comun.OUT / "11_cierre/validacion_final.csv")
    inventario = []
    for base in [comun.OUT / "11_cierre", comun.OUT / "12_atlas", comun.OUT / "13_figuras_finales", comun.DOCS]:
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() not in {".aux", ".log", ".fls", ".fdb_latexmk", ".nav", ".snm", ".toc", ".out"}:
                inventario.append({
                    "ruta": str(p.relative_to(comun.ROOT)), "bytes": p.stat().st_size,
                    "sha256": comun.sha256(p),
                })
    comun.guardar_csv(pd.DataFrame(inventario), comun.OUT / "11_cierre/inventario_cierre.csv")
    if not resultado.cumple.all():
        print(resultado[~resultado.cumple].to_string(index=False))
        raise RuntimeError("Falló la validación final de Parte 2.")
    print(resultado.to_string(index=False))


if __name__ == "__main__":
    main()
