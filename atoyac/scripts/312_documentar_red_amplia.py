"""Documenta resultados de red amplia, exploración local y pendientes."""
from pathlib import Path
import json,hashlib,platform
import geopandas as gpd
import pandas as pd
import networkx as nx
import rasterio
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/12_vialidades_amplias'

def table(d):
    def val(x):return 'sin dato' if pd.isna(x) else f'{x:.2f}' if isinstance(x,float) else str(x)
    return '\n'.join(['| '+' | '.join(d.columns)+' |','| '+' | '.join(['---']*len(d.columns))+' |']+['| '+' | '.join(val(x) for x in row)+' |' for row in d.itertuples(index=False,name=None)])

def main():
    summary=json.loads((OUT/'resumen.json').read_text(encoding='utf-8'))
    full=json.loads((OUT/'comprobacion_red_completa.json').read_text(encoding='utf-8'))
    assert set(full['componentes_santa_ana']).isdisjoint(full['componentes_ptar'])
    cov=pd.read_csv(OUT/'resumen_cobertura_pendientes.csv')
    terr=pd.read_csv(OUT/'cobertura_territorial.csv')
    matrix=pd.read_csv(OUT/'matriz_origen_destino.csv')
    routes=pd.read_csv(OUT/'cobertura_pendientes_rutas.csv')
    inv=pd.read_csv(OUT/'inventario_entregas.csv')
    gates=gpd.read_file(OUT/'grafo_corredores_exploratorios.gpkg',layer='extremos_inspeccion_santa_ana').to_crs(4326)
    gateview=pd.DataFrame({'extremo':gates.extremo_id,'longitud':gates.geometry.x.map(lambda x:f'{x:.6f}'),'latitud':gates.geometry.y.map(lambda x:f'{x:.6f}')})
    output=[]
    for _,r in cov.iterrows():
        output.append({'Localidad':r.zona,'Destino':r.destino_id,'Rutas':int(r.rutas),
            'Longitud vial min–max km':f'{r.longitud_min_m/1000:.2f}–{r.longitud_max_m/1000:.2f}',
            'Cobertura MDT media/min %':f'{r.cobertura_media_pct:.1f} / {r.cobertura_min_pct:.1f}',
            'Pendiente global min–max %': 'sin dato' if pd.isna(r.pendiente_global_min_pct) else f'{r.pendiente_global_min_pct:.2f}–{r.pendiente_global_max_pct:.2f}'})
    report=f'''# Santa Ana y Huejotzingo: vialidades amplias, grafos y relieve

## Resultado de la nueva entrega

Se revisaron las siete entregas de vialidad, incluidas la descarga de 46,146 tramos en la raíz de vialidades y las carpetas c2 y c3. Se homologaron a EPSG:32614 y se retiraron sólo geometrías exactamente repetidas. El análisis selecciona {summary['tramos_fuente']:,} tramos completos que intersectan la envolvente de los 408 establecimientos y tres PTAR + 2.5 km.

La descarga amplia NO cierra la conexión Santa Ana–Huejotzingo. Tras construir intersecciones, siguen {summary['componentes_nodando_cruces']} componentes. Los 31 orígenes prioritarios de Santa Ana permanecen en una componente distinta a las tres plantas. La separación mínima entre nodos de las dos componentes principales continúa en aproximadamente 990 m. Hay calles aisladas intermedias: esa cifra no significa 990 m exactos de vialidad faltante.

Este resultado no demuestra que físicamente no exista un camino. Muestra que ampliar el recorte de estas capas no agregó la continuidad necesaria. Debe revisarse la representación del enlace interurbano, sus interrupciones y posibles caminos/carreteras ausentes. No se inventaron líneas de conexión.

## Qué se pudo analizar para cada localidad

**Huejotzingo:** 34 orígenes alta/media con ruta a las tres PTAR (102 caminos). Las longitudes permanecen iguales a la revisión previa: la ampliación no cambió las rutas mínimas. Las PTAR son Cabecera Municipal PTAR_066 (asociada a 005), Paseo de los Sauces 067 y Real Segovia 068.

**Santa Ana:** se calcularon 62 caminos dentro de su red, desde los 31 orígenes alta/media hacia dos extremos viales existentes para inspección (EXT_01 y EXT_02). No son rutas a PTAR, puntos de descarga, cruces confirmados ni propuestas de conexión. Se seleccionaron extremos de grado uno dentro de su componente, próximos geométricamente al conjunto de PTAR y separados al menos 250 m entre sí. Sirven para explorar concentraciones de caminos y preparar reconocimiento en campo; no se eligieron por aptitud hidráulica.

{table(gateview)}

Los 408 establecimientos permanecen identificados y contextualizan los mapas; las rutas se limitan a los 65 de prioridad alta/media. La clasificación no acredita operación actual ni caudal. El grafo con accesos contiene {summary['nodos_con_accesos']:,} nodos y {summary['aristas_con_accesos']:,} aristas.

## ¿La elevación cubre bien el análisis?

{table(terr.rename(columns={'zona':'Localidad','establecimientos':'Establecimientos','establecimientos_con_mdt':'Con MDT','area_zona_con_mdt_pct':'Área operativa con MDT %','longitud_vial_con_mdt_pct':'Longitud vial con MDT %'}))}

Las zonas operativas son envolventes de establecimientos + 2 km, no límites oficiales. Los porcentajes territoriales se calculan con la máscara de píxeles válidos del MDT, no sólo con los rectángulos de las hojas.

{table(pd.DataFrame(output))}

La cobertura de ruta anterior mide LONGITUD dentro de la máscara válida, no sólo porcentaje de muestras. Las distancias de esta tabla son exclusivamente viales; los accesos geométricos a edificios y plantas figuran por separado en la matriz origen–destino.

- Huejotzingo–Cabecera y Huejotzingo–Paseo: cobertura completa de elevación sobre las trazas calculadas. Se puede analizar el relieve de esos corredores.
- Huejotzingo–Real Segovia: falta aproximadamente una cuarta parte del MDT en promedio; no se conoce la elevación final del corredor y no procede evaluar una pendiente global hasta esa planta.
- Santa Ana–EXT_01: cobertura insuficiente; el promedio es cercano a 68 % y hay rutas por debajo de 50 %. El extremo occidental/suroccidental del recorrido deja la hoja disponible.
- Santa Ana–EXT_02: cobertura mucho mejor, cercana a 100 % de media, pero no todos los recorridos quedan completos. Los porcentajes particulares están en cobertura_pendientes_rutas.csv.

## Método del grafo

1. **Geometría métrica y topología.** Grafo no dirigido en NetworkX. Nodos en vértices y cruces de líneas mediante unary_union; aristas entre vértices consecutivos, con costo igual a longitud en metros. No se impone sentido vehicular como dirección de flujo. Se consideran cruces geométricos conectados, pendiente verificar pasos a distinto nivel. No se unen extremos con una tolerancia arbitraria ni se rellenan brechas.
2. **Accesos.** Cada establecimiento y PTAR conserva su ubicación original. Se proyecta sobre la arista más próxima y se divide esa arista en el punto proyectado. El segmento de acceso se registra aparte y no demuestra conexión sanitaria o derecho de paso.
3. **Camino mínimo.** Dijkstra con peso longitud_m. Se obtiene la ruta de menor distancia vial desde cada origen a cada destino alcanzable. Una componente distinta se registra como SIN RUTA, no como distancia cero.
4. **Corredores compartidos.** Se cuenta cuántos caminos utilizan una arista por destino; no es caudal ni un diseño conjunto de colector. Las tres plantas son alternativas: sus demandas no deben sumarse.
5. **Alternativas.** Para un origen representativo alcanzable se prueban hasta 80 cierres individuales de aristas y se conserva un desvío con al menos 300 m y 15 % de longitud nueva. Es exploración heurística, no búsqueda exhaustiva de diseños.
6. **Relieve posterior.** La pendiente NO es todavía el peso del grafo ni restringe el sentido de recorrido. Primero se calcula por distancia; después se audita elevación y pendiente sobre la traza.

## Método para elevación y pendiente

Se utilizan sólo los dos MDT de terreno originales de 1.5 m, transformando las coordenadas de consulta al CRS de cada archivo. No se utiliza MDS como sustituto, no se interpolan faltantes y no se asigna elevación a segmentos sin datos.

- **Perfiles longitudinales:** elevación cada 20 m y en extremos del camino, sin incluir accesos. Son alturas del suelo, no cotas de fondo de tubería o entrada hidráulica a planta.
- **Pendiente longitudinal exploratoria:** cada 100 m (último intervalo puede ser más corto), p = 100 × (z_final − z_inicial) / longitud. Se informa sólo si ambos extremos tienen dato y toda la traza del intervalo queda cubierta. Valor positivo significa subida en el sentido origen–destino; negativo, descenso.
- **Pendiente global:** diferencia de alturas de los extremos dividida por longitud vial total. No resume los obstáculos intermedios; sólo se presenta si las alturas de ambos extremos están disponibles. Debe revisarse además la cobertura del recorrido.
- **Mapas de pendiente superficial:** el MDT se agrega por promedio a celdas de 15 m y se calcula 100 × sqrt((dz/dx)^2+(dz/dy)^2) usando diferencias finitas. Es magnitud de la inclinación del terreno, sin dirección de conducción. La escala de color se limita a 0–15 % para visualizar, sin recortar los valores del GeoTIFF. El MDT original sigue siendo 1.5 m; los 15 m son un producto cartográfico derivado.

Los perfiles de Huejotzingo hacia Cabecera y Paseo descienden globalmente, pero todos contienen al menos un intervalo válido con ascenso superior a 0.5 %. Este umbral sólo señala dónde revisar; no es un criterio de bombeo o aceptación hidráulica. Santa Ana presenta pendientes globales suaves y algunos recorridos con subida neta en el extremo cubierto. La incertidumbre vertical y las variaciones locales impiden deducir gravedad a partir de la pendiente global.

## Mapas y archivos

- [Explorador del territorio y grafo](explorador_territorio_grafos.html), autónomo, sin mapas de internet. Activar capas en la leyenda.
- [Santa Ana: elevación](05_santa_ana_elevacion.png) y [pendiente superficial](05_santa_ana_pendiente.png).
- [Huejotzingo: elevación](05_huejotzingo_elevacion.png) y [pendiente superficial](05_huejotzingo_pendiente.png).
- [Santa Ana: recorridos internos](06_santa_ana_corredores.png) y [perfiles](07_santa_ana_perfiles.png).
- [Huejotzingo: rutas a PTAR](06_huejotzingo_corredores.png) y [perfiles](07_huejotzingo_perfiles.png).
- grafo_corredores_exploratorios.gpkg: red, rutas hacia PTAR, rutas locales de inspección, extremos y cobertura MDT, en capas distintas.
- GeoTIFF *_elevacion_15m.tif y *_pendiente_pct_15m.tif: productos cartográficos en EPSG:32614, con NoData explícito.
- matriz_origen_destino.csv: 195 pares origen–PTAR (102 conectados, 93 sin ruta).
- cobertura_pendientes_rutas.csv: 164 recorridos perfilados (102 hacia PTAR + 62 internos).
- pendientes_longitudinales_100m.csv: pendientes con validez de cobertura por intervalo.
- Inventarios de entregas, MDT, cobertura territorial, resúmenes y manifiestos para trazabilidad.

## Qué permite concluir y qué falta

Se puede continuar la exploración de corredores dentro de ambas localidades y comparar caminos hacia las plantas desde Huejotzingo. No se puede afirmar todavía que Santa Ana esté conectada a una PTAR por las vialidades actuales. Tampoco se puede afirmar viabilidad por gravedad, caudal atendido, diámetros o necesidad de bombeo.

Prioridades: revisar la conexión vial interurbana con una fuente que represente el enlace, completar MDT en Santa Ana occidental y Real Segovia, revisar cruces y accesos privados, y confirmar cotas de entrada/operación de PTAR. Para diseño se necesitan caudales y topografía de campo.

## Reproducción

Desde atoyac, con los puntos de establecimientos y plantas del paquete 09:

```powershell
python scripts/310_actualizar_vialidades_amplias.py
python scripts/311_territorio_pendientes_locales.py
python scripts/312_documentar_red_amplia.py
```

Los paquetes 08–11 se conservan como revisiones anteriores. El paquete 12 es la revisión vigente para vialidades, grafos y mapas de relieve. La selección del foco económico y de PTAR permanece igual.
'''
    (OUT/'reporte_red_amplia_territorio.md').write_text(report,encoding='utf-8')
    docs=ROOT/'docs/parte_3';docs.mkdir(parents=True,exist_ok=True)
    docreport=report.replace('](explorador_','](../../outputs/parte_3/12_vialidades_amplias/explorador_')
    for prefix in ['05_','06_','07_']:docreport=docreport.replace(']('+prefix,'](../../outputs/parte_3/12_vialidades_amplias/'+prefix)
    (docs/'04_red_amplia_territorio_pendientes.md').write_text(docreport,encoding='utf-8')
    (OUT/'README.md').write_text('''# Revisión vigente: vialidades amplias, grafos y relieve

Leer [reporte y método](reporte_red_amplia_territorio.md), abrir [explorador interactivo](explorador_territorio_grafos.html) o cargar grafo_corredores_exploratorios.gpkg y los GeoTIFF en QGIS.

La descarga amplia no conecta Santa Ana con las plantas. Se exploran 102 rutas de Huejotzingo hacia PTAR y 62 recorridos internos de Santa Ana a extremos de inspección, en capas diferentes. Cobertura de terreno parcial en Santa Ana y Real Segovia. No se infiere gravedad ni se diseña infraestructura.

Esta revisión conserva 08–11 y se reproduce con scripts 310–312 desde atoyac.
''',encoding='utf-8')
    # Validar productos realmente escritos y evitar que NoData extremo aparezca como relieve.
    gp=OUT/'grafo_corredores_exploratorios.gpkg'
    for layer in ['rutas_minimas','rutas_locales_santa_ana','cobertura_mdt_valida','extremos_inspeccion_santa_ana']:
        g=gpd.read_file(gp,layer=layer);assert g.is_valid.all() and not g.geometry.is_empty.any() and g.crs.to_epsg()==32614
    local=gpd.read_file(gp,layer='rutas_locales_santa_ana');assert len(local)==62 and local.destino_id.str.startswith('EXT_').all()
    assert len(matrix)==195 and int(matrix.conectado.sum())==102
    assert len(routes)==164 and routes.cobertura_longitud_pct.between(-.001,100.001).all()
    assert routes[routes.destino_id.eq('PTAR_066')].cobertura_longitud_pct.ge(99.999).all()
    assert routes[routes.destino_id.eq('PTAR_067')].cobertura_longitud_pct.ge(99.999).all()
    for path in OUT.glob('*15m.tif'):
        with rasterio.open(path) as src:
            a=src.read(1,masked=True);assert src.crs.to_epsg()==32614 and src.nodata==-9999
            assert np.isfinite(a.compressed()).all() and a.min()>=0 and a.max()<10000
    manifest={'python':platform.python_version(),'networkx':nx.__version__,'geopandas':gpd.__version__,'rasterio':rasterio.__version__,'scripts':[],'mdt':pd.read_csv(OUT/'inventario_mdt.csv').to_dict('records'),
        'validaciones':{'pares_origen_ptar':195,'rutas_hacia_ptar':102,'rutas_locales_santa_ana':62,'geometrias_validas':True,'nodata_rasters_validado':True}}
    for name in ['307_grafos_corredores_exploratorios.py','310_actualizar_vialidades_amplias.py','311_territorio_pendientes_locales.py','312_documentar_red_amplia.py']:
        p=ROOT/'scripts'/name;manifest['scripts'].append({'ruta':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    manifest['foco_09_sha256']=hashlib.sha256((ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg').read_bytes()).hexdigest()
    (OUT/'manifest_analisis_terreno.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    p=docs/'README.md';s=p.read_text(encoding='utf-8')
    marker='\n## Revisión vigente con descarga amplia\n'
    if marker not in s:p.write_text(s+marker+'\nScripts 310–312: todas las entregas viales, exploración local de Santa Ana y mapas de relieve. Productos: `outputs/parte_3/12_vialidades_amplias/`. [Método y resultados](04_red_amplia_territorio_pendientes.md). Las revisiones 08–11 se conservan como antecedentes.\n',encoding='utf-8')
    print('Reporte, mapas y validaciones correctos.');print(cov.to_string(index=False))

if __name__=='__main__':main()
