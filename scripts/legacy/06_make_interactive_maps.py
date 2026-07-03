from __future__ import annotations

import json
from pathlib import Path

import geopandas as gpd
import pandas as pd

from common import OUTPUTS_DIR, PROCESSED_DIR, ensure_output_dirs, log, normalize_text, read_gpkg, relpath


INTERACTIVE_DIR = OUTPUTS_DIR / "maps_interactive"
REGIONS = {
    "huejotzingo": {"label": "Huejotzingo", "source_key": "huejotzingo"},
    "xalmimilulco": {"label": "Santa Ana Xalmimilulco", "source_key": "xalmimilulco"},
    "san_martin": {"label": "San Martin Texmelucan", "source_key": "san_martin"},
}
CATEGORY_COLORS = {
    "alta_relevancia_ambiental": "#b2182b",
    "media_relevancia_ambiental": "#ef8a62",
    "revisar": "#7b3294",
}


def source_filter(gdf: gpd.GeoDataFrame, source_key: str) -> gpd.GeoDataFrame:
    if gdf.empty or "source_folder" not in gdf.columns:
        return gdf
    return gdf[gdf["source_folder"].map(normalize_text).str.contains(source_key, na=False)].copy()


def line_geometries(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    return gdf[gdf.geometry.geom_type.fillna("").str.contains("Line", case=False)].copy()


def crop_to_bounds(gdf: gpd.GeoDataFrame, bounds, pad: float = 1600) -> gpd.GeoDataFrame:
    if gdf.empty or bounds is None:
        return gdf
    minx, miny, maxx, maxy = bounds
    cropped = gdf.cx[minx - pad : maxx + pad, miny - pad : maxy + pad].copy()
    return cropped if not cropped.empty else gdf


def points_payload(points: gpd.GeoDataFrame) -> list[dict]:
    if points.empty:
        return []
    wgs = points.to_crs("EPSG:4326")
    rows = []
    for _, row in wgs.iterrows():
        geom = row.geometry
        if geom is None or geom.is_empty:
            continue
        rows.append(
            {
                "lat": float(geom.y),
                "lon": float(geom.x),
                "nombre": str(row.get("nombre_de_la_unidad_economica", "")),
                "scian": str(row.get("codigo_de_la_clase_actividad_scian", row.get("codigo_scian_detectado", ""))),
                "categoria": str(row.get("categoria_relevancia_ambiental", "")),
                "distancia_m": "" if pd.isna(row.get("distancia_hidrografia_m", pd.NA)) else round(float(row.get("distancia_hidrografia_m")), 1),
                "rango": str(row.get("rango_distancia_hidrografia", "")),
                "palabras": str(row.get("palabras_clave_detectadas", "")),
                "fuente": str(row.get("source_folder", "")),
                "id": str(row.get("id", "")),
                "clee": str(row.get("clee", "")),
            }
        )
    return rows


def hydro_geojson(hydro: gpd.GeoDataFrame, bounds) -> dict:
    if hydro.empty:
        return {"type": "FeatureCollection", "features": []}
    cropped = crop_to_bounds(hydro, bounds, pad=1800).copy()
    cropped["geometry"] = cropped.geometry.simplify(15)
    keep_cols = [c for c in ["source_folder", "source_file", "tipo", "condicion"] if c in cropped.columns]
    return json.loads(cropped[keep_cols + ["geometry"]].to_crs("EPSG:4326").to_json(drop_id=True))


def html_template(title: str, points: list[dict], hydro: dict, center: tuple[float, float], zoom: int) -> str:
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    .legend {{ background: white; padding: 10px 12px; border-radius: 4px; box-shadow: 0 1px 8px rgba(0,0,0,.22); font: 12px Arial, sans-serif; }}
    .legend div {{ margin: 4px 0; }}
    .swatch {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }}
  </style>
</head>
<body>
<div id="map"></div>
<script>
const points = {json.dumps(points, ensure_ascii=False)};
const hydro = {json.dumps(hydro, ensure_ascii=False)};
const colors = {json.dumps(CATEGORY_COLORS, ensure_ascii=False)};

const map = L.map('map').setView([{center[0]}, {center[1]}], {zoom});
L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
  maxZoom: 19,
  attribution: '&copy; OpenStreetMap contributors'
}}).addTo(map);

const hydroLayer = L.geoJSON(hydro, {{
  style: {{ color: '#08519c', weight: 1.2, opacity: 0.75 }}
}}).addTo(map);

const pointLayer = L.layerGroup().addTo(map);
points.forEach(p => {{
  const color = colors[p.categoria] || '#525252';
  const popup = `
    <b>${{p.nombre}}</b><br>
    <b>SCIAN:</b> ${{p.scian}}<br>
    <b>Categoria:</b> ${{p.categoria}}<br>
    <b>Distancia a cauce:</b> ${{p.distancia_m}} m (${{p.rango}})<br>
    <b>Palabras:</b> ${{p.palabras}}<br>
    <b>Fuente:</b> ${{p.fuente}}<br>
    <b>ID:</b> ${{p.id}}<br>
    <b>CLEE:</b> ${{p.clee}}
  `;
  L.circleMarker([p.lat, p.lon], {{
    radius: 5,
    color: '#ffffff',
    weight: 1,
    fillColor: color,
    fillOpacity: 0.88
  }}).bindPopup(popup).addTo(pointLayer);
}});

L.control.layers(null, {{
  'Cauces / hidrografia': hydroLayer,
  'DENUE textil productivo': pointLayer
}}, {{ collapsed: false }}).addTo(map);

const legend = L.control({{position: 'bottomright'}});
legend.onAdd = function () {{
  const div = L.DomUtil.create('div', 'legend');
  div.innerHTML = '<b>{title}</b><br>' +
    Object.entries(colors).map(([k, v]) => `<div><span class="swatch" style="background:${{v}}"></span>${{k}}</div>`).join('');
  return div;
}};
legend.addTo(map);

if (points.length > 0) {{
  const bounds = L.latLngBounds(points.map(p => [p.lat, p.lon]));
  map.fitBounds(bounds.pad(0.18));
}}
</script>
</body>
</html>
"""


def write_map(filename: str, title: str, points: gpd.GeoDataFrame, hydro: gpd.GeoDataFrame) -> None:
    INTERACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    bounds = points.total_bounds if not points.empty else None
    payload = points_payload(points)
    hydro_payload = hydro_geojson(hydro, bounds)
    if payload:
        lat = sum(p["lat"] for p in payload) / len(payload)
        lon = sum(p["lon"] for p in payload) / len(payload)
        center = (lat, lon)
    else:
        center = (19.2, -98.4)
    html = html_template(title, payload, hydro_payload, center, 13)
    out = INTERACTIVE_DIR / filename
    out.write_text(html, encoding="utf-8")
    log(f"Mapa interactivo guardado: {relpath(out)}")


def main() -> None:
    ensure_output_dirs()
    INTERACTIVE_DIR.mkdir(parents=True, exist_ok=True)
    denue = read_gpkg(PROCESSED_DIR / "denue_textil_con_distancia.gpkg")
    hydro = line_geometries(read_gpkg(PROCESSED_DIR / "hidrografia.gpkg"))

    write_map("denue_textil_productivo_interactivo.html", "DENUE textil productivo - zona alta del Atoyac", denue, hydro)
    for region_id, meta in REGIONS.items():
        points = source_filter(denue, meta["source_key"])
        write_map(
            f"{region_id}_denue_textil_productivo_interactivo.html",
            f"{meta['label']}: DENUE textil productivo",
            points,
            hydro,
        )


if __name__ == "__main__":
    main()
