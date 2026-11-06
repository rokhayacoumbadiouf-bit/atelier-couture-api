from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Commande, LigneCommande, Mesure, TypeVetement, HistoriqueStatut, Utilisateur
from app.models.utilisateur import Utilisateur
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
    db.add(
        HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut=None,
            nouveau_statut="en_attente",
            utilisateur_id=acteur.id,
        )
    )
    db.flush()
    return commande

def _verifier_modifiable(commande: Commande) -> None:
    """RG12 : une commande livrée ou annulée n'est plus modifiable."""
    if commande.statut in ("livree", "annulee"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une commande « {commande.statut} » ne peut plus être modifiée",
        )


def _verifier_lignes_modifiables(commande: Commande) -> None:
    """RG10 : les lignes ne sont modifiables que tant que la commande est en attente."""
    if commande.statut != "en_attente":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Les prestations ne peuvent être modifiées que tant que la commande est en attente",
        )


def modifier_commande(db: Session, commande_id: int, data) -> Commande:
    """PATCH : mesure_id, date_livraison_prevue, remise, notes. Recalcule les montants."""
    commande = get_commande(db, commande_id)
    _verifier_modifiable(commande)
    modifications = data.model_dump(exclude_unset=True)

    if "mesure_id" in modifications:
        commande.mesure_id = _mesure_pour_commande(db, commande.client_id, modifications["mesure_id"])

    if "date_livraison_prevue" in modifications:
        if modifications["date_livraison_prevue"] is not None and modifications["date_livraison_prevue"] < commande.date_commande:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La date de livraison prévue ne peut pas précéder la date de commande",
            )
        commande.date_livraison_prevue = modifications["date_livraison_prevue"]

    if "remise" in modifications:
        commande.remise = modifications["remise"]

    if "notes" in modifications:
        commande.notes = modifications["notes"]

    recalculer_montants(commande)
    db.flush()
    return commande


def ajouter_ligne(db: Session, commande_id: int, data) -> Commande:
    """RG6, RG10 : ajoute une prestation et recalcule les montants."""
    commande = get_commande(db, commande_id)
    _verifier_lignes_modifiables(commande)

    prestation = db.get(TypeVetement, data.type_vetement_id)
    if prestation is None or not prestation.actif:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prestation introuvable ou plus disponible",
        )

    prix = data.prix_unitaire if data.prix_unitaire is not None else prestation.prix_base
    commande.lignes.append(
        LigneCommande(
            type_vetement_id=prestation.id,
            description=data.description,
            quantite=data.quantite,
            prix_unitaire=prix,
        )
    )
    recalculer_montants(commande)
    db.flush()
    return commande


def retirer_ligne(db: Session, commande_id: int, ligne_id: int) -> Commande:
    """RG10 : retire une prestation. Une commande garde toujours au moins une ligne."""
    commande = get_commande(db, commande_id)
    _verifier_lignes_modifiables(commande)

    ligne = next((l for l in commande.lignes if l.id == ligne_id), None)
    if ligne is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ligne introuvable")
    if len(commande.lignes) == 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Une commande doit garder au moins une prestation",
        )

    commande.lignes.remove(ligne)
    db.flush()
    recalculer_montants(commande)
    db.flush()
    return commande


def lister_commandes(
    db: Session,
    statut: str | None,
    client_id: int | None,
    date_min,
    date_max,
    numero: str | None,
    limit: int,
    offset: int,
):
    """Liste paginée, la plus récente d'abord. Ajoute aussi le solde et le retard (RG11)."""
    requete = select(Commande)
    if statut is not None:
        requete = requete.where(Commande.statut == statut)
    if client_id is not None:
        requete = requete.where(Commande.client_id == client_id)
    if date_min is not None:
        requete = requete.where(Commande.date_commande >= date_min)
    if date_max is not None:
        requete = requete.where(Commande.date_commande <= date_max)
    if numero is not None:
        requete = requete.where(Commande.numero == numero)

    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Commande.date_commande.desc(), Commande.id.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return list(items), total