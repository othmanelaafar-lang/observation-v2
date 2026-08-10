from __future__ import annotations

from datetime import datetime, timezone

import requests
from requests import RequestException

from etl.config import settings
from etl.models import ExpertRecord

GITHUB_API = "https://api.github.com"

DOMAIN_LABELS = {
    "machine learning": "Machine Learning",
    "deep learning": "Deep Learning",
    "natural language processing": "Natural Language Processing",
    "data science": "Data Science",
    "data analyst": "Data Analyst",
    "data analysis": "Data Analysis",
}


def _safe_get_json(
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, object] | None = None,
) -> dict[str, object] | list[object] | None:
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=settings.request_timeout)
    except RequestException as exc:
        print(f"[WARN] GitHub request failed for '{url}': {exc}")
        return None

    if resp.status_code == 403:
        print("[WARN] GitHub rate limit reached (403). Returning partial GitHub results.")
        return None

    if resp.status_code >= 400:
        return None

    payload = resp.json()
    if isinstance(payload, (dict, list)):
        return payload
    return None


def _email_domain(email: str | None) -> str | None:
    if not email or "@" not in email:
        return None
    return email.rsplit("@", 1)[-1].strip().lower() or None


def _account_age_years(created_at: str | None) -> float:
    if not created_at:
        return 0.0
    try:
        created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    now = datetime.now(timezone.utc)
    return max((now - created).days / 365.25, 0.0)


def _has_moroccan_signal(location: str | None, email: str | None) -> bool:
    location_text = (location or "").lower()
    if any(token in location_text for token in settings.moroccan_location_tokens):
        return True

    domain = _email_domain(email)
    if not domain:
        return False
    return any(domain.endswith(allowed) for allowed in settings.moroccan_email_domains)


def _fetch_user_repos(login: str, headers: dict[str, str]) -> list[dict[str, object]]:
    payload = _safe_get_json(
        f"{GITHUB_API}/users/{login}/repos",
        headers=headers,
        params={"per_page": 100, "sort": "updated"},
    )
    if isinstance(payload, list):
        return [repo for repo in payload if isinstance(repo, dict)]
    return []


def _count_ai_topic_repos(repos: list[dict[str, object]]) -> int:
    allowed = {topic.lower() for topic in settings.github_ai_topics}
    count = 0
    for repo in repos:
        topics = repo.get("topics") if isinstance(repo.get("topics"), list) else []
        topic_set = {str(topic).lower() for topic in topics}
        if topic_set.intersection(allowed):
            count += 1
    return count


def _count_notable_repo_contributions(login: str, headers: dict[str, str]) -> int:
    payload = _safe_get_json(
        f"{GITHUB_API}/users/{login}/events/public",
        headers=headers,
        params={"per_page": 100},
    )
    if not isinstance(payload, list):
        return 0

    notable = {repo.lower() for repo in settings.github_notable_repos}
    touched: set[str] = set()
    for event in payload:
        if not isinstance(event, dict):
            continue
        repo_obj = event.get("repo") if isinstance(event.get("repo"), dict) else {}
        full_name = str(repo_obj.get("name") or "").lower()
        if full_name in notable:
            touched.add(full_name)
    return len(touched)


def _match_domains(text: str) -> list[str]:
    normalized = text.lower()
    found = {
        label
        for keyword, label in DOMAIN_LABELS.items()
        if keyword in normalized
    }
    if "ml" in normalized:
        found.add("Machine Learning")
    if "nlp" in normalized:
        found.add("Natural Language Processing")
    return sorted(found)


def fetch_github_experts() -> list[ExpertRecord]:
    headers = {"Accept": "application/vnd.github+json"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"

    experts: list[ExpertRecord] = []
    seen_logins: set[str] = set()
    stop_due_to_rate_limit = False

    queries = [f"location:{settings.target_country_name}"]
    for domain in settings.target_ai_domains:
        queries.extend(
            [
                f"moroccan {domain}",
                f"maroc {domain}",
                f"location:Morocco {domain}",
            ]
        )

    for query in queries:
        if stop_due_to_rate_limit:
            break
        for page in range(1, settings.max_pages + 1):
            params = {
                "q": query,
                "type": "Users",
                "per_page": settings.page_size,
                "page": page,
            }
            payload = _safe_get_json(
                f"{GITHUB_API}/search/users",
                headers=headers,
                params=params,
            )
            if not isinstance(payload, dict):
                stop_due_to_rate_limit = True
                break

            items = payload.get("items", []) if isinstance(payload.get("items"), list) else []
            if not items:
                break

            for user in items:
                if not isinstance(user, dict):
                    continue
                login = user.get("login")
                if not login:
                    continue
                if login.lower() in seen_logins:
                    continue

                profile_payload = _safe_get_json(
                    f"{GITHUB_API}/users/{login}",
                    headers=headers,
                )
                if not isinstance(profile_payload, dict):
                    continue

                profile = profile_payload
                name = profile.get("name") or login
                bio = profile.get("bio") or ""
                company = profile.get("company")
                location_raw = profile.get("location")
                email_raw = profile.get("email")

                repos = _fetch_user_repos(login, headers)
                ai_topic_repo_count = _count_ai_topic_repos(repos)
                notable_repo_contrib_count = _count_notable_repo_contributions(login, headers)
                age_years = _account_age_years(str(profile.get("created_at") or ""))
                has_moroccan_signal = _has_moroccan_signal(
                    str(location_raw or ""),
                    str(email_raw or ""),
                )

                about_text = " ".join(
                    [
                        str(name or ""),
                        str(bio or ""),
                        str(company or ""),
                        str(profile.get("blog") or ""),
                        " ".join(
                            ",".join(str(topic) for topic in (repo.get("topics") or []))
                            for repo in repos
                            if isinstance(repo, dict)
                        ),
                    ]
                )
                matched_domains = _match_domains(about_text)

                location = str(location_raw or "").lower()
                country_code = settings.target_country_code if any(
                    token in location for token in settings.moroccan_location_tokens
                ) else None

                profile["notable_repo_contrib_count"] = notable_repo_contrib_count
                profile["ai_topic_repo_count"] = ai_topic_repo_count
                profile["account_age_years"] = round(age_years, 2)
                profile["has_moroccan_signal"] = has_moroccan_signal

                experts.append(
                    ExpertRecord(
                        full_name=name,
                        primary_affiliation=company,
                        country_code=country_code,
                        domains=matched_domains,
                        github_login=login,
                        github_url=profile.get("html_url"),
                        source_rank=float(profile.get("public_repos") or 0),
                        sources={"github"},
                        raw={"github": profile},
                    )
                )
                seen_logins.add(login.lower())

    return experts
