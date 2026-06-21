from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.modules.contract_deduction import schemas, service

router = APIRouter(prefix="/api", tags=["合同扣款模块"])


@router.post(
    "/contracts",
    response_model=schemas.ContractOut,
    status_code=status.HTTP_201_CREATED,
)
def create_contract(
    payload: schemas.ContractCreate, db: Session = Depends(get_db)
) -> schemas.ContractOut:
    return service.create_contract(db, payload)


@router.get("/contracts", response_model=list[schemas.ContractOut])
def list_contracts(db: Session = Depends(get_db)) -> list[schemas.ContractOut]:
    return service.list_contracts(db)


@router.get("/contracts/{contract_id}", response_model=schemas.ContractOut)
def get_contract(
    contract_id: int, db: Session = Depends(get_db)
) -> schemas.ContractOut:
    contract = service.get_contract(db, contract_id)
    if contract is None:
        raise HTTPException(status_code=404, detail="合同不存在")
    return contract


@router.post(
    "/contract-deduction/auto-run", response_model=schemas.AutoRunResult
)
def auto_run(db: Session = Depends(get_db)) -> schemas.AutoRunResult:
    contracts = service.auto_process_due_contracts(db)
    return schemas.AutoRunResult(processed=len(contracts), contracts=contracts)


@router.get("/deductions", response_model=list[schemas.DeductionOut])
def list_deductions(db: Session = Depends(get_db)) -> list[schemas.DeductionOut]:
    return service.list_deductions(db)


@router.get("/deductions/{deduction_id}", response_model=schemas.DeductionOut)
def get_deduction(
    deduction_id: int, db: Session = Depends(get_db)
) -> schemas.DeductionOut:
    deduction = service.get_deduction(db, deduction_id)
    if deduction is None:
        raise HTTPException(status_code=404, detail="扣款记录不存在")
    return deduction
