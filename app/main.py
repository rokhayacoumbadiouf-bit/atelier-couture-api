from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.auth import router as auth_router
from app.routers.utilisateurs import router as utilisateurs_router
from app.routers.clients import router as clients_router
from app.routers.catalogue import router as catalogue_router
from app.routers.mesures import router_clients as mesures_clients_router
from app.routers.mesures import router_mesures as mesures_router
from app.routers.commandes import router as commandes_router
from app.routers.paiements import router_commandes as paiements_commandes_router
from app.routers.paiements import router_paiements as paiements_router
from app.routers.livraisons import router_commandes as livraisons_commandes_router
from app.routers.livraisons import router_livraisons as livraisons_router
from app.routers.statistiques import router as statistiques_router


app = FastAPI(
    title="API atelier de couture",
    description="Gestion des clients, mesures, commandes, paiements et livraisons.",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(utilisateurs_router, prefix="/api/v1")
app.include_router(clients_router, prefix="/api/v1")
app.include_router(catalogue_router, prefix="/api/v1")
app.include_router(mesures_clients_router, prefix="/api/v1")
app.include_router(mesures_router, prefix="/api/v1")
app.include_router(commandes_router, prefix="/api/v1")
app.include_router(paiements_commandes_router, prefix="/api/v1")
app.include_router(paiements_router, prefix="/api/v1")
app.include_router(livraisons_commandes_router, prefix="/api/v1")
app.include_router(livraisons_router, prefix="/api/v1")
app.include_router(statistiques_router, prefix="/api/v1")


@app.get("/health", tags=["Santé"])
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    db.execute(text("SELECT 1"))
    return {"status": "ok"}