from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from database import engine, Base
from routers import labs, vms, websocket


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Créer les tables de base de données au démarrage
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Virtual Lab Manager API",
    description="API pour la gestion et le déploiement de laboratoires virtuels",
    version="1.0.0",
    lifespan=lifespan
)

# Configuration CORS pour permettre les requêtes depuis le frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusion des routeurs
app.include_router(labs.router, prefix="/api/v1", tags=["labs"])
app.include_router(vms.router, prefix="/api/v1", tags=["vms"])
app.include_router(websocket.router, prefix="/api/v1", tags=["websocket"])


@app.get("/")
async def root():
    return {"message": "Virtual Lab Manager API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

