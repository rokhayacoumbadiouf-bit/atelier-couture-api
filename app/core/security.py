from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.config import settings


ALGORITHM = "HS256"
_hasher = PasswordHasher()


def hash_password(mot_de_passe: str) -> str:
    return _hasher.hash(mot_de_passe)


def verify_password(mot_de_passe_hash: str, mot_de_passe: str) -> bool:
    try:
        return _hasher.verify(mot_de_passe_hash, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False


def create_access_token(utilisateur_id: int) -> tuple[str, int]:
    expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expiration = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": str(utilisateur_id), "exp": expiration}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)
    return token, expire_minutes * 60


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])