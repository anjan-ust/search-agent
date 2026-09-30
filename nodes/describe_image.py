import os

from clients import groq_client


async def describe_image(state: dict) -> dict:
    image_url = state.get("image_url")
    if not image_url:
        return {
            "attributes": {},
            "search_queries": [],
            "errors": ["describe_image: no image_url, skipped"],
        }

    api_key = os.environ["GROQ_API_KEY"]
    vlm_model = os.environ.get("GROQ_VLM_MODEL", "llama-3.2-11b-vision-preview")
    llm_model = os.environ.get("GROQ_LLM_MODEL", "llama-3.3-70b-versatile")
    errors: list[str] = []

    try:
        attributes = await groq_client.describe_image(image_url, api_key, vlm_model)
    except Exception as e:
        errors.append(f"describe_image (vlm): {e}")
        attributes = {}

    queries: list[str] = []
    if attributes:
        try:
            queries = await groq_client.generate_queries(attributes, api_key, llm_model)
        except Exception as e:
            errors.append(f"describe_image (query-gen): {e}")

    return {"attributes": attributes, "search_queries": queries, "errors": errors}
