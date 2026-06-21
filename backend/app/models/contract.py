from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SAEnum, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Currency(str, Enum):
    USD = "USD"
    THB = "THB"


class ContractStatus(str, Enum):
    ACTIVE = "active"
    PENDING_DEDUCTION = "pending_deduction"
    DEDUCTED = "deducted"
    OVERDUE = "overdue"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    borrower_name: Mapped[str] = mapped_column(String(128))
    currency: Mapped[Currency] = mapped_column(SAEnum(Currency))
    principal_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    interest_rate: Mapped[Decimal] = mapped_column(Numeric(6, 4))
    repayment_date: Mapped[date] = mapped_column(Date)
    base_rate_to_cny: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    status: Mapped[ContractStatus] = mapped_column(
        SAEnum(ContractStatus), default=ContractStatus.ACTIVE
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )

    deductions: Mapped[list["Deduction"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )
    offsets: Mapped[list["ExchangeOffset"]] = relationship(
        back_populates="contract", cascade="all, delete-orphan"
    )
