from __future__ import annotations

import argparse
import json
from pathlib import Path

from etl.config import settings
from etl.pipeline import records_to_json, run_pipeline, run_target_domain_pipeline


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Moroccan experts ETL")
    parser.add_argument(
        "--json-out",
        type=str,
        default="",
        help="Optional output path for JSON snapshot (example: etl/output/experts.json)",
    )
    parser.add_argument(
        "--no-db",
        action="store_true",
        help="Run extraction/transforms only, without loading PostgreSQL",
    )
    parser.add_argument(
        "--target-domains-only",
        action="store_true",
        help="Scrape and filter only elite Moroccan worldwide experts in target subdomains",
    )
    parser.add_argument(
        "--rejections-csv",
        type=str,
        default="",
        help="Optional output path for rejected profiles CSV with exclusion reasons",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    runner = run_target_domain_pipeline if args.target_domains_only else run_pipeline
    rejected_csv_path = args.rejections_csv or settings.rejected_profiles_csv_path or None
    stats, records = runner(load_db=not args.no_db, rejected_csv_path=rejected_csv_path)

    if args.json_out:
        output_path = Path(args.json_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        payload = records_to_json(records)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"JSON saved to: {output_path}")

    print("ETL completed")
    print(f"Extracted: {stats['extracted']}")
    print(f"Deduplicated: {stats['deduplicated']}")
    print(f"Filtered (cross-source + IA + scoring tiers): {stats['filtered']}")
    print(f"Rejected: {stats['rejected']}")
    print(f"Loaded: {stats['loaded']}")
