"""Genera reporte, atlas y presentación LaTeX finales de Parte 2."""

from importlib import import_module
import json
from pathlib import Path
import re

import pandas as pd

comun = import_module("200_parte2_comun")


def tex(valor):
    if pd.isna(valor):
        return "--"
    s = str(valor)
    reemplazos = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$",
        "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
        "~": r"\textasciitilde{}", "^": r"\textasciicircum{}",
    }
    return "".join(reemplazos.get(c, c) for c in s)


def imagen(nombre, ancho=r"0.92\textwidth", caption=None):
    cap = f"\\caption{{{caption}}}" if caption else ""
    return f"""\\begin{{figure}}[H]
\\centering
\\includegraphics[width={ancho}]{{{nombre}.png}}
{cap}
\\end{{figure}}"""


def main():
    comun.asegurar_directorios()
    seleccion = pd.read_csv(comun.OUT / "05_seleccion/seleccion_escenarios.csv")
    principal = seleccion[seleccion.rol.eq("PRINCIPAL")].iloc[0]
    perfiles = pd.read_csv(comun.OUT / "07_perfiles/perfiles_clusters.csv")
    ficha = pd.read_csv(comun.OUT / "11_cierre/fichas_resumen_clusters.csv")
    sensibilidad = pd.read_csv(comun.OUT / "11_cierre/sensibilidad_coexistencia.csv")
    ruido = pd.read_csv(comun.OUT / "11_cierre/comparacion_clusters_ruido.csv")
    similares = pd.read_csv(comun.OUT / "11_cierre/pares_clusters_similares.csv")
    with open(comun.OUT / "11_cierre/resumen_mega_cluster.json", encoding="utf-8") as fh:
        mega = json.load(fh)

    clusters = ficha[ficha.grupo_espacial.ne("RUIDO_DISPERSO")].sort_values("cluster")
    ruido_ficha = ficha[ficha.grupo_espacial.eq("RUIDO_DISPERSO")].iloc[0]
    filas_clusters = []
    for r in clusters.itertuples():
        filas_clusters.append(
            f"{int(r.cluster)} & {int(r.n_dentro_cuenca)} & {tex(r.municipio_principal)} & "
            f"{r.pct_lavanderia_tintoreria:.1f} & {r.pct_manufactura_textil:.1f} & "
            f"{r.persistencia_media:.2f} & {tex(str(r.tipo_coexistencia_descriptivo).replace('_', ' '))} \\\\"
        )
    tabla_clusters = "\n".join(filas_clusters)

    top_ruido = ruido.reindex(ruido.diferencia_agrupado_menos_ruido.abs().sort_values(ascending=False).index).head(8)
    tabla_ruido = "\n".join(
        f"{tex(r.senal)} & {100*r.prevalencia_agrupado:.1f} & {100*r.prevalencia_ruido:.1f} & "
        f"{100*r.diferencia_agrupado_menos_ruido:+.1f} & {r.p_ajustada_bh:.3g} \\\\"
        for r in top_ruido.itertuples()
    )
    tabla_similares = "\n".join(
        f"{tex(r.cluster_a)} & {tex(r.cluster_b)} & {r.distancia_perfil:.3f} \\\\"
        for r in similares.head(10).itertuples()
    )

    reporte = rf"""\documentclass[11pt]{{article}}
\usepackage[utf8]{{inputenc}}
\usepackage[T1]{{fontenc}}
\usepackage[spanish,es-nodecimaldot]{{babel}}
\usepackage{{geometry,graphicx,booktabs,longtable,array,float,xcolor,hyperref,caption}}
\geometry{{margin=2.2cm}}
\graphicspath{{{{../../../outputs/parte_2/13_figuras_finales/}}{{../../../outputs/parte_2/12_atlas/}}}}
\definecolor{{azul}}{{HTML}}{{2166AC}}
\hypersetup{{colorlinks=true,linkcolor=azul,urlcolor=azul}}
\title{{Parte 2: concentraciones territoriales y composición del universo sectorial ampliado}}
\author{{Proyecto Cuenca del Alto Atoyac}}
\date{{Septiembre de 2026}}
\begin{{document}}
\maketitle
\begin{{abstract}}
Este reporte identifica concentraciones territoriales del universo ampliado de actividades textiles, confección y servicios de lavandería/tintorería potencialmente relevantes. La detección utiliza 4,365 establecimientos para evitar artefactos de borde y la interpretación se concentra en 4,010 unidades dentro de la cuenca. La solución espacial se construye exclusivamente con coordenadas; la composición económica se incorpora después. Se documentan robustez, ruido, perfiles multilabel, sobrerrepresentación, coexistencia de lavanderías y manufactura, y similitud productiva entre clusters.
\end{{abstract}}
\tableofcontents

\section{{Preguntas y respuestas principales}}
\begin{{enumerate}}
\item \textbf{{¿Dónde se concentra la actividad?}} La solución fija detecta 22 clusters en el universo municipal; 18 tienen establecimientos dentro de la cuenca. El cluster 20, en el entorno metropolitano de Puebla, reúne 1,997 establecimientos.
\item \textbf{{¿Son robustas las concentraciones?}} La solución principal alcanza ARI {principal.ari_top5_mismo_metodo:.3f} frente a configuraciones próximas y {principal.ari_perturbacion_25m:.3f} ante perturbaciones de 25 m. La probabilidad media de pertenencia es {principal.probabilidad_media:.3f}.
\item \textbf{{¿Qué contienen?}} Existen perfiles manufactureros y mixtos. Las fichas y tablas describen SCIAN, confección, telas, acabado, maquila, lavandería y señales húmedas/secas sin exigir categorías exclusivas.
\item \textbf{{¿Qué está sobrerrepresentado?}} Los rasgos se destacan sólo cuando cumplen simultáneamente conteo mínimo, prevalencia, lift y significancia ajustada.
\item \textbf{{¿Las lavanderías forman clusters propios?}} Ninguno de los seis escenarios principal, de referencia y sensibilidad genera un cluster interior con al menos 80\% de lavanderías. En la solución principal hay 12 clusters predominantemente manufactureros y 6 de coexistencia mixta.
\item \textbf{{¿Hay perfiles semejantes en lugares distintos?}} Sí. La similitud se calcula posteriormente mediante señales y composición SCIAN, sin introducir ubicación en esta segunda representación.
\item \textbf{{¿Qué distingue la dispersión?}} Dentro de la cuenca, 578 establecimientos permanecen como actividad dispersa. Presentan relativamente más señales de proceso seco y manufactura, mientras la actividad agrupada presenta mayor prevalencia de lavanderías; las diferencias no implican causalidad.
\end{{enumerate}}

\section{{Universo, trazabilidad y efecto de borde}}
El universo de detección contiene 4,365 establecimientos y el de interpretación 4,010. Los 355 establecimientos externos se preservan exclusivamente para no cortar concentraciones que continúan más allá del límite de la cuenca. La llave \texttt{{d\_llave}} es única y todas las coordenadas son válidas.
{imagen('01_universos_borde', caption='Universo municipal de detección y universo interior de interpretación.')}

\section{{Diseño metodológico}}
Las coordenadas se reproyectaron de EPSG:4326 a EPSG:32614. Se evaluaron 24 configuraciones DBSCAN, 30 HDBSCAN y tres OPTICS; KDE y hexágonos se utilizaron como diagnósticos. SCIAN, señales textuales, evidencia hídrica y personal ocupado no participaron en la construcción ni selección de clusters.

La solución principal ya fijada es HDBSCAN con \texttt{{min\_cluster\_size=10}}, \texttt{{min\_samples=20}} y selección EOM. Produce {int(principal.n_clusters)} clusters, {int(principal.n_ruido)} registros municipales dispersos ({principal.pct_ruido:.1f}\%) y un cluster máximo de {int(principal.tam_max)} establecimientos. DBSCAN y las configuraciones restantes funcionan como sensibilidad, no como una nueva optimización.
{imagen('05_robustez_escenarios', caption='Comparación exclusivamente espacial y estabilidad de las configuraciones.')}

\section{{Geografía de la solución principal}}
{imagen('02_clusters_principales', caption='Clusters que intersectan la cuenca y actividad dispersa.')}
La solución preserva una categoría analítica de actividad dispersa y no obliga a asignar todos los establecimientos a una concentración. Un cluster cruza el límite de la cuenca: contiene 48 establecimientos, ocho dentro y 40 fuera.
{imagen('11_efecto_borde', caption='Composición interior y exterior de los clusters que intersectan la cuenca.')}

\section{{Persistencia territorial}}
La persistencia combina correspondencia Jaccard con la solución de referencia y escenarios próximos. Se distingue entre núcleos robustos, membresías estables y agrupaciones sensibles. Esta medida expresa estabilidad entre especificaciones, no certeza ontológica.
{imagen('03_persistencia_territorial', caption='Persistencia de la membresía territorial.')}

\section{{Mega-cluster 20}}
El cluster 20 contiene {mega['n_total']:,} establecimientos, abarca {mega['n_municipios']} municipios y {mega['n_localidades']} localidades, y alcanza persistencia media {mega['persistencia_media']:.3f}. El diagnóstico interno identifica {mega['subnucleos_diagnosticos']} subnúcleos exploratorios, con {mega['pct_ruido_diagnostico_interno']:.1f}\% no asignado en esa exploración local. Los {mega['hexagonos_ocupados_250m']} hexágonos ocupados de 250 m alcanzan un máximo de {mega['max_establecimientos_hexagono']} establecimientos. Esto evidencia heterogeneidad interna, pero no invalida ni reemplaza la membresía principal.
{imagen('10_diagnostico_mega_cluster', caption='Subestructura diagnóstica del mega-cluster, sin subdivisión operativa.')}

\section{{Composición económica de los clusters}}
\begin{{longtable}}{{r r p{{3.0cm}} r r r p{{3.4cm}}}}
\toprule
Cluster & $n$ interior & Municipio principal & Lav. \% & Manuf. \% & Persist. & Tipo descriptivo\\
\midrule\endhead
{tabla_clusters}
\bottomrule
\end{{longtable}}
{imagen('06_composicion_multilabel', caption='Señales multilabel; los porcentajes no deben sumar 100\\%.')}

\section{{Lavanderías y manufactura}}
La clasificación productiva se aplicó después del clustering. Ningún cluster interior alcanza 80\% de lavanderías en la solución principal. Se observan 12 concentraciones manufactureras y seis estructuras mixtas. Este patrón persiste en los seis escenarios seleccionados: el máximo porcentaje de lavanderías por cluster es siempre menor de 80\%. La coexistencia espacial no demuestra relación empresarial, productiva ni hidráulica.
{imagen('04_tipos_productivos_clusters', caption='Lectura posterior de manufactura y lavanderías.')}

\section{{Sobrerrepresentación}}
Se calcularon conteo, prevalencia interna y global, diferencia, lift, $\log_2$(lift), odds ratio, intervalo de confianza, Fisher y ajuste Benjamini--Hochberg. Un rasgo sólo se presenta como distintivo si cuenta con al menos cinco observaciones, prevalencia interna de 5\%, lift de 1.25 y $p$ ajustada no mayor de 0.05.
{imagen('07_rasgos_distintivos', caption='Rasgos que superan simultáneamente los criterios conservadores.')}

\section{{Clusters frente a actividad dispersa}}
\begin{{table}}[H]\centering
\begin{{tabular}}{{lrrrr}}\toprule
Señal & Agrupado \% & Disperso \% & Diferencia pp & $p$ BH\\\midrule
{tabla_ruido}
\bottomrule\end{{tabular}}
\caption{{Mayores diferencias absolutas entre actividad agrupada y dispersa.}}
\end{{table}}
{imagen('08_clusters_vs_ruido', caption='Diferencias de prevalencia; ruido no se interpreta como un cluster equivalente.')}

\section{{Tipología de perfiles de clusters espaciales}}
La comparación productiva utiliza distancia coseno para señales y Jensen--Shannon para composición SCIAN. La ubicación no entra en esta etapa. La tipología es una clasificación posterior de perfiles, no una redefinición territorial.
\begin{{table}}[H]\centering
\begin{{tabular}}{{llr}}\toprule Cluster A & Cluster B & Distancia\\\midrule
{tabla_similares}
\bottomrule\end{{tabular}}
\caption{{Diez pares de perfiles más similares.}}
\end{{table}}
{imagen('09_similitud_perfiles', caption='Distancia productiva entre clusters territorialmente distintos.')}

\section{{Limitaciones}}
DENUE puede omitir actividad informal o domiciliaria; las coordenadas no garantizan precisión predial; SCIAN 812210 no distingue lavandería comercial de industrial; las señales textuales son indicios y pueden estar correlacionadas. La concentración espacial no demuestra encadenamiento productivo, uso de agua, descarga o impacto ambiental.

\section{{Conclusiones}}
La cuenca contiene un sistema territorial desigual: un gran continuo metropolitano, concentraciones manufactureras menores, estructuras mixtas y actividad dispersa. La estabilidad espacial es alta para la solución principal, aunque algunos grupos pequeños son sensibles. Las lavanderías no forman una concentración interior casi exclusiva bajo ninguno de los escenarios seleccionados; aparecen principalmente dentro de territorios mixtos o junto con manufactura. La Parte 2 responde dónde están las concentraciones y qué contienen. La relación con ríos, cauces, intercepción o tratamiento queda explícitamente reservada para la Parte 3.

\appendix
\section{{Atlas de clusters}}
El atlas completo se entrega como documento separado: \texttt{{docs/parte\_2/atlas/atlas\_clusters.pdf}}.
\end{{document}}
"""

    atlas_frames = []
    for r in ficha.sort_values("cluster").itertuples():
        ruido_es = r.grupo_espacial == "RUIDO_DISPERSO"
        nombre = "ruido_disperso" if ruido_es else f"cluster_{int(r.cluster):03d}"
        titulo = "Actividad dispersa" if ruido_es else f"Cluster {int(r.cluster):03d}"
        total = int(r.n_dentro_cuenca if pd.isna(r.n_total_cluster) else r.n_total_cluster)
        fuera = 0 if pd.isna(r.n_fuera_cuenca) else int(r.n_fuera_cuenca)
        area = "No aplica" if pd.isna(r.area_convexa_km2) else f"{r.area_convexa_km2:.2f} km$^2$"
        atlas_frames.append(rf"""
\section*{{{tex(titulo)}}}
\addcontentsline{{toc}}{{section}}{{{tex(titulo)}}}
\begin{{center}}\includegraphics[width=\textwidth]{{{nombre}.png}}\end{{center}}
\begin{{tabular}}{{p{{0.31\textwidth}}p{{0.62\textwidth}}}}
\toprule
Establecimientos & {int(r.n_dentro_cuenca)} dentro; {fuera} fuera; {total} total\\
Área convexa & {area}\\
Persistencia & {r.persistencia_media:.3f}\\
Municipio/localidad dominante & {tex(r.municipio_principal)} / {tex(r.localidad_principal)}\\
Lavandería / manufactura & {r.pct_lavanderia_tintoreria:.1f}\% / {r.pct_manufactura_textil:.1f}\%\\
Confección / maquila & {r.pct__actividad_confeccion:.1f}\% / {r.pct__maquila:.1f}\%\\
Húmedo / seco explícito & {r.pct__humedo_explicito:.1f}\% / {r.pct__proceso_seco_explicito:.1f}\%\\
Tipología de perfil & {tex(r.tipo_perfil) if not pd.isna(r.tipo_perfil) else 'No aplica'}\\
Rasgos distintivos & {tex(r.rasgos_distintivos)}\\
Advertencia & {'Grupo comparativo; no es un cluster territorial.' if ruido_es else 'Perfil descriptivo multilabel; no prueba relaciones productivas ni ambientales.'}\\
\bottomrule
\end{{tabular}}
\clearpage
""")
    atlas = rf"""\documentclass[10pt]{{article}}
\usepackage[utf8]{{inputenc}}\usepackage[T1]{{fontenc}}\usepackage[spanish]{{babel}}
\usepackage{{geometry,graphicx,booktabs,hyperref}}
\geometry{{margin=1.7cm}}\graphicspath{{{{../../../outputs/parte_2/12_atlas/}}}}
\title{{Atlas de clusters espaciales — Parte 2}}\author{{Proyecto Cuenca del Alto Atoyac}}\date{{Septiembre de 2026}}
\begin{{document}}\maketitle
\noindent Las fichas utilizan la solución espacial principal fija. La composición económica se calcula posteriormente. \texttt{{RUIDO\_DISPERSO}} es un grupo comparativo, no un cluster equivalente.\tableofcontents\clearpage
{''.join(atlas_frames)}
\end{{document}}"""

    presentacion = rf"""\documentclass[aspectratio=169]{{beamer}}
\usepackage[utf8]{{inputenc}}\usepackage[T1]{{fontenc}}\usepackage[spanish]{{babel}}
\usepackage{{graphicx,booktabs}}
\usetheme{{Madrid}}\usecolortheme{{dolphin}}
\graphicspath{{{{../../../outputs/parte_2/13_figuras_finales/}}{{../../../outputs/parte_2/12_atlas/}}}}
\title{{Parte 2: concentraciones territoriales y composición}}\subtitle{{Universo sectorial ampliado en la cuenca del Alto Atoyac}}\author{{Proyecto Cuenca del Alto Atoyac}}\date{{Septiembre de 2026}}
\begin{{document}}
\frame{{\titlepage}}
\begin{{frame}}{{Siete preguntas de Parte 2}}\small
¿Dónde están las concentraciones? ¿Son robustas? ¿Qué contienen? ¿Qué está sobrerrepresentado? ¿Las lavanderías forman estructuras propias? ¿Qué clusters tienen perfiles similares? ¿Cómo se diferencia la dispersión?
\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{01_universos_borde.png}}\end{{frame}}
\begin{{frame}}{{Principio metodológico}}\Large\centering Dónde existen concentraciones\\[1em]$\downarrow$\\[1em]Qué contienen esas concentraciones\vfill\normalsize Las señales económicas nunca redefinen la membresía espacial.\end{{frame}}
\begin{{frame}}{{Batería espacial}}\begin{{itemize}}\item 24 DBSCAN, 30 HDBSCAN y 3 OPTICS.\item KDE y hexágonos como diagnóstico.\item EPSG:32614 y metros.\item Perturbaciones reproducibles de 25 m.\end{{itemize}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{05_robustez_escenarios.png}}\end{{frame}}
\begin{{frame}}{{Solución principal}}\begin{{columns}}\column{{.34\textwidth}}\Large HDBSCAN\\[.5em]\normalsize 22 clusters municipales\\18 dentro de cuenca\\584 dispersos municipales\\ARI perturbación: {principal.ari_perturbacion_25m:.3f}\column{{.66\textwidth}}\centering\includegraphics[height=.62\textheight]{{02_clusters_principales.png}}\end{{columns}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{03_persistencia_territorial.png}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{10_diagnostico_mega_cluster.png}}\end{{frame}}
\begin{{frame}}{{No se subdivide automáticamente}}\begin{{itemize}}\item 1,997 establecimientos.\item Persistencia media {mega['persistencia_media']:.3f}.\item {mega['subnucleos_diagnosticos']} subnúcleos exploratorios.\item La subestructura informa la lectura interna, no sustituye el cluster principal.\end{{itemize}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{06_composicion_multilabel.png}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{04_tipos_productivos_clusters.png}}\end{{frame}}
\begin{{frame}}{{Resultado robusto de coexistencia}}\Large\centering Ninguno de los seis escenarios seleccionados produce un cluster interior con $\geq80\%$ de lavanderías.\\[1em]\normalsize Solución principal: 12 concentraciones manufactureras y 6 mixtas.\\[1em]\alert{{Coexistencia espacial no implica relación empresarial, productiva o hidráulica.}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{07_rasgos_distintivos.png}}\end{{frame}}
\begin{{frame}}{{Criterio conservador}}\begin{{itemize}}\item Al menos cinco observaciones.\item Prevalencia interna mínima de 5\%.\item Lift mínimo 1.25.\item Fisher con ajuste Benjamini--Hochberg.\item Se interpreta efecto relativo junto con tamaño e incertidumbre.\end{{itemize}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{08_clusters_vs_ruido.png}}\end{{frame}}
\begin{{frame}}{{El ruido no es otro cluster}}\begin{{itemize}}\item 578 establecimientos dispersos dentro de la cuenca.\item Relativamente más manufactura y proceso seco explícito.\item Relativamente menos lavanderías que la actividad agrupada.\item La etiqueta depende de la escala espacial seleccionada.\end{{itemize}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{09_similitud_perfiles.png}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{cluster_020.png}}\end{{frame}}
\begin{{frame}}[plain]\centering\includegraphics[width=.96\paperwidth,height=.94\paperheight,keepaspectratio]{{11_efecto_borde.png}}\end{{frame}}
\begin{{frame}}{{Conclusiones}}\begin{{itemize}}\item La geografía combina un gran continuo metropolitano y concentraciones menores.\item La solución es estable, aunque algunos grupos pequeños son sensibles.\item Las lavanderías aparecen en estructuras mixtas, no en clusters interiores casi exclusivos.\item Los perfiles productivos se repiten en territorios distintos.\item La actividad dispersa tiene una composición parcialmente diferente.\end{{itemize}}\end{{frame}}
\begin{{frame}}{{Límites}}\begin{{itemize}}\item DENUE no es un censo de procesos ni descargas.\item SCIAN 812210 no separa lavandería comercial e industrial.\item Concentración no implica encadenamiento productivo o impacto ambiental.\item La solución principal organiza el análisis; no es la única geografía posible.\end{{itemize}}\end{{frame}}
\begin{{frame}}{{Transición a Parte 3}}\Large\centering Parte 2 cerrada:\\dónde están las concentraciones y qué contienen.\\[1.2em]\normalsize Parte 3 estudiará posteriormente su relación con la red hidrográfica, intercepción y tratamiento.\end{{frame}}
\end{{document}}"""

    reporte_dir = comun.DOCS / "reporte"
    presentacion_dir = comun.DOCS / "presentacion"
    atlas_dir = comun.DOCS / "atlas"
    for d in [reporte_dir, presentacion_dir, atlas_dir]:
        d.mkdir(parents=True, exist_ok=True)
    (reporte_dir / "reporte_tecnico_parte_2.tex").write_text(reporte, encoding="utf-8")
    (presentacion_dir / "presentacion_parte_2.tex").write_text(presentacion, encoding="utf-8")
    (atlas_dir / "atlas_clusters.tex").write_text(atlas, encoding="utf-8")
    print("LaTeX generado: reporte, presentación y atlas.")


if __name__ == "__main__":
    main()
