from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Commande, Mesure, Utilisateur
from app.schemas.mesure import CHAMPS_MESURES, MesureCreate, MesureUpdate
from app.services.clients import get_client


def _verifier_au_moins_une_mesure(mesure: Mesure) -> None:
    """RG2 : une prise doit contenir au moins une mesure."""
    if all(getattr(mesure, champ) is None for champ in CHAMPS_MESURES):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Une prise de mesures doit contenir au moins une mesure",
        )


def mesure_utilisee(db: Session, mesure_id: int) -> bool:
    """RG4 : une mesure utilisée par une commande ne peut pas être supprimée."""
    return db.scalar(select(Commande.id).where(Commande.mesure_id == mesure_id).limit(1)) is not None

def get_mesure(db: Session, mesure_id: int) -> Mesure:
    mesure = db.get(Mesure, mesure_id)
    if mesure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prise de mesures introuvable")
    return mesure


def creer_mesures(db: Session, client_id: int, data: MesureCreate, tailleur: Utilisateur) -> Mesure:
    get_client(db, client_id)
    valeurs = data.model_dump()
    date_prise = valeurs.pop("date_prise") or date.today()

    mesure = Mesure(client_id=client_id, prise_par_id=tailleur.id, date_prise=date_prise, **valeurs)
    _verifier_au_moins_une_mesure(mesure)

    db.add(mesure)
    db.flush()
    return mesure


def lister_mesures(db: Session, client_id: int) -> list[Mesure]:
    """RG3 : historique complet, la prise la plus récente en premier."""
    get_client(db, client_id)
    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
    )
    return list(db.scalars(requete).all())


def dernieres_mesures(db: Session, client_id: int) -> Mesure:
    """RG3 : les dernières mesures sont la prise de date la plus récente."""
    get_client(db, client_id)
    requete = (
        select(Mesure)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        .limit(1)
    )
    mesure = db.scalar(requete)
    if mesure is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ce client n'a encore aucune mesure")
    return mesure


def modifier_mesures(db: Session, mesure_id: int, data: MesureUpdate) -> Mesure:
    mesure = get_mesure(db, mesure_id)
    modifications = data.model_dump(exclude_unset=True)

    if "date_prise" in modifications and modifications["date_prise"] is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="La date de prise ne peut pas être vidée")
    for champ, valeur in modifications.items():
        setattr(mesure, champ, valeur)

    # Si la correction supprime toutes les mesures, l'exception annule la transaction
    _verifier_au_moins_une_mesure(mesure)
    db.flush()
    return mesure


def supprimer_mesures(db: Session, mesure_id: int) -> None:
    mesure = get_mesure(db, mesure_id)
    if mesure_utilisee(db, mesure_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cette prise de mesures est utilisée par une commande et ne peut pas être supprimée",
        )
    db.delete(mesure)
    db.flush()