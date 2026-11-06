from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.paiement import PaiementCreate, PaiementRead
from app.services import paiements as service


router_commandes = APIRouter(prefix="/commandes", tags=["Paiements"])
router_paiements = APIRouter(prefix="/paiements", tags=["Paiements"])


@router_commandes.post("/{commande_id}/paiements", response_model=PaiementRead, status_code=status.HTTP_201_CREATED)
def enregistrer(
    commande_id: int,
    data: PaiementCreate,
    db: Session = Depends(get_db),
    acteur: Utilisateur = Depends(require_roles("accueil")),
):
    paiement = service.enregistrer_paiement(db, commande_id, data, acteur)
    db.commit()
    return paiement


@router_commandes.get("/{commande_id}/paiements", response_model=list[PaiementRead])
def lister(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.lister_paiements(db, commande_id)


@router_paiements.delete("/{paiement_id}", status_code=status.HTTP_204_NO_CONTENT)
def annuler(
    paiement_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),
):
    service.annuler_paiement(db, paiement_id)
    db.commit()