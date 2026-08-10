from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.models.domain import Domain
from app.schemas.domain import DomainRead

router = APIRouter()


@router.get("/domains", response_model=list[DomainRead])
def list_domains(db: DBSession, limit: int = Query(200, ge=1, le=1000)) -> list[DomainRead]:
    items = db.scalars(select(Domain).order_by(Domain.name.asc()).limit(limit)).all()
    return [DomainRead.model_validate(item) for item in items]
