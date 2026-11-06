from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ModePaiement = Literal["especes", "wave", "orange_money", "virement", "cheque"]


class PaiementCreate(BaseModel):
    montant: int = Field(gt=0)
    mode: ModePaiement
    reference: str | None = Field(default=None, max_length=100)
    date_paiement: date | None = None


class PaiementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    commande_id: int
    montant: int
    mode: str
    reference: str | None
    date_paiement: date
    enregistre_par_id: int
    created_at: datetime