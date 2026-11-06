
import json
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


def save_artifacts(
    models_dir,
    X,
    scaler,
    feature_matrix,
    df_clean,
    metadata
):
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)

    # 1. Salva a matriz numérica
    np.save(
        models_dir / "feature_matrix.npy",
        X
    )

    # 2. Salva o scaler treinado
    with open(models_dir / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    # 3. Salva os dados originais das músicas após limpeza
    df_clean.to_pickle(
        models_dir / "songs_lookup.pkl"
    )

    # 4. Salva a ordem das colunas
    feature_columns = list(feature_matrix.columns)

    with open(
        models_dir / "feature_columns.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            feature_columns,
            f,
            indent=4,
            ensure_ascii=False
        )

    # 5. Salva os metadados e configurações
    with open(
        models_dir / "model_metadata.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            metadata,
            f,
            indent=4,
            ensure_ascii=False
        )

    print(f"\nArtifacts saved in: {models_dir.resolve()}")


def load_artifacts(models_dir):
    models_dir = Path(models_dir)

    required_files = [
        "feature_matrix.npy",
        "scaler.pkl",
        "songs_lookup.pkl",
        "feature_columns.json",
        "model_metadata.json"
    ]

    missing_files = [
        file for file in required_files
        if not (models_dir / file).exists()
    ]

    if missing_files:
        raise FileNotFoundError(
            f"Model artifacts not found: {missing_files}. "
            "Run the training module first."
        )

    # 1. Carrega a matriz
    X = np.load(
        models_dir / "feature_matrix.npy",
        allow_pickle=False
    )

    # 2. Carrega o scaler
    with open(models_dir / "scaler.pkl", "rb") as f:
        scaler = pickle.load(f)

    # 3. Carrega os dados das músicas
    df_clean = pd.read_pickle(
        models_dir / "songs_lookup.pkl"
    )

    # 4. Carrega as colunas
    with open(
        models_dir / "feature_columns.json",
        encoding="utf-8"
    ) as f:
        feature_columns = json.load(f)

    # 5. Carrega os metadados
    with open(
        models_dir / "model_metadata.json",
        encoding="utf-8"
    ) as f:
        metadata = json.load(f)

    # Valida a compatibilidade dos arquivos
    if X.shape[0] != len(df_clean):
        raise ValueError(
            "The feature matrix and songs DataFrame "
            "have different numbers of rows."
        )

    if X.shape[1] != len(feature_columns):
        raise ValueError(
            "The feature matrix and feature columns "
            "have incompatible dimensions."
        )

    if X.shape[1] != metadata["feature_dim"]:
        raise ValueError(
            "The feature matrix does not match model metadata."
        )

    return {
        "X": X,
        "scaler": scaler,
        "feature_columns": feature_columns,
        "df_clean": df_clean,
        "metadata": metadata
    }
