from __future__ import annotations

import json
from pathlib import Path

import requests
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Domain
from app.models.talent import Talent, TalentDomain, TalentUniversity
from app.models.university import University

OPENALEX_API = "https://api.openalex.org"
REQUEST_TIMEOUT_SECONDS = 20
FEATURED_SCORE_THRESHOLD = 0.65


def _slugify(name: str) -> str:
    return "-".join(name.strip().lower().split())


def _parse_country(record: dict[str, object]) -> str | None:
    code = record.get("country_code")
    if isinstance(code, str) and code.strip():
        return code.strip().upper()
    return None


def _extract_city_from_location(location: object) -> str | None:
    if not isinstance(location, str):
        return None
    text = location.strip()
    if not text:
        return None

    # Prefer city part when location is written as "City, Country".
    if "," in text:
        city = text.split(",", 1)[0].strip()
        return city or None

    return text


def _normalize_orcid(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("http"):
        return raw
    return f"https://orcid.org/{raw}"


def _extract_linkedin(blog_value: object) -> str | None:
    if not isinstance(blog_value, str):
        return None
    text = blog_value.strip()
    if not text:
        return None
    return text if "linkedin.com" in text.lower() else None


def _extract_website(blog_value: object) -> str | None:
    if not isinstance(blog_value, str):
        return None
    text = blog_value.strip()
    if not text:
        return None
    if text.lower() in {"null", "none", "n/a"}:
        return None
    if "linkedin.com" in text.lower():
        return None
    if text.startswith("http://") or text.startswith("https://"):
        return text
    if "." in text and " " not in text:
        return f"https://{text}"
    return None


def _normalize_scholar(value: object) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    return f"https://scholar.google.com/citations?user={raw}"


def _openalex_institution_city(institution_id: str, cache: dict[str, str | None]) -> str | None:
    if institution_id in cache:
        return cache[institution_id]

    short_id = institution_id.rsplit("/", 1)[-1].strip()
    if not short_id:
        cache[institution_id] = None
        return None

    try:
        response = requests.get(
            f"{OPENALEX_API}/institutions/{short_id}",
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            cache[institution_id] = None
            return None

        payload = response.json()
        geo = payload.get("geo") if isinstance(payload, dict) else {}
        city = geo.get("city") if isinstance(geo, dict) else None
        value = city.strip() if isinstance(city, str) and city.strip() else None
        cache[institution_id] = value
        return value
    except requests.RequestException:
        cache[institution_id] = None
        return None


def _institution_city(institution: object, cache: dict[str, str | None]) -> str | None:
    if not isinstance(institution, dict):
        return None

    geo = institution.get("geo") if isinstance(institution.get("geo"), dict) else {}
    city = geo.get("city") if isinstance(geo, dict) else None
    if isinstance(city, str) and city.strip():
        return city.strip()

    inst_id = institution.get("id") if isinstance(institution.get("id"), str) else None
    if inst_id:
        return _openalex_institution_city(inst_id, cache)
    return None


def _extract_city_from_openalex(openalex: dict[str, object], cache: dict[str, str | None]) -> str | None:
    """City of the institution the talent is currently attached to.

    `affiliations` is not sorted by recency, so scanning it from the top listed
    people under a city they left years ago.
    """
    last_known = openalex.get("last_known_institutions") if isinstance(openalex.get("last_known_institutions"), list) else []
    if last_known:
        city = _institution_city(last_known[0], cache)
        if city:
            return city

    affiliations = openalex.get("affiliations") if isinstance(openalex.get("affiliations"), list) else []
    ordered = sorted(
        (affiliation for affiliation in affiliations if isinstance(affiliation, dict)),
        key=lambda affiliation: max(
            (year for year in (affiliation.get("years") or []) if isinstance(year, int)),
            default=0,
        ),
        reverse=True,
    )
    for affiliation in ordered:
        city = _institution_city(affiliation.get("institution"), cache)
        if city:
            return city

    return None


def seed_talents_from_etl_json(db: Session, json_path: str) -> dict[str, int]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {json_path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValueError("ETL JSON must be a list of records")

    # Bulk-deleting talents does not cascade through the secondary tables in the
    # ORM, so stale association rows survive and collide with the reused primary
    # keys of the freshly inserted talents.
    db.query(TalentDomain).delete()
    db.query(TalentUniversity).delete()
    db.query(Talent).delete()
    db.flush()

    created_talents = 0
    created_domains = 0
    created_universities = 0
    institution_city_cache: dict[str, str | None] = {}

    for item in payload:
        if not isinstance(item, dict):
            continue

        raw = item.get("raw") if isinstance(item.get("raw"), dict) else {}
        github = raw.get("github") if isinstance(raw.get("github"), dict) else {}
        openalex = raw.get("openalex") if isinstance(raw.get("openalex"), dict) else {}
        summary = openalex.get("summary_stats") if isinstance(openalex.get("summary_stats"), dict) else {}

        city = _extract_city_from_location(github.get("location"))
        if not city:
            city = _extract_city_from_openalex(openalex, institution_city_cache)
        photo_url = github.get("avatar_url") if isinstance(github.get("avatar_url"), str) else None
        email = github.get("email") if isinstance(github.get("email"), str) else None
        linkedin = _extract_linkedin(github.get("blog"))
        website_url = _extract_website(github.get("blog"))
        openalex_url = item.get("openalex_id") if isinstance(item.get("openalex_id"), str) else None
        orcid_url = _normalize_orcid(item.get("orcid_id") or openalex.get("orcid"))
        scholar_url = _normalize_scholar(item.get("scholar_id"))

        talent = Talent(
            full_name=str(item.get("full_name") or "Unknown"),
            photo_url=photo_url,
            country=_parse_country(item),
            city=city,
            organization=str(item.get("primary_affiliation") or "") or None,
            bio=str(github.get("bio") or "") or None,
            email=email,
            linkedin=linkedin,
            website_url=website_url,
            github_url=str(item.get("github_url") or github.get("html_url") or "") or None,
            orcid_url=orcid_url,
            openalex_url=openalex_url,
            scholar_url=scholar_url,
            publications=int(openalex.get("works_count") or 0),
            h_index=int(summary.get("h_index") or 0),
            citations=int(openalex.get("cited_by_count") or 0),
            score=float(item.get("score") or 0),
            tier=str(raw.get("tier") or "") or None,
            ai_purity=float(raw.get("ai_purity") or 0),
            # The ETL score is normalized to 0..1, so the old `>= 90` test could
            # never be true. The pipeline's tier is the meaningful signal here.
            featured=str(raw.get("tier") or "") == "Elite"
            or float(item.get("score") or 0) >= FEATURED_SCORE_THRESHOLD,
            source=",".join(sorted(item.get("sources") or [])),
        )
        db.add(talent)

        domains = item.get("domains") if isinstance(item.get("domains"), list) else []
        domain_names: list[str] = []
        seen_domain_slugs: set[str] = set()
        for domain_value in domains:
            name = str(domain_value).strip()
            if not name:
                continue
            slug = _slugify(name)
            if slug in seen_domain_slugs:
                continue
            seen_domain_slugs.add(slug)
            domain_names.append(name)
        talent.skills_text = ", ".join(domain_names) if domain_names else None

        for domain_name in domain_names:
            slug = _slugify(domain_name)
            existing_domain = db.scalar(select(Domain).where(Domain.slug == slug))
            if not existing_domain:
                existing_domain = db.scalar(select(Domain).where(Domain.name == domain_name))
            if not existing_domain:
                existing_domain = Domain(name=domain_name, slug=slug)
                db.add(existing_domain)
                db.flush()
                created_domains += 1
            talent.domains.append(existing_domain)

        if talent.organization:
            uni_name = talent.organization
            existing_uni = db.scalar(select(University).where(University.name == uni_name))
            if not existing_uni:
                existing_uni = University(name=uni_name, country_code=talent.country)
                db.add(existing_uni)
                db.flush()
                created_universities += 1
            talent.universities.append(existing_uni)
        created_talents += 1

    db.commit()

    return {
        "talents": created_talents,
        "domains": created_domains,
        "universities": created_universities,
    }
