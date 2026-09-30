# Dress Image Search Agent

Given a photo of a dress, finds where to buy it (or something close to it)
from Indian retailers, ranked by how well it matches and what's been verified.

## How it works

```
                 ┌── lens_search (image) ─────────┐
start→host_image─┤                                 ├─ merge_dedupe ─ filter_india ─ verify_availability ─ rank_output
                 └── describe_image → shopping_search ┘
```

1. **host_image** — uploads your photo to imgbb to get a temporary public URL (needed because SerpApi's Lens engine only accepts image URLs, not file uploads).
2. **lens_search** — runs that URL through SerpApi's `google_lens` engine for exact/visual matches.
3. **describe_image** — in parallel, a Groq-hosted vision model extracts structured attributes (type, color, pattern, neckline, sleeve, fabric, occasion, length) from the same image, then a Groq text model turns those into 1-2 shopping search queries.
4. **shopping_search** — runs those queries through SerpApi's `google_shopping` engine (`gl=in`).
5. **merge_dedupe** — combines both branches, deduping by normalized URL and fuzzy title match per domain.
6. **filter_india** — keeps only results from Indian retailers (domain whitelist) or priced in INR; drops known non-Indian domains outright. Pure filter, no extra API calls.
7. **verify_availability** — for the top candidates, fetches the product page and looks for your target size near "out of stock" language. If the page is blocked, JS-rendered, or unreachable, the result is marked `unchecked` and still shown — never silently dropped.
8. **rank_output** — scores and sorts everything, tagging each result with `india_verified`, `size_status`, and `pincode_status` so you can see exactly what was and wasn't checked.

**Pincode delivery is never checked automatically.** It's the one filter that isn't reliably scriptable across retailers (site-specific AJAX calls, usually behind bot protection). The CLI just reminds you to check it manually for whatever survives the filters above.

## v1 scope (what's deliberately not included yet)

- **No Playwright / headless browser.** `verify_availability` uses a plain HTTP fetch. Sites that render their size selector client-side (Myntra, Ajio) will mostly come back `unchecked` rather than `available`/`unavailable` — that's an honest limitation, not a bug. Add a Playwright fallback later if you want to close this gap.
- **No per-retailer size/pincode adapters yet.** There's a `get_adapter()` registry in `adapters/` ready for site-specific parsers (see below) — only a generic heuristic is wired up today.
- **No run persistence/checkpointing.** Each run is stateless end to end.

## Tech requirements

- Python 3.11+
- Accounts/API keys (all free tier):
  - [SerpApi](https://serpapi.com/manage-api-key) — 250 searches/month free. Both `google_lens` and `google_shopping` calls count against this quota.
  - [Groq](https://console.groq.com/keys) — used for both the vision model (image → attributes) and the text model (attributes → search queries).
  - [imgbb](https://api.imgbb.com/) — used only to host your image long enough for SerpApi/Groq to fetch it by URL.

## Setup

```bash
# 1. create and activate a virtual environment (recommended)
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate      # macOS/Linux

# 2. install dependencies (includes FastAPI/uvicorn for the web UI and the CLI's deps)
pip install -r requirements.txt

# 3. configure API keys
cp .env.example .env
# then fill in SERPAPI_KEY, GROQ_API_KEY, IMGBB_API_KEY in .env
```

Check `GROQ_VLM_MODEL` / `GROQ_LLM_MODEL` in `.env` against the current list at
https://console.groq.com/docs/models before your first run — Groq's available
model ids change over time.

## Usage

### Web UI (recommended)

```bash
uvicorn server:app --reload
```

Then open **http://localhost:8000** in your browser. Drag/drop or click to upload a photo, optionally fill in target size and pincode, and hit **Find this dress**. A live checklist shows each graph node completing (Lens search, VLM analysis, dedupe, filter, availability check, ranking) via a streamed connection, then results render as a card grid — thumbnail, merchant, price, match type, origin (lens/shopping/both), and colored status pills for `india_verified` / `size_status` / `pincode_status`. Pincode is displayed as a manual-check reminder banner, never auto-verified (see below).

No separate frontend build step — `server.py` serves the page and a `/api/search` streaming endpoint directly; everything in `static/` is plain HTML/CSS/JS.

### CLI (alternative)

```bash
python cli.py --image ./photos/dress.jpg --size M --pincode 400001
```

- `--image` (required) — path to the dress photo.
- `--size` (optional) — target size to check for in `verify_availability`. If omitted, all results come back `size_status: unchecked`.
- `--pincode` (optional) — just echoed back as a reminder to check manually; not used by the graph.

Output is a table with columns: Title, Merchant, Price, Match type (`exact`/`similar`/`text`), Origin (`lens`/`shopping`/both), India-verified, Size status, Pincode status, Score, Link. Any node-level failures (a blocked fetch, a bad VLM response, etc.) print as warnings below the table instead of crashing the run — the graph is built to degrade gracefully rather than fail closed. The web UI surfaces the same warnings in a banner instead.

## Troubleshooting

- **`SSL: CERTIFICATE_VERIFY_FAILED`** — seen on corporate networks that intercept TLS with their own root CA. Point `httpx` at your corporate CA bundle, e.g. set `SSL_CERT_FILE=/path/to/corp-ca-bundle.pem` (or `REQUESTS_CA_BUNDLE`) in your environment before running, or ask your IT team for the bundle path. This is a network/environment issue, not a bug in this project.

## Project structure

```
graph.py               LangGraph wiring (fan-out/join)
models.py               Candidate + GraphState schemas
server.py               FastAPI app - serves the web UI and streams progress over SSE
cli.py                  CLI entrypoint (table output)
static/                 Frontend: index.html, style.css, app.js (no build step)
clients/                SerpApi, Groq, imgbb API wrappers
nodes/                  One module per graph node
adapters/               Per-retailer size-check parsers (generic fallback included)
utils/                  URL normalization helpers
config/domains.yaml      India whitelist/blacklist, editable without code changes
```

## Extending it

- **Site-specific size parsing**: add a module in `adapters/` (e.g. `adapters/myntra.py`) exposing `check_size(html: str, target_size: str) -> str`, then call `adapters.register("myntra.com", check_size)` on import.
- **Site-specific pincode checks**: for the 2-3 retailers you actually buy from, open devtools, watch the network tab when entering a pincode on the product page, and reverse-engineer that endpoint into a small per-site function. This won't generalize and isn't wired into the graph as an automated node on purpose — see the "v1 scope" note above.
- **Domain whitelist/blacklist**: edit `config/domains.yaml` directly, no code changes needed.
