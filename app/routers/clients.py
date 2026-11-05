from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.client import ClientCreate, ClientRead, ClientUpdate, Genre
from app.schemas.pagination import Page
from app.services import clients as service


router = APIRouter(prefix="/clients", tags=["Clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def creer(
    data: ClientCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    client = service.creer_client(db, data)
    db.commit()
    return client


@router.get("", response_model=Page[ClientRead])
def lister(
    q: str | None = None,
    genre: Genre | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    items, total = service.lister_clients(db, q, genre, limit, offset)
    return Page[ClientRead](
        items=[ClientRead.model_validate(c) for c in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{client_id}", response_model=ClientRead)
def detail(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.get_client(db, client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def modifier(
    client_id: int,
    data: ClientUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    client = service.modifier_client(db, client_id, data)
    db.commit()
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer(
    client_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),
):
    service.supprimer_client(db, client_id)
    db.commit()