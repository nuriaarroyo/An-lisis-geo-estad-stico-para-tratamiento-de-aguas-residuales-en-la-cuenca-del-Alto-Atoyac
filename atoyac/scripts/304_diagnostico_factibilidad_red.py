"""Diagnóstico de datos previo a corredores; no construye grafos ni rutas."""
from pathlib import Path
import json, re
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio

R=Path(__file__).resolve().parents[1]; P3=R/'outputs'/'parte_3'; G=P3/'parte_3_sistema_saneamiento_integrado.gpkg'
O=P3/'07_factibilidad_red'; D=O/'00_diagnostico'; S=O/'01_santa_ana'; D.mkdir(parents=True,exist_ok=True);S.mkdir(parents=True,exist_ok=True)
CRS='EPSG:32614'
def rd(n): return gpd.read_file(G,layer=n).to_crs(CRS)
def norm(x): return re.sub(r'[^A-Z0-9]+',' ',str(x).upper()).strip()
est,clu,sub,des,ptar,hid,mun,cuenca=[rd(x) for x in ['establecimientos_textiles','clusters_parte2','subnucleos_parte2','descargas','ptar','hidrografia','municipios','limite_cuenca']]

# Fase 1: inventario de capas recibidas y productos canónicos.
inv0=pd.read_csv(P3/'01_insumos_organizados'/'inventario_capas_espaciales.csv')
inv0=inv0.rename(columns={'ruta_relativa':'ruta','objetos':'numero_objetos'})
inv0['fuente']=np.where(inv0.ruta.str.contains('702825',na=False),'INEGI Red Hidrográfica RH18',np.where(inv0.ruta.str.contains('cngmd',case=False,na=False),'INEGI CNGMD 2021','Entrega colaboradora/CAARESA'))
inv0['anio']=np.where(inv0.ruta.str.contains('cngmd',case=False,na=False),'2021 (descarga 2023)',np.where(inv0.ruta.str.contains('RH18',na=False),'según campo FECHA/EDICION','no documentado'))
inv0['porcentaje_campos_faltantes']='requiere lectura por campo; ver campos_utiles_por_capa.csv'
inv0['cobertura_territorial']=np.where(inv0.ruta.str.contains('cngmd',case=False,na=False),'nacional',np.where(inv0.ruta.str.contains('RH18',na=False),'hojas RH18','cuenca/contexto'))
inv0['municipios_cubiertos']='variable/no aplicable';inv0['duplicados_potenciales']='no evaluado en inventario físico'
inv0['coordenadas_sospechosas']='sin señal automática en lectura inicial'
inv0['utilidad_modelo_red']=np.select([inv0.ruta.str.contains('RH18.*hl',case=False,regex=True),inv0.ruta.str.contains('municip|cuenca',case=False,regex=True),inv0.ruta.str.contains('cngmd|PTAR',case=False,regex=True)],['restricción/contexto hidrográfico','delimitación territorial','orígenes/destinos contextuales'],default='documental o auxiliar')
inv0['limitaciones']='No acredita conectividad, operación ni aptitud hidráulica'
cols=['capa','ruta','fuente','anio','geometria','crs','numero_objetos','campos','porcentaje_campos_faltantes','cobertura_territorial','municipios_cubiertos','duplicados_potenciales','coordenadas_sospechosas','utilidad_modelo_red','limitaciones']
inv0.reindex(columns=cols).to_csv(D/'inventario_insumos_red.csv',index=False,encoding='utf-8-sig')
cam=[]
for layer in pyogrio.list_layers(G)[:,0]:
    info=pyogrio.read_info(G,layer=layer)
    try:g=gpd.read_file(G,layer=layer)
    except:continue
    for c in g.columns:
        cam.append({'capa':layer,'campo':c,'tipo':str(g[c].dtype),'porcentaje_faltante':round(g[c].isna().mean()*100,2),'utilidad':('geometría' if c=='geometry' else 'identificación/trazabilidad/modelado según semántica'),'advertencia':'Validar definición de fuente; no inferir por nombre'})
pd.DataFrame(cam).to_csv(D/'campos_utiles_por_capa.csv',index=False,encoding='utf-8-sig')

# Fase 2: descargas y cauce próximo derivado.
near=gpd.sjoin_nearest(des,hid[['hidrografia_id','geometry']],distance_col='distancia_cauce_m')
near['receptor_declarado']=near.cuerpo_receptor;near['cauce_mas_cercano']=near.hidrografia_id
near['tipo_evidencia_receptor']=np.where(near.receptor_declarado.notna(),'A_declarado_y_C_proximidad_separados','C_solo_proximidad_geometrica')
near.drop(columns=['geometry','index_right']).to_csv(S/'descargas_diagnostico.csv',index=False,encoding='utf-8-sig')
freq=[]
for c in ['cuerpo_receptor','tipo_descarga','nombre_sistema','municipio','fuente','estado_verificacion']:
    for v,n in des[c].fillna('[SIN DATO]').value_counts(dropna=False).items():freq.append({'campo':c,'valor':v,'frecuencia':n})
pd.DataFrame(freq).to_csv(S/'frecuencias_campos_descargas.csv',index=False,encoding='utf-8-sig')

# Delimitación operativa piloto: envolvente de establecimientos DENUE de la localidad + 2 km.
x=est[est.localidad.astype(str).str.contains('Xalmimilulco',case=False,na=False)].copy(); centro=x.geometry.union_all().centroid
piloto=gpd.GeoDataFrame([{'zona_id':'XALMI_OPERATIVA','criterio':'envolvente convexa de establecimientos con localidad DENUE Santa Ana Xalmimilulco + buffer 2 km','geometry':x.geometry.union_all().convex_hull.buffer(2000)}],crs=CRS)
geom=piloto.geometry.iloc[0]; dx=des[des.intersects(geom)].copy(); px=ptar[ptar.distance(centro)<=10000].copy(); hx=gpd.clip(hid,piloto)
cx=clu[clu.intersects(geom)].copy(); sx=sub[sub.intersects(geom)].copy(); mx=mun[mun.intersects(geom)].copy()
gpkg=S/'santa_ana_piloto.gpkg'
if gpkg.exists():gpkg.unlink()
for n,g in [('zona_operativa',piloto),('establecimientos',x),('clusters',cx),('subnucleos',sx),('hidrografia',hx),('descargas',dx),('ptar_10km',px),('municipios_contexto',mx)]:pyogrio.write_dataframe(g,gpkg,layer=n,driver='GPKG',append=gpkg.exists())

# Fase 3: PTAR y aptitud de datos, sin evaluar capacidad de recibir efluente textil.
p=ptar.copy();p['utilizacion_capacidad_reportada']=p.caudal_tratado_ls/p.capacidad_ls
req=p[['capacidad_ls','caudal_tratado_ls','proceso','estado_operativo_reportado']].notna().sum(axis=1)
p['aptitud_para_evaluacion_destino']=np.select([req>=3,req>=1],['datos_suficientes_para_estudiar','datos_parciales'],default='datos_insuficientes')
p['variables_faltantes']='capacidad libre real; compatibilidad con efluente textil; calidad admisible; operación; permisos; pretratamiento'
p.drop(columns='geometry').to_csv(S/'ptar_diagnostico_destinos.csv',index=False,encoding='utf-8-sig')

# Fase 4: catálogo prudente; RH18 no contiene nombres de cauce.
cat=pd.DataFrame([
['RIO ATOYAC','Río Atoyac','río',True,'capa dedicada RioAtoyac + mención documental','B','Geometría disponible, conciliación nominal no embebida en RH18'],
['RIO XOCHIAC','Río Xochiac','río',False,'mención documental','D','No hay atributo nominal o geometría conciliable'],
['RIO TENITZATL','Río Tenitzatl','río',False,'mención documental','D','No hay atributo nominal o geometría conciliable'],
['RIO XOPANAC','Río Xopanac','río',False,'mención documental','D','No hay atributo nominal o geometría conciliable'] ],columns=['nombre_normalizado','nombre_original','tipo','geometria_encontrada','fuente','nivel_confianza','observaciones'])
cat.to_csv(O/'catalogo_cuerpos_receptores.csv',index=False,encoding='utf-8-sig')

# Fases 5-6: búsqueda ya auditada en todo el repositorio.
(O/'diagnostico_topografia.md').write_text('# Diagnóstico de topografía\n\nNo se encontraron DEM, MDT/MDE, CEM, SRTM, LiDAR, curvas de nivel ni puntos de elevación en el repositorio. Es un faltante crítico: no puede evaluarse pendiente, gravedad ni bombeo. Para la siguiente etapa se recomienda un DEM documentado de 5--15 m para prefactibilidad; para diseño, levantamiento topográfico de mayor precisión. No se descargó información nueva.\n',encoding='utf-8')
(O/'diagnostico_red_vial.md').write_text('# Diagnóstico de red vial\n\nNo existe una capa vectorial de calles o caminos en el repositorio. Las menciones a “camino” en el QGIS corresponden a nodos huérfanos asociados a posibles trazos de colector, no a una red vial. Por tanto no pueden evaluarse cobertura, continuidad, intersecciones, jerarquía, restricciones ni conectividad, y todavía no puede construirse un grafo.\n',encoding='utf-8')

# Fases 7-8: orígenes y destinos candidatos, sin selección.
orig=[]
for _,r in x[x.prioridad_ambiental.isin(['alta','media'])].iterrows():
    orig.append({'origen_id':f"ORI_{len(orig)+1:03d}",'tipo_origen':'establecimiento','establecimiento_subnucleo':r.establecimiento_id,'n_establecimientos':1,'alta_relevancia':int(r.prioridad_ambiental=='alta'),'media_relevancia':int(r.prioridad_ambiental=='media'),'proceso_humedo':int(r.proceso_hidrico=='humedo'),'x_utm':r.geometry.x,'y_utm':r.geometry.y,'nivel_confianza':'B_localizacion_C_generacion','justificacion':'Prioridad alta/media; caudal individual desconocido'})
orig.append({'origen_id':f"ORI_{len(orig)+1:03d}",'tipo_origen':'concentracion_cluster','establecimiento_subnucleo':'CLU_008_XALMIMILULCO','n_establecimientos':len(x),'alta_relevancia':(x.prioridad_ambiental=='alta').sum(),'media_relevancia':(x.prioridad_ambiental=='media').sum(),'proceso_humedo':(x.proceso_hidrico=='humedo').sum(),'x_utm':centro.x,'y_utm':centro.y,'nivel_confianza':'B_concentracion_C_generacion','justificacion':'Representa concentración completa; no equivale a punto hidráulico'})
pd.DataFrame(orig).to_csv(O/'origenes_candidatos_santa_ana.csv',index=False,encoding='utf-8-sig')
dest=[]
for _,r in px.iterrows():
    dist=r.geometry.distance(centro)
    dest.append({'destino_id':f"DST_{len(dest)+1:03d}",'tipo_destino':'PTAR_registrada','nombre':r.nombre_fuente,'capacidad_reportada':r.capacidad_ls,'caudal_reportado':r.caudal_tratado_ls,'proceso':r.proceso,'estado_operativo':r.estado_operativo_reportado,'distancia_aproximada_m':round(dist,1),'nivel_evidencia':r.estado_verificacion,'datos_faltantes':'capacidad libre; compatibilidad; operación; permisos; conducción; pretratamiento','justificacion_para_estudiarlo':'PTAR dentro de 10 km del centroide operativo; no implica aptitud ni conexión'})
pd.DataFrame(dest).to_csv(O/'destinos_candidatos_santa_ana.csv',index=False,encoding='utf-8-sig')

# Fase 9.
status={'puntos origen':'DISPONIBLE','clasificación ambiental':'DISPONIBLE','caudal por origen':'AUSENTE','puntos destino':'PARCIAL','capacidad de tratamiento':'PARCIAL','red vial':'AUSENTE','elevación':'AUSENTE','pendiente':'AUSENTE','hidrografía':'DISPONIBLE','cruces de cauces':'PARCIAL','uso de suelo':'AUSENTE','restricciones constructivas':'AUSENTE','derechos de vía':'AUSENTE','áreas inundables':'AUSENTE','propiedad/disponibilidad de terreno':'AUSENTE','costo de construcción':'AUSENTE','diámetros requeridos':'AUSENTE','necesidad de bombeo':'AUSENTE'}
pd.DataFrame([{'componente':k,'estado':v,'observacion':'Diagnóstico de datos; no evaluación de factibilidad hidráulica'} for k,v in status.items()]).to_csv(O/'matriz_prefactibilidad_red.csv',index=False,encoding='utf-8-sig')
falt=pd.DataFrame([{'componente':k,'prioridad':'CRITICA' if k in ['caudal por origen','red vial','elevación','pendiente'] else 'ALTA','estado':v,'accion_requerida':'obtener, documentar y validar antes del grafo'} for k,v in status.items() if v!='DISPONIBLE'])
falt.to_csv(D/'faltantes_para_modelo_red.csv',index=False,encoding='utf-8-sig')

summary={'establecimientos_xalmimilulco':len(x),'alta':int((x.prioridad_ambiental=='alta').sum()),'media':int((x.prioridad_ambiental=='media').sum()),'humedo':int((x.proceso_hidrico=='humedo').sum()),'descargas_zona_operativa_2km':len(dx),'ptar_10km':len(px),'red_vial':False,'topografia':False}
(O/'resumen_diagnostico.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=False,indent=2))
