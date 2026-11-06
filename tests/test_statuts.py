from tests.outils import P


def test_rg13_transition_interdite_indique_les_statuts_possibles(api, tailleur, commande_fatou):
    r = api.post(f"{P}/commandes/{commande_fatou['id']}/statut", json={"statut": "terminee"}, headers=tailleur)
    assert r.status_code == 409
    assert "en_coupe, annulee" in r.json()["detail"]


def test_rg13_statut_deja_en_cours_refuse(api, tailleur, commande_fatou, avancer):
    avancer(commande_fatou["id"], "en_coupe")
    r = api.post(f"{P}/commandes/{commande_fatou['id']}/statut", json={"statut": "en_coupe"}, headers=tailleur)
    assert r.status_code == 409


def test_rg13_livree_non_posable_directement(api, tailleur, commande_fatou, avancer):
    avancer(commande_fatou["id"], "en_coupe", "en_couture", "essayage", "terminee")
    r = api.post(f"{P}/commandes/{commande_fatou['id']}/statut", json={"statut": "livree"}, headers=tailleur)
    assert r.status_code == 409


def test_rg14_tailleur_ne_peut_pas_annuler(api, tailleur, commande_fatou):
    r = api.post(f"{P}/commandes/{commande_fatou['id']}/statut", json={"statut": "annulee"}, headers=tailleur)
    assert r.status_code == 403


def test_rg15_historique_trace_chaque_changement(api, tailleur, commande_fatou, avancer):
    avancer(commande_fatou["id"], "en_coupe")
    r = api.get(f"{P}/commandes/{commande_fatou['id']}/historique", headers=tailleur)
    assert r.status_code == 200
    historique = r.json()
    assert len(historique) == 2
    assert historique[0]["ancien_statut"] is None
    assert historique[0]["nouveau_statut"] == "en_attente"
    assert historique[1]["nouveau_statut"] == "en_coupe"