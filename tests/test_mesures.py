from datetime import date, timedelta

from tests.outils import P


def test_rg2_au_moins_une_mesure(api, tailleur, fatou):
    url = f"{P}/clients/{fatou['id']}/mesures"
    assert api.post(url, json={}, headers=tailleur).status_code == 422
    assert api.post(url, json={"tour_cou": 0}, headers=tailleur).status_code == 422
    assert api.post(url, json={"tour_cou": 301}, headers=tailleur).status_code == 422


def test_rg3_derniere_mesure_est_la_plus_recente(api, tailleur, fatou, mesures_fatou):
    ancienne = (date.today() - timedelta(days=30)).isoformat()
    r = api.post(
        f"{P}/clients/{fatou['id']}/mesures",
        json={"date_prise": ancienne, "tour_cou": 38},
        headers=tailleur,
    )
    assert r.status_code == 201

    r = api.get(f"{P}/clients/{fatou['id']}/mesures/derniere", headers=tailleur)
    assert r.status_code == 200
    assert r.json()["id"] == mesures_fatou["id"]


def test_rg4_mesure_utilisee_non_supprimable(api, tailleur, commande_fatou, mesures_fatou):
    r = api.delete(f"{P}/mesures/{mesures_fatou['id']}", headers=tailleur)
    assert r.status_code == 409


def test_droits_mesures_reserves_tailleur(api, accueil, fatou):
    r = api.post(f"{P}/clients/{fatou['id']}/mesures", json={"tour_cou": 38}, headers=accueil)
    assert r.status_code == 403