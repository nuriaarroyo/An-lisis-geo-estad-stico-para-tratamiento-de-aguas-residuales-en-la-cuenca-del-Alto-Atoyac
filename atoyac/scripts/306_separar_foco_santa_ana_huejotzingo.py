"""Separa el foco Santa Ana-Huejotzingo sin modificar los inventarios regionales."""
from pathlib import Path
import geopandas as gpd
import pandas as pd
import json

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'outputs/parte_3/08_integracion_vialidades_terreno'
OUT=ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo'
CRS='EPSG:32614'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    src=SOURCE/'localidades_vialidades_terreno.gpkg'
    layers={}
    establishments=[];roads=[];plants=[];zones=[]
    for slug in ['santa_ana','huejotzingo']:
        for suffix,collection in [('establecimientos',establishments),('vialidades',roads),('ptar_10km',plants),('zona_operativa',zones)]:
            g=gpd.read_file(src,layer=slug+'_'+suffix)
            g['zona_analisis']=slug
            collection.append(g)
    def concat(items):return gpd.GeoDataFrame(pd.concat(items,ignore_index=True),crs=CRS)
    e=concat(establishments);r=concat(roads).drop_duplicates('vialidad_id');p=concat(plants)
    relation=p[['ptar_id','zona_analisis']].drop_duplicates()
    mapping={'PTAR_005':'PTAR_066','PTAR_015':'PTAR_069'}
    relation['instalacion_trabajo_id']=relation.ptar_id.replace(mapping)
    relation['criterio']='a menos de 10 km del centroide de establecimientos; no conexion ni servicio'
    relation.to_csv(OUT/'ptar_registros_zonas.csv',index=False,encoding='utf-8-sig')
    p=p.drop_duplicates('ptar_id').copy()
    p['instalacion_trabajo_id']=p.ptar_id.replace(mapping)
    p['zona_analisis']=p.ptar_id.map(relation.groupby('ptar_id').zona_analisis.agg(lambda x:';'.join(sorted(set(x)))))
    layers['ptar_registros_originales']=p.copy()
    # Representante de compilación manual conserva datos técnicos; equivalencia provisional.
    p=p[~p.ptar_id.isin(mapping)].copy()
    p['registros_asociados']=p.ptar_id.map({'PTAR_066':'PTAR_005;PTAR_066','PTAR_069':'PTAR_015;PTAR_069'}).fillna(p.ptar_id)
    p['conciliacion']=p.ptar_id.map({'PTAR_066':'probable_misma_instalacion_nombre_y_coordenadas','PTAR_069':'probable_misma_instalacion_nombre_y_coordenadas'}).fillna('registro_individual_sin_confirmacion_operativa')
    p['papel_analisis']=p.municipio.eq('Huejotzingo').map({True:'nucleo_local',False:'contexto_externo'})
    p['zona_analisis']=p.ptar_id.map(relation.groupby('instalacion_trabajo_id').zona_analisis.agg(lambda x:';'.join(sorted(set(x)))))
    p['elevacion_disponible']=p.z_mdt_m.notna()
    layers.update({'establecimientos_foco':e,'vialidades_zonas':r,'zonas_operativas':concat(zones),
        'ptar_nucleo_local':p[p.papel_analisis.eq('nucleo_local')],
        'ptar_contexto_externo':p[p.papel_analisis.eq('contexto_externo')],
        'cobertura_terreno_superficie':gpd.read_file(src,layer='cobertura_rasters')})
    tmp=OUT/'foco_temporal.gpkg'
    if tmp.exists():tmp.unlink()
    for name,g in layers.items():g.to_file(tmp,layer=name,driver='GPKG',index=False)
    tmp.replace(OUT/'foco_santa_ana_huejotzingo.gpkg')
    p.drop(columns='geometry').to_csv(OUT/'catalogo_ptar_foco.csv',index=False,encoding='utf-8-sig')
    rasters=layers['cobertura_terreno_superficie'].drop(columns='geometry').copy()
    rasters['ruta_desde_paquete']=rasters.archivo.map(lambda s: str(Path('../../..')/s))
    rasters.to_csv(OUT/'referencias_rasters.csv',index=False,encoding='utf-8-sig')
    checks=[]
    for name,g in layers.items():
        check={'capa':name,'objetos':len(g),'epsg':g.crs.to_epsg(),'invalidas':int((~g.is_valid).sum()),'vacias':int(g.geometry.is_empty.sum())}
        assert check['epsg']==32614 and check['invalidas']==0 and check['vacias']==0
        checks.append(check)
    assert len(e)==408 and e.establecimiento_id.is_unique
    assert len(p)==8 and len(layers['ptar_nucleo_local'])==3
    (OUT/'validacion.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    (OUT/'README.md').write_text('''# Foco actual: Santa Ana Xalmimilulco y Huejotzingo

Abrir foco_santa_ana_huejotzingo.gpkg. Ejecutar desde atoyac: `python scripts/306_separar_foco_santa_ana_huejotzingo.py`, después del 305.

## Alcance

408 establecimientos sectoriales: 337 de Santa Ana y 71 de la localidad de Huejotzingo, seleccionados por localidad DENUE exacta, no por municipio completo. Vialidades recortadas por selección de intersección con envolventes de establecimientos + 2 km; los segmentos se conservan completos. Estas zonas no son límites oficiales ni áreas tributarias.

## Plantas

Núcleo local: Cabecera Municipal, Paseo de los Sauces y Real Segovia, todas registradas en el municipio de Huejotzingo. No hay PTAR registrada dentro de la zona operativa de Santa Ana en el inventario utilizado (verificar por separado si se cambia su delimitación). No se adjudica exclusividad de servicio a ninguna localidad.

Contexto externo: Chiautzingo, Tres Besanas, San Lucas Atoyatenco y los dos registros de Domingo Arenas. Se conserva para comparación posterior, separado del núcleo. La selección original fue por 10 km desde el centroide de cada localidad; no acredita aptitud, conexión ni inventario exhaustivo de plantas existentes.

Se reúnen provisionalmente los pares 005/066 y 015/069 como instalaciones de trabajo; se conserva el registro manual como representante por sus datos complementarios. La capa ptar_registros_originales y ptar_registros_zonas.csv conservan los 10 registros y procedencias originales. Resultan 8 instalaciones de trabajo: 3 locales y 5 externas. Domingo Arenas sigue separado.

## Estado para iniciar

Establecimientos identificados: sí, dentro del universo sectorial analizado; actividad y procesos reales pendientes de campo.
Vialidad local: buena correspondencia con establecimientos, sin certificación de exhaustividad ni topología. Esta capa local no garantiza corredores continuos hasta PTAR; consultar la red regional del paquete 08 y ampliar donde falte.
Elevación: dos MDT de 1.5 m, 331/337 establecimientos de Santa Ana y 71/71 de Huejotzingo cubiertos. Cabecera Municipal y Paseo de los Sauces con MDT; Real Segovia sin MDT. Faltan hojas para completar Santa Ana occidental y corredores externos. MDS se conserva sólo como contexto. Los BIL originales se cargan aparte usando referencias_rasters.csv; no están embebidos en el GeoPackage.
Plantas: inventario registral integrado, no operación/capacidad de recepción confirmadas. Datos de capacidad disponibles para Paseo de los Sauces y Real Segovia, ausentes para Cabecera Municipal.

Se puede iniciar integración y diagnóstico espacial de Parte 3. Para comparar trazos por gravedad faltan completar MDT, revisar continuidad vial y cotas; para diseñar, confirmar operación de plantas, caudales, conexiones y topografía de campo.
''',encoding='utf-8')
    print(pd.DataFrame(checks).to_string(index=False))
    print(p[['ptar_id','nombre_fuente','papel_analisis','elevacion_disponible']].to_string(index=False))

if __name__=='__main__':main()
