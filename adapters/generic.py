import re

OUT_OF_STOCK_PATTERNS = [
    r"out of stock",
    r"sold out",
    r"notify me",
    r"currently unavailable",
]


def check_size(html: str, target_size: str) -> str:
    """Best-effort heuristic: look for the target size in the page text and
    check nearby text for out-of-stock language. Returns "unchecked" whenever
    the page is client-side rendered or blocked (i.e. we can't find the size
    at all) rather than guessing.
    """
    html_lower = html.lower()
    size_lower = target_size.lower()

    size_pos = html_lower.find(size_lower)
    if size_pos == -1:
        return "unchecked"

    window = html_lower[max(0, size_pos - 200) : size_pos + 200]
    for pattern in OUT_OF_STOCK_PATTERNS:
        if re.search(pattern, window):
            return "unavailable"

    return "available"
