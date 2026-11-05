from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


Genre = Literal["homme", "femme", "enfant"]


class ClientCreate(BaseModel):
    nom: str = Field(min_length=1, max_length=100)
    prenom: str = Field(min_length=1, max_length=100)
    telephone: str = Field(min_length=1, max_length=40)
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: Genre
    notes: str | None = None


class ClientUpdate(BaseModel):
    nom: str | None = Field(default=None, min_length=1, max_length=100)
    prenom: str | None = Field(default=None, min_length=1, max_length=100)
    telephone: str | None = Field(default=None, min_length=1, max_length=40)
    email: EmailStr | None = None
    adresse: str | None = Field(default=None, max_length=255)
    genre: Genre | None = None
    notes: str | None = None


class ClientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nom: str
    prenom: str
    telephone: str
    email: str | None
    adresse: str | None
    genre: str
    notes: str | None
    created_at: datetime
    updated_at: datetime