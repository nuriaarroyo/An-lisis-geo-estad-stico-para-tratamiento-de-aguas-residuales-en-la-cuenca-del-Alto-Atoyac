from importlib import import_module

import pandas as pd

filter_scian_data_textil = import_module(
    "scripts.02_scian"
).filter_scian_data_textil
filter_text_data = import_module(
    "scripts.03_text_filter"
).filter_text_data


SENALES_TEXTO = [
    "textil",
    "mezclilla",
    "humedo_explicito",
    "lavado_generico",
    "produccion",
    "maquila",
    "proceso_seco_explicito",
]


def decisiones_preliminares(
    data,
    filtro_de_texto,
    id_column="d_llave",
    scian_column="cve_scian",
    lavanderias_solo_con_senal=False,
):
    """
    Combina los subconjuntos producidos por el filtro SCIAN y el filtro
    textual, y agrega las decisiones sectorial e hídrica.
    """
    data = data.copy()

    if id_column not in data.columns:
        raise ValueError(
            f"Falta la columna identificadora '{id_column}'."
        )

    if scian_column not in data.columns:
        raise ValueError(
            f"Falta la columna SCIAN '{scian_column}'."
        )

    if data[id_column].duplicated().any():
        raise ValueError(
            f"La columna '{id_column}' contiene duplicados."
        )

    # 1. Ejecutar independientemente los dos filtros.
    data_scian = filter_scian_data_textil(
        data.copy(),
        scian_column=scian_column,
    )

    data_texto = filter_text_data(
        data.copy(),
        filtro_de_texto,
    )

    # 2. Obtener la unión de los candidatos.
    ids_scian = set(data_scian[id_column])
    ids_texto = set(data_texto[id_column])
    ids_candidatos = ids_scian | ids_texto

    # 3. Recuperar una sola fila original para cada establecimiento.
    resultado = data.loc[
        data[id_column].isin(ids_candidatos)
    ].copy()

    resultado["coincide_filtro_scian"] = (
        resultado[id_column].isin(ids_scian)
    )

    resultado["coincide_filtro_texto"] = (
        resultado[id_column].isin(ids_texto)
    )

    # 4. Traer únicamente las señales producidas por el filtro textual.
    senales_texto = data_texto[
        [id_column, *SENALES_TEXTO]
    ].copy()

    resultado = resultado.merge(
        senales_texto,
        on=id_column,
        how="left",
        validate="one_to_one",
    )

    # ``eq(True)`` convierte tambien los nulos del left join en False sin
    # depender del downcasting implicito de pandas.
    resultado[SENALES_TEXTO] = resultado[SENALES_TEXTO].eq(True)

    # 5. Interpretar el código SCIAN.
    codigo = (
        resultado[scian_column]
        .fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    resultado["scian_textil"] = (
        resultado["coincide_filtro_scian"]
        & codigo.str.startswith(("313", "314", "315"))
    )

    resultado["scian_acabado_humedo"] = (
        resultado["coincide_filtro_scian"]
        & codigo.eq("313310")
    )

    resultado["scian_lavanderia"] = (
        resultado["coincide_filtro_scian"]
        & codigo.eq("812210")
    )

    # 6. Construir condiciones intermedias.
    contexto_textil = (
        resultado["scian_textil"]
        | resultado["textil"]
        | resultado["mezclilla"]
    )

    contexto_productivo = (
        resultado["produccion"]
        | resultado["maquila"]
    )

    evidencia_humeda = (
        resultado["scian_acabado_humedo"]
        | (
            resultado["humedo_explicito"]
            & contexto_textil
        )
    )

    senal_adicional_lavanderia = (
        resultado["textil"]
        | resultado["mezclilla"]
        | resultado["humedo_explicito"]
        | resultado["produccion"]
        | resultado["maquila"]
    )
    lavanderia_admisible = resultado["scian_lavanderia"].copy()
    if lavanderias_solo_con_senal:
        lavanderia_admisible &= senal_adicional_lavanderia

    lavado_por_revisar = (
        lavanderia_admisible
        | (resultado["lavado_generico"] & contexto_textil)
    )

    # La mezclilla por si sola no demuestra un proceso humedo: puede
    # corresponder a venta, corte o costura. Se conserva para revision solo
    # cuando tambien hay una senal de lavado, produccion o maquila.
    mezclilla_relevante = (
        resultado["mezclilla"]
        & (
            resultado["lavado_generico"]
            | resultado["humedo_explicito"]
            | contexto_productivo
        )
    )

    # 7. Decisión sectorial.
    # Todos ya son candidatos de alguno de los dos filtros.
    resultado["sector_textil"] = "REVISAR"

    inclusion_textil = (
        resultado["scian_textil"]
        | (
            contexto_productivo
            & (
                resultado["textil"]
                | resultado["mezclilla"]
            )
        )
        | evidencia_humeda
    )

    resultado.loc[
        inclusion_textil,
        "sector_textil",
    ] = "INCLUIR"

    # 8. Evaluación hídrica.
    resultado["evidencia_hidrica"] = "SIN_EVIDENCIA"

    resultado.loc[
        lavado_por_revisar | mezclilla_relevante,
        "evidencia_hidrica",
    ] = "REVISAR"

    # La evidencia húmeda gana incluso si también aparece proceso seco.
    resultado.loc[
        evidencia_humeda,
        "evidencia_hidrica",
    ] = "SI"

    return resultado
