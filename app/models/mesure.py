from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Mesure(Base):
    __tablename__ = "mesures"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(
        ForeignKey("clients.id", ondelete="CASCADE"), index=True
    )
    date_prise: Mapped[date] = mapped_column(Date)
    prise_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    notes: Mapped[str | None] = mapped_column(Text)

    taille_cm: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_cou: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    carrure_dos: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_epaule: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_poitrine: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_taille: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_bassin: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_manche: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_bras: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_poignet: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_dos: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_haut: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_pantalon: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_cuisse: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    tour_genou: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    bas_pantalon: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    entrejambe: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))
    longueur_robe: Mapped[float | None] = mapped_column(Numeric(5, 1, asdecimal=False))