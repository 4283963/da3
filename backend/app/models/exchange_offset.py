from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ExchangeOffset(Base):
    __tablename__ = "exchange_offsets"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    deduction_id: Mapped[int] = mapped_column(ForeignKey("deductions.id"))
    base_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    current_rate: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    gain_loss_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    contract: Mapped["Contract"] = relationship(back_populates="offsets")
    deduction: Mapped["Deduction"] = relationship(back_populates="offset")
