
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurRead, UtilisateurUpdate
from app.services import utilisateurs as service


router = APIRouter(prefix="/utilisateurs", tags=["Utilisateurs"])

# Sans rôle précisé, seul l'administrateur passe
admin_seulement = require_roles()


@router.post("", response_model=UtilisateurRead, status_code=status.HTTP_201_CREATED)
def creer(
    data: UtilisateurCreate,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
) -> Utilisateur:
    utilisateur = service.creer_utilisateur(db, data)
    db.commit()
    return utilisateur


@router.get("", response_model=list[UtilisateurRead])
def lister(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
) -> list[Utilisateur]:
    return service.lister_utilisateurs(db)


@router.get("/{utilisateur_id}", response_model=UtilisateurRead)
def detail(
    utilisateur_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
) -> Utilisateur:
    return service.get_utilisateur(db, utilisateur_id)


@router.patch("/{utilisateur_id}", response_model=UtilisateurRead)
def modifier(
    utilisateur_id: int,
    data: UtilisateurUpdate,
    db: Session = Depends(get_db),
    acteur: Utilisateur = Depends(admin_seulement),
) -> Utilisateur:
    utilisateur = service.modifier_utilisateur(db, utilisateur_id, data, acteur)
    db.commit()
    return utilisateur