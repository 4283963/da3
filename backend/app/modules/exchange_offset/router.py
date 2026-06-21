from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.contract import Currency
from app.modules.exchange_offset import schemas, service

router = APIRouter(prefix="/api", tags=["汇率冲抵模块"])


@router.get("/exchange-rates", response_model=list[schemas.ExchangeRateOut])
def list_rates(db: Session = Depends(get_db)) -> list[schemas.ExchangeRateOut]:
    return service.list_rates(db)


@router.get("/exchange-rates/today", response_model=schemas.TodayRateOut)
def get_today_rate(
    currency: Currency = Query(..., description="币种：USD 或 THB"),
    db: Session = Depends(get_db),
) -> schemas.TodayRateOut:
    rate = service.get_or_create_today_rate(db, currency)
    db.commit()
    return schemas.TodayRateOut(
        currency=currency, rate_date=date.today(), rate_to_cny=rate
    )


@router.get("/exchange-offsets", response_model=list[schemas.ExchangeOffsetOut])
def list_offsets(db: Session = Depends(get_db)) -> list[schemas.ExchangeOffsetOut]:
    return service.list_offsets(db)


@router.get("/exchange-offsets/summary", response_model=schemas.OffsetSummary)
def get_summary(db: Session = Depends(get_db)) -> schemas.OffsetSummary:
    return service.summary(db)
