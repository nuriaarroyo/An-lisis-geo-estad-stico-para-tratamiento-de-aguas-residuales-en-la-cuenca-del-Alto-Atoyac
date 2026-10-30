"""Audita la entrega QGIS de Lesly sin modificar ni reconstruir sus datos.

Lee el proyecto QGZ, inventaría sus capas y comprueba si las fuentes locales
referenciadas están presentes junto al proyecto. Los resultados se escriben en
outputs/parte_3/00_auditoria_insumos_lesly.
"""

from __future__ import annotations

import csv
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import unquote
from xml.etree import ElementTree as ET


RAIZ = Path(__file__).resolve().parents[1]
ENTRADA = RAIZ / "data" / "processed" / "lesly"
SALIDA = RAIZ / "outputs" / "parte_3" / "00_auditoria_insumos_lesly"


def texto(nodo: ET.Element | None, etiqueta: str) -> str:
    if nodo is None:
        return ""
    hijo = nodo.find(etiqueta)
    return (hijo.text or "").strip() if hijo is not None else ""


def ruta_local(datasource: str) -> str:
    """Extrae la parte de archivo de un datasource QGIS cuando es local."""
    if not datasource or datasource.startswith(("http", "crs=", "/private/")):
        return ""
    valor = datasource
    if valor.startswith("file:"):
        valor = valor[5:]
    valor = valor.split("|", 1)[0].split("?", 1)[0]
    return unquote(valor)


def clasificar(nombre: str, datasource: str) -> str:
    cadena = f"{nombre} {datasource}".lower()
    reglas = [
        ("ptar", "plantas_tratamiento"),
        ("agua_potable_y_saneamiento", "plantas_tratamiento"),
        ("rioatoyac", "cauce_rio_atoyac"),
        ("limites_federales", "zona_federal_buffer"),
        ("cuenca", "limite_cuenca"),
        ("municip", "limites_municipales"),
        ("denue", "establecimientos_denue"),
        ("heatmap", "raster_densidad_denue"),
        ("estado", "limite_estatal"),
    ]
    for patron, categoria in reglas:
        if patron in cadena:
            return categoria
    return "otro"


def escribir_csv(ruta: Path, filas: list[dict], campos: list[str]) -> None:
    with ruta.open("w", newline="", encoding="utf-8-sig") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=campos)
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    qgz = next(iter(sorted(ENTRADA.glob("*.qgz"))), None)
    pdf = next(iter(sorted(ENTRADA.glob("*.pdf"))), None)
    if qgz is None:
        raise FileNotFoundError(f"No se encontró un QGZ en {ENTRADA}")

    with zipfile.ZipFile(qgz) as comprimido:
        qgs_nombre = next(n for n in comprimido.namelist() if n.lower().endswith(".qgs"))
        raiz_xml = ET.fromstring(comprimido.read(qgs_nombre))

    crs_proyecto = texto(raiz_xml.find("projectCrs/spatialrefsys"), "authid")
    capas = []
    ids_fuente = set()
    for capa in raiz_xml.findall("./projectlayers/maplayer"):
        identificador = texto(capa, "id")
        ids_fuente.add(identificador)
        datasource = texto(capa, "datasource")
        local = ruta_local(datasource)
        ruta_resuelta = (ENTRADA / local).resolve() if local else None
        proveedor = texto(capa, "provider")
        capas.append(
            {
                "id_capa": identificador,
                "nombre": texto(capa, "layername"),
                "tipo": capa.attrib.get("type", ""),
                "geometria": capa.attrib.get("geometry", ""),
                "crs": texto(capa.find("srs/spatialrefsys"), "authid"),
                "proveedor": proveedor,
                "categoria_parte3": clasificar(texto(capa, "layername"), datasource),
                "datasource": datasource,
                "ruta_local": local,
                "fuente_disponible": bool(ruta_resuelta and ruta_resuelta.exists()),
            }
        )

    arbol = []
    for nodo in raiz_xml.findall(".//layer-tree-layer"):
        identificador = nodo.attrib.get("id", "")
        arbol.append(
            {
                "id_capa": identificador,
                "nombre": nodo.attrib.get("name", ""),
                "source": nodo.attrib.get("source", ""),
                "provider_key": nodo.attrib.get("providerKey", ""),
                "tiene_maplayer": identificador in ids_fuente,
            }
        )

    huerfanas = [fila for fila in arbol if not fila["tiene_maplayer"]]
    locales = [fila for fila in capas if fila["ruta_local"]]
    disponibles = [fila for fila in locales if fila["fuente_disponible"]]
    categorias = sorted({fila["categoria_parte3"] for fila in capas})
    resumen = {
        "entrada_qgz": str(qgz.relative_to(RAIZ)),
        "entrada_pdf": str(pdf.relative_to(RAIZ)) if pdf else None,
        "tipo_entrega": "proyecto_qgis_comprimido_no_geopackage",
        "crs_proyecto": crs_proyecto,
        "n_capas_maplayer": len(capas),
        "n_fuentes_locales_referenciadas": len(locales),
        "n_fuentes_locales_disponibles": len(disponibles),
        "n_nodos_arbol_sin_maplayer": len(huerfanas),
        "categorias_declaradas": categorias,
        "conclusion": (
            "El QGZ conserva configuración y simbología, pero no incorpora las fuentes "
            "vectoriales/raster locales referenciadas. No es posible contar objetos, "
            "auditar atributos ni analizar conectividad hasta recibir esos archivos."
        ),
    }

    escribir_csv(
        SALIDA / "capas_proyecto_qgis.csv",
        capas,
        ["id_capa", "nombre", "tipo", "geometria", "crs", "proveedor", "categoria_parte3",
         "datasource", "ruta_local", "fuente_disponible"],
    )
    escribir_csv(
        SALIDA / "nodos_arbol_sin_fuente.csv",
        huerfanas,
        ["id_capa", "nombre", "source", "provider_key", "tiene_maplayer"],
    )
    (SALIDA / "resumen_inspeccion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    # ASCII escapado mantiene la salida portable en consolas Windows no UTF-8.
    print(json.dumps(resumen, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
