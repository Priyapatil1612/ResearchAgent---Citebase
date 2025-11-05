# tools/search_web.py
from __future__ import annotations

import time
import logging
from typing import List, Dict, Tuple
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode

import requests

from config.settings import SETTINGS

logger = logging.getLogger(__name__)
logger.setLevel(getattr(logging, SETTINGS.LOG_LEVEL.upper(), logging.INFO))

# --- URL helpers ---
_UTM_KEYS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "igshid", "mc_cid", "mc_eid", "_hsenc", "_hsmi"
}

def _normalize_url(u: str) -> str:
    """Strip tracking params & fragments; only allow http(s)."""
    try:
        p = urlparse(u.strip())
        if p.scheme not in ("http", "https"):
            return ""
        q_pairs = [(k, v) for k, v in parse_qsl(p.query, keep_blank_values=True) if k not in _UTM_KEYS]
        q = urlencode(q_pairs, doseq=True)
        return urlunparse(p._replace(query=q, fragment=""))
    except Exception:
        return ""

def _domain(u: str) -> str:
    try:
        return urlparse(u).netloc.lower()
    except Exception:
        return ""

def _dedupe_and_diversify(items: List[Dict[str, str]], per_domain_limit: int = 2) -> List[Dict[str, str]]:
    seen_urls = set()
    domain_counts: Dict[str, int] = {}
    out: List[Dict[str, str]] = []
    for it in items:
        url = it.get("url") or ""
        if not url or url in seen_urls:
            continue
        d = _domain(url)
        if not d:
            continue
        if domain_counts.get(d, 0) >= per_domain_limit:
            continue
        seen_urls.add(url)
        domain_counts[d] = domain_counts.get(d, 0) + 1
        out.append(it)
    return out

# --- SerpAPI search ---
def search_web(query: str, k: int = 8) -> List[Dict[str, str]]:
    """
    Search the web via SerpAPI Google Search.

    Inputs:
        query: search string
        k: max results to return (will be <= SETTINGS.MAX_SEARCH_RESULTS)

    Output:
        List[ { "title": str, "url": str, "snippet": str } ]
    """
    if not SETTINGS.SERPAPI_API_KEY:
        logger.warning("SERPAPI_API_KEY missing; search_web returning [].")
        return []

    k = max(1, min(k, SETTINGS.MAX_SEARCH_RESULTS))
    endpoint = "https://serpapi.com/search"
    params = {
        "engine": "google",
        "q": query,
        "num": k,
        "api_key": SETTINGS.SERPAPI_API_KEY,
    }

    backoff = 1.0
    for attempt in range(SETTINGS.MAX_RETRIES + 1):
        try:
            r = requests.get(endpoint, params=params, timeout=SETTINGS.REQUEST_TIMEOUT_SECONDS)
            if r.status_code == 200:
                data = r.json()
                organic = data.get("organic_results") or []
                results: List[Dict[str, str]] = []
                for item in organic:
                    url = _normalize_url((item.get("link") or "").strip())
                    title = (item.get("title") or "").strip()
                    snippet = (item.get("snippet") or "").strip()
                    if url and title:
                        results.append({"title": title, "url": url, "snippet": snippet})
                results = _dedupe_and_diversify(results, per_domain_limit=2)
                return results[:k]
            elif r.status_code in (429, 500, 502, 503, 504):
                logger.warning(f"SerpAPI status {r.status_code}; retrying in {backoff:.1f}s (attempt {attempt+1})")
                time.sleep(backoff)
                backoff *= 2
            else:
                logger.warning(f"SerpAPI non-200 {r.status_code}: {r.text[:200]}")
                return []
        except requests.RequestException as e:
            logger.warning(f"SerpAPI request error: {e}; retrying in {backoff:.1f}s")
            time.sleep(backoff)
            backoff *= 2

    return []
