
import pandas as pd


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df_clean = df.copy()

    before = len(df_clean)

    df_clean = df_clean.dropna()

    df_clean = df_clean.drop_duplicates(
        subset="track_id",
        keep="first"
    )

    df_clean = df_clean.drop_duplicates()

    df_clean = df_clean[
        (df_clean["duration_ms"] > 0) &
        (df_clean["duration_ms"] < 20 * 60 * 1000)
    ]

    df_clean = df_clean[df_clean["tempo"] > 0]

    df_clean = df_clean.reset_index(drop=True)

    removed = before - len(df_clean)

    print(
        f"Cleaning: {before} -> {len(df_clean)} "
        f"rows ({removed} removed)"
    )

    assert df_clean["track_id"].is_unique
    assert df_clean.isnull().sum().sum() == 0

    return df_clean
