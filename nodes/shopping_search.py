import os

from clients import serpapi
from models import Candidate
from utils.urls import extract_domain


async def shopping_search(state: dict) -> dict:
    queries = state.get("search_queries") or []
    if not queries:
        return {"shopping_results": [], "errors": ["shopping_search: no queries, skipped"]}

    api_key = os.environ["SERPAPI_KEY"]
    results: list[Candidate] = []
    errors: list[str] = []

    for query in queries:
        try:
            data = await serpapi.google_shopping(query, api_key)
        except Exception as e:
            errors.append(f"shopping_search ({query}): {e}")
            continue
        for item in data.get("shopping_results", []):
            candidate = _to_candidate(item)
            if candidate:
                results.append(candidate)

    return {"shopping_results": results, "errors": errors}


def _to_candidate(item: dict):
    link = item.get("product_link") or item.get("link")
    if not link:
        return None
    return Candidate(
        id="",
        title=item.get("title", ""),
        link=link,
        source_domain=extract_domain(link),
        price=item.get("extracted_price"),
        currency=item.get("currency", "INR"),
        merchant=item.get("source"),
        thumbnail=item.get("thumbnail"),
        match_type="text",
        origin=["shopping"],
    )
