import dataclasses
import json
import os
import tempfile
import uuid
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Form, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from graph import build_graph

app = FastAPI(title="Dress Image Search Agent")

STATIC_DIR = Path(__file__).resolve().parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

REQUIRED_ENV = ["SERPAPI_KEY", "GROQ_API_KEY", "IMGBB_API_KEY"]

# Order here is just the checklist order shown in the UI - lens_search and
# describe_image actually run concurrently, so their "done" events can arrive
# in either order; the frontend doesn't assume strict sequencing.
STEP_LABELS = {
    "host_image": "Uploading image",
    "lens_search": "Searching Google Lens",
    "describe_image": "Analyzing image with VLM",
    "shopping_search": "Searching Google Shopping",
    "merge_dedupe": "Merging & deduping results",
    "filter_india": "Filtering for India availability",
    "verify_availability": "Checking size availability",
    "rank_output": "Ranking results",
}


@app.get("/")
async def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/steps")
async def steps():
    return [{"node": node, "label": label} for node, label in STEP_LABELS.items()]


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _candidate_dict(candidate) -> dict:
    return dataclasses.asdict(candidate)


@app.post("/api/search")
async def search(image: UploadFile, size: str = Form(""), pincode: str = Form("")):
    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:

        async def missing_gen():
            yield _sse(
                {
                    "type": "error",
                    "message": f"Missing env vars: {', '.join(missing)}. Set them in .env and restart the server.",
                }
            )

        return StreamingResponse(missing_gen(), media_type="text/event-stream")

    suffix = Path(image.filename or "upload.jpg").suffix or ".jpg"
    tmp_path = Path(tempfile.gettempdir()) / f"dress-search-{uuid.uuid4().hex}{suffix}"
    tmp_path.write_bytes(await image.read())

    async def event_generator():
        errors: list[str] = []
        ranked: list = []
        try:
            graph = build_graph()
            initial_state = {
                "image_path": str(tmp_path),
                "target_size": size or None,
                "pincode": pincode or None,
                "errors": [],
            }
            async for update in graph.astream(initial_state, stream_mode="updates"):
                for node_name, output in update.items():
                    yield _sse(
                        {
                            "type": "step",
                            "node": node_name,
                            "label": STEP_LABELS.get(node_name, node_name),
                        }
                    )
                    if output.get("errors"):
                        errors.extend(output["errors"])
                    if node_name == "rank_output":
                        ranked = output.get("ranked_output", [])

            yield _sse(
                {
                    "type": "done",
                    "results": [_candidate_dict(c) for c in ranked],
                    "errors": errors,
                    "pincode": pincode or None,
                }
            )
        except Exception as e:
            yield _sse({"type": "error", "message": str(e)})
        finally:
            tmp_path.unlink(missing_ok=True)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
