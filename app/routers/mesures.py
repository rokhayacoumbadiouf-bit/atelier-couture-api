from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.mesure import MesureCreate, MesureRead, MesureUpdate
from app.services import mesures as service


router_clients = APIRouter(prefix="/clients", tags=["Mesures"])
router_mesures = APIRouter(prefix="/mesures", tags=["Mesures"])


@router_clients.post("/{client_id}/mesures", response_model=MesureRead, status_code=status.HTTP_201_CREATED)
def creer(
    client_id: int,
    data: MesureCreate,
    db: Session = Depends(get_db),
    tailleur: Utilisateur = Depends(require_roles("tailleur")),
):
    mesure = service.creer_mesures(db, client_id, data, tailleur)
    db.commit()
    return mesure


@router_clients.get("/{client_id}/mesures", response_model=list[MesureRead])
def historique(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.lister_mesures(db, client_id)


@router_clients.get("/{client_id}/mesures/derniere", response_model=MesureRead)
def dernieres(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.dernieres_mesures(db, client_id)


@router_mesures.get("/{mesure_id}", response_model=MesureRead)
def detail(
    mesure_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.get_mesure(db, mesure_id)


@router_mesures.patch("/{mesure_id}", response_model=MesureRead)
def modifier(
    mesure_id: int,
    data: MesureUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("tailleur")),
):
    mesure = service.modifier_mesures(db, mesure_id, data)
    db.commit()
    return mesure


@router_mesures.delete("/{mesure_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer(
    mesure_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("tailleur")),
):
    service.supprimer_mesures(db, mesure_id)
    db.commit()