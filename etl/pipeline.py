from __future__ import annotations

import json
import csv
import re
import unicodedata
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from etl.config import settings
from etl.filters import (
    apply_business_filters,
    apply_business_filters_with_rejections,
    apply_target_domain_business_filters,
    apply_target_domain_business_filters_with_rejections,
    compute_h_index_normalized,
    openalex_recent_citations_5y,
)
from etl.models import ExpertRecord
from etl.sources.github_api import fetch_github_experts
from etl.sources.openalex_api import fetch_openalex_experts, fetch_openalex_target_domain_experts
from etl.sources.orcid_api import fetch_orcid_experts
from etl.sources.scholar_api import fetch_scholar_experts
from etl.utils import dedupe_key


def _normalize_name(value: str | None) -> str:
    text = (value or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", text)
    no_accents = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    collapsed = re.sub(r"\s+", " ", no_accents)
    cleaned = re.sub(r"[^a-z0-9 ]", "", collapsed)
    return cleaned.strip()


def _email_domain(record: ExpertRecord) -> str | None:
    raw = record.raw if isinstance(record.raw, dict) else {}
    github = raw.get("github") if isinstance(raw.get("github"), dict) else {}
    for key in ("email", "public_email"):
        value = github.get(key)
        if isinstance(value, str) and "@" in value:
            return value.rsplit("@", 1)[-1].strip().lower() or None
    return None


def _institution_tokens(record: ExpertRecord) -> set[str]:
    tokens: set[str] = set()
    if record.primary_affiliation:
        tokens.add(_normalize_name(record.primary_affiliation))

    raw = record.raw if isinstance(record.raw, dict) else {}
    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        name = institution.get("display_name")
        if isinstance(name, str) and name.strip():
            tokens.add(_normalize_name(name))

    return {token for token in tokens if token}


def match_score(profile_a: ExpertRecord, profile_b: ExpertRecord) -> int:
    score = 0

    if profile_a.orcid_id and profile_b.orcid_id and profile_a.orcid_id == profile_b.orcid_id:
        score += 3

    domain_a = _email_domain(profile_a)
    domain_b = _email_domain(profile_b)
    if domain_a and domain_b and domain_a == domain_b:
        score += 2

    if _normalize_name(profile_a.full_name) and _normalize_name(profile_a.full_name) == _normalize_name(profile_b.full_name):
        score += 1

    if _institution_tokens(profile_a).intersection(_institution_tokens(profile_b)):
        score += 1

    return score


def _build_match_groups(records: list[ExpertRecord]) -> list[list[int]]:
    n = len(records)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra = find(a)
        rb = find(b)
        if ra != rb:
            parent[rb] = ra

    for i in range(n):
        for j in range(i + 1, n):
            if match_score(records[i], records[j]) >= settings.dedupe_match_threshold:
                union(i, j)

    grouped: dict[int, list[int]] = defaultdict(list)
    for idx in range(n):
        grouped[find(idx)].append(idx)
    return list(grouped.values())


def _safe_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_minmax(values: list[float]) -> list[float]:
    if not values:
        return []
    low = min(values)
    high = max(values)
    if high <= low:
        return [0.0 for _ in values]
    return [(value - low) / (high - low) for value in values]


def _contains_whitelisted_institution(record: ExpertRecord) -> bool:
    haystacks = [record.primary_affiliation or ""]
    raw = record.raw if isinstance(record.raw, dict) else {}
    scholar = raw.get("scholar") if isinstance(raw.get("scholar"), dict) else {}
    haystacks.append(str(scholar.get("affiliation") or ""))

    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        haystacks.append(str(institution.get("display_name") or ""))

    merged = " ".join(haystacks).lower()
    return any(token in merged for token in settings.moroccan_university_whitelist)


def _institution_recognition_score(record: ExpertRecord) -> float:
    if _contains_whitelisted_institution(record):
        return 1.0
    if (record.primary_affiliation or "").strip():
        return 0.5
    return 0.0


def collect_all_sources() -> list[ExpertRecord]:
    records: list[ExpertRecord] = []
    source_fetchers = [
        ("github", fetch_github_experts),
        ("openalex", fetch_openalex_experts),
        ("orcid", fetch_orcid_experts),
        ("scholar", fetch_scholar_experts),
    ]

    for source_name, fetcher in source_fetchers:
        try:
            records.extend(fetcher())
        except Exception as exc:
            print(f"[WARN] Source '{source_name}' failed: {exc}")

    return records


def collect_target_domain_sources() -> list[ExpertRecord]:
    records: list[ExpertRecord] = []
    source_fetchers = [
        ("github", fetch_github_experts),
        ("openalex-target-domains", fetch_openalex_target_domain_experts),
        ("orcid", fetch_orcid_experts),
        ("scholar", fetch_scholar_experts),
    ]

    for source_name, fetcher in source_fetchers:
        try:
            records.extend(fetcher())
        except Exception as exc:
            print(f"[WARN] Source '{source_name}' failed: {exc}")

    return records


def deduplicate(records: list[ExpertRecord]) -> list[ExpertRecord]:
    if not records:
        return []

    # Stage 1: fast identity buckets
    grouped: dict[str, list[ExpertRecord]] = defaultdict(list)
    for rec in records:
        if rec.orcid_id:
            key = f"orcid:{rec.orcid_id}"
        elif rec.openalex_id:
            key = f"openalex:{rec.openalex_id}"
        elif rec.github_login:
            key = f"github:{rec.github_login.lower()}"
        else:
            key = dedupe_key(rec.full_name, rec.primary_affiliation)
        grouped[key].append(rec)

    stage1: list[ExpertRecord] = []
    for same_people in grouped.values():
        base = same_people[0]
        for item in same_people[1:]:
            base.merge(item)
        stage1.append(base)

    # Stage 2: cross-source match score union
    groups = _build_match_groups(stage1)
    merged: list[ExpertRecord] = []
    for group in groups:
        base = stage1[group[0]]
        for idx in group[1:]:
            base.merge(stage1[idx])
        merged.append(base)

    print(f"[DEDUPE] stage1={len(stage1)} -> stage2={len(merged)}")
    return merged


def _github_notable_repo_count(record: ExpertRecord) -> int:
    raw = record.raw if isinstance(record.raw, dict) else {}
    github = raw.get("github") if isinstance(raw.get("github"), dict) else {}
    return int(_safe_float(github.get("notable_repo_contrib_count"), 0.0))


def compute_score_components(record: ExpertRecord) -> dict[str, float]:
    h_index_norm = compute_h_index_normalized(record)
    notable_repo_contribs = float(_github_notable_repo_count(record))
    recent_citations_5y = float(openalex_recent_citations_5y(record))
    institution_recognition = _institution_recognition_score(record)
    return {
        "h_index_normalized": h_index_norm,
        "notable_repo_contribs": notable_repo_contribs,
        "recent_citations_5y": recent_citations_5y,
        "institution_recognition": institution_recognition,
    }


def assign_tier(score_final: float) -> str:
    if score_final >= settings.tier_elite_threshold:
        return "Elite"
    if score_final >= settings.tier_confirme_threshold:
        return "Confirme"
    if score_final >= settings.tier_emergent_threshold:
        return "Emergent"
    return "Exclu"


def score_records(records: list[ExpertRecord]) -> list[ExpertRecord]:
    if not records:
        return records

    components = [compute_score_components(record) for record in records]

    h_values = _normalize_minmax([item["h_index_normalized"] for item in components])
    repo_values = _normalize_minmax([item["notable_repo_contribs"] for item in components])
    citation_values = _normalize_minmax([item["recent_citations_5y"] for item in components])

    for idx, record in enumerate(records):
        institution_score = components[idx]["institution_recognition"]
        score_final = (
            settings.score_weight_hindex_norm * h_values[idx]
            + settings.score_weight_notable_repos * repo_values[idx]
            + settings.score_weight_recent_citations * citation_values[idx]
            + settings.score_weight_institution_recognition * institution_score
        )
        score_final = max(0.0, min(1.0, score_final))
        tier = assign_tier(score_final)

        record.score = round(score_final, 6)
        record.raw["score_components"] = {
            "h_index_normalized": round(h_values[idx], 6),
            "notable_repo_contribs": round(repo_values[idx], 6),
            "recent_citations_5y": round(citation_values[idx], 6),
            "institution_recognition": round(institution_score, 6),
        }
        record.raw["score_final"] = round(score_final, 6)
        record.raw["tier"] = tier

    return records


def export_rejections_csv(path: str, records: list[ExpertRecord]) -> None:
    if not path:
        return
    if not records:
        return

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "full_name",
                "primary_affiliation",
                "country_code",
                "sources",
                "openalex_id",
                "orcid_id",
                "github_login",
                "scholar_id",
                "score",
                "tier",
                "excluded_by",
                "filter_failures",
            ],
        )
        writer.writeheader()
        for record in records:
            failures = record.raw.get("filter_failures") if isinstance(record.raw, dict) else []
            writer.writerow(
                {
                    "full_name": record.full_name,
                    "primary_affiliation": record.primary_affiliation or "",
                    "country_code": record.country_code or "",
                    "sources": ",".join(sorted(record.sources)),
                    "openalex_id": record.openalex_id or "",
                    "orcid_id": record.orcid_id or "",
                    "github_login": record.github_login or "",
                    "scholar_id": record.scholar_id or "",
                    "score": record.score,
                    "tier": str(record.raw.get("tier") or ""),
                    "excluded_by": str(record.raw.get("excluded_by") or ""),
                    "filter_failures": " | ".join(failures) if isinstance(failures, list) else "",
                }
            )

    print(f"[DEBUG] Rejections CSV saved to: {path} ({len(records)} rows)")


def get_engine() -> Engine:
    return create_engine(settings.database_url, future=True)


def create_schema(engine: Engine) -> None:
    with engine.begin() as conn:
        schema_sql = open("etl/sql/schema.sql", "r", encoding="utf-8").read()
        for statement in [s.strip() for s in schema_sql.split(";") if s.strip()]:
            conn.execute(text(statement))


def load_to_postgres(engine: Engine, records: list[ExpertRecord]) -> None:
    insert_sql = text(
        """
        INSERT INTO experts (
            full_name,
            primary_affiliation,
            country_code,
            domains,
            github_login,
            github_url,
            openalex_id,
            orcid_id,
            scholar_id,
            source_rank,
            score,
            sources,
            raw,
            updated_at
        ) VALUES (
            :full_name,
            :primary_affiliation,
            :country_code,
            CAST(:domains AS jsonb),
            :github_login,
            :github_url,
            :openalex_id,
            :orcid_id,
            :scholar_id,
            :source_rank,
            :score,
            CAST(:sources AS jsonb),
            CAST(:raw AS jsonb),
            NOW()
        )
        """
    )

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE experts RESTART IDENTITY"))
        for rec in records:
            conn.execute(
                insert_sql,
                {
                    "full_name": rec.full_name,
                    "primary_affiliation": rec.primary_affiliation,
                    "country_code": rec.country_code,
                    "domains": json.dumps(rec.domains),
                    "github_login": rec.github_login,
                    "github_url": rec.github_url,
                    "openalex_id": rec.openalex_id,
                    "orcid_id": rec.orcid_id,
                    "scholar_id": rec.scholar_id,
                    "source_rank": rec.source_rank,
                    "score": rec.score,
                    "sources": json.dumps(sorted(rec.sources)),
                    "raw": json.dumps(rec.raw),
                },
            )


def run_pipeline(load_db: bool = True, rejected_csv_path: str | None = None) -> tuple[dict[str, int], list[ExpertRecord]]:
    extracted = collect_all_sources()
    deduped = deduplicate(extracted)
    scored = score_records(deduped)
    filtered, rejected = apply_business_filters_with_rejections(scored)

    if rejected_csv_path:
        export_rejections_csv(rejected_csv_path, rejected)

    if load_db:
        engine = get_engine()
        create_schema(engine)
        load_to_postgres(engine, filtered)

    stats = {
        "extracted": len(extracted),
        "deduplicated": len(deduped),
        "filtered": len(filtered),
        "rejected": len(rejected),
        "loaded": len(filtered) if load_db else 0,
    }
    return stats, filtered


def run_target_domain_pipeline(load_db: bool = True, rejected_csv_path: str | None = None) -> tuple[dict[str, int], list[ExpertRecord]]:
    extracted = collect_target_domain_sources()
    deduped = deduplicate(extracted)
    scored = score_records(deduped)
    filtered, rejected = apply_target_domain_business_filters_with_rejections(scored)

    if rejected_csv_path:
        export_rejections_csv(rejected_csv_path, rejected)

    if load_db:
        engine = get_engine()
        create_schema(engine)
        load_to_postgres(engine, filtered)

    stats = {
        "extracted": len(extracted),
        "deduplicated": len(deduped),
        "filtered": len(filtered),
        "rejected": len(rejected),
        "loaded": len(filtered) if load_db else 0,
    }
    return stats, filtered


def records_to_json(records: list[ExpertRecord]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for rec in records:
        item = asdict(rec)
        item["sources"] = sorted(rec.sources)
        output.append(item)
    return output
