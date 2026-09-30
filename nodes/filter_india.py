from pathlib import Path

import yaml

from models import Candidate

CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "domains.yaml"


def _load_config() -> dict:
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


async def filter_india(state: dict) -> dict:
    config = _load_config()
    whitelist = set(config.get("whitelist", []))
    blacklist = set(config.get("blacklist", []))

    filtered: list[Candidate] = []
    for candidate in state.get("merged", []):
        if candidate.source_domain in blacklist:
            continue
        is_whitelisted = candidate.source_domain in whitelist
        is_inr = (candidate.currency or "").upper() == "INR"
        if is_whitelisted or is_inr:
            candidate.india_verified = True
            filtered.append(candidate)

    return {"india_filtered": filtered}
