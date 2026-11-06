from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class LigneCreate(BaseModel):
    type_vetement_id: int
    quantite: int = Field(default=1, gt=0)
    prix_unitaire: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=255)


class CommandeCreate(BaseModel):
    client_id: int
    mesure_id: int | None = None
    lignes: list[LigneCreate] = Field(min_length=1)
    remise: int = Field(default=0, ge=0)
    date_livraison_prevue: date | None = None
    notes: str | None = None


class LigneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type_vetement_id: int
    description: str | None
    quantite: int
    prix_unitaire: int


class CommandeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    client_id: int
    mesure_id: int | None
    statut: str
    date_commande: date
    date_livraison_prevue: date | None
    date_livraison_reelle: date | None
    remise: int
    montant_total: int
    montant_paye: int
    solde: int
    notes: str | None
    lignes: list[LigneRead]
    created_at: datetime
    updated_at: datetime