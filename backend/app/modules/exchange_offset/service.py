from __future__ import annotations

import hashlib
import random
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.contract import Contract, Currency
from app.models.deduction import Deduction
from app.models.exchange_offset import ExchangeOffset
from app.models.exchange_rate import ExchangeRate
from app.modules.exchange_offset.schemas import (
    CurrencySummary,
    ExchangeOffsetOut,
    OffsetSummary,
)

CENT = Decimal("0.01")
RATE_PRECISION = Decimal("0.000001")

BASE_RATES: dict[Currency, Decimal] = {
    Currency.USD: Decimal("7.200000"),
    Currency.THB: Decimal("0.200000"),
}
FLUCTUATION = Decimal("0.015")


def _seed(currency: Currency, rate_date: date) -> int:
    key = f"{currency.value}:{rate_date.isoformat()}".encode("utf-8")
    return int(hashlib.sha256(key).hexdigest(), 16) % (2**32)


def simulate_rate(
    currency: Currency, rate_date: date, previous_rate: Decimal | None = None
) -> Decimal:
    rng = random.Random(_seed(currency, rate_date))
    delta = Decimal(str(rng.uniform(-0.015, 0.015)))
    base = previous_rate if previous_rate is not None else BASE_RATES[currency]
    return (base * (Decimal("1") + delta)).quantize(RATE_PRECISION)


def get_or_create_today_rate(db: Session, currency: Currency) -> Decimal:
    today = date.today()
    existing = db.scalars(
        select(ExchangeRate).where(
            ExchangeRate.currency == currency,
            ExchangeRate.rate_date == today,
        )
    ).first()
    if existing is not None:
        return existing.rate_to_cny

    prev = db.scalars(
        select(ExchangeRate)
        .where(
            ExchangeRate.currency == currency,
            ExchangeRate.rate_date < today,
        )
        .order_by(ExchangeRate.rate_date.desc())
    ).first()
    prev_rate = prev.rate_to_cny if prev is not None else None
    rate = simulate_rate(currency, today, prev_rate)

    db.add(ExchangeRate(currency=currency, rate_date=today, rate_to_cny=rate))
    db.flush()
    return rate


def list_rates(db: Session) -> list[ExchangeRate]:
    return list(
        db.scalars(
            select(ExchangeRate).order_by(
                ExchangeRate.rate_date.desc(), ExchangeRate.currency
            )
        ).all()
    )


def record_offset_for_deduction(
    db: Session, deduction: Deduction, contract: Contract
) -> ExchangeOffset:
    base_rate = contract.base_rate_to_cny
    current_rate = deduction.rate_to_cny
    gain_loss = (deduction.original_amount * (current_rate - base_rate)).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    offset = ExchangeOffset(
        contract_id=contract.id,
        deduction_id=deduction.id,
        base_rate=base_rate,
        current_rate=current_rate,
        original_amount=deduction.original_amount,
        gain_loss_cny=gain_loss,
    )
    db.add(offset)
    db.flush()
    return offset


def list_offsets(db: Session) -> list[ExchangeOffsetOut]:
    offsets = list(
        db.scalars(
            select(ExchangeOffset).order_by(ExchangeOffset.created_at.desc())
        ).all()
    )
    result: list[ExchangeOffsetOut] = []
    for o in offsets:
        contract = o.contract
        result.append(
            ExchangeOffsetOut(
                id=o.id,
                contract_id=o.contract_id,
                deduction_id=o.deduction_id,
                borrower_name=contract.borrower_name,
                currency=contract.currency,
                base_rate=o.base_rate,
                current_rate=o.current_rate,
                original_amount=o.original_amount,
                gain_loss_cny=o.gain_loss_cny,
                created_at=o.created_at,
            )
        )
    return result


def summary(db: Session) -> OffsetSummary:
    offsets = list(db.scalars(select(ExchangeOffset)).all())
    grouped: dict[Currency, dict] = {}
    total_gain = Decimal("0")

    for o in offsets:
        total_gain += o.gain_loss_cny
        currency = o.contract.currency
        bucket = grouped.setdefault(
            currency,
            {
                "contract_ids": set(),
                "total_original": Decimal("0"),
                "total_gain": Decimal("0"),
            },
        )
        bucket["contract_ids"].add(o.contract_id)
        bucket["total_original"] += o.original_amount
        bucket["total_gain"] += o.gain_loss_cny

    by_currency = [
        CurrencySummary(
            currency=currency,
            contract_count=len(bucket["contract_ids"]),
            total_original_amount=bucket["total_original"].quantize(CENT),
            total_gain_loss_cny=bucket["total_gain"].quantize(CENT),
        )
        for currency, bucket in grouped.items()
    ]

    return OffsetSummary(
        total_gain_loss_cny=total_gain.quantize(CENT),
        by_currency=by_currency,
    )
