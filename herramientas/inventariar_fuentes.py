"""Inventario de fuentes locales sin modificar los datos originales."""
from pathlib import Path
import csv,hashlib,os
ROOT=Path(__file__).resolve().parents[1]

def accessible(p):
    return Path('\\\\?\\'+str(p.resolve())) if os.name=='nt' else p

def main():
    rows=[]
    for base in [ROOT/'atoyac/data/raw',ROOT/'atoyac/data/processed']:
        for path in sorted(base.rglob('*')):
            if not path.is_file() or any(x in path.parts for x in ['__MACOSX','__pycache__']):continue
            p=accessible(path);h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            rows.append({'ruta':path.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':h.hexdigest(),'tipo':path.suffix.lower().lstrip('.') or 'sin_extension','grupo':base.name})
    dest=ROOT/'atoyac/data/MANIFIESTO_FUENTES.csv'
    with dest.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['ruta','bytes','sha256','tipo','grupo']);writer.writeheader();writer.writerows(rows)
    print(f'{len(rows)} archivos inventariados; {sum(x["bytes"] for x in rows)/1e6:.1f} MB.')

if __name__=='__main__':main()
