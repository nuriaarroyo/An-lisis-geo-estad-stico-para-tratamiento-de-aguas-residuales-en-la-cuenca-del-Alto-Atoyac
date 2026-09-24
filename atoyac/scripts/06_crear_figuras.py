"""Figuras cartograficas para presentar los subconjuntos DENUE."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


COLORES = {
    "territorio": "#c8c8c8",
    "INCLUIR": "#2468a2",
    "REVISAR": "#f2a541",
    "SI": "#c62828",
}


def _estilo_mapa(ax, titulo):
    ax.set_title(titulo, fontsize=12, fontweight="bold")
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    ax.grid(color="#dddddd", linewidth=0.5, alpha=0.7)
    ax.set_aspect("equal", adjustable="datalim")


def crear_figuras(localidad, slug, territorio, resultados, capa_origen, output_dir):
    """Crea un resumen de cuatro paneles y tres mapas individuales."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    origen = gpd.read_file(capa_origen)
    ids_territorio = set(territorio["d_llave"].astype(str).str.strip())
    fondo = origen.loc[origen["id"].astype(str).str.strip().isin(ids_territorio)].copy()
    capas = {
        nombre: gpd.read_file(info["layer_path"])
        for nombre, info in resultados.items()
    }

    universo = capas["universo_textil"]
    incluir = universo.loc[universo["sector_textil"].eq("INCLUIR")]
    revisar = universo.loc[universo["sector_textil"].eq("REVISAR")]
    hidrico_sr = capas["textil_hidrico_si_revisar"]
    hidrico_si = capas["textil_hidrico_si"]

    paneles = [
        (universo, "#2468a2", f"Candidatos textiles (n={len(universo)})"),
        (incluir, "#2468a2", f"Inclusión preliminar (n={len(incluir)})"),
        (revisar, "#f2a541", f"Revisión sectorial (n={len(revisar)})"),
        (hidrico_sr, "#c62828", f"Evidencia hídrica: Sí + Revisar (n={len(hidrico_sr)})"),
    ]
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), constrained_layout=True)
    for ax, (capa, color, titulo) in zip(axes.flat, paneles):
        fondo.plot(ax=ax, color=COLORES["territorio"], markersize=5, alpha=0.35)
        if not capa.empty:
            capa.plot(ax=ax, color=color, markersize=18, alpha=0.85, edgecolor="white", linewidth=0.25)
        _estilo_mapa(ax, titulo)
    fig.suptitle(f"DENUE textil — {localidad}\nResultados preliminares para revisión", fontsize=16, fontweight="bold")
    fig.savefig(output_dir / f"{slug}_resumen_subconjuntos.png", dpi=300, bbox_inches="tight")
    plt.close(fig)

    mapas = {
        "universo_textil": (
            [(incluir, COLORES["INCLUIR"], "Incluir"), (revisar, COLORES["REVISAR"], "Revisar")],
            "Universo candidato textil",
        ),
        "textil_hidrico_si_revisar": (
            [
                (hidrico_sr.loc[hidrico_sr["evidencia_hidrica"].eq("REVISAR")], COLORES["REVISAR"], "Revisar"),
                (hidrico_si, COLORES["SI"], "Sí"),
            ],
            "Candidatos con señal hídrica",
        ),
        "textil_hidrico_si": ([(hidrico_si, COLORES["SI"], "Sí")], "Evidencia hídrica explícita"),
    }
    for nombre, (series, titulo) in mapas.items():
        fig, ax = plt.subplots(figsize=(9, 8), constrained_layout=True)
        fondo.plot(ax=ax, color=COLORES["territorio"], markersize=7, alpha=0.3)
        leyenda = [Line2D([0], [0], marker="o", color="none", markerfacecolor=COLORES["territorio"], markeredgecolor="none", label=f"DENUE de la localidad (n={len(fondo)})", markersize=7)]
        for capa, color, etiqueta in series:
            if not capa.empty:
                capa.plot(ax=ax, color=color, markersize=25, alpha=0.9, edgecolor="white", linewidth=0.3)
            leyenda.append(Line2D([0], [0], marker="o", color="none", markerfacecolor=color, markeredgecolor="white", label=f"{etiqueta} (n={len(capa)})", markersize=8))
        _estilo_mapa(ax, f"{titulo}\n{localidad}")
        ax.legend(handles=leyenda, loc="best", frameon=True, fontsize=9)
        fig.savefig(output_dir / f"{slug}_{nombre}.png", dpi=300, bbox_inches="tight")
        plt.close(fig)

