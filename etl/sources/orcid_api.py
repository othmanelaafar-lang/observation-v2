from __future__ import annotations

import time

import requests
from requests import RequestException

from etl.config import settings
from etl.models import ExpertRecord

ORCID_API = "https://pub.orcid.org/v3.0"


def _safe_orcid_get(path: str, headers: dict[str, str]) -> dict[str, object] | None:
    try:
        resp = requests.get(
            f"{ORCID_API}{path}",
            headers=headers,
            timeout=settings.request_timeout,
        )
    except RequestException as exc:
        print(f"[WARN] ORCID request failed for '{path}': {exc}")
        return None

    if resp.status_code >= 400:
        return None

    payload = resp.json()
    return payload if isinstance(payload, dict) else None


def _affiliation_countries(payload: dict[str, object] | None) -> set[str]:
    """Country codes declared in an ORCID educations/employments section."""
    countries: set[str] = set()
    if not isinstance(payload, dict):
        return countries

    groups = payload.get("affiliation-group")
    if not isinstance(groups, list):
        return countries

    for group in groups:
        if not isinstance(group, dict):
            continue
        for summary in group.get("summaries") or []:
            if not isinstance(summary, dict):
                continue
            for value in summary.values():
                if not isinstance(value, dict):
                    continue
                organization = value.get("organization") if isinstance(value.get("organization"), dict) else {}
                address = organization.get("address") if isinstance(organization.get("address"), dict) else {}
                country = address.get("country")
                if isinstance(country, str) and country.strip():
                    countries.add(country.strip().upper())

    return countries


def fetch_orcid_affiliation_countries(orcid_id: str) -> set[str]:
    """Where this person actually studied and worked, per their own ORCID record."""
    short_id = (orcid_id or "").rsplit("/", 1)[-1].strip()
    if not short_id:
        return set()

    headers = {"Accept": "application/json"}
    countries: set[str] = set()
    for section in ("educations", "employments"):
        countries |= _affiliation_countries(_safe_orcid_get(f"/{short_id}/{section}", headers))
    return countries


def enrich_records_with_orcid(records: list[ExpertRecord]) -> None:
    """Attach ORCID-declared countries to each record, in place.

    Run this over survivors only - it costs two requests per profile.
    """
    if not settings.enable_orcid_enrichment:
        print("[ORCID] Enrichment disabled (ENABLE_ORCID_ENRICHMENT=false).")
        return

    enriched = 0
    for record in records:
        if not record.orcid_id:
            continue
        countries = fetch_orcid_affiliation_countries(record.orcid_id)
        if countries:
            record.raw["orcid_countries"] = sorted(countries)
            enriched += 1
        time.sleep(settings.orcid_enrichment_sleep_seconds)

    missing = sum(1 for record in records if not record.orcid_id)
    print(
        f"[ORCID] Enriched {enriched}/{len(records)} profiles "
        f"({missing} have no ORCID id, {len(records) - enriched - missing} returned no country)."
    )


def fetch_orcid_experts() -> list[ExpertRecord]:
    if not settings.enable_orcid:
        return []

    headers = {
        "Accept": "application/json",
    }
    query = f'affiliation-org-name:"{settings.target_country_name}"'
    params = {"q": query, "rows": settings.page_size}

    try:
        resp = requests.get(
            f"{ORCID_API}/expanded-search/",
            params=params,
            headers=headers,
            timeout=settings.request_timeout,
        )
    except RequestException as exc:
        print(f"[WARN] ORCID expanded-search failed: {exc}")
        return []

    if resp.status_code != 200:
        return []

    data = resp.json()
    results = data.get("expanded-result", [])

    experts: list[ExpertRecord] = []
    for item in results:
        if not isinstance(item, dict):
            continue

        given = item.get("given-names", "")
        family = item.get("family-names", "")
        full_name = f"{given} {family}".strip()
        if not full_name:
            continue

        orcid_id = item.get("orcid-id")
        employments = _safe_orcid_get(f"/{orcid_id}/employments", headers) if orcid_id else None
        educations = _safe_orcid_get(f"/{orcid_id}/educations", headers) if orcid_id else None

        experts.append(
            ExpertRecord(
                full_name=full_name,
                primary_affiliation=item.get("institution-name"),
                country_code=settings.target_country_code,
                orcid_id=orcid_id,
                source_rank=1.0,
                sources={"orcid"},
                raw={
                    "orcid": item,
                    "orcid_employments": employments or {},
                    "orcid_educations": educations or {},
                },
            )
        )

    return experts
