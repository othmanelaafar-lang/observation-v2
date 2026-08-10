from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExpertRecord:
    full_name: str
    primary_affiliation: str | None = None
    country_code: str | None = None
    domains: list[str] = field(default_factory=list)
    github_login: str | None = None
    github_url: str | None = None
    openalex_id: str | None = None
    orcid_id: str | None = None
    scholar_id: str | None = None
    source_rank: float = 0.0
    score: float = 0.0
    sources: set[str] = field(default_factory=set)
    raw: dict[str, Any] = field(default_factory=dict)

    def merge(self, other: "ExpertRecord") -> None:
        if not self.full_name and other.full_name:
            self.full_name = other.full_name
        if not self.primary_affiliation and other.primary_affiliation:
            self.primary_affiliation = other.primary_affiliation
        if not self.country_code and other.country_code:
            self.country_code = other.country_code

        self.domains = sorted(set(self.domains + other.domains))
        self.github_login = self.github_login or other.github_login
        self.github_url = self.github_url or other.github_url
        self.openalex_id = self.openalex_id or other.openalex_id
        self.orcid_id = self.orcid_id or other.orcid_id
        self.scholar_id = self.scholar_id or other.scholar_id

        self.source_rank = max(self.source_rank, other.source_rank)
        self.sources.update(other.sources)
        self.raw.update(other.raw)
