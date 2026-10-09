from data_loader import load_dataset
from data_types import identify_column_types
from preprocessing import clean_data
from features import one_hot_encode


def main():
    df = load_dataset()
    print("Tipos das colunas do dataset original:")
    print(identify_column_types(df).to_string(index=False))

    df_limpo = clean_data(df)
    df_codificado = one_hot_encode(df_limpo)

    print(df_codificado.head())
    print(f"Dataset codificado: {df_codificado.shape[0]} músicas e {df_codificado.shape[1]} colunas")

    df_codificado.to_csv("data/encoded_dataset.csv", index=False)
    print("Dataset salvo em data/encoded_dataset.csv")


if __name__ == "__main__":
    main()
