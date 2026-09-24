"""Genera y compila una presentacion Beamer con los mapas de la cuenca."""

from pathlib import Path
import subprocess


def _latex(texto):
    reemplazos = {
        "\\": r"\textbackslash{}", "&": r"\&", "%": r"\%",
        "$": r"\$", "#": r"\#", "_": r"\_", "{": r"\{", "}": r"\}",
    }
    return "".join(reemplazos.get(c, c) for c in str(texto))


def crear_presentacion(
    root,
    output,
    inventario,
    resumen,
    establecimientos,
    nombre_base="presentacion_cuenca_puebla",
    subtitulo="Cuenca del Alto Atoyac, Puebla",
):
    docs = Path(root) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    tex = docs / f"{nombre_base}.tex"
    pdf = docs / f"{nombre_base}.pdf"

    frames = []
    titulos = {
        "01_cuenca_informacion_hidrica": "Cuenca e información hídrica",
        "02_cuenca_establecimientos_hidricos": "Universo hídrico dentro de la cuenca",
        "03_establecimientos_distancia_rio": "Cercanía de establecimientos a la red",
        "04_establecimientos_confirmados_si": "Confirmación de campo MH y evidencia DENUE",
        "05_conteo_municipal": "Concentración por municipio",
        "06_conteo_localidad": "Concentración por localidad",
    }
    for producto in inventario:
        png = producto.get("png")
        if png is None or not Path(png).exists():
            continue
        nombre = producto["nombre"]
        titulo = titulos.get(nombre, nombre.replace("_", " ").title())
        relativo = Path(png).resolve().relative_to(docs.resolve().parent).as_posix()
        frames.append(
            "\\begin{frame}{" + _latex(titulo) + "}\n"
            "\\centering\n"
            "\\includegraphics[width=0.96\\textwidth,height=0.82\\textheight,keepaspectratio]{../"
            + relativo + "}\n"
            "\\end{frame}\n"
        )

    por_evidencia = establecimientos["evidencia_hidrica"].value_counts()
    si = int(por_evidencia.get("SI", 0))
    revisar = int(por_evidencia.get("REVISAR", 0))
    fuente_si = establecimientos.loc[
        establecimientos["evidencia_hidrica"].eq("SI"),
        "fuente_evidencia_hidrica",
    ]
    si_campo = int(fuente_si.eq("MH_TRABAJO_CAMPO").sum())
    si_denue = int(fuente_si.eq("REGLAS_DENUE").sum())
    total = max(len(establecimientos), 1)
    estrato = establecimientos["Descripcion estrato personal ocupado"].fillna("")
    pequenas_05 = int(estrato.eq("0 a 5 personas").sum())
    pequenas_610 = int(estrato.eq("6 a 10 personas").sum())
    por_municipio = establecimientos.groupby("Municipio").size().sort_values(ascending=False)
    por_localidad = establecimientos.groupby(
        ["Municipio", "localidad"]
    ).size().sort_values(ascending=False)
    filas_municipio = "\n".join(
        f"{_latex(nombre)} & {int(n):,}\\\\"
        for nombre, n in por_municipio.head(10).items()
    )
    filas_localidad = "\n".join(
        f"{_latex(loc)} ({_latex(mun)}) & {int(n):,}\\\\"
        for (mun, loc), n in por_localidad.head(10).items()
    )
    confirmados = establecimientos[
        establecimientos["evidencia_hidrica"].eq("SI")
    ]
    ubicaciones_si = confirmados.groupby(
        ["Municipio", "localidad"]
    ).size().sort_values(ascending=False)
    filas_si = "\n".join(
        f"{_latex(loc)} ({_latex(mun)}) & {int(n)}\\\\"
        for (mun, loc), n in ubicaciones_si.items()
    ) or "Sin casos & 0\\\\"
    cercanos = confirmados.sort_values("distancia_rio_m").head(8)
    filas_cercanos = "\n".join(
        f"{_latex(r.nom_est)} & {_latex(r.localidad)} & "
        f"{float(r.distancia_rio_m):.0f} m\\\\"
        for r in cercanos.itertuples()
    ) or "Sin casos & -- & --\\\\"
    todos_scian = bool(int(resumen.get("modo_todos_scian", 0)))
    if todos_scian:
        regla_lavanderias = (
            "Se cartografían todos los SCIAN descargados; la evidencia hídrica "
            "sólo se usa para diferenciarlos visualmente."
        )
        titulo_principal = "Universo sectorial completo de establecimientos"
        etiqueta_municipios = "Registros SCIAN en municipios solicitados"
        etiqueta_cuenca = "Registros SCIAN dentro de la cuenca"
        universo_nombre = "universo SCIAN dentro de la cuenca"
    elif int(resumen.get("regla_lavanderias_estricta", 0)):
        regla_lavanderias = (
            "SCIAN 812210 sólo entra con una señal adicional de actividad "
            "textil, mezclilla, proceso húmedo, producción o maquila."
        )
        titulo_principal = "Establecimientos textiles con relevancia hídrica"
        etiqueta_municipios = "Universo hídrico en municipios solicitados"
        etiqueta_cuenca = "Universo hídrico dentro de la cuenca"
        universo_nombre = "universo hídrico dentro de la cuenca"
    else:
        regla_lavanderias = (
            "Todo SCIAN 812210 entra como REVISAR, aun sin señal industrial explícita."
        )
        titulo_principal = "Establecimientos textiles con relevancia hídrica"
        etiqueta_municipios = "Universo hídrico en municipios solicitados"
        etiqueta_cuenca = "Universo hídrico dentro de la cuenca"
        universo_nombre = "universo hídrico dentro de la cuenca"
    analisis = rf"""
\begin{{frame}}{{Estructura de las unidades pequeñas}}
\begin{{itemize}}
\item De los {len(establecimientos):,} establecimientos del {universo_nombre},
{pequenas_05:,} ({100 * pequenas_05 / total:.1f}\%) reportan de 0 a 5 personas.
\item Otros {pequenas_610:,} ({100 * pequenas_610 / total:.1f}\%) reportan de 6 a 10 personas.
\item La estructura observada está dominada por microunidades; el conteo no representa empleo total ni volumen de agua.
\item Los registros MH sin estrato DENUE se conservan, pero no se asignan artificialmente a un tamaño.
\end{{itemize}}
\end{{frame}}
\begin{{frame}}{{Municipios con mayor número de establecimientos}}
\centering\small
\begin{{tabular}}{{lr}}\toprule Municipio & Establecimientos\\\midrule
{filas_municipio}
\bottomrule\end{{tabular}}
\end{{frame}}
\begin{{frame}}{{Localidades con mayor número de establecimientos}}
\centering\scriptsize
\begin{{tabular}}{{lr}}\toprule Localidad (municipio) & Establecimientos\\\midrule
{filas_localidad}
\bottomrule\end{{tabular}}
\end{{frame}}
\begin{{frame}}{{Dónde se localizan los establecimientos SI}}
\centering\scriptsize
\begin{{tabular}}{{lr}}\toprule Localidad (municipio) & Casos SI\\\midrule
{filas_si}
\bottomrule\end{{tabular}}
\vfill
De los {si} casos SI, {si_campo} provienen de trabajo de campo MH y
{si_denue} de evidencia explícita en DENUE. La fuente queda identificada por registro.
\end{{frame}}
\begin{{frame}}{{Casos SI más cercanos a la red hidrográfica}}
\centering\scriptsize
\begin{{tabular}}{{p{{0.48\textwidth}}p{{0.27\textwidth}}r}}\toprule
Establecimiento & Localidad & Distancia\\\midrule
{filas_cercanos}
\bottomrule\end{{tabular}}
\vfill
La cercanía es un indicador espacial de atención, no evidencia de descarga al cauce.
\end{{frame}}
"""
    contenido = r"""\documentclass[aspectratio=169]{beamer}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-nodecimaldot]{babel}
\usepackage{graphicx}
\usepackage{booktabs}
\usetheme{default}
\definecolor{AtoyacBlue}{HTML}{2166AC}
\definecolor{AtoyacRed}{HTML}{B2182B}
\setbeamercolor{structure}{fg=AtoyacBlue}
\setbeamercolor{frametitle}{fg=white,bg=AtoyacBlue}
\setbeamertemplate{navigation symbols}{}
\title{""" + _latex(titulo_principal) + r"""}
\subtitle{""" + _latex(subtitulo) + r"""}
\author{Procesamiento reproducible con DENUE 2026}
\date{11 de septiembre de 2026}
\begin{document}
\begin{frame}\titlepage\end{frame}
\begin{frame}{Universos construidos}
\centering
\begin{tabular}{lr}\toprule
Producto & Registros\\\midrule
DENUE estatal descargado & """ + f"{resumen['denue_estatal_descargado']:,}" + r"""\\
Universo textil en municipios solicitados & """ + f"{resumen['universo_textil_municipios']:,}" + r"""\\
""" + _latex(etiqueta_municipios) + " & " + f"{resumen['universo_hidrico_municipios']:,}" + r"""\\
""" + _latex(etiqueta_cuenca) + " & " + f"{resumen['universo_hidrico_dentro_cuenca']:,}" + r"""\\
Evidencia explícita SI dentro de cuenca & """ + f"{si:,}" + r"""\\
Evidencia REVISAR dentro de cuenca & """ + f"{revisar:,}" + r"""\\
Registros MH revisados & """ + f"{resumen.get('registros_mh_revisados', 0):,}" + r"""\\
Registros agregados gracias a MH & """ + f"{resumen.get('registros_mh_agregados', 0):,}" + r"""\\
\bottomrule\end{tabular}
\vfill
Los mapas muestran el recorte espacial real por el polígono de cuenca. Los HTML homónimos conservan hover y navegación interactiva.
\end{frame}
\begin{frame}{Criterio metodológico}
\begin{itemize}
\item Inclusión sectorial estructurada: SCIAN 313, 314 y 315.
\item """ + regla_lavanderias + r"""
\item Señales positivas: nombre y razón social; descripción SCIAN sólo para exclusiones.
\item Los registros MH son SI por trabajo de campo y tienen prioridad sobre la decisión automática.
\item Los demás registros usan SI, REVISAR o SIN EVIDENCIA según reglas DENUE auditables.
\item La distancia se calcula en metros a la red hidrográfica recortada por la cuenca.
\item La agregación por localidad usa el centro medio de sus establecimientos porque no se proporcionaron polígonos de localidad.
\end{itemize}
\end{frame}
""" + analisis + "\n".join(frames) + r"""
\begin{frame}{Notas de interpretación}
\begin{itemize}
\item La concentración representa conteos DENUE, no tasas ni intensidad de descarga.
\item Cercanía a un río no demuestra conexión hidráulica, descarga o causalidad ambiental.
\item El tamaño corresponde al estrato de personal ocupado reportado por DENUE.
\item Los mapas municipales usan polígonos recortados por la cuenca; los de localidad son agregaciones puntuales.
\end{itemize}
\end{frame}
\end{document}
"""
    tex.write_text(contenido, encoding="utf-8")

    comando = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex.name]
    for _ in range(2):
        proceso = subprocess.run(comando, cwd=docs, capture_output=True, text=True)
        if proceso.returncode:
            print("ADVERTENCIA: no se pudo compilar la presentación LaTeX.")
            print(proceso.stdout[-2000:])
            break
    if pdf.exists():
        print(f"Presentación generada: {pdf}")
    return tex, pdf
