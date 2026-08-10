from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import DBSession
from app.models.talent import Talent
from app.schemas.talent import TalentLeaderboardEntry, TalentLeaderboardResponse, TalentRead

router = APIRouter()


@router.get("/leaderboards/talent/{i}", response_model=TalentLeaderboardResponse)
def leaderboard_talent_rank(
    db: DBSession,
    i: int,
    window: int = Query(2, ge=0, le=20),
) -> TalentLeaderboardResponse:
    ordered = db.scalars(
        select(Talent)
        .options(selectinload(Talent.domains), selectinload(Talent.universities))
        .order_by(Talent.score.desc(), Talent.publications.desc(), Talent.id.asc())
    ).all()

    if not ordered:
        raise HTTPException(status_code=404, detail="No talents found")

    if i < 1 or i > len(ordered):
        raise HTTPException(status_code=404, detail=f"Rank {i} is out of range (1..{len(ordered)})")

    idx = i - 1
    start = max(0, idx - window)
    end = min(len(ordered), idx + window + 1)

    focus_talent = ordered[idx]
    focus = TalentLeaderboardEntry(rank=i, talent=TalentRead.model_validate(focus_talent))

    neighbors: list[TalentLeaderboardEntry] = []
    for rank, talent in enumerate(ordered[start:end], start=start + 1):
        if rank == i:
            continue
        neighbors.append(TalentLeaderboardEntry(rank=rank, talent=TalentRead.model_validate(talent)))

    return TalentLeaderboardResponse(focus_rank=i, focus=focus, neighbors=neighbors)
