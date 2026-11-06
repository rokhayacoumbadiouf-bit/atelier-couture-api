P = "/api/v1"


def payload_client(telephone: str = "77 123 45 67", nom: str = "Diop", prenom: str = "Fatou") -> dict:
    return {"nom": nom, "prenom": prenom, "telephone": telephone, "genre": "femme"}