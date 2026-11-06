from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Commande, Paiement, Utilisateur
from app.schemas.paiement import PaiementCreate
from app.services.commandes import get_commande


def recalculer_paye(db: Session, commande: Commande) -> None:
    """RG17 : le montant payé est toujours la somme des paiements enregistrés."""
    total_paye = db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(Paiement.commande_id == commande.id)
    )
    commande.montant_paye = int(total_paye)
    db.flush()


def enregistrer_paiement(db: Session, commande_id: int, data: PaiementCreate, acteur: Utilisateur) -> Paiement:
    commande = get_commande(db, commande_id)

    # RG16 : impossible sur une commande annulée
    if commande.statut == "annulee":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Aucun paiement ne peut être enregistré sur une commande annulée",
        )

    # RG16 : pas de date future
    date_paiement = data.date_paiement or date.today()
    if date_paiement > date.today():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La date de paiement ne peut pas être dans le futur",
        )

    # RG16 : le paiement ne peut pas dépasser le solde restant
    if data.montant > commande.solde:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Paiement supérieur au solde restant ({commande.solde} FCFA)",
        )

    paiement = Paiement(
        commande_id=commande.id,
        montant=data.montant,
        mode=data.mode,
        reference=data.reference,
        date_paiement=date_paiement,
        enregistre_par_id=acteur.id,
    )
    db.add(paiement)
    db.flush()
    recalculer_paye(db, commande)
    return paiement


def lister_paiements(db: Session, commande_id: int) -> list[Paiement]:
    get_commande(db, commande_id)
    requete = select(Paiement).where(Paiement.commande_id == commande_id).order_by(Paiement.id)
    return list(db.scalars(requete).all())


def annuler_paiement(db: Session, paiement_id: int) -> None:
    """RG17 : supprime un paiement saisi par erreur et recalcule le solde."""
    paiement = db.get(Paiement, paiement_id)
    if paiement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Paiement introuvable")

    commande = get_commande(db, paiement.commande_id)
    db.delete(paiement)
    db.flush()
    recalculer_paye(db, commande)