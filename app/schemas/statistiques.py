from datetime import date

from pydantic import BaseModel


class TableauDeBord(BaseModel):
    chiffre_affaires_mois: int
    encaisse_mois: int
    nb_commandes_mois: int
    reste_a_encaisser: int
    commandes_par_statut: dict[str, int]
    nb_commandes_en_retard: int
    commandes_pretes_a_livrer: int
    livraisons_du_jour: int


class PointPeriode(BaseModel):
    periode: str
    chiffre_affaires: int
    encaisse: int


class VentesTypeVetement(BaseModel):
    type_vetement_id: int
    nom: str
    quantite: int
    chiffre_affaires: int


class TopClient(BaseModel):
    client_id: int
    nom: str
    nb_commandes: int
    chiffre_affaires: int
    solde_du: int


class ImpayeRead(BaseModel):
    commande_id: int
    numero: str
    client_nom: str
    client_telephone: str
    statut: str
    date_livraison_prevue: date | None
    montant_total: int
    montant_paye: int
    solde: int
    en_retard: bool