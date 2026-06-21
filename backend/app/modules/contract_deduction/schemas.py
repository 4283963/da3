from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
)

from app.models.contract import ContractStatus, Currency

CENT = Decimal("0.01")
LOSS_THRESHOLD = Decimal("-0.10")


class ContractCreate(BaseModel):
    borrower_name: str = Field(min_length=1, max_length=128)
    currency: Currency
    principal_amount: Decimal = Field(gt=0)
    interest_rate: Decimal = Field(ge=0, le=1)
    repayment_date: date


class DeductionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    deduction_date: date
    principal_portion: Decimal
    interest_portion: Decimal
    original_amount: Decimal
    rate_to_cny: Decimal
    amount_in_cny: Decimal
    created_at: datetime


class ContractOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    borrower_name: str
    currency: Currency
    principal_amount: Decimal
    interest_rate: Decimal
    repayment_date: date
    base_rate_to_cny: Decimal
    status: ContractStatus
    created_at: datetime
    deductions: list[DeductionOut] = []

    @computed_field
    @property
    def expected_cny(self) -> Optional[Decimal]:
        if not self.deductions:
            return None
        last = self.deductions[-1]
        return (last.original_amount * self.base_rate_to_cny).quantize(
            CENT, rounding=ROUND_HALF_UP
        )

    @computed_field
    @property
    def actual_cny(self) -> Optional[Decimal]:
        if not self.deductions:
            return None
        return self.deductions[-1].amount_in_cny

    @computed_field
    @property
    def severe_loss_flag(self) -> bool:
        expected = self.expected_cny
        actual = self.actual_cny
        if expected is None or actual is None or expected <= 0:
            return False
        ratio = (actual - expected) / expected
        return ratio <= LOSS_THRESHOLD


class AutoRunResult(BaseModel):
    processed: int
    contracts: list[ContractOut]
