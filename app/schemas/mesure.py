from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


CHAMPS_MESURES = [
    "taille_cm", "tour_cou", "carrure_dos", "longueur_epaule", "tour_poitrine",
    "tour_taille", "tour_bassin", "longueur_manche", "tour_bras", "tour_poignet",
    "longueur_dos", "longueur_haut", "longueur_pantalon", "tour_cuisse", "tour_genou",
    "bas_pantalon", "entrejambe", "longueur_robe",
]

Mesure_cm = Field(default=None, gt=0, le=300)


class MesureCreate(BaseModel):
    date_prise: date | None = None
    notes: str | None = None

    taille_cm: float | None = Mesure_cm
    tour_cou: float | None = Mesure_cm
    carrure_dos: float | None = Mesure_cm
    longueur_epaule: float | None = Mesure_cm
    tour_poitrine: float | None = Mesure_cm
    tour_taille: float | None = Mesure_cm
    tour_bassin: float | None = Mesure_cm
    longueur_manche: float | None = Mesure_cm
    tour_bras: float | None = Mesure_cm
    tour_poignet: float | None = Mesure_cm
    longueur_dos: float | None = Mesure_cm
    longueur_haut: float | None = Mesure_cm
    longueur_pantalon: float | None = Mesure_cm
    tour_cuisse: float | None = Mesure_cm
    tour_genou: float | None = Mesure_cm
    bas_pantalon: float | None = Mesure_cm
    entrejambe: float | None = Mesure_cm
    longueur_robe: float | None = Mesure_cm


class MesureUpdate(MesureCreate):
    """Correction : tous les champs sont facultatifs, une mesure peut être remise à vide."""


class MesureRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    client_id: int
    date_prise: date
    prise_par_id: int
    notes: str | None
    taille_cm: float | None
    tour_cou: float | None
    carrure_dos: float | None
    longueur_epaule: float | None
    tour_poitrine: float | None
    tour_taille: float | None
    tour_bassin: float | None
    longueur_manche: float | None
    tour_bras: float | None
    tour_poignet: float | None
    longueur_dos: float | None
    longueur_haut: float | None
    longueur_pantalon: float | None
    tour_cuisse: float | None
    tour_genou: float | None
    bas_pantalon: float | None
    entrejambe: float | None
    longueur_robe: float | None