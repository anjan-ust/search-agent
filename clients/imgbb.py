import base64

import httpx

IMGBB_UPLOAD_URL = "https://api.imgbb.com/1/upload"


async def upload_image(image_path: str, api_key: str) -> str:
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            IMGBB_UPLOAD_URL,
            data={"key": api_key, "image": image_b64},
        )
        resp.raise_for_status()
        data = resp.json()
        return data["data"]["url"]
