from typing import Callable

from . import generic

_REGISTRY: dict[str, Callable[[str, str], str]] = {}


def register(domain: str, fn: Callable[[str, str], str]) -> None:
    _REGISTRY[domain] = fn


def get_adapter(domain: str) -> Callable[[str, str], str]:
    """Site-specific parsers can be registered here as they're written
    (see README). Falls back to the generic text-search heuristic for any
    domain without one.
    """
    return _REGISTRY.get(domain, generic.check_size)

