"""ORCID-first discovery of the Moroccan diaspora.

OpenAlex only knows researchers who *published while affiliated with* a Moroccan
institution. Someone who graduated in Rabat and left for a PhD abroad never
published from Morocco, so OpenAlex cannot see them at all - and that is the most
common path for the elite diaspora this observatory targets.

ORCID records *education*, not just publications, so it sees exactly that
population. The two sources are complementary rather than interchangeable:
Mehdi Bennis is found by OpenAlex (he published from Cadi Ayyad early on) but not
by ORCID (his ORCID lists only Oulu, EURECOM and EPFL).

Flow: search ORCID for people attached to a Moroccan institution, then hydrate
them from OpenAlex in batches of 50 to obtain the metrics needed for scoring and
tiering. Profiles with no OpenAlex record are dropped - without publication data
there is nothing to rank them on.
"""

from __future__ import annotations

import time

import requests
from requests import RequestException

from etl.config import settings
from etl.models import ExpertRecord
from etl.sources.openalex_api import _openalex_get

ORCID_SEARCH = "https://pub.orcid.org/v3.0/expanded-search/"


def _orcid_search(query: str, start: int, rows: int) -> dict[str, object] | None:
    try:
        response = requests.get(
            ORCID_SEARCH,
            headers={"Accept": "application/json"},
            params={"q": query, "start": start, "rows": rows},
            timeout=settings.request_timeout,
        )
    except RequestException as exc:
        print(f"[WARN] ORCID search failed for {query!r}: {exc}")
        return None

    if response.status_code >= 400:
        print(f"[WARN] ORCID search returned HTTP {response.status_code} for {query!r}.")
        return None

    try:
        payload = response.json()
    except ValueError:
        return None
    return payload if isinstance(payload, dict) else None


def _search_institution(institution: str) -> list[dict[str, object]]:
    """ORCID records that list one Moroccan institution as a *past* affiliation.

    `affiliation-org-name` matches current staff and students too, who are by
    definition not diaspora - on Cadi Ayyad it returns 1217 current affiliates
    against 387 past ones. Searching past affiliations targets the people who
    moved on, which is the population this observatory wants.
    """
    query = f'past-institution-affiliation-name:"{institution}"'
    collected: list[dict[str, object]] = []
    page_size = min(settings.orcid_search_page_size, 200)

    while len(collected) < settings.orcid_search_max_per_institution:
        payload = _orcid_search(query, start=len(collected), rows=page_size)
        if not payload:
            break

        results = payload.get("expanded-result")
        if not isinstance(results, list) or not results:
            break

        collected.extend(item for item in results if isinstance(item, dict))
        if len(results) < page_size:
            break
        time.sleep(settings.orcid_enrichment_sleep_seconds)

    return collected[: settings.orcid_search_max_per_institution]


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _hydrate_from_openalex(orcid_ids: list[str]) -> dict[str, dict[str, object]]:
    """Map ORCID id -> OpenAlex author payload, 50 ids per request."""
    hydrated: dict[str, dict[str, object]] = {}

    for batch in _chunk(orcid_ids, 50):
        # Goes through the shared client so these lookups hit the disk cache and
        # so an exhausted daily budget aborts loudly instead of silently
        # returning a fraction of the diaspora.
        payload = _openalex_get(
            "/authors", params={"filter": f"orcid:{'|'.join(batch)}", "per-page": 50}
        )
        if not payload:
            continue

        for author in payload.get("results") or []:
            if not isinstance(author, dict):
                continue
            orcid = author.get("orcid")
            if not isinstance(orcid, str):
                continue
            key = orcid.rsplit("/", 1)[-1].upper()
            # OpenAlex sometimes holds duplicate author records for one ORCID;
            # keep the one with the most works.
            existing = hydrated.get(key)
            if existing is None or (author.get("works_count") or 0) > (existing.get("works_count") or 0):
                hydrated[key] = author

    return hydrated


def fetch_orcid_diaspora_experts() -> list[ExpertRecord]:
    if not settings.enable_orcid_discovery:
        return []

    seen: dict[str, dict[str, object]] = {}
    matched_institution: dict[str, str] = {}
    for institution in settings.orcid_search_institutions:
        found = _search_institution(institution)
        for item in found:
            orcid_id = item.get("orcid-id")
            if isinstance(orcid_id, str) and orcid_id:
                key = orcid_id.upper()
                seen.setdefault(key, item)
                matched_institution.setdefault(key, institution)
        print(f"[ORCID-DISCO] {institution}: {len(found)} records (total distinct {len(seen)})")

    if not seen:
        return []

    hydrated = _hydrate_from_openalex(list(seen))
    print(f"[ORCID-DISCO] {len(hydrated)}/{len(seen)} ORCID ids matched an OpenAlex author.")

    experts: list[ExpertRecord] = []
    for orcid_id, search_row in seen.items():
        author = hydrated.get(orcid_id)
        if not author:
            continue

        affiliation = None
        country_code = None
        last_known = author.get("last_known_institutions") or []
        if isinstance(last_known, list) and last_known and isinstance(last_known[0], dict):
            affiliation = last_known[0].get("display_name")
            country_code = last_known[0].get("country_code")

        concepts = author.get("x_concepts") if isinstance(author.get("x_concepts"), list) else []
        domains = [
            concept.get("display_name")
            for concept in concepts[:8]
            if isinstance(concept, dict) and concept.get("display_name")
        ]

        experts.append(
            ExpertRecord(
                full_name=author.get("display_name")
                or f"{search_row.get('given-names','')} {search_row.get('family-names','')}".strip(),
                primary_affiliation=affiliation,
                country_code=country_code,
                domains=domains,
                openalex_id=author.get("id"),
                orcid_id=f"https://orcid.org/{orcid_id}",
                source_rank=float(author.get("works_count") or 0),
                sources={"openalex", "orcid"},
                raw={
                    "openalex": author,
                    "orcid_search": search_row,
                    "openalex_discovery": "orcid-diaspora",
                    "orcid_moroccan_institution": matched_institution.get(orcid_id),
                },
            )
        )

    print(f"[ORCID-DISCO] Collected {len(experts)} profiles.")
    return experts
