from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.core.security import create_access_token
from app.database import get_db
from app.models import Utilisateur
from app.schemas.auth import Token
from app.schemas.utilisateur import UtilisateurRead
from app.services.auth import authenticate_user


router = APIRouter(prefix="/auth", tags=["Authentification"])


@router.post("/login", response_model=Token)
def login(
    formulaire: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Token:
    utilisateur = authenticate_user(db, formulaire.username, formulaire.password)
    if utilisateur is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants incorrects ou compte désactivé",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, expires_in = create_access_token(utilisateur.id)
    return Token(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UtilisateurRead)
def me(utilisateur: Utilisateur = Depends(get_current_user)) -> Utilisateur:
    return utilisateur