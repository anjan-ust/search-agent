import os

from clients import serpapi
from models import Candidate
from utils.urls import extract_domain

# SerpApi's google_lens response shape has shifted between API versions; we
# check both possible keys defensively rather than assuming one.
MATCH_KEYS = [("exact_matches", "exact"), ("visual_matches", "similar")]


async def lens_search(state: dict) -> dict:
    image_url = state.get("image_url")
    if not image_url:
        return {"lens_results": [], "errors": ["lens_search: no image_url, skipped"]}

    api_key = os.environ["SERPAPI_KEY"]
    try:
        data = await serpapi.google_lens(image_url, api_key)
    except Exception as e:
        return {"lens_results": [], "errors": [f"lens_search: {e}"]}

    results: list[Candidate] = []
    for key, match_type in MATCH_KEYS:
        for item in data.get(key, []):
            candidate = _to_candidate(item, match_type)
            if candidate:
                results.append(candidate)

    return {"lens_results": results}


def _to_candidate(item: dict, match_type: str):
    link = item.get("link")
    if not link:
        return None
    price_info = item.get("price") or {}
    return Candidate(
        id="",
        title=item.get("title", ""),
        link=link,
        source_domain=extract_domain(link),
        price=price_info.get("extracted_value"),
        currency=price_info.get("currency"),
        merchant=item.get("source"),
        thumbnail=item.get("thumbnail"),
        match_type=match_type,
        origin=["lens"],
    )
