from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import verify_password
from app.models import Utilisateur


def authenticate_user(db: Session, email: str, mot_de_passe: str) -> Utilisateur | None:
    utilisateur = db.scalar(select(Utilisateur).where(Utilisateur.email == email))
    if utilisateur is None:
        return None
    if not verify_password(utilisateur.mot_de_passe_hash, mot_de_passe):
        return None
    if not utilisateur.actif:
        return None
    return utilisateur