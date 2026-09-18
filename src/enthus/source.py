"""One bounded, read-only Wikipedia adapter; the model cannot select endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .models import SourceItem, SourceResult


class _NoRedirect(HTTPRedirectHandler):
    # Following a source-provided redirect would widen the host's endpoint scope.
    def redirect_request(self, req: Request, fp: object, code: int, msg: str,
                         headers: object, newurl: str) -> None:
        return None


class Wikipedia:
    def __init__(self, language: str, timeout: float = 10) -> None:
        if language not in {"en", "zh"}:
            raise ValueError("Wikipedia language must be en or zh")
        self.language, self.timeout = language, timeout
        self._inflight: asyncio.Task[SourceResult] | None = None

    async def __call__(self, query: str) -> SourceResult:
        if self._inflight is not None and not self._inflight.done():
            raise RuntimeError("Previous read is still ending; no parallel source requests")
        self._inflight = asyncio.create_task(asyncio.to_thread(self._request, query))
        # Keep the worker tracked after the shell times out, so a slow socket
        # cannot silently create concurrent requests on the next evaluation.
        self._inflight.add_done_callback(lambda task: task.exception() if not task.cancelled() else None)
        return await asyncio.shield(self._inflight)

    def _request(self, query: str) -> SourceResult:
        if not isinstance(query, str) or not query.strip() or len(query) > 200:
            raise ValueError("Invalid query length")
        url = f"https://{self.language}.wikipedia.org/w/api.php?" + urlencode({
            "action": "query", "generator": "search", "gsrsearch": query,
            "gsrnamespace": 0, "gsrlimit": 3, "prop": "extracts|info",
            "exintro": 1, "explaintext": 1, "exchars": 1200, "exlimit": 3,
            "format": "json", "formatversion": 2, "maxlag": 5,
        })
        request = Request(url, headers={"User-Agent": "Enthus/0.0.1 (local conversational research prototype)",
                                       "Accept": "application/json"})
        deadline = time.monotonic() + self.timeout
        with build_opener(_NoRedirect()).open(request, timeout=self.timeout) as response:
            chunks: list[bytes] = []
            length = 0
            while length <= 262144:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Source read deadline exceeded")
                chunk = response.read1(min(16384, 262145 - length))
                if not chunk:
                    break
                chunks.append(chunk)
                length += len(chunk)
            raw = b"".join(chunks)
        if len(raw) > 262144:
            raise ValueError("Source response exceeded 256 KiB")
        snapshot = raw.decode("utf-8")
        data = json.loads(snapshot)
        if "error" in data:
            return SourceResult(query, url, (), snapshot, f"Wikipedia API error: {str(data['error'])[:300]}")
        items: list[SourceItem] = []
        for page in sorted(data.get("query", {}).get("pages", []), key=lambda p: p.get("index", 0))[:3]:
            if "missing" in page or not page.get("extract"):
                continue
            page_id, revision = int(page["pageid"]), int(page["lastrevid"])
            excerpt = str(page["extract"])[:1200]
            digest = hashlib.sha256(excerpt.encode()).hexdigest()[:16]
            identity = f"wiki:{self.language}:{page_id}:{revision}:{digest}"
            items.append(SourceItem(identity, str(page["title"])[:200],
                                    f"https://{self.language}.wikipedia.org/w/index.php?oldid={revision}",
                                    excerpt, revision))
        return SourceResult(query, url, tuple(items), snapshot)
