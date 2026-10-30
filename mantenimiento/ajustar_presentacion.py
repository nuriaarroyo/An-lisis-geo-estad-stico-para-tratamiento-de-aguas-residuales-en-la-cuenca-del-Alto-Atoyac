from pathlib import Path
p=Path('herramientas/documentar_repo.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("'docs/REPRODUCIR.md':'''", "'docs/REPRODUCIR.md':r'''")
s=s.replace('## Organización\n\n```text', '## Vista del trabajo\n\n| Concentraciones regionales | Integración local de terreno y establecimientos |\n|---|---|\n| ![Clusters regionales](entrega/figuras/00_clusters_regionales.png) | ![Terreno de Huejotzingo](entrega/figuras/05_huejotzingo_elevacion.png) |\n\n## Organización\n\n```text',1)
p.write_text(s,encoding='utf-8')
p=Path('herramientas/preparar_entrega.py');s=p.read_text(encoding='utf-8-sig')
s=s.replace("    images=['05_santa", "    copy(Path('atoyac/outputs/parte_2/13_figuras_finales/02_clusters_principales.png'),Path('figuras/00_clusters_regionales.png'))\n    images=['05_santa")
s=s.replace('## Mapas\n\n| Localidad', '## Mapas\n\n[Mapa regional de concentraciones](figuras/00_clusters_regionales.png). Los mapas siguientes desarrollan el foco local de parte 3.\n\n| Localidad')
p.write_text(s,encoding='utf-8')
