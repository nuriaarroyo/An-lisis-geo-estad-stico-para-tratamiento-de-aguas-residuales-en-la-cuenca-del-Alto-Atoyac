"""Verificación de lectura e integridad; no recalcula ni modifica análisis."""
from pathlib import Path
import argparse,ast,csv,hashlib,json,re,sys
from urllib.parse import unquote,urlsplit
from importlib import metadata

ROOT=Path(__file__).resolve().parents[1]


def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def markdown_links(path):
    text=path.read_text(encoding='utf-8-sig')
    for match in re.finditer(r'(?<!!)\[[^\]]*\]\(([^)]+)\)|!\[[^\]]*\]\(([^)]+)\)',text):
        target=(match.group(1) or match.group(2)).strip().strip('<>')
        if not target or target.startswith('#') or urlsplit(target).scheme:continue
        raw=unquote(target.split('#',1)[0].split('?',1)[0])
        yield (path.parent/raw).resolve(),target


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--datos',action='store_true',help='Comprobar además las rutas base de los insumos locales.')
    args=parser.parse_args()
    problems=[];notes=[]
    registry=json.loads((ROOT/'proyecto.json').read_text(encoding='utf-8'))
    docs=[ROOT/'README.md',ROOT/'atoyac/README.md',ROOT/'version_01/README.md',ROOT/'atoyac/scripts/README.md',ROOT/'atoyac/data/README.md',ROOT/'atoyac/docs/parte_3/README.md',ROOT/'atoyac/outputs/parte_3/README.md']
    docs+=sorted((ROOT/'docs').glob('*.md'))
    docs+=list((ROOT/registry['entrega']).rglob('*.md'))
    links=0
    for path in docs:
        if not path.exists():problems.append(f'Falta documento: {path.relative_to(ROOT)}');continue
        for target,raw in markdown_links(path):
            links+=1
            if not target.exists():problems.append(f'Enlace roto en {path.relative_to(ROOT)}: {raw}')
    scripts=[]
    for directory in ['atoyac/scripts','version_01/scripts','herramientas']:
        scripts+=list((ROOT/directory).rglob('*.py'))
    for path in scripts:
        try:ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
        except (SyntaxError,UnicodeError) as exc:problems.append(f'Sintaxis: {path.relative_to(ROOT)}: {exc}')
    manifest_path=ROOT/registry['entrega']/'MANIFIESTO.json'
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
        for row in manifest['archivos']:
            path=manifest_path.parent/row['ruta']
            if not path.exists() or digest(path)!=row['sha256']:problems.append('Entrega no coincide con manifiesto: '+row['ruta'])
        for row in manifest['fuentes_y_transformaciones']:
            origin=ROOT/row['origen']
            if origin.exists() and digest(origin)!=row['sha256_origen']:problems.append('Cambió fuente de entrega; regenerar: '+row['origen'])
        for filename,expected in [('establecimientos.csv',408),('ptar_candidatas.csv',3),('caminos_minimos.csv',164)]:
            with (manifest_path.parent/'datos'/filename).open(encoding='utf-8-sig',newline='') as f:
                count=sum(1 for _ in csv.DictReader(f))
            if count!=expected:problems.append(f'{filename}: {count} filas; esperado {expected}')
    else:problems.append('Falta entrega: ejecutar python herramientas/preparar_entrega.py')
    current=ROOT/registry['parte3']
    if (current/'resumen.json').exists():
        result=json.loads((current/'resumen.json').read_text(encoding='utf-8'))
        with (current/'matriz_origen_destino.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
        connected=sum(row['conectado'].lower()=='true' for row in rows)
        if len(rows)!=result['pares_origen_destino'] or connected!=result['rutas_conectadas']:problems.append('Matriz de rutas no coincide con resumen.')
    else:notes.append('No están los resultados científicos completos; la entrega puede leerse de forma independiente.')
    for line in (ROOT/'requirements.txt').read_text(encoding='utf-8-sig').splitlines():
        if '==' not in line or line.startswith('#'):continue
        package,expected=line.split('==',1)
        try:
            actual=metadata.version(package)
            if actual!=expected:notes.append(f'Entorno: {package} {actual}, referencia {expected}.')
        except metadata.PackageNotFoundError:notes.append(f'Entorno: falta {package}; se necesita para reconstrucción.')
    if args.datos:
        required=['atoyac/data/raw/denue_scian_313-314-315-81/INEGI_DENUE_11092026.csv',
                  'atoyac/data/raw/cuenca_alto_atoyac/atoyac/capas_gpkg/caaresa_cuenca_alto_atoyac_21_reg_a.gpkg',
                  'atoyac/data/processed/lesly/Archivos_PTAR/PTAR_Final.csv',
                  'atoyac/data/raw/vialidades/INEGI_Vialidades_.shp']
        for relative in required:
            if not (ROOT/relative).exists():problems.append('Falta insumo base: '+relative)
        if len(list((ROOT/'atoyac/data/raw/terreno').rglob('*_mt.bil')))<2:problems.append('Se requieren las dos hojas MDT del análisis local.')
    print(f'Documentos: {len(docs)} | enlaces locales: {links} | scripts con sintaxis revisada: {len(scripts)}')
    for note in notes:print('NOTA:',note)
    if problems:
        for problem in problems:print('ERROR:',problem)
        return 1
    print('Correcto: documentación, enlaces, integridad y conteos de la entrega.')
    return 0

if __name__=='__main__':raise SystemExit(main())
