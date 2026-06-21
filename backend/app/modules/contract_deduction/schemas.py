from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.contract import ContractStatus, Currency


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


class AutoRunResult(BaseModel):
    processed: int
    contracts: list[ContractOut]
