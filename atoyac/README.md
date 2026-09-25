# Análisis geo-estadístico para tratamiento de aguas residuales en la cuenca del Alto Atoyac

Proyecto de análisis territorial para identificar, comparar y caracterizar concentraciones de unidades económicas textiles, de confección y de lavandería/tintorería potencialmente relevantes dentro de la cuenca del Alto Atoyac, Puebla.

El repositorio transforma registros económicos y fuentes territoriales en un sistema auditable de universos, concentraciones espaciales, perfiles productivos e incertidumbre. Su propósito es indicar **dónde investigar primero** y qué debe verificarse en cada territorio antes de discutir infraestructura de saneamiento.

> **Alcance:** concentración espacial no significa contaminación; proximidad a un río no demuestra una descarga; un cluster no es una zona de servicio; lavandería/tintorería sectorial no equivale a lavandería industrial verificada; priorización territorial no constituye una recomendación de colector.

## Estado actual

El proyecto comprende dos fases analíticas y una transición hacia una etapa hidráulica futura:

1. **Construcción y auditoría del universo económico.** Recortes territoriales, filtros SCIAN y textuales, reglas amplia y estricta, integración de la fuente de campo MH y comparación con universos legacy de Huejotzingo y Santa Ana Xalmimilulco.
2. **Análisis regional de concentraciones.** Detección espacial sobre el universo sectorial ampliado, comparación de DBSCAN, HDBSCAN y OPTICS, selección reproducible, análisis de robustez, perfiles productivos, sobrerrepresentación, ruido y subnúcleos exploratorios.
3. **Siguiente etapa propuesta.** Integrar las concentraciones con hidrología, relieve, drenaje, captadores, descargas conocidas y plantas de tratamiento para formular y verificar rutas potenciales de los residuos líquidos hacia los cuerpos de agua.

La solución espacial está congelada para el cierre analítico. Los subnúcleos y perfiles posteriores no modifican silenciosamente la membresía principal.

## Resultados principales

| Elemento | Resultado |
|---|---:|
| Registros estatales iniciales acotados por SCIAN | 15,956 |
| Universo sectorial usado para detección y control de borde | 4,365 |
| Establecimientos dentro de la cuenca para interpretación | 4,010 |
| Configuraciones de clustering evaluadas | 57 |
| Solución seleccionada | HDBSCAN, `min_cluster_size=10`, `min_samples=20`, EOM |
| Clusters en el universo de detección | 22 |
| Clusters que intersectan la cuenca | 18 |
| Ruido en el universo de detección | 584 (13.38 %) |
| Cluster mayor | 1,997 establecimientos |

La configuración seleccionada obtuvo el mayor puntaje bajo la regla operativa documentada (`0.963`), pero existen configuraciones HDBSCAN prácticamente equivalentes (`0.962`). Por ello se utiliza como referencia reproducible, no como una geografía verdadera única.

Entre los territorios analizados destacan:

- **Santa Ana Xalmimilulco:** concentración de confección, maquila y mezclilla/pantalón.
- **Huejotzingo:** coexistencia de manufactura y actividades de lavandería/tintorería sectorial.
- **San Rafael Ixtapalucan y San Miguel Tianguistenco:** especialización relativa en tejido e hilado.
- **San Martín Texmelucan, San Rafael Tlanalapan y Santa María Moyotzingo:** núcleos diferentes dentro de un sistema territorial relacionado.
- **San Miguel Xoxtla–Coronango:** concentración manufacturera que requiere validar continuidad funcional e hidráulica.
- **Amozoc:** núcleos pequeños con señales mixtas y necesidad de verificación focal.
- **Puebla–Cholula–Cuautlancingo:** continuo metropolitano extenso y heterogéneo, descrito mediante 18 subnúcleos exploratorios sin reemplazar la membresía principal.

## Fuentes y universos

Las fuentes principales son:

- **DENUE/INEGI:** identificadores, actividad económica declarada y coordenadas.
- **Cuenca del Alto Atoyac:** polígono hidrológico adoptado para interpretación.
- **Marco municipal y red hidrográfica:** contexto administrativo e hídrico regional.
- **Fuente MH:** investigación de campo de Mary Helen Figueroa y Mayra Jaqueline Ramírez, conservada como fuente independiente y vinculada con IDs DENUE cuando fue posible.
- **Productos legacy:** tablas y auditorías de la fase inicial en Xalmimilulco y Huejotzingo.

Se construyeron cinco modalidades regionales:

| Modalidad | Dentro de cuenca | Uso |
|---|---:|---|
| Amplia + MH | 1,717 | Cobertura amplia con evidencia de campo. |
| Amplia DENUE | 1,679 | Sensibilidad alta sin fuente MH. |
| Estricta + MH | 510 | Priorización con señales más directas y fuente MH. |
| Estricta DENUE | 469 | Contraste restrictivo basado en DENUE. |
| Sectorial ampliada | 4,010 | Denominador principal del análisis de concentraciones. |

La modalidad estricta reduce ambigüedad, pero puede excluir operaciones industriales reales cuyo nombre no declara procesos húmedos. El universo sectorial se conserva para no perder esas unidades antes de la validación territorial.

## Metodología resumida

```text
DENUE + territorio + hidrografía + MH
                  │
                  ▼
        universo sectorial auditable
                  │
                  ▼
   geometrías métricas y control de borde
                  │
                  ▼
 diagnóstico multiescala + 57 escenarios
                  │
                  ▼
 solución HDBSCAN + sensibilidad + ruido
                  │
                  ▼
 perfiles productivos y evidencia hídrica
                  │
                  ▼
 concentraciones y zonas para validación
                  │
                  ▼
 etapa futura: hidrología + relieve + drenaje
 + captadores + descargas + tratamiento
```

El clustering utiliza exclusivamente coordenadas proyectadas en **EPSG:32614**. Los atributos productivos se incorporan después de fijar la geografía. La robustez se estudia mediante escenarios alternativos, ARI, Jaccard, persistencia de membresía, efecto de borde y perturbaciones posicionales.

Las pruebas de Fisher, odds ratio y ajuste Benjamini–Hochberg se usan como contrastes de asociación dentro del universo observado. DENUE no es una muestra probabilística y estas pruebas no corrigen dependencia espacial.

## Estructura del repositorio

```text
atoyac/
├── data/
│   ├── raw/                    # DENUE y capas territoriales originales
│   └── processed/              # catálogos, auditables, MH y legacy
├── scripts/                    # flujos locales, regionales y Parte 2
├── outputs/
│   ├── huejotzingo/            # productos locales
│   ├── xalmimilulco/           # productos locales y comparaciones legacy
│   ├── cuenca_alto_atoyac_*/   # cinco modalidades regionales
│   └── parte_2/                # clustering, perfiles, atlas y cierre
└── docs/
    ├── INVENTARIO_GENERAL_PROYECTO.md
    ├── parte_2/                # decisiones, metodología y trazabilidad
    ├── reporte_completo/       # reporte maestro
    └── reporte_sintetico/      # reporte de 17 páginas para público general
```

## Reportes y productos recomendados

### Lectura

- [Reporte sintético](docs/reporte_sintetico/reporte_sintetico.pdf): explicación breve del problema, territorios, robustez, límites y siguientes pasos; incluye diagrama de flujo y diccionario.
- [Reporte maestro](docs/reporte_completo/reporte_compelto.pdf): trazabilidad completa, decisiones metodológicas, resultados, tablas y anexos.
- [Inventario general](docs/INVENTARIO_GENERAL_PROYECTO.md): relación detallada de scripts, fuentes y productos.
- [Documentación de Parte 2](docs/parte_2/README.md): entrada técnica al pipeline de clustering.

### Datos analíticos

- `outputs/parte_2/01_matriz/matriz_maestra_establecimientos.csv`: universo integrado con IDs, coordenadas y señales.
- `outputs/parte_2/06_clusters/solucion_principal.gpkg`: membresías y geometría de la solución seleccionada.
- `outputs/parte_2/05_seleccion/persistencia_establecimientos.csv`: estabilidad por establecimiento.
- `outputs/parte_2/07_perfiles/establecimientos_perfilados_cuenca.csv`: registros interiores con cluster y perfil.
- `outputs/parte_2/07_perfiles/perfiles_clusters.csv`: resumen productivo por cluster.
- `outputs/parte_2/08_sobrerrepresentacion/sobrerrepresentacion_senales.csv`: lift, OR, intervalos, Fisher y ajuste BH.
- `outputs/parte_2/11_cierre/fichas_resumen_clusters.csv`: ficha compacta por cluster.
- `outputs/parte_2/14_segunda_pasada/subnucleos_mega_cluster_documentados.csv`: subnúcleos exploratorios del cluster 20.
- `outputs/parte_2/14_segunda_pasada/explorador_interactivo_clusters.html`: explorador autocontenido.

### Figuras y atlas

- `outputs/parte_2/12_atlas/`: fichas visuales de 18 clusters interiores y ruido.
- `outputs/parte_2/13_figuras_finales/`: figuras comparables de cierre.
- `outputs/parte_2/03_diagnosticos/figuras/`: KDE, mallas hexagonales y curvas k-distancia.
- `outputs/parte_2/14_segunda_pasada/figuras/`: estabilidad, perfiles y subnúcleos.

## Ejecución

El pipeline principal de Parte 2 se ejecuta desde la raíz del proyecto:

```powershell
python scripts\219_ejecutar_parte2_completa.py
```

Para reconstruir la segunda pasada más reciente:

```powershell
python scripts\220_segunda_pasada_analitica.py
python scripts\221_figuras_interactivo_segunda_pasada.py
python scripts\222_documentar_segunda_pasada.py
python scripts\217_compilar_documentos_parte2.py
```

Las figuras diagnósticas KDE/hexagonales se regeneran con:

```powershell
python scripts\223_figuras_diagnostico_kde_hex.py
```

Las modalidades regionales se generan con `scripts/101_main_cuenca_puebla.py`:

```powershell
python scripts\101_main_cuenca_puebla.py
python scripts\101_main_cuenca_puebla.py --sin-mh
python scripts\101_main_cuenca_puebla.py --estricto
python scripts\101_main_cuenca_puebla.py --estricto --sin-mh
python scripts\101_main_cuenca_puebla.py --todos-scian
```

### Entorno

El repositorio no contiene todavía un archivo de dependencias fijadas. Los scripts requieren Python 3 y utilizan principalmente:

- `pandas`, `numpy`;
- `geopandas`, `shapely`, `pyproj`;
- `scikit-learn`, `hdbscan`, `scipy`;
- `matplotlib`, `seaborn`, `folium`;
- una distribución LaTeX con `latexmk` para compilar los documentos.

Antes de una entrega reproducible en otro equipo debe generarse un entorno fijado (`requirements.txt` o equivalente) a partir del ambiente validado.

## Próxima etapa: integración hídrica

El análisis actual localiza concentraciones y describe perfiles; todavía no reconstruye el recorrido de los residuos líquidos. La siguiente fase debe integrar:

1. cauces, cuerpos de agua, subcuencas, modelo de elevación y pendientes;
2. atarjeas, colectores, pozos de visita, cárcamos, captadores e interceptores;
3. puntos de descarga conocidos y conexiones verificadas;
4. ubicación, cobertura, capacidad, tecnología y estado de plantas de tratamiento;
5. inspección de campo, aforos, trazadores y muestreo fisicoquímico;
6. escenarios de caudal y carga, CAPEX, OPEX, riesgo, permisos y gobernanza.

El objetivo será formular y comprobar cómo los posibles residuos de las agrupaciones entran y fluyen por el sistema de drenaje o por la superficie hacia los cuerpos de agua, y qué infraestructura existente podría captarlos o tratarlos. Las rutas modeladas deberán presentarse como hipótesis hasta ser verificadas.

## Límites de interpretación

Este repositorio no permite concluir, por sí solo:

- qué establecimientos están activos o contaminan;
- qué unidades usan procesos húmedos reales;
- cuánto agua consumen o qué carga descargan;
- si una unidad cercana a un río está conectada hidráulicamente;
- cuál es el área tributaria de una concentración;
- qué colector, planta o inversión debe construirse.

La información económica, espacial, hidráulica y ambiental debe conservar procedencia, fecha, responsable, sistema de referencia y reglas de enlace. Cualquier cambio en universo, parámetros principales o diccionarios debe registrarse como una nueva decisión metodológica.

## Autoría

**Nuria Arroyo Bustamante — 173605**  
Universidad de las Américas Puebla  
Corte documental: 24 de septiembre de 2026

