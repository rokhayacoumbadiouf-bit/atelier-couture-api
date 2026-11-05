from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import Utilisateur
from app.schemas.utilisateur import UtilisateurCreate, UtilisateurUpdate


def lister_utilisateurs(db: Session) -> list[Utilisateur]:
    return list(db.scalars(select(Utilisateur).order_by(Utilisateur.nom_complet)).all())


def get_utilisateur(db: Session, utilisateur_id: int) -> Utilisateur:
    utilisateur = db.get(Utilisateur, utilisateur_id)
    if utilisateur is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    return utilisateur


def creer_utilisateur(db: Session, data: UtilisateurCreate) -> Utilisateur:
    existe = db.scalar(select(Utilisateur.id).where(Utilisateur.email == data.email))
    if existe is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Un compte existe déjà avec l'e-mail {data.email}",
        )
    utilisateur = Utilisateur(
        email=data.email,
        nom_complet=data.nom_complet,
        mot_de_passe_hash=hash_password(data.mot_de_passe),
        role=data.role,
    )
    db.add(utilisateur)
    db.flush()
    return utilisateur


def modifier_utilisateur(
    db: Session, utilisateur_id: int, data: UtilisateurUpdate, acteur: Utilisateur
) -> Utilisateur:
    utilisateur = get_utilisateur(db, utilisateur_id)
    modifications = data.model_dump(exclude_unset=True)

    # RG24 : un administrateur ne peut ni se désactiver ni retirer son propre rôle admin
    if utilisateur.id == acteur.id:
        if modifications.get("actif") is False:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un administrateur ne peut pas se désactiver lui-même",
            )
        if "role" in modifications and modifications["role"] != "admin":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Un administrateur ne peut pas retirer son propre rôle admin",
            )

    if "mot_de_passe" in modifications:
        utilisateur.mot_de_passe_hash = hash_password(modifications.pop("mot_de_passe"))
    for champ, valeur in modifications.items():
        setattr(utilisateur, champ, valeur)

    db.flush()
    return utilisateur