from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Commande, LigneCommande, Mesure, TypeVetement, Utilisateur
from app.schemas.commande import CommandeCreate
from app.services.clients import get_client


def get_commande(db: Session, commande_id: int) -> Commande:
    commande = db.get(Commande, commande_id)
    if commande is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")
    return commande


def generer_numero(db: Session, annee: int) -> str:
    """RG5 : CMD-AAAA-NNNNN, numéro séquentiel par année."""
    prefixe = f"CMD-{annee}-"
    dernier = db.scalar(
        select(Commande.numero)
        .where(Commande.numero.like(f"{prefixe}%"))
        .order_by(Commande.numero.desc())
        .limit(1)
    )
    suivant = int(dernier.rsplit("-", 1)[1]) + 1 if dernier else 1
    return f"{prefixe}{suivant:05d}"


def _mesure_pour_commande(db: Session, client_id: int, mesure_id: int | None) -> int | None:
    """RG9 : les mesures doivent appartenir au client. Sans précision, on prend les dernières."""
    if mesure_id is not None:
        mesure = db.get(Mesure, mesure_id)
        if mesure is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Prise de mesures introuvable",
            )
        if mesure.client_id != client_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Ces mesures n'appartiennent pas à ce client",
            )
        return mesure.id

    return db.scalar(
        select(Mesure.id)
        .where(Mesure.client_id == client_id)
        .order_by(Mesure.date_prise.desc(), Mesure.id.desc())
        .limit(1)
    )


def recalculer_montants(commande: Commande) -> None:
    """RG7 : total = somme(quantité × prix unitaire) − remise. Le payé viendra en T3.5."""
    sous_total = sum(ligne.quantite * ligne.prix_unitaire for ligne in commande.lignes)
    if commande.remise > sous_total:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"La remise ({commande.remise}) ne peut pas dépasser le total des prestations ({sous_total})",
        )
    commande.montant_total = sous_total - commande.remise


def creer_commande(db: Session, data: CommandeCreate, acteur: Utilisateur) -> Commande:
    client = get_client(db, data.client_id)
    aujourd_hui = date.today()

    # RG8 : la date prévue ne peut pas précéder la date de commande
    if data.date_livraison_prevue is not None and data.date_livraison_prevue < aujourd_hui:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La date de livraison prévue ne peut pas être antérieure à la date de commande",
        )

    lignes: list[LigneCommande] = []
    delai_max = 0
    for ligne in data.lignes:
        prestation = db.get(TypeVetement, ligne.type_vetement_id)
        if prestation is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Prestation {ligne.type_vetement_id} introuvable",
            )
        # RG6 : une prestation inactive ne peut plus être commandée
        if not prestation.actif:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"La prestation « {prestation.nom} » n'est plus disponible",
            )
        # RG6 : prix de base par défaut, négociable ligne par ligne
        prix = ligne.prix_unitaire if ligne.prix_unitaire is not None else prestation.prix_base
        delai_max = max(delai_max, prestation.delai_jours)
        lignes.append(
            LigneCommande(
                type_vetement_id=prestation.id,
                description=ligne.description,
                quantite=ligne.quantite,
                prix_unitaire=prix,
            )
        )

    commande = Commande(
        numero=generer_numero(db, aujourd_hui.year),
        client_id=client.id,
        mesure_id=_mesure_pour_commande(db, client.id, data.mesure_id),
        statut="en_attente",
        date_commande=aujourd_hui,
        # RG8 : par défaut, date de commande + plus long délai
        date_livraison_prevue=data.date_livraison_prevue or aujourd_hui + timedelta(days=delai_max),
        remise=data.remise,
        montant_paye=0,
        notes=data.notes,
        cree_par_id=acteur.id,
    )
    commande.lignes = lignes
    recalculer_montants(commande)

    db.add(commande)
    db.flush()
    return commande