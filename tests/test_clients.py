from tests.outils import P, payload_client


def test_rg1_telephone_normalise_et_doublon(api, accueil):
    r = api.post(f"{P}/clients", json=payload_client("77 123 45 67"), headers=accueil)
    assert r.status_code == 201
    assert r.json()["telephone"] == "771234567"

    r = api.post(f"{P}/clients", json=payload_client("771234567"), headers=accueil)
    assert r.status_code == 409


def test_rg1_telephone_invalide_refuse(api, accueil):
    r = api.post(f"{P}/clients", json=payload_client("abc"), headers=accueil)
    assert r.status_code == 422


def test_rg4_client_avec_commandes_non_supprimable(api, admin, commande_fatou, fatou):
    r = api.delete(f"{P}/clients/{fatou['id']}", headers=admin)
    assert r.status_code == 409


def test_suppression_reservee_admin(api, accueil, fatou):
    r = api.delete(f"{P}/clients/{fatou['id']}", headers=accueil)
    assert r.status_code == 403