from urllib.parse import urlparse


def extract_domain(url: str) -> str:
    netloc = urlparse(url).netloc.lower()
    return netloc[4:] if netloc.startswith("www.") else netloc


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    domain = extract_domain(url)
    path = parsed.path.rstrip("/").lower()
    return f"{domain}{path}"
