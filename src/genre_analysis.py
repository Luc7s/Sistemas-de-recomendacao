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

    # Mostra os 20 maiores gêneros; a contagem completa fica no terminal.
    maiores = contagem.head(20)
    fig, ax = plt.subplots(figsize=(11, 9))
    maiores.plot(kind="barh", color="steelblue", ax=ax)
    ax.invert_yaxis()
    ax.bar_label(ax.containers[0], padding=4, fontsize=10)
    ax.set_xlim(0, maiores.max() * 1.15)
    ax.set_title("20 gêneros com mais músicas — dataset limpo", fontsize=15)
    ax.set_xlabel("Quantidade de músicas", fontsize=12)
    ax.set_ylabel("Gênero musical", fontsize=12)
    ax.tick_params(axis="y", labelsize=11)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    fig.text(0.5, 0.01, f"Exibindo {len(maiores)} de {len(contagem)} gêneros. Contagem completa no terminal.", ha="center", fontsize=10)
    plt.tight_layout(rect=(0, 0.04, 1, 1))
    plt.savefig(pasta / "musicas_por_genero.png", dpi=200)

    # Histograma: distribuição das quantidades por gênero.
    limite = (int(contagem.max()) // 100 + 1) * 100
    intervalos = list(range(0, limite + 1, 100))

    fig, ax = plt.subplots(figsize=(11, 7))
    frequencias, limites, barras = ax.hist(
        contagem.values, bins=intervalos, color="steelblue",
        edgecolor="black", label="Quantidade de gêneros em cada faixa",
    )
    centros = [(a + b) / 2 for a, b in zip(limites[:-1], limites[1:])]
    rotulos = [f"{int(a)}–{int(b) - 1}" for a, b in zip(limites[:-1], limites[1:])]
    ax.set_xticks(centros, rotulos, rotation=35, ha="right")
    ax.bar_label(barras, labels=[str(int(n)) for n in frequencias], padding=4)
    ax.set_ylim(0, max(frequencias) * 1.2)
    ax.set_title("Histograma: distribuição das músicas por gênero", fontsize=15)
    ax.set_xlabel("Faixa de quantidade de músicas por gênero", fontsize=12)
    ax.set_ylabel("Quantos gêneros estão nessa faixa", fontsize=12)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.2)
    ax.set_axisbelow(True)
    fig.text(0.5, 0.01, f"Cada gênero entra em uma faixa. Total: {len(contagem)} gêneros e {contagem.sum():,} músicas após a limpeza.".replace(",", "."), ha="center", fontsize=10)
    plt.tight_layout(rect=(0, 0.05, 1, 1))
    plt.savefig(pasta / "histograma_generos.png", dpi=200)

    print("\nGráficos salvos em outputs/musicas_por_genero.png e outputs/histograma_generos.png")
    plt.show()

    return contagem


if __name__ == "__main__":
    from data_loader import load_dataset
    from preprocessing import clean_data

    df_limpo = clean_data(load_dataset())
    analyze_genres(df_limpo)
