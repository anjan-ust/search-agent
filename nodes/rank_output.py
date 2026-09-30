from models import Candidate

MATCH_TYPE_SCORE = {"exact": 3, "similar": 2, "text": 1}
SIZE_SCORE = {"available": 2, "unchecked": 0, "unavailable": -5}


def _score(candidate: Candidate) -> float:
    total = MATCH_TYPE_SCORE.get(candidate.match_type, 0)
    total += len(candidate.origin)  # found by both branches ranks higher
    if candidate.india_verified:
        total += 1
    total += SIZE_SCORE.get(candidate.size_status, 0)
    if candidate.price:
        total += 0.1
    return total


async def rank_output(state: dict) -> dict:
    candidates = state.get("verified", [])
    for candidate in candidates:
        candidate.score = _score(candidate)
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    return {"ranked_output": ranked}
