from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession
from app.models.domain import Domain
from app.models.talent import Talent
from app.schemas.talent import TalentListResponse, TalentRead

router = APIRouter()


@router.get("/talents", response_model=TalentListResponse)
def list_talents(
    db: DBSession,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    domain: str | None = Query(default=None),
    country: str | None = Query(default=None),
    featured: bool | None = Query(default=None),
) -> TalentListResponse:
    id_stmt = select(Talent.id.label("id"), Talent.score.label("score"), Talent.publications.label("publications"))

    if country:
        id_stmt = id_stmt.where(Talent.country.ilike(f"%{country}%"))

    if featured is not None:
        id_stmt = id_stmt.where(Talent.featured == featured)

    if domain:
        id_stmt = id_stmt.join(Talent.domains).where(func.lower(Domain.name) == domain.lower())

    filtered_subquery = id_stmt.group_by(Talent.id, Talent.score, Talent.publications).subquery()

    total = db.scalar(select(func.count()).select_from(filtered_subquery)) or 0

    ids_page = db.scalars(
        select(filtered_subquery.c.id)
        .order_by(
            filtered_subquery.c.score.desc(),
            filtered_subquery.c.publications.desc(),
            filtered_subquery.c.id.asc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    if not ids_page:
        return TalentListResponse(total=total, page=page, page_size=page_size, items=[])

    stmt = (
        select(Talent)
        .where(Talent.id.in_(ids_page))
        .options(selectinload(Talent.domains), selectinload(Talent.universities))
        .order_by(Talent.score.desc(), Talent.publications.desc(), Talent.id.asc())
    )
    items = db.scalars(stmt).all()

    return TalentListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[TalentRead.model_validate(item) for item in items],
    )


@router.get("/talents/{talent_id}", response_model=TalentRead)
def get_talent(db: DBSession, talent_id: int) -> TalentRead:
    stmt = (
        select(Talent)
        .where(Talent.id == talent_id)
        .options(selectinload(Talent.domains), selectinload(Talent.universities))
    )
    talent = db.scalar(stmt)
    if not talent:
        raise HTTPException(status_code=404, detail="Talent not found")
    return TalentRead.model_validate(talent)
