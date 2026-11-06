from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Paiement(Base):
    __tablename__ = "paiements"
    __table_args__ = (
        CheckConstraint("montant > 0", name="ck_paiements_montant"),
        CheckConstraint(
            "mode IN ('especes', 'wave', 'orange_money', 'virement', 'cheque')",
            name="ck_paiements_mode",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    montant: Mapped[int] = mapped_column(Integer)
    mode: Mapped[str] = mapped_column(String(20))
    reference: Mapped[str | None] = mapped_column(String(100))
    date_paiement: Mapped[date] = mapped_column(Date)
    enregistre_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())