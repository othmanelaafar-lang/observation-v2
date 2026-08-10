from __future__ import annotations

from fastapi import APIRouter, Query
from sqlalchemy import desc, func, select

from app.api.deps import DBSession
from app.models.domain import Domain
from app.models.talent import Talent, TalentDomain
from app.schemas.talent import CountryStat, DomainStat, TalentStatsResponse

router = APIRouter()


@router.get("/stats", response_model=TalentStatsResponse)
def get_stats(db: DBSession, top: int = Query(10, ge=1, le=50)) -> TalentStatsResponse:
    total_talents = db.scalar(select(func.count()).select_from(Talent)) or 0
    featured_count = db.scalar(select(func.count()).select_from(Talent).where(Talent.featured.is_(True))) or 0

    total_countries = db.scalar(select(func.count(func.distinct(Talent.country))).where(Talent.country.is_not(None))) or 0
    total_domains = db.scalar(select(func.count()).select_from(Domain)) or 0

    domain_rows = db.execute(
        select(Domain.name, func.count(TalentDomain.id).label("count"))
        .join(TalentDomain, TalentDomain.domain_id == Domain.id)
        .group_by(Domain.id, Domain.name)
        .order_by(desc("count"), Domain.name)
        .limit(top)
    ).all()

    country_rows = db.execute(
        select(Talent.country, func.count(Talent.id).label("count"))
        .where(Talent.country.is_not(None))
        .group_by(Talent.country)
        .order_by(desc("count"), Talent.country)
        .limit(top)
    ).all()

    return TalentStatsResponse(
        total_talents=total_talents,
        total_countries=total_countries,
        total_domains=total_domains,
        featured_count=featured_count,
        top_domains=[DomainStat(name=name, count=count) for name, count in domain_rows],
        top_countries=[CountryStat(name=name, count=count) for name, count in country_rows],
    )
