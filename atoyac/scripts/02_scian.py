import pandas as pd


def filter_scian_data_textil(
    data,
    scian_column="cve_scian",
    scian_codes=("313", "314", "315", "812210"),
):
    """
    Devuelve registros que coinciden con los prefijos SCIAN pertinentes.
    """
    if scian_column not in data.columns:
        raise ValueError(
            f"El dataset debe contener la columna '{scian_column}'."
        )

    codigo = (
        data[scian_column]
        .fillna("")
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )

    mask = codigo.str.startswith(tuple(scian_codes))

    return data.loc[mask].copy()