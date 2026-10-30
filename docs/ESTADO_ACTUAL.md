# Estado actual del trabajo

Corte de lectura: 23 de octubre de 2026. Autora: Nuria Arroyo Bustamante.

## Pregunta y alcance

¿Dónde se concentran actividades textiles potencialmente relevantes y cómo se relacionan espacialmente con la infraestructura de saneamiento disponible? El trabajo avanza desde la construcción del universo económico hasta la exploración de corredores. No atribuye contaminación ni comprueba conexiones hidráulicas por proximidad.

## Parte 1: construir un universo auditable

Se combinan DENUE, filtros SCIAN y texto, evidencia de campo MH y fuentes territoriales. Se comparan cinco modalidades: amplia/estricta, con/sin MH y sectorial ampliada. La modalidad sectorial conserva posibles actividades que un filtro restrictivo podría excluir antes de validar sus procesos.

## Parte 2: identificar concentraciones

- Universo de detección con contexto de borde: 4,365 establecimientos.
- Interior de cuenca para interpretación: 4,010.
- Escenarios espaciales evaluados: 57.
- Referencia: HDBSCAN de scikit-learn, min_cluster_size=10, min_samples=20, EOM.
- 22 clusters en detección; 18 intersectan cuenca; 584 puntos como ruido.

Los perfiles productivos se incorporan después de fijar la solución espacial. La partición se conserva para que la integración posterior no cambie silenciosamente el universo.

## Parte 3: integrar infraestructura y explorar el territorio

Base regional: 69 registros PTAR (65 INEGI + 4 compilados), 302 descargas e hidrografía. Dos pares PTAR coinciden en nombre y coordenadas; los registros originales se conservan. No son 69 instalaciones físicas independientes confirmadas.

Foco actual: 337 establecimientos sectoriales de Santa Ana y 71 de Huejotzingo. Se exploran los 65 de prioridad alta/media: 31 y 34, respectivamente. Destinos del núcleo: Cabecera Municipal, Paseo de los Sauces y Real Segovia. Las plantas de contexto externo todavía no se analizan como destinos de esta comparación.

| Resultado | Interpretación |
|---|---|
| 102 rutas Huejotzingo–PTAR | Un camino por establecimiento y planta: 34 × 3. |
| 93 pares Santa Ana–PTAR sin ruta | La red disponible está desconectada; no prueba ausencia física de caminos o drenaje. |
| 62 recorridos internos de Santa Ana | 31 × 2 extremos existentes para inspección, no plantas. |
| Terreno completo hacia Cabecera y Paseo | Permite revisar perfiles superficiales; no acredita gravedad. |
| Terreno parcial hacia Real Segovia y Santa Ana occidental | Faltan hojas para comparar corredores completos. |

Dijkstra minimiza distancia vial. La pendiente se estudia sobre los caminos posteriormente y no decide todavía la ruta. La suma de caminos individuales repite tramos; su unión tampoco garantiza una red conjunta de menor costo.

## Parte 4: pendiente

La siguiente etapa requiere una red común hacia un destino, aportaciones de caudal/carga, cotas de tubería y entrada de planta, capacidad receptora verificada, cruces, derechos de vía y costos. No existe todavía una recomendación de obra o diseño definitivo.

## Qué puede revisar otra persona

La [entrega](../entrega/LEEME.md) reúne el resumen regional, la explicación ilustrada de caminos, mapas, tablas y capas seleccionadas. El [reporte técnico local](../atoyac/outputs/parte_3/12_vialidades_amplias/reporte_red_amplia_territorio.md) desarrolla el método y sus límites. Los scripts y manifiestos permiten seguir la procedencia de cada producto.
