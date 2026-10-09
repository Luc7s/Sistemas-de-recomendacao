# Sistemas de recomendação

Pré-processamento do dataset de músicas do Spotify: carregamento, limpeza e one-hot encoding dos gêneros.

## Como executar

Na pasta principal do projeto:

```bash
python -m pip install -r requirements.txt
python src/main.py
```

O programa lê `data/dataset.csv`, aplica a limpeza de `src/preprocessing.py` e salva o resultado codificado em `data/encoded_dataset.csv`, sem adicionar uma coluna de índice ao CSV. O arquivo gerado é ignorado pelo Git e pode ser recriado executando o programa.

## Tipos das colunas

O `main.py` também mostra uma tabela com o nome de cada coluna do dataset original, sua classificação (Número ou Não numérico) e o tipo identificado pelo pandas.

Para ver apenas essa tabela:

```bash
python src/data_types.py
```

A função `identify_column_types(df)` retorna a tabela e pode ser usada com qualquer DataFrame, inclusive `df_codificado`, para conferir os tipos após o one-hot encoding. Ela identifica as colunas numéricas com `select_dtypes(include="number")`; não converte os valores. Textos e booleanos entram em Não numérico. Por exemplo, `explicit` e `track_genre` são não numéricos no dataset original e as colunas `genre_*` são números após a codificação.

## One-hot encoding

A função `one_hot_encode` de `src/features.py` usa `pd.get_dummies` para codificar os gêneros musicais.

A coluna `track_genre` é substituída por uma coluna para cada gênero presente no dataset limpo. Por exemplo, uma música de rock recebe `genre_rock = 1` e `0` nas colunas dos outros gêneros. Todas as categorias são mantidas, sem `drop_first`.

As outras colunas, a ordem das músicas e o índice são preservados. O dataset limpo original continua disponível em `df_limpo`. Esta etapa apenas codifica os gêneros; a seleção e a normalização das demais características para calcular similaridade ficam para as próximas etapas.
