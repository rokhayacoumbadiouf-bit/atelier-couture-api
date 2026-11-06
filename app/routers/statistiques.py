from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.pagination import Page
from app.schemas.statistiques import ImpayeRead, PointPeriode, TableauDeBord, TopClient, VentesTypeVetement
from app.services import statistiques as service


router = APIRouter(prefix="/statistiques", tags=["Statistiques"])
admin_seulement = require_roles()


def _debut_par_defaut() -> date:
    return date.today().replace(day=1)


@router.get("/tableau-de-bord", response_model=TableauDeBord)
def tableau_de_bord(
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
):
    return service.tableau_de_bord(db)


@router.get("/chiffreaffaires", response_model=list[PointPeriode])
def chiffre_affaires(
    granularite: str = Query(default="jour"),
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
):
    return service.chiffre_affaires(
        db,
        granularite,
        date_debut or _debut_par_defaut(),
        date_fin or date.today(),
    )


@router.get("/typesvetement", response_model=list[VentesTypeVetement])
def types_vetement(
    date_debut: date | None = None,
    date_fin: date | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
):
    return service.ventes_par_type(db, date_debut or _debut_par_defaut(), date_fin or date.today())


@router.get("/top-clients", response_model=list[TopClient])
def top_clients(
    date_debut: date | None = None,
    date_fin: date | None = None,
    limite: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
):
    return service.top_clients(db, date_debut or _debut_par_defaut(), date_fin or date.today(), limite)


@router.get("/impayes", response_model=Page[ImpayeRead])
def impayes(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(admin_seulement),
):
    items, total = service.impayes(db, limit, offset)
    return Page[ImpayeRead](items=items, total=total, limit=limit, offset=offset)