from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Commande, HistoriqueStatut, Utilisateur
from app.services.commandes import get_commande


# Tableau de transitions de la section 6 de l'énoncé
TRANSITIONS: dict[str, tuple[str, ...]] = {
    "en_attente": ("en_coupe", "annulee"),
    "en_coupe": ("en_couture", "annulee"),
    "en_couture": ("essayage", "terminee", "annulee"),
    "essayage": ("retouches", "terminee", "annulee"),
    "retouches": ("essayage", "terminee", "annulee"),
    "terminee": ("livree",),
    "livree": (),
    "annulee": (),
}

# Statuts qui relèvent de la production : le tailleur peut les poser
STATUTS_PRODUCTION = {"en_coupe", "en_couture", "essayage", "retouches", "terminee"}


def _verifier_droits(utilisateur: Utilisateur, nouveau: str) -> None:
    """RG14 : le tailleur ne peut pas annuler une commande (403)."""
    if nouveau == "annulee" and utilisateur.role == "tailleur":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Le tailleur ne peut pas annuler une commande",
        )


def changer_statut(
    db: Session,
    commande_id: int,
    nouveau: str,
    commentaire: str | None,
    acteur: Utilisateur,
) -> Commande:
    commande = get_commande(db, commande_id)
    actuel = commande.statut

    # RG13 : le statut « livree » ne se pose que par la confirmation de livraison
    if nouveau == "livree":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Le statut « livree » résulte de la confirmation de livraison, il ne peut pas être posé directement",
        )

    # RG13 : demander le statut déjà en cours est refusé
    if nouveau == actuel:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"La commande est déjà « {actuel} »",
        )

    _verifier_droits(acteur, nouveau)

    possibles = TRANSITIONS.get(actuel, ())
    if nouveau not in possibles:
        options = ", ".join(possibles) if possibles else "aucun (statut final)"
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Transition interdite : {actuel} → {nouveau}. Statuts possibles : {options}",
        )

    # RG14 : annuler une commande qui a reçu un acompte exige un commentaire
    if nouveau == "annulee" and commande.montant_paye > 0 and not (commentaire and commentaire.strip()):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Annuler une commande payée exige un commentaire (remboursement, avoir...)",
        )

    commande.statut = nouveau
    # RG15 : chaque changement est tracé
    db.add(
        HistoriqueStatut(
            commande_id=commande.id,
            ancien_statut=actuel,
            nouveau_statut=nouveau,
            commentaire=commentaire,
            utilisateur_id=acteur.id,
        )
    )
    db.flush()
    return commande


def historique_commande(db: Session, commande_id: int) -> list[HistoriqueStatut]:
    get_commande(db, commande_id)
    requete = (
        select(HistoriqueStatut)
        .where(HistoriqueStatut.commande_id == commande_id)
        .order_by(HistoriqueStatut.date_changement, HistoriqueStatut.id)
    )
    return list(db.scalars(requete).all())