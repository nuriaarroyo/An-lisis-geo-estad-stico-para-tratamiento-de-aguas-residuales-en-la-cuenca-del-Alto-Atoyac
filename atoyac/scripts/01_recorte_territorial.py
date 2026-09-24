import pandas as pd


def recorte_territorial(data, location_column="cve_loc", location_value=None):
    """
    Recorta el dataset para incluir solo los registros del estado especificado.

    Parámetros:
    - data: DataFrame de pandas que contiene el dataset.
    - state_column: Nombre de la columna que contiene los códigos de estado (por defecto 'cve_ent').
    - state_code: Código del estado a filtrar (por defecto '21' para Puebla).

    Retorna:
    - DataFrame filtrado que contiene solo los registros del estado especificado.
    """
    
    # Asegurarse de que la columna especificada exista en el dataset
    if location_column not in data.columns:
        raise ValueError(f"El dataset debe contener una columna '{location_column}'.")
    
    # Filtrar el dataset basado en el código del estado proporcionado
    if location_value is None:
        raise ValueError("Se debe proporcionar el valor de la localidad.")

    filtered_data = data[
        data[location_column].astype(str).str.strip()
        == str(location_value).strip()
    ].copy()
    
    return filtered_data


# Compatibilidad con el nombre usado inicialmente en el proyecto.
recorte_territotial = recorte_territorial
