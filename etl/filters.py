from __future__ import annotations

import re
from datetime import datetime

from etl.config import settings
from etl.models import ExpertRecord

AI_KEYWORDS = {
    "artificial intelligence",
    "machine learning",
    "deep learning",
    "computer vision",
    "natural language processing",
    "data science",
    "data analyst",
    "data analyste",
    "data analysis",
    "reinforcement learning",
    "generative ai",
}

AI_REGEX_PATTERNS = [
    re.compile(r"\bai\b"),
    re.compile(r"\bml\b"),
    re.compile(r"\bnlp\b"),
    re.compile(r"\bllm\b"),
]

MOROCCO_KEYWORDS = {
    "morocco",
    "moroccan",
    "maroc",
    "marocain",
    "marocaine",
    "casablanca",
    "rabat",
    "marrakech",
    "fes",
    "agadir",
    "tanger",
    "meknes",
    "oujda",
    "tetouan",
    "kenitra",
}

MOROCCAN_NAME_TOKENS = {
    "abdel",
    "abdelilah",
    "abdelkrim",
    "abderrahim",
    "abid",
    "ait",
    "amine",
    "aziz",
    "ben",
    "benali",
    "bennani",
    "bouchikhi",
    "broumi",
    "chakir",
    "cherradi",
    "driss",
    "el",
    "essahlaoui",
    "ghogho",
    "hajji",
    "hicham",
    "idhammad",
    "jalal",
    "karim",
    "khaldi",
    "lahmiri",
    "maher",
    "mohamed",
    "mohammed",
    "mounir",
    "nawal",
    "noureddine",
    "oulad",
    "rachid",
    "saad",
    "sael",
    "salah",
    "said",
    "samira",
    "tajeddine",
    "younes",
    "youssef",
    "zahi",
}

TARGET_DOMAIN_KEYWORDS = {
    "machine learning",
    "deep learning",
    "natural language processing",
    "data science",
    "data analyst",
    "data analysis",
}

TARGET_DOMAIN_REGEX_PATTERNS = [
    re.compile(r"\bml\b"),
    re.compile(r"\bnlp\b"),
]

OPENALEX_AI_TOPICS = {
    "artificial intelligence",
    "machine learning",
    "natural language processing",
    "computer vision",
    "deep learning",
    "data science",
    "robotics",
}

OPENALEX_AI_SUBFIELDS = {
    "artificial intelligence",
    "computer vision and pattern recognition",
    "human-computer interaction",
    "information systems",
}


def _combined_text(record: ExpertRecord) -> str:
    chunks: list[str] = [record.full_name or "", record.primary_affiliation or ""]

    gh = record.raw.get("github") if isinstance(record.raw, dict) else None
    if isinstance(gh, dict):
        chunks.extend(
            [
                str(gh.get("bio") or ""),
                str(gh.get("location") or ""),
                str(gh.get("company") or ""),
                str(gh.get("name") or ""),
            ]
        )

    oa = record.raw.get("openalex") if isinstance(record.raw, dict) else None
    if isinstance(oa, dict):
        chunks.append(str(oa.get("display_name") or ""))
        chunks.extend(str(topic) for topic in (record.domains or []))
        for aff in oa.get("affiliations") or []:
            institution = aff.get("institution") or {}
            chunks.append(str(institution.get("display_name") or ""))
            chunks.append(str(institution.get("country_code") or ""))

    return " ".join(chunks).lower()


def is_ai_expert(record: ExpertRecord) -> bool:
    text = _combined_text(record)
    domains_text = " ".join(record.domains or []).lower()

    if any(keyword in domains_text for keyword in AI_KEYWORDS):
        return True

    if any(keyword in text for keyword in AI_KEYWORDS):
        return True

    return any(pattern.search(text) for pattern in AI_REGEX_PATTERNS)


def matches_target_ai_domains(record: ExpertRecord) -> bool:
    text = _combined_text(record)
    domains_text = " ".join(record.domains or []).lower()

    if any(keyword in domains_text for keyword in TARGET_DOMAIN_KEYWORDS):
        return True

    if any(keyword in text for keyword in TARGET_DOMAIN_KEYWORDS):
        return True

    return any(pattern.search(text) for pattern in TARGET_DOMAIN_REGEX_PATTERNS)


def has_moroccan_signal(record: ExpertRecord) -> bool:
    if (record.country_code or "").upper() == settings.target_country_code.upper():
        return True

    # Structured signal first: a diaspora researcher usually has a foreign
    # `country_code` but keeps a Moroccan institution in their affiliation history,
    # which free-text keyword matching alone never catches.
    if has_moroccan_origin_signal(record):
        return True

    text = _combined_text(record)
    return any(keyword in text for keyword in MOROCCO_KEYWORDS)


def has_moroccan_origin_signal(record: ExpertRecord) -> bool:
    raw = record.raw if isinstance(record.raw, dict) else {}

    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        country_code = institution.get("country_code") if isinstance(institution.get("country_code"), str) else None
        if country_code and country_code.upper() == settings.target_country_code.upper():
            return True
        institution_name = institution.get("display_name") if isinstance(institution.get("display_name"), str) else ""
        if any(keyword in institution_name.lower() for keyword in MOROCCO_KEYWORDS):
            return True

    orcid = raw.get("orcid") if isinstance(raw.get("orcid"), dict) else {}
    institution_name = str(orcid.get("institution-name") or "").lower()
    if any(keyword in institution_name for keyword in MOROCCO_KEYWORDS):
        return True

    return False


def moroccan_origin_confidence(record: ExpertRecord) -> int:
    score = 0
    raw = record.raw if isinstance(record.raw, dict) else {}

    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []
    has_ma_affiliation = False
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        country_code = institution.get("country_code") if isinstance(institution.get("country_code"), str) else None
        if country_code and country_code.upper() == settings.target_country_code.upper():
            has_ma_affiliation = True
            break
    if has_ma_affiliation:
        score += 2

    orcid = raw.get("orcid") if isinstance(raw.get("orcid"), dict) else {}
    institution_name = str(orcid.get("institution-name") or "").lower()
    if any(keyword in institution_name for keyword in MOROCCO_KEYWORDS):
        score += 1

    full_name = (record.full_name or "").lower()
    name_tokens = [token for token in re.split(r"[^a-z]+", full_name) if token]
    if any(token in MOROCCAN_NAME_TOKENS for token in name_tokens):
        score += 1

    gh = raw.get("github") if isinstance(raw.get("github"), dict) else {}
    location = str(gh.get("location") or "").lower()
    if any(keyword in location for keyword in MOROCCO_KEYWORDS):
        score += 1

    return score


def is_moroccan_abroad(record: ExpertRecord) -> bool:
    country_code = (record.country_code or "").strip().upper()
    if not country_code:
        return False
    if country_code == settings.target_country_code.upper():
        return False
    if not has_moroccan_origin_signal(record):
        return False
    return moroccan_origin_confidence(record) >= 3


def has_moroccan_research_signal(record: ExpertRecord) -> bool:
    if (record.country_code or "").upper() == settings.target_country_code.upper():
        return True

    raw = record.raw if isinstance(record.raw, dict) else {}
    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []

    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        country_code = institution.get("country_code") if isinstance(institution.get("country_code"), str) else None
        if country_code and country_code.upper() == settings.target_country_code.upper():
            return True

    return False


def moroccan_affiliation_depth(record: ExpertRecord) -> tuple[int, int]:
    """(distinct years, distinct institutions) attached to Morocco in OpenAlex."""
    raw = record.raw if isinstance(record.raw, dict) else {}
    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []

    years: set[int] = set()
    institutions: set[str] = set()

    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        if str(institution.get("country_code") or "").upper() != settings.target_country_code.upper():
            continue

        institution_id = institution.get("id") or institution.get("display_name")
        if isinstance(institution_id, str) and institution_id:
            institutions.add(institution_id)

        for year in affiliation.get("years") or []:
            if isinstance(year, int):
                years.add(year)

    return len(years), len(institutions)


def has_substantial_moroccan_affiliation(record: ExpertRecord) -> bool:
    """Reject one-off Moroccan co-authorships.

    OpenAlex attaches an institution to an author for a single paper, so a foreign
    researcher who co-signed one article with a Moroccan lab shows up as
    "Moroccan-affiliated". A genuine profile is either currently based in Morocco,
    or has a Moroccan affiliation spanning several years / institutions.
    """
    if "openalex" not in record.sources:
        return True

    if _openalex_has_ma_in_last_known(record):
        return True

    years, institutions = moroccan_affiliation_depth(record)
    record.raw["moroccan_affiliation_years"] = years
    record.raw["moroccan_affiliation_institutions"] = institutions

    if institutions >= settings.min_moroccan_affiliation_institutions:
        return True
    return years >= settings.min_moroccan_affiliation_years


def _to_int(value: object, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _log_filter_step(label: str, before: int, after: int) -> None:
    removed = max(before - after, 0)
    print(f"[FILTER] {label}: kept={after}/{before}, removed={removed}")


def _contains_whitelisted_university(text: str | None) -> bool:
    normalized = (text or "").lower()
    if not normalized:
        return False
    return any(token in normalized for token in settings.moroccan_university_whitelist)


def _openalex_payload(record: ExpertRecord) -> dict[str, object]:
    raw = record.raw if isinstance(record.raw, dict) else {}
    payload = raw.get("openalex")
    return payload if isinstance(payload, dict) else {}


def _github_payload(record: ExpertRecord) -> dict[str, object]:
    raw = record.raw if isinstance(record.raw, dict) else {}
    payload = raw.get("github")
    return payload if isinstance(payload, dict) else {}


def _orcid_payload(record: ExpertRecord) -> dict[str, object]:
    raw = record.raw if isinstance(record.raw, dict) else {}
    payload = raw.get("orcid")
    return payload if isinstance(payload, dict) else {}


def _scholar_payload(record: ExpertRecord) -> dict[str, object]:
    raw = record.raw if isinstance(record.raw, dict) else {}
    payload = raw.get("scholar")
    return payload if isinstance(payload, dict) else {}


def _openalex_counts_by_year(record: ExpertRecord) -> list[dict[str, object]]:
    payload = _openalex_payload(record)
    counts = payload.get("counts_by_year") if isinstance(payload.get("counts_by_year"), list) else []
    return [item for item in counts if isinstance(item, dict)]


def compute_career_length(record: ExpertRecord) -> int:
    current_year = datetime.now().year
    counts_by_year = _openalex_counts_by_year(record)
    years = [
        _to_int(item.get("year"), 0)
        for item in counts_by_year
        if _to_int(item.get("works_count"), 0) > 0 and _to_int(item.get("year"), 0) > 0
    ]
    if not years:
        return 1
    first_publication_year = min(years)
    return max(current_year - first_publication_year, 1)


def compute_h_index_normalized(record: ExpertRecord) -> float:
    payload = _openalex_payload(record)
    summary_stats = payload.get("summary_stats") if isinstance(payload.get("summary_stats"), dict) else {}
    h_index = _to_float(summary_stats.get("h_index"), 0.0)
    return h_index / max(compute_career_length(record), 1)


def _openalex_has_ma_in_last_known(record: ExpertRecord) -> bool:
    payload = _openalex_payload(record)
    institutions = payload.get("last_known_institutions") if isinstance(payload.get("last_known_institutions"), list) else []
    for inst in institutions:
        if not isinstance(inst, dict):
            continue
        if str(inst.get("country_code") or "").upper() == settings.target_country_code.upper():
            return True
    return False


def _openalex_has_ma_affiliation_history(record: ExpertRecord) -> bool:
    payload = _openalex_payload(record)
    affiliations = payload.get("affiliations") if isinstance(payload.get("affiliations"), list) else []
    for affiliation in affiliations:
        if not isinstance(affiliation, dict):
            continue
        institution = affiliation.get("institution") if isinstance(affiliation.get("institution"), dict) else {}
        if str(institution.get("country_code") or "").upper() == settings.target_country_code.upper():
            return True
    return False


def openalex_recent_works_count(record: ExpertRecord) -> int:
    counts = _openalex_counts_by_year(record)
    current_year = datetime.now().year
    min_year = current_year - settings.openalex_recent_years_window
    return sum(
        _to_int(item.get("works_count"), 0)
        for item in counts
        if _to_int(item.get("year"), 0) >= min_year
    )


def openalex_recent_citations_5y(record: ExpertRecord) -> int:
    counts = _openalex_counts_by_year(record)
    current_year = datetime.now().year
    min_year = current_year - 5
    return sum(
        _to_int(item.get("cited_by_count"), 0)
        for item in counts
        if _to_int(item.get("year"), 0) >= min_year
    )


def _openalex_has_ai_topic_with_relevance(record: ExpertRecord) -> bool:
    payload = _openalex_payload(record)

    concepts = payload.get("x_concepts") if isinstance(payload.get("x_concepts"), list) else []
    for concept in concepts:
        if not isinstance(concept, dict):
            continue
        name = str(concept.get("display_name") or "").lower()
        score = _to_float(concept.get("score"), 0.0)
        if name in OPENALEX_AI_TOPICS and score >= settings.openalex_min_topic_relevance:
            return True

    # `x_concepts` is deprecated and empty on many authors; `topics` is the
    # current OpenAlex taxonomy, so fall back to it (AI subfield / AI keywords).
    topics = payload.get("topics") if isinstance(payload.get("topics"), list) else []
    for topic in topics:
        if not isinstance(topic, dict):
            continue
        subfield = topic.get("subfield") if isinstance(topic.get("subfield"), dict) else {}
        if str(subfield.get("display_name") or "").lower() in OPENALEX_AI_SUBFIELDS:
            return True
        name = str(topic.get("display_name") or "").lower()
        if any(keyword in name for keyword in OPENALEX_AI_TOPICS):
            return True

    return False


def filter_openalex(record: ExpertRecord) -> bool:
    if "openalex" not in record.sources:
        return True

    payload = _openalex_payload(record)
    works_count = _to_int(payload.get("works_count"), 0)
    summary_stats = payload.get("summary_stats") if isinstance(payload.get("summary_stats"), dict) else {}
    h_index = _to_int(summary_stats.get("h_index"), 0)

    record.raw["career_length"] = compute_career_length(record)
    record.raw["h_index_normalized"] = round(compute_h_index_normalized(record), 6)
    record.raw["recent_works_count"] = openalex_recent_works_count(record)
    record.raw["recent_citations_5y"] = openalex_recent_citations_5y(record)

    has_ma = _openalex_has_ma_in_last_known(record) or _openalex_has_ma_affiliation_history(record)
    has_moroccan_fallback = has_moroccan_signal(record)
    if not (has_ma or has_moroccan_fallback):
        return False
    if works_count < settings.openalex_min_works_count:
        return False
    if h_index < settings.openalex_min_h_index:
        return False
    if not _openalex_has_ai_topic_with_relevance(record):
        return False
    if openalex_recent_works_count(record) < settings.openalex_min_recent_works:
        return False
    return True


def _scholar_has_cross_id(record: ExpertRecord) -> bool:
    if not settings.scholar_require_cross_id:
        return True
    return bool(record.openalex_id or record.orcid_id)


def _scholar_affiliation_is_whitelisted(record: ExpertRecord) -> bool:
    payload = _scholar_payload(record)
    scholar_affiliation = str(payload.get("affiliation") or "")
    return _contains_whitelisted_university(scholar_affiliation)


def filter_scholar(record: ExpertRecord) -> bool:
    if "scholar" not in record.sources:
        return True

    payload = _scholar_payload(record)
    citations_total = _to_int(payload.get("citations_total"), 0)
    i10_index = _to_int(payload.get("i10_index"), 0)

    if citations_total < settings.scholar_min_citations_total:
        return False
    if i10_index < settings.scholar_min_i10_index:
        return False
    if not _scholar_has_cross_id(record):
        return False
    if not _scholar_affiliation_is_whitelisted(record):
        return False
    return True


def _orcid_records_country_values(payload: dict[str, object]) -> list[str]:
    countries: list[str] = []
    summaries = payload.get("employment-summary") if isinstance(payload.get("employment-summary"), list) else []
    summaries += payload.get("education-summary") if isinstance(payload.get("education-summary"), list) else []
    for item in summaries:
        if not isinstance(item, dict):
            continue
        organization = item.get("organization") if isinstance(item.get("organization"), dict) else {}
        address = organization.get("address") if isinstance(organization.get("address"), dict) else {}
        country = str(address.get("country") or "").upper()
        if country:
            countries.append(country)
    return countries


def filter_orcid(record: ExpertRecord) -> bool:
    if "orcid" not in record.sources:
        return True

    raw = record.raw if isinstance(record.raw, dict) else {}
    employment_payload = raw.get("orcid_employments") if isinstance(raw.get("orcid_employments"), dict) else {}
    education_payload = raw.get("orcid_educations") if isinstance(raw.get("orcid_educations"), dict) else {}
    countries = _orcid_records_country_values(employment_payload) + _orcid_records_country_values(education_payload)

    if not countries:
        return False
    return settings.target_country_code.upper() in countries


def filter_github(record: ExpertRecord) -> bool:
    if "github" not in record.sources:
        return True

    payload = _github_payload(record)
    account_age_years = _to_float(payload.get("account_age_years"), 0.0)
    ai_topic_repo_count = _to_int(payload.get("ai_topic_repo_count"), 0)
    notable_repo_contrib_count = _to_int(payload.get("notable_repo_contrib_count"), 0)
    has_moroccan_signal = bool(payload.get("has_moroccan_signal"))

    if account_age_years < settings.github_min_account_age_years:
        return False
    if settings.github_require_ai_topic_repo and ai_topic_repo_count < 1:
        return False
    # Contributing to pytorch/tensorflow/... is an extremely rare signal, and it is
    # only observable through the last 100 public events, so it rejects virtually
    # every real profile. Kept as an opt-in boost criterion, not a hard gate.
    if settings.github_require_notable_repo and notable_repo_contrib_count < 1:
        return False
    if settings.github_require_moroccan_signal and not has_moroccan_signal:
        return False

    # Without any of the strict gates, still require an AI signal in the profile
    # so that GitHub does not flood the pipeline with unrelated developers.
    if not settings.github_require_ai_topic_repo and ai_topic_repo_count < 1:
        if not is_ai_expert(record):
            return False
    return True


def filter_orcid_join_only(record: ExpertRecord) -> bool:
    return not (record.sources == {"orcid"})


def _apply_step(records: list[ExpertRecord], label: str, predicate) -> tuple[list[ExpertRecord], list[ExpertRecord]]:
    before = len(records)
    kept: list[ExpertRecord] = []
    rejected: list[ExpertRecord] = []
    for record in records:
        if predicate(record):
            kept.append(record)
            continue
        failures = record.raw.setdefault("filter_failures", [])
        if isinstance(failures, list):
            failures.append(label)
        record.raw["excluded_by"] = label
        rejected.append(record)
    _log_filter_step(label, before, len(kept))
    return kept, rejected


def apply_business_filters_with_rejections(records: list[ExpertRecord]) -> tuple[list[ExpertRecord], list[ExpertRecord]]:
    filtered = records
    rejected: list[ExpertRecord] = []

    filtered, dropped = _apply_step(filtered, "orcid-join-only", filter_orcid_join_only)
    rejected.extend(dropped)
    filtered, dropped = _apply_step(filtered, "openalex", filter_openalex)
    rejected.extend(dropped)
    filtered, dropped = _apply_step(filtered, "orcid-country", filter_orcid)
    rejected.extend(dropped)
    filtered, dropped = _apply_step(filtered, "scholar", filter_scholar)
    rejected.extend(dropped)
    filtered, dropped = _apply_step(filtered, "github", filter_github)
    rejected.extend(dropped)

    if settings.ai_only:
        filtered, dropped = _apply_step(filtered, "ai-only", is_ai_expert)
        rejected.extend(dropped)

    if settings.require_moroccan_signal:
        filtered, dropped = _apply_step(filtered, "moroccan-signal", has_moroccan_signal)
        rejected.extend(dropped)
        filtered, dropped = _apply_step(
            filtered, "moroccan-affiliation-depth", has_substantial_moroccan_affiliation
        )
        rejected.extend(dropped)

    if settings.diaspora_only:
        filtered, dropped = _apply_step(filtered, "diaspora-only", is_moroccan_abroad)
        rejected.extend(dropped)

    if settings.require_seniority:
        filtered, dropped = _apply_step(filtered, "seniority", is_senior_expert)
        rejected.extend(dropped)

    filtered, dropped = _apply_step(
        filtered,
        f"min-score>={settings.min_elite_score}",
        lambda r: r.score >= settings.min_elite_score,
    )
    rejected.extend(dropped)

    return filtered, rejected


def apply_target_domain_business_filters_with_rejections(records: list[ExpertRecord]) -> tuple[list[ExpertRecord], list[ExpertRecord]]:
    filtered, rejected = apply_business_filters_with_rejections(records)

    filtered, dropped = _apply_step(filtered, "target-ai-domains", matches_target_ai_domains)
    rejected.extend(dropped)

    if settings.require_moroccan_signal:
        filtered, dropped = _apply_step(filtered, "moroccan-research-signal", has_moroccan_research_signal)
        rejected.extend(dropped)

    if settings.diaspora_only:
        filtered, dropped = _apply_step(filtered, "diaspora-only-target", is_moroccan_abroad)
        rejected.extend(dropped)

    if settings.require_seniority:
        filtered, dropped = _apply_step(filtered, "seniority-target", is_senior_expert)
        rejected.extend(dropped)

    filtered, dropped = _apply_step(
        filtered,
        f"min-score-target>={settings.min_elite_score}",
        lambda r: r.score >= settings.min_elite_score,
    )
    rejected.extend(dropped)

    return filtered, rejected


def is_senior_expert(record: ExpertRecord) -> bool:
    raw = record.raw if isinstance(record.raw, dict) else {}
    openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
    gh = raw.get("github") if isinstance(raw.get("github"), dict) else {}

    works_count = _to_int(openalex.get("works_count"), 0)
    cited_by_count = _to_int(openalex.get("cited_by_count"), 0)
    h_index = _to_int((openalex.get("summary_stats") or {}).get("h_index"), 0)

    followers = _to_int(gh.get("followers"), 0)
    public_repos = _to_int(gh.get("public_repos"), 0)

    strong_research = (
        works_count >= settings.min_works_count and h_index >= settings.min_h_index
    )
    strong_citations = cited_by_count >= settings.min_citations
    strong_engineering = (
        followers >= settings.min_github_followers and public_repos >= settings.min_github_repos
    )

    return strong_research or strong_citations or strong_engineering


def apply_business_filters(records: list[ExpertRecord]) -> list[ExpertRecord]:
    filtered, _ = apply_business_filters_with_rejections(records)
    return filtered


def apply_target_domain_business_filters(records: list[ExpertRecord]) -> list[ExpertRecord]:
    filtered, _ = apply_target_domain_business_filters_with_rejections(records)
    return filtered
