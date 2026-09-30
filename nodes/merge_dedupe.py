from rapidfuzz import fuzz

from models import Candidate
from utils.urls import normalize_url

FUZZY_MATCH_THRESHOLD = 85


async def merge_dedupe(state: dict) -> dict:
    all_candidates = list(state.get("lens_results", [])) + list(state.get("shopping_results", []))
    merged: list[Candidate] = []

    for candidate in all_candidates:
        candidate.id = normalize_url(candidate.link)
        match = _find_match(candidate, merged)
        if match is None:
            merged.append(candidate)
        else:
            _combine(match, candidate)

    return {"merged": merged}


def _find_match(candidate: Candidate, pool: list[Candidate]):
    for existing in pool:
        if existing.id == candidate.id:
            return existing
        if existing.source_domain == candidate.source_domain:
            similarity = fuzz.token_sort_ratio(existing.title, candidate.title)
            if similarity >= FUZZY_MATCH_THRESHOLD:
                return existing
    return None


def _combine(existing: Candidate, new: Candidate) -> None:
    for origin in new.origin:
        if origin not in existing.origin:
            existing.origin.append(origin)
    if not existing.price and new.price:
        existing.price = new.price
        existing.currency = new.currency
    # Prefer the more specific Lens match type over a generic text match.
    if existing.match_type == "text" and new.match_type in ("exact", "similar"):
        existing.match_type = new.match_type
