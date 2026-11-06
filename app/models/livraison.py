from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Livraison(Base):
    __tablename__ = "livraisons"
    __table_args__ = (
        CheckConstraint("mode IN ('retrait_atelier', 'domicile')", name="ck_livraisons_mode"),
        CheckConstraint("statut IN ('planifiee', 'livree')", name="ck_livraisons_statut"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), unique=True
    )
    mode: Mapped[str] = mapped_column(String(20))
    adresse: Mapped[str | None] = mapped_column(String(255))
    livreur: Mapped[str | None] = mapped_column(String(100))
    date_prevue: Mapped[date] = mapped_column(Date)
    date_effective: Mapped[date | None] = mapped_column(Date)
    statut: Mapped[str] = mapped_column(String(20), default="planifiee")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())