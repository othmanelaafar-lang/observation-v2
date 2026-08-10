from __future__ import annotations

import re


def normalize_name(name: str) -> str:
    cleaned = re.sub(r"\s+", " ", name or "").strip().lower()
    return re.sub(r"[^a-z0-9 ]", "", cleaned)


def dedupe_key(full_name: str, affiliation: str | None) -> str:
    name_key = normalize_name(full_name)
    affiliation_key = normalize_name(affiliation or "")
    return f"{name_key}|{affiliation_key}"
