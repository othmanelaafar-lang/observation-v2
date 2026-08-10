from __future__ import annotations

from app.schemas.common import ORMBase


class DomainRead(ORMBase):
    id: int
    name: str
    slug: str
    description: str | None = None
