import httpx

SERPAPI_URL = "https://serpapi.com/search.json"


async def google_lens(image_url: str, api_key: str) -> dict:
    params = {"engine": "google_lens", "url": image_url, "api_key": api_key}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SERPAPI_URL, params=params)
        resp.raise_for_status()
        return resp.json()


async def google_shopping(query: str, api_key: str, gl: str = "in", hl: str = "en") -> dict:
    params = {
        "engine": "google_shopping",
        "q": query,
        "gl": gl,
        "hl": hl,
        "api_key": api_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(SERPAPI_URL, params=params)
        resp.raise_for_status()
        return resp.json()
