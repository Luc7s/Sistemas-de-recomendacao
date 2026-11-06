from data_loader import load_dataset
from preprocessing import clean_data

df = clean_data(load_dataset())

matches = df[
    df["track_name"].str.contains(
        "god",
        case=False,
        na=False
    )
]

print(matches[["track_name", "artists"]].to_string(index=False))