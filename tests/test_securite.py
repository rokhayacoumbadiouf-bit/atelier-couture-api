from tests.outils import P


def test_rg21_hash_jamais_renvoye(api, admin):
    r = api.get(f"{P}/utilisateurs", headers=admin)
    assert r.status_code == 200
    assert "mot_de_passe_hash" not in r.text


def test_rg22_compte_desactive_refuse_immediatement(api, admin, tailleur):
    # Le jeton du tailleur est obtenu avant la désactivation
    tailleur_id = api.get(f"{P}/auth/me", headers=tailleur).json()["id"]
    r = api.patch(f"{P}/utilisateurs/{tailleur_id}", json={"actif": False}, headers=admin)
    assert r.status_code == 200

    r = api.get(f"{P}/auth/me", headers=tailleur)
    assert r.status_code == 401


def test_rg23_message_identique_email_inconnu_ou_mauvais_mot_de_passe(api, admin):
    inconnu = api.post(f"{P}/auth/login", data={"username": "inconnu@test.sn", "password": "mauvais12345"})
    faux_mdp = api.post(f"{P}/auth/login", data={"username": "admin@test.sn", "password": "mauvais12345"})
    assert inconnu.status_code == faux_mdp.status_code == 401
    assert inconnu.json() == faux_mdp.json()


def test_rg24_admin_ne_peut_pas_se_desactiver(api, admin):
    admin_id = api.get(f"{P}/auth/me", headers=admin).json()["id"]
    r = api.patch(f"{P}/utilisateurs/{admin_id}", json={"actif": False}, headers=admin)
    assert r.status_code == 409


def test_sans_jeton_401(api):
    assert api.get(f"{P}/clients").status_code == 401


def test_roles_utilisateurs_reserves_admin(api, accueil):
    assert api.get(f"{P}/utilisateurs", headers=accueil).status_code == 403


def test_roles_statistiques_reservees_admin(api, accueil):
    assert api.get(f"{P}/statistiques/tableau-de-bord", headers=accueil).status_code == 403