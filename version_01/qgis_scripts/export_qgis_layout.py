from pathlib import Path

from qgis.core import (
    QgsLayoutExporter,
    QgsLayoutItemLabel,
    QgsLayoutItemMap,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsPrintLayout,
    QgsProject,
    QgsUnitTypes,
)


project = QgsProject.instance()
project_root = Path(project.homePath() or Path.cwd())
out_dir = project_root / "outputs" / "maps"
out_dir.mkdir(parents=True, exist_ok=True)

layout = QgsPrintLayout(project)
layout.initializeDefaults()
layout.setName("Mapa preliminar Atoyac")
project.layoutManager().addLayout(layout)

map_item = QgsLayoutItemMap(layout)
map_item.attemptMove(QgsLayoutPoint(8, 18, QgsUnitTypes.LayoutMillimeters))
map_item.attemptResize(QgsLayoutSize(281, 170, QgsUnitTypes.LayoutMillimeters))
map_item.setExtent(project.layerTreeRoot().checkedLayers()[0].extent() if project.layerTreeRoot().checkedLayers() else project.fullExtent())
layout.addLayoutItem(map_item)

title = QgsLayoutItemLabel(layout)
title.setText("Actividad textil potencialmente relevante y red hidrografica")
title.attemptMove(QgsLayoutPoint(8, 6, QgsUnitTypes.LayoutMillimeters))
title.attemptResize(QgsLayoutSize(250, 10, QgsUnitTypes.LayoutMillimeters))
layout.addLayoutItem(title)

exporter = QgsLayoutExporter(layout)
pdf = out_dir / "qgis_mapa_preliminar.pdf"
png = out_dir / "qgis_mapa_preliminar.png"
exporter.exportToPdf(str(pdf), QgsLayoutExporter.PdfExportSettings())
exporter.exportToImage(str(png), QgsLayoutExporter.ImageExportSettings())
print(f"Layout exportado: {pdf} y {png}")

