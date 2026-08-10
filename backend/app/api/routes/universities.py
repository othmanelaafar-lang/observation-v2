from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import select

from app.api.deps import DBSession
from app.models.university import University
from app.schemas.university import UniversityRead

router = APIRouter()


@router.get("/universities", response_model=list[UniversityRead])
def list_universities(
    db: DBSession,
    country_code: str | None = Query(default=None),
    limit: int = Query(200, ge=1, le=1000),
) -> list[UniversityRead]:
    stmt = select(University)
    if country_code:
        stmt = stmt.where(University.country_code.ilike(country_code))

    items = db.scalars(stmt.order_by(University.name.asc()).limit(limit)).all()
    return [UniversityRead.model_validate(item) for item in items]
