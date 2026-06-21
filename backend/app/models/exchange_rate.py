from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SAEnum, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.contract import Currency


class ExchangeRate(Base):
    __tablename__ = "exchange_rates"
    __table_args__ = (UniqueConstraint("currency", "rate_date", name="uq_currency_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[Currency] = mapped_column(SAEnum(Currency))
    rate_date: Mapped[date] = mapped_column(Date)
    rate_to_cny: Mapped[Decimal] = mapped_column(Numeric(12, 6))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now()
    )
