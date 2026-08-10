from __future__ import annotations

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
