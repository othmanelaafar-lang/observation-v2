from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_list(value: str | None, default: list[str]) -> list[str]:
    if value is None:
        return default
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or default


@dataclass(frozen=True)
class Settings:
    database_url: str
    github_token: str | None
    target_country_code: str
    target_country_name: str
    page_size: int
    max_pages: int
    enable_orcid: bool
    enable_scholar: bool
    request_timeout: int
    target_ai_domains: list[str]
    ai_only: bool
    diaspora_only: bool
    require_moroccan_signal: bool
    min_moroccan_affiliation_years: int
    min_moroccan_affiliation_institutions: int
    min_elite_score: float
    require_seniority: bool
    min_works_count: int
    min_h_index: int
    min_citations: int
    min_github_followers: int
    min_github_repos: int
    openalex_min_works_count: int
    openalex_min_h_index: int
    openalex_min_topic_relevance: float
    openalex_recent_years_window: int
    openalex_min_recent_works: int
    openalex_mailto: str | None
    openalex_max_retries: int
    openalex_retry_backoff_seconds: int
    openalex_ai_topic_ids: list[str]
    openalex_max_target_authors: int
    github_require_ai_topic_repo: bool
    github_require_notable_repo: bool
    github_require_moroccan_signal: bool
    github_fetch_events: bool
    github_max_profiles: int
    scholar_min_citations_total: int
    scholar_min_i10_index: int
    scholar_require_cross_id: bool
    github_min_account_age_years: int
    github_ai_topics: list[str]
    github_notable_repos: list[str]
    moroccan_university_whitelist: list[str]
    moroccan_location_tokens: list[str]
    moroccan_email_domains: list[str]
    dedupe_match_threshold: int
    score_weight_hindex_norm: float
    score_weight_notable_repos: float
    score_weight_recent_citations: float
    score_weight_institution_recognition: float
    ai_subfield_ids: list[str]
    min_ai_purity: float
    min_ai_purity_floor: float
    min_ai_works: int
    tier_elite_min_h_index: int
    tier_elite_min_ai_purity: float
    tier_elite_min_ai_works: int
    tier_elite_min_recent_works: int
    tier_confirme_min_h_index: int
    tier_emergent_min_h_index: int
    enable_orcid_enrichment: bool
    orcid_enrichment_sleep_seconds: float
    scholar_dataset_path: str
    rejected_profiles_csv_path: str
    review_queue_csv_path: str


settings = Settings(
    database_url=os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/observatoire_ia"),
    github_token=os.getenv("GITHUB_TOKEN") or None,
    target_country_code=os.getenv("TARGET_COUNTRY_CODE", "MA"),
    target_country_name=os.getenv("TARGET_COUNTRY_NAME", "Morocco"),
    page_size=int(os.getenv("PAGE_SIZE", "50")),
    max_pages=int(os.getenv("MAX_PAGES", "2")),
    enable_orcid=_to_bool(os.getenv("ENABLE_ORCID"), False),
    enable_scholar=_to_bool(os.getenv("ENABLE_SCHOLAR"), False),
    request_timeout=int(os.getenv("REQUEST_TIMEOUT", "20")),
    target_ai_domains=_to_list(
        os.getenv("TARGET_AI_DOMAINS"),
        [
            "machine learning",
            "deep learning",
            "natural language processing",
            "data science",
            "data analyst",
            "data analysis",
        ],
    ),
    ai_only=_to_bool(os.getenv("AI_ONLY"), True),
    diaspora_only=_to_bool(os.getenv("DIASPORA_ONLY"), False),
    require_moroccan_signal=_to_bool(os.getenv("REQUIRE_MOROCCAN_SIGNAL"), True),
    min_moroccan_affiliation_years=int(os.getenv("MIN_MOROCCAN_AFFILIATION_YEARS", "2")),
    min_moroccan_affiliation_institutions=int(os.getenv("MIN_MOROCCAN_AFFILIATION_INSTITUTIONS", "2")),
    min_elite_score=float(os.getenv("MIN_ELITE_SCORE", "0.1")),
    require_seniority=_to_bool(os.getenv("REQUIRE_SENIORITY"), False),
    min_works_count=int(os.getenv("MIN_WORKS_COUNT", "30")),
    min_h_index=int(os.getenv("MIN_H_INDEX", "10")),
    min_citations=int(os.getenv("MIN_CITATIONS", "300")),
    min_github_followers=int(os.getenv("MIN_GITHUB_FOLLOWERS", "30")),
    min_github_repos=int(os.getenv("MIN_GITHUB_REPOS", "10")),
    openalex_min_works_count=int(os.getenv("OPENALEX_MIN_WORKS_COUNT", "3")),
    openalex_min_h_index=int(os.getenv("OPENALEX_MIN_H_INDEX", "3")),
    openalex_min_topic_relevance=float(os.getenv("OPENALEX_MIN_TOPIC_RELEVANCE", "0.15")),
    openalex_recent_years_window=int(os.getenv("OPENALEX_RECENT_YEARS_WINDOW", "5")),
    openalex_min_recent_works=int(os.getenv("OPENALEX_MIN_RECENT_WORKS", "1")),
    openalex_mailto=os.getenv("OPENALEX_MAILTO") or None,
    openalex_max_retries=int(os.getenv("OPENALEX_MAX_RETRIES", "3")),
    openalex_retry_backoff_seconds=int(os.getenv("OPENALEX_RETRY_BACKOFF_SECONDS", "5")),
    openalex_ai_topic_ids=_to_list(os.getenv("OPENALEX_AI_TOPIC_IDS"), []),
    openalex_max_target_authors=int(os.getenv("OPENALEX_MAX_TARGET_AUTHORS", "400")),
    github_require_ai_topic_repo=_to_bool(os.getenv("GITHUB_REQUIRE_AI_TOPIC_REPO"), False),
    github_require_notable_repo=_to_bool(os.getenv("GITHUB_REQUIRE_NOTABLE_REPO"), False),
    github_require_moroccan_signal=_to_bool(os.getenv("GITHUB_REQUIRE_MOROCCAN_SIGNAL"), True),
    github_fetch_events=_to_bool(os.getenv("GITHUB_FETCH_EVENTS"), False),
    github_max_profiles=int(os.getenv("GITHUB_MAX_PROFILES", "60")),
    scholar_min_citations_total=int(os.getenv("SCHOLAR_MIN_CITATIONS_TOTAL", "100")),
    scholar_min_i10_index=int(os.getenv("SCHOLAR_MIN_I10_INDEX", "3")),
    scholar_require_cross_id=_to_bool(os.getenv("SCHOLAR_REQUIRE_CROSS_ID"), True),
    github_min_account_age_years=int(os.getenv("GITHUB_MIN_ACCOUNT_AGE_YEARS", "0")),
    github_ai_topics=_to_list(
        os.getenv("GITHUB_AI_TOPICS"),
        [
            "machine-learning",
            "deep-learning",
            "nlp",
            "computer-vision",
            "artificial-intelligence",
        ],
    ),
    github_notable_repos=_to_list(
        os.getenv("GITHUB_NOTABLE_REPOS"),
        [
            "pytorch/pytorch",
            "huggingface/transformers",
            "tensorflow/tensorflow",
            "scikit-learn/scikit-learn",
            "langchain-ai/langchain",
            "ollama/ollama",
        ],
    ),
    moroccan_university_whitelist=_to_list(
        os.getenv("MOROCCAN_UNIVERSITY_WHITELIST"),
        [
            "um6p",
            "ensias",
            "al akhawayn",
            "emi",
            "inpt",
            "uir",
            "ensam",
            "fst",
            "universite hassan ii",
            "universite mohammed v",
            "universite mohamed v",
            "universite mohammed 5",
        ],
    ),
    moroccan_location_tokens=_to_list(
        os.getenv("MOROCCAN_LOCATION_TOKENS"),
        [
            "morocco",
            "maroc",
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
        ],
    ),
    moroccan_email_domains=_to_list(
        os.getenv("MOROCCAN_EMAIL_DOMAINS"),
        [
            "um6p.ma",
            "ensias.um5.ac.ma",
            "emi.ac.ma",
            "inpt.ac.ma",
            "uir.ac.ma",
            "uir.ma",
            "usmba.ac.ma",
            "uh2c.ac.ma",
            "um5.ac.ma",
            "uca.ma",
            "uae.ac.ma",
        ],
    ),
    dedupe_match_threshold=int(os.getenv("DEDUPE_MATCH_THRESHOLD", "3")),
    score_weight_hindex_norm=float(os.getenv("SCORE_WEIGHT_HINDEX_NORM", "0.35")),
    score_weight_notable_repos=float(os.getenv("SCORE_WEIGHT_NOTABLE_REPOS", "0.25")),
    score_weight_recent_citations=float(os.getenv("SCORE_WEIGHT_RECENT_CITATIONS", "0.2")),
    score_weight_institution_recognition=float(os.getenv("SCORE_WEIGHT_INSTITUTION_RECOGNITION", "0.2")),
    # OpenAlex subfields 1702 (Artificial Intelligence) and 1707 (Computer Vision
    # and Pattern Recognition) cover ML / DL / NLP / CV / RL as one family.
    ai_subfield_ids=_to_list(os.getenv("AI_SUBFIELD_IDS"), ["1702", "1707"]),
    min_ai_purity=float(os.getenv("MIN_AI_PURITY", "0.25")),
    min_ai_purity_floor=float(os.getenv("MIN_AI_PURITY_FLOOR", "0.1")),
    min_ai_works=int(os.getenv("MIN_AI_WORKS", "20")),
    tier_elite_min_h_index=int(os.getenv("TIER_ELITE_MIN_H_INDEX", "40")),
    tier_elite_min_ai_purity=float(os.getenv("TIER_ELITE_MIN_AI_PURITY", "0.5")),
    tier_elite_min_ai_works=int(os.getenv("TIER_ELITE_MIN_AI_WORKS", "50")),
    tier_elite_min_recent_works=int(os.getenv("TIER_ELITE_MIN_RECENT_WORKS", "1")),
    tier_confirme_min_h_index=int(os.getenv("TIER_CONFIRME_MIN_H_INDEX", "25")),
    tier_emergent_min_h_index=int(os.getenv("TIER_EMERGENT_MIN_H_INDEX", "10")),
    enable_orcid_enrichment=_to_bool(os.getenv("ENABLE_ORCID_ENRICHMENT"), True),
    orcid_enrichment_sleep_seconds=float(os.getenv("ORCID_ENRICHMENT_SLEEP_SECONDS", "0.2")),
    scholar_dataset_path=os.getenv("SCHOLAR_DATASET_PATH", "etl/input/scholar_profiles.json"),
    rejected_profiles_csv_path=os.getenv("REJECTED_PROFILES_CSV_PATH", ""),
    review_queue_csv_path=os.getenv("REVIEW_QUEUE_CSV_PATH", ""),
)
