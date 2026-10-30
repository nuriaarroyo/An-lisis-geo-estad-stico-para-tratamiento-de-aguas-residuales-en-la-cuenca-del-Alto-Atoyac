"""Integra todas las descargas viales, incluida la descarga amplia en la raíz."""
from pathlib import Path
import importlib.util,hashlib,json
import geopandas as gpd
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/parte_3/12_vialidades_amplias'

def audit_full_network(roads):
    import networkx as nx
    from shapely import unary_union
    from shapely.strtree import STRtree
    pieces=list(unary_union(roads.geometry.to_numpy()).geoms)
    graph=nx.Graph()
    for line in pieces:
        coords=[tuple(c[:2]) for c in line.coords]
        graph.add_edges_from(zip(coords[:-1],coords[1:]))
    components=sorted(nx.connected_components(graph),key=len,reverse=True)
    mapping={n:i for i,c in enumerate(components) for n in c}
    tree=STRtree(pieces)
    focus=ROOT/'outputs/parte_3/09_foco_santa_ana_huejotzingo/foco_santa_ana_huejotzingo.gpkg'
    est=gpd.read_file(focus,layer='establecimientos_foco')
    plants=gpd.read_file(focus,layer='ptar_nucleo_local')
    records=[]
    for _,p in est[est.prioridad_ambiental.isin(['alta','media'])].iterrows():
        line=pieces[int(tree.nearest(p.geometry))]
        records.append({'punto_id':p.establecimiento_id,'zona':p.zona_analisis,'componente':mapping[tuple(line.coords[0][:2])]})
    for _,p in plants.iterrows():
        line=pieces[int(tree.nearest(p.geometry))]
        records.append({'punto_id':p.ptar_id,'zona':'ptar','componente':mapping[tuple(line.coords[0][:2])]})
    df=pd.DataFrame(records)
    df.to_csv(OUT/'comprobacion_red_completa.csv',index=False,encoding='utf-8-sig')
    result={'tramos_red_completa':len(roads),'nodos':len(graph),'componentes':len(components)}
    for zone in ['santa_ana','huejotzingo','ptar']:
        result['componentes_'+zone]=sorted(df[df.zona.eq(zone)].componente.unique().tolist())
    (OUT/'comprobacion_red_completa.json').write_text(json.dumps(result,indent=2),encoding='utf-8')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    frames=[];inventory=[];hashes=[]
    for path in sorted((ROOT/'data/raw/vialidades').rglob('*.shp')):
        label=path.parent.relative_to(ROOT/'data/raw/vialidades').as_posix()
        if label=='.':label='descarga_amplia'
        original=gpd.read_file(path);g=original.to_crs(32614)
        g['vialidad_id']=[f'{label}_{i:06d}' for i in range(len(g))]
        g['ruta_fuente']=str(path.relative_to(ROOT));g['archivo_origen']=label
        inventory.append({'entrega':label,'ruta':str(path.relative_to(ROOT)),'tramos':len(g),
            'crs_original':str(original.crs),'invalidas':int((~g.is_valid).sum()),'vacias':int(g.geometry.is_empty.sum())})
        frames.append(g)
        for f in path.parent.glob(path.stem+'.*'):
            hashes.append({'ruta':str(f.relative_to(ROOT)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    # Conservar primero las fuentes anteriores en coincidencias exactas.
    frames.sort(key=lambda g:g.archivo_origen.iloc[0]=='descarga_amplia')
    roads=gpd.GeoDataFrame(pd.concat(frames,ignore_index=True),crs=32614)
    roads=roads.loc[~roads.geometry.to_wkb().duplicated()].copy()
    regional=OUT/'vialidades_regionales_actualizadas.gpkg'
    roads.to_file(regional,layer='vialidades_regionales',driver='GPKG',index=False)
    pd.DataFrame(inventory).to_csv(OUT/'inventario_entregas.csv',index=False,encoding='utf-8-sig')
    manifest={'entradas_viales':hashes,'tramos_regionales_unicos':len(roads),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    (OUT/'manifest_fuentes.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    name='307_grafos_corredores_exploratorios'
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/f'{name}.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    module.OUT=OUT;module.ROADS=regional;module.main()
    audit_full_network(roads)
    print(pd.DataFrame(inventory).to_string(index=False))

if __name__=='__main__':main()
