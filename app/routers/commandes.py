from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.commande import CommandeCreate, CommandeRead
from app.services import commandes as service


router = APIRouter(prefix="/commandes", tags=["Commandes"])


@router.post("", response_model=CommandeRead, status_code=status.HTTP_201_CREATED)
def creer(
    data: CommandeCreate,
    db: Session = Depends(get_db),
    acteur: Utilisateur = Depends(require_roles("accueil")),
):
    commande = service.creer_commande(db, data, acteur)
    db.commit()
    return commande


@router.get("/{commande_id}", response_model=CommandeRead)
def detail(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.get_commande(db, commande_id)