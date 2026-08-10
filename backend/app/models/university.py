from __future__ import annotations

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class University(Base):
    __tablename__ = "universities"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(180), unique=True, index=True)
    country_code: Mapped[str | None] = mapped_column(String(8), nullable=True, index=True)
    city: Mapped[str | None] = mapped_column(String(120), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    talents = relationship("Talent", secondary="talent_universities", back_populates="universities")
