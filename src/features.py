import pandas as pd


def one_hot_encode(df):
    return pd.get_dummies(
        df,
        columns=["track_genre"],
        prefix="genre",
        dtype=int,
    )
