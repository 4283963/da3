from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import app.models  # noqa: F401  register all models with Base.metadata
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.modules.contract_deduction.router import router as contract_router
from app.modules.exchange_offset.router import router as offset_router


def _on_startup() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        from app.modules.contract_deduction.service import auto_process_due_contracts

        auto_process_due_contracts(db)
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _on_startup()
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(contract_router)
app.include_router(offset_router)


@app.get("/", tags=["系统"])
def root() -> dict:
    return {"app": settings.app_name, "docs": "/docs"}
