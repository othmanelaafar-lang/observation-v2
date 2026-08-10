from __future__ import annotations

from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, func, select, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.seed_from_etl import seed_talents_from_etl_json
from app.models.talent import Talent


def _sqlite_path() -> str:
    return str((Path(__file__).resolve().parents[3] / "backend" / "observatoire.db").resolve())


def build_engine(database_url: str | None = None):
    configured_url = database_url or settings.database_url

    if configured_url.startswith("sqlite"):
        engine = create_engine(configured_url, future=True, connect_args={"check_same_thread": False})
        return engine

    engine = create_engine(configured_url, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return engine
    except OperationalError:
        print("[WARN] PostgreSQL unavailable. Falling back to SQLite for local data access.")

    fallback_url = f"sqlite:///{_sqlite_path()}"
    return create_engine(fallback_url, future=True, connect_args={"check_same_thread": False})


def initialize_database(engine) -> None:
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        count = session.scalar(select(func.count()).select_from(Talent)) or 0
        if count == 0:
            etl_path = Path(__file__).resolve().parents[3] / "etl" / "output" / "experts.json"
            if etl_path.exists():
                seed_talents_from_etl_json(session, str(etl_path))
            else:
                print(f"[WARN] ETL JSON not found: {etl_path}")


engine = build_engine()
initialize_database(engine)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
