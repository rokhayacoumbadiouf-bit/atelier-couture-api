import re

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models import Client
from app.schemas.client import ClientCreate, ClientUpdate


_SEPARATEURS = re.compile(r"[ .\-()]")
_TELEPHONE_VALIDE = re.compile(r"^\+?\d{6,20}$")
CHAMPS_OBLIGATOIRES = {"nom", "prenom", "telephone", "genre"}


def normaliser_telephone(brut: str) -> str:
    """RG1 : supprime espaces, points, tirets et parenthèses, puis valide la forme."""
    telephone = _SEPARATEURS.sub("", brut)
    if not _TELEPHONE_VALIDE.match(telephone):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Numéro de téléphone invalide : 6 à 20 chiffres, avec un + initial facultatif",
        )
    return telephone


def verifier_telephone_libre(db: Session, telephone: str, exclu_id: int | None = None) -> None:
    requete = select(Client.id).where(Client.telephone == telephone)
    if exclu_id is not None:
        requete = requete.where(Client.id != exclu_id)
    if db.scalar(requete) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Un client existe déjà avec ce numéro de téléphone",
        )


def get_client(db: Session, client_id: int) -> Client:
    client = db.get(Client, client_id)
    if client is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client introuvable")
    return client


def creer_client(db: Session, data: ClientCreate) -> Client:
    telephone = normaliser_telephone(data.telephone)
    verifier_telephone_libre(db, telephone)
    client = Client(**data.model_dump(exclude={"telephone"}), telephone=telephone)
    db.add(client)
    db.flush()
    return client


def modifier_client(db: Session, client_id: int, data: ClientUpdate) -> Client:
    client = get_client(db, client_id)
    modifications = data.model_dump(exclude_unset=True)

    for champ in CHAMPS_OBLIGATOIRES:
        if champ in modifications and modifications[champ] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Le champ « {champ} » ne peut pas être vidé",
            )

    if "telephone" in modifications:
        telephone = normaliser_telephone(modifications["telephone"])
        verifier_telephone_libre(db, telephone, exclu_id=client.id)
        modifications["telephone"] = telephone

    for champ, valeur in modifications.items():
        setattr(client, champ, valeur)

    db.flush()
    return client


def supprimer_client(db: Session, client_id: int) -> None:
    client = get_client(db, client_id)
    # RG4 : le refus si le client a des commandes sera ajouté avec le modèle Commande (palier 2)
    db.delete(client)
    db.flush()


def lister_clients(
    db: Session,
    q: str | None,
    genre: str | None,
    limit: int,
    offset: int,
) -> tuple[list[Client], int]:
    requete = select(Client)

    if q is not None:
        if len(q.strip()) < 2:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="La recherche demande au moins 2 caractères",
            )
        motif = f"%{q.strip()}%"
        requete = requete.where(
            or_(Client.nom.ilike(motif), Client.prenom.ilike(motif), Client.telephone.ilike(motif))
        )

    if genre is not None:
        requete = requete.where(Client.genre == genre)

    total = db.scalar(select(func.count()).select_from(requete.subquery()))
    items = db.scalars(
        requete.order_by(Client.nom, Client.prenom).limit(limit).offset(offset)
    ).all()
    return list(items), total