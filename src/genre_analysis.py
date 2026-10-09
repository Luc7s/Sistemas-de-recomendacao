from pathlib import Path

import matplotlib.pyplot as plt


def analyze_genres(df):
    # Conta quantas músicas existem em cada gênero.
    contagem = df["track_genre"].value_counts()

    print("\nQuantidade de músicas por gênero:")
    print(contagem.to_string())
    print(f"\nTotal de gêneros: {len(contagem)}")
    print(f"Total de músicas: {contagem.sum()}")

    pasta = Path("outputs")
    pasta.mkdir(exist_ok=True)

    # Gráfico de barras: quantidade de músicas por gênero.
    plt.figure(figsize=(24, 8))
    contagem.plot(kind="bar", color="steelblue")
    plt.title("Quantidade de músicas por gênero — dataset limpo")
    plt.xlabel("Gênero musical")
    plt.ylabel("Quantidade de músicas")
    plt.xticks(rotation=90, fontsize=7)
    plt.tight_layout()
    plt.savefig(pasta / "musicas_por_genero.png", dpi=200)

    # Histograma: distribuição das quantidades por gênero.
    plt.figure(figsize=(10, 6))
    plt.hist(contagem.values, bins=20, color="steelblue", edgecolor="black")
    plt.title("Distribuição da quantidade de músicas por gênero — dataset limpo")
    plt.xlabel("Quantidade de músicas por gênero")
    plt.ylabel("Quantidade de gêneros")
    plt.tight_layout()
    plt.savefig(pasta / "histograma_generos.png", dpi=200)

    print("\nGráficos salvos em outputs/musicas_por_genero.png e outputs/histograma_generos.png")
    plt.show()

    return contagem


if __name__ == "__main__":
    from data_loader import load_dataset
    from preprocessing import clean_data

    df_limpo = clean_data(load_dataset())
    analyze_genres(df_limpo)
