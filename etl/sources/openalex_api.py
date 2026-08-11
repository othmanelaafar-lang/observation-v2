from __future__ import annotations

import time

import requests
from requests import RequestException

from etl.config import settings
from etl.models import ExpertRecord

OPENALEX_API = "https://api.openalex.org"

# Fallback list used when /topics is unreachable: OpenAlex subfield 1702
# ("Artificial Intelligence") plus a few data-science oriented topics.
FALLBACK_AI_TOPIC_IDS = [
    "T10028",  # Topic Modeling
    "T10181",  # Natural Language Processing Techniques
    "T10215",  # Speech Recognition and Synthesis
    "T10320",  # Explainable Artificial Intelligence (XAI)
    "T11689",  # Machine Learning and Data Classification
    "T12072",  # Machine Learning and Algorithms
    "T12157",  # Multi-Agent Systems and Negotiation
    "T11512",  # Text and Document Classification
]

# OpenAlex subfields whose topics are considered "AI / data" for discovery.
AI_SUBFIELD_IDS = ["1702"]  # Artificial Intelligence

_topic_id_cache: list[str] | None = None


def _polite_params(params: dict[str, object] | None = None) -> dict[str, object]:
    merged = dict(params or {})
    if settings.openalex_mailto:
        merged.setdefault("mailto", settings.openalex_mailto)
    return merged


def _openalex_get(path: str, *, params: dict[str, object] | None = None) -> dict[str, object] | None:
    """GET an OpenAlex endpoint with retry on rate limiting."""
    attempts = max(settings.openalex_max_retries, 1)
    for attempt in range(attempts):
        try:
            resp = requests.get(
                f"{OPENALEX_API}{path}",
                params=_polite_params(params),
                timeout=settings.request_timeout,
            )
        except RequestException as exc:
            print(f"[WARN] OpenAlex request failed for '{path}': {exc}")
            return None

        if resp.status_code == 429:
            wait = settings.openalex_retry_backoff_seconds * (attempt + 1)
            print(f"[WARN] OpenAlex rate limit (429) on '{path}'. Retrying in {wait}s.")
            time.sleep(wait)
            continue

        if resp.status_code >= 400:
            print(f"[WARN] OpenAlex returned HTTP {resp.status_code} for '{path}'.")
            return None

        try:
            payload = resp.json()
        except ValueError:
            print(f"[WARN] OpenAlex returned a non-JSON body for '{path}'.")
            return None
        return payload if isinstance(payload, dict) else None

    print(f"[WARN] OpenAlex still rate limited after {attempts} attempts on '{path}'.")
    return None


def _ai_topic_ids() -> list[str]:
    """Resolve the AI topic ids used to filter authors, with a static fallback."""
    global _topic_id_cache
    if _topic_id_cache is not None:
        return _topic_id_cache

    if settings.openalex_ai_topic_ids:
        _topic_id_cache = list(settings.openalex_ai_topic_ids)
        return _topic_id_cache

    collected: list[str] = []
    for subfield_id in AI_SUBFIELD_IDS:
        payload = _openalex_get(
            "/topics",
            params={"filter": f"subfield.id:{subfield_id}", "per-page": 200},
        )
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            continue
        for topic in results:
            if not isinstance(topic, dict):
                continue
            topic_id = topic.get("id")
            if isinstance(topic_id, str) and topic_id:
                collected.append(topic_id.rsplit("/", 1)[-1])

    _topic_id_cache = collected or list(FALLBACK_AI_TOPIC_IDS)
    print(f"[OPENALEX] Using {len(_topic_id_cache)} AI topic ids for discovery.")
    return _topic_id_cache


def _extract_topics(author: dict[str, object]) -> list[str]:
    """Short, human-readable domain labels: prefer concepts, fall back to topics."""
    labels: list[str] = []
    seen: set[str] = set()

    concepts = author.get("x_concepts") if isinstance(author.get("x_concepts"), list) else []
    for concept in concepts[:8]:
        if not isinstance(concept, dict):
            continue
        name = concept.get("display_name")
        if isinstance(name, str) and name and name.lower() not in seen:
            seen.add(name.lower())
            labels.append(name)

    if labels:
        return labels

    topics = author.get("topics") if isinstance(author.get("topics"), list) else []
    for topic in topics[:8]:
        if not isinstance(topic, dict):
            continue
        name = topic.get("display_name")
        if isinstance(name, str) and name and name.lower() not in seen:
            seen.add(name.lower())
            labels.append(name)

    return labels


def _extract_affiliation(author: dict[str, object]) -> tuple[str | None, str | None]:
    """Current institution: last known first, else the most recent affiliation.

    `affiliations[0]` is not ordered by recency, so using it showed people under a
    random institution from their past.
    """
    last_known = author.get("last_known_institutions") or []
    if isinstance(last_known, list) and last_known and isinstance(last_known[0], dict):
        institution = last_known[0]
        return institution.get("display_name"), institution.get("country_code")

    affiliations = author.get("affiliations") if isinstance(author.get("affiliations"), list) else []
    most_recent: tuple[int, dict[str, object]] | None = None
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution")
        if not isinstance(institution, dict):
            continue
        years = [year for year in (affiliation.get("years") or []) if isinstance(year, int)]
        latest = max(years) if years else 0
        if most_recent is None or latest > most_recent[0]:
            most_recent = (latest, institution)

    if most_recent:
        return most_recent[1].get("display_name"), most_recent[1].get("country_code")

    return None, None


def _author_to_record(
    author: dict[str, object],
    matched_target_domains: list[str] | None = None,
) -> ExpertRecord | None:
    display_name = author.get("display_name")
    if not display_name:
        return None

    affiliation, country_code = _extract_affiliation(author)
    topics = _extract_topics(author)

    orcid = author.get("orcid") if isinstance(author.get("orcid"), str) else None

    record = ExpertRecord(
        full_name=display_name,
        primary_affiliation=affiliation,
        country_code=country_code,
        domains=topics,
        openalex_id=author.get("id"),
        orcid_id=orcid,
        source_rank=float(author.get("works_count") or 0),
        sources={"openalex"},
        raw={"openalex": author},
    )
    if matched_target_domains:
        record.raw["matched_target_domains"] = sorted(set(matched_target_domains))
    return record


def _author_filter_clause(country_clause: str) -> str:
    """Authors linked to a Moroccan institution and active on AI topics."""
    clauses = [country_clause, f"topics.id:{'|'.join(_ai_topic_ids())}"]
    if settings.openalex_min_works_count > 0:
        clauses.append(f"works_count:>{settings.openalex_min_works_count - 1}")
    if settings.openalex_min_h_index > 0:
        clauses.append(f"summary_stats.h_index:>{settings.openalex_min_h_index - 1}")
    return ",".join(clauses)


# "resident" = currently based in Morocco; "diaspora" = Moroccan institution
# somewhere in the affiliation history but currently abroad.
DISCOVERY_STRATEGIES = [
    ("resident", "last_known_institutions.country_code:{code}"),
    ("diaspora", "affiliations.institution.country_code:{code}"),
]


def fetch_openalex_experts() -> list[ExpertRecord]:
    """Discover Moroccan-affiliated AI authors directly from the authors index.

    The previous implementation used `/authors?search=<domain>`, but OpenAlex only
    searches an author's *display name* there, so it returned entities literally
    named "Machine Learning" instead of machine-learning researchers.
    """
    experts: list[ExpertRecord] = []
    seen_ids: set[str] = set()

    for strategy, country_template in DISCOVERY_STRATEGIES:
        country_clause = country_template.format(code=settings.target_country_code)
        filter_clause = _author_filter_clause(country_clause)
        collected = 0

        for page in range(1, settings.max_pages + 1):
            payload = _openalex_get(
                "/authors",
                params={
                    "filter": filter_clause,
                    "sort": "cited_by_count:desc",
                    "per-page": min(settings.page_size, 200),
                    "page": page,
                },
            )
            if not payload:
                break

            results = payload.get("results")
            if not isinstance(results, list) or not results:
                break

            for author in results:
                if not isinstance(author, dict):
                    continue
                author_id = author.get("id")
                if isinstance(author_id, str):
                    if author_id in seen_ids:
                        continue
                    seen_ids.add(author_id)

                record = _author_to_record(author)
                if record:
                    record.raw["openalex_discovery"] = strategy
                    experts.append(record)
                    collected += 1

        print(f"[OPENALEX] Strategy '{strategy}' collected {collected} profiles.")

    print(f"[OPENALEX] Authors discovery collected {len(experts)} profiles.")
    return experts


def _chunk(items: list[str], size: int) -> list[list[str]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def _fetch_authors_by_ids(author_ids: list[str]) -> dict[str, dict[str, object]]:
    """Batch-hydrate authors (50 per request) instead of one request per author."""
    hydrated: dict[str, dict[str, object]] = {}

    short_ids = [author_id.rsplit("/", 1)[-1] for author_id in author_ids]
    for batch in _chunk(short_ids, 50):
        payload = _openalex_get(
            "/authors",
            params={"filter": f"ids.openalex:{'|'.join(batch)}", "per-page": 50},
        )
        results = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(results, list):
            continue
        for author in results:
            if isinstance(author, dict) and isinstance(author.get("id"), str):
                hydrated[author["id"]] = author

    return hydrated


def fetch_openalex_target_domain_experts() -> list[ExpertRecord]:
    """Find Moroccan-affiliated authors publishing in the configured target domains."""
    author_domains: dict[str, set[str]] = {}
    author_works: dict[str, dict[str, object]] = {}
    ordered_ids: list[str] = []

    for domain in settings.target_ai_domains:
        for page in range(1, settings.max_pages + 1):
            payload = _openalex_get(
                "/works",
                params={
                    "search": domain,
                    "filter": f"institutions.country_code:{settings.target_country_code}",
                    "per-page": min(settings.page_size, 200),
                    "page": page,
                },
            )
            if not payload:
                break

            results = payload.get("results")
            if not isinstance(results, list) or not results:
                break

            for work in results:
                if not isinstance(work, dict):
                    continue

                authorships = work.get("authorships") if isinstance(work.get("authorships"), list) else []
                for authorship in authorships:
                    if not isinstance(authorship, dict):
                        continue

                    # Only keep authors actually attached to a Moroccan institution
                    # on this work, otherwise every foreign co-author leaks in.
                    institutions = authorship.get("institutions") if isinstance(authorship.get("institutions"), list) else []
                    is_moroccan_authorship = any(
                        isinstance(inst, dict)
                        and str(inst.get("country_code") or "").upper() == settings.target_country_code.upper()
                        for inst in institutions
                    )
                    if not is_moroccan_authorship:
                        continue

                    author_ref = authorship.get("author") if isinstance(authorship.get("author"), dict) else {}
                    author_id = author_ref.get("id") if isinstance(author_ref.get("id"), str) else None
                    if not author_id:
                        continue

                    if author_id not in author_domains:
                        author_domains[author_id] = set()
                        author_works[author_id] = work
                        ordered_ids.append(author_id)
                    author_domains[author_id].add(domain)

            if len(ordered_ids) >= settings.openalex_max_target_authors:
                break

        if len(ordered_ids) >= settings.openalex_max_target_authors:
            print(
                f"[OPENALEX] Reached openalex_max_target_authors="
                f"{settings.openalex_max_target_authors}; stopping works scan early."
            )
            break

    ordered_ids = ordered_ids[: settings.openalex_max_target_authors]
    print(f"[OPENALEX] Target-domain works scan found {len(ordered_ids)} Moroccan-affiliated authors.")

    hydrated = _fetch_authors_by_ids(ordered_ids)

    experts: list[ExpertRecord] = []
    for author_id in ordered_ids:
        author_payload = hydrated.get(author_id)
        if not author_payload:
            continue

        record = _author_to_record(
            author_payload,
            matched_target_domains=sorted(author_domains.get(author_id, set())),
        )
        if not record:
            continue

        record.raw["openalex_work"] = author_works.get(author_id)
        experts.append(record)

    print(f"[OPENALEX] Target-domain discovery collected {len(experts)} profiles.")
    return experts
