from qgis.core import QgsCategorizedSymbolRenderer, QgsProject, QgsRendererCategory, QgsSymbol
from qgis.PyQt.QtGui import QColor


colors = {
    "denue": QColor("#b2182b"),
    "hidrografia": QColor("#2b8cbe"),
    "vialidades": QColor("#636363"),
    "caminos": QColor("#8c6d31"),
    "agebs": QColor("#f2f2f2"),
    "manzanas": QColor("#d9d9d9"),
    "localidades": QColor("#525252"),
    "cuencas": QColor("#bdbdbd"),
}

category_colors = {
    "alta_relevancia_ambiental": QColor("#b2182b"),
    "media_relevancia_ambiental": QColor("#ef8a62"),
    "baja_relevancia_ambiental": QColor("#67a9cf"),
    "revisar": QColor("#7b3294"),
}

for layer in QgsProject.instance().mapLayers().values():
    name = layer.name().lower()
    if "denue_textil" in name and "categoria_relevancia_ambiental" in [f.name() for f in layer.fields()]:
        categories = []
        for value, color in category_colors.items():
            symbol = QgsSymbol.defaultSymbol(layer.geometryType())
            symbol.setColor(color)
            categories.append(QgsRendererCategory(value, symbol, value))
        layer.setRenderer(QgsCategorizedSymbolRenderer("categoria_relevancia_ambiental", categories))
    else:
        symbol = QgsSymbol.defaultSymbol(layer.geometryType())
        for key, color in colors.items():
            if key in name:
                symbol.setColor(color)
                break
        layer.renderer().setSymbol(symbol)
    layer.triggerRepaint()

print("Estilos basicos aplicados.")

