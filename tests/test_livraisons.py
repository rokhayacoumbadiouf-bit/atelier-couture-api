from tests.outils import P


def test_rg18_domicile_exige_une_adresse(api, accueil, commande_fatou):
    r = api.put(
        f"{P}/commandes/{commande_fatou['id']}/livraison",
        json={"mode": "domicile", "date_prevue": "2026-12-01"},
        headers=accueil,
    )
    assert r.status_code == 422


def test_rg18_replanifier_ne_cree_pas_de_seconde_livraison(api, accueil, commande_fatou):
    url = f"{P}/commandes/{commande_fatou['id']}/livraison"
    premiere = api.put(url, json={"mode": "retrait_atelier", "date_prevue": "2026-12-01"}, headers=accueil).json()
    seconde = api.put(url, json={"mode": "retrait_atelier", "date_prevue": "2026-12-05"}, headers=accueil).json()
    assert premiere["id"] == seconde["id"]
    assert seconde["date_prevue"] == "2026-12-05"


def test_rg19_confirmation_refusee_si_non_terminee(api, accueil, commande_fatou):
    r = api.post(f"{P}/commandes/{commande_fatou['id']}/livraison/confirmer", json={}, headers=accueil)
    assert r.status_code == 409


def test_rg19_solde_impaye_refuse_sauf_autorisation(api, accueil, tailleur, commande_fatou, avancer):
    avancer(commande_fatou["id"], "en_coupe", "en_couture", "essayage", "terminee")
    url = f"{P}/commandes/{commande_fatou['id']}/livraison/confirmer"

    r = api.post(url, json={}, headers=accueil)
    assert r.status_code == 409

    r = api.post(url, json={"autoriser_solde_impaye": True}, headers=accueil)
    assert r.status_code == 200
    assert r.json()["statut"] == "livree"


def test_rg20_confirmation_automatique_retrait_si_soldee(api, accueil, commande_fatou, avancer):
    api.post(
        f"{P}/commandes/{commande_fatou['id']}/paiements",
        json={"montant": 75000, "mode": "especes"},
        headers=accueil,
    )
    avancer(commande_fatou["id"], "en_coupe", "en_couture", "essayage", "terminee")

    r = api.post(f"{P}/commandes/{commande_fatou['id']}/livraison/confirmer", json={}, headers=accueil)
    assert r.status_code == 200
    assert r.json()["mode"] == "retrait_atelier"

    commande = api.get(f"{P}/commandes/{commande_fatou['id']}", headers=accueil).json()
    assert commande["statut"] == "livree"
    assert commande["solde"] == 0