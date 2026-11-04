from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError


_hasher = PasswordHasher()


def hash_password(mot_de_passe: str) -> str:
    return _hasher.hash(mot_de_passe)


def verify_password(mot_de_passe_hash: str, mot_de_passe: str) -> bool:
    try:
        return _hasher.verify(mot_de_passe_hash, mot_de_passe)
    except (VerificationError, InvalidHashError):
        return False