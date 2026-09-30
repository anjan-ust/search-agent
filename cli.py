import argparse
import asyncio
import os

from dotenv import load_dotenv
from tabulate import tabulate

load_dotenv()

REQUIRED_ENV = ["SERPAPI_KEY", "GROQ_API_KEY", "IMGBB_API_KEY"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dress image search agent")
    parser.add_argument("--image", required=True, help="Path to the dress image file")
    parser.add_argument("--size", default=None, help="Target size, e.g. M, L, 38")
    parser.add_argument(
        "--pincode",
        default=None,
        help="Delivery pincode, shown as a reminder only - not checked automatically",
    )
    return parser.parse_args()


def build_table(ranked_output) -> str:
    rows = [
        [
            c.title[:50],
            c.merchant or c.source_domain,
            f"{c.price} {c.currency}" if c.price else "-",
            c.match_type,
            "+".join(c.origin),
            "yes" if c.india_verified else "no",
            c.size_status,
            c.pincode_status,
            round(c.score, 2),
            c.link,
        ]
        for c in ranked_output
    ]
    headers = [
        "Title",
        "Merchant",
        "Price",
        "Match",
        "Origin",
        "India",
        "Size",
        "Pincode",
        "Score",
        "Link",
    ]
    return tabulate(rows, headers=headers, tablefmt="grid")


async def main() -> None:
    args = parse_args()

    missing = [name for name in REQUIRED_ENV if not os.environ.get(name)]
    if missing:
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill them in."
        )

    # Imported after the env check so a missing langgraph/dependency error
    # doesn't mask a more actionable "you forgot to set up .env" message.
    from graph import build_graph

    app = build_graph()
    initial_state = {
        "image_path": args.image,
        "target_size": args.size,
        "pincode": args.pincode,
        "errors": [],
    }
    result = await app.ainvoke(initial_state)

    print(build_table(result.get("ranked_output", [])))

    if args.pincode:
        print(
            f"\nPincode delivery is not checked automatically - verify "
            f"delivery to {args.pincode} yourself for the candidates above."
        )

    errors = result.get("errors", [])
    if errors:
        print("\nWarnings during this run:")
        for err in errors:
            print(f"  - {err}")


if __name__ == "__main__":
    asyncio.run(main())
