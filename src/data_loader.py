"""
Loads the raw Spotify tracks dataset from disk.
"""
import pandas as pd


def load_dataset(path: str = "data/dataset.csv") -> pd.DataFrame:
    """Load the raw dataset, keeping track_id as a column."""
    df = pd.read_csv(path)
    return df
