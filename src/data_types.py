import pandas as pd


def identify_column_types(df):
    resultado = []
    colunas_numericas = df.select_dtypes(include="number").columns

    for coluna in df.columns:
        if coluna in colunas_numericas:
            classificacao = "Número"
        else:
            classificacao = "Não numérico"

        resultado.append({
            "coluna": coluna,
            "classificacao": classificacao,
            "tipo_pandas": str(df[coluna].dtype),
        })

    return pd.DataFrame(resultado)


if __name__ == "__main__":
    from data_loader import load_dataset

    df = load_dataset()
    print(identify_column_types(df).to_string(index=False))
