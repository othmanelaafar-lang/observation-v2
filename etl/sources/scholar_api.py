from __future__ import annotations

import csv
import json
from pathlib import Path

from etl.config import settings
from etl.models import ExpertRecord


def _to_int(value: object, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _load_scholar_rows(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        print(f"[WARN] Scholar dataset not found: {path}")
        return []

    if path.suffix.lower() == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"[WARN] Invalid Scholar JSON: {exc}")
            return []
        if isinstance(payload, list):
            return [row for row in payload if isinstance(row, dict)]
        print("[WARN] Scholar JSON must be a list of objects.")
        return []

    if path.suffix.lower() == ".csv":
        rows: list[dict[str, object]] = []
        with path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                if isinstance(row, dict):
                    rows.append(dict(row))
        return rows

    print(f"[WARN] Unsupported Scholar dataset format: {path.suffix}")
    return []


def fetch_scholar_experts() -> list[ExpertRecord]:
    # Google Scholar blocks aggressive scraping and often requires captchas.
    # This connector consumes a curated intermediate dataset (JSON/CSV).
    if not settings.enable_scholar:
        return []

    dataset_path = Path(settings.scholar_dataset_path)
    rows = _load_scholar_rows(dataset_path)
    experts: list[ExpertRecord] = []

    for row in rows:
        full_name = str(row.get("full_name") or row.get("name") or "").strip()
        if not full_name:
            continue

        scholar_id = str(row.get("scholar_id") or row.get("id") or "").strip() or None
        affiliation = str(row.get("affiliation") or "").strip() or None
        orcid_id = str(row.get("orcid_id") or "").strip() or None
        openalex_id = str(row.get("openalex_id") or "").strip() or None
        citations_total = _to_int(row.get("citations_total"), 0)
        citations_5y = _to_int(row.get("citations_5y"), 0)
        i10_index = _to_int(row.get("i10_index"), 0)

        experts.append(
            ExpertRecord(
                full_name=full_name,
                primary_affiliation=affiliation,
                country_code=settings.target_country_code,
                openalex_id=openalex_id,
                orcid_id=orcid_id,
                scholar_id=scholar_id,
                source_rank=float(citations_total),
                sources={"scholar"},
                raw={
                    "scholar": {
                        "scholar_id": scholar_id,
                        "affiliation": affiliation,
                        "citations_total": citations_total,
                        "citations_5y": citations_5y,
                        "i10_index": i10_index,
                    }
                },
            )
        )

    print(f"[SCHOLAR] Loaded {len(experts)} records from {dataset_path}")
    return experts
