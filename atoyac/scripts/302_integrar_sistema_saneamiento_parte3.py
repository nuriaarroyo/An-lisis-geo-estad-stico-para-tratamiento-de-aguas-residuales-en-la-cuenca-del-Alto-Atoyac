"""Construye la base analítica integrada de la Parte 3 sin inferir conexiones hidráulicas."""

from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyogrio

RAIZ = Path(__file__).resolve().parents[1]
P2 = RAIZ / "outputs" / "parte_2"
P3 = RAIZ / "outputs" / "parte_3"
BASE = P3 / "01_insumos_organizados" / "parte_3_insumos_base.gpkg"
GPKG = P3 / "parte_3_sistema_saneamiento_integrado.gpkg"
CRS = "EPSG:32614"
FECHA = date.today().isoformat()

DIRS = {
    "auditoria": P3 / "00_auditoria",
    "homologados": P3 / "01_insumos_homologados",
    "integracion": P3 / "02_integracion",
    "relaciones": P3 / "03_relaciones_espaciales",
    "qa": P3 / "04_control_calidad",
    "mapas": P3 / "05_mapas",
    "docs": P3 / "docs",
}


def normalizar(valor: object) -> str:
    texto = "" if pd.isna(valor) else str(valor)
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Z0-9]+", " ", texto.upper()).strip()


def reparar_texto(valor: object) -> object:
    if not isinstance(valor, str) or "�" not in valor:
        return valor
    reemplazos = {"Mart\ufffdn": "Mart\u00edn", "compilaci\ufffdn": "compilaci\u00f3n", "R\ufffdo": "R\u00edo",
                   "Fisicoqu\ufffdmico": "Fisicoqu\u00edmico", "Quetzalc\ufffdatl": "Quetzalc\u00f3atl",
                   "Mar\ufffda": "Mar\u00eda"}
    for malo, bueno in reemplazos.items():
        valor = valor.replace(malo, bueno)
    return valor


def ids(prefijo: str, n: int, ancho: int = 5) -> list[str]:
    return [f"{prefijo}_{i:0{ancho}d}" for i in range(1, n + 1)]


def capa(ruta: Path, nombre: str) -> gpd.GeoDataFrame:
    return gpd.read_file(ruta, layer=nombre).to_crs(CRS)


def escribir(gdf: gpd.GeoDataFrame, nombre: str) -> None:
    pyogrio.write_dataframe(gdf, GPKG, layer=nombre, driver="GPKG", append=GPKG.exists())


def auditar_fuentes() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    fuentes = [
        ("P2_EST", P2 / "06_clusters" / "solucion_principal.gpkg", "Parte 2", "DENUE y clustering", "reutilizar"),
        ("P2_SUB", P2 / "11_cierre" / "diagnostico_mega_cluster.gpkg", "Parte 2", "subnúcleos diagnósticos", "reutilizar"),
        ("P2_SUBDOC", P2 / "14_segunda_pasada" / "subnucleos_mega_cluster_documentados.csv", "Parte 2", "atributos de subnúcleos", "reutilizar"),
        ("P3_BASE", BASE, "Lesly/INEGI/RH18", "infraestructura organizada", "reutilizar"),
        ("LESLY_PDF", RAIZ / "data" / "processed" / "lesly" / "Reporte_Río_Atoyac_colectores_lesly.pdf", "Lesly", "documentación", "referencia"),
        ("LESLY_QGZ", RAIZ / "data" / "processed" / "lesly" / "FINAL_ATOYAC.qgz", "Lesly", "proyecto QGIS", "referencia parcial"),
    ]
    fdf = pd.DataFrame(fuentes, columns=["fuente_id", "ruta", "origen", "contenido", "uso_parte3"])
    fdf["existe"] = fdf["ruta"].map(Path.exists)
    fdf["ruta"] = fdf["ruta"].map(lambda p: str(p.relative_to(RAIZ)))
    capas, campos = [], []
    for _, fila in fdf[fdf["existe"]].iterrows():
        ruta = RAIZ / fila["ruta"]
        if ruta.suffix.lower() != ".gpkg":
            continue
        for nombre, geom in pyogrio.list_layers(ruta):
            info = pyogrio.read_info(ruta, layer=nombre)
            capas.append({"fuente_id": fila.fuente_id, "ruta": fila.ruta, "capa": nombre,
                          "geometria": geom, "crs": info.get("crs"), "objetos": info.get("features")})
            for campo, tipo in zip(info.get("fields", []), info.get("dtypes", [])):
                campos.append({"fuente_id": fila.fuente_id, "capa": nombre, "campo": campo, "tipo": tipo})
    return fdf, pd.DataFrame(capas), pd.DataFrame(campos)


def preparar_establecimientos() -> gpd.GeoDataFrame:
    e = capa(P2 / "06_clusters" / "solucion_principal.gpkg", "establecimientos_membresia")
    e = e.reset_index(drop=True)
    e.insert(0, "establecimiento_id", ids("EST", len(e)))
    e["nombre"] = e["nom_est"]
    e["scian"] = e["cve_scian"].astype(str)
    e["actividad"] = e["desc_scian"]
    e["clasificacion"] = e["sector_textil"]
    alta = e["humedo_explicito"].fillna(False) | e["scian_acabado_humedo"].fillna(False)
    media = e["lavado_generico"].fillna(False) | e["scian_lavanderia"].fillna(False)
    e["prioridad_ambiental"] = np.select([alta, media], ["alta", "media"], default="por_revisar")
    e["proceso_hidrico"] = np.select(
        [alta, e["proceso_seco_explicito"].fillna(False)], ["humedo", "seco_explicito"], default="revisar")
    e["cluster_id"] = e["cluster"].map(lambda x: "RUIDO" if int(x) == -1 else f"CLU_{int(x):03d}")
    e["subnucleo_id"] = None
    sub = capa(P2 / "11_cierre" / "diagnostico_mega_cluster.gpkg", "establecimientos_subnucleos")
    mapa_sub = sub.set_index("d_llave")["subnucleo_diagnostico"].to_dict()
    e["subnucleo_id"] = e["d_llave"].map(mapa_sub).map(
        lambda x: f"SUB_{int(x):02d}" if pd.notna(x) and int(x) >= 0 else None)
    e["fuente"] = "Parte 2: solucion_principal.gpkg"
    e["estado_verificacion"] = "B"
    return e


def preparar_clusters() -> gpd.GeoDataFrame:
    c = capa(P2 / "06_clusters" / "solucion_principal.gpkg", "envolventes_convexas")
    c.insert(0, "cluster_id", c["cluster"].map(lambda x: f"CLU_{int(x):03d}"))
    c["fuente"] = "Parte 2: solución principal congelada"
    c["estado_verificacion"] = "B"
    return c


def preparar_subnucleos() -> gpd.GeoDataFrame:
    puntos = capa(P2 / "11_cierre" / "diagnostico_mega_cluster.gpkg", "establecimientos_subnucleos")
    puntos = puntos[puntos["subnucleo_diagnostico"] >= 0].copy()
    filas = []
    for valor, grupo in puntos.groupby("subnucleo_diagnostico"):
        geom = grupo.geometry.union_all().convex_hull
        if geom.geom_type in ("Point", "LineString"):
            geom = geom.buffer(50)
        filas.append({"subnucleo_id": f"SUB_{int(valor):02d}", "n_establecimientos": len(grupo),
                      "fuente": "Parte 2: diagnóstico interno del cluster 20",
                      "estado_verificacion": "C", "geometry": geom})
    return gpd.GeoDataFrame(filas, crs=CRS)


def preparar_ptar() -> tuple[gpd.GeoDataFrame, pd.DataFrame, pd.DataFrame]:
    ine = capa(BASE, "inegi_ptar_cuenca").reset_index(drop=True)
    man = capa(BASE, "ptar_compilacion_manual")
    for col in ["Tipo", "Nombre", "Municipio_Localidad", "Proceso", "Cuerpo_receptor_reuso", "fuente_datos"]:
        man[col] = man[col].map(reparar_texto)
    man = man[man["Tipo"].str.contains("tratamiento", case=False, na=False)].reset_index(drop=True)
    filas, fuentes = [], []
    for _, r in ine.iterrows():
        pid = f"PTAR_{len(filas)+1:03d}"
        filas.append({"ptar_id": pid, "nombre_normalizado": normalizar(r.nom_tipo), "nombre_fuente": r.nom_tipo,
                      "municipio": reparar_texto(r.nom_mun), "localidad": None, "tipo_ptar": "municipal_reportada",
                      "tipo_usuario": "municipal", "proceso": None, "capacidad_ls": None,
                      "caudal_tratado_ls": None, "cuerpo_receptor": None, "responsable_operacion": None,
                      "estado_operativo_reportado": None, "anio_fuente": 2021,
                      "fuente": "INEGI CNGMD 2021 (descarga 2023)", "fecha_consulta": FECHA,
                      "estado_verificacion": "A_registro_oficial_no_operacion", "observaciones": None,
                      "geometry": r.geometry})
        fuentes.append({"ptar_id": pid, "registro_fuente_id": r.cve_geo, "fuente": "INEGI CNGMD",
                        "anio": 2021, "nombre_fuente": r.nom_tipo, "ruta_origen": "P3_BASE/inegi_ptar_cuenca"})
    for _, r in man.iterrows():
        pid = f"PTAR_{len(filas)+1:03d}"
        filas.append({"ptar_id": pid, "nombre_normalizado": normalizar(r.Nombre), "nombre_fuente": r.Nombre,
                      "municipio": str(r.Municipio_Localidad).split(",")[0], "localidad": r.Municipio_Localidad,
                      "tipo_ptar": r.Tipo, "tipo_usuario": "municipal", "proceso": r.Proceso,
                      "capacidad_ls": r.Capacidad_instalada_Ls, "caudal_tratado_ls": r.Caudal_tratado_Ls,
                      "cuerpo_receptor": r.Cuerpo_receptor_reuso, "responsable_operacion": None,
                      "estado_operativo_reportado": None, "anio_fuente": r.Anio, "fuente": "PTAR_Final.csv",
                      "fecha_consulta": FECHA, "estado_verificacion": "C_compilacion_por_conciliar",
                      "observaciones": "Registro conservado por separado hasta conciliación", "geometry": r.geometry})
        fuentes.append({"ptar_id": pid, "registro_fuente_id": f"MANUAL_{int(r.id):03d}", "fuente": "PTAR_Final.csv",
                        "anio": r.Anio, "nombre_fuente": r.Nombre, "ruta_origen": "P3_BASE/ptar_compilacion_manual"})
    ptar = gpd.GeoDataFrame(filas, crs=CRS)
    pares = []
    a = ptar[ptar["fuente"].str.startswith("PTAR_Final")]
    b = ptar[ptar["fuente"].str.startswith("INEGI")]
    for _, ra in a.iterrows():
        dist = b.geometry.distance(ra.geometry)
        for idx in dist.nsmallest(3).index:
            rb = b.loc[idx]; d = float(dist.loc[idx])
            sim = SequenceMatcher(None, ra.nombre_normalizado, rb.nombre_normalizado).ratio()
            mismo = normalizar(ra.municipio) == normalizar(rb.municipio)
            exacta = d <= 20 and sim >= .9 and mismo
            pares.append({"registro_a": ra.ptar_id, "registro_b": rb.ptar_id, "distancia_m": round(d, 2),
                          "similitud_nombre": round(sim, 3), "mismo_municipio": mismo,
                          "atributos_coincidentes": "nombre+municipio+posición" if exacta else "por_revisar",
                          "decision": "misma_ptar_probable" if exacta else "no_consolidar_revision_manual",
                          "nivel_confianza": "B" if exacta else "D",
                          "justificacion": "Coincidencia exacta multicriterio" if exacta else "Candidato espacial; evidencia insuficiente"})
    return ptar, pd.DataFrame(fuentes), pd.DataFrame(pares)


def preparar_descargas() -> gpd.GeoDataFrame:
    ine = capa(BASE, "inegi_descargas_cuenca").reset_index(drop=True)
    filas = [{"descarga_id": f"DES_{i+1:03d}", "tipo_descarga": "no_especificado", "municipio": reparar_texto(r.nom_mun),
              "nombre_sistema": reparar_texto(r.nom_tipo), "cuerpo_receptor": None, "fuente": "INEGI CNGMD 2021 (descarga 2023)", "anio": 2021,
              "estado_verificacion": "A_registro_oficial_no_operacion", "observaciones": None, "geometry": r.geometry}
             for i, (_, r) in enumerate(ine.iterrows())]
    man = capa(BASE, "ptar_compilacion_manual")
    for col in ["Tipo", "Nombre", "Municipio_Localidad", "Proceso", "Cuerpo_receptor_reuso", "fuente_datos"]:
        man[col] = man[col].map(reparar_texto)
    for _, r in man[man["Tipo"].str.contains("descarga", case=False, na=False)].iterrows():
        filas.append({"descarga_id": f"DES_{len(filas)+1:03d}", "tipo_descarga": "industrial", "nombre_sistema": r.Nombre,
                      "municipio": "San Mart\u00edn Texmelucan", "cuerpo_receptor": r.Cuerpo_receptor_reuso,
                      "fuente": "PTAR_Final.csv", "anio": r.Anio, "estado_verificacion": "C_compilacion_por_verificar",
                      "observaciones": r.Nombre, "geometry": r.geometry})
    return gpd.GeoDataFrame(filas, crs=CRS)


def vecinos(origen: gpd.GeoDataFrame, destino: gpd.GeoDataFrame, oid: str, did: str) -> pd.DataFrame:
    if destino.empty:
        return pd.DataFrame(columns=[oid, did, "distancia_m", "nivel_evidencia"])
    j = gpd.sjoin_nearest(origen[[oid, "geometry"]], destino[[did, "geometry"]], distance_col="distancia_m")
    return j[[oid, did, "distancia_m"]].assign(nivel_evidencia="C_proximidad_espacial")


def mapa_base(ax, cuenca, hidro):
    cuenca.boundary.plot(ax=ax, color="#333333", linewidth=.8)
    hidro.plot(ax=ax, color="#8ecae6", linewidth=.25, alpha=.55)
    xmin, ymin, xmax, ymax = cuenca.total_bounds
    margen = max(xmax - xmin, ymax - ymin) * .035
    ax.set_xlim(xmin - margen, xmax + margen)
    ax.set_ylim(ymin - margen, ymax + margen)
    ax.set_axis_off()


def generar_mapas(est, clusters, subs, colectores, desc, ptar, hidro, cuenca):
    configuraciones = [
        ("01_establecimientos_subnucleos_colectores", "Establecimientos, subnúcleos y colectores", "sub"),
        ("02_establecimientos_descargas", "Establecimientos y descargas", "desc"),
        ("03_ptar_tipo_fuente", "PTAR por fuente", "ptar"),
        ("04_colectores_estatus", "Colectores por estatus", "col"),
        ("05_infraestructura_hidrografia", "Infraestructura e hidrografía", "all"),
        ("06_concentracion_sin_infraestructura", "Concentración textil y vacíos de información", "gap"),
    ]
    for archivo, titulo, modo in configuraciones:
        fig, ax = plt.subplots(figsize=(9, 9)); mapa_base(ax, cuenca, hidro)
        if modo in {"sub", "desc", "all", "gap"}:
            est.plot(ax=ax, color="#6a3d9a", markersize=1.5, alpha=.35, label="Establecimientos")
        if modo == "sub":
            subs.boundary.plot(ax=ax, color="#ff7f00", linewidth=1.2, label="Subnúcleos")
        if modo in {"desc", "all"}:
            desc.plot(ax=ax, color="#d73027", marker="x", markersize=18, label="Descargas")
        if modo in {"ptar", "all"}:
            for fuente, g in ptar.groupby("fuente"):
                g.plot(ax=ax, markersize=28, marker="^", label=fuente)
        if modo in {"col", "sub", "all"} and not colectores.empty:
            colectores.plot(ax=ax, color="#fdae61", linewidth=2, label="Colectores")
        if modo == "gap":
            clusters.boundary.plot(ax=ax, color="#ff7f00", linewidth=1, label="Clusters")
            ptar.plot(ax=ax, color="#1b9e77", marker="^", markersize=25, label="PTAR")
        ax.set_title(titulo)
        h, l = ax.get_legend_handles_labels()
        if h: ax.legend(loc="lower left", fontsize=7, frameon=True)
        fig.tight_layout(); fig.savefig(DIRS["mapas"] / f"{archivo}.png", dpi=220); plt.close(fig)


def main() -> None:
    for d in DIRS.values(): d.mkdir(parents=True, exist_ok=True)
    if GPKG.exists(): GPKG.unlink()
    fuentes, capas, campos = auditar_fuentes()
    fuentes.to_csv(DIRS["auditoria"] / "inventario_fuentes_parte3.csv", index=False, encoding="utf-8-sig")
    capas.to_csv(DIRS["auditoria"] / "inventario_capas_parte3.csv", index=False, encoding="utf-8-sig")
    campos.to_csv(DIRS["auditoria"] / "campos_por_capa_parte3.csv", index=False, encoding="utf-8-sig")

    est, clusters, subs = preparar_establecimientos(), preparar_clusters(), preparar_subnucleos()
    ptar, ptar_fuentes, conciliacion = preparar_ptar()
    desc = preparar_descargas()
    hidro, municipios, cuenca = capa(BASE, "red_hidrografica_rh18_cuenca"), capa(BASE, "municipios_interseccion_cuenca"), capa(BASE, "limite_cuenca")
    hidro.insert(0, "hidrografia_id", ids("HID", len(hidro)))
    hidro["fuente"] = "INEGI Red Hidrográfica RH18 1:50,000"; hidro["estado_verificacion"] = "A_fuente_oficial"
    # No hay geometrías fuente recuperables de colectores o cuerpos receptores diferenciados.
    colectores = gpd.GeoDataFrame(columns=["colector_id", "nombre", "municipio", "tipo", "estatus_geometria", "fuente", "anio", "verificacion", "observaciones", "geometry"], geometry="geometry", crs=CRS)
    cuerpos = gpd.GeoDataFrame(columns=["cuerpo_receptor_id", "nombre", "tipo", "fuente", "estado_verificacion", "geometry"], geometry="geometry", crs=CRS)

    for nombre, gdf in [("establecimientos_textiles", est), ("clusters_parte2", clusters), ("subnucleos_parte2", subs),
                        ("colectores", colectores), ("descargas", desc), ("ptar", ptar), ("hidrografia", hidro),
                        ("cuerpos_receptores", cuerpos), ("municipios", municipios), ("limite_cuenca", cuenca)]:
        escribir(gdf, nombre)

    rel_desc, rel_ptar = vecinos(est, desc, "establecimiento_id", "descarga_id"), vecinos(est, ptar, "establecimiento_id", "ptar_id")
    rel_col = pd.DataFrame(columns=["establecimiento_id", "colector_id", "distancia_m", "dentro_100m", "dentro_250m", "dentro_500m", "metodo_asociacion", "nivel_evidencia"])
    rel_desc.to_csv(DIRS["relaciones"] / "establecimiento_descarga.csv", index=False, encoding="utf-8-sig")
    rel_ptar.to_csv(DIRS["relaciones"] / "establecimiento_ptar.csv", index=False, encoding="utf-8-sig")
    rel_col.to_csv(DIRS["relaciones"] / "establecimiento_colector.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(columns=["colector_id", "descarga_id", "distancia_m", "tipo_relacion", "nivel_evidencia"]).to_csv(DIRS["relaciones"] / "colector_descarga.csv", index=False, encoding="utf-8-sig")

    subres = []
    for _, s in subs.iterrows():
        ee = est[est["subnucleo_id"] == s.subnucleo_id]
        nd, np_ = vecinos(ee, desc, "establecimiento_id", "descarga_id"), vecinos(ee, ptar, "establecimiento_id", "ptar_id")
        subres.append({"subnucleo_id": s.subnucleo_id, "n_establecimientos": len(ee),
                       "n_alta_prioridad": int((ee.prioridad_ambiental == "alta").sum()),
                       "n_media_prioridad": int((ee.prioridad_ambiental == "media").sum()),
                       "colector_mas_cercano": None, "distancia_colector_mediana": None,
                       "descarga_mas_cercana": nd.loc[nd.distancia_m.idxmin(), "descarga_id"] if len(nd) else None,
                       "distancia_descarga": nd.distancia_m.min() if len(nd) else None,
                       "ptar_mas_cercana": np_.loc[np_.distancia_m.idxmin(), "ptar_id"] if len(np_) else None,
                       "distancia_ptar": np_.distancia_m.min() if len(np_) else None,
                       "observaciones": "Sin capa de colectores; distancias son proximidad espacial, no conexión"})
    pd.DataFrame(subres).to_csv(DIRS["relaciones"] / "subnucleo_infraestructura.csv", index=False, encoding="utf-8-sig")
    conciliacion.to_csv(P3 / "conciliacion_ptar.csv", index=False, encoding="utf-8-sig")

    with sqlite3.connect(GPKG) as con:
        ptar_fuentes.to_sql("ptar_fuentes", con, if_exists="replace", index=False)
        rel_desc.to_sql("establecimiento_descarga", con, if_exists="replace", index=False)
        rel_ptar.to_sql("establecimiento_ptar", con, if_exists="replace", index=False)

    qa = {
        "geometrias_invalidas": {n: int((~g.geometry.is_valid).sum()) for n, g in {"establecimientos": est, "ptar": ptar, "descargas": desc, "hidrografia": hidro}.items()},
        "crs_objetivo": CRS, "ptar_candidatos_conciliacion": int((conciliacion.decision == "misma_ptar_probable").sum()),
        "puntos_fuera_cuenca": {"establecimientos": int((~est.within(cuenca.union_all())).sum()), "ptar": int((~ptar.within(cuenca.union_all())).sum()), "descargas": int((~desc.within(cuenca.union_all())).sum())},
        "colectores_sin_fuente": 2, "registros_ptar_sin_anio": int(ptar.anio_fuente.isna().sum()),
        "utilizacion_mayor_1": int(((ptar.caudal_tratado_ls / ptar.capacidad_ls) > 1).sum()),
    }
    (DIRS["qa"] / "resumen_control_calidad.json").write_text(json.dumps(qa, ensure_ascii=False, indent=2), encoding="utf-8")
    (DIRS["qa"] / "reporte_control_calidad.md").write_text(f"""# Reporte de control de calidad — Parte 3

- CRS métrico común: `{CRS}`.
- Geometrías inválidas: establecimientos={qa['geometrias_invalidas']['establecimientos']}, PTAR={qa['geometrias_invalidas']['ptar']}, descargas={qa['geometrias_invalidas']['descargas']}, hidrografía={qa['geometrias_invalidas']['hidrografia']}.
- Establecimientos fuera del límite estricto de cuenca: {qa['puntos_fuera_cuenca']['establecimientos']}. Se conservan porque la solución de Parte 2 incluye contexto de borde; no son errores automáticos.
- PTAR fuera de cuenca: {qa['puntos_fuera_cuenca']['ptar']}; descargas fuera de cuenca: {qa['puntos_fuera_cuenca']['descargas']}.
- Coincidencias de PTAR con evidencia multicriterio suficiente para marcar como probables: {qa['ptar_candidatos_conciliacion']}. No se fusionaron físicamente.
- Dos nombres de colectores aparecen en el árbol QGIS, pero carecen de geometría fuente; la capa queda vacía.
- No se calculó eficiencia. El cociente caudal/capacidad, cuando sea aplicable, debe llamarse `utilizacion_capacidad_reportada`.

Las relaciones generadas son exclusivamente de proximidad espacial y no prueban conexión hidráulica, cobertura o tratamiento.
""", encoding="utf-8")
    (DIRS["auditoria"] / "advertencias_integracion.md").write_text("""# Advertencias de integración

1. No existe una capa fuente recuperable de colectores. `Camino_contenedores_SMT` y `Camino_contenedores_huejotzingo` son nodos huérfanos del QGIS.
2. `PTAR_Final.csv` mezcla cuatro PTAR con una descarga industrial; se separaron por tipo.
3. El CNGMD confirma registros administrativos, no operación actual ni conexión.
4. La red RH18 representa hidrografía superficial, no drenaje sanitario.
5. La franja de 10 m no se interpreta como delimitación legal de zona federal.
6. Las 355 unidades fuera de la cuenca se preservan como contexto de borde heredado de Parte 2.
7. Las capas `colectores` y `cuerpos_receptores` conservan el esquema vacío hasta recibir geometrías verificables.
""", encoding="utf-8")

    dic = []
    for nombre, gdf in [("establecimientos_textiles", est), ("clusters_parte2", clusters), ("subnucleos_parte2", subs),
                        ("colectores", colectores), ("descargas", desc), ("ptar", ptar), ("hidrografia", hidro),
                        ("cuerpos_receptores", cuerpos), ("municipios", municipios), ("limite_cuenca", cuenca)]:
        for campo in gdf.columns:
            dic.append({"capa": nombre, "campo": campo, "tipo": str(gdf[campo].dtype),
                        "descripcion": "Geometría EPSG:32614" if campo == "geometry" else "Atributo homologado o preservado de la fuente",
                        "origen": "Parte 2" if nombre in {"establecimientos_textiles", "clusters_parte2", "subnucleos_parte2"} else "Integración Parte 3"})
    pd.DataFrame(dic).to_csv(P3 / "diccionario_datos_parte3.csv", index=False, encoding="utf-8-sig")
    traz = pd.DataFrame([
        {"producto": "establecimientos_textiles/clusters_parte2", "fuente": "outputs/parte_2/06_clusters/solucion_principal.gpkg", "anio_referencia": "DENUE heredado", "transformacion": "selección de campos e IDs estables"},
        {"producto": "subnucleos_parte2", "fuente": "outputs/parte_2/11_cierre/diagnostico_mega_cluster.gpkg", "anio_referencia": "Parte 2", "transformacion": "envolvente convexa diagnóstica"},
        {"producto": "ptar/descargas", "fuente": "INEGI CNGMD 2021 y PTAR_Final.csv", "anio_referencia": "2021–2022", "transformacion": "separación por tipo, homologación sin fusión"},
        {"producto": "hidrografia", "fuente": "INEGI RH18 1:50,000", "anio_referencia": "según EDICION/FECHA", "transformacion": "unión de hojas y recorte a cuenca"},
        {"producto": "colectores", "fuente": "QGIS/Reporte de Lesly", "anio_referencia": "2026", "transformacion": "esquema vacío: geometrías no entregadas"},
    ])
    traz.to_csv(P3 / "trazabilidad_fuentes_parte3.csv", index=False, encoding="utf-8-sig")
    generar_mapas(est, clusters, subs, colectores, desc, ptar, hidro, cuenca)
    print(json.dumps({"gpkg": str(GPKG.relative_to(RAIZ)), "capas": 10, "establecimientos": len(est), "clusters": len(clusters), "subnucleos": len(subs), "ptar": len(ptar), "descargas": len(desc), "colectores": len(colectores)}, ensure_ascii=False, indent=2))


if __name__ == "__main__": main()
