"""Mapas interactivos y estaticos para el universo hidrico de la cuenca."""

from pathlib import Path
import json
import re
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
import plotly.graph_objects as go


COLORES_DISTANCIA = {
    "0-250 m": "#b2182b",
    "250-500 m": "#ef8a62",
    "500-1,000 m": "#fddbc7",
    "1-2 km": "#67a9cf",
    ">2 km": "#2166ac",
}
ESCALA_ROJO_AZUL = [
    [0.00, "#2166ac"],
    [0.25, "#67a9cf"],
    [0.50, "#f7f7f7"],
    [0.75, "#ef8a62"],
    [1.00, "#b2182b"],
]
ESTRATOS_DENUE = [
    "0 a 5 personas",
    "6 a 10 personas",
]


def _slug(texto):
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto))
        if not unicodedata.combining(c)
    ).lower()
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")


def _lineas_lon_lat(geometrias):
    lon, lat = [], []
    for geom in geometrias:
        if geom is None or geom.is_empty:
            continue
        partes = list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]
        for parte in partes:
            x, y = parte.xy
            lon.extend(x)
            lat.extend(y)
            lon.append(None)
            lat.append(None)
    return lon, lat


def _borde_lon_lat(poligonos):
    lineas = []
    for geom in poligonos:
        if geom is None or geom.is_empty:
            continue
        partes = list(geom.geoms) if geom.geom_type == "MultiPolygon" else [geom]
        lineas.extend(p.exterior for p in partes)
    return _lineas_lon_lat(lineas)


def _estilo(fig, titulo, cuenca):
    minx, miny, maxx, maxy = cuenca.total_bounds
    margen_x = (maxx - minx) * 0.04
    margen_y = (maxy - miny) * 0.04
    fig.update_geos(
        projection_type="mercator",
        showland=True,
        landcolor="#f7f4ed",
        showlakes=True,
        lakecolor="#d9edf7",
        showcountries=False,
        showcoastlines=False,
        lonaxis_range=[minx - margen_x, maxx + margen_x],
        lataxis_range=[miny - margen_y, maxy + margen_y],
    )
    fig.update_layout(
        title={"text": titulo, "x": 0.5, "xanchor": "center"},
        template="plotly_white",
        font={"family": "Arial", "size": 14, "color": "#243447"},
        margin={"l": 15, "r": 15, "t": 75, "b": 20},
        legend={"orientation": "h", "y": -0.04, "x": 0.5, "xanchor": "center"},
        width=1400,
        height=950,
    )
    return fig


def _agregar_contexto(fig, cuenca, rios=None, municipios=None):
    if municipios is not None and not municipios.empty:
        lon, lat = _borde_lon_lat(municipios.geometry)
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat, mode="lines", line={"color": "#a7a7a7", "width": 0.7},
            hoverinfo="skip", name="Límites municipales", showlegend=True,
        ))
    if rios is not None and not rios.empty:
        lon, lat = _lineas_lon_lat(rios.geometry)
        fig.add_trace(go.Scattergeo(
            lon=lon, lat=lat, mode="lines", line={"color": "#2878b5", "width": 1.0},
            hoverinfo="skip", name="Red hidrográfica",
        ))
    lon, lat = _borde_lon_lat(cuenca.geometry)
    fig.add_trace(go.Scattergeo(
        lon=lon, lat=lat, mode="lines", line={"color": "#17202a", "width": 2.8},
        hoverinfo="skip", name="Límite de cuenca",
    ))


def _guardar(fig, nombre, directorio):
    directorio = Path(directorio)
    html_dir = directorio / "html"
    png_dir = directorio / "png"
    html_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    html = html_dir / f"{nombre}.html"
    png = png_dir / f"{nombre}.png"
    fig.write_html(html, include_plotlyjs=True, full_html=True)
    try:
        fig.write_image(png, width=1400, height=950, scale=1.5)
    except Exception as exc:
        print(f"ADVERTENCIA: no se pudo exportar {png.name}: {exc}")
        png = None
    return {"nombre": nombre, "html": html, "png": png}


def _hover_establecimientos(gdf):
    texto = (
        "<b>" + gdf["nom_est"].fillna("Sin nombre") + "</b>"
        + "<br>Municipio: " + gdf["Municipio"].fillna("")
        + "<br>Localidad: " + gdf["localidad"].fillna("")
        + "<br>SCIAN: " + gdf["cve_scian"].fillna("")
        + "<br>Evidencia hídrica: " + gdf["evidencia_hidrica"].fillna("")
        + "<br>Tamaño: " + gdf["Descripcion estrato personal ocupado"].fillna("")
    )
    if "fuente_evidencia_hidrica" in gdf.columns:
        texto += "<br>Fuente: " + gdf["fuente_evidencia_hidrica"].fillna("")
    return texto


def _mapa_confirmados(cuenca, rios, municipios, puntos):
    fig = go.Figure()
    _agregar_contexto(fig, cuenca, rios, municipios)
    grupos = [
        ("MH_TRABAJO_CAMPO", "Confirmado por trabajo de campo MH", "#b2182b"),
        ("REGLAS_DENUE", "Evidencia explícita en DENUE", "#ef8a62"),
    ]
    for fuente, etiqueta, color in grupos:
        parte = puntos[puntos["fuente_evidencia_hidrica"].eq(fuente)]
        if parte.empty:
            continue
        fig.add_trace(go.Scattergeo(
            lon=parte.geometry.x, lat=parte.geometry.y, mode="markers",
            marker={"size": 8, "color": color, "opacity": 0.85,
                    "line": {"color": "white", "width": 0.5}},
            text=_hover_establecimientos(parte),
            hovertemplate="%{text}<extra></extra>", name=etiqueta,
        ))
    return _estilo(
        fig, "Establecimientos confirmados por campo y evidencia explícita DENUE", cuenca
    )


def _mapa_hidrologia(cuenca, rios, municipios):
    fig = go.Figure()
    _agregar_contexto(fig, cuenca, rios, municipios)
    dato = cuenca.iloc[0]
    fig.add_annotation(
        text=(f"{dato['nom_cuenca']} · {dato['nom_rha']} · "
              f"{dato['clasif']} · disponibilidad: {dato['vol_dispo']} hm³"),
        x=0.5, y=0.01, xref="paper", yref="paper", showarrow=False,
        bgcolor="rgba(255,255,255,0.85)", bordercolor="#777",
    )
    return _estilo(fig, "Cuenca del Alto Atoyac e información hídrica", cuenca)


def _mapa_establecimientos(cuenca, rios, municipios, puntos):
    fig = go.Figure()
    _agregar_contexto(fig, cuenca, rios, municipios)
    for categoria, color in [
        ("SI", "#b2182b"),
        ("REVISAR", "#2166ac"),
        ("SIN_EVIDENCIA", "#7f8c8d"),
    ]:
        parte = puntos[puntos["evidencia_hidrica"].eq(categoria)]
        if parte.empty:
            continue
        fig.add_trace(go.Scattergeo(
            lon=parte.geometry.x, lat=parte.geometry.y, mode="markers",
            marker={"size": 7, "color": color, "opacity": 0.78,
                    "line": {"color": "white", "width": 0.4}},
            text=_hover_establecimientos(parte), hovertemplate="%{text}<extra></extra>",
            name=f"Evidencia {categoria}",
        ))
    return _estilo(fig, "Establecimientos por clasificación de evidencia hídrica", cuenca)


def _calcular_distancia(puntos, rios):
    puntos_m = puntos.to_crs(32614)
    rios_m = rios.to_crs(32614)
    red = rios_m.geometry.union_all()
    distancia = puntos_m.geometry.distance(red)
    puntos = puntos.copy()
    puntos["distancia_rio_m"] = distancia.to_numpy()
    puntos["rango_distancia"] = pd.cut(
        puntos["distancia_rio_m"],
        bins=[-np.inf, 250, 500, 1000, 2000, np.inf],
        labels=list(COLORES_DISTANCIA),
    ).astype(str)
    return puntos


def _mapa_distancia(cuenca, rios, municipios, puntos):
    fig = go.Figure()
    _agregar_contexto(fig, cuenca, rios, municipios)
    for rango, color in COLORES_DISTANCIA.items():
        parte = puntos[puntos["rango_distancia"].eq(rango)]
        if parte.empty:
            continue
        texto = _hover_establecimientos(parte) + (
            "<br>Distancia a la red: " + parte["distancia_rio_m"].round().astype(int).astype(str) + " m"
        )
        fig.add_trace(go.Scattergeo(
            lon=parte.geometry.x, lat=parte.geometry.y, mode="markers",
            marker={"size": 7, "color": color, "opacity": 0.82,
                    "line": {"color": "white", "width": 0.4}},
            text=texto, hovertemplate="%{text}<extra></extra>", name=rango,
        ))
    return _estilo(fig, "Establecimientos por cercanía a la red hidrográfica", cuenca)


def _conteo_municipal(puntos, municipios):
    base = municipios.copy().reset_index(drop=True)
    base["map_id"] = base.index.astype(str)
    asignados = gpd.sjoin(
        puntos[["geometry"]], base[["map_id", "geometry"]],
        how="left", predicate="within",
    )
    conteos = asignados["map_id"].value_counts()
    base["n_establecimientos"] = base["map_id"].map(conteos).fillna(0).astype(int)
    return base


def _mapa_municipal(cuenca, rios, municipios, puntos, titulo):
    datos = _conteo_municipal(puntos, municipios)
    geojson = json.loads(datos.to_json())
    texto = (
        "<b>" + datos["nom_mun"] + "</b>"
        + "<br>Establecimientos: " + datos["n_establecimientos"].astype(str)
    )
    fig = go.Figure(go.Choropleth(
        geojson=geojson, locations=datos.index.astype(str), z=datos["n_establecimientos"],
        featureidkey="id", colorscale=ESCALA_ROJO_AZUL, reversescale=False,
        zmin=0, zmax=max(1, int(datos["n_establecimientos"].max())),
        marker_line_color="white", marker_line_width=0.8,
        text=texto, hovertemplate="%{text}<extra></extra>",
        colorbar={"title": "Número de<br>establecimientos"},
    ))
    _agregar_contexto(fig, cuenca, rios, None)
    return _estilo(fig, titulo, cuenca)


def _mapa_localidades(cuenca, rios, municipios, puntos, titulo):
    if puntos.empty:
        resumen = pd.DataFrame(columns=["Municipio", "localidad", "lon", "lat", "n"])
    else:
        temporal = puntos.copy()
        temporal["lon"] = temporal.geometry.x
        temporal["lat"] = temporal.geometry.y
        resumen = temporal.groupby(["Municipio", "localidad"], as_index=False).agg(
            lon=("lon", "mean"), lat=("lat", "mean"), n=("d_llave", "size")
        )
    fig = go.Figure()
    _agregar_contexto(fig, cuenca, rios, municipios)
    if not resumen.empty:
        max_n = max(int(resumen["n"].max()), 1)
        texto = (
            "<b>" + resumen["localidad"] + "</b>"
            + "<br>Municipio: " + resumen["Municipio"]
            + "<br>Establecimientos: " + resumen["n"].astype(str)
        )
        fig.add_trace(go.Scattergeo(
            lon=resumen["lon"], lat=resumen["lat"], mode="markers",
            marker={"size": 9 + 25 * np.sqrt(resumen["n"] / max_n),
                    "color": resumen["n"], "colorscale": ESCALA_ROJO_AZUL,
                    "cmin": 0, "cmax": max_n, "opacity": 0.82,
                    "line": {"color": "white", "width": 0.7},
                    "colorbar": {"title": "Número de<br>establecimientos"}},
            text=texto, hovertemplate="%{text}<extra></extra>", name="Localidades",
        ))
    else:
        fig.add_annotation(
            text="Sin establecimientos en este estrato dentro de la cuenca",
            x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False,
            bgcolor="rgba(255,255,255,0.9)", bordercolor="#777",
        )
    return _estilo(fig, titulo, cuenca)


def crear_mapas_cuenca(cuenca, rios, municipios, establecimientos, output_dir):
    """Crea HTML interactivos, PNG y devuelve un inventario reproducible."""
    output_dir = Path(output_dir)
    cuenca = cuenca.to_crs(4326)
    rios = gpd.clip(rios.to_crs(4326), cuenca)
    municipios = gpd.clip(municipios.to_crs(4326), cuenca)
    establecimientos = establecimientos.to_crs(4326).copy()
    establecimientos = _calcular_distancia(establecimientos, rios)

    productos = []
    productos.append(_guardar(
        _mapa_hidrologia(cuenca, rios, municipios), "01_cuenca_informacion_hidrica", output_dir
    ))
    productos.append(_guardar(
        _mapa_establecimientos(cuenca, rios, municipios, establecimientos),
        "02_cuenca_establecimientos_hidricos", output_dir,
    ))
    productos.append(_guardar(
        _mapa_distancia(cuenca, rios, municipios, establecimientos),
        "03_establecimientos_distancia_rio", output_dir,
    ))
    confirmados = establecimientos[establecimientos["evidencia_hidrica"].eq("SI")]
    productos.append(_guardar(
        _mapa_confirmados(cuenca, rios, municipios, confirmados),
        "04_establecimientos_confirmados_si", output_dir,
    ))
    productos.append(_guardar(
        _mapa_municipal(cuenca, rios, municipios, establecimientos,
                        "Concentración de establecimientos por municipio"),
        "05_conteo_municipal", output_dir,
    ))
    productos.append(_guardar(
        _mapa_localidades(cuenca, rios, municipios, establecimientos,
                          "Concentración de establecimientos por localidad"),
        "06_conteo_localidad", output_dir,
    ))

    estrato_col = "Descripcion estrato personal ocupado"
    for numero, estrato in enumerate(ESTRATOS_DENUE, start=1):
        parte = establecimientos[establecimientos[estrato_col].eq(estrato)]
        slug = _slug(estrato)
        productos.append(_guardar(
            _mapa_municipal(cuenca, rios, municipios, parte,
                            f"Establecimientos de {estrato} por municipio"),
            f"07_{numero:02d}_{slug}_municipio", output_dir,
        ))
        productos.append(_guardar(
            _mapa_localidades(cuenca, rios, municipios, parte,
                              f"Establecimientos de {estrato} por localidad"),
            f"07_{numero:02d}_{slug}_localidad", output_dir,
        ))

    # Un mapa por cada municipio poblano disponible en la capa de cuenca.
    for numero, (_, municipio) in enumerate(
        municipios.sort_values("nom_mun").iterrows(), start=1
    ):
        area = gpd.GeoDataFrame([municipio], geometry="geometry", crs=municipios.crs)
        puntos_municipio = establecimientos[
            establecimientos.geometry.within(municipio.geometry)
        ]
        rios_municipio = gpd.clip(rios, area)
        figura = _mapa_establecimientos(area, rios_municipio, area, puntos_municipio)
        figura.update_layout(title={
            "text": f"{municipio['nom_mun']}: establecimientos con potencial hídrico",
            "x": 0.5, "xanchor": "center",
        })
        productos.append(_guardar(
            figura, f"08_{numero:02d}_municipio_{_slug(municipio['nom_mun'])}", output_dir
        ))

    inventario = pd.DataFrame(productos)
    inventario.to_csv(output_dir / "inventario_mapas.csv", index=False, encoding="utf-8-sig")
    establecimientos.to_file(
        output_dir.parent / "layers" / "establecimientos_hidricos_distancia.gpkg",
        layer="establecimientos_hidricos_distancia", driver="GPKG",
    )
    return productos, establecimientos
