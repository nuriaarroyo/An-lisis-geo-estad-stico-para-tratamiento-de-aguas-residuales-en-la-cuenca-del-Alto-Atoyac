"""Genera una entrega portátil con resultados seleccionados y su procedencia."""
from pathlib import Path
import json,hashlib,shutil,zipfile
import geopandas as gpd
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]

def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def main():
    registry=json.loads((ROOT/'proyecto.json').read_text(encoding='utf-8'))
    current=ROOT/registry['parte3'];out=ROOT/registry['entrega']
    for name in ['reportes','figuras','datos']:(out/name).mkdir(parents=True,exist_ok=True)
    sources=[]
    def copy(src,dst):
        origin=ROOT/src;target=out/dst;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(origin,target);sources.append({'origen':str(src).replace('\\','/'),'destino':str(dst).replace('\\','/'),'sha256_origen':digest(origin),'transformacion':'copia sin cambios'})
    copy(Path('atoyac/docs/reporte_sintetico/reporte_sintetico.pdf'),Path('reportes/01_resumen_regional.pdf'))
    copy(Path(registry['pdf_caminos']),Path('reportes/02_explicacion_caminos.pdf'))
    copy(Path('atoyac/docs/parte_2/reporte/reporte_tecnico_parte_2.pdf'),Path('reportes/04_reporte_tecnico_parte2.pdf'))
    copy(Path('atoyac/outputs/parte_2/13_figuras_finales/02_clusters_principales.png'),Path('figuras/00_clusters_regionales.png'))
    images=['05_santa_ana_elevacion.png','05_santa_ana_pendiente.png','05_huejotzingo_elevacion.png','05_huejotzingo_pendiente.png','06_santa_ana_corredores.png','06_huejotzingo_corredores.png','07_santa_ana_perfiles.png','07_huejotzingo_perfiles.png']
    for name in images:copy(Path(registry['parte3'])/name,Path('figuras')/name)
    copy(Path(registry['parte3'])/'explorador_territorio_grafos.html',Path('explorador.html'))
    report=(current/'reporte_red_amplia_territorio.md').read_text(encoding='utf-8')
    report=report.replace('](explorador_territorio_grafos.html)','](../explorador.html)')
    for prefix in ['05_','06_','07_']:report=report.replace(']('+prefix,'](../figuras/'+prefix)
    (out/'reportes/03_resultados_parte3.md').write_text(report,encoding='utf-8')
    sources.append({'origen':(Path(registry['parte3'])/'reporte_red_amplia_territorio.md').as_posix(),'destino':'reportes/03_resultados_parte3.md','sha256_origen':digest(current/'reporte_red_amplia_territorio.md'),'transformacion':'reubicar enlaces a imágenes y explorador dentro de entrega'})
    # Vista de datos estable y reducida: conservar IDs y sólo los campos de lectura.
    focus=ROOT/registry['foco_puntos'];gp=current/'grafo_corredores_exploratorios.gpkg'
    est=gpd.read_file(focus,layer='establecimientos_foco')
    est['longitud']=est.to_crs(4326).geometry.x;est['latitud']=est.to_crs(4326).geometry.y
    est=est[['establecimiento_id','d_llave','nombre','scian','actividad','localidad','prioridad_ambiental','proceso_hidrico','zona_analisis','longitud','latitud','geometry']]
    plants=gpd.read_file(gp,layer='ptar_destinos')
    plants=plants[['ptar_id','nombre_fuente','municipio','capacidad_ls','caudal_tratado_ls','fuente','anio_fuente','estado_verificacion','registros_asociados','conciliacion','geometry']]
    road=gpd.read_file(gp,layer='vialidades_fuente')[['vialidad_id','CVEGEO','TIPO_VIAL','NOM_VIAL','archivo_origen','geometry']]
    individual=gpd.read_file(gp,layer='rutas_minimas')
    individual=individual[['ruta_id','origen_id','zona','destino_id','destino','longitud_vial_m','acceso_origen_m','acceso_destino_m','longitud_con_accesos_m','muestras_mdt_validas_pct','geometry']]
    internal=gpd.read_file(gp,layer='rutas_locales_santa_ana')
    internal=internal[['ruta_id','origen_id','zona','destino_id','destino','longitud_vial_m','cobertura_longitud_pct','pendiente_global_pct','geometry']]
    layers={'establecimientos':est,'ptar_candidatas':plants,'vialidades':road,'rutas_huejotzingo_a_ptar':individual,'recorridos_internos_santa_ana':internal,
        'corredores_compartidos':gpd.read_file(gp,layer='corredores_compartidos'),
        'extremos_inspeccion':gpd.read_file(gp,layer='extremos_inspeccion_santa_ana'),
        'cobertura_mdt':gpd.read_file(gp,layer='cobertura_mdt_valida'),
        'hidrografia_contexto':gpd.read_file(gp,layer='hidrografia_contexto')}
    temp=out/'datos/capas_temporales.gpkg'
    if temp.exists():raise RuntimeError('Existe una escritura temporal anterior; revisar antes de regenerar.')
    for name,g in layers.items():g.to_file(temp,layer=name,driver='GPKG',index=False)
    temp.replace(out/'datos/capas_seleccionadas.gpkg')
    est.drop(columns='geometry').to_csv(out/'datos/establecimientos.csv',index=False,encoding='utf-8-sig')
    plants.drop(columns='geometry').to_csv(out/'datos/ptar_candidatas.csv',index=False,encoding='utf-8-sig')
    table=pd.read_csv(current/'matriz_origen_destino.csv')
    selected=table[table.conectado].merge(pd.read_csv(current/'cobertura_pendientes_rutas.csv')[['ruta_id','cobertura_longitud_pct','pendiente_global_pct']],on='ruta_id',how='left')
    selected['tipo_destino']='PTAR';local=internal.drop(columns='geometry').copy();local['tipo_destino']='extremo_inspeccion_no_PTAR'
    fields=['ruta_id','origen_id','zona','tipo_destino','destino_id','destino','longitud_vial_m','acceso_origen_m','acceso_destino_m','longitud_con_accesos_m','cobertura_longitud_pct','pendiente_global_pct']
    paths=pd.concat([selected,local],ignore_index=True).reindex(columns=fields)
    paths.to_csv(out/'datos/caminos_minimos.csv',index=False,encoding='utf-8-sig')
    for name in ['cobertura_territorial.csv','resumen_cobertura_pendientes.csv']:copy(Path(registry['parte3'])/name,Path('datos')/name)
    dictionary=[
        ('establecimiento_id','Identificador del establecimiento en la integración; d_llave conserva su referencia original.'),
        ('prioridad_ambiental','Señal alta/media/por_revisar según actividad y texto; no caudal ni contaminación demostrada.'),
        ('ptar_id / destino_id','Registro representante de planta o extremo EXT de inspección; no acredita operación.'),
        ('tipo_destino','PTAR o extremo_inspeccion_no_PTAR: no mezclar ambos tipos de resultado.'),
        ('registros_asociados / conciliacion','IDs de fuentes reunidos provisionalmente por nombre y coordenadas; conservar evidencia original.'),
        ('longitud_vial_m','Camino mínimo por aristas viales, en metros, sin accesos.'),
        ('acceso_origen_m / acceso_destino_m','Enlaces geométricos a calle más próxima; no conexiones sanitarias comprobadas.'),
        ('longitud_con_accesos_m','Longitud vial más ambos accesos, sólo cuando se informa.'),
        ('cobertura_longitud_pct','Porcentaje de longitud de la traza dentro de píxeles válidos del MDT.'),
        ('pendiente_global_pct','100 × diferencia de alturas / longitud; negativa es descenso. No garantiza gravedad.'),
        ('n_origenes','Número de caminos de un mismo destino que comparten arista; no caudal.'),
        ('capacidad_ls / caudal_tratado_ls','Valores reportados de PTAR; no disponibilidad actual ni eficiencia de remoción.'),
        ('coordenadas','Vectores EPSG:32614; longitud/latitud en CSV de establecimientos EPSG:4326.'),
        ('campo vacío','Dato no disponible/no calculado; no interpretar como cero.')]
    pd.DataFrame(dictionary,columns=['campo','interpretacion']).to_csv(out/'datos/DICCIONARIO.csv',index=False,encoding='utf-8-sig')
    readme='''# Entrega de lectura — Alto Atoyac

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
'''
    (out/'LEEME.md').write_text(readme,encoding='utf-8')
    sources.extend([{'origen':registry['foco_puntos'],'destino':'datos/establecimientos.csv;datos/capas_seleccionadas.gpkg','sha256_origen':digest(focus),'transformacion':'selección de campos, preservar IDs y geometrías; añadir lon/lat'},
        {'origen':str(gp.relative_to(ROOT)).replace('\\','/'),'destino':'datos/capas_seleccionadas.gpkg;datos/caminos_minimos.csv','sha256_origen':digest(gp),'transformacion':'selección de capas/campos de lectura; sin recalcular caminos'},
        {'origen':str((current/'matriz_origen_destino.csv').relative_to(ROOT)).replace('\\','/'),'destino':'datos/caminos_minimos.csv','sha256_origen':digest(current/'matriz_origen_destino.csv'),'transformacion':'sólo rutas conectadas, añadir cobertura y recorridos internos; 164 filas'}])
    inventory=[]
    for p in sorted(out.rglob('*')):
        if p.is_file() and p.name!='MANIFIESTO.json':inventory.append({'ruta':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':digest(p)})
    manifest={'corte':registry['corte'],'autora':registry['autora'],'revision_analitica':registry['parte3'],'fuentes_y_transformaciones':sources,'archivos':inventory,
        'conteos':{'establecimientos':len(est),'ptar_nucleo':len(plants),'rutas_ptar':len(individual),'recorridos_internos':len(internal),'caminos_tabla':len(paths)},
        'generador_sha256':digest(Path(__file__))}
    (out/'MANIFIESTO.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    dist=ROOT/'dist';dist.mkdir(exist_ok=True);archive=dist/f'alto_atoyac_entrega_{registry["corte"]}.zip'
    tempzip=dist/'entrega_temporal.zip'
    with zipfile.ZipFile(tempzip,'w',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,Path('alto_atoyac')/p.relative_to(out))
    with zipfile.ZipFile(tempzip) as z:assert z.testzip() is None
    tempzip.replace(archive)
    print(f'Entrega: {len(inventory)+1} archivos. ZIP: {archive.relative_to(ROOT)} ({archive.stat().st_size/1e6:.1f} MB).')
    print(json.dumps(manifest['conteos'],ensure_ascii=False))

if __name__=='__main__':main()
