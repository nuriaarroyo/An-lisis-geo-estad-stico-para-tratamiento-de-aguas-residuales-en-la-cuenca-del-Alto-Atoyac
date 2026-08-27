# Reporte reproducible del universo textil independiente

Fecha de generación: 2026-08-20T20:59:17-06:00

## 1. Objetivo y alcance

El procedimiento identifica establecimientos con señales de actividad textil en las
localidades marcadas como activas en `localidades.csv`. En esta ejecución únicamente está
activa Santa Ana Xalmimilulco. La clasificación representa prioridad
analítica y posible relevancia ambiental; no demuestra descargas ni contaminación.

## 2. Separación metodológica

La clasificación se ejecutó antes de abrir las capas MH y canónica. Su manifiesto declara:
`No se leyó ninguna capa MH ni canónica durante la clasificación.` La comparación de
referencias consume una capa independiente ya materializada y no modifica sus decisiones.

El proceso está dividido en dos etapas. La primera construye el universo productivo amplio.
La segunda lee esa capa sin volver a buscar establecimientos y aplica exclusiones de alcance
y prioridades mediante `politica_refinamiento.csv`.

## 3. Datos y delimitación territorial

Fuente operativa: `data/raw/denue2026/Denue26 area estudio.shp`.

La selección territorial usa el atributo administrativo DENUE `cve_loc=0029`. El polígono
se conserva como referencia cartográfica, pero no elimina registros que DENUE identifica
como Santa Ana. El criterio se controla desde `localidades.csv`:

| localidad_id | nombre_salida | metodo_seleccion | campo_seleccion | valor_seleccion | activa |
| --- | --- | --- | --- | --- | --- |
| huejotzingo | Huejotzingo | atributo | cve_loc | 1 | False |
| santa_ana_xalmimilulco | Santa Ana Xalmimilulco | atributo | cve_loc | 29 | True |
| san_martin_texmelucan | San Martín Texmelucan | atributo | cve_loc | 1 | False |

Los Encinos (`cve_loc=0093`) se mantiene separado y fuera del universo de Santa Ana. Esta
decisión explica la ausencia del establecimiento 6272576, aunque aparezca en MH.

## 4. Preparación del texto

Se concatenan los campos DENUE disponibles: nombre del establecimiento, razón social y
descripción SCIAN. Se eliminan acentos, se convierte a minúsculas y se normalizan espacios.
Las palabras se buscan como términos o frases completas, con límites alfanuméricos, para
reducir coincidencias parciales accidentales.

## 5. Construcción de candidatos y clasificación

Las reglas se almacenan fuera del código. Los archivos editables son:

- `palabras_clave.csv`: términos, grupos, etapa, evidencia y rol.
- `codigos_scian.csv`: códigos exactos o prefijos y su señal.
- `reglas_clasificacion.csv`: catálogo metodológico.
- `politica_categorias.csv`: categorías, prioridad y decisión.
- `localidades.csv`: polígonos incluidos.
- `referencias_comparacion.csv`: referencias que se abren solo en la comparación.

### Códigos SCIAN

| code | match_type | signal | process_stage | evidence_level |
| --- | --- | --- | --- | --- |
| 313 | prefix | textile_manufacturing | fabricacion_insumos_textiles | alta |
| 314 | prefix | textile_manufacturing | fabricacion_productos_textiles | media |
| 315 | prefix | textile_manufacturing | confeccion_prendas | media |
| 8122 | prefix | textile_service | lavanderia_tintoreria | media |
| 313310 | exact | wet_process | acabado_textil | alta |
| 812210 | exact | wet_service_possible | lavanderia_tintoreria | media |
| 46 | prefix | commerce | comercio | alta |

### Reglas

| rule_id | stage | source | criterion | interpretation |
| --- | --- | --- | --- | --- |
| base_saic_textil | candidato | codigo SCIAN | Prefijo manufacturero textil identificado en SAIC | SAIC define las familias manufactureras que se buscan posteriormente en DENUE. |
| base_servicio_textil | candidato | codigo SCIAN | Codigo marcado como textile_service | Extiende SAIC con lavanderia y tintoreria para detectar procesos relevantes. |
| base_texto_textil | candidato | nombre razon social y actividad DENUE | Palabra del grupo candidate_textile | Recupera establecimientos cuya descripcion explicita una posible relacion textil. |
| exc_comercio_o_giro_no_textil | depuracion | codigo SCIAN y texto DENUE | Comercio sin produccion o giro no textil | Retira comercio y coincidencias de sectores no textiles. |
| exc_nombre_no_objetivo | exclusion_estricta | nombre razon social y actividad | Palabra del grupo excluded_name | Identifica planchado confeccion menor insumos y otros falsos positivos. |
| exc_actividad_no_objetivo | exclusion_estricta | actividad y codigo SCIAN | Palabra excluded_activity o codigo comercial | Identifica actividades declaradas fuera del objetivo analitico. |
| inc_humedo_texto | inclusion_estricta | nombre razon social y actividad | Palabra del grupo wet_specific | Senal textual explicita de proceso humedo o acabado. |
| inc_humedo_scian | inclusion_estricta | codigo SCIAN | Codigo marcado como wet_process | Actividad compatible con lavanderia tintoreria o acabado textil. |
| inc_mezclilla_texto | inclusion_estricta | nombre razon social y actividad | Palabra del grupo denim | Senal explicita de trabajo con mezclilla o jeans. |
| inc_material_textil | inclusion_estricta | codigo SCIAN y texto | SCIAN 313 mas palabra material sin exclusion | Incluye produccion de material textil y evita productos terminados no objetivo. |
| rev_contradiccion_scian_texto | revision | codigo SCIAN y texto | SCIAN 8122 combinado con bodega o desperdicio | Evita excluir automáticamente un servicio de lavandería cuando el nombre sugiere almacenamiento o residuos. |
| exc_coincidencia_generica_no_textil | depuracion | codigo SCIAN y texto | Solo aparecen palabras generales como elaboracion industria o industrial y el SCIAN no pertenece al universo textil | Elimina falsos positivos de alimentos construccion quimica acero y otros sectores no textiles. |

### Matriz ejecutable de precedencia

Esta tabla es leída directamente por el clasificador; las decisiones no están fijadas dentro
del script.

| priority | decision_rule | all_flags | any_flags | none_flags | category | decision |
| --- | --- | --- | --- | --- | --- | --- |
| 100 | exclusion_fuerte | strong_exclusion |  |  | excluir_actividad_no_objetivo | EXCLUIR |
| 98 | exclusion_generica_no_textil | generic_nontextile_only |  |  | excluir_coincidencia_generica_no_textil | EXCLUIR |
| 95 | contradiccion_servicio_bodega | service_storage_contradiction |  |  | revisar_contradiccion_scian_texto | REVISAR |
| 90 | exclusion_condicional | conditional_exclusion |  | commerce_overridden | excluir_comercio | EXCLUIR |
| 80 | proceso_humedo |  | wet_text/wet_code | strong_exclusion | lavado_acabado_textil | INCLUIR_ALTA |
| 70 | maquila_textil | maquila | textile_text/denim | strong_exclusion | maquila_textil | INCLUIR_MEDIA |
| 60 | produccion_mezclilla |  | denim | strong_exclusion | produccion_textil | INCLUIR_MEDIA |
| 50 | produccion_textil |  | textile_code/production_and_textile | strong_exclusion | produccion_textil | INCLUIR_MEDIA |
| 40 | revision_lavado | generic_wash |  |  | revisar_lavado_generico | REVISAR |
| 30 | revision_maquila | maquila |  |  | revisar_maquila_sola | REVISAR |
| 20 | revision_textil |  | textile_text/has_alert_role |  | revisar_textil_ambiguo | REVISAR |
| 0 | sin_evidencia |  |  |  | fuera_filtro | FUERA |

### Política de refinamiento

| priority | refinement_rule | all_flags | any_flags | none_flags | refined_decision | refined_priority | reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | excluir_tintoreria_comercial | is_scian_812210/name_tintoreria |  | name_industrial/name_proceso_productivo | EXCLUIR_ALCANCE | excluir | Servicio comercial de tintorería sobre prendas terminadas; fuera del foco productivo y de procesamiento de mezclilla |
| 90 | revisar_tintoreria_industrial | is_scian_812210/name_tintoreria | name_industrial/name_proceso_productivo |  | REVISAR | revision | Tintorería con señal productiva o industrial que requiere comprobación |
| 80 | prioridad_hidrica_original | original_incluir_alta |  |  | RETENER | alta | Proceso húmedo explícito conservado desde la clasificación de giro |
| 0 | conservar_universo_productivo |  |  |  | RETENER | media | Actividad perteneciente al universo productivo amplio sin señal húmeda prioritaria |

### Resultado del refinamiento

| decision_refinada | prioridad_refinada | regla_refinamiento | registros |
| --- | --- | --- | --- |
| EXCLUIR_ALCANCE | excluir | excluir_tintoreria_comercial | 2 |
| RETENER | alta | prioridad_hidrica_original | 6 |
| RETENER | media | conservar_universo_productivo | 306 |

## 6. Precedencia de decisión

1. Una exclusión fuerte no textil produce `EXCLUIR`.
2. Comercio o nombre excluido produce `EXCLUIR`, salvo que exista evidencia productiva
   explícita capaz de superar la exclusión condicional.
3. Proceso húmedo textual o SCIAN específico produce `INCLUIR_ALTA`.
4. Producción textil, mezclilla o maquila textil produce `INCLUIR_MEDIA`.
5. Lavado, maquila o señal textil ambigua produce `REVISAR`.
6. Sin evidencia suficiente produce `FUERA`.

La tabla `clasificacion_completa.csv` conserva, registro por registro, texto normalizado,
términos y códigos detectados, reglas activadas, regla decisiva, decisión y explicación.

## 7. Resultados independientes

| localidad_analisis | decision_clasificacion | categoria_clasificacion | registros |
| --- | --- | --- | --- |
| Santa Ana Xalmimilulco | INCLUIR_ALTA | lavado_acabado_textil | 4 |
| Santa Ana Xalmimilulco | INCLUIR_MEDIA | maquila_textil | 171 |
| Santa Ana Xalmimilulco | INCLUIR_MEDIA | produccion_textil | 135 |
| Santa Ana Xalmimilulco | REVISAR | revisar_contradiccion_scian_texto | 2 |
| Santa Ana Xalmimilulco | REVISAR | revisar_lavado_generico | 18 |
| Santa Ana Xalmimilulco | REVISAR | revisar_maquila_sola | 2 |

Los registros `REVISAR` no forman parte de la capa incluida. Se entregan en una capa
separada para decisión humana.

## 8. Referencias disponibles

| referencia_id | localidad_id | estado | registros | nota |
| --- | --- | --- | --- | --- |
| mh_filtrado | santa_ana_xalmimilulco | DISPONIBLE | 43 | Capa de referencia disponible únicamente para Santa Ana |
| canonico_original | santa_ana_xalmimilulco | DISPONIBLE | 38 | Se extrae la membresía canónica conservada en la comparación histórica |

MH y el canónico disponible corresponden a Santa Ana, la localidad activa en esta ejecución.

## 9. Comparación

| localidad_id_analisis | perfil_comparacion | registros |
| --- | --- | --- |
| santa_ana_xalmimilulco | en_los_tres | 7 |
| santa_ana_xalmimilulco | independiente_y_canonico | 10 |
| santa_ana_xalmimilulco | independiente_y_mh | 34 |
| santa_ana_xalmimilulco | solo_canonico | 21 |
| santa_ana_xalmimilulco | solo_independiente | 261 |
| santa_ana_xalmimilulco | solo_mh | 2 |

La comparación se realiza por identificador DENUE normalizado. No se usa proximidad espacial
para declarar una coincidencia.

### Razones de referencias no incluidas

| id_denue | nombre | en_mh | en_canonico | estado_fuente | razon_no_inclusion |
| --- | --- | --- | --- | --- | --- |
| 3327188 | 13 | True | False | ausente_denue_2026 | AUSENTE_DENUE_2026: el ID de referencia no existe en la fuente DENUE 2026 |
| 6272576 | LAVADOS NACIONALES | True | False | fuera_localidad_administrativa | FUERA_AREA: localidad=Los Encinos, cve_loc=0093; Santa Ana usa cve_loc=0029 |
| 10086701 | LAVANDERIA MEXICO | False | True | clasificado_no_incluido | :  /  |
| 10451408 | STONE LAV | False | True | clasificado_no_incluido | INCLUIR_ALTA: lavado_acabado_textil / inc_humedo_texto |
| 10801837 | LAVANDERIA SIN NOMBRE | False | True | clasificado_no_incluido | :  /  |
| 10876257 | LAVANDERIA MA & MA | False | True | clasificado_no_incluido | :  /  |
| 11081907 | BODEGA SIN NOMBRE | False | True | clasificado_no_incluido | :  /  |
| 11096797 | LAVADOS Y PROCESOS FLORES | False | True | ausente_denue_2026 | AUSENTE_DENUE_2026: el ID de referencia no existe en la fuente DENUE 2026 |
| 11149643 | LAVANDERIA LOS SOLARES | False | True | clasificado_no_incluido | :  /  |
| 11183668 | BODEGA DE DESPERDICIO | False | True | clasificado_no_incluido | :  /  |
| 3326066 | LAVANDERIA LAVAPLUS | False | True | clasificado_no_incluido | :  /  |
| 3427213 | LAVANDERIA MAGALY | False | True | clasificado_no_incluido | :  /  |
| 3427228 | TINTORERIA LIZ | False | True | clasificado_no_incluido | EXCLUIR_ALCANCE: excluir_tintoreria_comercial / Servicio comercial de tintorería sobre prendas terminadas; fuera del foco productivo y de procesamiento de mezclilla |
| 3427244 | TINTORERIA LIZ | False | True | clasificado_no_incluido | EXCLUIR_ALCANCE: excluir_tintoreria_comercial / Servicio comercial de tintorería sobre prendas terminadas; fuera del foco productivo y de procesamiento de mezclilla |
| 3427993 | LAVANDERIA SIN NOMBRE | False | True | clasificado_no_incluido | :  /  |
| 3428103 | LAVANDERIA NOVALAV | False | True | clasificado_no_incluido | :  /  |
| 3428125 | LAVANDERIA SANTA CECILIA | False | True | clasificado_no_incluido | :  /  |
| 3428174 | LAVANDERIA ALEX | False | True | clasificado_no_incluido | :  /  |
| 3428283 | LAVANDERIA LAVAMEXXAL | False | True | clasificado_no_incluido | :  /  |
| 8089261 | LAVANDERIA REY | False | True | clasificado_no_incluido | :  /  |
| 8089562 | LAVANDERIA SANTY | False | True | clasificado_no_incluido | :  /  |
| 8111334 | VAQUIMTEX PRODUCTOS PARA LAVANDERIA | False | True | clasificado_no_incluido | :  /  |
| 8776900 | LAVANDERIA MARY | False | True | clasificado_no_incluido | :  /  |

Los identificadores 3327188 y 11096797 aparecen en referencias históricas pero no existen
en la fuente DENUE 2026 utilizada. Se documentan como ausencias de fuente y no como errores
del filtro.

## 10. Validaciones

| validacion | resultado |
| --- | --- |
| ids_unicos_por_localidad | OK |
| todas_decisiones_asignadas | OK |
| incluidos_sin_exclusion_fuerte | OK |
| localidades_activas_presentes | OK |

## 11. Archivos de salida

- `outputs/universo_independiente_3_localidades/capas_qgis/`: base, clasificación e incluidos.
- `outputs/universo_independiente_3_localidades/tablas/`: trazabilidad y controles.
- `outputs/universo_independiente_3_localidades/manifest_clasificacion.json`: hashes de entradas.
- `outputs/comparacion_3_localidades/capas_qgis/comparacion_referencias.gpkg`.
- `outputs/comparacion_3_localidades/tablas/comparacion_referencias.csv`.
- `outputs/comparacion_3_localidades/mapas/universo_independiente_3_localidades.png`.

## 12. Limitaciones

DENUE describe unidades registradas y no prueba procesos observados en campo. La clasificación
depende de códigos y descripciones disponibles. La ausencia de un establecimiento no prueba
su inexistencia. Toda modificación metodológica debe crear una nueva versión de los CSV y
volver a ejecutar la clasificación completa.
