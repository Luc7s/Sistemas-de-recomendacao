
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.state import state
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Carregando modelo...")
    state.load()
    print("API pronta!")

    yield


app = FastAPI(
    title="Spotify Music Recommendation API",
    description=(
        "API de recomendação musical utilizando "
        "similaridade do cosseno e MMR."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "Spotify Recommendation API",
        "status": "online",
        "documentation": "/docs",
    }


app.include_router(router, prefix="/api")
