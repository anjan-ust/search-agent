import os

from clients import imgbb


async def host_image(state: dict) -> dict:
    """Uploads the local image to imgbb so it has a public URL. Both
    lens_search and describe_image need this (Lens requires a public URL,
    and the Groq vision call also accepts a URL), so it runs once before the
    fan-out rather than being duplicated in each branch.
    """
    api_key = os.environ["IMGBB_API_KEY"]
    try:
        url = await imgbb.upload_image(state["image_path"], api_key)
        return {"image_url": url}
    except Exception as e:
        return {"image_url": "", "errors": [f"host_image: {e}"]}
