# Entrega de lectura — Alto Atoyac

**Nuria Arroyo Bustamante · UDLAP · corte: 23 de octubre de 2026.**

Este paquete muestra la evolución del trabajo: universo económico, concentraciones regionales e integración con infraestructura y relieve. Puede copiarse completo o compartirse en ZIP; los PDF y el explorador se leen sin instalar Python.

## Orden de lectura

1. [Resumen regional](reportes/01_resumen_regional.pdf): motivación, universo económico y concentraciones; su corte es anterior a la exploración local.
2. [Explicación ilustrada de caminos](reportes/02_explicacion_caminos.pdf): seis páginas para entender caminos individuales y tramos compartidos.
3. [Resultados actuales de territorio, grafo y pendiente](reportes/03_resultados_parte3.md).
4. [Explorador interactivo](explorador.html): abrir en navegador y activar capas en la leyenda.
5. [Reporte técnico de parte 2](reportes/04_reporte_tecnico_parte2.pdf): metodología y cierre de concentraciones.

## Qué demuestra el análisis actual

- 408 establecimientos sectoriales identificados: 337 Santa Ana y 71 localidad de Huejotzingo.
- 65 prioritarios analizados: 31 Santa Ana y 34 Huejotzingo.
- 102 caminos individuales de Huejotzingo a tres PTAR candidatas. Dijkstra minimiza distancia; la pendiente se revisa después.
- Santa Ana no tiene ruta continua a esas plantas en las capas actuales; se muestran 62 recorridos internos a dos extremos para inspección.
- Terreno completo sobre rutas a Cabecera Municipal y Paseo; parcial hacia Real Segovia y Santa Ana occidental.

La red compartida no está optimizada conjuntamente y no es un diseño hidráulico. Registro no acredita operación; cercanía no acredita conexión; prioridad no acredita contaminación o caudal.

## Mapas

[Mapa regional de concentraciones](figuras/00_clusters_regionales.png). Los mapas siguientes desarrollan el foco local de parte 3.

| Localidad | Terreno | Inclinación | Recorridos | Perfiles |
|---|---|---|---|---|
| Santa Ana | [Elevación](figuras/05_santa_ana_elevacion.png) | [Pendiente](figuras/05_santa_ana_pendiente.png) | [Internos](figuras/06_santa_ana_corredores.png) | [Perfil](figuras/07_santa_ana_perfiles.png) |
| Huejotzingo | [Elevación](figuras/05_huejotzingo_elevacion.png) | [Pendiente](figuras/05_huejotzingo_pendiente.png) | [A PTAR](figuras/06_huejotzingo_corredores.png) | [Perfil](figuras/07_huejotzingo_perfiles.png) |

## Datos para revisar

- [Capas seleccionadas para QGIS](datos/capas_seleccionadas.gpkg): establecimientos, plantas, vialidad, caminos y cobertura; vectores EPSG:32614.
- [Establecimientos](datos/establecimientos.csv), [PTAR candidatas](datos/ptar_candidatas.csv) y [164 caminos calculados](datos/caminos_minimos.csv).
- [Diccionario](datos/DICCIONARIO.csv), [cobertura territorial](datos/cobertura_territorial.csv) y [cobertura/pendiente de recorridos](datos/resumen_cobertura_pendientes.csv).
- [Manifiesto](MANIFIESTO.json): integridad, selección y procedencia.

Los extremos EXT_01 y EXT_02 no son plantas o descargas comprobadas. Los campos sin información permanecen vacíos. La entrega no incluye los raster originales ni la totalidad de antecedentes o archivos de reconstrucción.

## Fuentes y autoría

DENUE/INEGI, CNGMD 2021, RH18, MDT/MDS de INEGI, capas territoriales CAARESA, evidencia MH de Mary Helen Figueroa y Mayra Jaqueline Ramírez, y compilación de PTAR de la entrega de Lesly. Conservar esta atribución y las condiciones originales de uso de cada fuente al compartir.

Para reconstrucción, consultar la guía técnica del repositorio. Este paquete se genera desde la raíz con `python herramientas/preparar_entrega.py`.
