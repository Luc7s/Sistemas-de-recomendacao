import pandas as pd
from pandas.api.types import is_bool_dtype, is_numeric_dtype, is_string_dtype


def identify_column_types(df):
    resultado = []

    for coluna in df.columns:
        tipo = df[coluna].dtype

        if is_bool_dtype(tipo):
            classificacao = "Booleano (True/False)"
        elif is_numeric_dtype(tipo):
            classificacao = "Número"
        elif is_string_dtype(tipo):
            classificacao = "Texto"
        else:
            classificacao = "Outro"

        resultado.append({
            "coluna": coluna,
            "classificacao": classificacao,
            "tipo_pandas": str(tipo),
        })

    return pd.DataFrame(resultado, columns=["coluna", "classificacao", "tipo_pandas"])


if __name__ == "__main__":
    from data_loader import load_dataset

    df = load_dataset()
    print(identify_column_types(df).to_string(index=False))
