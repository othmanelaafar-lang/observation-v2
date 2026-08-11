from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TalentDomain(Base):
    __tablename__ = "talent_domains"
    __table_args__ = (UniqueConstraint("talent_id", "domain_id", name="uq_talent_domain"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    talent_id: Mapped[int] = mapped_column(ForeignKey("talents.id", ondelete="CASCADE"), index=True)
    domain_id: Mapped[int] = mapped_column(ForeignKey("domains.id", ondelete="CASCADE"), index=True)


class TalentUniversity(Base):
    __tablename__ = "talent_universities"
    __table_args__ = (UniqueConstraint("talent_id", "university_id", name="uq_talent_university"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    talent_id: Mapped[int] = mapped_column(ForeignKey("talents.id", ondelete="CASCADE"), index=True)
    university_id: Mapped[int] = mapped_column(ForeignKey("universities.id", ondelete="CASCADE"), index=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)


class Talent(Base):
    __tablename__ = "talents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(180), index=True)
    name_ar: Mapped[str | None] = mapped_column(String(180), nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    country: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    role: Mapped[str | None] = mapped_column(String(180), nullable=True)
    organization: Mapped[str | None] = mapped_column(String(180), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(180), nullable=True)
    linkedin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    website_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    github_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    orcid_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    openalex_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scholar_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    skills_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    interests_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    publications: Mapped[int] = mapped_column(Integer, default=0)
    h_index: Mapped[int] = mapped_column(Integer, default=0)
    citations: Mapped[int] = mapped_column(Integer, default=0)
    score: Mapped[float] = mapped_column(Float, default=0)
    # Elite / Confirme / Emergent, assigned by the ETL from absolute thresholds.
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    ai_purity: Mapped[float] = mapped_column(Float, default=0)
    featured: Mapped[bool] = mapped_column(Boolean, default=False)

    source: Mapped[str | None] = mapped_column(String(40), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    domains = relationship("Domain", secondary="talent_domains", back_populates="talents")
    universities = relationship("University", secondary="talent_universities", back_populates="talents")
