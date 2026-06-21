from __future__ import annotations

import hashlib
import logging
import random
import time
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
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

log = logging.getLogger(__name__)


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


def _inverse_rate(cny_per_x: Decimal) -> Decimal:
    if cny_per_x <= 0:
        raise ValueError("非正汇率不可用")
    return (Decimal("1") / cny_per_x).quantize(RATE_PRECISION)


def fetch_live_rates_via_http() -> dict[Currency, Decimal] | None:
    """
    调真实的国际汇率接口。返回 {币种: 1 外币兑换多少 CNY}。
    网络 / 超时 / HTTP 错一律捕获并返回 None，让上层 fallback 到本地模拟。
    """
    try:
        import requests
    except Exception as exc:  # pragma: no cover - 极端依赖缺失情况
        log.warning("requests 库不可用，跳过在线汇率: %s", exc)
        return None

    timeout = settings.exchange_rate_timeout
    max_retries = max(1, settings.exchange_rate_max_retries)
    backoff = settings.exchange_rate_backoff
    last_error: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                settings.exchange_rate_api_url,
                timeout=timeout,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            payload = response.json()
            rates = payload.get("rates") or {}
            base = (payload.get("base") or "CNY").upper()

            if base == "CNY":
                raw_usd = rates.get(Currency.USD.value)
                raw_thb = rates.get(Currency.THB.value)
                if raw_usd is None or raw_thb is None:
                    raise ValueError("返回的汇率缺少 USD/THB 字段")
                return {
                    Currency.USD: _inverse_rate(Decimal(str(raw_usd))),
                    Currency.THB: _inverse_rate(Decimal(str(raw_thb))),
                }

            if base == "USD":
                raw_cny = rates.get("CNY")
                raw_thb = rates.get(Currency.THB.value)
                if raw_cny is None or raw_thb is None:
                    raise ValueError("返回的汇率缺少 CNY/THB 字段")
                usd_cny = Decimal(str(raw_cny)).quantize(RATE_PRECISION)
                thb_cny = (usd_cny / Decimal(str(raw_thb))).quantize(RATE_PRECISION)
                return {Currency.USD: usd_cny, Currency.THB: thb_cny}

            raise ValueError(f"不支持的基础币种: {base}")

        except Exception as exc:
            last_error = exc
            if attempt < max_retries:
                sleep_for = backoff * (2 ** (attempt - 1))
                log.warning(
                    "汇率接口第 %s/%s 次调用失败: %s，%.2fs 后重试",
                    attempt,
                    max_retries,
                    exc,
                    sleep_for,
                )
                time.sleep(sleep_for)

    log.error(
        "汇率接口连续 %s 次调用失败，将回退到本地模拟。最后错误: %s",
        max_retries,
        last_error,
    )
    return None


def _today_rates_cache(db: Session, today: date) -> dict[Currency, Decimal]:
    """
    1) 先查数据库里今天已有的汇率；
    2) 缺失的币种先尝试在线接口一次性批量拉取；
    3) 在线失败 / 仍缺，就用 simulate_rate 本地兜底；
    4) 所有新生成的汇率写回 DB（唯一约束防重），供同一请求内其它合同复用，避免重复调接口。
    """
    rows = db.scalars(
        select(ExchangeRate).where(
            ExchangeRate.rate_date == today,
            ExchangeRate.currency.in_([Currency.USD, Currency.THB]),
        )
    ).all()
    result: dict[Currency, Decimal] = {r.currency: r.rate_to_cny for r in rows}

    missing = [c for c in (Currency.USD, Currency.THB) if c not in result]
    if missing:
        live = fetch_live_rates_via_http()
        if live is not None:
            for cur in missing:
                if cur in live:
                    result[cur] = live[cur]

    still_missing = [c for c in (Currency.USD, Currency.THB) if c not in result]
    if still_missing:
        for cur in still_missing:
            prev = db.scalars(
                select(ExchangeRate)
                .where(
                    ExchangeRate.currency == cur,
                    ExchangeRate.rate_date < today,
                )
                .order_by(ExchangeRate.rate_date.desc())
            ).first()
            prev_rate = prev.rate_to_cny if prev is not None else None
            result[cur] = simulate_rate(cur, today, prev_rate)

    for cur in (Currency.USD, Currency.THB):
        if cur not in result:
            continue
        existing = db.scalars(
            select(ExchangeRate).where(
                ExchangeRate.currency == cur,
                ExchangeRate.rate_date == today,
            )
        ).first()
        if existing is None:
            db.add(
                ExchangeRate(
                    currency=cur, rate_date=today, rate_to_cny=result[cur]
                )
            )
    db.flush()
    return result


def get_or_create_today_rate(db: Session, currency: Currency) -> Decimal:
    today = date.today()
    cache = _today_rates_cache(db, today)
    return cache[currency]


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
