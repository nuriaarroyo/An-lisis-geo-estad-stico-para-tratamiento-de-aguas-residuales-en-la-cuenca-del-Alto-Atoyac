from pathlib import Path

from qgis.core import QgsProject, QgsVectorLayer


project_root = Path(QgsProject.instance().homePath() or Path.cwd())
processed_dir = project_root / "data" / "processed"

for gpkg in sorted(processed_dir.glob("*.gpkg")):
    layer = QgsVectorLayer(str(gpkg), gpkg.stem, "ogr")
    if layer.isValid():
        QgsProject.instance().addMapLayer(layer)
        print(f"Cargada: {gpkg.name}")
    else:
        print(f"No se pudo cargar: {gpkg.name}")

