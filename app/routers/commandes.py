from fastapi import APIRouter, Depends,Query, status
from sqlalchemy.orm import Session
from datetime import date

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.commande import CommandeCreate, CommandeRead,CommandeUpdate, LigneAjout
from app.schemas.pagination import Page

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


@router.get("", response_model=Page[CommandeRead])
def lister(
    statut: str | None = None,
    client_id: int | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    numero: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    items, total = service.lister_commandes(db, statut, client_id, date_min, date_max, numero, limit, offset)
    return Page[CommandeRead](
        items=[CommandeRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.patch("/{commande_id}", response_model=CommandeRead)
def modifier(
    commande_id: int,
    data: CommandeUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("accueil")),
):
    commande = service.modifier_commande(db, commande_id, data)
    db.commit()
    return commande


@router.post("/{commande_id}/lignes", response_model=CommandeRead, status_code=status.HTTP_201_CREATED)
def ajouter_ligne(
    commande_id: int,
    data: LigneAjout,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("accueil")),
):
    commande = service.ajouter_ligne(db, commande_id, data)
    db.commit()
    return commande


@router.delete("/{commande_id}/lignes/{ligne_id}", response_model=CommandeRead)
def retirer_ligne(
    commande_id: int,
    ligne_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("accueil")),
):
    commande = service.retirer_ligne(db, commande_id, ligne_id)
    db.commit()
    return commande