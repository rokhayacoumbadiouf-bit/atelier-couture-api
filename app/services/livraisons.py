from datetime import date

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Client, Commande, HistoriqueStatut, Livraison, Utilisateur
from app.schemas.livraison import LivraisonConfirmer, LivraisonPlanifier
from app.services.commandes import get_commande


def _get_livraison(db: Session, commande_id: int) -> Livraison | None:
    return db.scalar(select(Livraison).where(Livraison.commande_id == commande_id))


def planifier_livraison(db: Session, commande_id: int, data: LivraisonPlanifier) -> Livraison:
    commande = get_commande(db, commande_id)

    # RG12 : commande livrée ou annulée non modifiable
    if commande.statut in ("livree", "annulee"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une commande « {commande.statut} » ne peut plus être modifiée",
        )

    # RG18 : une livraison à domicile exige une adresse
    if data.mode == "domicile" and not (data.adresse and data.adresse.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Une livraison à domicile exige une adresse",
        )

    livraison = _get_livraison(db, commande.id)
    if livraison is None:
        livraison = Livraison(commande_id=commande.id, statut="planifiee")
        db.add(livraison)

    # RG18 : replanifier modifie la livraison existante, sans en créer une seconde
    livraison.mode = data.mode
    livraison.date_prevue = data.date_prevue
    livraison.adresse = data.adresse if data.mode == "domicile" else None
    livraison.livreur = data.livreur
    livraison.notes = data.notes

    # RG18 : la date prévue de la commande est mise à jour
    commande.date_livraison_prevue = data.date_prevue
    db.flush()
    return livraison


def get_livraison(db: Session, commande_id: int) -> Livraison:
    get_commande(db, commande_id)
    livraison = _get_livraison(db, commande_id)
    if livraison is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Aucune livraison planifiée pour cette commande")
    return livraison


def confirmer_livraison(
    db: Session,
    commande_id: int,
    data: LivraisonConfirmer,
    acteur: Utilisateur,
) -> Livraison:
    commande = get_commande(db, commande_id)

    # RG19 : la commande doit être « terminee »
    if commande.statut != "terminee":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Confirmer une livraison exige une commande « terminee » (actuelle : « {commande.statut} »)",
        )

    # RG19 : la commande doit être soldée, sauf autorisation explicite
    if commande.solde > 0 and not data.autoriser_solde_impaye:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Commande non soldée : montant impayé {commande.solde} FCFA",
        )

    livraison = _get_livraison(db, commande.id)
    # RG20 : sans planification préalable, une livraison retrait_atelier est créée automatiquement
    if livraison is None:
        livraison = Livraison(
            commande_id=commande.id,
            mode="retrait_atelier",
            date_prevue=commande.date_livraison_prevue or date.today(),
            statut="planifiee",
        )
        db.add(livraison)

    date_effective = data.date_effective or date.today()
    livraison.statut = "livree"
    livraison.date_effective = date_effective

    # RG20 : la commande passe à « livree » et la date réelle est renseignée
    ancien = commande.statut
    commande.statut = "livree"
    commande.date_livraison_reelle = date_effective

    # RG19 : la mention d'un solde impayé est inscrite dans l'historique
    commentaire = None
    if commande.solde > 0:
        commentaire = f"Livraison confirmée avec solde impayé de {commande.solde} FCFA (autorisation explicite)"

    db.add(
        HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut=ancien,
            nouveau_statut="livree",
            commentaire=commentaire,
            utilisateur_id=acteur.id,
        )
    )
    db.flush()
    return livraison


def lister_livraisons(
    db: Session,
    statut: str | None,
    date_min: date | None,
    date_max: date | None,
):
    requete = (
        select(Livraison, Commande, Client)
        .join(Commande, Livraison.commande_id == Commande.id)
        .join(Client, Commande.client_id == Client.id)
    )
    if statut is not None:
        requete = requete.where(Livraison.statut == statut)
    if date_min is not None:
        requete = requete.where(Livraison.date_prevue >= date_min)
    if date_max is not None:
        requete = requete.where(Livraison.date_prevue <= date_max)
    return list(db.execute(requete.order_by(Livraison.date_prevue, Livraison.id)).all())