from data_loader import load_dataset
from preprocessing import clean_data


def main():
    df = load_dataset()
    df_limpo = clean_data(df)

    print(df_limpo.head())
    # Use df_limpo nas próximas etapas do sistema.


if __name__ == "__main__":
    main()