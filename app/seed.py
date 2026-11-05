from sqlalchemy import select

from app.config import settings
from app.core.security import hash_password
from app.database import SessionLocal
from app.models import TypeVetement, Utilisateur


CATALOGUE_DE_DEPART = [
    {"nom": "Boubou", "description": "Boubou homme en bazin ou brodé", "prix_base": 35000, "delai_jours": 10},
    {"nom": "Costume 2 pièces", "description": "Veste et pantalon", "prix_base": 85000, "delai_jours": 14},
    {"nom": "Robe", "description": "Robe sur mesure", "prix_base": 30000, "delai_jours": 7},
    {"nom": "Ensemble wax", "description": "Tenue deux pièces en wax", "prix_base": 25000, "delai_jours": 7},
    {"nom": "Chemise", "description": "Chemise sur mesure", "prix_base": 15000, "delai_jours": 5},
    {"nom": "Pantalon", "description": "Pantalon sur mesure", "prix_base": 12000, "delai_jours": 4},
    {"nom": "Retouche", "description": "Ourlet, rétrécissement, remplacement de fermeture", "prix_base": 3000, "delai_jours": 2},
]


def creer_administrateur(db) -> None:
    if not settings.ADMIN_PASSWORD or len(settings.ADMIN_PASSWORD) < 8:
        raise SystemExit("ADMIN_PASSWORD doit être renseigné dans .env (8 caractères minimum)")

    existe = db.scalar(select(Utilisateur.id).where(Utilisateur.email == settings.ADMIN_EMAIL))
    if existe is not None:
        print(f"Administrateur déjà présent : {settings.ADMIN_EMAIL}")
        return

    db.add(
        Utilisateur(
            email=settings.ADMIN_EMAIL,
            nom_complet=settings.ADMIN_NOM_COMPLET,
            mot_de_passe_hash=hash_password(settings.ADMIN_PASSWORD),
            role="admin",
        )
    )
    print(f"Administrateur créé : {settings.ADMIN_EMAIL}")


def creer_catalogue(db) -> None:
    ajoutees = 0
    for prestation in CATALOGUE_DE_DEPART:
        existe = db.scalar(select(TypeVetement.id).where(TypeVetement.nom == prestation["nom"]))
        if existe is None:
            db.add(TypeVetement(**prestation))
            ajoutees += 1
    print(f"Catalogue : {ajoutees} prestation(s) ajoutée(s)")


def main() -> None:
    db = SessionLocal()
    try:
        creer_administrateur(db)
        creer_catalogue(db)
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()