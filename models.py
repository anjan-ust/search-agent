from __future__ import annotations

import operator
from dataclasses import dataclass, field
from typing import Annotated, Literal, Optional, TypedDict

MatchType = Literal["exact", "similar", "text"]
Origin = Literal["lens", "shopping"]
SizeStatus = Literal["available", "unavailable", "unchecked"]
PincodeStatus = Literal["deliverable", "not_deliverable", "unchecked"]


@dataclass
class Candidate:
    id: str
    title: str
    link: str
    source_domain: str
    price: Optional[float] = None
    currency: Optional[str] = None
    merchant: Optional[str] = None
    thumbnail: Optional[str] = None
    match_type: MatchType = "text"
    origin: list[Origin] = field(default_factory=list)
    india_verified: bool = False
    size_status: SizeStatus = "unchecked"
    pincode_status: PincodeStatus = "unchecked"
    score: float = 0.0


class GraphState(TypedDict, total=False):
    image_path: str
    image_url: str
    attributes: dict
    search_queries: list[str]
    lens_results: list[Candidate]
    shopping_results: list[Candidate]
    merged: list[Candidate]
    india_filtered: list[Candidate]
    verified: list[Candidate]
    ranked_output: list[Candidate]
    target_size: Optional[str]
    pincode: Optional[str]
    # Multiple branches run concurrently and each may append warnings in the
    # same superstep, so this needs a reducer instead of last-write-wins.
    errors: Annotated[list[str], operator.add]
