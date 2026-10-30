"""Audita cobertura e integra vialidades, MDT y puntos de Parte 3; no modela drenaje."""
from pathlib import Path
import hashlib
import json
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio
from rasterio.features import shapes
from shapely.geometry import box, shape
from shapely.ops import unary_union
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'outputs/parte_3/08_integracion_vialidades_terreno'
BASE = ROOT / 'outputs/parte_3/parte_3_sistema_saneamiento_integrado.gpkg'
CRS = 'EPSG:32614'
TARGETS = {'santa_ana': ('Santa Ana Xalmimilulco', 'santa ana', '210740029'),
           'huejotzingo': ('Huejotzingo', 'huejotzingo', '210740001')}

def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    gpkg = OUT / 'localidades_vialidades_terreno.gpkg'
    est = gpd.read_file(BASE, layer='establecimientos_textiles').to_crs(CRS)
    ptar = gpd.read_file(BASE, layer='ptar').to_crs(CRS)
    roads_all, inventories, footprints, sources = [], [], [], []
    for p in sorted((ROOT / 'data/raw/vialidades').rglob('*.shp')):
        g = gpd.read_file(p).to_crs(CRS)
        g['vialidad_id'] = [f'{p.parent.name}_{i:06d}' for i in range(len(g))]
        g['ruta_fuente'] = str(p.relative_to(ROOT))
        g['archivo_origen'] = p.parent.name
        inventories.append({'archivo':str(p.relative_to(ROOT)), 'tramos':len(g),
            'invalidos':int((~g.is_valid).sum()), 'vacios':int(g.geometry.is_empty.sum()),
            'duplicados_geometria':int(g.geometry.to_wkb().duplicated().sum()),
            'fecha_act_sin_dato':int(g.FECHA_ACT.isna().sum()),
            'claves_localidad':';'.join(sorted(g.CVEGEO.unique()))})
        roads_all.append(g)
    roads = gpd.GeoDataFrame(pd.concat(roads_all,ignore_index=True),crs=CRS)
    # Sólo eliminar geometrías exactamente repetidas en la red de consulta.
    roads = roads.loc[~roads.geometry.to_wkb().duplicated()].copy()
    rasters = sorted((ROOT / 'data/raw/terreno').rglob('*.bil'))
    terrain = [p for p in rasters if p.stem.endswith('_mt')]
    valid_geoms = []
    for p in rasters:
        with rasterio.open(p) as src:
            valid = src.read_masks(1) > 0
            geom = unary_union([shape(s) for s,v in shapes(valid.astype('uint8'),mask=valid,transform=src.transform) if v==1])
            row = {'archivo':str(p.relative_to(ROOT)), 'tipo':'MDT' if p in terrain else 'MDS',
                   'resolucion_m':src.res[0], 'crs_fuente':str(src.crs),
                   'porcentaje_pixeles_validos':float(valid.mean()*100), 'geometry':geom}
            foot = gpd.GeoDataFrame([row],crs=src.crs).to_crs(CRS)
            footprints.append(foot)
            if p in terrain: valid_geoms.append(foot.geometry.iloc[0])
            sources.append({'ruta':str(p.relative_to(ROOT)), 'sha256':digest(p), 'tipo':row['tipo']})
    valid_union = unary_union(valid_geoms)
    def elevations(points):
        values=np.full(len(points),np.nan); origin=np.full(len(points),'',dtype=object)
        for path in terrain:
            with rasterio.open(path) as src:
                q=points.to_crs(src.crs)
                vals=list(src.sample([(p.x,p.y) for p in q.geometry],masked=True))
                for i,v in enumerate(vals):
                    if not np.ma.is_masked(v[0]) and np.isfinite(v[0]) and np.isnan(values[i]):
                        values[i]=float(v[0]); origin[i]=str(path.relative_to(ROOT))
        return values,origin
    summaries=[]; outputs={'vialidades_regionales':roads,
        'cobertura_rasters':gpd.GeoDataFrame(pd.concat(footprints,ignore_index=True),crs=CRS)}
    for slug,(name,folder,code) in TARGETS.items():
        e=est[est.localidad.eq(name)].copy().reset_index(drop=True)
        local_roads=roads[roads.CVEGEO.eq(code)].copy()
        delivered_roads=roads[roads.archivo_origen.eq(folder)]
        dlocal=gpd.sjoin_nearest(e[['establecimiento_id','geometry']],delivered_roads[['geometry']],distance_col='dist_entrega_m').groupby('establecimiento_id').dist_entrega_m.min()
        zone=e.geometry.union_all().convex_hull.buffer(2000)
        p=ptar[ptar.distance(e.geometry.union_all().centroid)<=10000].copy().reset_index(drop=True)
        r=roads[roads.intersects(zone)].copy()
        # Mantener los puntos originales: las distancias no prueban conexión sanitaria.
        for points,key in [(e,'establecimiento_id'),(p,'ptar_id')]:
            points['z_mdt_m'],points['fuente_mdt']=elevations(points)
            nearest=gpd.sjoin_nearest(points[[key,'geometry']],roads[['vialidad_id','geometry']],distance_col='dist_vial_m')
            nearest=nearest.sort_values(['dist_vial_m','vialidad_id']).drop_duplicates(key).set_index(key)
            points['vialidad_proxima_id']=points[key].map(nearest.vialidad_id)
            points['dist_vial_m']=points[key].map(nearest.dist_vial_m)
            points['tipo_relacion']='proximidad_geometrica_no_conexion'
            points.drop(columns='geometry').to_csv(OUT/f'{slug}_{key}_cobertura.csv',index=False,encoding='utf-8-sig')
        r['longitud_m']=r.length
        r['longitud_con_mdt_m']=r.geometry.intersection(valid_union).length
        summaries.append({'localidad':name,'establecimientos':len(e),'tramos_clave_localidad':len(local_roads),
            'dist_max_vial_archivo_local_m':float(dlocal.max()),'establecimientos_100m_archivo_local':int(dlocal.le(100).sum()),'tramos_zona_2km':len(r),'establecimientos_con_mdt':int(e.z_mdt_m.notna().sum()),
            'dist_vial_mediana_m':float(e.dist_vial_m.median()),'dist_vial_max_m':float(e.dist_vial_m.max()),
            'establecimientos_vial_menos_50m':int(e.dist_vial_m.le(50).sum()),
            'establecimientos_vial_menos_100m':int(e.dist_vial_m.le(100).sum()),
            'ptar_10km_registros':len(p),'ptar_10km_con_mdt':int(p.z_mdt_m.notna().sum()),
            'porcentaje_longitud_vial_zona_con_mdt':float(100*r.longitud_con_mdt_m.sum()/r.longitud_m.sum()),
            'porcentaje_area_zona_con_mdt':float(100*zone.intersection(valid_union).area/zone.area)})
        outputs.update({f'{slug}_establecimientos':e,f'{slug}_ptar_10km':p,f'{slug}_vialidades':r,
                       f'{slug}_zona_operativa':gpd.GeoDataFrame([{'criterio':'envolvente establecimientos + 2 km; no limite oficial','geometry':zone}],crs=CRS)})
        fig,ax=plt.subplots(figsize=(10,9))
        gpd.GeoSeries(valid_geoms,crs=CRS).boundary.plot(ax=ax,color='green',linewidth=1.5,label='Limite MDT valido')
        r.plot(ax=ax,color='#999999',linewidth=.5)
        e.plot(ax=ax,color='#6a3d9a',markersize=12,label='Establecimientos')
        p.plot(ax=ax,color='#e66101',marker='^',markersize=65,label='PTAR registradas (10 km)')
        for _,row in p.iterrows(): ax.annotate(row.ptar_id,(row.geometry.x,row.geometry.y),fontsize=6)
        ax.set_title(f'{name}: vialidades, establecimientos y cobertura MDT')
        ax.set_aspect('equal');ax.legend(fontsize=8)
        fig.text(.03,.015,'EPSG:32614 | Verde: cobertura MDT disponible | Proximidad no acredita conexion sanitaria',fontsize=8)
        fig.savefig(OUT/f'{slug}_cobertura.png',dpi=170,bbox_inches='tight');plt.close(fig)
    # Escribir a temporal y sustituir sólo el producto propio una vez completado.
    temp=OUT/'integracion_temporal.gpkg'
    if temp.exists():temp.unlink()
    for layer,g in outputs.items():
        g.to_file(temp,layer=layer,driver='GPKG',index=False)
    temp.replace(gpkg)
    pd.DataFrame(inventories).to_csv(OUT/'inventario_vialidades.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(summaries).to_csv(OUT/'resumen_cobertura.csv',index=False,encoding='utf-8-sig')
    for p in (ROOT/'data/raw/vialidades').rglob('*'):
        if p.is_file():sources.append({'ruta':str(p.relative_to(ROOT)),'sha256':digest(p),'tipo':'vialidad_auxiliar_o_vector'})
    (OUT/'fuentes_sha256.json').write_text(json.dumps(sources,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'README.md').write_text('''# Integración local de vialidades y terreno

Ejecutar desde atoyac: `python scripts/305_integrar_vialidades_terreno.py`.

Abrir `localidades_vialidades_terreno.gpkg` en QGIS. Los BIL originales se cargan por separado; la capa cobertura_rasters conserva sus rutas y tipo MDT/MDS. Todos los vectores se homologan a EPSG:32614; el muestreo transforma cada punto al CRS nativo del raster. No se reproyectan ni alteran los originales.

Las localidades se seleccionan por nombre exacto de DENUE y vialidades por CVEGEO 210740029 (Santa Ana) / 210740001 (Huejotzingo). No se cuenta con polígonos oficiales de localidad: no se acredita exhaustividad de calles mediante un límite oficial. La zona operativa es envolvente de establecimientos + 2 km, no área tributaria. Los puntos de PTAR se seleccionan a 10 km del centroide; son registros sin conciliación física.

La cobertura MDT usa la máscara de píxeles válidos, no sólo el rectángulo del archivo. Se informa cobertura en establecimientos, PTAR y longitud de vialidad dentro de la zona; no certifica corredores externos hasta PTAR. Las elevaciones se muestrean por píxel, sin interpolar huecos. Se utiliza exclusivamente MDT para z_mdt_m; MDS queda como referencia. Revisar precisión y referencia vertical en los metadatos antes de calcular pendientes hidráulicas.

Las distancias a vialidad se calculan contra los tres archivos regionales y conservan el ID de tramo. Umbrales 50/100 m son indicadores diagnósticos de proximidad, no prueba de acceso ni conexión. No se ajustan los puntos a calles. No se valida topología, cruces a distinto nivel, transitabilidad o continuidad de un grafo sanitario. Se eliminan únicamente geometrías viales exactamente repetidas en la red de consulta.

Los diagnósticos históricos 304 sobre ausencia de vialidad y topografía quedaron desactualizados: sus mensajes están fijados en código. Este producto registra la nueva entrega sin sobrescribir la integración previa.
''',encoding='utf-8')
    print(json.dumps(summaries,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
