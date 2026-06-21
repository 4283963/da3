from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contract import Contract, ContractStatus
from app.models.deduction import Deduction
from app.modules.contract_deduction.schemas import ContractCreate

CENT = Decimal("0.01")


def _initial_status(repayment_date: date) -> ContractStatus:
    today = date.today()
    if repayment_date < today:
        return ContractStatus.OVERDUE
    if repayment_date == today:
        return ContractStatus.PENDING_DEDUCTION
    return ContractStatus.ACTIVE


def _term_years(contract: Contract) -> Decimal:
    created = contract.created_at
    created_date = created.date() if hasattr(created, "date") else created
    days = (contract.repayment_date - created_date).days
    if days <= 0:
        days = 1
    return Decimal(days) / Decimal(365)


def create_contract(db: Session, payload: ContractCreate) -> Contract:
    from app.modules.exchange_offset.service import get_or_create_today_rate

    base_rate = get_or_create_today_rate(db, payload.currency)
    contract = Contract(
        borrower_name=payload.borrower_name,
        currency=payload.currency,
        principal_amount=payload.principal_amount,
        interest_rate=payload.interest_rate,
        repayment_date=payload.repayment_date,
        base_rate_to_cny=base_rate,
        status=_initial_status(payload.repayment_date),
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return contract


def list_contracts(db: Session) -> list[Contract]:
    return list(
        db.scalars(select(Contract).order_by(Contract.repayment_date)).all()
    )


def get_contract(db: Session, contract_id: int) -> Contract | None:
    return db.get(Contract, contract_id)


def list_deductions(db: Session) -> list[Deduction]:
    return list(db.scalars(select(Deduction).order_by(Deduction.deduction_date.desc())).all())


def get_deduction(db: Session, deduction_id: int) -> Deduction | None:
    return db.get(Deduction, deduction_id)


def auto_process_due_contracts(db: Session) -> list[Contract]:
    from app.modules.exchange_offset.service import (
        get_or_create_today_rate,
        record_offset_for_deduction,
    )

    today = date.today()
    stmt = select(Contract).where(
        Contract.repayment_date <= today,
        Contract.status.in_(
            [
                ContractStatus.ACTIVE,
                ContractStatus.PENDING_DEDUCTION,
                ContractStatus.OVERDUE,
            ]
        ),
    )
    contracts = list(db.scalars(stmt).all())
    processed: list[Contract] = []

    for contract in contracts:
        term_years = _term_years(contract)
        interest = (
            (contract.principal_amount * contract.interest_rate * term_years)
            .quantize(CENT, rounding=ROUND_HALF_UP)
        )
        original_amount = (
            (contract.principal_amount + interest).quantize(CENT, rounding=ROUND_HALF_UP)
        )
        current_rate = get_or_create_today_rate(db, contract.currency)
        amount_in_cny = (original_amount * current_rate).quantize(
            CENT, rounding=ROUND_HALF_UP
        )

        deduction = Deduction(
            contract_id=contract.id,
            deduction_date=today,
            principal_portion=contract.principal_amount,
            interest_portion=interest,
            original_amount=original_amount,
            rate_to_cny=current_rate,
            amount_in_cny=amount_in_cny,
        )
        db.add(deduction)
        db.flush()

        record_offset_for_deduction(db, deduction, contract)

        contract.status = ContractStatus.DEDUCTED
        processed.append(contract)

    db.commit()
    for contract in processed:
        db.refresh(contract)
    return processed
