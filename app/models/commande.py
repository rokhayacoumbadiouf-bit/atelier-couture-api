from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


STATUTS = (
    "en_attente", "en_coupe", "en_couture", "essayage",
    "retouches", "terminee", "livree", "annulee",
)


class Commande(Base):
    __tablename__ = "commandes"
    __table_args__ = (
        CheckConstraint(
            "statut IN ('en_attente', 'en_coupe', 'en_couture', 'essayage', "
            "'retouches', 'terminee', 'livree', 'annulee')",
            name="ck_commandes_statut",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("clients.id"), index=True)
    mesure_id: Mapped[int | None] = mapped_column(ForeignKey("mesures.id"))
    statut: Mapped[str] = mapped_column(String(20), default="en_attente")
    date_commande: Mapped[date] = mapped_column(Date, default=date.today)
    date_livraison_prevue: Mapped[date | None] = mapped_column(Date)
    date_livraison_reelle: Mapped[date | None] = mapped_column(Date)
    remise: Mapped[int] = mapped_column(Integer, default=0)
    montant_total: Mapped[int] = mapped_column(Integer, default=0)
    montant_paye: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
    cree_par_id: Mapped[int] = mapped_column(ForeignKey("utilisateurs.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    lignes: Mapped[list["LigneCommande"]] = relationship(
        back_populates="commande",
        cascade="all, delete-orphan",
        order_by="LigneCommande.id",
    )

    @property
    def solde(self) -> int:
        return self.montant_total - self.montant_paye


class LigneCommande(Base):
    __tablename__ = "lignes_commande"
    __table_args__ = (
        CheckConstraint("quantite > 0", name="ck_lignes_quantite"),
        CheckConstraint("prix_unitaire > 0", name="ck_lignes_prix"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    commande_id: Mapped[int] = mapped_column(
        ForeignKey("commandes.id", ondelete="CASCADE"), index=True
    )
    type_vetement_id: Mapped[int] = mapped_column(ForeignKey("types_vetement.id"))
    description: Mapped[str | None] = mapped_column(String(255))
    quantite: Mapped[int] = mapped_column(Integer, default=1)
    prix_unitaire: Mapped[int] = mapped_column(Integer)

    commande: Mapped["Commande"] = relationship(back_populates="lignes")