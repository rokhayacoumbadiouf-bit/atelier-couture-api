from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import TypeVetement
from app.schemas.type_vetement import TypeVetementCreate, TypeVetementUpdate


def verifier_nom_libre(db: Session, nom: str, exclu_id: int | None = None) -> None:
    requete = select(TypeVetement.id).where(TypeVetement.nom == nom)
    if exclu_id is not None:
        requete = requete.where(TypeVetement.id != exclu_id)
    if db.scalar(requete) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Une prestation nommée « {nom} » existe déjà",
        )


def get_prestation(db: Session, prestation_id: int) -> TypeVetement:
    prestation = db.get(TypeVetement, prestation_id)
    if prestation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prestation introuvable")
    return prestation


def creer_prestation(db: Session, data: TypeVetementCreate) -> TypeVetement:
    verifier_nom_libre(db, data.nom)
    prestation = TypeVetement(**data.model_dump())
    db.add(prestation)
    db.flush()
    return prestation


def modifier_prestation(db: Session, prestation_id: int, data: TypeVetementUpdate) -> TypeVetement:
    prestation = get_prestation(db, prestation_id)
    modifications = data.model_dump(exclude_unset=True)

    if "nom" in modifications:
        verifier_nom_libre(db, modifications["nom"], exclu_id=prestation.id)

    # Un champ obligatoire ne peut pas être vidé
    for champ in ("nom", "prix_base", "delai_jours", "actif"):
        if champ in modifications and modifications[champ] is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Le champ « {champ} » ne peut pas être vidé",
            )

    # actif=false retire la prestation sans toucher aux anciennes commandes
    for champ, valeur in modifications.items():
        setattr(prestation, champ, valeur)

    db.flush()
    return prestation


def lister_prestations(db: Session, actifs_seulement: bool) -> list[TypeVetement]:
    requete = select(TypeVetement).order_by(TypeVetement.nom)
    if actifs_seulement:
        requete = requete.where(TypeVetement.actif.is_(True))
    return list(db.scalars(requete).all())