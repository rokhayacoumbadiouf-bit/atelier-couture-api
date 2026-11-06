from datetime import date, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, literal, select
from sqlalchemy.orm import Session

from app.models import Client, Commande, LigneCommande, Livraison, Paiement, TypeVetement
from app.schemas.statistiques import ImpayeRead, PointPeriode, TableauDeBord, TopClient, VentesTypeVetement


STATUTS_TOUS = (
    "en_attente", "en_coupe", "en_couture", "essayage",
    "retouches", "terminee", "livree", "annulee",
)


def _debut_du_mois(aujourd_hui: date) -> date:
    return aujourd_hui.replace(day=1)


def _est_en_retard(commande: Commande, aujourd_hui: date) -> bool:
    """RG11 : date prévue dépassée et ni livrée ni annulée."""
    return (
        commande.date_livraison_prevue is not None
        and commande.date_livraison_prevue < aujourd_hui
        and commande.statut not in ("livree", "annulee")
    )


def tableau_de_bord(db: Session) -> TableauDeBord:
    aujourd_hui = date.today()
    debut = _debut_du_mois(aujourd_hui)

    ca_mois, nb_mois = db.execute(
        select(func.coalesce(func.sum(Commande.montant_total), 0), func.count(Commande.id)).where(
            Commande.statut != "annulee",
            Commande.date_commande >= debut,
            Commande.date_commande <= aujourd_hui,
        )
    ).one()

    encaisse_mois = db.scalar(
        select(func.coalesce(func.sum(Paiement.montant), 0)).where(
            Paiement.date_paiement >= debut,
            Paiement.date_paiement <= aujourd_hui,
        )
    )

    reste = db.scalar(
        select(func.coalesce(func.sum(Commande.montant_total - Commande.montant_paye), 0)).where(
            Commande.statut != "annulee"
        )
    )

    # Tous les statuts apparaissent, même à 0
    compte = dict(
        db.execute(select(Commande.statut, func.count(Commande.id)).group_by(Commande.statut)).all()
    )
    par_statut = {statut: int(compte.get(statut, 0)) for statut in STATUTS_TOUS}

    en_retard = db.scalars(
        select(Commande).where(
            Commande.date_livraison_prevue < aujourd_hui,
            Commande.statut.not_in(("livree", "annulee")),
        )
    ).all()

    prets = par_statut["terminee"]
    livraisons_jour = db.scalar(
        select(func.count(Livraison.id)).where(
            Livraison.date_prevue == aujourd_hui,
            Livraison.statut == "planifiee",
        )
    )

    return TableauDeBord(
        chiffre_affaires_mois=int(ca_mois),
        encaisse_mois=int(encaisse_mois),
        nb_commandes_mois=int(nb_mois),
        reste_a_encaisser=int(reste),
        commandes_par_statut=par_statut,
        nb_commandes_en_retard=len(en_retard),
        commandes_pretes_a_livrer=prets,
        livraisons_du_jour=int(livraisons_jour),
    )


def _verifier_periode(date_debut: date, date_fin: date) -> None:
    if date_debut > date_fin:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="date_debut ne peut pas être postérieure à date_fin",
        )


def chiffre_affaires(db: Session, granularite: str, date_debut: date, date_fin: date) -> list[PointPeriode]:
    _verifier_periode(date_debut, date_fin)
    if granularite not in ("jour", "mois"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="granularite doit être « jour » ou « mois »",
        )

    format_sql = "YYYY-MM-DD" if granularite == "jour" else "YYYY-MM"

    periode_commande = func.to_char(Commande.date_commande, literal(format_sql)).label("periode")
    ca = dict(
        db.execute(
            select(periode_commande, func.sum(Commande.montant_total))
            .where(
                Commande.statut != "annulee",
                Commande.date_commande >= date_debut,
                Commande.date_commande <= date_fin,
            )
            .group_by(periode_commande)
        ).all()
    )

    periode_paiement = func.to_char(Paiement.date_paiement, literal(format_sql)).label("periode")
    encaisse = dict(
        db.execute(
            select(periode_paiement, func.sum(Paiement.montant))
            .where(Paiement.date_paiement >= date_debut, Paiement.date_paiement <= date_fin)
            .group_by(periode_paiement)
        ).all()
    )

    periodes = sorted(set(ca) | set(encaisse))
    return [
        PointPeriode(periode=p, chiffre_affaires=int(ca.get(p, 0)), encaisse=int(encaisse.get(p, 0)))
        for p in periodes
    ]


def ventes_par_type(db: Session, date_debut: date, date_fin: date) -> list[VentesTypeVetement]:
    _verifier_periode(date_debut, date_fin)
    requete = (
        select(
            TypeVetement.id,
            TypeVetement.nom,
            func.sum(LigneCommande.quantite),
            func.sum(LigneCommande.quantite * LigneCommande.prix_unitaire),
        )
        .join(LigneCommande, LigneCommande.type_vetement_id == TypeVetement.id)
        .join(Commande, Commande.id == LigneCommande.commande_id)
        .where(
            Commande.statut != "annulee",
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
        )
        .group_by(TypeVetement.id, TypeVetement.nom)
    )
    lignes = [
        VentesTypeVetement(type_vetement_id=i, nom=n, quantite=int(q), chiffre_affaires=int(ca))
        for i, n, q, ca in db.execute(requete).all()
    ]
    return sorted(lignes, key=lambda v: v.chiffre_affaires, reverse=True)


def top_clients(db: Session, date_debut: date, date_fin: date, limite: int) -> list[TopClient]:
    _verifier_periode(date_debut, date_fin)
    requete = (
        select(
            Client.id,
            Client.prenom,
            Client.nom,
            func.count(Commande.id),
            func.sum(Commande.montant_total),
            func.sum(Commande.montant_total - Commande.montant_paye),
        )
        .join(Commande, Commande.client_id == Client.id)
        .where(
            Commande.statut != "annulee",
            Commande.date_commande >= date_debut,
            Commande.date_commande <= date_fin,
        )
        .group_by(Client.id, Client.prenom, Client.nom)
        .order_by(func.sum(Commande.montant_total).desc())
        .limit(limite)
    )
    return [
        TopClient(
            client_id=i,
            nom=f"{p} {n}",
            nb_commandes=int(nb),
            chiffre_affaires=int(ca),
            solde_du=int(solde),
        )
        for i, p, n, nb, ca, solde in db.execute(requete).all()
    ]


def impayes(db: Session, limit: int, offset: int) -> tuple[list[ImpayeRead], int]:
    aujourd_hui = date.today()
    base = (
        select(Commande, Client)
        .join(Client, Commande.client_id == Client.id)
        .where(
            Commande.statut != "annulee",
            Commande.montant_total > Commande.montant_paye,
        )
    )
    total = db.scalar(select(func.count()).select_from(base.with_only_columns(Commande.id).subquery()))
    lignes = db.execute(
        base.order_by(Commande.date_livraison_prevue.asc().nulls_last(), Commande.id)
        .limit(limit)
        .offset(offset)
    ).all()

    items = [
        ImpayeRead(
            commande_id=c.id,
            numero=c.numero,
            client_nom=f"{cl.prenom} {cl.nom}",
            client_telephone=cl.telephone,
            statut=c.statut,
            date_livraison_prevue=c.date_livraison_prevue,
            montant_total=c.montant_total,
            montant_paye=c.montant_paye,
            solde=c.solde,
            en_retard=_est_en_retard(c, aujourd_hui),
        )
        for c, cl in lignes
    ]
    return items, total