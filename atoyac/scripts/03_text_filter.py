import re
import unicodedata

import pandas as pd


SENALES_TEXTO = [
    "textil",
    "mezclilla",
    "humedo_explicito",
    "lavado_generico",
    "produccion",
    "maquila",
    "proceso_seco_explicito",
]

SENAL_NO_TEXTIL = "no_textil_explicito"


def normalizar_texto(valor):
    """
    Convierte texto a minúsculas, elimina acentos y normaliza espacios.
    """
    if pd.isna(valor):
        return ""

    texto = str(valor).lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )
    texto = re.sub(r"\s+", " ", texto)

    return texto


def construir_patron(terminos):
    """
    Construye un patrón que busca palabras o frases completas.
    """
    terminos = [
        normalizar_texto(termino)
        for termino in terminos
        if normalizar_texto(termino)
    ]

    # Primero se colocan las frases largas.
    terminos = sorted(set(terminos), key=len, reverse=True)

    if not terminos:
        return None

    alternativas = "|".join(
        re.escape(termino).replace(r"\ ", r"\s+")
        for termino in terminos
    )

    return rf"(?<![a-z0-9])(?:{alternativas})(?![a-z0-9])"


def filter_text_data(data, filtro_de_texto):
    """
    Agrega columnas booleanas de señales textuales y devuelve solamente
    los registros con al menos una coincidencia.
    """
    required_data_columns = [
        "nom_est",
        "desc_scian",
        "raz_soc",
    ]

    missing = [
        column
        for column in required_data_columns
        if column not in data.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas en los datos: {missing}"
        )

    required_filter_columns = ["palabra", "senal"]

    missing_filter = [
        column
        for column in required_filter_columns
        if column not in filtro_de_texto.columns
    ]

    if missing_filter:
        raise ValueError(
            "El diccionario debe contener las columnas "
            f"{required_filter_columns}"
        )

    resultado = data.copy()

    # Construir el texto que se analizará.
    resultado["texto_filtro"] = (
        resultado["nom_est"].fillna("").astype(str)
        + " "
        #+ resultado["desc_scian"].fillna("").astype(str)
        #+ " "
        + resultado["raz_soc"].fillna("").astype(str)
    ).map(normalizar_texto)

    # Crear una columna booleana para cada señal.
    for senal in SENALES_TEXTO:
        terminos = filtro_de_texto.loc[
            filtro_de_texto["senal"].eq(senal),
            "palabra",
        ]

        patron = construir_patron(terminos)

        if patron is None:
            resultado[senal] = False
        else:
            resultado[senal] = resultado[
                "texto_filtro"
            ].str.contains(
                patron,
                regex=True,
                na=False,
            )

    # Conservar también proceso_seco_explicito en el filtro.
    terminos_no_textiles = filtro_de_texto.loc[
        filtro_de_texto["senal"].eq(SENAL_NO_TEXTIL),
        "palabra",
    ]
    patron_no_textil = construir_patron(terminos_no_textiles)
    if patron_no_textil is None:
        resultado[SENAL_NO_TEXTIL] = False
    else:
        resultado[SENAL_NO_TEXTIL] = resultado["texto_filtro"].str.contains(
            patron_no_textil,
            regex=True,
            na=False,
        )

    tiene_alguna_senal = resultado[SENALES_TEXTO].any(axis=1)

    # La evidencia explicita de actividad no textil tiene prioridad.
    tiene_alguna_senal &= ~resultado[SENAL_NO_TEXTIL]

    return resultado.loc[tiene_alguna_senal].copy()
