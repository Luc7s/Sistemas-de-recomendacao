from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import os

app = FastAPI(title="Spotify Recommender API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_PATH = "similarity.pkl"
DATA_PATH = "df.pkl"

if os.path.exists(MODEL_PATH) and os.path.exists(DATA_PATH):
    with open(MODEL_PATH, "rb") as f:
        similarity = pickle.load(f)
    with open(DATA_PATH, "rb") as f:
        df = pickle.load(f)
else:
    similarity = None
    df = None

class RecommendationRequest(BaseModel):
    song_name: str
    top_n: int = 5

@app.get("/")
def read_root():
    return {"status": "online"}

@app.post("/recommend")
def get_recommendations(payload: RecommendationRequest):
    if df is None or similarity is None:
        raise HTTPException(status_code=500, detail="Arquivos .pkl não encontrados.")
    
    song_query = payload.song_name.strip().lower()
    df['normalized_name'] = df['name'].str.lower()
    matches = df[df['normalized_name'] == song_query]
    
    if matches.empty:
        raise HTTPException(status_code=404, detail="Música não encontrada.")
    
    idx = matches.index[0]
    distances = similarity[idx]
    sorted_recommendations = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:payload.top_n+1]
    
    recommendations = []
    for i, score in sorted_recommendations:
        recommendations.append({
            "name": df.iloc[i]['name'],
            "artist": df.iloc[i]['artists'],
            "similarity_score": float(score)
        })
        
    return {"query_song": df.iloc[idx]['name'], "recommendations": recommendations}