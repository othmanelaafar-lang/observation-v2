"""Offline validation of the pipeline - run this before spending OpenAlex budget.

OpenAlex bills every request against a daily quota that resets at midnight UTC.
Discovering a broken install *after* the quota is gone costs a day, so this
script exercises everything that can be checked without paying: imports,
configuration, the scoring and origin logic (replayed against stored payloads),
and the ORCID half of discovery, which is free and unmetered.

    python -m etl.selfcheck

Exit code 0 means the machine is ready for a real run.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from etl.models import ExpertRecord

FIXTURE = Path("etl/fixtures/origin_cases.json")

failures: list[str] = []
notes: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'OK ' if ok else 'FAIL'}] {label}{f' - {detail}' if detail else ''}")
    if not ok:
        failures.append(label)
    return ok


def _record_from_fixture(case: dict) -> ExpertRecord:
    return ExpertRecord(
        full_name=case["full_name"],
        primary_affiliation=case.get("primary_affiliation"),
        country_code=case.get("country_code"),
        domains=case.get("domains") or [],
        openalex_id=case.get("openalex_id"),
        sources={"openalex"},
        raw=case["raw"],
    )


def check_imports() -> None:
    print("\n1. Modules and configuration")
    from etl import filters, pipeline  # noqa: F401
    from etl.config import settings
    from etl.sources import openalex_api, orcid_api, orcid_discovery  # noqa: F401

    check("every module imports", True)
    check(
        "AI subfields configured",
        len(settings.ai_subfield_ids) > 0,
        f"{settings.ai_subfield_ids}",
    )
    check(
        "ORCID institutions configured",
        len(settings.orcid_search_institutions) >= 10,
        f"{len(settings.orcid_search_institutions)} establishments",
    )
    if not settings.openalex_mailto:
        notes.append(
            "OPENALEX_MAILTO is empty. Set it in etl/.env to join the polite pool "
            "(faster, more reliable). It does not raise the daily budget."
        )


def check_cache() -> None:
    print("\n2. OpenAlex response cache")
    from etl.config import settings
    from etl.sources.openalex_api import _cache_key, _cache_read, _cache_write

    if not settings.openalex_cache_enabled:
        notes.append(
            "OPENALEX_CACHE_ENABLED is false. Every rerun will re-spend the daily "
            "budget on data already downloaded."
        )
        check("cache enabled", False, "set OPENALEX_CACHE_ENABLED=true")
        return

    probe = {"filter": "selfcheck-probe"}
    key = _cache_key("/selfcheck", probe)
    _cache_write(key, {"ok": True})
    check("writes and reads back", _cache_read(key) == {"ok": True})
    check(
        "mailto excluded from the key",
        _cache_key("/selfcheck", probe) == _cache_key("/selfcheck", {**probe, "mailto": "a@b.c"}),
    )
    entry = Path(settings.openalex_cache_dir) / f"{key}.json"
    entry.unlink(missing_ok=True)


def check_origin_logic() -> None:
    """Replay the diaspora rules against hand-labelled real profiles."""
    print("\n3. Origin routing (replayed offline)")
    from etl.filters import ORIGIN_REJECT, origin_verdict

    if not FIXTURE.exists():
        check("fixture present", False, f"{FIXTURE} missing")
        return

    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    wrong: list[str] = []
    for case in cases:
        record = _record_from_fixture(case)
        actual = origin_verdict(record)
        if actual != case["expected_verdict"]:
            wrong.append(f"{case['full_name']}: expected {case['expected_verdict']}, got {actual}")

    check(f"{len(cases)} labelled profiles routed correctly", not wrong)
    for line in wrong:
        print(f"         {line}")

    residents = [c for c in cases if c.get("based_in_morocco")]
    if residents:
        still_in = [
            c["full_name"]
            for c in residents
            if origin_verdict(_record_from_fixture(c)) != ORIGIN_REJECT
        ]
        check("researchers based in Morocco are excluded", not still_in, ", ".join(still_in))


def check_scoring() -> None:
    print("\n4. AI focus and tiering (replayed offline)")
    from etl.config import settings
    from etl.filters import ai_purity, ai_works_count, is_ai_focused, openalex_h_index
    from etl.pipeline import assign_tier

    if not FIXTURE.exists():
        return

    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))
    for case in cases:
        if "expected_tier" not in case:
            continue
        record = _record_from_fixture(case)
        tier = assign_tier(record)
        check(
            f"{case['full_name']} -> {case['expected_tier']}",
            tier == case["expected_tier"],
            f"h={openalex_h_index(record)} purity={ai_purity(record):.3f} "
            f"ai_works={ai_works_count(record)} got={tier}",
        )

    # The volume fallback is what admits cross-disciplinary AI researchers whose
    # share looks low because their work is filed under another subfield.
    borderline = [c for c in cases if c.get("tests_volume_fallback")]
    for case in borderline:
        record = _record_from_fixture(case)
        check(
            f"volume fallback admits {case['full_name']}",
            is_ai_focused(record, settings.min_ai_purity, settings.min_ai_works),
            f"purity={ai_purity(record):.3f} < {settings.min_ai_purity} "
            f"but ai_works={ai_works_count(record)}",
        )


def check_orcid_live() -> None:
    """ORCID is free and unmetered, so this half can be proven for real."""
    print("\n5. ORCID discovery (live, free)")
    from etl.sources.orcid_discovery import _orcid_search

    payload = _orcid_search('past-institution-affiliation-name:"Cadi Ayyad University"', 0, 5)
    if payload is None:
        check("ORCID reachable", False, "no response - check the network")
        return
    found = payload.get("num-found") or 0
    check("ORCID reachable and returning people", found > 100, f"{found} past affiliates")


def main() -> int:
    print("Offline self-check - no OpenAlex budget is spent.")
    try:
        check_imports()
        check_cache()
        check_origin_logic()
        check_scoring()
        check_orcid_live()
    except Exception as exc:  # noqa: BLE001 - the report is the product here
        print(f"\n[FAIL] unexpected error: {type(exc).__name__}: {exc}")
        failures.append(str(exc))

    print()
    for note in notes:
        print(f"  note: {note}")

    if failures:
        print(f"\n{len(failures)} check(s) failed. Fix these before running the pipeline.")
        return 1

    print("\nAll checks passed. Safe to run the pipeline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
