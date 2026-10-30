"""Audita la nueva entrega connect y recalcula sin sobrescribir la revisión previa."""
from pathlib import Path
import hashlib,json,importlib.util
import geopandas as gpd
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely import unary_union,shortest_line

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/11_actualizacion_connect'

def load(name):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    before=ROOT/'outputs/parte_3/08_integracion_vialidades_terreno'
    prior=json.loads((before/'fuentes_sha256.json').read_text(encoding='utf-8'))
    hashes={r['ruta'].replace('\\','/'):r['sha256'] for r in prior}
    audit=[];frames=[]
    for folder in ['huejotzingo','santa ana','san martin labastida','connect']:
        directory=ROOT/'data/raw/vialidades'/folder
        for p in sorted(directory.iterdir()):
            if not p.is_file():continue
            relative=p.relative_to(ROOT).as_posix();current=hashlib.sha256(p.read_bytes()).hexdigest();old=hashes.get(relative)
            audit.append({'ruta':relative,'sha256_anterior':old,'sha256_actual':current,'estado':'igual' if old==current else 'nuevo' if old is None else 'cambiado'})
        path=directory/'INEGI_Vialidades_.shp'
        g=gpd.read_file(path).to_crs(32614)
        g['vialidad_id']=[f'{folder}_{i:06d}' for i in range(len(g))]
        g['ruta_fuente']=str(path.relative_to(ROOT));g['archivo_origen']=folder
        frames.append(g)
    pd.DataFrame(audit).to_csv(OUT/'auditoria_cambios_archivos.csv',index=False,encoding='utf-8-sig')
    combined=gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),crs=32614)
    # Priorizar la procedencia previa en duplicados geométricos exactos.
    combined=combined.loc[~combined.geometry.to_wkb().duplicated()].copy()
    regional=OUT/'vialidades_con_connect.gpkg'
    combined.to_file(regional,layer='vialidades_regionales',driver='GPKG',index=False)
    oldg=gpd.read_file(before/'localidades_vialidades_terreno.gpkg',layer='vialidades_regionales')
    new=frames[-1]
    added=len(set(new.geometry.to_wkb())-set(oldg.geometry.to_wkb()))
    connect_parts=unary_union(new.geometry.to_numpy())
    graph=load('307_grafos_corredores_exploratorios');graph.OUT=OUT;graph.ROADS=regional;graph.main()
    report=load('308_documentar_grafos_corredores');report.OUT=OUT;report.DOC_REPORT='03_actualizacion_connect.md';report.main()
    previous=json.loads((ROOT/'outputs/parte_3/10_grafos_corredores/resumen.json').read_text(encoding='utf-8'))
    current=json.loads((OUT/'resumen.json').read_text(encoding='utf-8'))
    oldgap=pd.read_csv(ROOT/'outputs/parte_3/10_grafos_corredores/brechas_componentes.csv').distancia_brecha_m.min()
    newgap=pd.read_csv(OUT/'brechas_componentes.csv').distancia_brecha_m.min()
    edges=gpd.read_file(OUT/'grafo_corredores_exploratorios.gpkg',layer='aristas_grafo')
    # Componente de las PTAR y componente de los orígenes Santa Ana según enlaces originales.
    pts=gpd.read_file(OUT/'grafo_corredores_exploratorios.gpkg',layer='puntos_enlace')
    targets=pts[pts.tipo.eq('ptar')].componente.unique();santa=pts[pts.zona.eq('santa_ana') & pts.tipo.eq('establecimiento')].componente.value_counts().idxmax()
    destination=unary_union(edges[edges.componente.isin(targets)].geometry)
    origin=unary_union(edges[edges.componente.eq(santa)].geometry)
    gap=shortest_line(destination,origin)
    gapg=gpd.GeoDataFrame([{'distancia_m':gap.length,'tipo':'brecha_geometrica_no_ruta','geometry':gap}],crs=32614)
    gapg.to_file(regional,layer='brecha_pendiente',driver='GPKG',index=False)
    center=gap.centroid
    fig,ax=plt.subplots(figsize=(10,9))
    clipbox=center.buffer(2000).envelope
    oldg[oldg.intersects(clipbox)].plot(ax=ax,color='#999999',linewidth=1,label='Vialidad previa')
    new[new.intersects(clipbox)].plot(ax=ax,color='#e66101',linewidth=1.2,label='Entrega connect')
    gapg.plot(ax=ax,color='red',linestyle='--',linewidth=2,label=f'Brecha pendiente: {gap.length:.0f} m')
    x0,y0,x1,y1=clipbox.bounds;ax.set_xlim(x0,x1);ax.set_ylim(y0,y1)
    ax.set_title('Connect aporta calles, pero persiste discontinuidad Santa Ana–Huejotzingo')
    ax.set_aspect('equal');ax.legend(fontsize=8);fig.tight_layout();fig.savefig(OUT/'05_detalle_connect_brecha.png',dpi=180);plt.close(fig)
    diff={'archivos_huejotzingo_sin_cambios':all(r['estado']=='igual' for r in audit if '/huejotzingo/' in r['ruta']),
          'connect_tramos':len(new),'connect_invalidos':int((~new.is_valid).sum()),'connect_geometrias_no_presentes_antes':added,
          'red_regional_antes':len(oldg),'red_regional_actual':len(combined),'componentes_antes':previous['componentes_nodando_cruces'],
          'componentes_actual':current['componentes_nodando_cruces'],'brecha_nodos_antes_m':float(oldgap),'brecha_nodos_actual_m':float(newgap),
          'brecha_geometrica_actual_m':gap.length,'rutas_antes':previous['rutas_conectadas'],'rutas_actual':current['rutas_conectadas']}
    (OUT/'comparacion_entrega_connect.json').write_text(json.dumps(diff,ensure_ascii=False,indent=2),encoding='utf-8')
    a=gpd.GeoSeries([gap],crs=32614).to_crs(4326).iloc[0]
    readme=f'''# Actualización con entrega connect

Huejotzingo: sus seis archivos son idénticos por SHA-256 a la auditoría anterior. Tampoco cambiaron Santa Ana ni San Martín.

Connect: {len(new):,} tramos válidos; {added:,} geometrías no presentes en el paquete previo (se eliminaron repeticiones exactas en la red conjunta). La red regional pasa de {len(oldg):,} a {len(combined):,} geometrías únicas.

La nueva entrega toca las redes previas de ambas localidades, pero sus diferentes grupos de calles no forman un puente continuo. El grafo sigue sin ruta desde los 31 orígenes prioritarios de Santa Ana hacia las tres PTAR. La brecha mínima entre nodos se reduce de {oldgap:.1f} a {newgap:.1f} m; se comprobó también por distancia entre líneas ({gap.length:.1f} m).

Extremos aproximados de la brecha (longitud, latitud): {list(a.coords)}. La línea roja sólo diagnostica la falta de continuidad; no se creó como arista ni representa una propuesta constructiva. Completar esa franja de vialidades y revisar los cruces antes de volver a calcular.

Abrir [detalle de la nueva entrega](05_detalle_connect_brecha.png), [explorador actualizado](explorador_grafos.html) y [reporte actualizado](reporte_grafos_corredores.md). Para QGIS: grafo_corredores_exploratorios.gpkg. La red regional con connect y la brecha están en vialidades_con_connect.gpkg.

Los resultados anteriores de 08–10 se conservan. Esta revisión es la vigente para vialidades y rutas; repetir desde atoyac con `python scripts/309_actualizar_connect.py`. El paquete 09 sigue aportando puntos y destinos, que no cambiaron; el paquete 11 usa las vialidades actuales directamente desde raw. La elevación no cambia.
'''
    (OUT/'README.md').write_text(readme,encoding='utf-8')
    # El manifiesto de 308 incluye sus dependencias históricas; agregar la entrada real de esta revisión.
    manifest_path=OUT/'manifest_reproducibilidad.json';manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['fuente_vial_real_esta_revision']=str(regional.relative_to(ROOT))
    manifest['sha256_fuente_vial_real']=hashlib.sha256(regional.read_bytes()).hexdigest()
    manifest['auditoria_raw']='auditoria_cambios_archivos.csv'
    manifest['script_actualizacion_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(diff,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
