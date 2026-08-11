from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import ORMBase
from app.schemas.domain import DomainRead
from app.schemas.university import UniversityRead


class TalentRead(ORMBase):
    id: int
    full_name: str
    name_ar: str | None = None
    photo_url: str | None = None
    country: str | None = None
    city: str | None = None
    role: str | None = None
    organization: str | None = None
    bio: str | None = None
    email: str | None = None
    linkedin: str | None = None
    website_url: str | None = None
    github_url: str | None = None
    orcid_url: str | None = None
    openalex_url: str | None = None
    scholar_url: str | None = None
    skills_text: str | None = None
    interests_text: str | None = None
    publications: int
    h_index: int
    citations: int
    score: float
    tier: str | None = None
    ai_purity: float = 0
    featured: bool
    source: str | None = None
    domains: list[DomainRead] = []
    universities: list[UniversityRead] = []


class TalentListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[TalentRead]


class TalentLeaderboardEntry(BaseModel):
    rank: int
    talent: TalentRead


class TalentLeaderboardResponse(BaseModel):
    focus_rank: int
    focus: TalentLeaderboardEntry
    neighbors: list[TalentLeaderboardEntry]


class SearchResponse(BaseModel):
    total: int
    query: str
    items: list[TalentRead]


class DomainStat(BaseModel):
    name: str
    count: int


class CountryStat(BaseModel):
    name: str
    count: int


class TalentStatsResponse(BaseModel):
    total_talents: int
    total_countries: int
    total_domains: int
    top_domains: list[DomainStat]
    top_countries: list[CountryStat]
    featured_count: int
