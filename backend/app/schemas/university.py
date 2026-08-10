from __future__ import annotations

from app.schemas.common import ORMBase


class UniversityRead(ORMBase):
    id: int
    name: str
    country_code: str | None = None
    city: str | None = None
    website: str | None = None
