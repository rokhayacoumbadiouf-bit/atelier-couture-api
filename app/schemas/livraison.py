from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LivraisonPlanifier(BaseModel):
    mode: Literal["retrait_atelier", "domicile"]
    date_prevue: date
    adresse: str | None = Field(default=None, max_length=255)
    livreur: str | None = Field(default=None, max_length=100)
    notes: str | None = None


class LivraisonConfirmer(BaseModel):
    date_effective: date | None = None
    autoriser_solde_impaye: bool = False


class LivraisonRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    mode: str
    adresse: str | None
    livreur: str | None
    date_prevue: date
    date_effective: date | None
    statut: str
    notes: str | None


class LivraisonTournee(LivraisonRead):
    numero_commande: str
    client_nom: str
    client_telephone: str
    solde_commande: int