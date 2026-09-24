"""Segunda pasada auditable de Parte 2; no modifica la solucion espacial fija."""
from importlib import import_module
import json, re
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import cdist, jensenshannon, squareform
from sklearn.cluster import HDBSCAN
from sklearn.metrics import adjusted_rand_score
from sklearn.metrics.pairwise import cosine_distances

comun = import_module("200_parte2_comun")
perfil = import_module("207_perfilar_clusters")
OUT = comun.OUT / "14_segunda_pasada"

def modo(s):
    x=s.fillna("Sin dato").astype(str).value_counts(); return x.index[0] if len(x) else "Sin dato"

def ari_variantes(a,b,base,mega=20):
    a=np.asarray(a); b=np.asarray(b); base=np.asarray(base)
    ambos=(a>=0)&(b>=0); sinmega=base!=mega
    return {
      "ari_global_con_ruido":adjusted_rand_score(a,b),
      "ari_excluyendo_ruido_ambas_particiones":adjusted_rand_score(a[ambos],b[ambos]) if ambos.sum()>1 else np.nan,
      "n_excluyendo_ruido":int(ambos.sum()),
      "ari_sin_mega_cluster_principal":adjusted_rand_score(a[sinmega],b[sinmega]),
      "n_sin_mega":int(sinmega.sum())}

def main():
    comun.asegurar_directorios(); OUT.mkdir(parents=True,exist_ok=True)
    sel=pd.read_csv(comun.OUT/"05_seleccion/seleccion_escenarios.csv")
    mem=comun.leer_membresias(); pts=comun.leer_puntos_metricos().sort_values("d_llave").reset_index(drop=True)
    ids=pts.d_llave.astype(str).to_numpy(); xy=np.c_[pts.geometry.x,pts.geometry.y]
    principal=sel.loc[sel.rol.eq("PRINCIPAL"),"escenario_id"].iloc[0]
    labels={e:g.set_index("d_llave").reindex(ids).cluster.to_numpy(int) for e,g in mem.groupby("escenario_id")}
    base=labels[principal]
    # Las cinco particiones de mayor ARI del mismo metodo (no vecindad parametrica).
    metodo=sel.set_index("escenario_id").loc[principal,"metodo"]
    candidatos=[]
    for e in sel.loc[(sel.metodo.eq(metodo))&(~sel.escenario_id.eq(principal)),"escenario_id"]:
        candidatos.append((e,adjusted_rand_score(base,labels[e])))
    top5=sorted(candidatos,key=lambda z:z[1],reverse=True)[:5]
    filas=[]
    for orden,(e,_) in enumerate(top5,1):
        filas.append({"tipo_comparacion":"cinco_particiones_mas_similares_mismo_metodo","orden":orden,"escenario_comparado":e,**ari_variantes(base,labels[e],base)})
    # Reproduce exactamente las tres perturbaciones gaussianas N(0,25m) por eje y SeedSequence historica.
    row=sel[sel.escenario_id.eq(principal)].iloc[0]
    for rep,seed in enumerate(np.random.SeedSequence(comun.SEMILLA).spawn(3),1):
        rng=np.random.default_rng(seed); pert=xy+rng.normal(0,25,size=xy.shape)
        model=HDBSCAN(min_cluster_size=int(row.min_cluster_size),min_samples=int(row.min_samples),cluster_selection_method=str(row.cluster_selection_method),metric="euclidean",n_jobs=-1)
        lab=model.fit_predict(pert)
        filas.append({"tipo_comparacion":"perturbacion_gaussiana_25m","orden":rep,"escenario_comparado":f"repeticion_{rep}",**ari_variantes(base,lab,base)})
    aris=pd.DataFrame(filas); comun.guardar_csv(aris,OUT/"diagnostico_ari_variantes.csv")
    resumen=aris.groupby("tipo_comparacion").agg(n_comparaciones=("orden","size"),ari_global_media=("ari_global_con_ruido","mean"),ari_global_min=("ari_global_con_ruido","min"),ari_sin_ruido_media=("ari_excluyendo_ruido_ambas_particiones","mean"),ari_sin_ruido_min=("ari_excluyendo_ruido_ambas_particiones","min"),ari_sin_mega_media=("ari_sin_mega_cluster_principal","mean"),ari_sin_mega_min=("ari_sin_mega_cluster_principal","min")).reset_index()
    comun.guardar_csv(resumen,OUT/"resumen_ari_variantes.csv")
    # Componentes cluster-level: Jaccard de cada una de las cinco comparaciones usadas en membresia.
    jac=pd.read_csv(comun.OUT/"05_seleccion/jaccard_clusters_seleccionados.csv")
    est=pd.read_csv(comun.OUT/"05_seleccion/persistencia_establecimientos.csv",dtype={"d_llave":str})
    est=est.rename(columns={"persistencia_territorial":"estabilidad_membresia_entre_especificaciones","clase_persistencia":"clase_estabilidad_membresia"})
    comun.guardar_csv(est,OUT/"estabilidad_membresia_establecimientos.csv")
    comp=jac.pivot(index="cluster_principal",columns="escenario_comparado",values="jaccard").reset_index()
    agg=est[est.cluster_principal.ge(0)].groupby("cluster_principal").agg(n=("d_llave","size"),estabilidad_media=("estabilidad_membresia_entre_especificaciones","mean"),estabilidad_min=("estabilidad_membresia_entre_especificaciones","min"),pct_nucleo_robusto=("clase_estabilidad_membresia",lambda s:100*s.eq("NUCLEO_ROBUSTO").mean()),pct_estable=("clase_estabilidad_membresia",lambda s:100*s.eq("ESTABLE").mean()),pct_sensible=("clase_estabilidad_membresia",lambda s:100*s.eq("SENSIBLE").mean())).reset_index()
    jstat=jac.groupby("cluster_principal").jaccard.agg(jaccard_media="mean",jaccard_min="min",jaccard_max="max").reset_index()
    comun.guardar_csv(agg.merge(jstat,on="cluster_principal").merge(comp,on="cluster_principal"),OUT/"componentes_estabilidad_por_cluster.csv")
    # Tres espacios metricos y explicacion de pares.
    datos=pd.read_csv(comun.OUT/"07_perfiles/establecimientos_perfilados_cuenca.csv",low_memory=False); datos=datos[datos.cluster.ge(0)].copy()
    for c in perfil.SENALES: datos[c]=comun.booleano(datos[c]).astype(float)
    grupos=sorted(datos.grupo_espacial.unique()); sig=datos.groupby("grupo_espacial")[perfil.SENALES].mean().reindex(grupos).fillna(0)
    sc=pd.crosstab(datos.grupo_espacial,datos.scian_3,normalize="index").reindex(grupos).fillna(0)
    dc=cosine_distances(sig); dj=np.zeros_like(dc)
    for i in range(len(grupos)):
      for j in range(i+1,len(grupos)): dj[i,j]=dj[j,i]=jensenshannon(sc.iloc[i]+1e-12,sc.iloc[j]+1e-12,base=2)
    comb=.5*dc+.5*dj
    for name,m in [("distancia_coseno_senales",dc),("distancia_jensen_shannon_scian3",dj),("distancia_combinada_50_50",comb)]:
        z=pd.DataFrame(m,index=grupos,columns=grupos); z.index.name="grupo_espacial"; comun.guardar_csv(z.reset_index(),OUT/f"{name}.csv")
    pairs=[]
    for i in range(len(grupos)):
      for j in range(i+1,len(grupos)):
        shared=(np.minimum(sig.iloc[i],sig.iloc[j])).sort_values(ascending=False).head(5)
        diff=(sig.iloc[i]-sig.iloc[j]).abs().sort_values(ascending=False).head(3)
        shared_sc=np.minimum(sc.iloc[i],sc.iloc[j]).sort_values(ascending=False).head(3)
        pairs.append({"cluster_a":grupos[i],"cluster_b":grupos[j],"distancia_coseno":dc[i,j],"distancia_js":dj[i,j],"distancia_combinada":comb[i,j],"senales_compartidas":" | ".join(f"{k}:{100*v:.1f}%" for k,v in shared.items() if v>0),"scian3_compartidos":" | ".join(f"{k}:{100*v:.1f}%" for k,v in shared_sc.items() if v>0),"diferencias_principales":" | ".join(f"{k}:{100*v:.1f}pp" for k,v in diff.items())})
    comun.guardar_csv(pd.DataFrame(pairs).sort_values("distancia_combinada"),OUT/"explicacion_pares_similares.csv")
    # Tabla completa de sobre-representacion con estados explicitos.
    sob=pd.read_csv(comun.OUT/"08_sobrerrepresentacion/sobrerrepresentacion_senales.csv")
    sob["estado_celda"]=np.select([sob.prevalencia_universo.eq(0),sob.evidencia_descriptiva_suficiente,sob.lift.le(1)],["NO_EVALUABLE","SOBRERREPRESENTADO","NO_SOBRERREPRESENTADO"],default="FILTRADO_POR_CRITERIO")
    sob["IC95"]=sob.or_ic95_inf.map(lambda x:f"[{x:.3g}")+", "+sob.or_ic95_sup.map(lambda x:f"{x:.3g}]")
    full=sob.rename(columns={"grupo_espacial":"cluster","senal":"rasgo","n_grupo":"n","conteo_senal":"conteo","prevalencia_grupo":"prevalencia_cluster","prevalencia_universo":"prevalencia_global","diferencia_prevalencia":"diferencia_pp","odds_ratio_fisher":"odds_ratio","p_ajustada_bh":"p_BH"})
    full["diferencia_pp"]*=100
    comun.guardar_csv(full[["cluster","rasgo","n","conteo","prevalencia_cluster","prevalencia_global","diferencia_pp","lift","log2_lift","odds_ratio","IC95","p_fisher","p_BH","estado_celda"]],OUT/"sobrerrepresentacion_completa.csv")
    top=full[full.estado_celda.eq("SOBRERREPRESENTADO")].sort_values(["cluster","log2_lift"],ascending=[True,False]).groupby("cluster").head(5)
    comun.guardar_csv(top,OUT/"top_rasgos_por_cluster.csv")
    # Diccionario analitico (reglas canonicas + trazabilidad a columnas).
    maes=comun.cargar_maestra(); inside=maes[maes.dentro_cuenca.astype(bool)].copy()
    mainvars={"actividad_lavanderia_tintoreria","actividad_confeccion","actividad_fabricacion_telas","actividad_acabado_textil","maquila","mezclilla","humedo_explicito","proceso_seco_explicito"}
    rows=[]
    for v in perfil.SENALES:
        vals=comun.booleano(inside[v]); origin="etiqueta canonica derivada de giro/diccionario" if not v.startswith("scian_") else "regla agregada a partir de codigo SCIAN"
        rows.append({"etiqueta_canonica":v,"grupo":"SCIAN" if v.startswith("scian_") else "senal_multilabel","diccionario_origen":origin,"terminos_que_activan":"Consultar scripts/03_text_filter.py y 201_construir_matriz_maestra.py; regla versionada en codigo","conteo_global":int(vals.sum()),"prevalencia_global":float(vals.mean()),"heatmap_principal":v in mainvars,"razon":"lectura sustantiva compacta central" if v in mainvars else "reservada para heatmap ampliado para evitar redundancia visual"})
    comun.guardar_csv(pd.DataFrame(rows),OUT/"diccionario_variables_analiticas.csv")
    # Diagnostico completo de los 18 subnucleos, con perfilado posterior.
    mega=gpd.read_file(comun.OUT/"11_cierre/diagnostico_mega_cluster.gpkg",layer="establecimientos_subnucleos")
    datos["d_llave"]=datos.d_llave.astype(str); prof=datos.set_index("d_llave"); mega["d_llave"]=mega.d_llave.astype(str); mega=mega.join(prof[[*perfil.SENALES,"scian_3"]],on="d_llave",rsuffix="_perfil")
    cores=mega[mega.subnucleo_diagnostico.ge(0)].copy(); cent={}
    for cid,g in cores.groupby("subnucleo_diagnostico"): cent[int(cid)]=np.array([g.geometry.x.mean(),g.geometry.y.mean()])
    subrows=[]
    for cid,g in cores.groupby("subnucleo_diagnostico"):
        a=np.c_[g.geometry.x,g.geometry.y]; medidx=np.argmin(cdist(a,a).sum(axis=1)); med=g.iloc[medidx]
        hull=g.geometry.union_all().convex_hull; area=hull.area/1e6; diag=float(np.hypot(g.geometry.x.max()-g.geometry.x.min(),g.geometry.y.max()-g.geometry.y.min())/1000)
        near=min((np.linalg.norm(cent[int(cid)]-p),k) for k,p in cent.items() if k!=int(cid))
        rr={"subnucleo_id":int(cid),"n":len(g),"pct_mega_cluster":100*len(g)/len(mega),"municipio_dominante":modo(g.Municipio),"localidad_dominante":modo(g.localidad),"centroide_x":cent[int(cid)][0],"centroide_y":cent[int(cid)][1],"medoid_d_llave":med.d_llave,"medoid_x":med.geometry.x,"medoid_y":med.geometry.y,"area_convexa_km2":area,"extension_bbox_km":diag,"densidad_por_km2":len(g)/area if area>0 else np.nan,"n_localidades":g.localidad.nunique(),"subnucleo_mas_proximo":near[1],"distancia_mas_proximo_m":near[0],"scian3_principales":" | ".join(map(str,g.scian_3.value_counts().head(3).index))}
        for v in ["scian_textil","actividad_lavanderia_tintoreria","actividad_confeccion","actividad_acabado_textil","actividad_fabricacion_telas","maquila","senal_mezclilla_o_pantalon","humedo_explicito","proceso_seco_explicito"]: rr[f"pct__{v}"]=100*comun.booleano(g[v]).mean()
        subrows.append(rr)
    comun.guardar_csv(pd.DataFrame(subrows),OUT/"subnucleos_mega_cluster_documentados.csv")
    meta={"solucion_principal_inmutable":principal,"semilla":comun.SEMILLA,"perturbacion":"ruido gaussiano independiente N(0,25 m) en x e y; 3 repeticiones; se reajusta HDBSCAN completo","aclaracion_top5":"media de las cinco particiones del mismo metodo con mayor ARI; no son vecinas parametricas","estabilidad_membresia":"fraccion no ponderada de 5 especificaciones alternativas en que cada punto permanece en el cluster emparejado por maximo Jaccard; peso 0.2 cada una","umbrales":"SENSIBLE 0-0.49; ESTABLE 0.50-0.79; NUCLEO_ROBUSTO 0.80-1.00","mega":"HDBSCAN espacial mcs=30, min_samples=10, leaf; exploratorio, no redefine membresia principal"}
    comun.guardar_json(meta,OUT/"metadatos_metodologicos.json")
    print(resumen.to_string(index=False)); print(f"Subnucleos documentados: {len(subrows)}")
if __name__=="__main__": main()
