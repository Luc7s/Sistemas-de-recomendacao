# Sistemas de recomendação

Pré-processamento do dataset de músicas do Spotify: carregamento, limpeza e one-hot encoding dos gêneros.

## Como executar

Com o Python instalado, abra o terminal na pasta principal do projeto. Todas as bibliotecas externas usadas pelo código estão listadas em `requirements.txt`, nas versões usadas para testar o projeto:

- `pandas`: leitura do CSV, limpeza, identificação de tipos e one-hot encoding.
- `matplotlib`: criação e salvamento dos gráficos.

Instale todas de uma vez:

```bash
python -m pip install -r requirements.txt
```

O pip também instala automaticamente as dependências dessas bibliotecas, como NumPy. O módulo `pathlib` já vem com o Python.

Se estiver no Windows e o comando `python` não funcionar, use:

```bash
py -m pip install -r requirements.txt
```

Depois execute o projeto:

```bash
python src/main.py
```

No Windows, também pode executar com `py src/main.py`. Este projeto usa Python e seu comando de instalação é o do pip.

O programa lê `data/dataset.csv`, aplica a limpeza de `src/preprocessing.py` e salva o resultado codificado em `data/encoded_dataset.csv`, sem adicionar uma coluna de índice ao CSV. O arquivo gerado é ignorado pelo Git e pode ser recriado executando o programa.

## Tipos das colunas

O `main.py` também mostra uma tabela com o nome de cada coluna do dataset original, sua classificação (Número ou Não numérico) e o tipo identificado pelo pandas.

Para ver apenas essa tabela:

```bash
python src/data_types.py
```

A função `identify_column_types(df)` retorna a tabela e pode ser usada com qualquer DataFrame, inclusive `df_codificado`, para conferir os tipos após o one-hot encoding. Ela identifica as colunas numéricas com `select_dtypes(include="number")`; não converte os valores. Textos e booleanos entram em Não numérico. Por exemplo, `explicit` e `track_genre` são não numéricos no dataset original e as colunas `genre_*` são números após a codificação.

## Contagem e gráficos de gêneros

Execute `python src/genre_analysis.py` na pasta principal para contar as músicas por gênero no dataset limpo. A contagem completa dos 113 gêneros aparece no terminal.

- `outputs/musicas_por_genero.png`: os 20 gêneros com mais músicas, em barras horizontais com nomes e quantidades.
- `outputs/histograma_generos.png`: todos os gêneros agrupados em faixas de 100 músicas, com a quantidade de gêneros escrita sobre cada barra.

As imagens são salvas antes de abrir as janelas dos gráficos e podem ser inseridas em slides. Ao executar `main.py`, feche as janelas para continuar para o one-hot encoding. A pasta `outputs` é ignorada pelo Git e pode ser recriada executando a análise.

## One-hot encoding

A função `one_hot_encode` de `src/features.py` usa `pd.get_dummies` para codificar os gêneros musicais.

A coluna `track_genre` é substituída por uma coluna para cada gênero presente no dataset limpo. Por exemplo, uma música de rock recebe `genre_rock = 1` e `0` nas colunas dos outros gêneros. Todas as categorias são mantidas, sem `drop_first`.

As outras colunas, a ordem das músicas e o índice são preservados. O dataset limpo original continua disponível em `df_limpo`. Esta etapa apenas codifica os gêneros; a seleção e a normalização das demais características para calcular similaridade ficam para as próximas etapas.
