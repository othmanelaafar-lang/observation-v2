from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession
from app.models.talent import Talent
from app.schemas.talent import SearchResponse, TalentRead

router = APIRouter()


@router.get("/search", response_model=SearchResponse)
def search_talents(
    db: DBSession,
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=100),
) -> SearchResponse:
    pattern = f"%{q}%"
    stmt = (
        select(Talent)
        .options(selectinload(Talent.domains), selectinload(Talent.universities))
        .where(
            or_(
                Talent.full_name.ilike(pattern),
                Talent.bio.ilike(pattern),
                Talent.organization.ilike(pattern),
                Talent.country.ilike(pattern),
                Talent.city.ilike(pattern),
                Talent.skills_text.ilike(pattern),
                Talent.interests_text.ilike(pattern),
            )
        )
        .order_by(Talent.score.desc(), Talent.publications.desc(), Talent.id.asc())
        .limit(limit)
    )

    items = db.scalars(stmt).all()
    return SearchResponse(total=len(items), query=q, items=[TalentRead.model_validate(item) for item in items])
