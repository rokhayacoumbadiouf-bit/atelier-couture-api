import re
from datetime import timedelta

from tests.outils import P, payload_client


def test_rg5_numero_au_format_attendu(commande_fatou):
    assert re.match(r"^CMD-\d{4}-\d{5}$", commande_fatou["numero"])


def test_rg7_montant_total_calcule_par_le_serveur(commande_fatou):
    assert commande_fatou["montant_total"] == 75000
    assert commande_fatou["solde"] == 75000


def test_rg7_remise_superieure_au_total_refusee(api, accueil, fatou, prestations):
    r = api.post(
        f"{P}/commandes",
        json={
            "client_id": fatou["id"],
            "lignes": [{"type_vetement_id": prestations["pantalon"], "quantite": 1}],
            "remise": 999999,
        },
        headers=accueil,
    )
    assert r.status_code == 422


def test_rg6_prix_par_defaut_du_catalogue(api, accueil, fatou, prestations):
    r = api.post(
        f"{P}/commandes",
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": prestations["boubou"]}]},
        headers=accueil,
    )
    assert r.status_code == 201
    assert r.json()["lignes"][0]["prix_unitaire"] == 35000


def test_rg6_prestation_inactive_non_commandable(api, admin, accueil, fatou, prestations):
    r = api.patch(f"{P}/catalogue/{prestations['pantalon']}", json={"actif": False}, headers=admin)
    assert r.status_code == 200

    r = api.post(
        f"{P}/commandes",
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": prestations["pantalon"]}]},
        headers=accueil,
    )
    assert r.status_code == 422


def test_rg8_date_prevue_par_defaut(api, accueil, fatou, prestations, aujourdhui):
    r = api.post(
        f"{P}/commandes",
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": prestations["boubou"]}]},
        headers=accueil,
    )
    assert r.json()["date_livraison_prevue"] == (aujourdhui + timedelta(days=10)).isoformat()


def test_rg9_mesures_d_un_autre_client_refusees(api, accueil, mesures_fatou, prestations):
    autre = api.post(f"{P}/clients", json=payload_client("770000001", nom="Ndiaye", prenom="Awa"), headers=accueil)
    assert autre.status_code == 201

    r = api.post(
        f"{P}/commandes",
        json={
            "client_id": autre.json()["id"],
            "mesure_id": mesures_fatou["id"],
            "lignes": [{"type_vetement_id": 1}],
        },
        headers=accueil,
    )
    assert r.status_code == 422


def test_droits_creation_commande_reservee_accueil(api, tailleur, fatou, prestations):
    r = api.post(
        f"{P}/commandes",
        json={"client_id": fatou["id"], "lignes": [{"type_vetement_id": prestations["boubou"]}]},
        headers=tailleur,
    )
    assert r.status_code == 403