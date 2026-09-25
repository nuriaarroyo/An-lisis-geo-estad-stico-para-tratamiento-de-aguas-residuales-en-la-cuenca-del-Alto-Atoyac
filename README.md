# Análisis geo-estadístico para tratamiento de aguas residuales en la cuenca del Alto Atoyac

Repositorio de investigación para construir, auditar y analizar territorialmente el universo de unidades económicas textiles, de confección y de lavandería/tintorería potencialmente relevantes en la cuenca del Alto Atoyac, Puebla.

El proyecto evolucionó desde una auditoría local de Santa Ana Xalmimilulco hacia un análisis regional reproducible de 26 municipios, con comparación de universos, clustering espacial por densidad, perfiles productivos, evaluación de robustez y productos para orientar la validación de campo. La siguiente etapa propuesta integra las concentraciones con hidrología, relieve, drenaje, captadores y plantas de tratamiento.

> **Interpretación obligatoria:** concentración espacial no significa contaminación; proximidad a río no demuestra descarga; cluster no equivale a zona de servicio; lavandería sectorial no significa lavandería industrial verificada; priorización territorial no constituye una recomendación de colector.

## Organización del repositorio

```text
repositorio/
├── version_01/              # fase inicial: auditoría local y universo independiente
├── atoyac/                  # fase regional vigente, clustering y reportes
├── requirements.txt         # dependencias mínimas históricas de version_01
└── README.md                # entrada general
```

### `version_01/`: origen local y auditoría manual

Contiene el desarrollo inicial centrado en Santa Ana Xalmimilulco, con Huejotzingo y San Martín Texmelucan como territorios configurados. En esta fase se construyeron reglas independientes de clasificación, universos auditables, colas de revisión manual y comparaciones posteriores con fuentes MH y canónicas.

Sus principales aportaciones fueron:

- separar la clasificación independiente de las fuentes usadas para comparación;
- documentar palabras clave, SCIAN y precedencia de reglas en archivos configurables;
- realizar la auditoría manual de Xalmimilulco;
- producir tablas auditables y comparaciones legacy;
- reconocer los límites de extrapolar manualmente el flujo local a toda la cuenca.

Documentación de esta fase:

- [`version_01/filtros_textiles_santa_ana/README.md`](version_01/filtros_textiles_santa_ana/README.md)
- [`version_01/data/README.md`](version_01/data/README.md)
- [`version_01/scripts/legacy/README.md`](version_01/scripts/legacy/README.md)
- [`version_01/outputs/legacy/README.md`](version_01/outputs/legacy/README.md)

### `atoyac/`: análisis regional actual

Es la fase principal vigente. Integra DENUE, fuentes territoriales, hidrografía, productos legacy y evidencia MH; construye cinco modalidades regionales; detecta concentraciones sobre el universo sectorial ampliado; caracteriza clusters y ruido; documenta incertidumbre; y genera reportes, atlas y un explorador interactivo.

Entradas técnicas:

- [`atoyac/README.md`](atoyac/README.md)
- [`atoyac/docs/parte_2/README.md`](atoyac/docs/parte_2/README.md)
- [`atoyac/docs/INVENTARIO_GENERAL_PROYECTO.md`](atoyac/docs/INVENTARIO_GENERAL_PROYECTO.md)

## Evolución metodológica

```text
Versión 1: universo local independiente
        │
        ├── filtros SCIAN y texto configurables
        ├── auditoría manual de Xalmimilulco
        └── comparación posterior con MH y legacy
        │
        ▼
Fase regional: cinco modalidades comparables
        │
        ├── amplia / estricta
        ├── con MH / sin MH
        └── universo sectorial completo
        │
        ▼
Parte 2: análisis espacial de concentraciones
        │
        ├── diagnóstico KDE, hexágonos y vecinos
        ├── DBSCAN, HDBSCAN y OPTICS
        ├── selección, estabilidad y efecto de borde
        └── perfiles productivos posteriores
        │
        ▼
Clusters, ruido, atlas y zonas de validación
        │
        ▼
Etapa futura: hidrología + relieve + drenaje
        + captadores + descargas + tratamiento
```

La transición conserva la fase local como antecedente y trazabilidad. El análisis regional no extrapola automáticamente decisiones manuales de Xalmimilulco al resto de los municipios.

## Estado actual y resultados

| Elemento | Resultado |
|---|---:|
| Registros estatales iniciales acotados por SCIAN | 15,956 |
| Universo sectorial de detección y control de borde | 4,365 |
| Establecimientos dentro de la cuenca para interpretación | 4,010 |
| Configuraciones espaciales evaluadas | 57 |
| Solución seleccionada | HDBSCAN, `min_cluster_size=10`, `min_samples=20`, EOM |
| Clusters en el universo de detección | 22 |
| Clusters que intersectan la cuenca | 18 |
| Ruido en detección | 584 (13.38 %) |
| Cluster mayor | 1,997 establecimientos |

La solución seleccionada obtuvo el mayor puntaje operativo (`0.963`), pero dos configuraciones HDBSCAN alcanzaron `0.962` y producen resultados prácticamente equivalentes. Se usa como referencia reproducible, no como una partición territorial verdadera única.

### Territorios representativos

- **Santa Ana Xalmimilulco:** confección, maquila y mezclilla/pantalón.
- **Huejotzingo:** coexistencia de manufactura y lavandería/tintorería sectorial.
- **Tlahuapan:** San Rafael Ixtapalucan y San Miguel Tianguistenco destacan en tejido e hilado; Santiago Coltzingo en maquila.
- **San Martín Texmelucan, San Rafael Tlanalapan y Santa María Moyotzingo:** núcleos relacionados pero diferenciados.
- **San Miguel Xoxtla–Coronango:** concentración manufacturera que requiere validación funcional e hidráulica.
- **Amozoc:** núcleos pequeños con perfiles mixtos.
- **Puebla–Cholula–Cuautlancingo:** sistema metropolitano continuo y heterogéneo, no una zona operativa única.

## Fuentes y modalidades regionales

Las fuentes principales son DENUE/INEGI, el polígono de la cuenca, división municipal, red hidrográfica, productos legacy y la investigación de campo MH de Mary Helen Figueroa y Mayra Jaqueline Ramírez.

| Modalidad regional | Dentro de cuenca | Función |
|---|---:|---|
| Amplia + MH | 1,717 | Cobertura amplia con evidencia de campo. |
| Amplia DENUE | 1,679 | Sensibilidad alta sin MH. |
| Estricta + MH | 510 | Priorización con señales más directas y MH. |
| Estricta DENUE | 469 | Contraste restrictivo basado en DENUE. |
| Sectorial ampliada | 4,010 | Denominador del análisis regional de concentraciones. |

La modalidad estricta reduce ambigüedad, pero puede excluir actividades industriales reales cuyos nombres no declaran procesos húmedos. Por ello el clustering regional utiliza el universo sectorial ampliado y perfila las señales después.

## Productos principales

### Reportes

- [Reporte sintético](atoyac/docs/reporte_sintetico/reporte_sintetico.pdf): documento de 17 páginas para público menos técnico, con diagrama de flujo, territorios, límites, siguientes pasos y diccionario.
- [Reporte maestro](atoyac/docs/reporte_completo/reporte_compelto.pdf): trazabilidad completa, metodología, clustering, perfiles, robustez, resultados y anexos.
- [Inventario general](atoyac/docs/INVENTARIO_GENERAL_PROYECTO.md): relación detallada de fuentes, scripts y productos.

### Datos y capas

- `atoyac/outputs/parte_2/01_matriz/matriz_maestra_establecimientos.csv`
- `atoyac/outputs/parte_2/05_seleccion/persistencia_establecimientos.csv`
- `atoyac/outputs/parte_2/06_clusters/solucion_principal.gpkg`
- `atoyac/outputs/parte_2/07_perfiles/establecimientos_perfilados_cuenca.csv`
- `atoyac/outputs/parte_2/07_perfiles/perfiles_clusters.csv`
- `atoyac/outputs/parte_2/08_sobrerrepresentacion/sobrerrepresentacion_senales.csv`
- `atoyac/outputs/parte_2/11_cierre/fichas_resumen_clusters.csv`
- `atoyac/outputs/parte_2/14_segunda_pasada/subnucleos_mega_cluster_documentados.csv`
- `atoyac/outputs/parte_2/14_segunda_pasada/explorador_interactivo_clusters.html`

### Figuras

- `atoyac/outputs/parte_2/12_atlas/`: fichas de 18 clusters interiores y ruido.
- `atoyac/outputs/parte_2/13_figuras_finales/`: figuras definitivas.
- `atoyac/outputs/parte_2/03_diagnosticos/figuras/`: KDE, hexágonos y curvas k-distancia.
- `atoyac/outputs/parte_2/14_segunda_pasada/figuras/`: estabilidad, perfiles y subnúcleos.

## Ejecución

### Pipeline regional actual

Desde la raíz del repositorio:

```powershell
Set-Location atoyac
python scripts\219_ejecutar_parte2_completa.py
python scripts\220_segunda_pasada_analitica.py
python scripts\221_figuras_interactivo_segunda_pasada.py
python scripts\222_documentar_segunda_pasada.py
python scripts\217_compilar_documentos_parte2.py
```

El script `219` ejecuta el cierre principal; `220–222` forman la segunda pasada y se ejecutan después. `223_figuras_diagnostico_kde_hex.py` regenera los diagnósticos KDE/hexagonales usados en los reportes. Los comandos de las cinco modalidades regionales están en [`atoyac/README.md`](atoyac/README.md).

### Pipeline histórico de versión 1

El pipeline inicial se conserva para trazabilidad dentro de `version_01/`. Sus insumos y configuración deben revisarse antes de ejecutarlo, porque representa una fase metodológica anterior y no sustituye el flujo regional vigente.

## Dependencias

El archivo raíz [`requirements.txt`](requirements.txt) contiene las dependencias mínimas históricas de `version_01`: `geopandas`, `matplotlib`, `numpy`, `pandas`, `pyogrio` y `shapely`.

La fase regional requiere además `scikit-learn`, `hdbscan`, `scipy`, `seaborn`, `folium`, `pyproj` y una distribución LaTeX con `latexmk`. Todavía no existe un entorno fijado único para todo el repositorio; generarlo a partir del ambiente validado es un pendiente de reproducibilidad.

## Próxima etapa: integración hídrica

El proyecto actual permite localizar concentraciones y entender su perfil productivo. Lo siguiente es integrar:

1. hidrología, cauces, cuerpos de agua y subcuencas;
2. relieve, modelos de elevación y pendientes;
3. atarjeas, colectores, pozos, cárcamos, captadores e interceptores;
4. descargas conocidas y conexiones verificadas;
5. ubicación, cobertura, capacidad y tecnología de plantas de tratamiento;
6. inspecciones, aforos, trazadores y muestreo fisicoquímico.

La integración buscará formular cómo los posibles residuos líquidos de las agrupaciones entran y fluyen por el drenaje o la superficie hacia los cuerpos de agua, y qué infraestructura puede captarlos o tratarlos. Esas rutas serán hipótesis hasta ser verificadas con información del organismo operador y evidencia de campo.

## Lo que el repositorio no demuestra

Los resultados no permiten concluir por sí solos:

- que un establecimiento está activo, utiliza agua o contamina;
- que una lavandería sectorial es una lavandería industrial;
- que la cercanía a un río implica una descarga;
- cuánto caudal o carga contaminante produce una unidad;
- que un cluster es un área tributaria o una zona de servicio;
- qué colector, planta o inversión debe ejecutarse.

Antes de hablar de inversión se requieren validación de procesos, rutas reales de descarga, aforos, calidad del agua, red sanitaria, topografía, capacidad de tratamiento, costos, permisos y gobernanza.

## Autoría

**Nuria Arroyo Bustamante — 173605**<br>
Universidad de las Américas Puebla<br>
Corte documental: 24 de septiembre de 2026
