# Sistema de Recomendação de Músicas

Projeto de um sistema de recomendação musical utilizando um dataset do Spotify. O objetivo é recomendar músicas semelhantes a partir de uma música informada pelo usuário, considerando características musicais e gêneros.

## Tecnologias utilizadas

- Python
- Pandas
- NumPy
- Matplotlib
- Scikit-learn

## Funcionalidades implementadas

### 1. Carregamento dos dados
- Leitura do dataset em formato CSV.
- Carregamento centralizado pelo módulo `data_loader.py`.

### 2. Tratamento dos dados
- Remoção de valores nulos.
- Remoção de músicas com `track_id` duplicado.
- Remoção de registros duplicados.
- Filtragem de durações inválidas ou superiores a 20 minutos.
- Remoção de músicas com BPM inválido.
- Reinicialização dos índices.

### 3. Análise dos gêneros
- Contagem de músicas por gênero.
- Identificação da quantidade de gêneros.
- Geração de gráficos para analisar a distribuição dos dados.

### 4. Engenharia de características (Feature Engineering)
Preparação das características musicais para o algoritmo de recomendação:

- Aplicação de `log1p` em variáveis assimétricas.
- Padronização de características numéricas com `StandardScaler`.
- Codificação dos gêneros com One-hot Encoding.
- Transformação da tonalidade musical (`key`) utilizando seno e cosseno.
- Aplicação de peso nas características de gênero.

### 5. Sistema de recomendação

Foram implementados dois métodos:

**Baseline — Similaridade do Cosseno**

Compara a música escolhida com as demais músicas do dataset e retorna as mais semelhantes.

**MMR — Maximal Marginal Relevance**

Busca equilibrar relevância e diversidade, evitando recomendações excessivamente repetitivas.

## Estrutura do projeto

```text
Sistemas-de-recomendacao/
│
├── data/
│   ├── dataset.csv
│   ├── feature_matrix.csv
│   ├── features.npy
│   ├── recommendations_baseline.csv
│   └── recommendations_mmr.csv
│
├── outputs/
│   ├── musicas_por_genero.png
│   └── histograma_generos.png
│
├── src/
│   ├── main.py
│   ├── data_loader.py
│   ├── data_types.py
│   ├── preprocessing.py
│   ├── features.py
│   ├── genre_analysis.py
│   └── recommender.py
│
├── requirements.txt
└── README.md
```

Os arquivos gerados durante a execução são recriados pelo programa e não precisam estar previamente disponíveis.

## Como executar o projeto

### 1. Clonar o repositório

```bash
git clone https://github.com/Luc7s/Sistemas-de-recomendacao.git
```

### 2. Entrar na pasta

```bash
cd Sistemas-de-recomendacao
```

### 3. Instalar as dependências

```bash
python -m pip install -r requirements.txt
```

No Windows, caso necessário:

```bash
py -m pip install -r requirements.txt
```

### 4. Adicionar o dataset

Coloque o arquivo `dataset.csv` dentro da pasta `data/`.

O caminho esperado é:

```text
data/dataset.csv
```

### 5. Executar o projeto

Na pasta principal, execute:

```bash
python src/main.py
```

Ou, no Windows:

```bash
py src/main.py
```

### 6. Pesquisar uma música

O programa solicitará:

```text
Digite o nome da música:
Digite o artista (opcional):
```

Depois, serão exibidas as recomendações geradas pelos dois métodos:

- Baseline
- MMR

Os resultados também são salvos em arquivos CSV na pasta `data/`.

## Próximas etapas

- Validar e comparar os resultados dos algoritmos.
- Avaliar a diversidade e a qualidade das recomendações.
- Desenvolver uma API utilizando FastAPI.
- Criar uma interface utilizando React.
- Integrar o sistema à API do Spotify, se necessário.

## Objetivo

Desenvolver um sistema de recomendação musical baseado em conteúdo (*Content-Based Filtering*), utilizando características das músicas para identificar similaridades e gerar recomendações.