from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.type_vetement import TypeVetementCreate, TypeVetementRead, TypeVetementUpdate
from app.services import catalogue as service


router = APIRouter(prefix="/catalogue", tags=["Catalogue"])


@router.post("", response_model=TypeVetementRead, status_code=status.HTTP_201_CREATED)
def creer(
    data: TypeVetementCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),
):
    prestation = service.creer_prestation(db, data)
    db.commit()
    return prestation


@router.get("", response_model=list[TypeVetementRead])
def lister(
    actifs_seulement: bool = Query(default=True),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.lister_prestations(db, actifs_seulement)


@router.get("/{prestation_id}", response_model=TypeVetementRead)
def detail(
    prestation_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.get_prestation(db, prestation_id)


@router.patch("/{prestation_id}", response_model=TypeVetementRead)
def modifier(
    prestation_id: int,
    data: TypeVetementUpdate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles()),
):
    prestation = service.modifier_prestation(db, prestation_id, data)
    db.commit()
    return prestation