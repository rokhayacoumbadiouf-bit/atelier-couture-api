from datetime import date

from fastapi import APIRouter, Body, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_roles
from app.database import get_db
from app.models import Utilisateur
from app.schemas.livraison import LivraisonConfirmer, LivraisonPlanifier, LivraisonRead, LivraisonTournee
from app.services import livraisons as service


router_commandes = APIRouter(prefix="/commandes", tags=["Livraisons"])
router_livraisons = APIRouter(prefix="/livraisons", tags=["Livraisons"])


@router_commandes.put("/{commande_id}/livraison", response_model=LivraisonRead)
def planifier(
    commande_id: int,
    data: LivraisonPlanifier,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(require_roles("accueil")),
):
    livraison = service.planifier_livraison(db, commande_id, data)
    db.commit()
    return livraison


@router_commandes.get("/{commande_id}/livraison", response_model=LivraisonRead)
def detail(
    commande_id: int,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    return service.get_livraison(db, commande_id)


@router_commandes.post("/{commande_id}/livraison/confirmer", response_model=LivraisonRead)
def confirmer(
    commande_id: int,
    data: LivraisonConfirmer | None = Body(default=None),
    db: Session = Depends(get_db),
    acteur: Utilisateur = Depends(require_roles("accueil")),
):
    livraison = service.confirmer_livraison(db, commande_id, data or LivraisonConfirmer(), acteur)
    db.commit()
    return livraison


@router_livraisons.get("", response_model=list[LivraisonTournee])
def tournee(
    statut: str | None = None,
    date_min: date | None = None,
    date_max: date | None = None,
    db: Session = Depends(get_db),
    _: Utilisateur = Depends(get_current_user),
):
    lignes = service.lister_livraisons(db, statut, date_min, date_max)
    return [
        LivraisonTournee(
            id=livraison.id,
            commande_id=livraison.commande_id,
            mode=livraison.mode,
            adresse=livraison.adresse,
            livreur=livraison.livreur,
            date_prevue=livraison.date_prevue,
            date_effective=livraison.date_effective,
            statut=livraison.statut,
            notes=livraison.notes,
            numero_commande=commande.numero,
            client_nom=f"{client.prenom} {client.nom}",
            client_telephone=client.telephone,
            solde_commande=commande.solde,
        )
        for livraison, commande, client in lignes
    ]