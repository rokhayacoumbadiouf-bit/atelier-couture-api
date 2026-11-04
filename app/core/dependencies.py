import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.database import get_db
from app.models import Utilisateur


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Utilisateur:
    def erreur_401() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Jeton invalide ou expiré",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = decode_access_token(token)
        utilisateur_id = int(payload["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise erreur_401()

    utilisateur = db.get(Utilisateur, utilisateur_id)
    if utilisateur is None or not utilisateur.actif:
        raise erreur_401()
    return utilisateur


def require_roles(*roles: str):
    """L'administrateur est autorisé partout ; les autres rôles doivent figurer dans la liste."""

    def verifier(utilisateur: Utilisateur = Depends(get_current_user)) -> Utilisateur:
        if utilisateur.role != "admin" and utilisateur.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Rôle insuffisant pour cette action",
            )
        return utilisateur

    return verifier