import asyncio
import os

import httpx

from adapters import get_adapter
from models import Candidate

TOP_N = int(os.environ.get("VERIFY_TOP_N", "12"))
MAX_CONCURRENCY = int(os.environ.get("VERIFY_MAX_CONCURRENCY", "5"))
PER_DOMAIN_CONCURRENCY = 2
TIMEOUT = 8.0


async def verify_availability(state: dict) -> dict:
    all_filtered = state.get("india_filtered", [])
    candidates = all_filtered[:TOP_N]
    untouched = all_filtered[TOP_N:]  # kept but not verified, to stay cheap
    target_size = state.get("target_size")

    global_sem = asyncio.Semaphore(MAX_CONCURRENCY)
    domain_sems: dict[str, asyncio.Semaphore] = {}

    async def process(candidate: Candidate) -> Candidate:
        domain_sem = domain_sems.setdefault(
            candidate.source_domain, asyncio.Semaphore(PER_DOMAIN_CONCURRENCY)
        )
        async with global_sem, domain_sem:
            candidate.size_status = await _check_size(candidate, target_size)
        return candidate

    verified = await asyncio.gather(*(process(c) for c in candidates)) if candidates else []
    return {"verified": list(verified) + untouched}


async def _check_size(candidate: Candidate, target_size: str | None) -> str:
    if not target_size:
        return "unchecked"
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            resp = await client.get(candidate.link, headers={"User-Agent": "Mozilla/5.0"})
        # Blocked/challenge pages are typically small or non-200; treat both
        # as "we couldn't verify" rather than guessing availability.
        if resp.status_code != 200 or len(resp.text) < 500:
            return "unchecked"
        adapter = get_adapter(candidate.source_domain)
        return adapter(resp.text, target_size)
    except Exception:
        return "unchecked"
