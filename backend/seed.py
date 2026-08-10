from __future__ import annotations

import argparse

from app.db.seed_from_etl import seed_talents_from_etl_json
from app.db.session import SessionLocal


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed backend from ETL JSON file")
    parser.add_argument(
        "--json-path",
        type=str,
        default="../etl/output/experts_elite.json",
        help="Path to ETL JSON file",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    with SessionLocal() as db:
        stats = seed_talents_from_etl_json(db, args.json_path)
    print("Seed completed")
    print(f"Talents: {stats['talents']}")
    print(f"Domains created: {stats['domains']}")
    print(f"Universities created: {stats['universities']}")
