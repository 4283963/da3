from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Deduction(Base):
    __tablename__ = "deductions"

    id: Mapped[int] = mapped_column(primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"))
    deduction_date: Mapped[date] = mapped_column(Date, default=date.today)
    principal_portion: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    interest_portion: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    original_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    rate_to_cny: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    amount_in_cny: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    contract: Mapped["Contract"] = relationship(back_populates="deductions")
    offset: Mapped["ExchangeOffset"] = relationship(
        back_populates="deduction", uselist=False, cascade="all, delete-orphan"
    )
