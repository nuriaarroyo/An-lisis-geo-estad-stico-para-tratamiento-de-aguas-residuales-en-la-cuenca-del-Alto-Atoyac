# Reporte técnico de Parte 2

## Estado del análisis

Documento generado reproduciblemente por `211_generar_documentos_parte2.py`. La denominación oficial es **Universo sectorial ampliado de actividades textiles, confección y servicios de lavandería/tintorería potencialmente relevantes**.

## Universo y borde

- Detección espacial: 4,365 establecimientos de los municipios de apoyo.
- Interpretación principal: 4,010 establecimientos dentro de la cuenca.
- Registros fuera de cuenca utilizados para evitar fragmentación de borde: 355.
- CRS de análisis: EPSG:32614; distancia euclidiana en metros.

## Separación metodológica

La detección y selección emplearon únicamente coordenadas proyectadas. SCIAN, señales textuales, evidencia hídrica y estrato de personal se incorporaron después de seleccionar la solución espacial.

## Solución principal

- Escenario: `hdbscan__min_cluster_size-10__min_samples-20__cluster_selection_method-eom`.
- Método: HDBSCAN.
- Clusters detectados sobre el universo municipal: 22.
- Ruido municipal: 584 (13.4%).
- Cluster mayor: 1997 (45.8% del universo de detección).
- Probabilidad media de pertenencia: 0.914.
- Estabilidad ARI promedio de las cinco configuraciones más próximas: 0.937.
- Clusters con establecimientos dentro de la cuenca: 18.
- Actividad dispersa dentro de la cuenca: 578 establecimientos.
- Clusters que cruzan el límite: 1.

La configuración es una solución operativa principal, no una partición territorial verdadera única. Se conserva una referencia DBSCAN y cuatro escenarios HDBSCAN de sensibilidad.

## Coexistencia sectorial descriptiva

Clasificación posterior de los clusters: {'CONCENTRACION_MANUFACTURA': 12, 'COEXISTENCIA_MIXTA': 6}. Esta tipología no intervino en su construcción. La tabla auditable se encuentra en `outputs/parte_2/07_perfiles/analisis_coexistencia_lavanderias_manufactura.csv`.

## Sobrerrepresentación

Se ejecutaron 342 comparaciones cluster-señal. 54 cumplen simultáneamente conteo mínimo, prevalencia, lift y significancia con ajuste Benjamini–Hochberg. Estos criterios son descriptivos y no equivalen a causalidad ni a validación de procesos reales.

## Limitaciones vigentes

- DENUE puede omitir actividad informal o domiciliaria.
- SCIAN 812210 no distingue lavandería comercial de industrial.
- Las coordenadas válidas no garantizan precisión predial.
- El mega-cluster principal exige interpretación multiescala y comparación con sensibilidad.
- Cercanía o coexistencia no demuestran relación productiva, consumo de agua ni descarga.
