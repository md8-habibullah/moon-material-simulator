"""Read-only client for NASA's Technical Reports Server (NTRS) public search API.

Safety: the host and path are fixed, the only caller-controlled value is the URL-encoded query
string, responses are size-capped and time-limited, and results are cached for an hour so the
upstream service isn't hammered.
"""
import json
import threading
import time
import urllib.parse
import urllib.request

NTRS_SEARCH_URL = "https://ntrs.nasa.gov/api/citations/search"
NTRS_BASE = "https://ntrs.nasa.gov"
TIMEOUT_S = 8
MAX_BYTES = 2_000_000
CACHE_TTL_S = 3600
MAX_UPSTREAM_CALLS_PER_MIN = 30

_cache: dict[tuple, tuple[float, list]] = {}
_calls: list[float] = []
_lock = threading.Lock()


class NTRSError(Exception):
    """Upstream failure; the message is safe to log but not meant for clients."""


def _year(record: dict) -> int | None:
    for pub in record.get("publications") or []:
        if pub.get("publicationDate"):
            return int(pub["publicationDate"][:4])
    for key in ("submittedDate", "created"):
        if record.get(key):
            return int(record[key][:4])
    return None


def simplify(record: dict) -> dict:
    downloads = [d.get("links", {}).get("pdf") for d in record.get("downloads") or []]
    pdf = next((d for d in downloads if d), None)
    authors = [
        a.get("meta", {}).get("author", {}).get("name")
        for a in record.get("authorAffiliations") or []
    ]
    return {
        "id": str(record["id"]),
        "title": " ".join((record.get("title") or "").split()),
        "year": _year(record),
        "type": record.get("stiTypeDetails") or record.get("stiType"),
        "center": (record.get("center") or {}).get("name"),
        "authors": [a for a in authors if a][:4],
        "abstract": " ".join((record.get("abstract") or "").split())[:600],
        "url": f"{NTRS_BASE}/citations/{record['id']}",
        "pdf": f"{NTRS_BASE}{pdf}" if pdf else None,
    }


def _rate_limited() -> bool:
    now = time.monotonic()
    with _lock:
        _calls[:] = [t for t in _calls if now - t < 60]
        if len(_calls) >= MAX_UPSTREAM_CALLS_PER_MIN:
            return True
        _calls.append(now)
        return False


def search(query: str, size: int = 8) -> list[dict]:
    key = (query.strip().lower(), size)
    now = time.monotonic()
    with _lock:
        hit = _cache.get(key)
        if hit and now - hit[0] < CACHE_TTL_S:
            return hit[1]
    if _rate_limited():
        raise NTRSError("local rate limit reached")

    params = urllib.parse.urlencode({"q": query, "page.size": size})
    request = urllib.request.Request(
        f"{NTRS_SEARCH_URL}?{params}",
        headers={"Accept": "application/json", "User-Agent": "moon-material-simulator (NASA Space Apps 2026)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
            body = response.read(MAX_BYTES + 1)
    except OSError as exc:
        raise NTRSError(f"NTRS request failed: {exc}") from exc
    if len(body) > MAX_BYTES:
        raise NTRSError("NTRS response too large")
    try:
        results = [simplify(r) for r in json.loads(body).get("results", [])]
    except (ValueError, KeyError, TypeError) as exc:
        raise NTRSError("NTRS response not understood") from exc

    with _lock:
        _cache[key] = (now, results)
    return results
