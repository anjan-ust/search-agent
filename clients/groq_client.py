import json

import httpx

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

ATTRIBUTE_PROMPT = """You are analyzing a photo of a dress for an online shopping search.
Return ONLY valid JSON (no markdown fences, no commentary) with these exact keys:
type, color, pattern, neckline, sleeve, fabric, occasion, length.
Use short lowercase phrases (2-4 words max) for each value. If a field is not visible, use "unknown".
"""

QUERY_PROMPT = """Given these dress attributes as JSON, write 1 to 2 short Google Shopping search
queries (5-8 words each) that would find this exact style of dress. Return ONLY a JSON array of
strings, no commentary.

Attributes:
{attributes}
"""


async def describe_image(image_url: str, api_key: str, model: str) -> dict:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": ATTRIBUTE_PROMPT},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ],
            }
        ],
        "temperature": 0.2,
    }
    text = await _chat(payload, api_key)
    return _parse_json_object(text)


async def generate_queries(attributes: dict, api_key: str, model: str) -> list[str]:
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": QUERY_PROMPT.format(attributes=json.dumps(attributes))}
        ],
        "temperature": 0.3,
    }
    text = await _chat(payload, api_key)
    queries = _parse_json_array(text)
    return queries or [_fallback_query(attributes)]


async def _chat(payload: dict, api_key: str) -> str:
    headers = {"Authorization": f"Bearer {api_key}"}
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(GROQ_CHAT_URL, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def _parse_json_object(text: str) -> dict:
    try:
        result = json.loads(_strip_fences(text))
        return result if isinstance(result, dict) else {}
    except json.JSONDecodeError:
        return {}


def _parse_json_array(text: str) -> list[str]:
    try:
        result = json.loads(_strip_fences(text))
        return [str(q) for q in result] if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []


def _fallback_query(attributes: dict) -> str:
    parts = [attributes.get(k, "") for k in ("color", "pattern", "type")]
    return " ".join(p for p in parts if p and p != "unknown") or "dress"
