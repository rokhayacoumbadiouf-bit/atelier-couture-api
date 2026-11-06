from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.core.security import hash_password
from app.database import Base, get_db
from app.main import app
from app.models import TypeVetement, Utilisateur
from tests.outils import P, payload_client


MOT_DE_PASSE = "motdepasse123"

URL_TEST = make_url(settings.DATABASE_URL).set(database="atelier_couture_test")
engine_test = create_engine(URL_TEST, pool_pre_ping=True)
SessionTest = sessionmaker(bind=engine_test, autoflush=False, expire_on_commit=False)


def _session_de_test():
    session = SessionTest()
    try:
        yield session
    finally:
        session.close()


# Toutes les requêtes de l'API utilisent la base de test
app.dependency_overrides[get_db] = _session_de_test


@pytest.fixture(scope="session", autouse=True)
def schema():
    Base.metadata.drop_all(engine_test)
    Base.metadata.create_all(engine_test)
    yield
    Base.metadata.drop_all(engine_test)


@pytest.fixture(autouse=True)
def nettoyer_base():
    yield
    with engine_test.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture
def api():
    return TestClient(app)


@pytest.fixture
def db():
    session = SessionTest()
    yield session
    session.close()


@pytest.fixture
def entetes(api, db):
    def _entetes(role: str) -> dict:
        email = f"{role}@test.sn"
        if db.scalar(select(Utilisateur.id).where(Utilisateur.email == email)) is None:
            db.add(
                Utilisateur(
                    email=email,
                    nom_complet=role.title(),
                    mot_de_passe_hash=hash_password(MOT_DE_PASSE),
                    role=role,
                )
            )
            db.commit()
        r = api.post(f"{P}/auth/login", data={"username": email, "password": MOT_DE_PASSE})
        assert r.status_code == 200, r.text
        return {"Authorization": f"Bearer {r.json()['access_token']}"}

    return _entetes


@pytest.fixture
def admin(entetes):
    return entetes("admin")


@pytest.fixture
def accueil(entetes):
    return entetes("accueil")


@pytest.fixture
def tailleur(entetes):
    return entetes("tailleur")


@pytest.fixture
def prestations(db):
    boubou = TypeVetement(nom="Boubou", prix_base=35000, delai_jours=10)
    pantalon = TypeVetement(nom="Pantalon", prix_base=12000, delai_jours=4)
    db.add_all([boubou, pantalon])
    db.commit()
    return {"boubou": boubou.id, "pantalon": pantalon.id}


@pytest.fixture
def fatou(api, accueil):
    r = api.post(f"{P}/clients", json=payload_client(), headers=accueil)
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def mesures_fatou(api, tailleur, fatou):
    r = api.post(
        f"{P}/clients/{fatou['id']}/mesures",
        json={"tour_poitrine": 96, "longueur_manche": 62},
        headers=tailleur,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def commande_fatou(api, accueil, fatou, mesures_fatou, prestations):
    """2 boubous (35 000) + 1 pantalon négocié (10 000) − remise 5 000 = 75 000 FCFA."""
    r = api.post(
        f"{P}/commandes",
        json={
            "client_id": fatou["id"],
            "lignes": [
                {"type_vetement_id": prestations["boubou"], "quantite": 2},
                {"type_vetement_id": prestations["pantalon"], "quantite": 1, "prix_unitaire": 10000},
            ],
            "remise": 5000,
        },
        headers=accueil,
    )
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture
def avancer(api, tailleur):
    def _avancer(commande_id: int, *statuts: str) -> None:
        for statut in statuts:
            r = api.post(f"{P}/commandes/{commande_id}/statut", json={"statut": statut}, headers=tailleur)
            assert r.status_code == 200, r.text

    return _avancer


@pytest.fixture
def aujourdhui():
    return date.today()