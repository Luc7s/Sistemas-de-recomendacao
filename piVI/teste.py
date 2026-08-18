import pandas as pd

df = pd.read_csv("/app/data/raw/spotify.csv")

print(df.shape)
print(df.head())