"""Explicit public-query smoke probe; no model and no conversation data."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from enthus.source import Wikipedia


async def probe(language: str, query: str) -> dict[str, object]:
    source = Path(__file__).resolve().parents[1] / "src/enthus/source.py"
    result = await Wikipedia(language)(query)
    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "source_code_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "kind": "live-source-probe-only", "model": None,
        "query": query, "request_url": result.request_url,
        "response_bytes": len(result.response.encode()),
        "response_sha256": hashlib.sha256(result.response.encode()).hexdigest(),
        "error": result.error,
        "items": [{"id": item.id, "title": item.title, "url": item.url,
                   "revision": item.revision, "excerpt_characters": len(item.excerpt)} for item in result.items],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--language", choices=("en", "zh"), default="en")
    parser.add_argument("--query", default="puzzle game")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = asyncio.run(probe(args.language, args.query))
    report = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(report)
    print(report, end="")


if __name__ == "__main__":
    main()
