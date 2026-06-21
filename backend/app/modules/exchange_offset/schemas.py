from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import (
    BaseModel,
    ConfigDict,
    computed_field,
)

from app.models.contract import Currency

LOSS_THRESHOLD = Decimal("-0.10")


class ExchangeRateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    currency: Currency
    rate_date: date
    rate_to_cny: Decimal
    created_at: datetime


class TodayRateOut(BaseModel):
    currency: Currency
    rate_date: date
    rate_to_cny: Decimal


class ExchangeOffsetOut(BaseModel):
    id: int
    contract_id: int
    deduction_id: int
    borrower_name: str
    currency: Currency
    base_rate: Decimal
    current_rate: Decimal
    original_amount: Decimal
    gain_loss_cny: Decimal
    created_at: datetime

    @computed_field
    @property
    def severe_loss_flag(self) -> bool:
        expected_cny = self.original_amount * self.base_rate
        if expected_cny <= 0:
            return False
        ratio = self.gain_loss_cny / expected_cny
        return ratio <= LOSS_THRESHOLD


class CurrencySummary(BaseModel):
    currency: Currency
    contract_count: int
    total_original_amount: Decimal
    total_gain_loss_cny: Decimal


class OffsetSummary(BaseModel):
    total_gain_loss_cny: Decimal
    by_currency: list[CurrencySummary]
