from __future__ import annotations

from pathlib import Path
from urllib.parse import quote_plus

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

from common import PROJECT_ROOT, safe_to_file


OUT_DIR = PROJECT_ROOT / "outputs" / "universo_hidrico_preliminar"
BASE = PROJECT_ROOT / "outputs/universo_independiente_3_localidades/capas_qgis/clasificacion_completa.gpkg"
AUDITED = PROJECT_ROOT / "outputs/auditoria_6_especiales/capas_qgis/universo_productivo_auditado.gpkg"
MANUAL = PROJECT_ROOT / "outputs/universo_refinado_santa_ana/tablas/cola_reauditoria_lavanderias_20_llenado.csv"
MAQUILA_ALL = PROJECT_ROOT / "outputs/revision_maquila/cola_revision_maquila.csv"
MAQUILA_MANUAL = PROJECT_ROOT / "outputs/revision_maquila/cola_revision_maquila_pendiente_llenado.csv"
PRODUCTION_ALL = PROJECT_ROOT / "outputs/revision_produccion/cola_revision_produccion.csv"
PRODUCTION_MANUAL = PROJECT_ROOT / "outputs/revision_produccion/cola_revision_produccion_pendiente_llenado.csv"
REFERENCES = PROJECT_ROOT / "config/filtros_textiles_santa_ana/versiones/v1/referencias_comparacion.csv"
POLYGON = PROJECT_ROOT / "data/processed/localidades.gpkg"
FIG_DIR = OUT_DIR / "figuras"


def id_series(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.replace(r"\.0$", "", regex=True).str.strip()


def completed_inclusions(frame: pd.DataFrame) -> pd.DataFrame:
    status = frame["estado_revision_manual"].str.strip().str.upper()
    decision = frame["decision_manual"].str.strip().str.upper()
    return frame.loc[status.eq("COMPLETADO") & decision.str.startswith("INCLU")].copy()


def clean_value(value: object) -> str:
    return "" if pd.isna(value) else str(value).strip()


def enrich_audit_table(frame: gpd.GeoDataFrame, inclusion_sources: dict[str, str],
                       manual_frames: list[pd.DataFrame], audited: gpd.GeoDataFrame,
                       maquila: pd.DataFrame, production: pd.DataFrame) -> gpd.GeoDataFrame:
    enriched = frame.copy()
    aliases = {
        "nom_estab": "nombre_de_la_unidad_economica", "codigo_act": "codigo_de_la_clase_actividad_scian",
        "nombre_act": "nombre_clase_actividad_scian", "tipoUniEco": "tipounieco",
    }
    for source, target in aliases.items():
        if target not in enriched and source in enriched:
            enriched[target] = enriched[source]
        if source in enriched and source.lower() == target.lower() and source != target:
            enriched = enriched.drop(columns=source)
    for column in [
        "nombre_de_la_unidad_economica", "raz_social", "codigo_de_la_clase_actividad_scian",
        "nombre_clase_actividad_scian", "per_ocu", "tipo_vial", "nom_vial", "numero_ext",
        "letra_ext", "numero_int", "letra_int", "tipo_asent", "nomb_asent", "cod_postal",
        "localidad", "municipio", "entidad", "telefono", "correoelec", "www", "clee",
    ]:
        if column not in enriched:
            enriched[column] = ""
        enriched[column] = enriched[column].fillna("").astype(str)
    enriched["direccion_completa"] = enriched.apply(
        lambda row: ", ".join(value for value in [
            " ".join(value for value in [clean_value(row["tipo_vial"]), clean_value(row["nom_vial"]), clean_value(row["numero_ext"]), clean_value(row["letra_ext"])] if value),
            " ".join(value for value in [clean_value(row["tipo_asent"]), clean_value(row["nomb_asent"])] if value),
            clean_value(row["cod_postal"]), clean_value(row["localidad"]),
            clean_value(row["municipio"]), clean_value(row["entidad"]),
        ] if value), axis=1,
    )
    geo4326 = enriched.to_crs("EPSG:4326")
    enriched["latitud_revision"] = geo4326.geometry.y.to_numpy()
    enriched["longitud_revision"] = geo4326.geometry.x.to_numpy()
    enriched["url_busqueda_google_maps"] = enriched.apply(
        lambda row: "https://www.google.com/maps/search/?api=1&query=" + quote_plus(" ".join(
            value for value in [clean_value(row["nombre_de_la_unidad_economica"]), clean_value(row["direccion_completa"]), "Puebla México"] if value
        )), axis=1,
    )
    enriched["url_punto_google_maps"] = [
        "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{lat},{lon}")
        for lat, lon in zip(enriched["latitud_revision"], enriched["longitud_revision"])
    ]
    enriched["url_openstreetmap"] = [
        f"https://www.openstreetmap.org/?mlat={lat:.7f}&mlon={lon:.7f}#map=19/{lat:.7f}/{lon:.7f}"
        for lat, lon in zip(enriched["latitud_revision"], enriched["longitud_revision"])
    ]
    enriched["fuente_inclusion_tentativa"] = enriched["_id_key"].map(inclusion_sources).fillna("")

    audit_fields = [
        "estado_revision_manual", "establecimiento_encontrado", "evidencia_textil",
        "evidencia_mezclilla", "evidencia_proceso_humedo", "decision_manual",
        "confianza_revision", "fuentes_consultadas", "fecha_revision", "revisor", "notas_revision",
    ]
    audit_maps: dict[str, dict[str, str]] = {field: {} for field in audit_fields}
    audit_origin: dict[str, str] = {}
    for origin, manual_frame in zip(["LAVANDERIAS_20", "MAQUILA", "PRODUCCION"], manual_frames):
        for _, row in manual_frame.iterrows():
            key = row["_id_key"]
            if clean_value(row.get("decision_manual")) or clean_value(row.get("estado_revision_manual")) == "COMPLETADO":
                audit_origin[key] = origin
                for field in audit_fields:
                    audit_maps[field][key] = clean_value(row.get(field))
    enriched["origen_auditoria_manual"] = enriched["_id_key"].map(audit_origin).fillna("")
    for field in audit_fields:
        enriched[field] = enriched["_id_key"].map(audit_maps[field]).fillna("")
    enriched["incluido_por_auditoria_usuario"] = enriched["decision_manual"].str.strip().str.upper().str.startswith("INCLU") & enriched["estado_revision_manual"].str.strip().str.upper().eq("COMPLETADO")

    automatic = pd.concat([
        maquila[["_id_key", "decision_hidrica_automatica"]],
        production[["_id_key", "decision_hidrica_automatica"]],
    ]).drop_duplicates("_id_key").set_index("_id_key")["decision_hidrica_automatica"].to_dict()
    enriched["decision_hidrica_automatica"] = enriched["_id_key"].map(automatic).fillna("")
    special = audited.set_index("_id_key")
    for source, target in [
        ("decision_auditoria", "decision_auditoria_especial"),
        ("prioridad_auditoria", "prioridad_auditoria_especial"),
        ("causa_auditoria_especial", "causa_auditoria_especial"),
        ("fuentes_auditoria_especial", "fuentes_auditoria_especial"),
    ]:
        mapping = special[source].to_dict() if source in special else {}
        enriched[target] = enriched["_id_key"].map(mapping).fillna("")

    def priority(row: pd.Series) -> str:
        manual = clean_value(row["decision_manual"]).upper()
        if "ALTA" in manual:
            return "alta"
        if "MEDIA" in manual:
            return "media"
        sources = clean_value(row["fuente_inclusion_tentativa"])
        if "PROCESO_HUMEDO" in sources:
            return "alta"
        if row.get("en_universo_hidrico_preliminar", False):
            return "media"
        return ""
    enriched["prioridad_final_tentativa"] = enriched.apply(priority, axis=1)
    enriched["decision_final_tentativa"] = enriched["prioridad_final_tentativa"].map(
        {"alta": "INCLUIR_ALTA", "media": "INCLUIR_MEDIA"}
    ).fillna("NO_INCLUIDO_EN_TENTATIVO")
    enriched["fundamento_prioridad"] = ""
    enriched.loc[enriched["incluido_por_auditoria_usuario"], "fundamento_prioridad"] = "DICTAMEN_MANUAL_COMPLETADO"
    enriched.loc[
        enriched["fuente_inclusion_tentativa"].str.contains("PROCESO_HUMEDO", na=False),
        "fundamento_prioridad",
    ] = "PROCESO_HUMEDO_EXPLICITO_O_CONFIRMADO"
    enriched.loc[
        enriched["prioridad_final_tentativa"].eq("media") & enriched["fundamento_prioridad"].eq(""),
        "fundamento_prioridad",
    ] = "INCLUSION_PRECAUTORIA_MEZCLILLA_O_PRODUCTIVA"
    enriched.loc[
        enriched["prioridad_final_tentativa"].eq("") & enriched["en_mh"],
        "fundamento_prioridad",
    ] = "SOLO_REFERENCIA_MH_SIN_PRIORIDAD_PROPIA"
    return enriched


def save_map(points: gpd.GeoDataFrame, polygon: gpd.GeoDataFrame, filename: str,
             title: str, color: str, note: str) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9, 8))
    polygon.boundary.plot(ax=ax, color="#263238", linewidth=1.2)
    outside = 0
    if not points.empty:
        mapped = points.to_crs(polygon.crs)
        mapped.plot(ax=ax, color=color, markersize=10, alpha=.72)
        territory = polygon.geometry.union_all()
        outside = int((~mapped.geometry.intersects(territory)).sum())
    minx, miny, maxx, maxy = polygon.total_bounds
    margin_x = (maxx - minx) * .04
    margin_y = (maxy - miny) * .04
    ax.set_xlim(minx - margin_x, maxx + margin_x)
    ax.set_ylim(miny - margin_y, maxy + margin_y)
    ax.set_title(title, fontsize=14, pad=12)
    if outside:
        note += f" | {outside} punto(s) fuera del polígono, conservados en la capa"
    ax.text(.01, .01, note, transform=ax.transAxes, fontsize=9,
            bbox={"facecolor": "white", "alpha": .85, "edgecolor": "#cccccc"})
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(FIG_DIR / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def write_document(counts: dict[str, int], audit_counts: dict[str, str]) -> None:
    text = f"""# Construcción auditable del universo textil e hídrico de Santa Ana Xalmimilulco

## 1. Objetivo y alcance

Este documento registra el procedimiento reproducible seguido para pasar del DENUE 2026 a dos productos distintos: **el universo tentativo auditado**, construido con reglas independientes y decisiones humanas, y **el universo combinado tentativo + MH**, que agrega la referencia histórica de MH sin convertirla retroactivamente en una regla del filtro inicial.

La unidad de análisis es el **registro de establecimiento**. Un registro DENUE no equivale necesariamente a una empresa única ni a un sitio físico único. CLEE diferentes, como los dos registros próximos de Stone Lav, se conservan para trazabilidad aunque posteriormente puedan agruparse como un mismo complejo operativo.

## 2. Entradas

1. DENUE 2026: atributos de identificación, CLEE, nombre, razón social, SCIAN, personal ocupado, domicilio, contacto, coordenadas, tipo de unidad y fecha de alta.
2. Polígono/localidad administrativa: Santa Ana Xalmimilulco, seleccionada con `cve_loc=0029`.
3. Catálogos externos editables: códigos SCIAN, palabras clave, matriz de decisión, política de categorías y política de refinamiento.
4. MH: referencia externa comparada sólo después de materializar el universo independiente.
5. Auditorías humanas: lavanderías, maquila y producción.

![DENUE completo](figuras/01_denue_santa_ana.png)

El DENUE territorial contiene **{counts['denue']} registros**. Esta capa conserva todos los giros; todavía no representa el universo textil.

## 3. Delimitación territorial

![Polígono de Santa Ana](figuras/02_poligono_santa_ana.png)

La selección efectiva se hace por el atributo administrativo `cve_loc=0029`. El polígono se usa como representación cartográfica y comprobación espacial, no como sustituto silencioso del código administrativo. Esto evita perder registros por pequeñas discrepancias entre puntos y límites geométricos.

## 4. Universo textil/productivo amplio

![Universo textil amplio](figuras/03_universo_textil_amplio.png)

El filtrado automático combina:

- código y descripción SCIAN;
- nombre del establecimiento y razón social;
- términos de evidencia textil, mezclilla, maquila, lavado, teñido y acabado;
- términos de exclusión o contradicción;
- una matriz de prioridades que devuelve `INCLUIR`, `REVISAR` o `EXCLUIR` y conserva la regla decisiva.

El resultado amplio contiene **{counts['textil']} registros**. La clasificación inicial no lee MH ni el canónico. Por eso puede compararse posteriormente sin circularidad metodológica.

### 4.1 Catálogo SCIAN utilizado

El archivo externo `config/filtros_textiles_santa_ana/versiones/v1/codigos_scian.csv` define los códigos y no los oculta dentro del script:

| Código | Coincidencia | Interpretación |
|---|---|---|
| 313 | prefijo | fabricación de insumos y acabado textil; evidencia alta |
| 314 | prefijo | productos textiles excepto prendas; evidencia media |
| 315 | prefijo | confección de prendas; pertenencia productiva, no prueba hídrica |
| 8122 | prefijo | lavandería/tintorería; candidato para revisar |
| 313310 | exacto | acabado de productos textiles; señal húmeda alta |
| 812210 | exacto | lavandería/tintorería que necesita contexto para separar industria de servicio comercial |
| 46 | prefijo | comercio; señal de exclusión salvo evidencia productiva que la supere |

### 4.2 Catálogo de palabras

El catálogo completo está en `palabras_clave.csv` y cada fila guarda término, grupos, etapa del proceso, universo, nivel de evidencia, función y nota. Los grupos principales son:

- **textil/material:** textil, textilera, tela, tejido, tejeduría, telar, hilado, hilo y fibra textil;
- **mezclilla:** mezclilla, mesclilla, denim, jean, jeans y frases de pantalón o prendas de mezclilla;
- **húmedo:** lavado industrial/textil/de prendas, deslavado, prelavado, enjuague, stone wash, acid wash, teñido, tintura, blanqueo, mercerizado, enzimas, sosa cáustica, colorante, baño químico, suavizado, neutralizado, centrifugado y oxidante;
- **producción/maquila:** maquila textil, maquila de ropa/prendas/mezclilla, confección en serie, ensamble y taller textil;
- **alertas ambiguas:** acabado, tratamiento, estampado, serigrafía, sublimación, bordado o maquila sin objeto explícito;
- **seco o menor prioridad hídrica:** corte, costura, confección, deshebrado, bordado, over, recta, hojal, ensamble y planchado;
- **comercio/exclusión:** venta, tienda, boutique, mayoreo, distribuidora, comercializadora, outlet, bazar, mercería, renta y alquiler;
- **no textil:** autolavado, mecánica, vehículos, reparación de lavadoras, carpintería, herrería, medicina, calzado, bolsos, maletas y publicidad;
- **contradicciones:** bodega, desperdicio, productos para lavandería, servilleta y recuerdo.

La detección se realiza sobre la concatenación normalizada de nombre, razón social y actividad DENUE. Una palabra no decide sola: produce banderas que después interpreta la matriz. Así, `lavandería` aislada manda a revisión, mientras `lavandería industrial`, `lavado de prendas` o SCIAN 313310 aportan evidencia más fuerte.

### 4.3 Matriz de decisión y precedencia

La matriz externa se evalúa de mayor a menor prioridad; se aplica la primera fila cuyas banderas obligatorias, alternativas y prohibidas se cumplen:

| Prioridad | Regla | Resultado |
|---:|---|---|
| 100 | exclusión fuerte no textil | EXCLUIR |
| 98 | coincidencia genérica sin SCIAN/evidencia textil | EXCLUIR |
| 95 | lavandería contradicha por bodega/desperdicio | REVISAR |
| 90 | comercio o nombre excluido no superado por evidencia productiva | EXCLUIR |
| 80 | texto o código de proceso húmedo | INCLUIR_ALTA |
| 70 | maquila + evidencia textil/mezclilla | INCLUIR_MEDIA |
| 60 | mezclilla o jeans explícitos | INCLUIR_MEDIA |
| 50 | SCIAN textil o producción + texto textil | INCLUIR_MEDIA |
| 40 | lavado genérico | REVISAR |
| 30 | maquila sola | REVISAR |
| 20 | señal textil ambigua | REVISAR |
| 0 | sin evidencia suficiente | FUERA |

La política de categorías traduce esas decisiones en tres universos: principal, revisión y exclusión. El universo amplio incluye categorías productivas; los casos ambiguos se conservan en colas de revisión en lugar de borrarse.

## 5. Refinamiento y auditorías posteriores

La etapa de refinamiento separa pertenencia al giro textil de pertinencia hídrica. Tintorerías comerciales se excluyen del foco productivo; procesos húmedos explícitos conservan prioridad alta; actividades de confección o maquila sin evidencia de lavado permanecen sujetas a revisión.

### 5.1 Política de refinamiento

`politica_refinamiento.csv` aplica cuatro reglas ordenadas:

1. SCIAN 812210 + nombre de tintorería, sin señal industrial/productiva: `EXCLUIR_ALCANCE` por servicio comercial.
2. Tintorería con señal industrial o de proceso: `REVISAR`.
3. Caso originalmente `INCLUIR_ALTA`: `RETENER`, prioridad alta.
4. Resto del universo productivo: `RETENER`, prioridad media.

La única excepción que consulta MH en esta etapa es explícita y trazable: una lavandería genérica que estaba en revisión puede entrar como `INCLUIR_POR_MH`, prioridad media. MH no altera la clasificación inicial de los demás registros.

### 5.2 Segregación posterior de procesos secos

La exclusión de “seco” no significa que el establecimiento deje de ser textil. Significa que se retira del **universo hídrico prioritario** cuando el único proceso declarado es seco.

En maquila y producción se examina el nombre normalizado con esta precedencia:

`húmedo explícito > mezclilla explícita > seco explícito > acabado ambiguo > proceso no declarado`.

- **Húmedo explícito:** lavado, lavandería, deslave, stone/acid wash, teñido, blanqueo, mercerizado, enzimas, sosa, colorante, baño químico, suavizado, decolorado, neutralizado, centrifugado, enjuague u oxidante → `INCLUIR_PROCESO_HUMEDO`, prioridad alta.
- **Mezclilla explícita:** mezclilla, mesclilla, denim o jeans → `INCLUIR_POR_MEZCLILLA`, inclusión precautoria media si no hay señal húmeda. No se afirma automáticamente que exista lavado.
- **Seco explícito:** corte, costura, confección, deshebrado, bordado, over, recta, hojal, ensamble, presilla, etiquetado, dobladillo o armado → `EXCLUIR_SECO` del universo hídrico.
- **Planchado:** se trata como seco/consumo indirecto insuficiente para prioridad hídrica.
- **Acabado, terminado, preparado o elaboración sin técnica:** permanece `REVISAR`.
- **Maquila o producción sin proceso declarado:** permanece `REVISAR`.

Si aparecen señales contrapuestas, húmedo prevalece sobre mezclilla y mezclilla sobre seco. Esto evita excluir, por ejemplo, un establecimiento que menciona corte y lavado a la vez.

### 5.3 Seis casos especiales

| ID | Caso | Dictamen especial | Prioridad/razón |
|---:|---|---|---|
| 3427952 | Maquila de lavandería de pantalón | CONFIRMAR | alta; SCIAN 313310 y lavado explícito |
| 3428321 | Lavandería y Terminados G C | CONFIRMAR | alta; evidencia pública de mezclilla |
| 3428329 | Poliproceso | CONFIRMAR | alta; acabado textil SCIAN 313310 |
| 6861846 | Stone Lav | CONFIRMAR | alta; evidencia industrial y procesos de lavado |
| 10262715 | Impresos en servilletas para recuerdo | REVISAR_NO_TEXTIL | SCIAN textil, pero objeto/material y proceso no comprobados |
| 10451408 | Ston/Stone Lav | REVISAR_DUPLICADO | CLEE distinto y coordenada cercana; no se elimina automáticamente |

Estado de las auditorías utilizadas:

| Auditoría | Estado leído |
|---|---:|
| Lavanderías | {audit_counts['lavanderias']} |
| Maquila | {audit_counts['maquila']} |
| Producción | {audit_counts['produccion']} |

Sólo se incorporan automáticamente decisiones con `estado_revision_manual=COMPLETADO` y un dictamen que comienza con `INCLU`. Los dictámenes pendientes no se interpretan como inclusión ni como exclusión definitiva. Se toleran las variantes `INCLUIR` e `INCLUR`, pero se conservan textualmente para auditoría.

## 6. Universo tentativo auditado

![Universo tentativo](figuras/04_universo_tentativo_auditado.png)

El universo tentativo auditado contiene **{counts['tentativo']} registros** y reúne:

- procesos húmedos confirmados por las reglas y la auditoría especial;
- inclusiones de la auditoría manual de lavanderías;
- casos automáticos de maquila o producción con evidencia explícita de mezclilla/proceso hídrico;
- inclusiones manuales completadas de maquila y producción.

Se denomina **tentativo** porque quedan revisiones pendientes y porque DENUE describe el giro registrado, no verifica la operación actual, el consumo de agua ni el proceso observado en campo.

La prioridad final se expresa deliberadamente sólo como **alta** o **media** para los integrantes del tentativo: **{counts['prioridad_alta']} altas** y **{counts['prioridad_media']} medias**. Los registros que aparecen únicamente por MH no reciben una prioridad inventada; su decisión queda como `NO_INCLUIDO_EN_TENTATIVO` y su fundamento como `SOLO_REFERENCIA_MH_SIN_PRIORIDAD_PROPIA`.

## 7. Referencia MH

![Registros MH](figuras/05_mh.png)

MH contiene **{counts['mh_total']} registros administrativos**. De ellos, **{counts['mh_con_id']}** traen un ID DENUE utilizable: **{counts['mh_validos']}** tienen correspondencia con el DENUE 2026 cargado y **{counts['mh_sin_denue']}** no tienen correspondencia directa. Además, **{counts['mh_sin_id']}** filas de MH no proporcionan ID DENUE. Todas se conservan con la geometría y el nombre disponibles en MH, marcadas como tales; no se inventan atributos DENUE.

La coincidencia se determina por ID DENUE normalizado, no por similitud de nombre ni cercanía espacial. Por eso posibles duplicados físicos permanecen como registros separados mientras no exista un dictamen explícito de agrupación.

## 8. Universo combinado tentativo + MH

![Universo combinado](figuras/06_universo_combinado.png)

El universo combinado contiene **{counts['combinado']} registros únicos por ID**:

- **{counts['ambos']}** presentes tanto en el universo tentativo como en MH;
- **{counts['solo_tentativo']}** presentes sólo en el tentativo;
- **{counts['solo_mh']}** presentes sólo en MH.

Esta unión es un producto de cobertura máxima para planeación y revisión de campo. No debe presentarse como si todos sus integrantes estuvieran confirmados con el mismo nivel de evidencia. La columna `resultado_comparacion` mantiene la procedencia de cada registro.

## 9. Productos entregados

- `universo_tentativo_auditado.gpkg`, `.csv` y `.xlsx`: producto construido por reglas y auditorías.
- `universo_combinado_tentativo_mh.gpkg`, `.csv` y `.xlsx`: unión máxima con MH.
- `tabla_maestra_combinada_enriquecida.xlsx`: tabla de auditoría completa del combinado, con DENUE, enlaces, MH, decisiones y prioridad.
- `tabla_maestra_tentativa_enriquecida.xlsx`: la misma estructura limitada a los 55 integrantes del tentativo.

La tabla maestra enriquecida contiene 76+ columnas organizadas en: identificación DENUE; SCIAN; domicilio y contacto; coordenadas; tres enlaces de auditoría; pertenencia al tentativo y a MH; resultado de comparación; fuente automática de inclusión; origen y contenido de la auditoría manual; dictamen especial; decisión final `INCLUIR_ALTA/INCLUIR_MEDIA`; prioridad final y fundamento. Por ello es el archivo recomendado para lectura registro por registro.
- `comparacion_hidrico_preliminar_vs_mh.gpkg`: compatibilidad con el nombre anterior.
- `figuras/`: seis representaciones cartográficas del flujo.
- `resumen_comparacion_mh.csv`: conteos de intersección y diferencias.

## 10. Lectura correcta y limitaciones

El SCIAN es evidencia sectorial, no prueba de proceso. Un teléfono, correo o web vacío significa ausencia en DENUE, no inexistencia del negocio. Las coordenadas pueden ser aproximadas. La fecha de alta es la incorporación al directorio y no necesariamente la fecha de apertura. Finalmente, el universo combinado amplía cobertura, mientras que el universo tentativo conserva mayor independencia metodológica.
"""
    (OUT_DIR / "documentacion_completa_proceso.md").write_text(text, encoding="utf-8")


def main() -> None:
    base = gpd.read_file(BASE, engine="pyogrio")
    base["_id_key"] = id_series(base["id"])
    audited = gpd.read_file(AUDITED, engine="pyogrio")
    audited["_id_key"] = id_series(audited["id"])
    manual = pd.read_csv(MANUAL, dtype=str).fillna("")
    manual["_id_key"] = id_series(manual["id"])
    maquila = pd.read_csv(MAQUILA_ALL, dtype=str).fillna("")
    maquila["_id_key"] = id_series(maquila["id"])
    maquila_manual = pd.read_csv(MAQUILA_MANUAL, dtype=str).fillna("")
    maquila_manual["_id_key"] = id_series(maquila_manual["id"])
    production = pd.read_csv(PRODUCTION_ALL, dtype=str).fillna("")
    production["_id_key"] = id_series(production["id"])
    production_manual = pd.read_csv(PRODUCTION_MANUAL, dtype=str).fillna("")
    production_manual["_id_key"] = id_series(production_manual["id"])

    wet_ids = set(audited.loc[audited["prioridad_auditoria"].eq("alta"), "_id_key"])
    manual_include = completed_inclusions(manual)
    manual_ids = set(manual_include["_id_key"])
    maquila_manual_include = completed_inclusions(maquila_manual)
    maquila_manual_ids = set(maquila_manual_include["_id_key"])
    maquila_ids = set(maquila.loc[maquila["decision_hidrica_automatica"].str.startswith("INCLUIR"), "_id_key"])
    production_ids = set(production.loc[production["decision_hidrica_automatica"].str.startswith("INCLUIR"), "_id_key"])
    production_manual_include = completed_inclusions(production_manual)
    production_manual_ids = set(production_manual_include["_id_key"])
    selected_ids = (
        wet_ids | manual_ids | maquila_ids | production_ids
        | maquila_manual_ids | production_manual_ids
    )

    hydric = base.loc[base["_id_key"].isin(selected_ids)].copy()
    inclusion_sources = {
        key: "|".join(source for source, ids in [
            ("PROCESO_HUMEDO_CONFIRMADO", wet_ids),
            ("AUDITORIA_MANUAL_20", manual_ids),
            ("MAQUILA_MEZCLILLA_AUTOMATICA", maquila_ids),
            ("AUDITORIA_MANUAL_MAQUILA", maquila_manual_ids),
            ("PRODUCCION_MEZCLILLA_AUTOMATICA", production_ids),
            ("AUDITORIA_MANUAL_PRODUCCION", production_manual_ids),
        ] if key in ids)
        for key in selected_ids
    }
    hydric["fuente_inclusion_hidrica"] = hydric["_id_key"].map(inclusion_sources).fillna("")
    hydric["decision_hidrica_preliminar"] = "INCLUIR_PRELIMINAR"
    manual_decisions = manual_include.set_index("_id_key")["decision_manual"].to_dict()
    manual_decisions.update(
        maquila_manual_include.set_index("_id_key")["decision_manual"].to_dict()
    )
    manual_decisions.update(
        production_manual_include.set_index("_id_key")["decision_manual"].to_dict()
    )
    hydric["dictamen_manual_origen"] = hydric["_id_key"].map(manual_decisions).fillna("")

    refs = pd.read_csv(REFERENCES, dtype=str).fillna("")
    ref = refs.loc[refs["referencia_id"].eq("mh_filtrado")].iloc[0]
    mh = gpd.read_file(PROJECT_ROOT / ref["ruta"], engine="pyogrio")
    mh["_id_key"] = id_series(mh[ref["campo_id"]])
    no_id_mask = mh["_id_key"].isin(["", "nan", "None"])
    for sequence, index in enumerate(mh.index[no_id_mask], start=1):
        mh.at[index, "_id_key"] = f"MH_SIN_ID_{sequence:02d}"
    mh_ids = set(mh.loc[~no_id_mask, "_id_key"])
    mh_all_keys = set(mh["_id_key"])
    hydric["en_mh"] = hydric["_id_key"].isin(mh_ids)

    union_ids = selected_ids | mh_ids
    raw = gpd.read_file(PROJECT_ROOT / "data/raw/denue2026/Denue26 area estudio.shp", engine="pyogrio")
    raw["_id_key"] = id_series(raw["id"])
    comparison = raw.loc[raw["_id_key"].isin(union_ids)].copy()
    missing_mh_ids = mh_ids - set(comparison["_id_key"])
    if missing_mh_ids:
        mh_missing = mh.loc[mh["_id_key"].isin(missing_mh_ids)].to_crs(raw.crs)
        missing_rows = []
        for _, mh_row in mh_missing.iterrows():
            record = {column: None for column in comparison.columns}
            record["id"] = id_series(pd.Series([mh_row[ref["campo_id"]]])).iloc[0]
            record["_id_key"] = record["id"]
            record["nom_estab"] = f"Registro MH sin correspondencia DENUE 2026 (Name={mh_row.get('Name', '')})"
            record["geometry"] = mh_row.geometry
            missing_rows.append(record)
        comparison = gpd.GeoDataFrame(
            pd.concat([comparison, pd.DataFrame(missing_rows)], ignore_index=True),
            geometry="geometry", crs=raw.crs,
        )
    mh_no_id = mh.loc[no_id_mask].to_crs(raw.crs)
    if not mh_no_id.empty:
        no_id_rows = []
        for _, mh_row in mh_no_id.iterrows():
            record = {column: None for column in comparison.columns}
            record["id"] = mh_row["_id_key"]
            record["_id_key"] = mh_row["_id_key"]
            record["nom_estab"] = f"Registro MH sin ID DENUE (Name={mh_row.get('Name', '')})"
            record["geometry"] = mh_row.geometry
            no_id_rows.append(record)
        comparison = gpd.GeoDataFrame(
            pd.concat([comparison, pd.DataFrame(no_id_rows)], ignore_index=True),
            geometry="geometry", crs=raw.crs,
        )
    comparison["en_universo_hidrico_preliminar"] = comparison["_id_key"].isin(selected_ids)
    comparison["en_mh"] = comparison["_id_key"].isin(mh_all_keys)
    comparison["resultado_comparacion"] = ""
    comparison.loc[comparison["en_universo_hidrico_preliminar"] & comparison["en_mh"], "resultado_comparacion"] = "EN_AMBOS"
    comparison.loc[comparison["en_universo_hidrico_preliminar"] & ~comparison["en_mh"], "resultado_comparacion"] = "SOLO_HIDRICO_PRELIMINAR"
    comparison.loc[~comparison["en_universo_hidrico_preliminar"] & comparison["en_mh"], "resultado_comparacion"] = "SOLO_MH"

    manual_status = manual.set_index("_id_key")["decision_manual"].to_dict()
    manual_status.update(maquila_manual.set_index("_id_key")["decision_manual"].to_dict())
    manual_status.update(production_manual.set_index("_id_key")["decision_manual"].to_dict())
    maquila_status = maquila.set_index("_id_key")["decision_hidrica_automatica"].to_dict()
    production_status = production.set_index("_id_key")["decision_hidrica_automatica"].to_dict()
    def reason(key: str) -> str:
        if key in selected_ids:
            return "INCLUIDO_PRELIMINAR"
        if key in manual_status and manual_status[key].strip():
            return f"AUDITORIA_MANUAL:{manual_status[key].strip()}"
        if key in maquila_status:
            return f"MAQUILA:{maquila_status[key]}"
        if key in production_status:
            return f"PRODUCCION:{production_status[key]}"
        return "NO_CALIFICA_AUN_O_FUERA_AREA"
    comparison["razon_situacion"] = comparison["_id_key"].map(reason)

    combined_enriched = enrich_audit_table(
        comparison, inclusion_sources,
        [manual, maquila_manual, production_manual], audited, maquila, production,
    )
    tentative_enriched = combined_enriched.loc[
        combined_enriched["en_universo_hidrico_preliminar"]
    ].copy()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_to_file(hydric, OUT_DIR / "universo_hidrico_preliminar.gpkg", layer="universo_hidrico_preliminar")
    hydric.drop(columns="geometry").to_csv(OUT_DIR / "universo_hidrico_preliminar.csv", index=False, encoding="utf-8-sig")
    hydric.drop(columns="geometry").to_excel(OUT_DIR / "universo_hidrico_preliminar.xlsx", index=False)
    safe_to_file(hydric, OUT_DIR / "universo_tentativo_auditado.gpkg", layer="universo_tentativo_auditado")
    hydric.drop(columns="geometry").to_csv(OUT_DIR / "universo_tentativo_auditado.csv", index=False, encoding="utf-8-sig")
    hydric.drop(columns="geometry").to_excel(OUT_DIR / "universo_tentativo_auditado.xlsx", index=False)
    safe_to_file(comparison, OUT_DIR / "comparacion_hidrico_preliminar_vs_mh.gpkg", layer="comparacion_hidrico_vs_mh")
    comparison.drop(columns="geometry").to_csv(OUT_DIR / "comparacion_hidrico_preliminar_vs_mh.csv", index=False, encoding="utf-8-sig")
    safe_to_file(comparison, OUT_DIR / "universo_combinado_tentativo_mh.gpkg", layer="universo_combinado_tentativo_mh")
    comparison.drop(columns="geometry").to_csv(OUT_DIR / "universo_combinado_tentativo_mh.csv", index=False, encoding="utf-8-sig")
    comparison.drop(columns="geometry").to_excel(OUT_DIR / "universo_combinado_tentativo_mh.xlsx", index=False)
    safe_to_file(
        combined_enriched, OUT_DIR / "tabla_maestra_combinada_enriquecida.gpkg",
        layer="tabla_maestra_combinada_enriquecida",
    )
    combined_enriched.drop(columns="geometry").to_csv(
        OUT_DIR / "tabla_maestra_combinada_enriquecida.csv", index=False, encoding="utf-8-sig"
    )
    combined_enriched.drop(columns="geometry").to_excel(
        OUT_DIR / "tabla_maestra_combinada_enriquecida.xlsx", index=False
    )
    tentative_enriched.drop(columns="geometry").to_excel(
        OUT_DIR / "tabla_maestra_tentativa_enriquecida.xlsx", index=False
    )
    summary = comparison.groupby("resultado_comparacion").size().reset_index(name="registros")
    summary.to_csv(OUT_DIR / "resumen_comparacion_mh.csv", index=False, encoding="utf-8-sig")

    territorial = gpd.read_file(BASE, engine="pyogrio")
    textile = gpd.read_file(
        PROJECT_ROOT / "outputs/universo_independiente_3_localidades/capas_qgis/universo_independiente_incluido.gpkg",
        engine="pyogrio",
    )
    polygons = gpd.read_file(POLYGON, engine="pyogrio")
    polygon = polygons.loc[polygons["id"].astype(str).eq("210740029")].copy()
    if polygon.empty:
        polygon = polygons.loc[polygons["nombre"].astype(str).str.contains("Santa Ana", case=False, na=False)].copy()
    mh_plot = mh.to_crs(polygon.crs)
    save_map(territorial, polygon, "01_denue_santa_ana.png", "DENUE 2026 en Santa Ana Xalmimilulco", "#9e9e9e", f"{len(territorial):,} registros")
    save_map(gpd.GeoDataFrame(geometry=[], crs=polygon.crs), polygon, "02_poligono_santa_ana.png", "Delimitación de Santa Ana Xalmimilulco", "#ffffff", "Selección administrativa: cve_loc=0029")
    save_map(textile, polygon, "03_universo_textil_amplio.png", "Universo textil/productivo amplio", "#1976d2", f"{len(textile):,} registros incluidos")
    save_map(hydric, polygon, "04_universo_tentativo_auditado.png", "Universo tentativo auditado", "#ef6c00", f"{len(hydric):,} registros")
    save_map(mh_plot, polygon, "05_mh.png", "Referencia MH", "#7b1fa2", f"{len(mh):,} registros MH")
    save_map(comparison, polygon, "06_universo_combinado.png", "Universo combinado: tentativo + MH", "#00897b", f"{len(comparison):,} ID únicos")

    result_counts = comparison["resultado_comparacion"].value_counts()
    counts = {
        "denue": len(territorial), "textil": len(textile), "tentativo": len(hydric),
        "mh_total": len(mh), "mh_con_id": len(mh_ids),
        "mh_validos": len(mh_ids & set(raw["_id_key"])),
        "mh_sin_denue": len(missing_mh_ids), "mh_sin_id": int(no_id_mask.sum()),
        "combinado": len(comparison),
        "ambos": int(result_counts.get("EN_AMBOS", 0)),
        "solo_tentativo": int(result_counts.get("SOLO_HIDRICO_PRELIMINAR", 0)),
        "solo_mh": int(result_counts.get("SOLO_MH", 0)),
        "prioridad_alta": int(combined_enriched["prioridad_final_tentativa"].eq("alta").sum()),
        "prioridad_media": int(combined_enriched["prioridad_final_tentativa"].eq("media").sum()),
    }
    audit_counts = {
        "lavanderias": f"{manual['estado_revision_manual'].str.strip().eq('COMPLETADO').sum()} completadas de {len(manual)}",
        "maquila": f"{maquila_manual['estado_revision_manual'].str.strip().eq('COMPLETADO').sum()} completadas de {len(maquila_manual)} pendientes enviados",
        "produccion": f"{production_manual['estado_revision_manual'].str.strip().eq('COMPLETADO').sum()} completadas de {len(production_manual)} pendientes enviados",
    }
    write_document(counts, audit_counts)
    print(f"Universo hídrico preliminar: {len(hydric)}; MH: {len(mh_ids)}")


if __name__ == "__main__":
    main()
