from tests.outils import P


def _payer(api, accueil, commande_id, montant):
    return api.post(
        f"{P}/commandes/{commande_id}/paiements",
        json={"montant": montant, "mode": "wave", "reference": "TEST-001"},
        headers=accueil,
    )


def test_rg16_paiement_superieur_au_solde_refuse(api, accueil, commande_fatou):
    r = _payer(api, accueil, commande_fatou["id"], 100000)
    assert r.status_code == 409


def test_rg16_montant_nul_refuse(api, accueil, commande_fatou):
    r = _payer(api, accueil, commande_fatou["id"], 0)
    assert r.status_code == 422


def test_rg16_paiement_sur_commande_annulee_refuse(api, accueil, commande_fatou):
    api.post(f"{P}/commandes/{commande_fatou['id']}/statut", json={"statut": "annulee"}, headers=accueil)
    r = _payer(api, accueil, commande_fatou["id"], 1000)
    assert r.status_code == 409


def test_rg17_annulation_paiement_recalcule_le_solde(api, admin, accueil, commande_fatou):
    paiement = _payer(api, accueil, commande_fatou["id"], 20000).json()
    r = api.delete(f"{P}/paiements/{paiement['id']}", headers=admin)
    assert r.status_code == 204

    commande = api.get(f"{P}/commandes/{commande_fatou['id']}", headers=accueil).json()
    assert commande["montant_paye"] == 0
    assert commande["solde"] == 75000


def test_rg17_annulation_paiement_reservee_admin(api, accueil, commande_fatou):
    paiement = _payer(api, accueil, commande_fatou["id"], 20000).json()
    r = api.delete(f"{P}/paiements/{paiement['id']}", headers=accueil)
    assert r.status_code == 403


def test_rg14_annulation_avec_acompte_exige_commentaire(api, accueil, commande_fatou):
    _payer(api, accueil, commande_fatou["id"], 20000)
    url = f"{P}/commandes/{commande_fatou['id']}/statut"

    r = api.post(url, json={"statut": "annulee"}, headers=accueil)
    assert r.status_code == 422

    r = api.post(url, json={"statut": "annulee", "commentaire": "Remboursement en espèces"}, headers=accueil)
    assert r.status_code == 200