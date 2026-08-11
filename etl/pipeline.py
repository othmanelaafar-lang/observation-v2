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
    ai_purity,
    ai_works_count,
    is_ai_focused,
    apply_business_filters,
    apply_business_filters_with_rejections,
    apply_target_domain_business_filters,
    apply_target_domain_business_filters_with_rejections,
    compute_h_index_normalized,
    openalex_h_index,
    openalex_recent_citations_5y,
    openalex_recent_works_count,
    split_by_origin,
)
from etl.models import ExpertRecord
from etl.sources.github_api import fetch_github_experts
from etl.sources.openalex_api import fetch_openalex_experts, fetch_openalex_target_domain_experts
from etl.sources.orcid_api import enrich_records_with_orcid, fetch_orcid_experts
from etl.sources.orcid_discovery import fetch_orcid_diaspora_experts
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
        ("orcid-diaspora", fetch_orcid_diaspora_experts),
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
        ("orcid-diaspora", fetch_orcid_diaspora_experts),
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


def assign_tier(record: ExpertRecord) -> str:
    """Tier from absolute metrics, not from the batch-relative score.

    `score_final` is min-max normalized across whatever happened to be scraped in
    this run, so a single outlier compresses everyone else toward zero and the
    tier of a given person changes from run to run. Absolute thresholds on
    h-index, AI focus and recent activity are stable and comparable over time.
    The score is kept as a sort key inside a tier.
    """
    h_index = openalex_h_index(record)
    recent_works = openalex_recent_works_count(record)
    ai_core = is_ai_focused(record, settings.min_ai_purity, settings.min_ai_works)
    ai_strong = is_ai_focused(
        record, settings.tier_elite_min_ai_purity, settings.tier_elite_min_ai_works
    )

    if (
        h_index >= settings.tier_elite_min_h_index
        and ai_strong
        and recent_works >= settings.tier_elite_min_recent_works
    ):
        return "Elite"
    if h_index >= settings.tier_confirme_min_h_index and ai_core:
        return "Confirme"
    if h_index >= settings.tier_emergent_min_h_index and ai_core:
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
        tier = assign_tier(record)

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


CSV_FIELDNAMES = [
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
    "h_index",
    "ai_purity",
    "ai_works_count",
    "orcid_countries",
    "moroccan_affiliation_years",
    "moroccan_affiliation_institutions",
    "moroccan_career_fraction",
    "origin_verdict",
    "origin_reason",
    "excluded_by",
    "filter_failures",
]


def _csv_row(record: ExpertRecord) -> dict[str, object]:
    raw = record.raw if isinstance(record.raw, dict) else {}
    failures = raw.get("filter_failures")
    countries = raw.get("orcid_countries")
    return {
        "full_name": record.full_name,
        "primary_affiliation": record.primary_affiliation or "",
        "country_code": record.country_code or "",
        "sources": ",".join(sorted(record.sources)),
        "openalex_id": record.openalex_id or "",
        "orcid_id": record.orcid_id or "",
        "github_login": record.github_login or "",
        "scholar_id": record.scholar_id or "",
        "score": record.score,
        "tier": str(raw.get("tier") or ""),
        "h_index": openalex_h_index(record),
        "ai_purity": raw.get("ai_purity", ""),
        "ai_works_count": raw.get("ai_works_count", ""),
        "orcid_countries": ",".join(countries) if isinstance(countries, list) else "",
        "moroccan_affiliation_years": raw.get("moroccan_affiliation_years", ""),
        "moroccan_affiliation_institutions": raw.get("moroccan_affiliation_institutions", ""),
        "moroccan_career_fraction": raw.get("moroccan_career_fraction", ""),
        "origin_verdict": str(raw.get("origin_verdict") or ""),
        "origin_reason": str(raw.get("origin_reason") or ""),
        "excluded_by": str(raw.get("excluded_by") or ""),
        "filter_failures": " | ".join(failures) if isinstance(failures, list) else "",
    }


def _export_csv(path: str, records: list[ExpertRecord], label: str) -> None:
    if not path or not records:
        return

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES)
        writer.writeheader()
        for record in records:
            writer.writerow(_csv_row(record))

    print(f"[DEBUG] {label} CSV saved to: {path} ({len(records)} rows)")


def export_rejections_csv(path: str, records: list[ExpertRecord]) -> None:
    _export_csv(path, records, "Rejections")


def export_review_queue_csv(path: str, records: list[ExpertRecord]) -> None:
    _export_csv(path, records, "Review queue")


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


def _finalize(
    extracted: list[ExpertRecord],
    deduped: list[ExpertRecord],
    filtered: list[ExpertRecord],
    rejected: list[ExpertRecord],
    *,
    load_db: bool,
    rejected_csv_path: str | None,
    review_csv_path: str | None,
) -> tuple[dict[str, int], list[ExpertRecord]]:
    """ORCID origin check, then split into accepted / review / rejected."""
    enrich_records_with_orcid(filtered)
    accepted, review, origin_rejected = split_by_origin(filtered)
    rejected = rejected + origin_rejected

    # The origin verdict depends on ORCID data fetched after scoring, so refresh
    # the tier now that every signal is available.
    for record in accepted + review:
        record.raw["tier"] = assign_tier(record)

    # A profile tiered "Exclu" sits below the lowest published tier; keep it out
    # of the accepted set rather than shipping it to the API.
    below_bar = [record for record in accepted if record.raw.get("tier") == "Exclu"]
    for record in below_bar:
        failures = record.raw.setdefault("filter_failures", [])
        if isinstance(failures, list):
            failures.append("tier-exclu")
        record.raw["excluded_by"] = "tier-exclu"
    if below_bar:
        print(f"[TIER] Dropped {len(below_bar)} profiles below the Emergent bar.")
    accepted = [record for record in accepted if record.raw.get("tier") != "Exclu"]
    rejected = rejected + below_bar

    if rejected_csv_path:
        export_rejections_csv(rejected_csv_path, rejected)
    if review_csv_path:
        export_review_queue_csv(review_csv_path, review)

    if load_db:
        engine = get_engine()
        create_schema(engine)
        load_to_postgres(engine, accepted)

    stats = {
        "extracted": len(extracted),
        "deduplicated": len(deduped),
        "filtered": len(accepted),
        "review": len(review),
        "rejected": len(rejected),
        "loaded": len(accepted) if load_db else 0,
    }
    return stats, accepted


def run_pipeline(
    load_db: bool = True,
    rejected_csv_path: str | None = None,
    review_csv_path: str | None = None,
) -> tuple[dict[str, int], list[ExpertRecord]]:
    extracted = collect_all_sources()
    deduped = deduplicate(extracted)
    scored = score_records(deduped)
    filtered, rejected = apply_business_filters_with_rejections(scored)

    return _finalize(
        extracted,
        deduped,
        filtered,
        rejected,
        load_db=load_db,
        rejected_csv_path=rejected_csv_path,
        review_csv_path=review_csv_path,
    )


def run_target_domain_pipeline(
    load_db: bool = True,
    rejected_csv_path: str | None = None,
    review_csv_path: str | None = None,
) -> tuple[dict[str, int], list[ExpertRecord]]:
    extracted = collect_target_domain_sources()
    deduped = deduplicate(extracted)
    scored = score_records(deduped)
    filtered, rejected = apply_target_domain_business_filters_with_rejections(scored)

    return _finalize(
        extracted,
        deduped,
        filtered,
        rejected,
        load_db=load_db,
        rejected_csv_path=rejected_csv_path,
        review_csv_path=review_csv_path,
    )


def records_to_json(records: list[ExpertRecord]) -> list[dict[str, object]]:
    output: list[dict[str, object]] = []
    for rec in records:
        item = asdict(rec)
        item["sources"] = sorted(rec.sources)
        output.append(item)
    return output
