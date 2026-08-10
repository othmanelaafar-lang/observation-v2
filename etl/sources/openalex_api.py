from __future__ import annotations

import requests
from requests import RequestException

from etl.config import settings
from etl.models import ExpertRecord

OPENALEX_API = "https://api.openalex.org"


def _openalex_get(path: str, *, params: dict[str, object] | None = None) -> dict[str, object] | None:
    try:
        resp = requests.get(
            f"{OPENALEX_API}{path}",
            params=params,
            timeout=settings.request_timeout,
        )
    except RequestException as exc:
        print(f"[WARN] OpenAlex request failed for '{path}': {exc}")
        return None

    if resp.status_code == 429:
        print("[WARN] OpenAlex rate limit reached (429). Returning partial OpenAlex results.")
        return None

    if resp.status_code >= 400:
        print(f"[WARN] OpenAlex returned HTTP {resp.status_code} for '{path}'.")
        return None

    payload = resp.json()
    return payload if isinstance(payload, dict) else None


def _extract_topics(author: dict[str, object]) -> list[str]:
    return [
        t.get("display_name", "")
        for t in author.get("x_concepts", [])[:8]
        if isinstance(t, dict) and t.get("display_name")
    ]


def _extract_affiliation(author: dict[str, object]) -> tuple[str | None, str | None]:
    affiliation = None
    country_code = None
    affiliations = author.get("affiliations") or []
    if affiliations:
        institution = affiliations[0].get("institution") or {}
        affiliation = institution.get("display_name")
        country_code = institution.get("country_code")

    if not country_code:
        last_known = author.get("last_known_institutions") or []
        if last_known:
            country_code = (last_known[0] or {}).get("country_code")

    return affiliation, country_code


def _author_to_record(author: dict[str, object], matched_target_domains: list[str] | None = None) -> ExpertRecord | None:
    display_name = author.get("display_name")
    if not display_name:
        return None

    affiliation, country_code = _extract_affiliation(author)
    topics = _extract_topics(author)

    record = ExpertRecord(
        full_name=display_name,
        primary_affiliation=affiliation,
        country_code=country_code,
        domains=topics,
        openalex_id=author.get("id"),
        source_rank=float(author.get("works_count") or 0),
        sources={"openalex"},
        raw={"openalex": author},
    )
    if matched_target_domains:
        record.raw["matched_target_domains"] = sorted(set(matched_target_domains))
    return record


def fetch_openalex_experts() -> list[ExpertRecord]:
    experts: list[ExpertRecord] = []
    seen_ids: set[str] = set()
    stop_due_to_rate_limit = False

    for domain in settings.target_ai_domains:
        if stop_due_to_rate_limit:
            break

        search_terms = [
            domain,
            f"{domain} morocco",
            f"{domain} maroc",
        ]

        for search_term in search_terms:
            if stop_due_to_rate_limit:
                break

            for page in range(1, settings.max_pages + 1):
                params = {
                    "search": search_term,
                    "per-page": settings.page_size,
                    "page": page,
                }
                try:
                    resp = requests.get(
                        f"{OPENALEX_API}/authors",
                        params=params,
                        timeout=settings.request_timeout,
                    )
                except RequestException as exc:
                    print(f"[WARN] OpenAlex request failed for '{search_term}' page {page}: {exc}")
                    break

                if resp.status_code == 429:
                    print("[WARN] OpenAlex rate limit reached (429). Returning partial OpenAlex results.")
                    stop_due_to_rate_limit = True
                    break

                if resp.status_code >= 400:
                    print(
                        f"[WARN] OpenAlex returned HTTP {resp.status_code} for '{search_term}' page {page}."
                    )
                    break

                results = resp.json().get("results", [])
                if not results:
                    break

                for author in results:
                    author_id = author.get("id")
                    if isinstance(author_id, str) and author_id in seen_ids:
                        continue

                    display_name = author.get("display_name")
                    if not display_name:
                        continue

                    topics = [
                        t.get("display_name", "")
                        for t in author.get("x_concepts", [])[:5]
                        if t.get("display_name")
                    ]

                    affiliation = None
                    country_code = None
                    affiliations = author.get("affiliations") or []
                    if affiliations:
                        institution = affiliations[0].get("institution") or {}
                        affiliation = institution.get("display_name")
                        country_code = institution.get("country_code")

                    if not country_code:
                        last_known = author.get("last_known_institutions") or []
                        if last_known:
                            country_code = (last_known[0] or {}).get("country_code")

                    experts.append(
                        ExpertRecord(
                            full_name=display_name,
                            primary_affiliation=affiliation,
                            country_code=country_code,
                            domains=topics,
                            openalex_id=author_id,
                            source_rank=float(author.get("works_count") or 0),
                            sources={"openalex"},
                            raw={"openalex": author},
                        )
                    )
                    if isinstance(author_id, str):
                        seen_ids.add(author_id)

    return experts


def fetch_openalex_target_domain_experts() -> list[ExpertRecord]:
    experts: list[ExpertRecord] = []
    seen_ids: set[str] = set()
    author_cache: dict[str, dict[str, object] | None] = {}

    for domain in settings.target_ai_domains:
        for page in range(1, settings.max_pages + 1):
            payload = _openalex_get(
                "/works",
                params={
                    "search": domain,
                    "filter": f"institutions.country_code:{settings.target_country_code}",
                    "per-page": settings.page_size,
                    "page": page,
                },
            )
            if not payload:
                break

            results = payload.get("results", [])
            if not isinstance(results, list) or not results:
                break

            for work in results:
                if not isinstance(work, dict):
                    continue

                authorships = work.get("authorships") if isinstance(work.get("authorships"), list) else []
                for authorship in authorships:
                    if not isinstance(authorship, dict):
                        continue

                    author_ref = authorship.get("author") if isinstance(authorship.get("author"), dict) else {}
                    author_id = author_ref.get("id") if isinstance(author_ref.get("id"), str) else None
                    if not author_id or author_id in seen_ids:
                        continue

                    if author_id not in author_cache:
                        short_id = author_id.rsplit("/", 1)[-1]
                        author_cache[author_id] = _openalex_get(f"/authors/{short_id}")

                    author_payload = author_cache.get(author_id)
                    if not author_payload:
                        continue

                    record = _author_to_record(author_payload, matched_target_domains=[domain])
                    if not record:
                        continue

                    record.raw["openalex_work"] = work
                    experts.append(record)
                    seen_ids.add(author_id)

    return experts
